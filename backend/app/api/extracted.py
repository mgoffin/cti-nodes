"""Extracted entity API endpoints."""

import uuid
from fastapi import APIRouter, HTTPException

from ..core.database import get_db
from ..models import Extracted, ExtractedCreate, ExtractedUpdate
from ..extractors.defang import refang, is_defanged

router = APIRouter()

# Default entity types (always shown)
DEFAULT_ENTITY_TYPES = [
    "ipv4",
    "ipv6",
    "domain",
    "url",
    "hash_md5",
    "hash_sha1",
    "hash_sha256",
    "email",
    "cve",
    "threat_actor",
    "malware",
    "tool",
    "campaign",
    "registry_key",
    "file_path",
    "mutex",
    "user_agent",
    "asn",
    "country",
    "mitre_attack",
]


@router.get("/types", response_model=list[str])
async def get_entity_types() -> list[str]:
    """Get list of entity types (defaults + any custom types from database)."""
    async with get_db() as db:
        # Get all unique types from the database
        cursor = await db.execute(
            "SELECT DISTINCT type FROM extracted ORDER BY type"
        )
        rows = await cursor.fetchall()
        db_types = {row["type"] for row in rows}

    # Combine defaults with any custom types from DB
    all_types = set(DEFAULT_ENTITY_TYPES) | db_types
    return sorted(all_types)


@router.post("/node/{node_id}", response_model=Extracted)
async def add_extracted_to_node(
    node_id: str,
    entity: ExtractedCreate
) -> Extracted:
    """Add an extracted entity to a node."""
    async with get_db() as db:
        # Verify node exists
        cursor = await db.execute(
            "SELECT id FROM nodes WHERE id = ?",
            (node_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Node not found")

        # Create the extracted entity
        entity_id = str(uuid.uuid4())

        # Refang the value if it's defanged
        original_value = entity.value
        fanged_value = refang(original_value)

        # Store original as raw_value if it was defanged
        if is_defanged(original_value):
            raw_value = original_value
        else:
            raw_value = entity.raw_value or fanged_value

        await db.execute(
            """
            INSERT INTO extracted
            (id, node_id, type, value, raw_value, canonical_value)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entity_id,
                node_id,
                entity.type,
                fanged_value,
                raw_value,
                entity.canonical_value
            ),
        )
        await db.commit()

        return Extracted(
            id=entity_id,
            node_id=node_id,
            type=entity.type,
            value=fanged_value,
            raw_value=raw_value,
            canonical_value=entity.canonical_value,
        )


@router.put("/{extracted_id}", response_model=Extracted)
async def update_extracted(
    extracted_id: str,
    updates: ExtractedUpdate
) -> Extracted:
    """Update an extracted entity."""
    async with get_db() as db:
        # Get existing entity
        cursor = await db.execute(
            "SELECT * FROM extracted WHERE id = ?",
            (extracted_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Extracted entity not found")

        # Build update query
        update_fields = []
        params = []

        if updates.type is not None:
            update_fields.append("type = ?")
            params.append(updates.type)
        if updates.value is not None:
            # Refang the value if defanged
            original_value = updates.value
            fanged_value = refang(original_value)
            update_fields.append("value = ?")
            params.append(fanged_value)
            # Update raw_value if value was defanged
            if is_defanged(original_value):
                update_fields.append("raw_value = ?")
                params.append(original_value)
        if updates.raw_value is not None:
            update_fields.append("raw_value = ?")
            params.append(updates.raw_value)
        if updates.canonical_value is not None:
            update_fields.append("canonical_value = ?")
            params.append(updates.canonical_value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(extracted_id)
        await db.execute(
            f"UPDATE extracted SET {', '.join(update_fields)} WHERE id = ?",
            params,
        )
        await db.commit()

        # Fetch updated entity
        cursor = await db.execute(
            "SELECT * FROM extracted WHERE id = ?",
            (extracted_id,)
        )
        updated = await cursor.fetchone()

        return Extracted(
            id=updated["id"],
            node_id=updated["node_id"],
            type=updated["type"],
            value=updated["value"],
            raw_value=updated["raw_value"],
            canonical_value=updated["canonical_value"],
        )


@router.delete("/{extracted_id}")
async def delete_extracted(extracted_id: str) -> dict:
    """Delete an extracted entity."""
    async with get_db() as db:
        # Verify entity exists
        cursor = await db.execute(
            "SELECT id FROM extracted WHERE id = ?",
            (extracted_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Extracted entity not found")

        await db.execute("DELETE FROM extracted WHERE id = ?", (extracted_id,))
        await db.commit()

        return {"message": "Extracted entity deleted"}
