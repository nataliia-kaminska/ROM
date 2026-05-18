from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import ResearcherProfile, User, UserRole
from app.db.session import get_db
from app.application.use_cases.ingestion import ExternalSourceIngestionUseCase, GrantsGovIngestionUseCase
from app.application.use_cases.recommendations import ListRecommendationsUseCase


bearer_scheme = HTTPBearer(auto_error=False)


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("typ", "access") != "access":
            raise ValueError("Invalid token type")
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user(user: User | None = Depends(get_optional_current_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def ensure_profile_access(
    profile: ResearcherProfile | None,
    current_user: User | None,
) -> ResearcherProfile:
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.user_id is not None and (current_user is None or current_user.id != profile.user_id):
        raise HTTPException(status_code=403, detail="Profile access denied")
    return profile


def get_recommendation_use_case(db: Session = Depends(get_db)) -> ListRecommendationsUseCase:
    return ListRecommendationsUseCase(db)


def get_grants_gov_ingestion_use_case(db: Session = Depends(get_db)) -> GrantsGovIngestionUseCase:
    return GrantsGovIngestionUseCase(db)


def get_external_source_ingestion_use_case(db: Session = Depends(get_db)) -> ExternalSourceIngestionUseCase:
    return ExternalSourceIngestionUseCase(db)
