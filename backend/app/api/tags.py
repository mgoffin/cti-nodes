"""Tag API endpoints."""

import uuid
from fastapi import APIRouter, HTTPException

from ..core.database import get_db
from ..models import Tag, TagCreate, TagUpdate

router = APIRouter()

# System tags that cannot be modified or deleted
SYSTEM_TAGS = ["source", "datetime"]


@router.get("/suggestions")
async def get_tag_suggestions(prefix: str = "") -> dict[str, list[str]]:
    """Get tag name and value suggestions based on existing tags."""
    async with get_db() as db:
        # Get unique tag names
        if prefix:
            cursor = await db.execute(
                "SELECT DISTINCT name FROM tags WHERE name LIKE ? ORDER BY name LIMIT 20",
                (f"{prefix}%",),
            )
        else:
            cursor = await db.execute(
                "SELECT DISTINCT name FROM tags ORDER BY name LIMIT 50"
            )
        name_rows = await cursor.fetchall()
        names = [row["name"] for row in name_rows]

        # Get unique tag values (excluding datetime values)
        if prefix:
            cursor = await db.execute(
                """
                SELECT DISTINCT value FROM tags
                WHERE name != 'datetime' AND value LIKE ?
                ORDER BY value LIMIT 20
                """,
                (f"{prefix}%",),
            )
        else:
            cursor = await db.execute(
                """
                SELECT DISTINCT value FROM tags
                WHERE name != 'datetime'
                ORDER BY value LIMIT 50
                """
            )
        value_rows = await cursor.fetchall()
        values = [row["value"] for row in value_rows]

    return {"names": names, "values": values}


@router.get("/names")
async def get_tag_names() -> list[str]:
    """Get all unique tag names."""
    async with get_db() as db:
        cursor = await db.execute("SELECT DISTINCT name FROM tags ORDER BY name")
        rows = await cursor.fetchall()
    return [row["name"] for row in rows]


@router.get("/values/{tag_name}")
async def get_tag_values(tag_name: str) -> list[str]:
    """Get all unique values for a specific tag name."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT DISTINCT value FROM tags WHERE name = ? ORDER BY value",
            (tag_name,),
        )
        rows = await cursor.fetchall()
    return [row["value"] for row in rows]


@router.post("/node/{node_id}", response_model=Tag)
async def add_tag_to_node(node_id: str, tag: TagCreate) -> Tag:
    """Add a tag to a node."""
    async with get_db() as db:
        # Verify node exists
        cursor = await db.execute(
            "SELECT id FROM nodes WHERE id = ?",
            (node_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Node not found")

        # Prevent adding system tags
        if tag.name in SYSTEM_TAGS:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot add system tag '{tag.name}'"
            )

        # Check for duplicate tag
        cursor = await db.execute(
            "SELECT id FROM tags WHERE node_id = ? AND name = ? AND value = ?",
            (node_id, tag.name, tag.value)
        )
        if await cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Tag with this name and value already exists"
            )

        # Create the tag
        tag_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO tags (id, node_id, name, value) VALUES (?, ?, ?, ?)",
            (tag_id, node_id, tag.name, tag.value),
        )
        await db.commit()

        return Tag(id=tag_id, node_id=node_id, name=tag.name, value=tag.value)


@router.put("/{tag_id}", response_model=Tag)
async def update_tag(tag_id: str, updates: TagUpdate) -> Tag:
    """Update a tag."""
    async with get_db() as db:
        # Get existing tag
        cursor = await db.execute(
            "SELECT * FROM tags WHERE id = ?",
            (tag_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tag not found")

        # Prevent modifying system tags
        if row["name"] in SYSTEM_TAGS:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot modify system tag '{row['name']}'"
            )

        # Prevent changing to system tag name
        if updates.name is not None and updates.name in SYSTEM_TAGS:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change tag name to system tag '{updates.name}'"
            )

        # Build update query
        update_fields = []
        params = []

        if updates.name is not None:
            update_fields.append("name = ?")
            params.append(updates.name)
        if updates.value is not None:
            update_fields.append("value = ?")
            params.append(updates.value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(tag_id)
        await db.execute(
            f"UPDATE tags SET {', '.join(update_fields)} WHERE id = ?",
            params,
        )
        await db.commit()

        # Fetch updated tag
        cursor = await db.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
        updated = await cursor.fetchone()

        return Tag(
            id=updated["id"],
            node_id=updated["node_id"],
            name=updated["name"],
            value=updated["value"],
        )


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str) -> dict:
    """Delete a tag."""
    async with get_db() as db:
        # Get existing tag
        cursor = await db.execute(
            "SELECT * FROM tags WHERE id = ?",
            (tag_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tag not found")

        # Prevent deleting system tags
        if row["name"] in SYSTEM_TAGS:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete system tag '{row['name']}'"
            )

        await db.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        await db.commit()

        return {"message": "Tag deleted"}
