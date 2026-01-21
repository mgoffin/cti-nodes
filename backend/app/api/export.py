"""Export API endpoints for nodes."""

import io
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response

from ..core.database import get_db
from ..core.dependencies import get_current_user, User
from ..models.schemas import ExportPreview, ExportRequest

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/preview")
async def preview_export(
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
) -> ExportPreview:
    """Preview what will be exported without generating the actual export."""
    async with get_db() as db:
        # Get nodes
        placeholders = ",".join("?" * len(request.node_ids))
        query = f"SELECT * FROM nodes WHERE id IN ({placeholders})"
        cursor = await db.execute(query, request.node_ids)
        rows = await cursor.fetchall()
        nodes = [dict(row) for row in rows]

        if not nodes:
            raise HTTPException(
                status_code=404, detail="No nodes found with provided IDs"
            )

        node_count = len(nodes)
        node_ids_set = {node["id"] for node in nodes}

        # Count tags
        tag_count = 0
        if request.options.include_tags:
            query = f"SELECT * FROM tags WHERE node_id IN ({placeholders})"
            cursor = await db.execute(query, request.node_ids)
            tags = await cursor.fetchall()

            if request.options.include_system_tags:
                tag_count = len(tags)
            else:
                tag_count = sum(
                    1 for tag in tags if tag["name"] not in ("source", "datetime")
                )

        # Count extracted entities
        entity_count = 0
        if request.options.include_extracted:
            placeholders = ",".join("?" * len(node_ids_set))
            query = f"SELECT * FROM extracted WHERE node_id IN ({placeholders})"
            cursor = await db.execute(query, list(node_ids_set))
            entities = await cursor.fetchall()
            
            for entity in entities:
                if (
                    request.options.entity_types is None
                    or entity["type"] in request.options.entity_types
                ):
                    entity_count += 1

        # Count edges
        edge_count = 0
        if request.options.include_edges:
            query = f"""
                SELECT COUNT(*) as count FROM edges 
                WHERE (source_node_id IN ({placeholders}) OR target_node_id IN ({placeholders}))
                AND edge_type != 'tag_match'
            """
            cursor = await db.execute(query, request.node_ids + request.node_ids)
            result = await cursor.fetchone()
            edge_count = result["count"] if result else 0

        # Count comments
        comment_count = 0
        if request.options.include_comments:
            query = f"SELECT COUNT(*) as count FROM comments WHERE node_id IN ({placeholders})"
            cursor = await db.execute(query, request.node_ids)
            result = await cursor.fetchone()
            comment_count = result["count"] if result else 0

        # Count related nodes
        related_node_count = 0
        if request.options.include_related_nodes:
            related_ids = await _get_related_node_ids(
                db, node_ids_set, request.options.related_depth
            )
            related_node_count = len(related_ids - node_ids_set)

        # Estimate size (rough approximation)
        estimated_size_kb = _estimate_export_size(
            node_count,
            tag_count,
            entity_count,
            edge_count,
            comment_count,
            related_node_count,
            request.options.format,
        )

        # Generate warnings
        warnings = []
        if estimated_size_kb > 10000:  # 10 MB
            warnings.append(
                f"Large export size: ~{estimated_size_kb // 1024} MB. "
                "This may take a while."
            )
        if related_node_count > 100:
            warnings.append(
                f"Many related nodes ({related_node_count}). "
                "Consider reducing depth."
            )

        return ExportPreview(
            node_count=node_count,
            tag_count=tag_count,
            entity_count=entity_count,
            edge_count=edge_count,
            comment_count=comment_count,
            related_node_count=related_node_count,
            estimated_size_kb=estimated_size_kb,
            warnings=warnings,
        )


