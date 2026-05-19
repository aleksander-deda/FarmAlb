from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator


class BookingCreateRequest(BaseModel):
    slot_id: UUID
    guests: int = 1
    promotion_code: str | None = None

    @field_validator("guests")
    @classmethod
    def validate_guests(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Must book at least 1 guest")
        if v > 50:
            raise ValueError("Cannot book more than 50 guests at once")
        return v


class BookingCancelRequest(BaseModel):
    reason: str | None = None


class BookingResponse(BaseModel):
    id: UUID
    slot_id: UUID
    vendor_id: UUID | None = None
    experience_title: str | None = None
    guests: int
    subtotal: float
    discount_amount: float
    platform_fee: float
    total: float
    currency: str
    status: str
    booked_at: datetime
    cancelled_at: datetime | None

    model_config = {"from_attributes": True}


class BookingDetailResponse(BookingResponse):
    slot_starts_at: datetime | None = None
    slot_ends_at: datetime | None = None
    cancellation_reason: str | None = None
    payment_status: str | None = None