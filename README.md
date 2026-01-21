# Nodes

> A lightweight graph-based intelligence notebook for capturing, connecting, and searching unstructured threat intel.

**Think of it as a "threat intel scratch pad" that builds its own connection map.**

---

## ⚡ Quick Start

```bash
git clone https://github.com/mgoffin/cti-nodes.git
cd cti-nodes
docker-compose -f docker/docker-compose.yml up -d
```

Open **http://localhost:8000** and start capturing intelligence!

📖 **New to Nodes?** See [QUICKSTART.md](QUICKSTART.md) for a 5-minute guide.

---

## 🎯 Core Features

- **Quick Capture** - Add nodes (text blobs) with minimal friction; just paste/type and tag
- **Smart Auto-Linking** - Automatically discovers relationships by matching IOCs, entities, tags, and content
- **Automatic Entity Extraction** - Detects 24+ entity types (IPs, domains, hashes, threat actors, malware, CVEs, etc.)
- **Suggested Tags & Entities** - Intelligent suggestions from related nodes and content analysis
- **Edge Confidence Scoring** - Relationships weighted by match quality (exact IOC = high, partial content = low)
- **Dual View Modes** - Toggle between List View and interactive Graph View
- **Powerful Search** - Query language: `content="*cobalt strike*" AND tag:source="*twitter*"`
- **Threat Actor Normalization** - Uses Microsoft naming with alias resolution (APT28 → Forest Blizzard)
- **Entity Validation** - Detects type mismatches and defanged IOCs, suggests corrections
- **Chrome Extension** - Capture intel while browsing, right-click to add or search
- **Optional Authentication** - SSO support (Duo, Okta, Azure AD, Google) for team deployments
- **Dark/Light Theme** - Comfortable viewing in any environment

---

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](QUICKSTART.md)** - Get running in 5 minutes
- **[Installation with Docker](docs/installation/docker.md)** - Recommended method (Windows/Mac/Linux)
- **[Installation with Podman](docs/installation/podman.md)** - Docker alternative
- **[Manual Installation](docs/installation/manual.md)** - Without containers

### Configuration & Deployment
- **[Configuration Guide](docs/configuration.md)** - Environment variables, authentication, security settings
- **[Production Deployment](docs/production-deployment.md)** - HTTPS, backups, monitoring, systemd

### Usage & Features
- **[User Guide](docs/user-guide.md)** - Complete platform walkthrough
- **[Chrome Extension](docs/chrome-extension.md)** - Browser extension setup and usage
- **[Architecture](docs/architecture.md)** - Technical overview, data model, design decisions

### Data Safety
- **[Data Persistence Guide](DATA_PERSISTENCE.md)** - **Critical!** How Docker volumes keep your data safe
- **Backup Scripts** - `./backup-database.sh` (Linux/macOS) or `.\backup-database.ps1` (Windows)
- **Health Check** - `./check-database.sh` (Linux/macOS) or `.\check-database.ps1` (Windows)

### Help & Support
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[FAQ](docs/faq.md)** - Frequently asked questions

---

## 🏗️ Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React 19 + Vite + Tailwind | Modern, fast, responsive UI |
| **Backend** | Python 3.14 + FastAPI | Async API, entity extraction |
| **Database** | SQLite + FTS5 | Zero-config, portable, fast full-text search |
| **Graph** | Cytoscape.js | Interactive network visualization |

**Why SQLite?** Zero configuration, single portable file, excellent full-text search, easy backup. Perfect for personal/small team use (< 10 concurrent users, < 100k nodes).

---

## 🔐 Authentication (Optional)

Nodes runs in **single-user mode by default** (no authentication required). For team deployments, enable SSO:

**Supported Providers:**
- Duo Security
- Okta
- Azure AD
- Google
- Any OIDC-compliant provider

**Features when enabled:**
- Role-based access control (Administrator / Analyst / Viewer)
- Audit logging
- Session management
- User profiles

