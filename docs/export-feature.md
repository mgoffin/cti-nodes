# Export Feature - Phase 1 Implementation

## Overview

The export feature allows users to export nodes in multiple formats: JSON, CSV, and STIX 2.1. This document describes the Phase 1 implementation.

## Features Implemented

### Backend

**Export API Endpoints** (`backend/app/api/export.py`):
- `POST /api/export/preview` - Preview what will be exported before generating the file
- `POST /api/export` - Export nodes in the specified format

**Export Options** (`backend/app/models/schemas.py`):
```python
class ExportOptions(BaseModel):
    format: str                      # json, csv, or stix
    include_tags: bool              # Include tags
    include_system_tags: bool       # Include system tags (datetime, source)
    include_extracted: bool         # Include extracted entities
    include_edges: bool             # Include relationships/edges
    include_comments: bool          # Include comments
    include_related_nodes: bool     # Include related nodes
    related_depth: int              # Depth for related nodes (1-3)
    entity_types: list[str] | None  # Filter specific entity types
```

**Export Formats**:

1. **JSON**: Full structured export with metadata
   - Export metadata (format, version, timestamp, counts)
   - Node data (id, content, source, timestamps, author)
   - Optional: tags, extracted entities, comments
   - Optional: edges/relationships

2. **CSV**: Tabular export for analysis
   - Columns: id, content, source, created_at, author
   - Optional columns: tags, extracted_entities, comment_count
   - Tags and entities are semicolon-separated

3. **STIX 2.1 JSON**: Standards-compliant threat intelligence format
   - STIX Bundle wrapper with unique bundle ID
   - Nodes mapped to STIX objects (indicator, malware, threat-actor, tool, campaign)
   - Automatic type detection based on tags and extracted entities
   - Relationships exported as STIX relationship objects
   - Custom properties for source, author, extracted entities

### Frontend

**Export Components**:

1. **ExportButton** (`frontend/src/components/ExportButton.tsx`)
   - Dropdown menu with format selection (JSON/CSV/STIX)
   - Opens preview modal before export
   - Handles download with auto-generated filename

2. **ExportPreviewModal** (`frontend/src/components/ExportPreviewModal.tsx`)
   - Shows preview statistics (node count, tag count, entity count, etc.)
   - Export options configuration:
     - Include/exclude tags, system tags, extracted entities, edges, comments
     - Include related nodes with depth selector (1-3)
     - Entity type filter with select all/deselect all
   - Warnings for large exports or many related nodes
   - Live preview updates as options change

3. **Node Selection in Dashboard** (`frontend/src/components/Dashboard.tsx`)
   - "Select Nodes" button to enable selection mode
   - "Select All" / "Deselect All" toggle
   - Export button appears when nodes are selected
   - Selection counter in header

4. **Node Selection in NodeList** (`frontend/src/components/NodeList.tsx`)
   - Checkbox column when in selection mode
   - Individual node selection
   - Preserves link navigation while in selection mode

5. **Export Button in NodeDetail** (`frontend/src/components/NodeDetail.tsx`)
   - Export button next to Delete button
   - Exports single node with all options

## Usage

### Exporting from Node Detail Page

1. Navigate to a node
2. Click "Export" button
3. Select format (JSON/CSV/STIX)
4. Configure export options in preview modal
5. Click "Export" to download

### Exporting from Dashboard

1. Go to Dashboard (or search results)
2. Click "Select Nodes" button
3. Check boxes next to nodes to export (or use "Select All")
4. Click "Export" button that appears
5. Select format and configure options
6. Click "Export" to download

## Export Preview

Before exporting, users see:
- **Counts**: Nodes, tags, entities, edges, comments, related nodes
- **Estimated Size**: Approximate file size in KB or MB
- **Warnings**: Alerts for large exports or many related nodes
- **Options**: Configure what to include in export

## STIX 2.1 Compliance

### Object Type Mapping

The system automatically determines STIX object types based on:
- **Tags**: malware tags → `malware` object, threat-actor/APT tags → `threat-actor`, etc.
- **Extracted Entities**: IPs/domains/URLs → `indicator`, CVEs → `vulnerability`
- **Default**: `indicator` if no specific type detected

### STIX Bundle Structure

```json
{
  "type": "bundle",
  "id": "bundle--<uuid>",
  "objects": [
    {
      "type": "indicator",
      "id": "indicator--<node-id>",
      "created": "2024-01-01T00:00:00Z",
      "modified": "2024-01-01T00:00:00Z",
      "name": "Node content (first 100 chars)",
      "description": "Full node content",
      "labels": ["tag1", "tag2"],
      "x_source": "Source URL/reference",
      "x_author": "analyst@example.com",
      "x_extracted": {"ipv4": ["1.2.3.4"], "domain": ["example.com"]}
    }
  ]
}
```

