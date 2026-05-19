from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator


class CartItem(BaseModel):
    product_id: UUID
    quantity: int

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        if v > 100:
            raise ValueError("Cannot order more than 100 of one item")
        return v


class OrderCreateRequest(BaseModel):
    vendor_id: UUID
    items: list[CartItem]
    shipping_address: str | None = None
    promotion_code: str | None = None

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list[CartItem]) -> list[CartItem]:
        if not v:
            raise ValueError("Order must have at least one item")
        # No duplicate product_ids
        ids = [item.product_id for item in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate products in order — combine quantities instead")
        return v


class OrderCancelRequest(BaseModel):
    reason: str | None = None


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name_snapshot: str
    quantity: int
    unit_price: float
    line_total: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: UUID
    vendor_id: UUID
    subtotal: float
    discount_amount: float
    platform_fee: float
    shipping_cost: float
    total: float
    currency: str
    status: str
    shipping_address: str | None
    tracking_number: str | None
    placed_at: datetime
    shipped_at: datetime | None
    delivered_at: datetime | None
    cancelled_at: datetime | None

    model_config = {"from_attributes": True}


class OrderDetailResponse(OrderResponse):
    items: list[OrderItemResponse] = []
    payment_status: str | None = None


class OrderShipRequest(BaseModel):
    tracking_number: str


class TrackingUpdateRequest(BaseModel):
    tracking_number: str