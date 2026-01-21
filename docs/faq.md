# FAQ

Frequently asked questions about Nodes.

## General

### What is Nodes?

Nodes is a personal knowledge graph for cyber threat intelligence. It helps you capture intelligence snippets and automatically discovers relationships between them over time.

### Who is it for?

- Threat intelligence analysts
- SOC analysts
- Incident responders
- Security researchers
- Red teamers documenting findings

### Is it free?

Yes! Nodes is open source (MIT license, TBD).

### Do I need to know how to code?

No. Nodes is a user-facing application. Just install and use it through the web interface.

## Installation

### Which installation method should I use?

- **Docker** (recommended) - Easiest, works everywhere
- **Podman** - Docker alternative, better security
- **Manual** - If you can't use containers or need development setup

See [installation guides](installation/) for details.

### Do I need authentication?

No! Authentication is optional. By default, Nodes runs in single-user mode with no login required.

### Can I use it offline?

Yes. Nodes runs entirely locally with no internet required (except for SSO authentication if you enable it).

## Usage

### What kind of data should I add?

Anything useful for threat intelligence:
- IOCs from reports
- Snippets from blog posts
- Notes from conversations
- References to threat actors
- URLs to resources
- Your own analysis notes

### How does auto-linking work?

When you save a node, Nodes:
1. Extracts IOCs (IPs, domains, hashes, etc.)
2. Extracts entities (threat actors, malware, tools)
3. Searches existing nodes for matches
4. Creates edges with confidence scores