### Relationships

When `include_edges` is enabled, edges are exported as STIX `relationship` objects:
```json
{
  "type": "relationship",
  "id": "relationship--<edge-id>",
  "relationship_type": "related-to",
  "source_ref": "indicator--<source-node-id>",
  "target_ref": "threat-actor--<target-node-id>",
  "confidence": 85,
  "description": "Evidence text"
}
```

## File Naming

Auto-generated filenames follow the pattern:
```
nodes_export_YYYYMMDD_HHMMSS.<extension>
```

Examples:
- `nodes_export_20240315_143022.json`
- `nodes_export_20240315_143022.csv`
- `nodes_export_20240315_143022.json` (STIX uses .json extension)

## Performance Considerations

- **Large Exports**: Warning shown when export exceeds 10 MB
- **Related Nodes**: Warning when including 100+ related nodes
- **Related Depth**: Limit of 3 levels to prevent exponential growth
- **Preview**: Lightweight preview calculation before full export generation

## API Examples

### Export Preview Request

```bash
curl -X POST http://localhost:8000/api/export/preview \
  -H "Content-Type: application/json" \
  -d '{
    "node_ids": ["node-1", "node-2"],
    "options": {
      "format": "json",
      "include_tags": true,
      "include_system_tags": true,
      "include_extracted": true,
      "include_edges": false,
      "include_comments": false,
      "include_related_nodes": false,
      "related_depth": 1,
      "entity_types": null
    }
  }'
```

### Export Request

```bash
curl -X POST http://localhost:8000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "node_ids": ["node-1", "node-2"],
    "options": {
      "format": "stix",
      "include_tags": true,
      "include_system_tags": false,
      "include_extracted": true,
      "include_edges": true,
      "include_comments": true,
      "include_related_nodes": true,
      "related_depth": 2,
      "entity_types": ["ipv4", "domain", "malware"]
    }
  }' \
  --output export.json
```

## Potential Future Enhancements

> **Note**: These are ideas for potential future improvements that may or may not be implemented based on user needs and priorities.

### Phase 2 Ideas (Enhanced Features)
- **Date range filtering** - Export nodes created/updated within a specific time period
- **More advanced STIX mappings** - Better automatic detection and mapping to STIX object types
- **CSV field customization UI** - Let users choose which fields to include in CSV exports
- **Export templates/presets** - Save common export configurations for quick reuse

### Phase 3 Ideas (Advanced Features)
- **Save export configurations per user** - User-specific saved presets stored in database
- **Chunked exports for very large datasets** - Stream large exports to handle 1000+ nodes
- **Scheduled/automated exports** - Periodic exports or webhook-triggered exports
- **Advanced STIX relationship types** - More specific relationship mappings beyond "related-to"
- **TLP markings integration** - Add Traffic Light Protocol (TLP) markings to STIX exports

## Testing

To test the export feature:

1. **Create test nodes** with various content, tags, and entities
2. **Test single node export** from NodeDetail page
3. **Test bulk export** from Dashboard with selection
4. **Test different formats** (JSON, CSV, STIX)
5. **Test with options**:
   - Include/exclude tags, entities, edges, comments
   - Include related nodes at different depths
   - Filter by entity types
6. **Test edge cases**:
   - Empty selections
   - Large exports (100+ nodes)
   - Deep related node graphs (depth 3)
   - Nodes with no tags/entities/edges/comments

## Known Limitations

- CSV format doesn't preserve nested structures (edges, comments are simplified)
- STIX type detection is heuristic-based (may need manual review for accuracy)
- Related node depth limited to 3 to prevent performance issues
- Large exports (>10 MB) may take time to generate

## Source Files

**Backend**:
- `backend/app/api/export.py` - Export API endpoints and logic
- `backend/app/models/schemas.py` - Export request/response schemas (lines 308-337)
- `backend/app/api/__init__.py` - Router registration (line 20)

**Frontend**:
- `frontend/src/components/ExportButton.tsx` - Export button with dropdown
- `frontend/src/components/ExportPreviewModal.tsx` - Preview and options modal
- `frontend/src/components/Dashboard.tsx` - Selection mode and bulk export
- `frontend/src/components/NodeList.tsx` - Checkbox support
- `frontend/src/components/NodeDetail.tsx` - Single node export
- `frontend/src/api/client.ts` - Export API client (lines 256-267)
- `frontend/src/types/index.ts` - Export TypeScript types (lines 210-230)
