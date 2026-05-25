import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.rate_limit import rate_limit
from app.core.security import create_access_token, hash_password, hash_token, verify_password
from app.core.config import settings
from app.db.models import ResearcherProfile, User
from app.db.session import get_db
from app.integrations.orcid.client import OrcidClient
from app.integrations.orcid.mapper import extract_profile_payload
from app.integrations.orcid.service import import_orcid_profile as import_orcid_profile_service
from app.schemas.orcid import OrcidImportRequest
from app.schemas.auth import AuthProviderConfigRead, TokenRead, UserAccountUpdate, UserLogin, UserPasswordChange, UserRead, UserRegister, UserRegisterRead, UserVerifyEmail
from app.services.email_verification import issue_email_verification, send_verification_email, verify_email_token
from app.services.orcid_oauth import (
    OrcidOAuthError,
    build_authorization_url,
    create_orcid_state,
    display_name_from_token,
    email_from_token,
    exchange_authorization_code,
    orcid_placeholder_email,
    validate_orcid_state,
)
from app.services.refresh_tokens import issue_refresh_token, revoke_refresh_token, verify_refresh_token


router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/providers", response_model=AuthProviderConfigRead)
def read_auth_providers() -> AuthProviderConfigRead:
    return AuthProviderConfigRead(
        orcid_oauth_enabled=bool(settings.orcid_oauth_enabled and settings.orcid_client_id and settings.orcid_client_secret)
    )


@router.post("/register", response_model=UserRegisterRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit("auth_register"))])
def register(payload: UserRegister, response: Response, db: Session = Depends(get_db)) -> UserRegisterRead:
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
    _set_refresh_cookie(response, issue_refresh_token(user))
    db.commit()
    return UserRegisterRead(message="Registration successful.", email=user.email, access_token=token, user=user)


@router.post("/verify-email", response_model=UserRead, dependencies=[Depends(rate_limit("auth_verify_email"))])
def verify_email(payload: UserVerifyEmail, db: Session = Depends(get_db)) -> UserRead:
    token_hash = hash_token(payload.token)
    user = db.query(User).filter(User.email_verification_token_hash == token_hash).first()
    if user is None or not verify_email_token(user, payload.token):
        raise HTTPException(status_code=400, detail="Email verification link is invalid or expired")
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenRead, dependencies=[Depends(rate_limit("auth_login"))])
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)) -> TokenRead:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not user.password_login_enabled or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    if settings.email_verification_required and not user.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email before signing in")

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    _set_refresh_cookie(response, issue_refresh_token(user))
    db.commit()
    return TokenRead(access_token=token, user=user)


