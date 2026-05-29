from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.constants import AuditAction
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token, create_refresh_token,
    decode_token, hash_password, verify_password,
)
from app.db.session import get_db
from app.models.identity import User, UserRole
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.schemas.response import ApiResponse
from app.utils.audit import AuditLogger
from app.utils.response import success_response

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=body.full_name,
        email=body.email,
        hashed_password=hash_password(body.password),
        locale=body.locale,
        status="active",  # in prod: "pending_verification" + send email
    )
    db.add(user)
    db.flush()

    # Assign default GUEST role
    from app.models.identity import Role
    guest_role = db.query(Role).filter_by(code="GUEST").first()
    if guest_role:
        db.add(UserRole(user_id=user.id, role_id=guest_role.id))

    db.commit()
    AuditLogger.log(
        db=db,
        action=AuditAction.AUTH_REGISTER,
        resource_type="User",
        actor=user,
        resource_id=user.id,
        after={"status": user.status, "email": user.email},
        request=request,
    )
    return success_response(
        data={"message": "Registration successful", "user_id": str(user.id)},
        message="Registration successful",
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status != "active":
        raise HTTPException(status_code=403, detail=f"Account is {user.status}")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token_response = TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
    audit = AuditLogger.log(
        db=db,
        action=AuditAction.AUTH_LOGIN,
        resource_type="User",
        actor=user,
        resource_id=user.id,
        after={"status": user.status},
        request=request,
    )
    print(f"Audit log created with ID: {audit.id} for user {user.email}")
    print(f"User {user.email} logged in successfully")
    return success_response(data=token_response)


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
def refresh(body: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
        user_id = uuid.UUID(payload["sub"])   # ← convert here too
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()   # ← and here
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="User not found or inactive")

    token_response = TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
    AuditLogger.log(
        db=db,
        action=AuditAction.AUTH_REFRESH,
        resource_type="User",
        actor=user,
        resource_id=user.id,
        after={"status": user.status},
        request=request,
    )
    return success_response(data=token_response)


@router.get("/me", response_model=ApiResponse[UserResponse])
def me(current_user: User = Depends(get_current_user)):
    data = {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "locale": current_user.locale,
        "status": current_user.status,
        "is_superuser": current_user.is_superuser,
    }
    return success_response(data=data)