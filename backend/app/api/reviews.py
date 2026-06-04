from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_superadmin
from app.db.session import get_db
from app.models.identity import User
from app.schemas.review import (
    ReviewCreateRequest, ReviewUpdateRequest,
    ReviewModerateRequest, ReviewResponse,
    VendorReplyRequest, VendorRatingStats,
)
from app.services.review_service import get_review_service

router = APIRouter(prefix="/reviews", tags=["Reviews"])


# ── Public ─────────────────────────────────────────────────────────────────────

@router.get("/vendors/{vendor_id}", response_model=list[ReviewResponse])
def vendor_reviews(
    vendor_id: UUID,
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    return _enrich(get_review_service().list_vendor(db, vendor_id, status, current_user), db)


@router.get("/vendors/{vendor_id}/stats", response_model=VendorRatingStats)
def vendor_stats(
    vendor_id: UUID,
    db: Session = Depends(get_db),
):
    return get_review_service().get_vendor_rating_stats(db, vendor_id)


# ── Authenticated ──────────────────────────────────────────────────────────────

@router.post("", response_model=ReviewResponse, status_code=201)
def create(
    body: ReviewCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = get_review_service().create(db, body, current_user, request)
    return _enrich_one(review, db)


@router.get("/me", response_model=list[ReviewResponse])
def my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _enrich(get_review_service().list_my(db, current_user), db)


@router.get("/{review_id}", response_model=ReviewResponse)
def detail(
    review_id: UUID,
    db: Session = Depends(get_db),
):
    return _enrich_one(get_review_service().get(db, review_id), db)


@router.patch("/{review_id}", response_model=ReviewResponse)
def update(
    review_id: UUID,
    body: ReviewUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _enrich_one(get_review_service().update(db, review_id, body, current_user, request), db)


@router.post("/{review_id}/reply", response_model=ReviewResponse)
def reply(
    review_id: UUID,
    body: VendorReplyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _enrich_one(get_review_service().reply(db, review_id, body, current_user, request), db)


@router.delete("/{review_id}/reply", response_model=ReviewResponse)
def remove_reply(
    review_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _enrich_one(get_review_service().delete_reply(db, review_id, current_user, request), db)


# ── Superadmin ─────────────────────────────────────────────────────────────────

@router.post("/{review_id}/moderate", response_model=ReviewResponse)
def moderate(
    review_id: UUID,
    body: ReviewModerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    return _enrich_one(get_review_service().moderate(db, review_id, body, current_user, request), db)


# ── Enrichment helpers ─────────────────────────────────────────────────────────
# Attaches reviewer_name to responses without exposing full user data

def _enrich_one(review, db: Session) -> dict:
    from app.models.identity import User as UserModel
    user = db.query(UserModel).filter(UserModel.id == review.user_id).first()
    data = ReviewResponse.model_validate(review).model_dump()
    data["reviewer_name"] = user.full_name if user else "Anonymous"
    return data


def _enrich(reviews: list, db: Session) -> list[dict]:
    return [_enrich_one(r, db) for r in reviews]