"""Auto-linking logic for finding and creating relationships between nodes."""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import aiosqlite

# Confidence scores for different match types
CONFIDENCE_SCORES = {
    "ioc_exact": 1.0,
    "threat_actor_canonical": 1.0,
    "threat_actor_alias": 0.9,
    "tag_exact": 0.8,
    "url_domain": 0.7,
    "malware_match": 0.85,
    "tool_match": 0.85,
}


async def find_and_create_links(db: aiosqlite.Connection, node_id: str) -> Dict:
    """
    Find and create links between the given node and other existing nodes.

    Returns a dict with:
    - links_found: number of new links created
    - edges: list of created edge dicts
    """
    edges_created = []

    # Get extracted items for this node
    cursor = await db.execute(
        "SELECT * FROM extracted WHERE node_id = ?",
        (node_id,),
    )
    extractions = await cursor.fetchall()

    # Get tags for this node
    cursor = await db.execute(
        "SELECT * FROM tags WHERE node_id = ?",
        (node_id,),
    )
    tags = await cursor.fetchall()

    # Find matching extractions in other nodes
    for ext in extractions:
        ext_type = ext["type"]
        ext_value = ext["value"]
        ext_canonical = ext["canonical_value"]

        # Determine confidence based on type
        if ext_type in ("ipv4", "ipv6", "hash_md5", "hash_sha1", "hash_sha256", "email", "cve"):
            confidence = CONFIDENCE_SCORES["ioc_exact"]
            edge_type = "ioc_match"
        elif ext_type == "threat_actor":
            # Use canonical value for matching
            confidence = CONFIDENCE_SCORES["threat_actor_canonical"]
            edge_type = "entity_match"
        elif ext_type == "malware":
            confidence = CONFIDENCE_SCORES["malware_match"]
            edge_type = "entity_match"
        elif ext_type == "tool":
            confidence = CONFIDENCE_SCORES["tool_match"]
            edge_type = "entity_match"
        elif ext_type == "domain":
            confidence = CONFIDENCE_SCORES["ioc_exact"]
            edge_type = "ioc_match"
        elif ext_type == "url":
            confidence = CONFIDENCE_SCORES["url_domain"]
            edge_type = "ioc_match"
        else:
            confidence = 0.5
            edge_type = "content_match"

        # Find other nodes with matching extractions
        if ext_canonical:
            # Match on canonical value (for threat actors with aliases)
            cursor = await db.execute(
                """
                SELECT DISTINCT node_id FROM extracted
                WHERE node_id != ? AND (canonical_value = ? OR value = ?)
                """,
                (node_id, ext_canonical, ext_canonical),
            )
        else:
            cursor = await db.execute(
                """
                SELECT DISTINCT node_id FROM extracted
                WHERE node_id != ? AND value = ?
                """,
                (node_id, ext_value),
            )

        matching_nodes = await cursor.fetchall()

        for row in matching_nodes:
            target_node_id = row["node_id"]

            # Check if edge already exists
            if await edge_exists(db, node_id, target_node_id):
                continue

            # Create the edge
            edge = await create_edge(
                db, node_id, target_node_id, edge_type,
                match_value=ext_canonical or ext_value,
                confidence=confidence,
            )
            edges_created.append(edge)

    # Find matching tags in other nodes
    for tag in tags:
        # Skip datetime tags (too generic)
        if tag["name"] == "datetime":
            continue

        cursor = await db.execute(
            """
            SELECT DISTINCT node_id FROM tags
            WHERE node_id != ? AND name = ? AND value = ?
            """,
            (node_id, tag["name"], tag["value"]),
        )
        matching_nodes = await cursor.fetchall()

        for row in matching_nodes:
            target_node_id = row["node_id"]

            if await edge_exists(db, node_id, target_node_id):
                continue

            edge = await create_edge(
                db, node_id, target_node_id, "tag_match",
                match_value=f"{tag['name']}={tag['value']}",
                confidence=CONFIDENCE_SCORES["tag_exact"],
            )
            edges_created.append(edge)

    return {
        "links_found": len(edges_created),
        "edges": edges_created,
    }


async def edge_exists(db: aiosqlite.Connection, node_a: str, node_b: str) -> bool:
    """Check if an edge already exists between two nodes (in either direction)."""
    cursor = await db.execute(
        """
        SELECT id FROM edges
        WHERE (source_node_id = ? AND target_node_id = ?)
           OR (source_node_id = ? AND target_node_id = ?)
        """,
        (node_a, node_b, node_b, node_a),
    )
    return await cursor.fetchone() is not None


async def create_edge(
    db: aiosqlite.Connection,
    source_id: str,
    target_id: str,
    edge_type: str,
    match_value: str,
    confidence: float,
) -> Dict:
    """Create an edge between two nodes."""
    edge_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        """
        INSERT INTO edges (id, source_node_id, target_node_id, edge_type, match_value, confidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (edge_id, source_id, target_id, edge_type, match_value, confidence, now),
    )

    return {
        "id": edge_id,
        "source_node_id": source_id,
        "target_node_id": target_id,
        "edge_type": edge_type,
        "match_value": match_value,
        "confidence": confidence,
        "created_at": now,
    }
