"""
Booking business logic.

Flow:
  1. Guest picks a slot
  2. System validates availability, applies promotion if any
  3. Calculates subtotal, platform fee, total
  4. Creates booking (status=pending) + payment record (status=pending)
  5. Decrements slot available_spots
  6. On payment confirmation → booking becomes confirmed
  7. On cancellation → spots are restored
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.core.constants import AuditAction
from app.models.catalog import ExperienceSlot, Experience, Promotion
from app.models.commerce import Booking, Payment
from app.models.identity import User, UserRole, Role
from app.schemas.booking import BookingCreateRequest, BookingCancelRequest
from app.utils.audit import AuditLogger
from app.services.base import BaseService


class BookingService(BaseService):
    """Service for managing bookings."""

    def _apply_promotion(
        self,
        db: Session,
        promotion_code: str,
        vendor_id: uuid.UUID,
        subtotal: float,
    ) -> tuple[Promotion, float]:
        """
        Apply a promotion code to a booking.
        Returns (promotion, discount_amount).
        Raises HTTPException if invalid or expired.
        """
        now = datetime.now(timezone.utc)
        promo = db.query(Promotion).filter(
            Promotion.code == promotion_code,
            Promotion.vendor_id == vendor_id,
            Promotion.status == "active",
            Promotion.applies_to.in_(["ALL", "BOOKINGS"]),
        ).first()

        if not promo:
            raise HTTPException(status_code=404, detail="Promotion code not found or not applicable")

        if promo.valid_from and promo.valid_from > now:
            raise HTTPException(status_code=422, detail="Promotion is not active yet")

        if promo.valid_until and promo.valid_until < now:
            raise HTTPException(status_code=422, detail="Promotion has expired")

        if promo.max_uses and promo.used_count >= promo.max_uses:
            raise HTTPException(status_code=422, detail="Promotion has reached its usage limit")

        if promo.type == "PERCENTAGE":
            discount = self.round_amount(subtotal * float(promo.value) / 100)
        else:  # FIXED_AMOUNT
            discount = self.round_amount(min(float(promo.value), subtotal))

        return promo, discount

    def _calculate_totals(
        self,
        subtotal: float,
        discount: float,
        commission_rate: float,
    ) -> tuple[float, float, float]:
        """Calculate discounted subtotal, platform fee, and total.
        Returns (discounted_subtotal, platform_fee, total).
        """
        discounted = self.round_amount(subtotal - discount)
        fee = self.round_amount(discounted * commission_rate)
        total = self.round_amount(discounted + fee)
        return discounted, fee, total

    def create(
        self,
        db: Session,
        body: BookingCreateRequest,
        current_user: User,
        request: Any | None = None,
    ) -> Booking:
        """Create a new booking for a guest."""
        # 1. Load slot and experience
        slot = db.query(ExperienceSlot).filter(
            ExperienceSlot.id == body.slot_id,
        ).with_for_update().first()  # lock row to prevent race conditions

        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")

        if slot.status != "open":
            raise HTTPException(status_code=409, detail=f"Slot is {slot.status}")

        if slot.starts_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=422, detail="Slot has already started or passed")

        if slot.available_spots < body.guests:
            raise HTTPException(
                status_code=409,
                detail=f"Not enough spots. Available: {slot.available_spots}, requested: {body.guests}",
            )

        experience = db.query(Experience).filter(
            Experience.id == slot.experience_id
        ).first()

        if experience.status != "active":
            raise HTTPException(status_code=409, detail="Experience is not available for booking")

        # 2. Calculate subtotal (price × guests)
        subtotal = self.round_amount(float(experience.base_price) * body.guests)

        # 3. Apply promotion if provided
        promotion = None
        discount_amount = 0.0

        if body.promotion_code:
            promotion, discount_amount = self._apply_promotion(
                db, body.promotion_code, experience.vendor_id, subtotal
            )

        # 4. Calculate totals
        _, platform_fee, total = self._calculate_totals(
            subtotal, discount_amount, settings.platform_booking_commission_rate
        )

        # 5. Create booking
        booking = Booking(
            user_id=current_user.id,
            slot_id=slot.id,
            promotion_id=promotion.id if promotion else None,
            guests=body.guests,
            subtotal=subtotal,
            discount_amount=discount_amount,
            platform_fee=platform_fee,
            total=total,
            currency=experience.currency,
            status="pending",
        )
        db.add(booking)
        db.flush()

        # 6. Create pending payment record
        payment = Payment(
            booking_id=booking.id,
            provider="stripe",
            amount=total,
            currency=experience.currency,
            status="pending",
            initiated_at=datetime.now(timezone.utc),
        )
        db.add(payment)

        # 7. Decrement available spots
        slot.available_spots -= body.guests
        if slot.available_spots == 0:
            slot.status = "full"

        # 8. Increment promotion usage
        if promotion:
            promotion.used_count += 1

        db.commit()
        db.refresh(booking)
        AuditLogger.log(
            db=db,
            action=AuditAction.BOOKING_CREATE,
            resource_type="Booking",
            actor=current_user,
            resource_id=booking.id,
            after={
                "status": booking.status,
                "total": float(booking.total),
                "guests": booking.guests,
            },
            request=request,
        )
        return booking

    def get(
        self,
        db: Session,
        booking_id: uuid.UUID,
        current_user: User,
    ) -> Booking:
        """Get a booking by ID with authorization checks."""
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # Owner or superadmin or vendor admin can view
        if booking.user_id != current_user.id and not current_user.is_superuser:
            slot = db.query(ExperienceSlot).filter(
                ExperienceSlot.id == booking.slot_id
            ).first()
            experience = db.query(Experience).filter(
                Experience.id == slot.experience_id
            ).first()
            is_vendor = db.query(UserRole).join(Role).filter(
                UserRole.user_id == current_user.id,
                UserRole.vendor_id == experience.vendor_id,
                Role.code.in_(["VENDOR_ADMIN", "VENDOR_STAFF"]),
            ).first()
            if not is_vendor:
                raise HTTPException(status_code=403, detail="Not authorized")

        return booking

    def list_my(
        self,
        db: Session,
        current_user: User,
        status: str | None = None,
    ) -> list[Booking]:
        """List bookings for the current user."""
        q = db.query(Booking).filter(Booking.user_id == current_user.id)
        if status:
            q = q.filter(Booking.status == status)
        return q.order_by(Booking.created_at.desc()).all()

    def list_for_vendor(
        self,
        db: Session,
        vendor_id: uuid.UUID,
        current_user: User,
        status: str | None = None,
    ) -> list[Booking]:
        """List bookings for a vendor with authorization checks."""
        # Verify access
        if not current_user.is_superuser:
            is_vendor = db.query(UserRole).join(Role).filter(
                UserRole.user_id == current_user.id,
                UserRole.vendor_id == vendor_id,
                Role.code.in_(["VENDOR_ADMIN", "VENDOR_STAFF"]),
            ).first()
            if not is_vendor:
                raise HTTPException(status_code=403, detail="Not authorized")

        # Join through slot → experience → vendor
        q = (
            db.query(Booking)
            .join(ExperienceSlot, Booking.slot_id == ExperienceSlot.id)
            .join(Experience, ExperienceSlot.experience_id == Experience.id)
            .filter(Experience.vendor_id == vendor_id)
        )
        if status:
            q = q.filter(Booking.status == status)
        return q.order_by(Booking.created_at.desc()).all()

    def cancel(
        self,
        db: Session,
        booking_id: uuid.UUID,
        body: BookingCancelRequest,
        current_user: User,
        request: Any | None = None,
    ) -> Booking:
        """Cancel an existing booking."""
        booking = db.query(Booking).filter(
            Booking.id == booking_id
        ).with_for_update().first()

        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        if booking.status not in ("pending", "confirmed"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot cancel a booking with status '{booking.status}'",
            )

        # Only the guest or superadmin can cancel
        if booking.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Restore slot spots
        slot = db.query(ExperienceSlot).filter(
            ExperienceSlot.id == booking.slot_id
        ).with_for_update().first()

        if slot and slot.starts_at > datetime.now(timezone.utc):
            slot.available_spots += booking.guests
            if slot.status == "full":
                slot.status = "open"

        # Restore promotion usage
        if booking.promotion_id:
            promo = db.query(Promotion).filter(
                Promotion.id == booking.promotion_id
            ).first()
            if promo and promo.used_count > 0:
                promo.used_count -= 1

        # Update booking
        booking.status = "cancelled"
        booking.cancellation_reason = body.reason
        booking.cancelled_at = datetime.now(timezone.utc)
        booking.cancelled_by = current_user.id

        # Update payment
        if booking.payment:
            booking.payment.status = "refunded"
            booking.payment.refunded_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(booking)
        AuditLogger.log(
            db=db,
            action=AuditAction.BOOKING_CANCEL,
            resource_type="Booking",
            actor=current_user,
            resource_id=booking.id,
            before={"status": "pending"},
            after={"status": booking.status, "reason": body.reason},
            request=request,
        )
        return booking

    def confirm(
        self,
        db: Session,
        booking_id: uuid.UUID,
        current_user: User,
        request: Any | None = None,
    ) -> Booking:
        """
        Confirm a booking after successful payment.
        Called after successful payment confirmation from Stripe webhook.
        For now exposed as a manual endpoint for testing.
        """
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        if booking.status != "pending":
            raise HTTPException(status_code=409, detail=f"Booking is already {booking.status}")

        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Superadmin only")

        booking.status = "confirmed"

        if booking.payment:
            booking.payment.status = "confirmed"
            booking.payment.confirmed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(booking)
        AuditLogger.log(
            db=db,
            action=AuditAction.BOOKING_CONFIRM,
            resource_type="Booking",
            actor=current_user,
            resource_id=booking.id,
            before={"status": "pending"},
            after={"status": booking.status},
            request=request,
        )
        return booking


# Singleton instance for backward compatibility
_booking_service = None


def get_booking_service() -> BookingService:
    """Get or create the booking service instance."""
    global _booking_service
    if _booking_service is None:
        _booking_service = BookingService()
    return _booking_service


# Keep old function-based API for gradual migration
def create_booking(
    db: Session,
    body: BookingCreateRequest,
    current_user: User,
    request: Any | None = None,
) -> Booking:
    """Deprecated: Use BookingService.create() instead."""
    return get_booking_service().create(db, body, current_user, request)


def get_booking(
    db: Session,
    booking_id: uuid.UUID,
    current_user: User,
) -> Booking:
    """Deprecated: Use BookingService.get() instead."""
    return get_booking_service().get(db, booking_id, current_user)


def list_my_bookings(
    db: Session,
    current_user: User,
    status: str | None = None,
) -> list[Booking]:
    """Deprecated: Use BookingService.list_my() instead."""
    return get_booking_service().list_my(db, current_user, status)


def list_vendor_bookings(
    db: Session,
    vendor_id: uuid.UUID,
    current_user: User,
    status: str | None = None,
) -> list[Booking]:
    """Deprecated: Use BookingService.list_for_vendor() instead."""
    return get_booking_service().list_for_vendor(db, vendor_id, current_user, status)


def cancel_booking(
    db: Session,
    booking_id: uuid.UUID,
    body: BookingCancelRequest,
    current_user: User,
    request: Any | None = None,
) -> Booking:
    """Deprecated: Use BookingService.cancel() instead."""
    return get_booking_service().cancel(db, booking_id, body, current_user, request)


def confirm_booking(
    db: Session,
    booking_id: uuid.UUID,
    current_user: User,
    request: Any | None = None,
) -> Booking:
    """Deprecated: Use BookingService.confirm() instead."""
    return get_booking_service().confirm(db, booking_id, current_user, request)