@router.post("/refresh", response_model=TokenRead, dependencies=[Depends(rate_limit("auth_refresh"))])
def refresh_access_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=settings.auth_refresh_cookie_name),
    db: Session = Depends(get_db),
) -> TokenRead:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token is missing")
    token_hash = hash_token(refresh_token)
    user = db.query(User).filter(User.refresh_token_hash == token_hash).first()
    if user is None or not user.is_active or not verify_refresh_token(user, refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token is invalid or expired")
    next_refresh_token = issue_refresh_token(user)
    access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    _set_refresh_cookie(response, next_refresh_token)
    db.commit()
    db.refresh(user)
    return TokenRead(access_token=access_token, user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    revoke_refresh_token(current_user)
    db.commit()
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/orcid/start", dependencies=[Depends(rate_limit("auth_orcid_start"))])
def start_orcid_sign_in() -> RedirectResponse:
    if not settings.orcid_oauth_enabled or not settings.orcid_client_id or not settings.orcid_client_secret:
        raise HTTPException(status_code=503, detail="ORCID sign-in is not configured")
    state = create_orcid_state()
    authorization_url = build_authorization_url(state)
    logger.info("starting ORCID OAuth sign-in")
    return RedirectResponse(authorization_url, status_code=status.HTTP_302_FOUND)


@router.get("/orcid/callback", dependencies=[Depends(rate_limit("auth_orcid_callback"))])
def complete_orcid_sign_in(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if error:
        return _redirect_to_frontend_error(f"ORCID sign-in was cancelled: {error}")
    if not code or not state:
        return _redirect_to_frontend_error("ORCID sign-in response is missing required values")
    try:
        validate_orcid_state(state)
        token_payload = exchange_authorization_code(code)
    except OrcidOAuthError as exc:
        return _redirect_to_frontend_error(str(exc))

    orcid_id = str(token_payload["orcid"])
    preferred_email = email_from_token(token_payload) or _public_orcid_email(orcid_id)
    user = db.query(User).filter(User.orcid_id == orcid_id).first()
    if user is None:
        email = _unique_orcid_email(db, orcid_id, preferred_email)
        user = User(
            email=email,
            hashed_password="",
            full_name=display_name_from_token(token_payload),
            auth_provider="orcid",
            orcid_id=orcid_id,
            password_login_enabled=False,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("created ORCID OAuth user user_id=%s orcid_id=%s", user.id, orcid_id)
    else:
        if not user.is_active:
            return _redirect_to_frontend_error("This account is inactive")
        user.email_verified = True
        user.auth_provider = user.auth_provider or "orcid"
        db.commit()
        db.refresh(user)
        logger.info("completed ORCID OAuth sign-in user_id=%s orcid_id=%s", user.id, orcid_id)

    _ensure_orcid_profile(db, user, orcid_id)
    access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    refresh_token = issue_refresh_token(user)
    db.commit()
    query = urlencode({"token": access_token})
    response = RedirectResponse(f"{settings.frontend_base_url}/orcid-callback?{query}", status_code=status.HTTP_302_FOUND)
    _set_refresh_cookie(response, refresh_token)
    return response


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return current_user


@router.put("/me", response_model=UserRead, dependencies=[Depends(rate_limit("auth_update_me"))])
def update_me(
    payload: UserAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    if current_user.auth_provider == "orcid":
        raise HTTPException(status_code=403, detail="Name and email are managed by ORCID for this account")
    next_email = payload.email.lower()
    existing = db.query(User).filter(User.email == next_email, User.id != current_user.id).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    email_changed = next_email != current_user.email
    current_user.full_name = payload.full_name
    current_user.email = next_email
    for profile in db.query(ResearcherProfile).filter(ResearcherProfile.user_id == current_user.id).all():
        profile.full_name = payload.full_name
        profile.email = next_email
    if email_changed and settings.email_verification_required:
        current_user.email_verified = False
        verification_token = issue_email_verification(current_user)
        send_verification_email(current_user, verification_token)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password", response_model=UserRead, dependencies=[Depends(rate_limit("auth_update_password"))])
def update_password(
    payload: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    if not current_user.password_login_enabled:
        raise HTTPException(status_code=403, detail="Password login is disabled for this account")
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    db.refresh(current_user)
    return current_user


def _unique_orcid_email(db: Session, orcid_id: str, preferred_email: str | None = None) -> str:
    email = (preferred_email or orcid_placeholder_email(orcid_id)).lower()
    if db.query(User).filter(User.email == email).first() is None:
        return email
    suffix = 2
    while True:
        candidate = f"orcid-{orcid_id.replace('-', '')}+{suffix}@example.com"
        if db.query(User).filter(User.email == candidate).first() is None:
            return candidate
        suffix += 1


def _public_orcid_email(orcid_id: str) -> str | None:
    try:
        record = OrcidClient().read_public_record(orcid_id)
        extracted = extract_profile_payload(orcid_id, record)
        return extracted.get("email")
    except Exception:
        logger.info("ORCID public record did not provide an email or could not be read orcid_id=%s", orcid_id)
        return None


def _ensure_orcid_profile(db: Session, user: User, orcid_id: str) -> None:
    existing = (
        db.query(ResearcherProfile)
        .filter((ResearcherProfile.user_id == user.id) | (ResearcherProfile.orcid_id == orcid_id))
        .first()
    )
    if existing is not None:
        if existing.user_id is None:
            existing.user_id = user.id
            db.commit()
            logger.info("linked existing ORCID profile profile_id=%s user_id=%s", existing.id, user.id)
        return

    try:
        result = import_orcid_profile_service(
            db,
            OrcidImportRequest(
                orcid_id=orcid_id,
                email=user.email,
                career_stage="phd",
                disciplines=[],
                preferred_countries=[],
            ),
            user,
        )
        logger.info("created ORCID profile on first OAuth login profile_id=%s user_id=%s", result.profile.id, user.id)
    except Exception:
        db.rollback()
        logger.exception("failed to auto-create ORCID profile on OAuth login user_id=%s orcid_id=%s", user.id, orcid_id)


def _redirect_to_frontend_error(message: str) -> RedirectResponse:
    logger.warning("ORCID OAuth sign-in failed: %s", message)
    query = urlencode({"error": message})
    return RedirectResponse(f"{settings.frontend_base_url}/orcid-callback?{query}", status_code=status.HTTP_302_FOUND)


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.auth_refresh_cookie_name,
        token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.auth_refresh_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/auth",
    )
