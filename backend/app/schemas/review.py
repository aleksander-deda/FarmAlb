from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator


class ReviewCreateRequest(BaseModel):
    booking_id: UUID
    rating: int
    body: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str | None) -> str | None:
        if v is not None and len(v.strip()) < 10:
            raise ValueError("Review body must be at least 10 characters")
        if v is not None and len(v) > 2000:
            raise ValueError("Review body cannot exceed 2000 characters")
        return v.strip() if v else None


class ReviewUpdateRequest(BaseModel):
    body: str | None = None
    rating: int | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int | None) -> int | None:
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str | None) -> str | None:
        if v is not None and len(v.strip()) < 10:
            raise ValueError("Review body must be at least 10 characters")
        if v is not None and len(v) > 2000:
            raise ValueError("Review body cannot exceed 2000 characters")
        return v.strip() if v else None


class ReviewModerateRequest(BaseModel):
    action: str          # approve | reject
    reason: str | None = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in {"approve", "reject"}:
            raise ValueError("Action must be 'approve' or 'reject'")
        return v


class ReviewResponse(BaseModel):
    id: UUID
    vendor_id: UUID
    booking_id: UUID
    reviewer_name: str | None = None
    rating: int
    body: str | None
    verified_visit: bool
    status: str
    vendor_reply: str | None = None
    vendor_replied_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VendorReplyRequest(BaseModel):
    body: str

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Reply must be at least 5 characters")
        if len(v) > 1000:
            raise ValueError("Reply cannot exceed 1000 characters")
        return v


class VendorRatingStats(BaseModel):
    vendor_id: UUID
    total_reviews: int
    average_rating: float
    rating_breakdown: dict[int, int]   # {5: 10, 4: 5, 3: 2, 2: 1, 1: 0}