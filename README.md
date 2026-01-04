# Nodes

> A lightweight graph-based intelligence notebook for capturing, connecting, and searching unstructured threat intel.

## Overview

Nodes is a personal (and eventually team-based) knowledge graph designed for cyber threat intelligence professionals. It provides a fast, frictionless way to capture snippets of information—URLs, conversations, indicators, adversary references—and automatically discovers relationships between them over time.

Think of it as a "threat intel scratch pad" that builds its own connection map.

## Core Features

- **Quick Capture** - Add nodes (text blobs) with minimal friction; just paste/type and tag
- **Automatic Tagging** - Every node gets a `datetime` (auto) and `source` (required); custom tags are suggested from existing tags
- **Smart Auto-Linking** - Automatically finds related nodes by:
  - Matching tag values
  - Extracted indicators (IPs, domains, hashes, emails, URLs)
  - Named entities (threat actors, malware families, tools)
  - Content overlap
- **Edge Confidence Scoring** - Edges are weighted by match quality (exact IOC match = high, partial content = low)
- **Dual View Modes** - Toggle between:
  - **List View** - Traditional list with related nodes (depth 1)
  - **Graph View** - Visual node-edge graph with configurable depth
- **Powerful Search** - Query language supporting:
  - Freeform search (all fields)
  - Content-only search
  - Tag-targeted search (by name or value)

  Example: `content="*cobalt strike*" AND tag:source="*twitter*"`

- **Relationship Notifications** - Get notified when new connections are discovered ("Found 5 related nodes!")
- **Threat Actor Normalization** - Uses Microsoft threat actor naming as the canonical standard, with alias mapping (e.g., "Fancy Bear" → "Forest Blizzard")

## Planned Features

- Import/Export (JSON, CSV, STIX)
- Multi-user support with centralized deployment
- API access for automation

## Architecture

### Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Database** | SQLite + FTS5 | Zero-config, portable single file, powerful full-text search, easy backup. Future multi-user can swap to PostgreSQL. |
| **Backend** | Python 3.14+ / FastAPI | Cross-platform, async, excellent for regex/NLP extraction, easy to extend. |
| **Frontend** | React 19 + Vite + Tailwind CSS | Modern, fast, huge ecosystem, excellent Chrome support, utility-first styling. |
| **Graph Visualization** | Cytoscape.js | Mature, performant, supports depth expansion, great layout algorithms. |
| **Entity Extraction** | Regex + curated lists | IOCs via regex patterns; threat actors/malware via curated lists (Microsoft naming, Malpedia). |

### Project Structure

```
nodes/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── api/
│   │   │   ├── nodes.py         # Node CRUD endpoints
│   │   │   ├── tags.py          # Tag endpoints
│   │   │   ├── edges.py         # Edge endpoints
│   │   │   └── search.py        # Search endpoint
│   │   ├── core/
│   │   │   ├── config.py        # App configuration
│   │   │   └── database.py      # SQLite connection
│   │   ├── extractors/
│   │   │   ├── ioc.py           # IOC regex patterns
│   │   │   └── entities.py      # Named entity matching
│   │   ├── linker/
│   │   │   └── auto_link.py     # Auto-linking logic
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   └── data/
│   │       ├── threat_actors.json
│   │       └── malware.json
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── NodeForm.tsx
│   │   │   ├── NodeList.tsx
│   │   │   ├── GraphView.tsx
│   │   │   └── SearchBar.tsx
│   │   ├── hooks/
│   │   ├── api/
│   │   └── App.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── README.md
└── Makefile                     # Convenience commands
```

### Data Model

```
nodes
├── id (UUID, PK)
├── content (TEXT) ─────────────► FTS5 indexed
├── created_at (DATETIME)
└── updated_at (DATETIME)

tags
├── id (UUID, PK)
├── node_id (FK → nodes)
├── name (TEXT) ────────────────► e.g., "source", "adversary", "campaign"
└── value (TEXT) ───────────────► FTS5 indexed

edges
├── id (UUID, PK)
├── source_node_id (FK → nodes)
├── target_node_id (FK → nodes)
├── edge_type (TEXT) ───────────► "tag_match", "ioc_match", "entity_match", "manual"
├── match_value (TEXT) ─────────► The actual value that caused the link
├── confidence (FLOAT) ─────────► 0.0 - 1.0 score
└── created_at (DATETIME)

extracted
├── id (UUID, PK)
├── node_id (FK → nodes)
├── type (TEXT) ────────────────► "ipv4", "ipv6", "domain", "url", "hash_md5",
│                                  "hash_sha1", "hash_sha256", "email",
│                                  "threat_actor", "malware", "tool"
├── value (TEXT) ───────────────► The extracted value (normalized)
├── raw_value (TEXT) ───────────► Original value as found in content
└── canonical_value (TEXT) ─────► For aliases: the canonical name (e.g., "Forest Blizzard")

threat_actor_aliases (reference table)
├── alias (TEXT, PK) ───────────► e.g., "Fancy Bear", "APT28", "Sofacy"
└── canonical_name (TEXT) ──────► e.g., "Forest Blizzard"
```

### Edge Confidence Scoring

| Match Type | Confidence | Description |
|------------|------------|-------------|
| Exact IOC match | 1.0 | Same IP, hash, domain, etc. |
| Threat actor (canonical) | 1.0 | Same normalized actor name |
| Threat actor (alias resolved) | 0.9 | Matched via alias → canonical |
| Exact tag value match | 0.8 | Same tag name and value |
| URL domain match | 0.7 | Same domain, different paths |
| Partial content overlap | 0.3 - 0.6 | Significant shared keywords |
| Manual link | 1.0 | User-created edge |

