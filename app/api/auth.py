from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, hash_token, verify_password
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import TokenRead, UserLogin, UserRead, UserRegister, UserRegisterRead, UserVerifyEmail
from app.services.email_verification import issue_email_verification, send_verification_email, verify_email_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRegisterRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> UserRegisterRead:
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        email_verified=not settings.email_verification_required,
    )
    verification_token = issue_email_verification(user) if settings.email_verification_required else ""
    db.add(user)
    db.commit()
    db.refresh(user)
    if settings.email_verification_required:
        send_verification_email(user, verification_token)
        return UserRegisterRead(message="Registration successful. Check your email to verify your account.", email=user.email)
    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    return UserRegisterRead(message="Registration successful.", email=user.email, access_token=token, user=user)


@router.post("/verify-email", response_model=UserRead)
def verify_email(payload: UserVerifyEmail, db: Session = Depends(get_db)) -> UserRead:
    token_hash = hash_token(payload.token)
    user = db.query(User).filter(User.email_verification_token_hash == token_hash).first()
    if user is None or not verify_email_token(user, payload.token):
        raise HTTPException(status_code=400, detail="Email verification link is invalid or expired")
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenRead)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenRead:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    if settings.email_verification_required and not user.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email before signing in")

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    return TokenRead(access_token=token, user=user)


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return current_user
