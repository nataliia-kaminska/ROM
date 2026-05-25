from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from jwt import InvalidTokenError

from app.core.config import settings


logger = logging.getLogger(__name__)


class OrcidOAuthError(RuntimeError):
    """Raised when the ORCID OAuth flow cannot be completed safely."""


def create_orcid_state() -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.oauth_state_expire_minutes)
    payload = {"purpose": "orcid_oauth", "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def validate_orcid_state(state: str) -> None:
    try:
        payload = jwt.decode(state, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError as exc:
        raise OrcidOAuthError("Invalid or expired ORCID sign-in state") from exc
    if payload.get("purpose") != "orcid_oauth":
        raise OrcidOAuthError("Invalid ORCID sign-in state")


def build_authorization_url(state: str) -> str:
    query = urlencode(
        {
            "client_id": settings.orcid_client_id,
            "response_type": "code",
            "scope": settings.orcid_oauth_scope,
            "redirect_uri": settings.orcid_redirect_uri,
            "state": state,
        }
    )
    return f"{settings.orcid_authorize_url}?{query}"


def exchange_authorization_code(code: str) -> dict[str, Any]:
    logger.info("exchanging ORCID authorization code")
    try:
        response = httpx.post(
            settings.orcid_token_url,
            data={
                "client_id": settings.orcid_client_id,
                "client_secret": settings.orcid_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.orcid_redirect_uri,
            },
            headers={"Accept": "application/json"},
            timeout=20,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("ORCID token exchange failed: %s", exc)
        raise OrcidOAuthError("ORCID sign-in failed while exchanging the authorization code") from exc
    payload = response.json()
    if not payload.get("orcid"):
        raise OrcidOAuthError("ORCID did not return an authenticated iD")
    return payload


def orcid_placeholder_email(orcid_id: str) -> str:
    return f"orcid-{orcid_id.replace('-', '')}@example.com"


def email_from_token(payload: dict[str, Any]) -> str | None:
    direct_email = str(payload.get("email") or "").strip().lower()
    if direct_email:
        return direct_email
    emails = payload.get("emails")
    if isinstance(emails, list):
        for item in emails:
            if isinstance(item, dict):
                value = str(item.get("email") or item.get("value") or "").strip().lower()
                if value:
                    return value
            elif isinstance(item, str) and item.strip():
                return item.strip().lower()
    return None


def display_name_from_token(payload: dict[str, Any]) -> str:
    name = str(payload.get("name") or "").strip()
    if name:
        return name
    return f"ORCID Researcher {payload['orcid']}"
