"""
Dev seed — creates default roles, permissions, and dummy users.
Run once after: alembic upgrade head

Usage:
    python -m app.db.seed
"""
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.identity import Role, Permission, RolePermission, User
from app.core.security import hash_password  # we'll create this next


# ── Roles ──────────────────────────────────────────────────────────────────
ROLES = [
    {"code": "SUPER_ADMIN",   "name": "Super Admin",   "description": "Full platform access"},
    {"code": "VENDOR_ADMIN",  "name": "Vendor Admin",  "description": "Manages a single vendor"},
    {"code": "VENDOR_STAFF",  "name": "Vendor Staff",  "description": "Limited vendor access"},
    {"code": "GUEST",         "name": "Guest",         "description": "Registered customer"},
]

# ── Permissions ────────────────────────────────────────────────────────────
PERMISSIONS = [
    # bookings
    {"code": "BOOKING_READ",    "resource": "booking",  "action": "read"},
    {"code": "BOOKING_CREATE",  "resource": "booking",  "action": "create"},
    {"code": "BOOKING_CANCEL",  "resource": "booking",  "action": "cancel"},
    # products
    {"code": "PRODUCT_READ",    "resource": "product",  "action": "read"},
    {"code": "PRODUCT_CREATE",  "resource": "product",  "action": "create"},
    {"code": "PRODUCT_UPDATE",  "resource": "product",  "action": "update"},
    {"code": "PRODUCT_DELETE",  "resource": "product",  "action": "delete"},
    # vendors
    {"code": "VENDOR_READ",     "resource": "vendor",   "action": "read"},
    {"code": "VENDOR_APPROVE",  "resource": "vendor",   "action": "approve"},
    {"code": "VENDOR_SUSPEND",  "resource": "vendor",   "action": "suspend"},
    # payouts
    {"code": "PAYOUT_READ",     "resource": "payout",   "action": "read"},
    {"code": "PAYOUT_APPROVE",  "resource": "payout",   "action": "approve"},
    # users
    {"code": "USER_READ",       "resource": "user",     "action": "read"},
    {"code": "USER_SUSPEND",    "resource": "user",     "action": "suspend"},
]

# ── Role → Permission mapping ──────────────────────────────────────────────
ROLE_PERMISSIONS = {
    "SUPER_ADMIN":  [p["code"] for p in PERMISSIONS],  # all
    "VENDOR_ADMIN": ["BOOKING_READ", "BOOKING_CANCEL", "PRODUCT_READ", "PRODUCT_CREATE",
                     "PRODUCT_UPDATE", "PRODUCT_DELETE", "PAYOUT_READ"],
    "VENDOR_STAFF": ["BOOKING_READ", "PRODUCT_READ", "PRODUCT_UPDATE"],
    "GUEST":        ["BOOKING_READ", "BOOKING_CREATE", "BOOKING_CANCEL", "PRODUCT_READ"],
}

# ── Dummy users ────────────────────────────────────────────────────────────
USERS = [
    {
        "full_name": "Admin User",
        "email": "admin@farmalb.al",
        "password": "admin1234",
        "status": "active",
        "is_superuser": True,
        "role_code": "SUPER_ADMIN",
    },
    {
        "full_name": "Vendor Besa",
        "email": "besa@farmalb.al",
        "password": "vendor1234",
        "status": "active",
        "is_superuser": False,
        "role_code": "VENDOR_ADMIN",
    },
    {
        "full_name": "Guest Ardit",
        "email": "ardit@farmalb.al",
        "password": "guest1234",
        "status": "active",
        "is_superuser": False,
        "role_code": "GUEST",
    },
]


def seed(db: Session) -> None:
    # 1. Roles
    role_map: dict[str, Role] = {}
    for r in ROLES:
        role = db.query(Role).filter_by(code=r["code"]).first()
        if not role:
            role = Role(**r)
            db.add(role)
        role_map[r["code"]] = role
    db.flush()

    # 2. Permissions
    perm_map: dict[str, Permission] = {}
    for p in PERMISSIONS:
        perm = db.query(Permission).filter_by(code=p["code"]).first()
        if not perm:
            perm = Permission(**p)
            db.add(perm)
        perm_map[p["code"]] = perm
    db.flush()

    # 3. Role → Permission links
    for role_code, perm_codes in ROLE_PERMISSIONS.items():
        role = role_map[role_code]
        existing = {rp.permission_id for rp in role.role_permissions}
        for perm_code in perm_codes:
            perm = perm_map[perm_code]
            if perm.id not in existing:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db.flush()

    # 4. Users
    from app.models.identity import UserRole
    for u in USERS:
        user = db.query(User).filter_by(email=u["email"]).first()
        if not user:
            user = User(
                full_name=u["full_name"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                status=u["status"],
                is_superuser=u["is_superuser"],
            )
            db.add(user)
            db.flush()
            db.add(UserRole(user_id=user.id, role_id=role_map[u["role_code"]].id))
            print(f"  Created user: {u['email']}  role: {u['role_code']}")
        else:
            print(f"  Skipped (exists): {u['email']}")

    db.commit()
    print("Seed complete.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()