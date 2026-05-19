from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator


VALID_TYPES = {"PERCENTAGE", "FIXED_AMOUNT"}
VALID_APPLIES_TO = {"ALL", "BOOKINGS", "ORDERS"}


class PromotionCreateRequest(BaseModel):
    code: str
    type: str
    value: float
    applies_to: str = "ALL"
    max_uses: int | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.upper().strip()
        if not v:
            raise ValueError("Code cannot be empty")
        if len(v) > 60:
            raise ValueError("Code too long")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_TYPES:
            raise ValueError(f"Must be one of: {', '.join(VALID_TYPES)}")
        return v

    @field_validator("applies_to")
    @classmethod
    def validate_applies_to(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_APPLIES_TO:
            raise ValueError(f"Must be one of: {', '.join(VALID_APPLIES_TO)}")
        return v

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Value must be greater than 0")
        return v

    @field_validator("max_uses")
    @classmethod
    def validate_max_uses(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("Max uses must be at least 1")
        return v


class PromotionUpdateRequest(BaseModel):
    value: float | None = None
    max_uses: int | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v and v not in {"active", "disabled"}:
            raise ValueError("Must be one of: active, disabled")
        return v


class PromotionResponse(BaseModel):
    id: UUID
    vendor_id: UUID
    code: str
    type: str
    value: float
    applies_to: str
    max_uses: int | None
    used_count: int
    valid_from: datetime | None
    valid_until: datetime | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PromotionValidateRequest(BaseModel):
    code: str
    vendor_id: UUID
    amount: float   # subtotal to validate discount against


class PromotionValidateResponse(BaseModel):
    valid: bool
    discount_amount: float
    message: str