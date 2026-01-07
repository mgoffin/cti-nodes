"""Authentication API endpoints for SSO login and session management."""

from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from uuid import uuid4

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from ..core.config import settings
from ..core.database import get_db
from ..core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_token,
    generate_state_token,
    verify_state_token,
)
from ..core.dependencies import get_current_active_user, User
from ..core.audit import log_audit
from ..core.oidc_providers import get_oidc_provider

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/config")
async def get_auth_config():
    """
    Get authentication configuration for frontend.

    Returns auth status, provider info, and default author.
    """
    return {
        "auth_enabled": settings.auth_enabled,
        "sso_provider": settings.sso_provider if settings.auth_enabled else None,
        "default_author": settings.default_author,
    }


@router.get("/login")
async def login():
    """
    Redirect to SSO provider authorization endpoint.

    Raises:
        HTTPException: If auth is not enabled or OIDC not configured
    """
    if not settings.auth_enabled:
        raise HTTPException(status_code=400, detail="Authentication is not enabled")

    if not settings.effective_sso_base_url:
        raise HTTPException(
            status_code=500,
            detail="SSO not configured. Please set NODES_SSO_BASE_URL or NODES_DUO_API_HOST",
        )

    # Get OIDC provider configuration
    provider = get_oidc_provider(settings.sso_provider, settings.effective_sso_base_url)

    # Build authorization URL
    params = {
        "response_type": "code",
        "client_id": settings.effective_sso_client_id,
        "redirect_uri": settings.sso_redirect_uri or settings.duo_redirect_uri,
        "scope": provider.scopes,
        "state": generate_state_token(),
    }

    auth_url = f"{provider.authorization_endpoint}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(code: str, state: str, db=Depends(get_db)):
    """
    Handle SSO callback and create user session.

    Args:
        code: Authorization code from SSO provider
        state: State token for CSRF protection
        db: Database connection

    Returns:
        Redirect to frontend with auth cookies set
    """
    if not HTTPX_AVAILABLE:
        raise HTTPException(
            status_code=500, detail="httpx required for authentication"
        )

    if not JWT_AVAILABLE:
        raise HTTPException(
            status_code=500, detail="PyJWT required for authentication"
        )

    # Verify state token (CSRF protection)
    if not verify_state_token(state):
        raise HTTPException(status_code=400, detail="Invalid state token")

    # Get provider config
    provider = get_oidc_provider(settings.sso_provider, settings.effective_sso_base_url)

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            provider.token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.sso_redirect_uri or settings.duo_redirect_uri,
                "client_id": settings.effective_sso_client_id,
                "client_secret": settings.effective_sso_client_secret,
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange code for token: {token_response.text}",
        )

    tokens = token_response.json()

    # Decode ID token to get user info
    id_token = jwt.decode(
        tokens["id_token"], options={"verify_signature": False}
    )

    # Extract user info using provider-specific claims
    sso_subject = id_token["sub"]
    username = id_token.get(provider.username_claim) or id_token.get("email", "").split("@")[0]
    email = id_token.get(provider.email_claim)
    display_name = id_token.get(provider.display_name_claim) or username

    # Check if this is the first user (becomes admin)
    cursor = await db.execute("SELECT COUNT(*) FROM users")
    user_count = (await cursor.fetchone())[0]
    is_first_user = user_count == 0

    # Create or update user
    cursor = await db.execute(
        "SELECT * FROM users WHERE sso_provider = ? AND sso_subject_id = ?",
        (settings.sso_provider, sso_subject),
    )
    existing_user = await cursor.fetchone()

    now = datetime.now(timezone.utc).isoformat()

    if existing_user:
        # Update last login
        user_id = existing_user["id"]
        await db.execute(
            "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
            (now, now, user_id),
        )
        await db.commit()
        user = existing_user
    else:
        # Create new user
        user_id = str(uuid4())
        role = "administrator" if is_first_user else settings.default_user_role

        await db.execute(
            """
            INSERT INTO users (id, username, email, display_name, role, is_active,
                             created_at, updated_at, last_login_at, sso_provider, sso_subject_id)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                email,
                display_name,
                role,
                now,
                now,
                now,
                settings.sso_provider,
                sso_subject,
            ),
        )
        await db.commit()

        await log_audit(
            db,
            username="System",
            action="create",
            resource_type="user",
            resource_id=user_id,
            details={
                "role": role,
                "is_first_user": is_first_user,
                "sso_provider": settings.sso_provider,
            },
        )

        # Fetch the created user
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()

    # Create session and tokens
    user_dict = dict(user)
    access_token = create_access_token(user_dict)
    refresh_token = create_refresh_token()

    # Store refresh token in database
    session_id = str(uuid4())
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=settings.auth_refresh_token_expire_days)
    ).isoformat()

    await db.execute(
        """
        INSERT INTO sessions (id, user_id, token_hash, expires_at, created_at, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            user_id,
            hash_token(refresh_token),
            expires_at,
            now,
            None,  # TODO: Extract from request
            None,  # TODO: Extract from request
        ),
    )
    await db.commit()

    await log_audit(
        db,
        username=user["username"],
        action="login",
        resource_type="session",
        resource_id=session_id,
        user_id=user_id,
        details={"sso_provider": settings.sso_provider},
    )

    # Redirect to frontend with tokens in httpOnly cookies
    response = RedirectResponse(url="/")

    # Access token in httpOnly cookie (15 min expiry)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.debug,  # HTTPS only in production
        samesite="lax",
        max_age=settings.auth_access_token_expire_minutes * 60,
    )

    # Refresh token in httpOnly cookie (7 day expiry)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.auth_refresh_token_expire_days * 24 * 60 * 60,
    )

    return response


