"""Audit log API endpoints."""

from fastapi import APIRouter, Depends, Query

from ..core.config import settings
from ..core.database import get_db
from ..core.dependencies import require_role, User
from ..core.audit import cleanup_old_audit_logs, get_audit_log_size_mb

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/")
async def query_audit_log(
    resource_type: str | None = None,
    username: str | None = None,
    action: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    current_user: User = Depends(require_role("administrator")),
    db=Depends(get_db),
):
    """
    Query audit logs with filters (admin only).

    Args:
        resource_type: Filter by resource type
        username: Filter by username
        action: Filter by action
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        limit: Maximum results to return
        offset: Offset for pagination
        current_user: Current admin user
        db: Database connection

    Returns:
        Filtered audit logs
    """
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []

    if resource_type:
        query += " AND resource_type = ?"
        params.append(resource_type)

    if username:
        query += " AND username = ?"
        params.append(username)

    if action:
        query += " AND action = ?"
        params.append(action)

    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)

    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()

    return {"logs": [dict(row) for row in rows], "limit": limit, "offset": offset}


@router.post("/cleanup")
async def cleanup_audit_log(
    current_user: User = Depends(require_role("administrator")),
    db=Depends(get_db),
):
    """
    Manually trigger audit log cleanup (admin only).

    Removes audit logs older than the configured retention period.

    Args:
        current_user: Current admin user
        db: Database connection

    Returns:
        Count of deleted entries
    """
    deleted_count = await cleanup_old_audit_logs(db)
    return {"deleted_count": deleted_count}


@router.get("/stats")
async def get_audit_stats(
    current_user: User = Depends(require_role("administrator")),
    db=Depends(get_db),
):
    """
    Get audit log statistics (admin only).

    Args:
        current_user: Current admin user
        db: Database connection

    Returns:
        Audit log size and configuration
    """
    cursor = await db.execute("SELECT COUNT(*) FROM audit_log")
    count = (await cursor.fetchone())[0]

    size_mb = await get_audit_log_size_mb(db)

    return {
        "total_entries": count,
        "estimated_size_mb": round(size_mb, 2),
        "retention_days": settings.audit_log_retention_days,
        "max_size_mb": settings.audit_log_max_size_mb,
        "enabled": settings.audit_log_enabled,
    }
