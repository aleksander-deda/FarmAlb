from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.identity import User
from app.schemas.catalog import (
    ExperienceCreateRequest, ExperienceUpdateRequest,
    ExperienceResponse, ExperienceDetailResponse,
    SlotCreateRequest, SlotUpdateRequest, SlotResponse,
    ProductCreateRequest, ProductUpdateRequest, ProductResponse,
)
from app.services.catalog_service import (
    create_experience, get_experience, list_experiences,
    update_experience, delete_experience,
    create_slot, list_slots, update_slot, delete_slot,
    create_product, get_product, list_products,
    update_product, delete_product,
)

router = APIRouter(tags=["Catalog"])


# ── Experiences ────────────────────────────────────────────────────────────────

@router.get("/vendors/{vendor_id}/experiences", response_model=list[ExperienceResponse])
def list_vendor_experiences(
    vendor_id: UUID,
    include_drafts: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    return list_experiences(db, vendor_id, include_drafts)


@router.post("/vendors/{vendor_id}/experiences", response_model=ExperienceResponse, status_code=201)
def create_vendor_experience(
    vendor_id: UUID,
    body: ExperienceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_experience(db, vendor_id, body, current_user)


@router.get("/experiences/{experience_id}", response_model=ExperienceDetailResponse)
def get_experience_detail(
    experience_id: UUID,
    db: Session = Depends(get_db),
):
    experience = get_experience(db, experience_id)
    slots = list_slots(db, experience_id, only_open=True)
    response = ExperienceDetailResponse.model_validate(experience)
    response.slots = slots
    return response


@router.patch("/experiences/{experience_id}", response_model=ExperienceResponse)
def update_vendor_experience(
    experience_id: UUID,
    body: ExperienceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_experience(db, experience_id, body, current_user)


@router.delete("/experiences/{experience_id}", status_code=204)
def delete_vendor_experience(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_experience(db, experience_id, current_user)


# ── Slots ──────────────────────────────────────────────────────────────────────

@router.get("/experiences/{experience_id}/slots", response_model=list[SlotResponse])
def list_experience_slots(
    experience_id: UUID,
    only_open: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    return list_slots(db, experience_id, only_open)


@router.post("/experiences/{experience_id}/slots", response_model=SlotResponse, status_code=201)
def create_experience_slot(
    experience_id: UUID,
    body: SlotCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_slot(db, experience_id, body, current_user)


@router.patch("/slots/{slot_id}", response_model=SlotResponse)
def update_experience_slot(
    slot_id: UUID,
    body: SlotUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_slot(db, slot_id, body, current_user)


@router.delete("/slots/{slot_id}", status_code=204)
def delete_experience_slot(
    slot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_slot(db, slot_id, current_user)


# ── Products ───────────────────────────────────────────────────────────────────

@router.get("/vendors/{vendor_id}/products", response_model=list[ProductResponse])
def list_vendor_products(
    vendor_id: UUID,
    category: str | None = Query(default=None),
    include_drafts: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    return list_products(db, vendor_id, category, include_drafts)


@router.post("/vendors/{vendor_id}/products", response_model=ProductResponse, status_code=201)
def create_vendor_product(
    vendor_id: UUID,
    body: ProductCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_product(db, vendor_id, body, current_user)


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product_detail(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    return get_product(db, product_id)


@router.patch("/products/{product_id}", response_model=ProductResponse)
def update_vendor_product(
    product_id: UUID,
    body: ProductUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_product(db, product_id, body, current_user)


@router.delete("/products/{product_id}", status_code=204)
def delete_vendor_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_product(db, product_id, current_user)