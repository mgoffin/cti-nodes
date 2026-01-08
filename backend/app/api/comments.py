"""API endpoints for comments."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from ..core.dependencies import get_db_dependency, get_current_user, User
from ..models.schemas import Comment, CommentCreate, CommentUpdate
from ..core.audit import log_audit

router = APIRouter(tags=["comments"])


def get_author(user: User) -> str:
    """Get author from user."""
    return user.username


@router.get("/nodes/{node_id}/comments", response_model=list[Comment])
async def list_comments(
    node_id: str,
    sort_by: str = "created_at",  # created_at or updated_at
    order: str = "desc",  # asc or desc
    db=Depends(get_db_dependency),
):
    """Get all comments for a node."""
    # Validate sort parameters
    if sort_by not in ["created_at", "updated_at"]:
        raise HTTPException(status_code=400, detail="sort_by must be 'created_at' or 'updated_at'")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")

    # Check if node exists
    cursor = await db.execute("SELECT id FROM nodes WHERE id = ?", (node_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Node not found")

    # Fetch comments
    query = f"""
        SELECT id, node_id, content, author, created_at, updated_at
        FROM comments
        WHERE node_id = ?
        ORDER BY {sort_by} {order}
    """
    cursor = await db.execute(query, (node_id,))
    rows = await cursor.fetchall()

    comments = []
    for row in rows:
        comments.append(Comment(
            id=row[0],
            node_id=row[1],
            content=row[2],
            author=row[3],
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
        ))

    return comments


@router.post("/nodes/{node_id}/comments", response_model=Comment, status_code=201)
async def create_comment(
    node_id: str,
    comment_data: CommentCreate,
    db=Depends(get_db_dependency),
    current_user: User = Depends(get_current_user),
):
    """Create a new comment on a node."""
    # Check if node exists
    cursor = await db.execute("SELECT id FROM nodes WHERE id = ?", (node_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Node not found")

    comment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    author = get_author(current_user)

    await db.execute(
        """
        INSERT INTO comments (id, node_id, content, author, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (comment_id, node_id, comment_data.content, author, now, now),
    )
    await db.commit()

    # Log audit
    await log_audit(
        db,
        username=current_user.username,
        action="create",
        resource_type="comment",
        resource_id=comment_id,
        user_id=current_user.id,
    )

    return Comment(
        id=comment_id,
        node_id=node_id,
        content=comment_data.content,
        author=author,
        created_at=datetime.fromisoformat(now),
        updated_at=datetime.fromisoformat(now),
    )


@router.put("/comments/{comment_id}", response_model=Comment)
async def update_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    db=Depends(get_db_dependency),
    current_user: User = Depends(get_current_user),
):
    """Update a comment."""
    # Check if comment exists
    cursor = await db.execute(
        "SELECT id, node_id, content, author, created_at FROM comments WHERE id = ?",
        (comment_id,),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Comment not found")

    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        "UPDATE comments SET content = ?, updated_at = ? WHERE id = ?",
        (comment_data.content, now, comment_id),
    )
    await db.commit()

    # Log audit
    await log_audit(
        db,
        username=current_user.username,
        action="update",
        resource_type="comment",
        resource_id=comment_id,
        user_id=current_user.id,
    )

    return Comment(
        id=row[0],
        node_id=row[1],
        content=comment_data.content,
        author=row[3],
        created_at=datetime.fromisoformat(row[4]),
        updated_at=datetime.fromisoformat(now),
    )


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: str,
    db=Depends(get_db_dependency),
    current_user: User = Depends(get_current_user),
):
    """Delete a comment."""
    # Check if comment exists
    cursor = await db.execute("SELECT node_id FROM comments WHERE id = ?", (comment_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Comment not found")

    node_id = row[0]

    await db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    await db.commit()

    # Log audit
    await log_audit(
        db,
        username=current_user.username,
        action="delete",
        resource_type="comment",
        resource_id=comment_id,
        user_id=current_user.id,
    )

    return None