@router.post("")
async def export_nodes(
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
) -> Response:
    """Export nodes in the specified format."""
    async with get_db() as db:
        # Get nodes
        placeholders = ",".join("?" * len(request.node_ids))
        query = f"SELECT * FROM nodes WHERE id IN ({placeholders})"
        cursor = await db.execute(query, request.node_ids)
        rows = await cursor.fetchall()
        nodes = [dict(row) for row in rows]

        if not nodes:
            raise HTTPException(
                status_code=404, detail="No nodes found with provided IDs"
            )

        node_ids_set = {node["id"] for node in nodes}

        # Get related nodes if requested
        if request.options.include_related_nodes:
            related_ids = await _get_related_node_ids(
                db, node_ids_set, request.options.related_depth
            )
            placeholders = ",".join("?" * len(related_ids))
            query = f"SELECT * FROM nodes WHERE id IN ({placeholders})"
            cursor = await db.execute(query, list(related_ids))
            rows = await cursor.fetchall()
            nodes = [dict(row) for row in rows]
            node_ids_set = {node["id"] for node in nodes}

        # Get tags
        tags_by_node = {}
        if request.options.include_tags:
            placeholders = ",".join("?" * len(node_ids_set))
            query = f"SELECT * FROM tags WHERE node_id IN ({placeholders})"
            cursor = await db.execute(query, list(node_ids_set))
            all_tags = await cursor.fetchall()

            for tag in all_tags:
                tag_dict = dict(tag)
                is_system = tag_dict["name"] in ("source", "datetime")
                if not request.options.include_system_tags and is_system:
                    continue
                if tag_dict["node_id"] not in tags_by_node:
                    tags_by_node[tag_dict["node_id"]] = []
                tags_by_node[tag_dict["node_id"]].append(tag_dict)

        # Get extracted entities
        extracted_by_node = {}
        if request.options.include_extracted:
            placeholders = ",".join("?" * len(node_ids_set))
            query = f"SELECT * FROM extracted WHERE node_id IN ({placeholders})"
            cursor = await db.execute(query, list(node_ids_set))
            all_extracted = await cursor.fetchall()

            for entity in all_extracted:
                entity_dict = dict(entity)
                # Filter by entity type if specified
                if request.options.entity_types and entity_dict["type"] not in request.options.entity_types:
                    continue
                if entity_dict["node_id"] not in extracted_by_node:
                    extracted_by_node[entity_dict["node_id"]] = []
                extracted_by_node[entity_dict["node_id"]].append(entity_dict)

        # Get edges
        edges = []
        if request.options.include_edges:
            placeholders = ",".join("?" * len(node_ids_set))
            query = f"""
                SELECT * FROM edges 
                WHERE (source_node_id IN ({placeholders}) OR target_node_id IN ({placeholders}))
                AND edge_type != 'tag_match'
            """
            cursor = await db.execute(
                query, list(node_ids_set) + list(node_ids_set)
            )
            edges = [dict(row) for row in await cursor.fetchall()]

        # Get comments
        comments_by_node = {}
        if request.options.include_comments:
            placeholders = ",".join("?" * len(node_ids_set))
            query = f"SELECT * FROM comments WHERE node_id IN ({placeholders})"
            cursor = await db.execute(query, list(node_ids_set))
            all_comments = await cursor.fetchall()

            for comment in all_comments:
                comment_dict = dict(comment)
                if comment_dict["node_id"] not in comments_by_node:
                    comments_by_node[comment_dict["node_id"]] = []
                comments_by_node[comment_dict["node_id"]].append(comment_dict)

        # Generate export based on format
        if request.options.format == "json":
            content, media_type = _export_json(
                nodes, tags_by_node, extracted_by_node, edges, comments_by_node, request.options
            )
            extension = "json"
        elif request.options.format == "csv":
            content, media_type = _export_csv(
                nodes, tags_by_node, extracted_by_node, edges, comments_by_node, request.options
            )
            extension = "csv"
        elif request.options.format == "stix":
            content, media_type = _export_stix(
                nodes, tags_by_node, extracted_by_node, edges, comments_by_node, request.options
            )
            extension = "json"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {request.options.format}",
            )

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"nodes_export_{timestamp}.{extension}"

        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


async def _get_related_node_ids(
    db: Any, node_ids: set[str], depth: int
) -> set[str]:
    """Recursively get related node IDs up to the specified depth."""
    all_ids = set(node_ids)
    current_ids = node_ids

    for _ in range(depth):
        placeholders = ",".join("?" * len(current_ids))
        query = f"""
            SELECT * FROM edges 
            WHERE (source_node_id IN ({placeholders}) OR target_node_id IN ({placeholders}))
            AND edge_type != 'tag_match'
        """
        cursor = await db.execute(query, list(current_ids) + list(current_ids))
        edges = await cursor.fetchall()

        next_ids = set()
        for edge in edges:
            edge_dict = dict(edge)
            next_ids.add(edge_dict["source_node_id"])
            next_ids.add(edge_dict["target_node_id"])

        new_ids = next_ids - all_ids
        if not new_ids:
            break

        all_ids.update(new_ids)
        current_ids = new_ids

    return all_ids


