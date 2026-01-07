"""Search API endpoints."""

import re
from datetime import datetime
from fastapi import APIRouter, Depends

from ..core.database import get_db
from ..core.dependencies import get_current_user, User
from ..models import Node, Tag, Extracted, SearchQuery, SearchResult

router = APIRouter()


@router.post("/", response_model=SearchResult)
async def search_nodes(
    query: SearchQuery,
    current_user: User = Depends(get_current_user),
) -> SearchResult:
    """
    Search nodes using the query syntax.

    Query syntax:
    - *keyword* : Search everywhere (content + tags + extracted)
    - content="*text*" : Search node content only
    - tag:name="value" : Search for specific tag with value
    - tag:name=* : Find all nodes with a specific tag name
    - tag-value="*partial*" : Search all tag values
    - AND / OR : Combine conditions (not yet implemented)

    Note: All users can search all data regardless of ownership (by design).
    """
    parsed = parse_query(query.query)

    async with get_db() as db:
        node_ids = set()

        if parsed["type"] == "freeform":
            # Search everywhere
            search_term = escape_fts_term(parsed["term"])

            # Search in nodes_fts
            cursor = await db.execute(
                """
                SELECT n.id FROM nodes n
                JOIN nodes_fts fts ON n.rowid = fts.rowid
                WHERE nodes_fts MATCH ?
                """,
                (search_term,),
            )
            rows = await cursor.fetchall()
            node_ids.update(row["id"] for row in rows)

            # Search in tags_fts
            cursor = await db.execute(
                """
                SELECT DISTINCT t.node_id FROM tags t
                JOIN tags_fts fts ON t.rowid = fts.rowid
                WHERE tags_fts MATCH ?
                """,
                (search_term,),
            )
            rows = await cursor.fetchall()
            node_ids.update(row["node_id"] for row in rows)

            # Search in extracted_fts
            cursor = await db.execute(
                """
                SELECT DISTINCT e.node_id FROM extracted e
                JOIN extracted_fts fts ON e.rowid = fts.rowid
                WHERE extracted_fts MATCH ?
                """,
                (search_term,),
            )
            rows = await cursor.fetchall()
            node_ids.update(row["node_id"] for row in rows)

        elif parsed["type"] == "content":
            # Search content only
            search_term = escape_fts_term(parsed["term"])
            cursor = await db.execute(
                """
                SELECT n.id FROM nodes n
                JOIN nodes_fts fts ON n.rowid = fts.rowid
                WHERE nodes_fts MATCH ?
                """,
                (search_term,),
            )
            rows = await cursor.fetchall()
            node_ids.update(row["id"] for row in rows)

        elif parsed["type"] == "tag":
            # Search by tag name and optionally value
            tag_name = parsed["name"]
            tag_value = parsed.get("value")

            if tag_value and tag_value != "*":
                cursor = await db.execute(
                    """
                    SELECT DISTINCT node_id FROM tags
                    WHERE name = ? AND value LIKE ?
                    """,
                    (tag_name, tag_value.replace("*", "%")),
                )
            else:
                cursor = await db.execute(
                    "SELECT DISTINCT node_id FROM tags WHERE name = ?",
                    (tag_name,),
                )
            rows = await cursor.fetchall()
            node_ids.update(row["node_id"] for row in rows)

        elif parsed["type"] == "tag_value":
            # Search all tag values
            search_term = parsed["term"]
            cursor = await db.execute(
                """
                SELECT DISTINCT node_id FROM tags
                WHERE value LIKE ?
                """,
                (search_term.replace("*", "%"),),
            )
            rows = await cursor.fetchall()
            node_ids.update(row["node_id"] for row in rows)

        elif parsed["type"] == "extracted":
            # Search by extracted entity type and value
            entity_type = parsed.get("entity_type")
            entity_value = parsed["value"]

            if entity_type and entity_type != "*":
                cursor = await db.execute(
                    """
                    SELECT DISTINCT node_id FROM extracted
                    WHERE type = ? AND (value LIKE ? OR canonical_value LIKE ?)
                    """,
                    (
                        entity_type,
                        entity_value.replace("*", "%"),
                        entity_value.replace("*", "%")
                    ),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT DISTINCT node_id FROM extracted
                    WHERE value LIKE ? OR canonical_value LIKE ?
                    """,
                    (
                        entity_value.replace("*", "%"),
                        entity_value.replace("*", "%")
                    ),
                )
            rows = await cursor.fetchall()
            node_ids.update(row["node_id"] for row in rows)

        # Fetch the actual nodes
        total = len(node_ids)
        node_id_list = list(node_ids)

        # Apply pagination
        paginated_ids = node_id_list[query.offset : query.offset + query.limit]

        nodes = []
        for nid in paginated_ids:
            cursor = await db.execute("SELECT * FROM nodes WHERE id = ?", (nid,))
            row = await cursor.fetchone()
            if row:
                # Get tags
                tag_cursor = await db.execute("SELECT * FROM tags WHERE node_id = ?", (nid,))
                tag_rows = await tag_cursor.fetchall()
                tags = [
                    Tag(id=t["id"], node_id=t["node_id"], name=t["name"], value=t["value"])
                    for t in tag_rows
                ]

                # Get extracted entities
                ext_cursor = await db.execute("SELECT * FROM extracted WHERE node_id = ?", (nid,))
                ext_rows = await ext_cursor.fetchall()
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

                nodes.append(
                    Node(
                        id=row["id"],
                        content=row["content"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                        tags=tags,
                        extracted=extracted,
                    )
                )

        # Sort by created_at descending
        nodes.sort(key=lambda n: n.created_at, reverse=True)

    return SearchResult(nodes=nodes, total=total, query=query.query)


def escape_fts_term(term: str) -> str:
    """
    Escape a search term for FTS5.

    FTS5 treats certain characters as special (like dots in IP addresses).
    Wrapping the term in double quotes makes it a literal string search.
    """
    # Remove any existing quotes and escape internal quotes
    term = term.strip('"').replace('"', '""')
    return f'"{term}"'


def parse_query(query: str) -> dict:
    """
    Parse the search query string into a structured format.

    Returns a dict with:
    - type: "freeform", "content", "tag", "tag_value", "extracted"
    - term: the search term (for freeform, content, tag_value)
    - name: tag name (for tag type)
    - value: tag/extracted value
    - entity_type: extracted entity type (for extracted type)
    """
    query = query.strip()

    # Check for content="..." pattern
    content_match = re.match(r'content\s*=\s*"([^"]*)"', query, re.IGNORECASE)
    if content_match:
        term = content_match.group(1).replace("*", "")
        return {"type": "content", "term": term}

    # Check for extracted:type="value" pattern
    extracted_match = re.match(
        r'extracted:(\w+|\*)\s*=\s*"([^"]*)"',
        query,
        re.IGNORECASE
    )
    if extracted_match:
        entity_type = extracted_match.group(1)
        if entity_type == "*":
            entity_type = None
        return {
            "type": "extracted",
            "entity_type": entity_type,
            "value": extracted_match.group(2)
        }

    # Check for tag:name="value" pattern
    tag_match = re.match(r'tag:(\w+)\s*=\s*"?([^"]*)"?', query, re.IGNORECASE)
    if tag_match:
        return {
            "type": "tag",
            "name": tag_match.group(1),
            "value": tag_match.group(2)
        }

    # Check for tag:name=* pattern (just checking for tag existence)
    tag_exists_match = re.match(r'tag:(\w+)\s*=\s*\*', query, re.IGNORECASE)
    if tag_exists_match:
        return {"type": "tag", "name": tag_exists_match.group(1), "value": "*"}

    # Check for name="value" pattern (shorthand for tag search)
    shorthand_tag_match = re.match(r'(\w+)\s*=\s*"([^"]*)"', query)
    if shorthand_tag_match:
        return {
            "type": "tag",
            "name": shorthand_tag_match.group(1),
            "value": shorthand_tag_match.group(2)
        }

    # Check for tag-value="..." pattern
    tag_value_match = re.match(
        r'tag-value\s*=\s*"([^"]*)"',
        query,
        re.IGNORECASE
    )
    if tag_value_match:
        return {"type": "tag_value", "term": tag_value_match.group(1)}

    # Default: freeform search
    # Remove wildcards for FTS search (FTS5 uses different syntax)
    term = query.replace("*", "").strip()
    if not term:
        term = query  # Keep original if only wildcards

    return {"type": "freeform", "term": term}
