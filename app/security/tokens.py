from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

import jwt

from app.core.config import settings
from app.core.exceptions import AppException


def create_access_token(user_id: UUID) -> str:
    """Create a short-lived signed JWT for authenticated API requests."""

    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> UUID:
    """Decode and validate an access token, returning the user id."""

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise AppException(
            "Invalid or expired access token.",
            status_code=401,
            error_code="invalid_token",
        ) from exc

    if payload.get("type") != "access" or not payload.get("sub"):
        raise AppException("Invalid access token.", status_code=401, error_code="invalid_token")

    return UUID(payload["sub"])


def create_refresh_token() -> str:
    """Create an opaque refresh token.

    The client receives the raw token. The database stores only a SHA-256 hash
    so a database leak does not reveal usable refresh tokens.
    """

    return token_urlsafe(64)


def hash_refresh_token(refresh_token: str) -> str:
    return sha256(refresh_token.encode("utf-8")).hexdigest()


def refresh_token_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