def _estimate_export_size(
    node_count: int,
    tag_count: int,
    entity_count: int,
    edge_count: int,
    comment_count: int,
    related_node_count: int,
    format: str,
) -> int:
    """Estimate export size in KB."""
    # Rough estimates per item in KB
    node_size = 2  # ~2KB per node (content, source, extracted, etc.)
    tag_size = 0.1
    entity_size = 0.05
    edge_size = 0.2
    comment_size = 0.5

    total_kb = (
        (node_count + related_node_count) * node_size
        + tag_count * tag_size
        + entity_count * entity_size
        + edge_count * edge_size
        + comment_count * comment_size
    )

    # Format overhead
    if format == "json":
        total_kb *= 1.2  # JSON formatting overhead
    elif format == "stix":
        total_kb *= 1.5  # STIX bundle overhead
    elif format == "csv":
        total_kb *= 0.5  # CSV is more compact

    return int(total_kb)


def _export_json(
    nodes: list[dict],
    tags_by_node: dict[str, list[dict]],
    extracted_by_node: dict[str, list[dict]],
    edges: list[dict],
    comments_by_node: dict[str, list[dict]],
    options: Any,
) -> tuple[bytes, str]:
    """Export nodes as JSON."""
    export_data = {
        "export_metadata": {
            "format": "json",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "node_count": len(nodes),
        },
        "nodes": [],
    }

    for node in nodes:
        node_data = {
            "id": node["id"],
            "content": node["content"],
            "source": node.get("source", ""),  # Always include source
            "created_at": node.get("created_at"),
            "updated_at": node.get("updated_at"),
            "author": node.get("author"),
        }

        if options.include_tags and node["id"] in tags_by_node:
            node_data["tags"] = [
                {"name": tag["name"], "value": tag["value"]}
                for tag in tags_by_node[node["id"]]
            ]

        if options.include_extracted and node["id"] in extracted_by_node:
            # Group entities by type
            entities_by_type = {}
            for entity in extracted_by_node[node["id"]]:
                entity_type = entity["type"]
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append({
                    "value": entity["value"],
                    "raw_value": entity.get("raw_value"),
                    "canonical_value": entity.get("canonical_value"),
                })
            node_data["extracted"] = entities_by_type

        if options.include_comments and node["id"] in comments_by_node:
            node_data["comments"] = [
                {
                    "id": comment["id"],
                    "text": comment["text"],
                    "author": comment.get("author"),
                    "created_at": comment.get("created_at"),
                }
                for comment in comments_by_node[node["id"]]
            ]

        export_data["nodes"].append(node_data)

    if options.include_edges and edges:
        export_data["edges"] = [
            {
                "id": edge["id"],
                "source_id": edge["source_node_id"],
                "target_id": edge["target_node_id"],
                "edge_type": edge.get("edge_type"),
                "match_value": edge.get("match_value"),
                "confidence": edge.get("confidence"),
                "created_at": edge.get("created_at"),
            }
            for edge in edges
        ]

    content = json.dumps(export_data, indent=2, ensure_ascii=False).encode(
        "utf-8"
    )
    return content, "application/json"


def _export_csv(
    nodes: list[dict],
    tags_by_node: dict[str, list[dict]],
    extracted_by_node: dict[str, list[dict]],
    edges: list[dict],
    comments_by_node: dict[str, list[dict]],
    options: Any,
) -> tuple[bytes, str]:
    """Export nodes as CSV."""
    import csv

    output = io.StringIO()

    # Define CSV columns
    columns = ["id", "content", "source", "created_at", "author"]
    if options.include_tags:
        columns.append("tags")
    if options.include_extracted:
        columns.append("extracted_entities")
    if options.include_comments:
        columns.append("comment_count")

    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()

    for node in nodes:
        # Find source from tags_by_node
        source = node.get("source", "")
        if not source and node["id"] in tags_by_node:
            for tag in tags_by_node[node["id"]]:
                if tag["name"] == "source":
                    source = tag["value"]
                    break

        row = {
            "id": node["id"],
            "content": node["content"],
            "source": source,  # Always include source
            "created_at": node.get("created_at", ""),
            "author": node.get("author", ""),
        }

        if options.include_tags:
            tags = tags_by_node.get(node["id"], [])
            row["tags"] = "; ".join(f"{tag['name']}={tag['value']}" for tag in tags)

        if options.include_extracted and node["id"] in extracted_by_node:
            entities = []
            for entity in extracted_by_node[node["id"]]:
                entities.append(f"{entity['type']}:{entity['value']}")
            row["extracted_entities"] = "; ".join(entities)

        if options.include_comments:
            row["comment_count"] = len(comments_by_node.get(node["id"], []))

        writer.writerow(row)

    content = output.getvalue().encode("utf-8")
    return content, "text/csv"


