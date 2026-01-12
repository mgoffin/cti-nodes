# Nodes

> A lightweight graph-based intelligence notebook for capturing, connecting, and searching unstructured threat intel.

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Chrome Extension](#chrome-extension)
- [Planned Features](#planned-features)
- [Authentication & Multi-User Support](#authentication--multi-user-support-optional)
- [Architecture](#architecture)
  - [Tech Stack](#tech-stack)
  - [Project Structure](#project-structure)
  - [Data Model](#data-model)
  - [Supported Entity Types](#supported-entity-types)
  - [Edge Confidence Scoring](#edge-confidence-scoring)
- [Installation](#installation)
  - [Option 1: Docker (Recommended)](#option-1-docker-recommended)
  - [Option 2: Podman (Docker Alternative)](#option-2-podman-docker-alternative)
  - [Option 3: Manual Installation](#option-3-manual-installation)
  - [Option 4: Using Make](#option-4-using-make-linuxmacos)
  - [Development Mode](#development-mode)
  - [Environment Configuration](#environment-configuration)
- [Production Deployment](#production-deployment)
- [Quick Start Guide](#quick-start-guide)
- [Search Syntax](#search-syntax)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [License](#license)

---

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
- **Entity Validation** - Automatically detects and suggests corrections for:
  - Type mismatches (e.g., filename labeled as domain)
  - Defanged IOCs that should be refanged (e.g., `192[.]168[.]1[.]1` → `192.168.1.1`)
- **Dark/Light Theme** - Toggle between dark and light modes for comfortable viewing
- **Comments** - Add markdown-formatted comments to nodes for collaboration and documentation

## Chrome Extension

The Nodes Chrome Extension allows you to capture content and search directly from any webpage. Perfect for quickly adding IOCs, articles, or threat intel snippets while browsing.

### Features

- **Add to Nodes** - Right-click selected text to create a new node with the page URL as source
- **Search Value** - Quickly search for highlighted text in your Nodes database
- **Search Source** - Find all nodes that reference the current page URL
- **Toast Notifications** - Get instant feedback with links to newly created nodes
- **Configurable** - Set custom API and frontend URLs for any deployment

### Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked" and select the `chrome_extension` folder
4. Click the extension icon to configure your API and frontend URLs
5. Start right-clicking!

See [chrome_extension/README.md](chrome_extension/README.md) for detailed instructions and troubleshooting.

## Planned Features

- Import/Export (JSON, CSV, STIX)
- Multi-user support with centralized deployment (authentication now available!)
- API access for automation

## Authentication & Multi-User Support (Optional)

Nodes supports optional SSO-based authentication for team deployments. When disabled (default), the platform runs in single-user mode with no authentication required.

### Quick Auth Setup

**1. Enable authentication:**
```bash
# Set in .env or environment
NODES_AUTH_ENABLED=true
NODES_SSO_PROVIDER=duo  # or okta, azure, google
```

**2. Configure your SSO provider:**
```bash
# Duo example
NODES_SSO_CLIENT_ID=your_client_id
NODES_SSO_CLIENT_SECRET=your_client_secret
NODES_SSO_REDIRECT_URI=http://localhost:8000/api/auth/callback

# Or use generic OIDC endpoints
NODES_SSO_AUTHORIZATION_URL=https://...
NODES_SSO_TOKEN_URL=https://...
NODES_SSO_USERINFO_URL=https://...
```

**3. Run database migration:**
```bash
cd backend
python migrate_v2_users.py
```

**4. Restart the application - first user to log in becomes administrator!**

### Features When Auth Enabled

- **SSO Authentication** - Supports Duo, Okta, Azure AD, Google (via generic OIDC)
- **Role-Based Access Control** - 3 roles: Administrator, Analyst, Viewer
  - **Administrator** - Full access, user management, audit logs
  - **Analyst** - Create/edit/delete own content, view all content
  - **Viewer** - Read-only access to all content
- **Ownership Model** - Content owned by creator, admins can modify anything
- **Audit Logging** - All modifications tracked (optional, configurable retention)
- **Session Management** - View and revoke active sessions
- **User Profiles** - Customize display name, avatar, theme preference
- **SSO Health Monitoring** - Fallback modes when SSO is unavailable

### Environment Variables

See `.env.example` for complete configuration. Key settings:

```bash
# Authentication
NODES_AUTH_ENABLED=false              # Enable/disable authentication
NODES_SSO_PROVIDER=duo                # duo, okta, azure, google
NODES_SSO_DISPLAY_NAME="Duo Security" # Friendly name shown in UI
NODES_SSO_CLIENT_ID=...               # OAuth client ID
NODES_SSO_CLIENT_SECRET=...           # OAuth client secret
NODES_SSO_REDIRECT_URI=...            # Callback URL

# Security
NODES_JWT_SECRET_KEY=...              # Generate with: openssl rand -hex 32
NODES_ACCESS_TOKEN_EXPIRE_MINUTES=15  # Access token lifetime
NODES_REFRESH_TOKEN_EXPIRE_DAYS=7     # Refresh token lifetime

# Audit Logging (when auth enabled)
NODES_AUDIT_LOG_ENABLED=true          # Enable audit logging
NODES_AUDIT_LOG_RETENTION_DAYS=90     # Keep logs for 90 days

# SSO Fallback (when SSO is down)
NODES_SSO_FALLBACK_MODE=require_sso   # require_sso or fallback_anonymous
```

### Migration from Single-User to Multi-User

The migration script (`migrate_v2_users.py`) adds authentication tables and assigns ownership:

1. **Backs up your database** to `nodes.db.backup.TIMESTAMP`
2. **Adds new tables**: `users`, `sessions`, `audit_log`, `user_preferences`
3. **Adds author columns** to `nodes`, `tags`, `extracted`, `edges`
4. **Assigns existing content** to "Anonymous" author
5. **Creates indexes** for performance
6. **Rebuilds FTS indexes** (can take ~1s per 10k nodes)

Run with:
```bash
cd backend
python migrate_v2_users.py
```

**Migration is idempotent** - safe to run multiple times. If auth columns already exist, it skips gracefully.

### Backward Compatibility

**The platform is fully functional without authentication enabled.** When `NODES_AUTH_ENABLED=false`:

- No login required
- All users are implicit administrators
- All operations allowed
- No audit logging
- Content authored as "Anonymous"

This ensures existing single-user deployments continue working without changes.

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
cti-nodes/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── api/
│   │   │   ├── nodes.py         # Node CRUD endpoints
│   │   │   ├── tags.py          # Tag endpoints
│   │   │   ├── edges.py         # Edge endpoints
│   │   │   ├── search.py        # Search endpoint
│   │   │   └── extracted.py     # Extracted entity endpoints
│   │   ├── core/
│   │   │   ├── config.py        # App configuration
│   │   │   └── database.py      # SQLite connection
│   │   ├── extractors/
│   │   │   ├── ioc.py           # IOC regex patterns
│   │   │   ├── entities.py      # Named entity matching
│   │   │   └── defang.py        # Defang/refang utilities
│   │   ├── validators/
│   │   │   ├── entity_validator.py  # Entity type validation
│   │   │   └── tag_suggester.py     # Tag autocomplete
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
│   │   │   ├── Layout.tsx       # App layout with navigation
│   │   │   ├── Dashboard.tsx    # Main dashboard view
│   │   │   ├── NodeList.tsx     # Node list display
│   │   │   ├── NodeDetail.tsx   # Single node view
│   │   │   ├── NewNode.tsx      # Create node form
│   │   │   ├── GraphView.tsx    # Cytoscape graph visualization
│   │   │   ├── SearchBar.tsx    # Search input component
│   │   │   ├── TagManager.tsx   # Tag editing interface
│   │   │   └── ExtractedManager.tsx  # Entity management
│   │   ├── hooks/
│   │   │   └── useTheme.tsx     # Dark/light theme toggle
│   │   ├── api/
│   │   │   └── client.ts        # API client functions
│   │   ├── utils/
│   │   │   ├── formatters.ts    # Display formatting utilities
│   │   │   └── entityColors.ts  # Entity highlight colors
│   │   ├── types/
│   │   │   └── index.ts         # TypeScript type definitions
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
├── type (TEXT) ────────────────► Entity types (see table below)
├── value (TEXT) ───────────────► The extracted value (normalized)
├── raw_value (TEXT) ───────────► Original value as found in content
└── canonical_value (TEXT) ─────► For aliases: the canonical name (e.g., "Forest Blizzard")

### Supported Entity Types

| Internal Name | Display Name | Description |
|--------------|--------------|-------------|
| `ipv4` | IPv4 | IPv4 addresses (e.g., `192.168.1.1`) |
| `ipv6` | IPv6 | IPv6 addresses |
| `domain` | Domain | Domain names (e.g., `evil.com`) |
| `url` | URL | Full URLs (e.g., `https://evil.com/payload`) |
| `hash_md5` | MD5 | MD5 hashes (32 hex chars) |
| `hash_sha1` | SHA1 | SHA1 hashes (40 hex chars) |
| `hash_sha256` | SHA256 | SHA256 hashes (64 hex chars) |
| `email` | Email | Email addresses |
| `cve` | CVE | CVE identifiers (e.g., `CVE-2024-1234`) |
| `filename` | Filename | Filenames with extensions (e.g., `malware.exe`) |
| `file_path` | Filepath | Full file paths |
| `threat_actor` | Threat Actor | Threat actor names (normalized to Microsoft naming) |
| `malware` | Malware | Malware family names |
| `tool` | Tool | Tool names (e.g., Cobalt Strike, Mimikatz) |
| `campaign` | Campaign | Campaign names |
| `registry_key` | Registry Key | Windows registry keys |
| `mutex` | Mutex | Mutex names |
| `user_agent` | User-Agent | HTTP User-Agent strings |
| `asn` | ASN | Autonomous System Numbers |
| `country` | Country | Country codes/names |
| `mitre_attack` | ATT&CK | MITRE ATT&CK technique IDs |

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

> **Note:** The GitHub repository is named `cti-nodes`. When you clone it, your directory will be `cti-nodes/`. All examples below reflect this naming.

---

### Option 1: Docker (Recommended)

The easiest way to run Nodes is with Docker. This works on **Windows**, **macOS**, and **Linux**.

#### Step 1: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/mgoffin/cti-nodes.git
cd cti-nodes
```

#### Step 2: Configure Environment (Optional)

Before building the container, create a `.env` file to customize settings. This is especially important if you want to enable authentication or change default ports.

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your preferred settings
# Key settings to configure before building:
```

**Basic Configuration:**
```bash
# Application
NODES_DEBUG=false
NODES_HOST=0.0.0.0
NODES_PORT=8000

# Database path (inside container)
NODES_DATABASE_PATH=/app/data/nodes.db
```

**Authentication Configuration (if enabling SSO):**

See the [Authentication & Multi-User Support](#authentication--multi-user-support-optional) section above for complete SSO setup. You must configure these BEFORE building:

```bash
NODES_AUTH_ENABLED=true
NODES_SSO_PROVIDER=duo  # duo, okta, azure, google
NODES_SSO_DISPLAY_NAME="Your Company SSO"
NODES_SSO_CLIENT_ID=your_client_id_here
NODES_SSO_CLIENT_SECRET=your_client_secret_here
NODES_SSO_REDIRECT_URI=https://your-domain.com/api/auth/callback

# Generate a secure secret key
NODES_JWT_SECRET_KEY=your_generated_secret_here  # openssl rand -hex 32
```

**CORS Configuration (if accessing from different domain):**
```bash
NODES_CORS_ORIGINS=["http://localhost:5173","https://your-domain.com"]
```

#### Step 3: Build and Run

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up --build

# Or run in detached mode (background)
docker-compose -f docker/docker-compose.yml up -d --build

# Or using make (if you have make installed)
make docker-up
```

The application will be available at `http://localhost:8000`.

#### Step 4: Database Migration (if enabling authentication)

If you're enabling authentication on an existing database, run the migration script inside the container:

```bash
# Access the running container
docker exec -it nodes-app /bin/bash

# Run migration
cd /app/backend
python migrate_v2_users.py

# Exit container
exit
```

#### Docker Management Commands

**Development Mode (Hot-Reload):**

For active development, use the development compose file which mounts your source code for instant updates:

```bash
# Start in development mode
docker-compose -f docker/docker-compose.dev.yml up --build

# The container will:
# - Mount your source code as volumes
# - Auto-reload backend when Python files change
# - Auto-reload frontend when TypeScript/React files change
# - Expose backend on http://localhost:8000
# - Expose frontend dev server on http://localhost:5173
```

After initial build, you can start without `--build` for faster startup:
```bash
docker-compose -f docker/docker-compose.dev.yml up
```

Code changes will be reflected immediately without rebuilding! Use `Ctrl+C` to stop.

**Production Mode:**

**Stopping the container:**
```bash
docker-compose -f docker/docker-compose.yml down
# Or: make docker-down
```

**Viewing logs:**
```bash
docker-compose -f docker/docker-compose.yml logs -f
# Or: make docker-logs

# For development mode logs:
docker-compose -f docker/docker-compose.dev.yml logs -f
```

**Restarting after config changes:**
```bash
# If you changed .env, restart the container
docker-compose -f docker/docker-compose.yml restart

# If you changed code or Dockerfile, rebuild (production)
docker-compose -f docker/docker-compose.yml up -d --build

# Development mode: no rebuild needed for code changes!
# Just save your files and they'll hot-reload
```

**Accessing the container shell:**
```bash
docker exec -it nodes-app /bin/bash
```

**Backing up your data:**
```bash
# The database is stored in a Docker volume named 'nodes-data'
# Create a backup by copying from the volume
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    tar czf /backup/nodes-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .

# On Windows PowerShell:
docker run --rm -v nodes-data:/data -v ${PWD}:/backup alpine tar czf /backup/nodes-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').tar.gz -C /data .
```

**Restoring from backup:**
```bash
# Stop the container first
docker-compose -f docker/docker-compose.yml down

# Extract backup into volume
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    tar xzf /backup/nodes-backup-YYYYMMDD-HHMMSS.tar.gz -C /data

# Restart container
docker-compose -f docker/docker-compose.yml up -d
```

---

### Option 2: Podman (Docker Alternative)

Podman is a daemonless container engine that's compatible with Docker commands. It's especially popular on RHEL/Fedora systems and offers rootless container execution for better security.

#### Installing Podman

**Linux (Fedora/RHEL/CentOS):**
```bash
sudo dnf install podman podman-compose
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install podman podman-compose
```

**macOS:**
```bash
brew install podman podman-compose
podman machine init
podman machine start
```

**Windows:**
Download the installer from [Podman Desktop](https://podman-desktop.io/) or use Chocolatey:
```powershell
choco install podman-desktop
```

#### Step 1: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/mgoffin/cti-nodes.git
cd cti-nodes

# Configure environment (same as Docker)
cp .env.example .env
# Edit .env with your settings (see Docker section above)
```

#### Step 2: Build and Run with Podman

Podman commands are nearly identical to Docker:

```bash
# Build and run with podman-compose
podman-compose -f docker/docker-compose.yml up --build

# Or run in detached mode
podman-compose -f docker/docker-compose.yml up -d --build
```

**Alternative: Use Podman directly without compose:**

```bash
# Build the image
podman build -t nodes-app -f docker/Dockerfile .

# Create a volume for data persistence
podman volume create nodes-data

# Run the container
podman run -d \
  --name nodes-app \
  -p 8000:8000 \
  -v nodes-data:/app/data:Z \
  --env-file .env \
  nodes-app

# The :Z flag is important for SELinux systems (Fedora/RHEL)
```

#### Step 3: Database Migration (if enabling authentication)

```bash
# Access the running container
podman exec -it nodes-app /bin/bash

# Run migration
cd /app/backend
python migrate_v2_users.py
exit
```

#### Podman Management Commands

**Stopping the container:**
```bash
podman-compose -f docker/docker-compose.yml down
# Or: podman stop nodes-app
```

**Viewing logs:**
```bash
podman-compose -f docker/docker-compose.yml logs -f
# Or: podman logs -f nodes-app
```

**Restarting after config changes:**
```bash
podman-compose -f docker/docker-compose.yml restart
# Or: podman restart nodes-app
```

**Accessing the container shell:**
```bash
podman exec -it nodes-app /bin/bash
```

**Backing up your data:**
```bash
# Podman volumes work the same as Docker
podman run --rm -v nodes-data:/data -v $(pwd):/backup:Z alpine \
    tar czf /backup/nodes-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
```

**Restoring from backup:**
```bash
podman-compose -f docker/docker-compose.yml down
podman run --rm -v nodes-data:/data -v $(pwd):/backup:Z alpine \
    tar xzf /backup/nodes-backup-YYYYMMDD-HHMMSS.tar.gz -C /data
podman-compose -f docker/docker-compose.yml up -d
```

#### Podman-Specific Features

**Rootless mode (Linux):**
Podman runs containers without root privileges by default, enhancing security:
```bash
# Check if running rootless
podman info | grep rootless

# All commands work the same, but containers run as your user
podman run -d --name nodes-app -p 8000:8000 nodes-app
```

**Generate systemd service (Linux):**
Run Nodes as a system service that starts on boot:
```bash
# Generate service file
podman generate systemd --new --name nodes-app > ~/.config/systemd/user/nodes-app.service

# Enable and start service
systemctl --user daemon-reload
systemctl --user enable nodes-app.service
systemctl --user start nodes-app.service

# Check status
systemctl --user status nodes-app.service
```

**Podman Desktop (GUI):**
For users preferring a graphical interface, [Podman Desktop](https://podman-desktop.io/) provides a Docker Desktop-like experience with container management, image building, and volume inspection.

---

### Option 3: Manual Installation

If you prefer not to use containers or need a development environment, you can install Nodes directly on your system.

#### Linux / macOS

```bash
# Clone the repository
git clone https://github.com/mgoffin/cti-nodes.git
cd cti-nodes

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
git clone https://github.com/mgoffin/cti-nodes.git
cd cti-nodes

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
git clone https://github.com/mgoffin/cti-nodes.git
cd cti-nodes

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

### Option 4: Using Make (Linux/macOS)

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

Nodes uses environment variables for configuration. Copy `.env.example` to `.env` to customize settings:

```bash
cp .env.example .env
```

#### Core Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `NODES_DEBUG` | `false` | Enable debug mode with hot-reload |
| `NODES_HOST` | `0.0.0.0` | Host to bind to (0.0.0.0 = all interfaces) |
| `NODES_PORT` | `8000` | Port to listen on |
| `NODES_DATABASE_PATH` | `data/nodes.db` | SQLite database file path |
| `NODES_CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:8000"]` | Allowed CORS origins (JSON array) |

#### Authentication Settings (Optional)

See the [Authentication & Multi-User Support](#authentication--multi-user-support-optional) section for complete details.

| Variable | Default | Description |
|----------|---------|-------------|
| `NODES_AUTH_ENABLED` | `false` | Enable/disable authentication |
| `NODES_SSO_PROVIDER` | `duo` | SSO provider: duo, okta, azure, google |
| `NODES_SSO_DISPLAY_NAME` | `"Duo Security"` | Friendly name shown in login UI |
| `NODES_SSO_CLIENT_ID` | - | OAuth client ID from your SSO provider |
| `NODES_SSO_CLIENT_SECRET` | - | OAuth client secret (keep secure!) |
| `NODES_SSO_REDIRECT_URI` | - | Callback URL (e.g., `https://nodes.example.com/api/auth/callback`) |
| `NODES_JWT_SECRET_KEY` | - | Secret key for JWT signing (generate with `openssl rand -hex 32`) |
| `NODES_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime (short for security) |
| `NODES_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

#### Audit Logging Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `NODES_AUDIT_LOG_ENABLED` | `true` | Enable audit logging (when auth enabled) |
| `NODES_AUDIT_LOG_RETENTION_DAYS` | `90` | Keep audit logs for N days |

#### Rate Limiting Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `NODES_RATE_LIMIT_ENABLED` | `true` | Enable rate limiting per user/IP |
| `NODES_RATE_LIMIT_PER_MINUTE` | `60` | Requests allowed per minute |

#### SSO Health Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `NODES_SSO_FALLBACK_MODE` | `require_sso` | What to do when SSO is down: `require_sso` or `fallback_anonymous` |
| `NODES_SSO_HEALTH_CHECK_INTERVAL` | `300` | Seconds between SSO health checks |

#### Example Production Configuration

```bash
# Application
NODES_DEBUG=false
NODES_HOST=0.0.0.0
NODES_PORT=8000
NODES_DATABASE_PATH=/app/data/nodes.db

# Authentication (Okta example)
NODES_AUTH_ENABLED=true
NODES_SSO_PROVIDER=okta
NODES_SSO_DISPLAY_NAME="Company SSO (Okta)"
NODES_SSO_CLIENT_ID=0oa1234567890abcdef
NODES_SSO_CLIENT_SECRET=your-super-secret-key-here
NODES_SSO_REDIRECT_URI=https://threat-intel.company.com/api/auth/callback
NODES_JWT_SECRET_KEY=your-randomly-generated-hex-string-here

# Security
NODES_ACCESS_TOKEN_EXPIRE_MINUTES=15
NODES_REFRESH_TOKEN_EXPIRE_DAYS=7
NODES_RATE_LIMIT_ENABLED=true
NODES_RATE_LIMIT_PER_MINUTE=60

# Audit
NODES_AUDIT_LOG_ENABLED=true
NODES_AUDIT_LOG_RETENTION_DAYS=90

# CORS (allow your domain)
NODES_CORS_ORIGINS=["https://threat-intel.company.com"]
```

**Important Security Notes:**

1. **Always generate a new `NODES_JWT_SECRET_KEY`** - Never use default or example values:
   ```bash
   openssl rand -hex 32
   ```

2. **Keep `.env` file secure** - Add it to `.gitignore` (already included) and restrict file permissions:
   ```bash
   chmod 600 .env
   ```

3. **Use HTTPS in production** - Set your `NODES_SSO_REDIRECT_URI` to use `https://` and place Nodes behind a reverse proxy (nginx, Caddy, Traefik) with TLS certificates.

4. **Restrict CORS origins** - Only include the actual domains that will access your API.

## Quick Start Guide

### Using Docker/Podman

1. Follow [Option 1: Docker](#option-1-docker-recommended) or [Option 2: Podman](#option-2-podman-docker-alternative) installation steps above
2. Open `http://localhost:8000` in your browser
3. Click **New Node** to create your first entry
4. Paste or type your intel snippet
5. Add a source (URL, person, file path, etc.)
6. Optionally add custom tags (suggestions appear from existing tags)
7. Save - the system will automatically find and link related nodes
8. Use the **List/Graph** toggle to explore connections
9. Use the search bar with the query syntax to find nodes later

### Using Manual Installation

1. Follow [Option 3: Manual Installation](#option-3-manual-installation) steps above
2. Start the backend: `cd backend && source venv/bin/activate && python -m app.main` (or activate script for Windows)
3. Open `http://localhost:8000` in your browser
4. Follow steps 3-9 from the Docker section above

---

## Production Deployment

For production deployments, follow these best practices:

### 1. Use a Reverse Proxy with HTTPS

Place Nodes behind a reverse proxy (nginx, Caddy, Traefik) with TLS certificates. Example with Caddy:

```caddy
# Caddyfile
threat-intel.company.com {
    reverse_proxy localhost:8000

    # Optional: Restrict access by IP
    @internal {
        remote_ip 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16
    }
    handle @internal {
        reverse_proxy localhost:8000
    }
    respond 403
}
```

Example with nginx:

```nginx
# /etc/nginx/sites-available/nodes
server {
    listen 443 ssl http2;
    server_name threat-intel.company.com;

    ssl_certificate /etc/letsencrypt/live/threat-intel.company.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/threat-intel.company.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Configure Authentication

Enable SSO authentication for team deployments:

```bash
# In .env
NODES_AUTH_ENABLED=true
NODES_SSO_PROVIDER=okta  # or duo, azure, google
NODES_SSO_CLIENT_ID=your_client_id
NODES_SSO_CLIENT_SECRET=your_secret
NODES_SSO_REDIRECT_URI=https://threat-intel.company.com/api/auth/callback
NODES_JWT_SECRET_KEY=$(openssl rand -hex 32)
```

See [Authentication & Multi-User Support](#authentication--multi-user-support-optional) for complete setup.

### 3. Database Backups

Set up automated backups of your SQLite database:

**With Docker/Podman:**
```bash
#!/bin/bash
# backup-nodes.sh
BACKUP_DIR="/backups/nodes"
DATE=$(date +%Y%m%d-%H%M%S)

docker run --rm \
  -v nodes-data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/nodes-$DATE.tar.gz -C /data .

# Keep only last 30 days
find $BACKUP_DIR -name "nodes-*.tar.gz" -mtime +30 -delete
```

Add to crontab for daily backups:
```bash
0 2 * * * /usr/local/bin/backup-nodes.sh
```

**With Manual Installation:**
```bash
#!/bin/bash
# backup-nodes.sh
BACKUP_DIR="/backups/nodes"
DB_PATH="/app/data/nodes.db"
DATE=$(date +%Y%m%d-%H%M%S)

# Create backup using SQLite online backup
sqlite3 $DB_PATH ".backup $BACKUP_DIR/nodes-$DATE.db"

# Compress backup
gzip $BACKUP_DIR/nodes-$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "nodes-*.db.gz" -mtime +30 -delete
```

### 4. Monitoring and Health Checks

Nodes provides a health check endpoint at `/api/health`:

```bash
# Check application health
curl http://localhost:8000/api/health

# Response when healthy:
{"status": "healthy", "database": "connected"}
```

Set up monitoring with your preferred tool (Prometheus, Datadog, etc.):

**Example with Docker health checks:**
The provided `docker-compose.yml` already includes health checks. View status:
```bash
docker ps  # Look for (healthy) status
docker inspect nodes-app | grep -A 10 Health
```

### 5. Resource Requirements

| Deployment Size | Nodes | CPU | Memory | Disk |
|----------------|-------|-----|--------|------|
| **Small** (< 10k nodes) | 1-3 users | 1 core | 512MB | 1GB |
| **Medium** (10k-100k nodes) | 3-10 users | 2 cores | 1GB | 5GB |
| **Large** (100k+ nodes) | 10+ users | 4+ cores | 2GB | 20GB+ |

SQLite performs well for single-digit concurrent users. For larger teams (20+), consider migrating to PostgreSQL in the future.

### 6. Systemd Service (Linux)

For manual installations, create a systemd service:

```ini
# /etc/systemd/system/nodes.service
[Unit]
Description=Nodes Threat Intelligence Platform
After=network.target

[Service]
Type=simple
User=nodes
Group=nodes
WorkingDirectory=/opt/cti-nodes/backend
Environment="PATH=/opt/cti-nodes/backend/venv/bin"
EnvironmentFile=/opt/cti-nodes/.env
ExecStart=/opt/cti-nodes/backend/venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nodes
sudo systemctl start nodes
sudo systemctl status nodes
```

---

## Quick Start Guide
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

---

## Troubleshooting

### Docker/Podman Issues

**Problem: Port 8000 already in use**
```bash
# Find what's using the port
sudo lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Change the port in docker-compose.yml or .env
NODES_PORT=8080

# Or map to a different host port
docker run -p 8080:8000 nodes-app
```

**Problem: Permission denied accessing volume**
```bash
# Fix volume permissions (Linux)
docker run --rm -v nodes-data:/data alpine chown -R 1000:1000 /data

# For Podman on SELinux systems, use :Z flag
podman run -v nodes-data:/app/data:Z nodes-app
```

**Problem: Container keeps restarting**
```bash
# Check logs for errors
docker logs nodes-app
# Or
podman logs nodes-app

# Common issues:
# - Missing .env file or invalid configuration
# - Database corruption (restore from backup)
# - Port conflict (see above)
```

### Authentication Issues

**Problem: SSO login fails with "Invalid redirect URI"**
- Verify `NODES_SSO_REDIRECT_URI` exactly matches the URI configured in your SSO provider
- Ensure the URI includes the protocol (http:// or https://)
- Check that your SSO provider allows the redirect URI

**Problem: "First user becomes admin" didn't work**
- Check if any users already exist: `SELECT * FROM users;` in the database
- Delete test users and try again
- Verify `NODES_AUTH_ENABLED=true` in your configuration

**Problem: JWT token errors**
- Regenerate `NODES_JWT_SECRET_KEY` with `openssl rand -hex 32`
- Clear browser cookies and try logging in again
- Check that token expiry settings are reasonable (not too short)

### Database Issues

**Problem: Database locked errors**
```bash
# SQLite can have locking issues with multiple processes
# Ensure only one backend instance is running

# Check for stale lock files
rm /app/data/nodes.db-shm
rm /app/data/nodes.db-wal

# Enable WAL mode for better concurrency (done automatically)
```

**Problem: Full-text search not working**
```bash
# Rebuild FTS indexes
cd backend
python -c "
from app.core.database import get_db_connection
conn = get_db_connection()
conn.execute('INSERT INTO nodes_fts(nodes_fts) VALUES(\"rebuild\")')
conn.commit()
print('FTS index rebuilt')
"
```

**Problem: Migration script fails**
```bash
# The migration script is idempotent - safe to run multiple times
# If it fails partway through, your backup is at nodes.db.backup.TIMESTAMP

# Restore from backup if needed
cp nodes.db.backup.TIMESTAMP nodes.db

# Check for table existence
sqlite3 nodes.db ".tables"

# If specific tables are missing, report as a bug
```

### Performance Issues

**Problem: Slow search with large databases**
- FTS indexes should be automatic - verify with: `SELECT * FROM nodes_fts LIMIT 1;`
- Check for disk space - SQLite requires free space for temporary files
- Consider VACUUM to reclaim space: `sqlite3 nodes.db "VACUUM;"`

**Problem: Graph view slow with many nodes**
- Use the depth slider to limit graph size
- Filter to specific tags before opening graph view
- Graph rendering is client-side - try a different browser or upgrade hardware

### Frontend Issues

**Problem: Blank page or "Failed to fetch"**
```bash
# Check that backend is running
curl http://localhost:8000/api/health

# Check CORS settings in .env
NODES_CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]

# Check browser console for errors (F12)
# Look for CORS errors or network failures
```

**Problem: Auto-linking not working**
- Verify extractors are enabled (default)
- Check that IOCs/entities are being detected in node detail view
- Manually trigger linking by editing and saving the node

### Getting Help

If you encounter issues not covered here:

1. Check the logs: `docker logs nodes-app` or check backend console output
2. Verify your configuration in `.env` matches `.env.example` format
3. Try with authentication disabled (`NODES_AUTH_ENABLED=false`) to isolate issues
4. Search existing GitHub issues or create a new one with:
   - Your environment (Docker/Podman/Manual, OS version)
   - Relevant logs
   - Steps to reproduce the issue

---

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
