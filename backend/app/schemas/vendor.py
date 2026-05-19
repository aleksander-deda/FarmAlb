from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class VendorApplicationRequest(BaseModel):
    business_name: str
    type: str           # FARM | WINERY | AGRITOURISM | RESTAURANT
    region: str | None = None
    contact_email: EmailStr
    website: str | None = None
    description: str | None = None


class VendorApplicationResponse(BaseModel):
    id: UUID
    business_name: str
    type: str
    status: str
    submitted_at: datetime | None

    model_config = {"from_attributes": True}


class VendorResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    type: str
    status: str
    region: str | None
    address: str | None
    lat: float | None
    lng: float | None
    tier: str
    website: str | None
    phone: str | None
    email: str | None
    approved_at: datetime | None

    model_config = {"from_attributes": True}


class VendorUpdateRequest(BaseModel):
    name: str | None = None
    region: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    description: str | None = None