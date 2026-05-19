"""
Audit logging utility.

Usage anywhere in a service:
    from app.utils.audit import audit_log

    audit_log(
        db=db,
        actor=current_user,
        action="booking.cancel",
        resource_type="Booking",
        resource_id=booking.id,
        before={"status": "confirmed"},
        after={"status": "cancelled"},
        request=request,   # optional FastAPI Request for IP/UA
    )
"""
import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.platform import AuditLog
from app.models.identity import User


def _serialize(data: Any) -> str | None:
    if data is None:
        return None
    try:
        return json.dumps(data, default=str)
    except Exception:
        return str(data)


def audit_log(
    db: Session,
    action: str,
    resource_type: str,
    actor: User | None = None,
    resource_id: uuid.UUID | None = None,
    before: dict | None = None,
    after: dict | None = None,
    request: Any | None = None,   # FastAPI Request object
    actor_type: str = "user",
) -> AuditLog:
    """
    Creates and persists an audit log entry.
    Commits independently so logs are never lost even if
    the main transaction rolls back.
    """
    ip_address = None
    user_agent = None

    if request is not None:
        try:
            # Handle reverse proxy forwarding
            forwarded = request.headers.get("x-forwarded-for")
            ip_address = forwarded.split(",")[0].strip() if forwarded else request.client.host
            user_agent = request.headers.get("user-agent")
        except Exception:
            pass

    log = AuditLog(
        actor_id=actor.id if actor else None,
        actor_type=actor_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before_state=_serialize(before),
        after_state=_serialize(after),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    db.flush()   # write immediately without full commit
    return log