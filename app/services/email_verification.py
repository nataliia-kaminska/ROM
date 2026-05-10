from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from app.core.config import settings
from app.core.security import create_url_token, hash_token
from app.db.models import User
from app.services.email_delivery import get_email_provider


def issue_email_verification(user: User) -> str:
    token = create_url_token()
    user.email_verification_token_hash = hash_token(token)
    user.email_verification_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        hours=settings.email_verification_expire_hours
    )
    return token


def verification_link(token: str) -> str:
    return f"{settings.frontend_base_url.rstrip('/')}/verify-email?{urlencode({'token': token})}"


def send_verification_email(user: User, token: str) -> None:
    link = verification_link(token)
    body = (
        f"Hi {user.full_name or user.email},\n\n"
        "Confirm your Research Opportunity Matcher account by opening this link:\n\n"
        f"{link}\n\n"
        f"This link expires in {settings.email_verification_expire_hours} hours.\n"
        "If you did not create this account, you can ignore this email."
    )
    get_email_provider().send(user.email, "Confirm your Research Matcher email", body)


def verify_email_token(user: User, token: str) -> bool:
    if not user.email_verification_token_hash:
        return False
    if user.email_verification_token_hash != hash_token(token):
        return False
    expires_at = user.email_verification_expires_at
    if expires_at and expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        return False
    user.email_verified = True
    user.email_verification_token_hash = ""
    user.email_verification_expires_at = None
    return True
