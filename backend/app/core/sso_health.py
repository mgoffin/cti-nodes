"""SSO health check and fallback handling."""

from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import settings
from .oidc_providers import get_oidc_provider


# Health check cache
_sso_health_cache = {
    "healthy": True,
    "last_check": None,
    "cache_duration_seconds": 60,
}


async def check_sso_health() -> bool:
    """
    Check if SSO provider is accessible.

    Results are cached for 1 minute to avoid excessive health checks.

    Returns:
        True if SSO provider is healthy, False otherwise
    """
    if not HTTPX_AVAILABLE:
        # If httpx not available, assume healthy (it's already in requirements.txt)
        return True

    if not settings.auth_enabled:
        # Auth disabled, no need to check
        return True

    now = datetime.now()

    # Return cached result if recent
    if (
        _sso_health_cache["last_check"]
        and now - _sso_health_cache["last_check"]
        < timedelta(seconds=_sso_health_cache["cache_duration_seconds"])
    ):
        return _sso_health_cache["healthy"]

    # Check SSO provider health
    is_healthy = True
    try:
        base_url = settings.effective_sso_base_url
        if not base_url:
            # No SSO configured, assume healthy
            is_healthy = True
        else:
            provider = get_oidc_provider(settings.sso_provider, base_url)
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    provider.authorization_endpoint, follow_redirects=False
                )
                # 200 or 302 are both normal for auth endpoints
                is_healthy = response.status_code in [200, 302, 400, 401]
    except Exception:
        # Any exception means SSO is unreachable
        is_healthy = False

    # Update cache
    _sso_health_cache["healthy"] = is_healthy
    _sso_health_cache["last_check"] = now

    return is_healthy


def invalidate_sso_health_cache():
    """Force next health check to run (useful for testing)."""
    _sso_health_cache["last_check"] = None


class SSOFallbackMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle SSO outages based on configured fallback mode.

    When SSO is down:
    - Mode "require_sso": Block write operations, return 503
    - Mode "fallback_anonymous": Allow operations, tag request for fallback tracking
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and check SSO health for write operations.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        if not settings.auth_enabled:
            # Auth disabled, pass through
            return await call_next(request)

        # Check if this is a write operation
        is_write = request.method in ["POST", "PUT", "DELETE", "PATCH"]

        # Check if this is an auth endpoint (allow these through)
        is_auth_endpoint = request.url.path.startswith("/api/auth/")

        # Check if this is a health check endpoint (allow through)
        is_health_endpoint = request.url.path == "/api/health"

        if is_write and not is_auth_endpoint and not is_health_endpoint:
            sso_healthy = await check_sso_health()

            if not sso_healthy:
                if settings.sso_fallback_mode == "require_sso":
                    # Block write operations
                    raise HTTPException(
                        status_code=503,
                        detail="Authentication service unavailable. Platform is temporarily read-only.",
                    )
                elif settings.sso_fallback_mode == "fallback_anonymous":
                    # Allow operation but mark request for fallback tracking
                    request.state.sso_fallback = True
                    request.state.sso_fallback_timestamp = datetime.now(
                        timezone.utc
                    ).isoformat()

        response = await call_next(request)
        return response
