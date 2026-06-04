"""
All vendor business logic lives here — routers stay thin.
"""
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.constants import AuditAction
from app.models.identity import User, UserRole, Role
from app.models.platform import VendorApplication
from app.models.catalog import Vendor
from app.schemas.vendor import VendorApplicationRequest, VendorUpdateRequest
from app.utils.audit import AuditLogger
from app.services.base import BaseService


VALID_VENDOR_TYPES = {"FARM", "WINERY", "AGRITOURISM", "RESTAURANT"}


class VendorService(BaseService):
    """Service for managing vendors and applications."""

    def _slugify(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_-]+", "-", text)
        return text

    def _unique_slug(self, db: Session, base: str) -> str:
        slug = self._slugify(base)
        candidate = slug
        counter = 1
        while db.query(Vendor).filter(Vendor.slug == candidate).first():
            candidate = f"{slug}-{counter}"
            counter += 1
        return candidate

    def apply_as_vendor(
        self,
        db: Session,
        user: User,
        body: VendorApplicationRequest,
        request: Any | None = None,
    ) -> VendorApplication:
        if body.type not in VALID_VENDOR_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid vendor type. Must be one of: {', '.join(VALID_VENDOR_TYPES)}",
            )

        # One pending/approved application per user is enough
        existing = (
            db.query(VendorApplication)
            .filter(
                VendorApplication.applicant_id == user.id,
                VendorApplication.status.in_(["pending", "approved"]),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You already have a {existing.status} application.",
            )

        application = VendorApplication(
            applicant_id=user.id,
            business_name=body.business_name,
            type=body.type,
            region=body.region,
            contact_email=body.contact_email,
            website=body.website,
            description=body.description,
            status="pending",
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        AuditLogger.log(
            db=db,
            action=AuditAction.VENDOR_CREATE,
            resource_type="VendorApplication",
            actor=user,
            resource_id=application.id,
            after={"status": application.status, "business_name": application.business_name},
            request=request,
        )
        return application

    def approve_application(
        self,
        db: Session,
        application_id: uuid.UUID,
        reviewed_by: User,
        request: Any | None = None,
    ) -> Vendor:
        application = db.query(VendorApplication).filter(
            VendorApplication.id == application_id
        ).first()

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        if application.status != "pending":
            raise HTTPException(
                status_code=409,
                detail=f"Application is already {application.status}",
            )

        # Create the vendor
        vendor = Vendor(
            owner_id=application.applicant_id,
            name=application.business_name,
            slug=self._unique_slug(db, application.business_name),
            type=application.type,
            region=application.region,
            email=application.contact_email,
            website=application.website,
            description=application.description,
            status="active",
            tier="FREE",
            approved_at=datetime.now(timezone.utc),
            approved_by=reviewed_by.id,
        )
        db.add(vendor)
        db.flush()

        # Update application
        application.status = "approved"
        application.reviewed_by = reviewed_by.id
        application.reviewed_at = datetime.now(timezone.utc)
        application.vendor_id = vendor.id

        # Assign VENDOR_ADMIN role scoped to this vendor
        vendor_admin_role = db.query(Role).filter(Role.code == "VENDOR_ADMIN").first()
        if vendor_admin_role:
            # Avoid duplicates
            already = db.query(UserRole).filter(
                UserRole.user_id == application.applicant_id,
                UserRole.role_id == vendor_admin_role.id,
                UserRole.vendor_id == vendor.id,
            ).first()
            if not already:
                db.add(UserRole(
                    user_id=application.applicant_id,
                    role_id=vendor_admin_role.id,
                    vendor_id=vendor.id,
                    granted_at=datetime.now(timezone.utc),
                    granted_by=reviewed_by.id,
                ))

        db.commit()
        db.refresh(vendor)
        AuditLogger.log(
            db=db,
            action=AuditAction.VENDOR_APPROVE,
            resource_type="Vendor",
            actor=reviewed_by,
            resource_id=vendor.id,
            after={"status": vendor.status, "slug": vendor.slug},
            request=request,
        )
        return vendor

    def reject_application(
        self,
        db: Session,
        application_id: uuid.UUID,
        reviewed_by: User,
        reason: str | None = None,
        request: Any | None = None,
    ) -> VendorApplication:
        application = db.query(VendorApplication).filter(
            VendorApplication.id == application_id
        ).first()

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        if application.status != "pending":
            raise HTTPException(status_code=409, detail=f"Application is already {application.status}")

        application.status = "rejected"
        application.reviewed_by = reviewed_by.id
        application.reviewed_at = datetime.now(timezone.utc)
        application.rejection_reason = reason
        db.commit()
        db.refresh(application)
        AuditLogger.log(
            db=db,
            action=AuditAction.VENDOR_REJECT,
            resource_type="VendorApplication",
            actor=reviewed_by,
            resource_id=application.id,
            before={"status": "pending"},
            after={"status": application.status, "reason": reason},
            request=request,
        )
        return application

    def update(
        self,
        db: Session,
        vendor_id: uuid.UUID,
        body: VendorUpdateRequest,
        current_user: User,
        request: Any | None = None,
    ) -> Vendor:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()

        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        # Must be the owner or a superadmin
        if vendor.owner_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized")

        previous_status = vendor.status
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(vendor, field, value)

        db.commit()
        db.refresh(vendor)
        AuditLogger.log(
            db=db,
            action=AuditAction.VENDOR_UPDATE,
            resource_type="Vendor",
            actor=current_user,
            resource_id=vendor.id,
            before={"status": previous_status},
            after={"status": vendor.status, "name": vendor.name},
            request=request,
        )
        return vendor


# ── Global singleton instance and accessors ────────────────────────────────────

_vendor_service = VendorService()


def get_vendor_service() -> VendorService:
    """Get the global vendor service instance."""
    return _vendor_service


# ── Backward-compatible wrapper functions ──────────────────────────────────────

def apply_as_vendor(
    db: Session,
    user: User,
    body: VendorApplicationRequest,
    request: Any | None = None,
) -> VendorApplication:
    return get_vendor_service().apply_as_vendor(db, user, body, request)


def approve_application(
    db: Session,
    application_id: uuid.UUID,
    reviewed_by: User,
    request: Any | None = None,
) -> Vendor:
    return get_vendor_service().approve_application(db, application_id, reviewed_by, request)


def reject_application(
    db: Session,
    application_id: uuid.UUID,
    reviewed_by: User,
    reason: str | None = None,
    request: Any | None = None,
) -> VendorApplication:
    return get_vendor_service().reject_application(db, application_id, reviewed_by, reason, request)


def update_vendor(
    db: Session,
    vendor_id: uuid.UUID,
    body: VendorUpdateRequest,
    current_user: User,
    request: Any | None = None,
) -> Vendor:
    return get_vendor_service().update(db, vendor_id, body, current_user, request)
