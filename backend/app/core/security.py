"""Security utilities for JWT token creation and validation."""

from datetime import datetime, timedelta, timezone
from typing import Any
import secrets
import hashlib

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

from .config import settings


def create_access_token(user: dict[str, Any]) -> str:
    """
    Create a JWT access token for a user.

    Args:
        user: User object with id, username, email, role

    Returns:
        Encoded JWT token string

    Raises:
        RuntimeError: If PyJWT is not installed and auth is enabled
    """
    if not JWT_AVAILABLE and settings.auth_enabled:
        raise RuntimeError(
            "PyJWT is required for authentication. Install with: pip install PyJWT>=2.8.0"
        )

    if not settings.auth_enabled:
        # Auth disabled, return placeholder
        return "auth_disabled"

    expires_delta = timedelta(minutes=settings.auth_access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "sub": user.get("id") or user.get("user_id"),
        "username": user.get("username"),
        "email": user.get("email"),
        "role": user.get("role"),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.auth_secret_key, algorithm=settings.auth_algorithm
    )
    return encoded_jwt


def create_refresh_token() -> str:
    """
    Create a secure random refresh token.

    Returns:
        Cryptographically secure random token string
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """
    Hash a token for secure storage.

    Args:
        token: Token string to hash

    Returns:
        SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
        RuntimeError: If PyJWT is not installed and auth is enabled
    """
    if not JWT_AVAILABLE and settings.auth_enabled:
        raise RuntimeError(
            "PyJWT is required for authentication. Install with: pip install PyJWT>=2.8.0"
        )

    if not settings.auth_enabled:
        # Auth disabled, return placeholder
        return {"sub": "anonymous", "username": settings.default_author, "role": "administrator"}

    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[settings.auth_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise


def generate_state_token() -> str:
    """
    Generate a state token for CSRF protection during OAuth flow.

    Returns:
        Cryptographically secure random state token
    """
    return secrets.token_urlsafe(32)


def verify_state_token(state: str) -> bool:
    """
    Verify a state token from OAuth callback.

    In a production system, this should check against a stored value
    (e.g., in session or Redis). For now, we accept any non-empty state.

    Args:
        state: State token to verify

    Returns:
        True if valid, False otherwise

    TODO: Implement proper state storage and verification
    """
    return bool(state and len(state) > 10)
