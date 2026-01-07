"""Extracted entity API endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends

from ..core.database import get_db
from ..core.dependencies import get_current_user, can_modify_resource, User
from ..core.audit import log_audit
from ..models import (
    Extracted,
    ExtractedCreate,
    ExtractedUpdate,
    EntitySuggestion,
    EntitySuggestionsResponse,
    RejectSuggestionRequest,
)
from ..extractors.defang import refang, is_defanged
from ..linker import find_and_create_links
from ..validators.entity_validator import validate_entity

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
    "filename",
    "mutex",
    "user_agent",
    "asn",
    "country",
    "mitre_attack",
]


@router.get("/types", response_model=list[str])
async def get_entity_types(
    current_user: User = Depends(get_current_user),
) -> list[str]:
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
    entity: ExtractedCreate,
    current_user: User = Depends(get_current_user),
) -> Extracted:
    """Add an extracted entity to a node."""
    async with get_db() as db:
        # Verify node exists and check ownership
        cursor = await db.execute(
            "SELECT id, author FROM nodes WHERE id = ?",
            (node_id,)
        )
        node = await cursor.fetchone()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        # Check ownership (extracted entities inherit from their parent node)
        if not can_modify_resource(current_user, node["author"]):
            raise HTTPException(status_code=403, detail="Not authorized to modify entities on this node")

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
            (id, node_id, type, value, raw_value, canonical_value, author)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity_id,
                node_id,
                entity.type,
                fanged_value,
                raw_value,
                entity.canonical_value,
                current_user.username,
            ),
        )
        await db.commit()

        # Audit log
        await log_audit(
            db,
            username=current_user.username,
            action="create",
            resource_type="extracted",
            resource_id=entity_id,
            details={"node_id": node_id, "type": entity.type, "value": fanged_value},
        )

        # Re-link the node to find new connections based on the added entity
        await db.execute(
            "DELETE FROM edges WHERE (source_node_id = ? OR target_node_id = ?) AND edge_type != 'manual'",
            (node_id, node_id),
        )
        await find_and_create_links(db, node_id)
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
    updates: ExtractedUpdate,
    current_user: User = Depends(get_current_user),
) -> Extracted:
    """Update an extracted entity."""
    async with get_db() as db:
        # Get existing entity and its parent node
        cursor = await db.execute(
            "SELECT e.*, n.author as node_author FROM extracted e JOIN nodes n ON e.node_id = n.id WHERE e.id = ?",
            (extracted_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Extracted entity not found")

        # Check ownership (extracted entities inherit from their parent node)
        if not can_modify_resource(current_user, row["node_author"]):
            raise HTTPException(status_code=403, detail="Not authorized to modify this entity")

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

        # Audit log
        update_details = {}
        if updates.type: update_details["type"] = updates.type
        if updates.value: update_details["value"] = updates.value
        if updates.canonical_value: update_details["canonical_value"] = updates.canonical_value
        await log_audit(
            db,
            username=current_user.username,
            action="update",
            resource_type="extracted",
            resource_id=extracted_id,
            details=update_details,
        )

        # Fetch updated entity
        cursor = await db.execute(
            "SELECT * FROM extracted WHERE id = ?",
            (extracted_id,)
        )
        updated = await cursor.fetchone()

        # Re-link the node to find new connections based on the updated entity
        node_id = updated["node_id"]
        await db.execute(
            "DELETE FROM edges WHERE (source_node_id = ? OR target_node_id = ?) AND edge_type != 'manual'",
            (node_id, node_id),
        )
        await find_and_create_links(db, node_id)
        await db.commit()

        return Extracted(
            id=updated["id"],
            node_id=updated["node_id"],
            type=updated["type"],
            value=updated["value"],
            raw_value=updated["raw_value"],
            canonical_value=updated["canonical_value"],
        )


@router.delete("/{extracted_id}")
async def delete_extracted(
    extracted_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete an extracted entity."""
    async with get_db() as db:
        # Verify entity exists, get node_id for re-linking, and check ownership
        cursor = await db.execute(
            "SELECT e.*, n.author as node_author FROM extracted e JOIN nodes n ON e.node_id = n.id WHERE e.id = ?",
            (extracted_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Extracted entity not found")

        # Check ownership (extracted entities inherit from their parent node)
        if not can_modify_resource(current_user, row["node_author"]):
            raise HTTPException(status_code=403, detail="Not authorized to delete this entity")

        node_id = row["node_id"]

        await db.execute("DELETE FROM extracted WHERE id = ?", (extracted_id,))
        await db.commit()

        # Audit log
        await log_audit(
            db,
            username=current_user.username,
            action="delete",
            resource_type="extracted",
            resource_id=extracted_id,
            details={"node_id": node_id, "type": row["type"], "value": row["value"]},
        )

        # Re-link the node to update connections after entity removal
        await db.execute(
            "DELETE FROM edges WHERE (source_node_id = ? OR target_node_id = ?) AND edge_type != 'manual'",
            (node_id, node_id),
        )
        await find_and_create_links(db, node_id)
        await db.commit()

        return {"message": "Extracted entity deleted"}


@router.get("/suggestions/{node_id}", response_model=EntitySuggestionsResponse)
async def get_entity_suggestions(
    node_id: str,
    current_user: User = Depends(get_current_user),
) -> EntitySuggestionsResponse:
    """
    Get validation suggestions for all extracted entities of a node.

    Reviews entities for:
    - Defanged values that should be refanged
    - Type mismatches (e.g., SHA256 labeled as MD5)

    Filters out suggestions that have been previously rejected.
    """
    async with get_db() as db:
        # Verify node exists
        cursor = await db.execute(
            "SELECT id FROM nodes WHERE id = ?",
            (node_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Node not found")

        # Get all extracted entities for this node
        cursor = await db.execute(
            "SELECT * FROM extracted WHERE node_id = ?",
            (node_id,)
        )
        entities = await cursor.fetchall()

        # Get all rejected suggestions for these entities
        entity_ids = [e["id"] for e in entities]
        if entity_ids:
            placeholders = ",".join("?" * len(entity_ids))
            cursor = await db.execute(
                f"""
                SELECT extracted_id, suggestion_type, suggested_value, suggested_type
                FROM rejected_suggestions
                WHERE extracted_id IN ({placeholders})
                """,
                entity_ids
            )
            rejected_rows = await cursor.fetchall()
            # Create a set of rejected suggestion keys
            rejected = {
                (r["extracted_id"], r["suggestion_type"], r["suggested_value"], r["suggested_type"])
                for r in rejected_rows
            }
        else:
            rejected = set()

        # Validate each entity and collect suggestions
        suggestions = []
        for entity in entities:
            suggestion = validate_entity(
                extracted_id=entity["id"],
                entity_type=entity["type"],
                value=entity["value"],
                raw_value=entity["raw_value"]
            )

            if suggestion:
                # Check if this suggestion was rejected
                key = (
                    suggestion.extracted_id,
                    suggestion.suggestion_type,
                    suggestion.suggested_value,
                    suggestion.suggested_type
                )
                if key not in rejected:
                    suggestions.append(EntitySuggestion(
                        extracted_id=suggestion.extracted_id,
                        suggestion_type=suggestion.suggestion_type,
                        current_value=suggestion.current_value,
                        suggested_value=suggestion.suggested_value,
                        current_type=suggestion.current_type,
                        suggested_type=suggestion.suggested_type,
                        reason=suggestion.reason,
                    ))

    return EntitySuggestionsResponse(
        node_id=node_id,
        suggestions=suggestions
    )


@router.post("/suggestions/reject")
async def reject_suggestion(
    request: RejectSuggestionRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Reject a suggestion so it won't be shown again.

    The rejection is persisted and tied to the specific extracted entity
    and suggestion type/value.
    """
    async with get_db() as db:
        # Verify entity exists
        cursor = await db.execute(
            "SELECT id FROM extracted WHERE id = ?",
            (request.extracted_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Extracted entity not found")

        # Check if already rejected
        cursor = await db.execute(
            """
            SELECT id FROM rejected_suggestions
            WHERE extracted_id = ?
            AND suggestion_type = ?
            AND (suggested_value = ? OR (suggested_value IS NULL AND ? IS NULL))
            AND (suggested_type = ? OR (suggested_type IS NULL AND ? IS NULL))
            """,
            (
                request.extracted_id,
                request.suggestion_type,
                request.suggested_value,
                request.suggested_value,
                request.suggested_type,
                request.suggested_type,
            )
        )
        if await cursor.fetchone():
            return {"message": "Suggestion already rejected"}

        # Insert rejection
        rejection_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        await db.execute(
            """
            INSERT INTO rejected_suggestions
            (id, extracted_id, suggestion_type, suggested_value, suggested_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                rejection_id,
                request.extracted_id,
                request.suggestion_type,
                request.suggested_value,
                request.suggested_type,
                now,
            )
        )
        await db.commit()

    return {"message": "Suggestion rejected"}
