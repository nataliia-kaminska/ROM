from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.security import create_url_token, hash_token
from app.db.models import User


def issue_refresh_token(user: User) -> str:
    token = create_url_token()
    user.refresh_token_hash = hash_token(token)
    user.refresh_token_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.refresh_token_expire_days)
    return token


def verify_refresh_token(user: User, token: str) -> bool:
    if not user.refresh_token_hash or user.refresh_token_hash != hash_token(token):
        return False
    if user.refresh_token_expires_at is None:
        return False
    return user.refresh_token_expires_at > datetime.utcnow()


def revoke_refresh_token(user: User) -> None:
    user.refresh_token_hash = ""
    user.refresh_token_expires_at = None