See [Configuration Guide](docs/configuration.md#authentication) for setup.

---

## 🌐 Chrome Extension

Capture intelligence while browsing:

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" → Select `chrome_extension` folder
4. Configure API and frontend URLs
5. Right-click selected text → "Add to Nodes"

See [Chrome Extension Guide](docs/chrome-extension.md) for details.

---

## 🔍 Search Syntax

| Query | What it searches |
|-------|------------------|
| `keyword` | Everywhere (content + tags) |
| `content="*text*"` | Node content only |
| `tag:source="*twitter*"` | Specific tag by name and value |
| `tag:adversary=*` | All nodes with adversary tag |
| `content="*ransomware*" AND tag:severity="high"` | Combined search |

See [User Guide](docs/user-guide.md#search) for complete syntax.

---

## 🛠️ Quick Commands

### Docker (Recommended)

```bash
# Start
docker-compose -f docker/docker-compose.yml up -d

# Stop (NEVER use -v flag!)
docker-compose -f docker/docker-compose.yml down

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Backup database
./backup-database.sh  # or .ps1 on Windows

# Check health
./check-database.sh   # or .ps1 on Windows
```

### Development Mode

```bash
# Hot-reload for instant code changes
docker-compose -f docker/docker-compose.dev.yml up
```

---

## 📊 What Gets Extracted Automatically

**IOCs:**
- IPv4/IPv6 addresses
- Domains and URLs
- Email addresses
- File hashes (MD5, SHA1, SHA256)
- CVE identifiers

**Entities:**
- Threat actors (normalized to Microsoft naming)
- Malware families
- Tool names
- Commands
- File paths and registry keys

**Edges (Connections):**
- IOC matches across nodes
- Entity matches
- Tag value matches
- Content overlap

---

## ⚠️ Data Safety

**Your database is safe from container rebuilds!**

✅ **Data persists through:**
- `docker-compose down` (stops containers, keeps data)
- `docker-compose up --build` (rebuilds image, keeps data)
- Code updates and container restarts

❌ **NEVER use:**
- `docker-compose down -v` (the `-v` flag **DELETES your data!**)
- `docker volume rm nodes-data`

**Set up automated backups:**
```bash
# Run regularly (set up cron/Task Scheduler)
./backup-database.sh  # Linux/macOS
.\backup-database.ps1  # Windows
```

See [DATA_PERSISTENCE.md](DATA_PERSISTENCE.md) for complete details.

---

## 🎓 Use Cases

- **Threat Intelligence Analysts** - Track campaigns, adversaries, IOCs across multiple sources
- **SOC Analysts** - Build institutional knowledge, connect related incidents
- **Incident Responders** - Document findings, discover relationships
- **Security Researchers** - Organize research notes, track malware families
- **Red Teamers** - Document infrastructure, tools, techniques

---

## 📈 Roadmap

- ✅ Auto-linking and entity extraction
- ✅ Graph visualization
- ✅ Chrome extension
- ✅ SSO authentication
- ✅ Suggested tags and entities
- ✅ Entity validation
- 🔄 Import/Export (JSON, CSV, STIX)
- 🔄 API access tokens
- 🔄 PostgreSQL support for larger teams
- 🔄 Advanced analytics
- 🔄 ML-powered suggestions

---

## 🤝 Contributing

Contributions welcome! Check GitHub for:
- Issue tracker
- Feature requests
- Contribution guidelines

---

## 📝 License

MIT (TBD)

---

## 🆘 Getting Help

- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Troubleshooting**: [docs/troubleshooting.md](docs/troubleshooting.md)
- **FAQ**: [docs/faq.md](docs/faq.md)
- **GitHub Issues**: (link TBD)

---

## 💡 Example Workflow

1. **Paste a blog post snippet** about a new ransomware campaign
2. Nodes automatically extracts:
   - IOCs (domains, IPs, hashes)
   - Threat actor names
   - Malware families
   - Tags (suggests `iocs`, `malware`, `attribution`)
3. **Discovers related nodes** mentioning same IOCs or actors
4. **View connections** in graph mode to see the bigger picture
5. **Search later** with `content="*ransomware name*"` to find all related intel
6. **Chrome extension** helps you capture intel from Twitter, reports, blogs while browsing

---

**Ready to get started?** → [QUICKSTART.md](QUICKSTART.md)

**Want to understand the platform?** → [User Guide](docs/user-guide.md)

**Deploying for a team?** → [Production Deployment](docs/production-deployment.md)
