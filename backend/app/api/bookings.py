from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_superadmin
from app.db.session import get_db
from app.models.catalog import ExperienceSlot, Experience
from app.models.identity import User
from app.schemas.booking import (
    BookingCreateRequest, BookingCancelRequest,
    BookingResponse, BookingDetailResponse,
)
from app.services.booking_service import (
    create_booking, get_booking, list_my_bookings,
    list_vendor_bookings, cancel_booking, confirm_booking,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=201)
def book(
    body: BookingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_booking(db, body, current_user)


@router.get("/me", response_model=list[BookingResponse])
def my_bookings(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_my_bookings(db, current_user, status)


@router.get("/vendor/{vendor_id}", response_model=list[BookingResponse])
def vendor_bookings(
    vendor_id: UUID,
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_vendor_bookings(db, vendor_id, current_user, status)


@router.get("/{booking_id}", response_model=BookingDetailResponse)
def booking_detail(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = get_booking(db, booking_id, current_user)

    # Enrich with slot and experience data
    slot = db.query(ExperienceSlot).filter(
        ExperienceSlot.id == booking.slot_id
    ).first()
    experience = db.query(Experience).filter(
        Experience.id == slot.experience_id
    ).first() if slot else None

    response = BookingDetailResponse.model_validate(booking)
    response.vendor_id = experience.vendor_id if experience else None
    response.experience_title = experience.title if experience else None
    response.slot_starts_at = slot.starts_at if slot else None
    response.slot_ends_at = slot.ends_at if slot else None
    response.payment_status = booking.payment.status if booking.payment else None
    return response


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel(
    booking_id: UUID,
    body: BookingCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cancel_booking(db, booking_id, body, current_user)


@router.post("/{booking_id}/confirm", response_model=BookingResponse)
def confirm(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    return confirm_booking(db, booking_id, current_user)