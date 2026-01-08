"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, Request
from typing import Callable, AsyncGenerator
import aiosqlite

from .config import settings
from .security import verify_token


async def get_db_dependency() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    FastAPI dependency for database connection.

    Yields:
        Database connection
    """
    db = await aiosqlite.connect(settings.database_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


class User:
    """User model for dependency injection."""

    def __init__(
        self,
        id: str,
        username: str,
        email: str | None,
        display_name: str,
        role: str,
        is_active: bool = True,
    ):
        self.id = id
        self.username = username
        self.email = email
        self.display_name = display_name
        self.role = role
        self.is_active = is_active


def get_anonymous_user() -> User:
    """
    Create an anonymous user with admin privileges when auth is disabled.

    Returns:
        User object with administrator role
    """
    return User(
        id="anonymous",
        username=settings.default_author,
        email=None,
        display_name=settings.default_author,
        role="administrator",
        is_active=True,
    )


async def get_user_by_id(db, user_id: str) -> User | None:
    """
    Get a user from the database by ID.

    Args:
        db: Database connection
        user_id: User ID to lookup

    Returns:
        User object if found, None otherwise
    """
    cursor = await db.execute(
        "SELECT id, username, email, display_name, role, is_active FROM users WHERE id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()

    if not row:
        return None

    return User(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        display_name=row["display_name"],
        role=row["role"],
        is_active=bool(row["is_active"]),
    )


async def get_current_user(request: Request, db=Depends(get_db_dependency)) -> User:
    """
    Get current user from JWT token in httpOnly cookie.

    Returns configured default author if auth is disabled.

    Args:
        request: FastAPI request object
        db: Database connection

    Returns:
        User object

    Raises:
        HTTPException: If not authenticated or user not found
    """
    if not settings.auth_enabled:
        return get_anonymous_user()

    # Extract JWT from httpOnly cookie
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = verify_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    user = await get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user is active (not deactivated).

    Args:
        current_user: Current user from get_current_user

    Returns:
        Active user object

    Raises:
        HTTPException: If user account is disabled
    """
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User account is disabled")
    return current_user


def require_role(*allowed_roles: str) -> Callable:
    """
    Dependency factory to require specific roles.

    Args:
        *allowed_roles: Role names that are allowed (e.g., "administrator", "analyst")

    Returns:
        Dependency function that checks user role

    Example:
        @router.get("/admin-only", dependencies=[Depends(require_role("administrator"))])
    """

    async def check_role(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user.role}' cannot perform this action. Required: {', '.join(allowed_roles)}",
            )
        return user

    return check_role


def can_modify_resource(user: User, resource_author: str) -> bool:
    """
    Check if user can modify a resource based on ownership and role.

    Args:
        user: User attempting to modify
        resource_author: Username of resource owner

    Returns:
        True if user can modify, False otherwise
    """
    # Administrators can modify anything
    if user.role == "administrator":
        return True

    # Analysts can only modify their own content
    if user.role == "analyst" and resource_author == user.username:
        return True

    # Read-only users cannot modify anything
    return False


def require_modify_permission(resource_author: str) -> Callable:
    """
    Dependency factory to check modify permission on a specific resource.

    Args:
        resource_author: Username of the resource owner

    Returns:
        Dependency function that checks modification permission

    Raises:
        HTTPException: If user doesn't have permission to modify
    """

    async def check_permission(user: User = Depends(get_current_active_user)) -> User:
        if not can_modify_resource(user, resource_author):
            raise HTTPException(
                status_code=403, detail="You can only modify your own content"
            )
        return user

    return check_permission
