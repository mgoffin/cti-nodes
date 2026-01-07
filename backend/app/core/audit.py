"""Audit logging utilities for tracking user actions."""

from uuid import uuid4
from datetime import datetime, timezone, timedelta
import json

from .config import settings


async def log_audit(
    db,
    username: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict | None = None,
    user_id: str | None = None,
) -> None:
    """
    Log an audit event to the database.

    Args:
        db: Database connection
        username: Username performing the action
        action: Action performed (create, update, delete, login, logout, etc.)
        resource_type: Type of resource (node, tag, edge, user, session, etc.)
        resource_id: ID of the resource
        details: Optional dict with additional context
        user_id: Optional user ID

    Example:
        await log_audit(
            db,
            username="john.doe",
            action="create",
            resource_type="node",
            resource_id=node_id,
            user_id=current_user.id,
            details={"auto_extracted": True}
        )
    """
    if not settings.audit_log_enabled:
        return

    try:
        await db.execute(
            """
            INSERT INTO audit_log (id, timestamp, user_id, username, action, resource_type, resource_id, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                datetime.now(timezone.utc).isoformat(),
                user_id,
                username,
                action,
                resource_type,
                resource_id,
                json.dumps(details) if details else None,
            ),
        )
        await db.commit()
    except Exception as e:
        # If audit logging fails (e.g., schema mismatch), log warning but don't break the request
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Audit log failed: {e}. Database may need migration.")
        # Don't re-raise - audit logging should never break functionality


async def cleanup_old_audit_logs(db) -> int:
    """
    Remove audit logs older than retention period.

    Args:
        db: Database connection

    Returns:
        Count of deleted records
    """
    if settings.audit_log_retention_days == 0:
        return 0  # Keep forever

    cutoff_date = datetime.now(timezone.utc) - timedelta(
        days=settings.audit_log_retention_days
    )
    cutoff_iso = cutoff_date.isoformat()

    cursor = await db.execute(
        "DELETE FROM audit_log WHERE timestamp < ?", (cutoff_iso,)
    )
    deleted_count = cursor.rowcount
    await db.commit()

    return deleted_count


async def get_audit_log_size_mb(db) -> float:
    """
    Get approximate size of audit log in MB.

    Args:
        db: Database connection

    Returns:
        Estimated size in megabytes
    """
    cursor = await db.execute("SELECT COUNT(*) as count FROM audit_log")
    result = await cursor.fetchone()
    count = result["count"] if result else 0

    # Rough estimate: 500 bytes per log entry average
    size_bytes = count * 500
    size_mb = size_bytes / (1024 * 1024)

    return size_mb


async def should_cleanup_audit_log(db) -> bool:
    """
    Check if audit log cleanup is needed based on size.

    Args:
        db: Database connection

    Returns:
        True if cleanup recommended
    """
    if settings.audit_log_max_size_mb == 0:
        return False  # No size limit

    current_size = await get_audit_log_size_mb(db)
    return current_size >= settings.audit_log_max_size_mb
