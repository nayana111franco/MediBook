"""Authentication routes for MediBook."""
hello testing

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.user import TokenResponse, UserCreate, UserLogin, UserPublic, CurrentUser, UserUpdate
from utils.auth import authenticate_user, get_password_hash, issue_token_for_user, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _build_public_user(user: User) -> UserPublic:
    """Create a UserPublic schema from a model."""
    return UserPublic.from_orm(user)


@router.post("/register", response_model=TokenResponse)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    """Register a new user and return a token."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.role == "doctor" and not payload.specialization:
        payload.specialization = "General"

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        specialization=payload.specialization,
        bio=payload.bio,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(**issue_token_for_user(user))


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate user and return access token."""
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(**issue_token_for_user(user))


@router.get("/me", response_model=CurrentUser)
def get_me(current_user: User = Depends(get_current_user)) -> CurrentUser:
    """Return current user data."""
    return CurrentUser(user=_build_public_user(current_user))


@router.get("/status")
def auth_status() -> dict:
    """Return auth service status."""
    return {"status": "ok", "service": "auth"}


@router.get("/validate", response_model=UserPublic)
def validate_token(current_user: User = Depends(get_current_user)) -> UserPublic:
    """Validate a token and return user data."""
    return _build_public_user(current_user)


@router.put("/profile", response_model=UserPublic)
def update_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPublic:
    """Update current user's profile fields."""
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.bio is not None:
        current_user.bio = payload.bio
    db.commit()
    db.refresh(current_user)
    return _build_public_user(current_user)


@router.post("/logout")
def logout() -> dict:
    """Client-side logout placeholder endpoint."""
    return {"status": "ok", "message": "Logged out on client"}


@router.get("/roles")
def list_roles() -> dict:
    """Return supported roles."""
    return {"roles": ["patient", "doctor"]}


@router.get("/me/role")
def my_role(current_user: User = Depends(get_current_user)) -> dict:
    """Return the current user's role."""
    return {"role": current_user.role}
