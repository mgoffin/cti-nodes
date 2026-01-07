"""User management API endpoints."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..core.config import settings
from ..core.database import get_db
from ..core.dependencies import get_current_active_user, require_role, User
from ..core.audit import log_audit

router = APIRouter(prefix="/users", tags=["users"])


# Pydantic models
class UserProfileUpdate(BaseModel):
    """Schema for updating user profile preferences."""

    display_name: str | None = None
    avatar_url: str | None = None
    theme: str | None = None  # 'light', 'dark', 'system'


class UserUpdate(BaseModel):
    """Schema for updating user (admin only)."""

    role: str | None = None  # 'read_only', 'analyst', 'administrator'
    is_active: bool | None = None


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    username: str
    email: str | None
    display_name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login_at: str | None
    sso_provider: str | None


# User Management Endpoints (Admin Only)


@router.get("/")
async def list_users(
    current_user: User = Depends(require_role("administrator")),
    db=Depends(get_db),
):
    """
    List all users (admin only).

    Args:
        current_user: Current admin user
        db: Database connection

    Returns:
        List of all users
    """
    cursor = await db.execute(
        """
        SELECT id, username, email, display_name, role, is_active,
               created_at, updated_at, last_login_at, sso_provider
        FROM users
        ORDER BY created_at DESC
        """
    )
    rows = await cursor.fetchall()

    return {"users": [dict(row) for row in rows]}


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(require_role("administrator")),
    db=Depends(get_db),
):
    """
    Get user details (admin only).

    Args:
        user_id: User ID to retrieve
        current_user: Current admin user
        db: Database connection

    Returns:
        User details
    """
    cursor = await db.execute(
        """
        SELECT id, username, email, display_name, role, is_active,
               created_at, updated_at, last_login_at, sso_provider
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return dict(row)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    updates: UserUpdate,
    current_user: User = Depends(require_role("administrator")),
    db=Depends(get_db),
):
    """
    Update user role or status (admin only).

    Args:
        user_id: User ID to update
        updates: Update data
        current_user: Current admin user
        db: Database connection

    Returns:
        Success message
    """
    # Prevent self-deactivation
    if user_id == current_user.id and updates.is_active is False:
        raise HTTPException(
            status_code=400, detail="Cannot deactivate your own account"
        )

    # Get current user data
    cursor = await db.execute("SELECT username, role, is_active FROM users WHERE id = ?", (user_id,))
    user = await cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build update query
    update_fields = []
    params = []

    if updates.role is not None:
        if updates.role not in ["read_only", "analyst", "administrator"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        update_fields.append("role = ?")
        params.append(updates.role)

    if updates.is_active is not None:
        update_fields.append("is_active = ?")
        params.append(int(updates.is_active))

    if not update_fields:
        raise HTTPException(status_code=400, detail="No updates provided")

    update_fields.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(user_id)

    await db.execute(
        f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?", params
    )
    await db.commit()

    # Log the change
    details = {}
    if updates.role is not None:
        details["old_role"] = user["role"]
        details["new_role"] = updates.role
    if updates.is_active is not None:
        details["old_is_active"] = bool(user["is_active"])
        details["new_is_active"] = updates.is_active

    await log_audit(
        db,
        username=current_user.username,
        action="update",
        resource_type="user",
        resource_id=user_id,
        user_id=current_user.id,
        details=details,
    )

    return {"message": "User updated"}


@router.put("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_role("administrator")),
    db=Depends(get_db),
):
    """
    Deactivate a user account (admin only).

    Args:
        user_id: User ID to deactivate
        current_user: Current admin user
        db: Database connection

    Returns:
        Success message
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    cursor = await db.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = await cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        "UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), user_id),
    )
    await db.commit()

    await log_audit(
        db,
        username=current_user.username,
        action="deactivate",
        resource_type="user",
        resource_id=user_id,
        user_id=current_user.id,
        details={"deactivated_username": user["username"]},
    )

    return {"message": "User deactivated"}


@router.put("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: User = Depends(require_role("administrator")),
    db=Depends(get_db),
):
    """
    Reactivate a user account (admin only).

    Args:
        user_id: User ID to activate
        current_user: Current admin user
        db: Database connection

    Returns:
        Success message
    """
    cursor = await db.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = await cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        "UPDATE users SET is_active = 1, updated_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), user_id),
    )
    await db.commit()

    await log_audit(
        db,
        username=current_user.username,
        action="activate",
        resource_type="user",
        resource_id=user_id,
        user_id=current_user.id,
        details={"activated_username": user["username"]},
    )

    return {"message": "User activated"}


# User Profile Endpoints (Own Profile)


@router.get("/me/profile")
async def get_my_profile(
    current_user: User = Depends(get_current_active_user), db=Depends(get_db)
):
    """
    Get current user's profile with preferences.

    Args:
        current_user: Current authenticated user
        db: Database connection

    Returns:
        User profile with preferences
    """
    cursor = await db.execute(
        "SELECT * FROM user_preferences WHERE user_id = ?", (current_user.id,)
    )
    prefs = await cursor.fetchone()

    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "display_name": current_user.display_name,
            "role": current_user.role,
        },
        "preferences": dict(prefs) if prefs else None,
    }


@router.put("/me/profile")
async def update_my_profile(
    updates: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """
    Update current user's profile preferences.

    Args:
        updates: Profile update data
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Success message
    """
    now = datetime.now(timezone.utc).isoformat()

    # Check if preferences exist
    cursor = await db.execute(
        "SELECT user_id FROM user_preferences WHERE user_id = ?", (current_user.id,)
    )
    exists = await cursor.fetchone()

    if exists:
        # Update existing preferences
        update_fields = []
        params = []

        if updates.display_name is not None:
            update_fields.append("display_name_override = ?")
            params.append(updates.display_name)

        if updates.avatar_url is not None:
            update_fields.append("avatar_url = ?")
            params.append(updates.avatar_url)

        if updates.theme is not None:
            if updates.theme not in ["light", "dark", "system"]:
                raise HTTPException(status_code=400, detail="Invalid theme")
            update_fields.append("theme_preference = ?")
            params.append(updates.theme)

        if update_fields:
            update_fields.append("updated_at = ?")
            params.append(now)
            params.append(current_user.id)

            await db.execute(
                f"UPDATE user_preferences SET {', '.join(update_fields)} WHERE user_id = ?",
                params,
            )
    else:
        # Create new preferences
        await db.execute(
            """
            INSERT INTO user_preferences (user_id, display_name_override, avatar_url, theme_preference, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                current_user.id,
                updates.display_name,
                updates.avatar_url,
                updates.theme,
                now,
                now,
            ),
        )

    await db.commit()

    await log_audit(
        db,
        username=current_user.username,
        action="update",
        resource_type="user_profile",
        resource_id=current_user.id,
        user_id=current_user.id,
    )

    return {"message": "Profile updated"}
