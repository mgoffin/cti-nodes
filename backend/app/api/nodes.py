"""Node API endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends

from ..core.database import get_db
from ..core.dependencies import get_current_user, can_modify_resource, User
from ..core.audit import log_audit
from ..models import Node, NodeCreate, NodeUpdate, NodeWithRelations, Tag, Edge, Extracted, LinkNotification
from ..extractors import extract_all
from ..linker import find_and_create_links

router = APIRouter()


@router.post("/", response_model=NodeWithRelations, status_code=status.HTTP_201_CREATED)
async def create_node(
    node_data: NodeCreate,
    current_user: User = Depends(get_current_user),
) -> NodeWithRelations:
    """Create a new node with automatic extraction and linking."""
    node_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    async with get_db() as db:
        # Insert the node
        await db.execute(
            "INSERT INTO nodes (id, content, created_at, updated_at, author) VALUES (?, ?, ?, ?, ?)",
            (node_id, node_data.content, now, now, current_user.username),
        )

        # Insert required 'source' tag
        source_tag_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO tags (id, node_id, name, value) VALUES (?, ?, ?, ?)",
            (source_tag_id, node_id, "source", node_data.source),
        )

        # Insert required 'datetime' tag
        datetime_tag_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO tags (id, node_id, name, value) VALUES (?, ?, ?, ?)",
            (datetime_tag_id, node_id, "datetime", now),
        )

        # Insert custom tags
        for tag in node_data.tags:
            tag_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO tags (id, node_id, name, value) VALUES (?, ?, ?, ?)",
                (tag_id, node_id, tag.name, tag.value),
            )

        # Extract IOCs and entities from content
        extractions = await extract_all(node_data.content)
        for ext in extractions:
            ext_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO extracted (id, node_id, type, value, raw_value, canonical_value) VALUES (?, ?, ?, ?, ?, ?)",
                (ext_id, node_id, ext["type"], ext["value"], ext["raw_value"], ext.get("canonical_value")),
            )

        await db.commit()

        # Audit log
        await log_audit(
            db,
            username=current_user.username,
            action="create",
            resource_type="node",
            resource_id=node_id,
            details={"content_length": len(node_data.content), "tags_count": len(node_data.tags)},
        )

        # Find and create links to other nodes
        link_result = await find_and_create_links(db, node_id)
        await db.commit()

        # Fetch the complete node with relations
        node = await get_node_with_relations(db, node_id)

    return node


@router.get("/", response_model=list[Node])
async def list_nodes(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
) -> list[Node]:
    """List all nodes with pagination."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM nodes ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()

        nodes = []
        for row in rows:
            tags = await get_tags_for_node(db, row["id"])
            extracted = await get_extracted_for_node(db, row["id"])
            nodes.append(
                Node(
                    id=row["id"],
                    content=row["content"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    author=row["author"] if "author" in row.keys() else None,
                    tags=tags,
                    extracted=extracted,
                )
            )

    return nodes


@router.get("/{node_id}", response_model=NodeWithRelations)
async def get_node(
    node_id: str,
    current_user: User = Depends(get_current_user),
) -> NodeWithRelations:
    """Get a node by ID with all relations."""
    async with get_db() as db:
        node = await get_node_with_relations(db, node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.put("/{node_id}", response_model=NodeWithRelations)
async def update_node(
    node_id: str,
    node_data: NodeUpdate,
    current_user: User = Depends(get_current_user),
) -> NodeWithRelations:
    """Update a node's content and/or tags, re-extract entities, and re-link."""
    now = datetime.now(timezone.utc).isoformat()
    needs_relinking = False

    async with get_db() as db:
        # Check node exists
        cursor = await db.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Node not found")

        # Check ownership
        if not can_modify_resource(current_user, row["author"]):
            raise HTTPException(status_code=403, detail="Not authorized to modify this node")

        # Update content if provided
        if node_data.content is not None:
            await db.execute(
                "UPDATE nodes SET content = ?, updated_at = ? WHERE id = ?",
                (node_data.content, now, node_id),
            )

            # Re-extract IOCs/entities
            await db.execute("DELETE FROM extracted WHERE node_id = ?", (node_id,))
            extractions = await extract_all(node_data.content)
            for ext in extractions:
                ext_id = str(uuid.uuid4())
                await db.execute(
                    "INSERT INTO extracted (id, node_id, type, value, raw_value, canonical_value) VALUES (?, ?, ?, ?, ?, ?)",
                    (ext_id, node_id, ext["type"], ext["value"], ext["raw_value"], ext.get("canonical_value")),
                )
            needs_relinking = True

        # Update tags if provided
        if node_data.tags is not None:
            # Remove old custom tags (keep datetime and source)
            await db.execute(
                "DELETE FROM tags WHERE node_id = ? AND name NOT IN ('datetime', 'source')",
                (node_id,),
            )
            # Add new tags
            for tag in node_data.tags:
                tag_id = str(uuid.uuid4())
                await db.execute(
                    "INSERT INTO tags (id, node_id, name, value) VALUES (?, ?, ?, ?)",
                    (tag_id, node_id, tag.name, tag.value),
                )
            needs_relinking = True

        await db.commit()

        # Audit log
        await log_audit(
            db,
            username=current_user.username,
            action="update",
            resource_type="node",
            resource_id=node_id,
            details={
                "content_updated": node_data.content is not None,
                "tags_updated": node_data.tags is not None,
            },
        )

        # Re-link if content or tags changed
        if needs_relinking:
            # Delete old auto-generated edges (keep manual edges)
            await db.execute(
                "DELETE FROM edges WHERE (source_node_id = ? OR target_node_id = ?) AND edge_type != 'manual'",
                (node_id, node_id),
            )
            await db.commit()

            # Find and create new links
            await find_and_create_links(db, node_id)
            await db.commit()

        # Fetch updated node with relations
        node = await get_node_with_relations(db, node_id)

    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a node and all related data."""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Node not found")

        # Check ownership
        if not can_modify_resource(current_user, row["author"]):
            raise HTTPException(status_code=403, detail="Not authorized to delete this node")

        await db.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        await db.commit()

        # Audit log
        await log_audit(
            db,
            username=current_user.username,
            action="delete",
            resource_type="node",
            resource_id=node_id,
            details={"author": row["author"]},
        )


@router.get("/{node_id}/related", response_model=list[Node])
async def get_related_nodes(
    node_id: str,
    depth: int = 1,
    current_user: User = Depends(get_current_user),
) -> list[Node]:
    """Get nodes related to this node up to a certain depth."""
    async with get_db() as db:
        # Check node exists
        cursor = await db.execute("SELECT id FROM nodes WHERE id = ?", (node_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Node not found")

        related_ids = set()
        current_level = {node_id}

        for _ in range(depth):
            if not current_level:
                break

            next_level = set()
            for nid in current_level:
                # Find nodes connected by edges (both directions)
                cursor = await db.execute(
                    """
                    SELECT target_node_id FROM edges WHERE source_node_id = ?
                    UNION
                    SELECT source_node_id FROM edges WHERE target_node_id = ?
                    """,
                    (nid, nid),
                )
                rows = await cursor.fetchall()
                for row in rows:
                    connected_id = row[0]
                    if connected_id != node_id and connected_id not in related_ids:
                        next_level.add(connected_id)
                        related_ids.add(connected_id)

            current_level = next_level

        # Fetch the related nodes
        nodes = []
        for rid in related_ids:
            cursor = await db.execute("SELECT * FROM nodes WHERE id = ?", (rid,))
            row = await cursor.fetchone()
            if row:
                tags = await get_tags_for_node(db, rid)
                nodes.append(
                    Node(
                        id=row["id"],
                        content=row["content"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                        tags=tags,
                    )
                )

    return nodes


# --- Helper Functions ---


async def get_tags_for_node(db, node_id: str) -> list[Tag]:
    """Get all tags for a node."""
    cursor = await db.execute("SELECT * FROM tags WHERE node_id = ?", (node_id,))
    rows = await cursor.fetchall()
    return [
        Tag(id=row["id"], node_id=row["node_id"], name=row["name"], value=row["value"])
        for row in rows
    ]


async def get_extracted_for_node(db, node_id: str) -> list[Extracted]:
    """Get all extracted entities for a node."""
    cursor = await db.execute("SELECT * FROM extracted WHERE node_id = ?", (node_id,))
    rows = await cursor.fetchall()
    return [
        Extracted(
            id=row["id"],
            node_id=row["node_id"],
            type=row["type"],
            value=row["value"],
            raw_value=row["raw_value"],
            canonical_value=row["canonical_value"],
        )
        for row in rows
    ]


async def get_node_with_relations(db, node_id: str) -> NodeWithRelations | None:
    """Get a node with all its relations."""
    cursor = await db.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
    row = await cursor.fetchone()
    if not row:
        return None

    # Get tags
    tags = await get_tags_for_node(db, node_id)

    # Get edges
    cursor = await db.execute(
        "SELECT * FROM edges WHERE source_node_id = ? OR target_node_id = ?",
        (node_id, node_id),
    )
    edge_rows = await cursor.fetchall()
    edges = [
        Edge(
            id=e["id"],
            source_node_id=e["source_node_id"],
            target_node_id=e["target_node_id"],
            edge_type=e["edge_type"],
            match_value=e["match_value"],
            confidence=e["confidence"],
            created_at=datetime.fromisoformat(e["created_at"]),
        )
        for e in edge_rows
    ]

    # Get extracted
    cursor = await db.execute("SELECT * FROM extracted WHERE node_id = ?", (node_id,))
    ext_rows = await cursor.fetchall()
    extracted = [
        Extracted(
            id=e["id"],
            node_id=e["node_id"],
            type=e["type"],
            value=e["value"],
            raw_value=e["raw_value"],
            canonical_value=e["canonical_value"],
        )
        for e in ext_rows
    ]

    # Get related nodes (depth 1)
    related_ids = set()
    for edge in edges:
        if edge.source_node_id != node_id:
            related_ids.add(edge.source_node_id)
        if edge.target_node_id != node_id:
            related_ids.add(edge.target_node_id)

    related_nodes = []
    for rid in related_ids:
        cursor = await db.execute("SELECT * FROM nodes WHERE id = ?", (rid,))
        r = await cursor.fetchone()
        if r:
            rtags = await get_tags_for_node(db, rid)
            related_nodes.append(
                Node(
                    id=r["id"],
                    content=r["content"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                    updated_at=datetime.fromisoformat(r["updated_at"]),
                    author=r["author"] if "author" in r.keys() else None,
                    tags=rtags,
                )
            )

    return NodeWithRelations(
        id=row["id"],
        content=row["content"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        author=row["author"] if "author" in row.keys() else None,
        tags=tags,
        edges=edges,
        extracted=extracted,
        related_nodes=related_nodes,
    )