@router.post("/refresh")
async def refresh_token_endpoint(request: Request, response: Response, db=Depends(get_db)):
    """
    Refresh access token using refresh token from cookie.

    Args:
        request: FastAPI request
        response: FastAPI response
        db: Database connection

    Returns:
        Success message (new access token set in cookie)
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    # Verify refresh token in database
    token_hash_value = hash_token(refresh_token)
    cursor = await db.execute(
        """
        SELECT s.*, u.* FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token_hash = ? AND s.expires_at > ?
        """,
        (token_hash_value, datetime.now(timezone.utc).isoformat()),
    )
    session = await cursor.fetchone()

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Check if user is active
    if not session["is_active"]:
        raise HTTPException(status_code=403, detail="User account is disabled")

    # Issue new access token
    user_dict = {
        "id": session["user_id"],
        "username": session["username"],
        "email": session["email"],
        "role": session["role"],
    }
    access_token = create_access_token(user_dict)

    # Set new access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.auth_access_token_expire_minutes * 60,
    )

    return {"message": "Token refreshed"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """
    Logout and invalidate session.

    Args:
        request: FastAPI request
        response: FastAPI response
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Success message
    """
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        token_hash_value = hash_token(refresh_token)
        await db.execute(
            "DELETE FROM sessions WHERE token_hash = ?", (token_hash_value,)
        )
        await db.commit()

    await log_audit(
        db,
        username=current_user.username,
        action="logout",
        resource_type="session",
        resource_id=current_user.id,
        user_id=current_user.id,
    )

    # Delete cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "Logged out"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User profile information
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_active_user), db=Depends(get_db)
):
    """
    List user's active sessions.

    Args:
        current_user: Current authenticated user
        db: Database connection

    Returns:
        List of active sessions
    """
    cursor = await db.execute(
        """
        SELECT id, created_at, expires_at, ip_address, user_agent
        FROM sessions
        WHERE user_id = ? AND expires_at > ?
        ORDER BY created_at DESC
        """,
        (current_user.id, datetime.now(timezone.utc).isoformat()),
    )
    rows = await cursor.fetchall()

    return {"sessions": [dict(row) for row in rows]}


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """
    Revoke a specific session.

    Args:
        session_id: Session ID to revoke
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Success message
    """
    # Verify session belongs to current user
    cursor = await db.execute(
        "SELECT id, user_id FROM sessions WHERE id = ?", (session_id,)
    )
    session = await cursor.fetchone()

    if not session or session["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    await db.commit()

    await log_audit(
        db,
        username=current_user.username,
        action="delete",
        resource_type="session",
        resource_id=session_id,
        user_id=current_user.id,
    )

    return {"message": "Session revoked"}
