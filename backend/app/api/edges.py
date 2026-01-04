"""Edge API endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from ..core.database import get_db
from ..models import Edge, EdgeCreate

router = APIRouter()


@router.post("/", response_model=Edge, status_code=status.HTTP_201_CREATED)
async def create_edge(source_node_id: str, edge_data: EdgeCreate) -> Edge:
    """Create a manual edge between two nodes."""
    edge_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    async with get_db() as db:
        # Verify both nodes exist
        cursor = await db.execute("SELECT id FROM nodes WHERE id = ?", (source_node_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Source node not found")

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
            INSERT INTO edges (id, source_node_id, target_node_id, edge_type, match_value, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (edge_id, source_node_id, edge_data.target_node_id, edge_data.edge_type,
             edge_data.match_value, edge_data.confidence, now),
        )
        await db.commit()

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
async def delete_edge(edge_id: str) -> None:
    """Delete an edge."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM edges WHERE id = ?", (edge_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Edge not found")

        await db.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
        await db.commit()
