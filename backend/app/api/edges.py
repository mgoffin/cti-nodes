"""Edge API endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends

from ..core.database import get_db
from ..core.dependencies import get_current_user, can_modify_resource, User
from ..core.audit import log_audit
from ..models import Edge, EdgeCreate

router = APIRouter()


@router.post("/", response_model=Edge, status_code=status.HTTP_201_CREATED)
async def create_edge(
    source_node_id: str,
    edge_data: EdgeCreate,
    current_user: User = Depends(get_current_user),
) -> Edge:
    """Create a manual edge between two nodes."""
    edge_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    async with get_db() as db:
        # Verify both nodes exist and check ownership of source node
        cursor = await db.execute("SELECT id, author FROM nodes WHERE id = ?", (source_node_id,))
        source_node = await cursor.fetchone()
        if not source_node:
            raise HTTPException(status_code=404, detail="Source node not found")

        # Check ownership (must own source node to create edge)
        if not can_modify_resource(current_user, source_node["author"]):
            raise HTTPException(status_code=403, detail="Not authorized to create edges from this node")

        cursor = await db.execute("SELECT id FROM nodes WHERE id = ?", (edge_data.target_node_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Target node not found")

        # Check for existing edge
        cursor = await db.execute(
            """
            SELECT id FROM edges
            WHERE (source_node_id = ? AND target_node_id = ?)
               OR (source_node_id = ? AND target_node_id = ?)
            """,
            (source_node_id, edge_data.target_node_id, edge_data.target_node_id, source_node_id),
        )
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Edge already exists between these nodes")

        # Create the edge
        await db.execute(
            """
            INSERT INTO edges (id, source_node_id, target_node_id, edge_type, match_value, confidence, created_at, author)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (edge_id, source_node_id, edge_data.target_node_id, edge_data.edge_type,
             edge_data.match_value, edge_data.confidence, now, current_user.username),
        )
        await db.commit()

        # Audit log
        await log_audit(
            db,
            username=current_user.username,
            action="create",
            resource_type="edge",
            resource_id=edge_id,
            details={
                "source_node_id": source_node_id,
                "target_node_id": edge_data.target_node_id,
                "edge_type": edge_data.edge_type,
            },
        )

    return Edge(
        id=edge_id,
        source_node_id=source_node_id,
        target_node_id=edge_data.target_node_id,
        edge_type=edge_data.edge_type,
        match_value=edge_data.match_value,
        confidence=edge_data.confidence,
        created_at=datetime.fromisoformat(now),
    )


@router.get("/", response_model=list[Edge])
async def list_edges(
    edge_type: str | None = None,
    min_confidence: float = 0.0,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
) -> list[Edge]:
    """List edges with optional filtering."""
    async with get_db() as db:
        query = "SELECT * FROM edges WHERE confidence >= ?"
        params: list = [min_confidence]

        if edge_type:
            query += " AND edge_type = ?"
            params.append(edge_type)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

    return [
        Edge(
            id=row["id"],
            source_node_id=row["source_node_id"],
            target_node_id=row["target_node_id"],
            edge_type=row["edge_type"],
            match_value=row["match_value"],
            confidence=row["confidence"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


@router.delete("/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge(
    edge_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an edge."""
    async with get_db() as db:
        # Get edge with source node author for ownership check
        cursor = await db.execute(
            "SELECT e.*, n.author as source_author FROM edges e JOIN nodes n ON e.source_node_id = n.id WHERE e.id = ?",
            (edge_id,)
        )
        edge = await cursor.fetchone()
        if not edge:
            raise HTTPException(status_code=404, detail="Edge not found")

        # Check ownership (must own source node to delete edge)
        if not can_modify_resource(current_user, edge["source_author"]):
            raise HTTPException(status_code=403, detail="Not authorized to delete this edge")

        await db.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
        await db.commit()

        # Audit log
        await log_audit(
            db,
            username=current_user.username,
            action="delete",
            resource_type="edge",
            resource_id=edge_id,
            details={
                "source_node_id": edge["source_node_id"],
                "target_node_id": edge["target_node_id"],
                "edge_type": edge["edge_type"],
            },
        )
