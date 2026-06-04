from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_superadmin
from app.schemas.response import ApiResponse
from app.utils.response import success_response
from app.db.session import get_db
from app.models.catalog import ExperienceSlot, Experience
from app.models.identity import User
from app.schemas.booking import (
    BookingCreateRequest, BookingCancelRequest,
    BookingResponse, BookingDetailResponse,
)
from app.services.booking_service import get_booking_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=ApiResponse[BookingResponse], status_code=201)
def book(
    body: BookingCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = get_booking_service().create(db, body, current_user, request)
    return success_response(data=booking)


@router.get("/me", response_model=ApiResponse[list[BookingResponse]])
def my_bookings(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(data=get_booking_service().list_my(db, current_user, status))


@router.get("/vendor/{vendor_id}", response_model=ApiResponse[list[BookingResponse]])
def vendor_bookings(
    vendor_id: UUID,
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(data=get_booking_service().list_vendor(db, vendor_id, current_user, status))


@router.get("/{booking_id}", response_model=ApiResponse[BookingDetailResponse])
def booking_detail(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = get_booking_service().get(db, booking_id, current_user)

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
    return success_response(data=response)


@router.post("/{booking_id}/cancel", response_model=ApiResponse[BookingResponse])
def cancel(
    booking_id: UUID,
    body: BookingCancelRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = get_booking_service().cancel(db, booking_id, body, current_user, request)
    return success_response(data=booking)


@router.post("/{booking_id}/confirm", response_model=ApiResponse[BookingResponse])
def confirm(
    booking_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    booking = get_booking_service().confirm(db, booking_id, current_user, request)
    return success_response(data=booking)