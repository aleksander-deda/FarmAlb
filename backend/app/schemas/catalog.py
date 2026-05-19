from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator


# ── Experience ─────────────────────────────────────────────────────────────────

VALID_EXPERIENCE_TYPES = {"TASTING", "COOKING_CLASS", "FARM_STAY", "TOUR", "HARVEST"}
VALID_STATUSES = {"draft", "active", "archived"}


class ExperienceCreateRequest(BaseModel):
    title: str
    description: str | None = None
    type: str
    duration_minutes: int | None = None
    capacity: int
    base_price: float
    currency: str = "EUR"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_EXPERIENCE_TYPES:
            raise ValueError(f"Must be one of: {', '.join(VALID_EXPERIENCE_TYPES)}")
        return v

    @field_validator("capacity")
    @classmethod
    def validate_capacity(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Capacity must be at least 1")
        return v

    @field_validator("base_price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v


class ExperienceUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    duration_minutes: int | None = None
    capacity: int | None = None
    base_price: float | None = None
    currency: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v and v not in VALID_STATUSES:
            raise ValueError(f"Must be one of: {', '.join(VALID_STATUSES)}")
        return v


class ExperienceResponse(BaseModel):
    id: UUID
    vendor_id: UUID
    title: str
    description: str | None
    type: str
    duration_minutes: int | None
    capacity: int
    base_price: float
    currency: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Experience Slots ───────────────────────────────────────────────────────────

class SlotCreateRequest(BaseModel):
    starts_at: datetime
    ends_at: datetime | None = None
    available_spots: int

    @field_validator("available_spots")
    @classmethod
    def validate_spots(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Must have at least 1 available spot")
        return v


class SlotUpdateRequest(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    available_spots: int | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v and v not in {"open", "full", "cancelled"}:
            raise ValueError("Must be one of: open, full, cancelled")
        return v


class SlotResponse(BaseModel):
    id: UUID
    experience_id: UUID
    starts_at: datetime
    ends_at: datetime | None
    available_spots: int
    status: str

    model_config = {"from_attributes": True}


class ExperienceDetailResponse(ExperienceResponse):
    slots: list[SlotResponse] = []


# ── Product ────────────────────────────────────────────────────────────────────

VALID_CATEGORIES = {"WINE", "OLIVE_OIL", "CHEESE", "RAKIA", "HONEY", "OTHER"}
VALID_PRODUCT_STATUSES = {"draft", "active", "archived", "out_of_stock"}


class ProductCreateRequest(BaseModel):
    name: str
    description: str | None = None
    category: str
    price: float
    currency: str = "EUR"
    stock_qty: int = 0
    shippable: bool = True
    weight_grams: int | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Must be one of: {', '.join(VALID_CATEGORIES)}")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v

    @field_validator("stock_qty")
    @classmethod
    def validate_stock(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Stock cannot be negative")
        return v


class ProductUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    stock_qty: int | None = None
    shippable: bool | None = None
    weight_grams: int | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v and v not in VALID_PRODUCT_STATUSES:
            raise ValueError(f"Must be one of: {', '.join(VALID_PRODUCT_STATUSES)}")
        return v


class ProductResponse(BaseModel):
    id: UUID
    vendor_id: UUID
    name: str
    description: str | None
    category: str
    price: float
    currency: str
    stock_qty: int
    shippable: bool
    weight_grams: int | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}