See [user-guide.md](user-guide.md#auto-linking) for details.

### What entities can Nodes detect?

24+ types including:
- Network indicators (IPs, domains, URLs)
- File hashes (MD5, SHA1, SHA256)
- Threat actors and malware families
- CVEs and ATT&CK techniques
- Files, paths, registry keys
- Commands and tools

See [complete list](user-guide.md#extracted-entities).

### What is Microsoft threat actor naming?

Microsoft uses weather-themed names like "Forest Blizzard" instead of "APT28". Nodes uses this as the standard but recognizes aliases, so searching "APT28" still finds "Forest Blizzard" references.

### Can I manually link nodes?

Yes! In addition to auto-linking, you can create manual edges between any nodes. Manual edges have 1.0 confidence.

### How do I search effectively?

- Use wildcards: `*partial*match*`
- Search content only: `content="*text*"`
- Search specific tags: `tag:source="*twitter*"`
- Combine with AND/OR: `content="*apt28*" AND tag:severity="high"`

See [search syntax](user-guide.md#search).

## Data Safety

### Where is my data stored?

- **Docker/Podman**: In a named volume (`nodes-data`) on your host
- **Manual install**: In `backend/data/nodes.db`

### Will I lose data when updating?

No! When using Docker/Podman, your database is in a persistent volume that survives container rebuilds.

### How do I back up?

**Easy way:**
```bash
./backup-database.sh  # Linux/macOS
.\backup-database.ps1  # Windows
```

**Manual way:**
- Docker: Copy from volume (see [DATA_PERSISTENCE.md](../DATA_PERSISTENCE.md))
- Manual: Copy `backend/data/nodes.db` file

### How do I restore from backup?

See [DATA_PERSISTENCE.md](../DATA_PERSISTENCE.md) for detailed steps.

### What if I accidentally delete the database?

If you have backups, you can restore. If not, data is unrecoverable. **Always keep backups!**

## Authentication & Multi-User

### Do I need authentication for single-user?

No. Authentication is optional. Disable it (or don't configure it) to run in single-user mode.

### What SSO providers are supported?

- Duo Security
- Okta
- Azure AD
- Google
- Any OIDC-compliant provider

See [configuration.md](configuration.md#authentication).

### How do roles work?

- **Administrator** - Full access, user management
- **Analyst** - Create/edit own content, view all
- **Viewer** - Read-only access

First user to log in becomes Administrator.

### Can I switch between single-user and multi-user?

Yes! Run the migration script to add auth tables, then enable authentication in `.env`.

### What happens to existing data when enabling auth?

The migration script assigns all existing content to "Anonymous" author. First user to login becomes admin and can claim ownership if desired.

## Technical

### Why SQLite instead of PostgreSQL?

SQLite is:
- Zero configuration
- Single file (easy backup)
- Fast for < 100k nodes
- Portable
- FTS5 for excellent search

For larger teams (20+ users), PostgreSQL may be added in future.

### How scalable is it?

Works well for:
- < 10 concurrent users
- < 100k nodes
- Single server

Larger deployments should consider PostgreSQL backend (planned).

### Can I export my data?

Currently:
- Manual SQLite export
- Direct database access

Planned:
- JSON/CSV export
- STIX export

### Is there an API?

Yes! All features accessible via REST API at `/api/*`. Documentation coming soon.

### Can I automate things?

Yes - use the API. Example:
```bash
curl -X POST http://localhost:8000/api/nodes \
  -H "Content-Type: application/json" \
  -d '{"content": "New intel", "source": "automation"}'
```

## Troubleshooting

### Port 8000 already in use

Change port in `.env`:
```bash
NODES_PORT=8080
```

### Container won't start

Check logs:
```bash
docker logs nodes-app
```

Common issues:
- Missing/invalid .env
- Port conflict
- Database corruption

### Search isn't working

Rebuild FTS indexes:
```bash
docker exec nodes-app python -c "
from app.core.database import get_db_connection
conn = get_db_connection()
conn.execute('INSERT INTO nodes_fts(nodes_fts) VALUES(\"rebuild\")')
conn.commit()
"
```

### Auto-linking stopped working

Verify extractors are running - check node detail view to see if entities are being detected. If not, file a bug report.

### Lost database after rebuild

See [troubleshooting guide](troubleshooting.md#database-issues) for recovery steps.

## Chrome Extension

### How do I install it?

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `chrome_extension` folder
5. Configure URLs in extension popup

See [chrome-extension.md](chrome-extension.md).

### Can I use it with Firefox?

Not currently. Chrome/Edge only. Firefox support may come later.

### Extension shows "Failed to connect"

Check:
1. Nodes is running (`http://localhost:8000`)
2. URLs configured correctly in extension
3. CORS settings allow extension origin

## Support

### Where do I report bugs?

GitHub Issues (link TBD when repo is public).

### How do I request features?

GitHub Issues or Discussions.

### Can I contribute?

Yes! Contributions welcome. Check GitHub for contribution guidelines.

### Is there a community?

Coming soon - Discord/Slack for discussion.

## Comparison

### Nodes vs. MISP?

- **MISP**: Full TIP platform, complex, multi-tenant, event-based
- **Nodes**: Personal knowledge graph, simple, auto-linking, note-based

Nodes is for personal/small team quick capture and exploration. MISP is for structured intel sharing.

### Nodes vs. Maltego?

- **Maltego**: Visual transforms, external data sources, graph analysis
- **Nodes**: Text-first note-taking, auto-extraction, quick capture

Nodes is for capturing and organizing your own intel. Maltego is for pivoting and enrichment.

### Nodes vs. Obsidian with plugins?

- **Obsidian**: General knowledge management, markdown files
- **Nodes**: CTI-specific, IOC extraction, threat actor normalization, auto-linking

Nodes is purpose-built for threat intelligence with domain-specific features.

## License & Legal

### What license is Nodes under?

MIT License (TBD - to be confirmed).

### Can I use it commercially?

Yes, MIT license allows commercial use.

### Do you collect telemetry?

No. Nodes runs entirely locally with no telemetry or phone-home.

### Is it GDPR compliant?

When self-hosted, you control all data. No data is sent to third parties. SSO providers may have their own compliance requirements.

## Next Steps

- **Get started**: [QUICKSTART.md](../QUICKSTART.md)
- **Learn the platform**: [user-guide.md](user-guide.md)
- **Deploy in production**: [production-deployment.md](production-deployment.md)
- **Get help**: [troubleshooting.md](troubleshooting.md)
