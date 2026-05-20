"""
Review business logic.

Rules:
- Only guests who have a COMPLETED booking can leave a review.
- One review per booking (enforced by unique constraint on booking_id).
- Reviews start as 'pending' and must be approved by platform before publishing.
- Vendors can reply to published reviews only.
- Guests can edit their review only while it's still pending.
- Platform can approve or reject any pending review.
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.catalog import Experience, ExperienceSlot
from app.models.commerce import Booking, Review
from app.models.identity import User, UserRole, Role
from app.schemas.review import (
    ReviewCreateRequest, ReviewUpdateRequest,
    ReviewModerateRequest, VendorReplyRequest,
)
from app.utils.audit import audit_log


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_booking_vendor(db: Session, booking: Booking) -> uuid.UUID:
    """Resolves vendor_id from a booking through slot → experience."""
    slot = db.query(ExperienceSlot).filter(
        ExperienceSlot.id == booking.slot_id
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Booking slot not found")
    experience = db.query(Experience).filter(
        Experience.id == slot.experience_id
    ).first()
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    return experience.vendor_id


def _is_vendor_member(db: Session, user: User, vendor_id: uuid.UUID) -> bool:
    if user.is_superuser:
        return True
    return bool(
        db.query(UserRole).join(Role).filter(
            UserRole.user_id == user.id,
            UserRole.vendor_id == vendor_id,
            Role.code.in_(["VENDOR_ADMIN", "VENDOR_STAFF"]),
        ).first()
    )


# ── Service functions ──────────────────────────────────────────────────────────

def create_review(
    db: Session,
    body: ReviewCreateRequest,
    current_user: User,
    request=None,
) -> Review:
    # 1. Load and validate booking
    booking = db.query(Booking).filter(
        Booking.id == body.booking_id,
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only review your own bookings",
        )

    if booking.status != "confirmed":
        raise HTTPException(
            status_code=409,
            detail="You can only review confirmed bookings",
        )

    # 2. Check no existing review for this booking
    existing = db.query(Review).filter(
        Review.booking_id == body.booking_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already reviewed this booking",
        )

    # 3. Resolve vendor
    vendor_id = _get_booking_vendor(db, booking)

    # 4. Create review
    review = Review(
        user_id=current_user.id,
        booking_id=body.booking_id,
        vendor_id=vendor_id,
        rating=body.rating,
        body=body.body,
        verified_visit=True,
        status="pending",
    )
    db.add(review)
    db.flush()

    audit_log(
        db=db,
        actor=current_user,
        action="review.create",
        resource_type="Review",
        resource_id=review.id,
        after={
            "rating": body.rating,
            "vendor_id": str(vendor_id),
            "booking_id": str(body.booking_id),
        },
        request=request,
    )

    db.commit()
    db.refresh(review)
    return review


def get_review(db: Session, review_id: uuid.UUID) -> Review:
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


def list_vendor_reviews(
    db: Session,
    vendor_id: uuid.UUID,
    status: str | None = None,
    current_user: User | None = None,
) -> list[Review]:
    q = db.query(Review).filter(Review.vendor_id == vendor_id)

    # Guests and public only see published reviews
    # Vendor staff and superadmin can filter by status
    if current_user and (current_user.is_superuser or _is_vendor_member(db, current_user, vendor_id)):
        if status:
            q = q.filter(Review.status == status)
    else:
        q = q.filter(Review.status == "published")

    return q.order_by(Review.created_at.desc()).all()


def list_my_reviews(
    db: Session,
    current_user: User,
) -> list[Review]:
    return (
        db.query(Review)
        .filter(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )


def update_review(
    db: Session,
    review_id: uuid.UUID,
    body: ReviewUpdateRequest,
    current_user: User,
    request=None,
) -> Review:
    review = get_review(db, review_id)

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if review.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Only pending reviews can be edited. "
                   "Contact support to update a published review.",
        )

    before = {"rating": review.rating, "body": review.body}

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(review, field, value)

    audit_log(
        db=db,
        actor=current_user,
        action="review.update",
        resource_type="Review",
        resource_id=review.id,
        before=before,
        after=body.model_dump(exclude_unset=True),
        request=request,
    )

    db.commit()
    db.refresh(review)
    return review


def moderate_review(
    db: Session,
    review_id: uuid.UUID,
    body: ReviewModerateRequest,
    current_user: User,
    request=None,
) -> Review:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superadmin only")

    review = get_review(db, review_id)

    if review.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Review is already {review.status}",
        )

    before = {"status": review.status}

    if body.action == "approve":
        review.status = "published"
        review.rejection_reason = None
        action = "review.approve"
    else:
        review.status = "rejected"
        review.rejection_reason = body.reason
        action = "review.reject"

    audit_log(
        db=db,
        actor=current_user,
        action=action,
        resource_type="Review",
        resource_id=review.id,
        before=before,
        after={"status": review.status, "reason": body.reason},
        request=request,
    )

    db.commit()
    db.refresh(review)
    return review


def reply_to_review(
    db: Session,
    review_id: uuid.UUID,
    body: VendorReplyRequest,
    current_user: User,
    request=None,
) -> Review:
    review = get_review(db, review_id)

    if review.status != "published":
        raise HTTPException(
            status_code=409,
            detail="Can only reply to published reviews",
        )

    if not _is_vendor_member(db, current_user, review.vendor_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    if review.vendor_reply:
        raise HTTPException(
            status_code=409,
            detail="A reply already exists. Delete it first to re-reply.",
        )

    before = {"vendor_reply": None}
    review.vendor_reply = body.body
    review.vendor_replied_at = datetime.now(timezone.utc)

    audit_log(
        db=db,
        actor=current_user,
        action="review.reply",
        resource_type="Review",
        resource_id=review.id,
        before=before,
        after={"vendor_reply": body.body},
        request=request,
    )

    db.commit()
    db.refresh(review)
    return review


def delete_reply(
    db: Session,
    review_id: uuid.UUID,
    current_user: User,
    request=None,
) -> Review:
    review = get_review(db, review_id)

    if not _is_vendor_member(db, current_user, review.vendor_id) and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not review.vendor_reply:
        raise HTTPException(status_code=404, detail="No reply to delete")

    before = {"vendor_reply": review.vendor_reply}
    review.vendor_reply = None
    review.vendor_replied_at = None

    audit_log(
        db=db,
        actor=current_user,
        action="review.delete_reply",
        resource_type="Review",
        resource_id=review.id,
        before=before,
        after={"vendor_reply": None},
        request=request,
    )

    db.commit()
    db.refresh(review)
    return review


def get_vendor_rating_stats(
    db: Session,
    vendor_id: uuid.UUID,
) -> dict:
    """Aggregate rating stats for a vendor's public profile."""
    reviews = (
        db.query(Review)
        .filter(
            Review.vendor_id == vendor_id,
            Review.status == "published",
        )
        .all()
    )

    total = len(reviews)
    if total == 0:
        return {
            "vendor_id": vendor_id,
            "total_reviews": 0,
            "average_rating": 0.0,
            "rating_breakdown": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        }

    breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_score = 0
    for r in reviews:
        breakdown[r.rating] += 1
        total_score += r.rating

    return {
        "vendor_id": str(vendor_id),
        "total_reviews": total,
        "average_rating": round(total_score / total, 2),
        "rating_breakdown": breakdown,
    }