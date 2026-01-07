"""Rate limiting middleware using slowapi."""

from typing import Callable

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    # Provide dummy implementations when slowapi is not installed
    class Limiter:
        def __init__(self, **kwargs):
            pass

        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

    def get_remote_address(request):
        return "127.0.0.1"

    class RateLimitExceeded(Exception):
        pass

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from .config import settings


def get_limiter() -> Limiter:
    """
    Get the rate limiter instance.

    Returns:
        Limiter configured with remote address as key
    """
    return Limiter(key_func=get_remote_address)


limiter = get_limiter()


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Handle rate limit exceeded errors.

    Args:
        request: FastAPI request
        exc: Rate limit exception

    Returns:
        JSON response with 429 status
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please try again later.",
        },
    )


def get_rate_limit_for_endpoint(endpoint_type: str) -> str:
    """
    Get rate limit string for a specific endpoint type.

    Args:
        endpoint_type: Type of endpoint (auth, api, create, search)

    Returns:
        Rate limit string (e.g., "5/minute")
    """
    limits = {
        "auth": settings.rate_limit_auth,
        "api": settings.rate_limit_api,
        "create": "30/minute",  # Node creation
        "search": "60/minute",  # Search queries
    }
    return limits.get(endpoint_type, settings.rate_limit_api)


def check_slowapi_available() -> bool:
    """
    Check if slowapi is available.

    Returns:
        True if slowapi is installed, False otherwise
    """
    return SLOWAPI_AVAILABLE