def _export_stix(
    nodes: list[dict],
    tags_by_node: dict[str, list[dict]],
    extracted_by_node: dict[str, list[dict]],
    edges: list[dict],
    comments_by_node: dict[str, list[dict]],
    options: Any,
) -> tuple[bytes, str]:
    """Export nodes as STIX 2.1 JSON."""
    import uuid

    stix_bundle = {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "objects": [],
    }

    # Map nodes to STIX objects
    for node in nodes:
        # Determine STIX type based on tags or content
        stix_type = _determine_stix_type(
            node, tags_by_node.get(node["id"], []), extracted_by_node.get(node["id"], [])
        )

        # Find source from tags_by_node
        source = node.get("source", "")
        if not source and node["id"] in tags_by_node:
            for tag in tags_by_node[node["id"]]:
                if tag["name"] == "source":
                    source = tag["value"]
                    break

        stix_object = {
            "type": stix_type,
            "id": f"{stix_type}--{node['id']}",
            "created": node.get("created_at", datetime.utcnow().isoformat()),
            "modified": node.get("updated_at", datetime.utcnow().isoformat()),
            "name": node["content"][:100],  # Use first 100 chars as name
            "description": node["content"],
        }

        # Add labels (tags)
        if options.include_tags and node["id"] in tags_by_node:
            stix_object["labels"] = [
                f"{tag['name']}:{tag['value']}" for tag in tags_by_node[node["id"]]
            ]

        # Add custom properties
        stix_object["x_source"] = source  # Always include source
        if node.get("author"):
            stix_object["x_author"] = node["author"]

        # Add extracted entities as custom property
        if options.include_extracted and node["id"] in extracted_by_node:
            # Group entities by type
            entities_by_type = {}
            for entity in extracted_by_node[node["id"]]:
                entity_type = entity["type"]
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(entity["value"])
            stix_object["x_extracted"] = entities_by_type

        stix_bundle["objects"].append(stix_object)

    # Add relationships (edges) as STIX relationship objects
    if options.include_edges:
        for edge in edges:
            source_type = _determine_stix_type_by_id(
                edge["source_node_id"], nodes, tags_by_node
            )
            target_type = _determine_stix_type_by_id(
                edge["target_node_id"], nodes, tags_by_node
            )

            relationship = {
                "type": "relationship",
                "id": f"relationship--{edge['id']}",
                "created": edge.get("created_at", datetime.utcnow().isoformat()),
                "modified": edge.get("created_at", datetime.utcnow().isoformat()),
                "relationship_type": "related-to",
                "source_ref": f"{source_type}--{edge['source_node_id']}",
                "target_ref": f"{target_type}--{edge['target_node_id']}",
            }

            if edge.get("confidence"):
                relationship["confidence"] = edge["confidence"]
            if edge.get("evidence"):
                relationship["description"] = edge["evidence"]

            stix_bundle["objects"].append(relationship)

    content = json.dumps(stix_bundle, indent=2, ensure_ascii=False).encode(
        "utf-8"
    )
    return content, "application/json"


def _determine_stix_type(
    node: dict, tags: list[dict], extracted_entities: list[dict]
) -> str:
    """Determine STIX object type based on node content and tags."""
    tag_names = [tag["name"].lower() for tag in tags]

    # Check tags for hints
    if any("malware" in t for t in tag_names):
        return "malware"
    if any("threat-actor" in t or "apt" in t for t in tag_names):
        return "threat-actor"
    if any("tool" in t for t in tag_names):
        return "tool"
    if any("campaign" in t for t in tag_names):
        return "campaign"

    # Check extracted entities
    if extracted_entities:
        entity_types = {e["type"] for e in extracted_entities}
        if any(t in entity_types for t in ["ipv4", "ipv6", "domain"]):
            return "indicator"
        if any(t in entity_types for t in ["cve", "vulnerability"]):
            return "vulnerability"

    # Default to indicator
    return "indicator"


def _determine_stix_type_by_id(
    node_id: str, nodes: list[dict], tags_by_node: dict[str, list[dict]]
) -> str:
    """Determine STIX type for a node by its ID."""
    for node in nodes:
        if node["id"] == node_id:
            # Parse extracted if it's a JSON string
            extracted_data = None
            if node.get("extracted"):
                extracted_data = (
                    json.loads(node["extracted"])
                    if isinstance(node["extracted"], str)
                    else node["extracted"]
                )
            return _determine_stix_type(
                node, tags_by_node.get(node_id, []), extracted_data
            )
    return "indicator"  # Default fallback