## Installation

### Prerequisites

- **Python 3.14+** - [Download](https://www.python.org/downloads/)
- **Node.js 22+** - [Download](https://nodejs.org/) (for frontend build)
- **Docker** (optional) - [Download](https://www.docker.com/products/docker-desktop/) (for containerized deployment)

---

### Option 1: Docker (Recommended)

The easiest way to run Nodes is with Docker. This works on **Windows**, **macOS**, and **Linux**.

```bash
# Clone the repository
git clone <repo-url>
cd nodes

# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up --build

# Or using make (if you have make installed)
make docker-up
```

The application will be available at `http://localhost:8000`.

**Stopping the container:**
```bash
docker-compose -f docker/docker-compose.yml down
# Or: make docker-down
```

**Viewing logs:**
```bash
docker-compose -f docker/docker-compose.yml logs -f
# Or: make docker-logs
```

---

### Option 2: Manual Installation

#### Linux / macOS

```bash
# Clone the repository
git clone <repo-url>
cd nodes

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
npm run build

# Run the application
cd ../backend
source venv/bin/activate
python -m app.main
```

#### Windows (Command Prompt)

```cmd
:: Clone the repository
git clone <repo-url>
cd nodes

:: Backend setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

:: Frontend setup
cd ..\frontend
npm install
npm run build

:: Run the application
cd ..\backend
venv\Scripts\activate
python -m app.main
```

#### Windows (PowerShell)

```powershell
# Clone the repository
git clone <repo-url>
cd nodes

# Backend setup
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Frontend setup
cd ..\frontend
npm install
npm run build

# Run the application
cd ..\backend
.\venv\Scripts\Activate.ps1
python -m app.main
```

---

### Option 3: Using Make (Linux/macOS)

If you have `make` installed:

```bash
# Install all dependencies
make install

# Build frontend
make build

# Run the application
make run
```

For Windows users with Make installed, use the `-win` variants:
```cmd
make install-backend-win
make install-frontend
make build
make run-backend-win
```

---

### Development Mode

For development with hot-reload:

**Terminal 1 - Backend:**
```bash
# Linux/macOS
cd backend && source venv/bin/activate && NODES_DEBUG=true python -m app.main

# Windows (Command Prompt)
cd backend && venv\Scripts\activate && set NODES_DEBUG=true && python -m app.main

# Windows (PowerShell)
cd backend; .\venv\Scripts\Activate.ps1; $env:NODES_DEBUG="true"; python -m app.main
```

**Terminal 2 - Frontend:**
```bash
cd frontend && npm run dev
```

The frontend dev server runs at `http://localhost:5173` and proxies API requests to the backend.

---

### Environment Configuration

Copy `.env.example` to `.env` to customize settings:

```bash
cp .env.example .env
```

Available options:
| Variable | Default | Description |
|----------|---------|-------------|
| `NODES_DEBUG` | `false` | Enable debug mode with hot-reload |
| `NODES_HOST` | `0.0.0.0` | Host to bind to |
| `NODES_PORT` | `8000` | Port to listen on |
| `NODES_DATABASE_PATH` | `data/nodes.db` | SQLite database file path |
| `NODES_CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:8000"]` | Allowed CORS origins |

## Quick Start Guide

1. Start the application and open `http://localhost:8000` in your browser
2. Click **New Node** to create your first entry
3. Paste or type your intel snippet
4. Add a source (URL, person, file path, etc.)
5. Optionally add custom tags (suggestions appear from existing tags)
6. Save - the system will automatically find and link related nodes
7. Use the **List/Graph** toggle to explore connections
8. Use the search bar with the query syntax to find nodes later

## Search Syntax

| Query | Description |
|-------|-------------|
| `*keyword*` | Search everywhere (content + tags) |
| `content="*text*"` | Search node content only |
| `tag:name="value"` | Search for specific tag with value |
| `tag:name=*` | Find all nodes with a specific tag |
| `tag-value="*partial*"` | Search all tag values |
| `AND` / `OR` | Combine conditions |

## FAQ

### What kind of data should I put in a node?

Anything that might be useful later: a snippet from a blog post, IOCs from a report, notes from a conversation, a reference to a threat actor, a suspicious URL—if it's worth remembering, it's worth a node.

### How does auto-linking work?

When you save a node, the system extracts:
- **Indicators**: IPs, domains, URLs, file hashes (MD5/SHA1/SHA256), email addresses
- **Named entities**: Threat actor names (normalized to Microsoft naming), malware families, tool names
- **Tag values**: Exact matches on tag values

It then searches existing nodes for matches and creates edges with confidence scores automatically.

### What is the Microsoft threat actor naming convention?

Microsoft uses weather-themed names for threat actors (e.g., "Forest Blizzard" instead of "APT28" or "Fancy Bear"). Nodes uses this as the canonical naming standard but recognizes aliases, so entering "APT28" will still link to nodes mentioning "Forest Blizzard".

### Can I manually link nodes?

Yes - in addition to auto-linking, you can manually create edges between any two nodes. Manual edges have a confidence score of 1.0.

### Is my data stored locally?

Yes, by default everything is stored in a local SQLite database file. For team deployment, a centralized server option will be available.

### Will this work offline?

Yes, the application runs entirely locally and requires no internet connection.

---

## License

MIT (TBD)
