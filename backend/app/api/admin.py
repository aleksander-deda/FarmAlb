from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_superadmin
from app.db.session import get_db
from app.models.identity import User
from app.models.platform import AuditLog

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/audit-logs")
def list_audit_logs(
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    actor_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if actor_id:
        q = q.filter(AuditLog.actor_id == actor_id)

    total = q.count()
    logs = q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [
            {
                "id": str(log.id),
                "actor_id": str(log.actor_id) if log.actor_id else None,
                "actor_type": log.actor_type,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "before_state": log.before_state,
                "after_state": log.after_state,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }