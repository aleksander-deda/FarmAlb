from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_superadmin
from app.db.session import get_db
from app.models.identity import User
from app.models.catalog import Vendor
from app.models.platform import VendorApplication
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.vendor import (
    VendorApplicationRequest, VendorApplicationResponse,
    VendorResponse, VendorUpdateRequest,
)
from app.services.vendor_service import (
    apply_as_vendor, approve_application,
    reject_application, update_vendor,
)

router = APIRouter(prefix="/vendors", tags=["Vendors"])


# ── Public ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[VendorResponse])
def list_vendors(
    type: str | None = None,
    region: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Vendor).filter(Vendor.status == "active")
    if type:
        q = q.filter(Vendor.type == type.upper())
    if region:
        q = q.filter(Vendor.region.ilike(f"%{region}%"))
    return q.all()


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.status == "active",
    ).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


# ── Authenticated ──────────────────────────────────────────────────────────────

@router.post("/apply", response_model=VendorApplicationResponse, status_code=201)
def apply(
    body: VendorApplicationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return apply_as_vendor(db, current_user, body)


@router.get("/my/application", response_model=VendorApplicationResponse)
def my_application(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = db.query(VendorApplication).filter(
        VendorApplication.applicant_id == current_user.id
    ).order_by(VendorApplication.created_at.desc()).first()

    if not application:
        raise HTTPException(status_code=404, detail="No application found")
    return application


@router.patch("/{vendor_id}", response_model=VendorResponse)
def update(
    vendor_id: UUID,
    body: VendorUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_vendor(db, vendor_id, body, current_user)


# ── Superadmin only ────────────────────────────────────────────────────────────

@router.get("/admin/applications", response_model=list[VendorApplicationResponse])
def list_applications(
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    q = db.query(VendorApplication)
    if status:
        q = q.filter(VendorApplication.status == status)
    return q.order_by(VendorApplication.created_at.desc()).all()


@router.post("/admin/applications/{application_id}/approve", response_model=VendorResponse)
def approve(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    return approve_application(db, application_id, current_user)


@router.post("/admin/applications/{application_id}/reject")
def reject(
    application_id: UUID,
    reason: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    return reject_application(db, application_id, current_user, reason)