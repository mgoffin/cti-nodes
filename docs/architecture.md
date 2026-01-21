# Architecture

Technical overview of Nodes architecture, data model, and design decisions.

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Database** | SQLite + FTS5 | Zero-config, portable, powerful full-text search, easy backup |
| **Backend** | Python 3.14 / FastAPI | Async, excellent for regex/NLP, easy to extend |
| **Frontend** | React 19 + Vite + Tailwind | Modern, fast, huge ecosystem, utility-first styling |
| **Graph Viz** | Cytoscape.js | Mature, performant, supports depth expansion |
| **Extraction** | Regex + curated lists | IOCs via regex; threat actors/malware via curated data |

## Project Structure

```
cti-nodes/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint
│   │   ├── api/                       # API endpoints
│   │   │   ├── nodes.py               # Node CRUD
│   │   │   ├── tags.py                # Tag management
│   │   │   ├── edges.py               # Edge queries
│   │   │   ├── search.py              # Search endpoint
│   │   │   ├── extracted.py           # Entity management
│   │   │   ├── auth.py                # Authentication
│   │   │   ├── users.py               # User management
│   │   │   └── audit.py               # Audit logs
│   │   ├── core/
│   │   │   ├── config.py              # Configuration
│   │   │   ├── database.py            # SQLite connection
│   │   │   ├── security.py            # Auth/JWT
│   │   │   ├── oidc_providers.py      # SSO configuration
│   │   │   └── rate_limit.py          # Rate limiting
│   │   ├── extractors/
│   │   │   ├── ioc.py                 # IOC patterns
│   │   │   ├── entities.py            # Entity matching
│   │   │   └── defang.py              # Defang/refang
│   │   ├── validators/
│   │   │   ├── entity_validator.py    # Type validation
│   │   │   ├── entity_suggester.py    # Entity suggestions
│   │   │   └── tag_suggester.py       # Tag autocomplete
│   │   ├── linker/
│   │   │   └── auto_link.py           # Auto-linking logic
│   │   ├── models/
│   │   │   └── schemas.py             # Pydantic models
│   │   └── data/
│   │       ├── threat_actors.json     # Actor aliases
│   │       ├── malware.json           # Malware families
│   │       └── tools.json             # Tool names
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/                # React components
│       ├── api/client.ts              # API client
│       ├── hooks/                     # Custom React hooks
│       ├── contexts/                  # React contexts
│       ├── types/                     # TypeScript types
│       └── utils/                     # Utilities
├── docker/
│   ├── Dockerfile                     # Production build
│   ├── Dockerfile.dev                 # Development build
│   ├── docker-compose.yml             # Production compose
│   └── docker-compose.dev.yml         # Dev compose
├── docs/                              # Documentation
└── chrome_extension/                  # Browser extension
```

## Data Model

### Core Tables

**nodes**
```sql
id              TEXT PRIMARY KEY  -- UUID
content         TEXT              -- Main content (FTS5 indexed)
created_at      DATETIME
updated_at      DATETIME
author_id       TEXT              -- FK to users (when auth enabled)
```

**tags**
```sql
id              TEXT PRIMARY KEY  -- UUID
node_id         TEXT              -- FK to nodes
name            TEXT              -- Tag name (e.g., "source", "malware")
value           TEXT              -- Tag value (FTS5 indexed)
created_at      DATETIME
author_id       TEXT              -- FK to users (when auth enabled)
```

**edges**
```sql
id              TEXT PRIMARY KEY  -- UUID
source_node_id  TEXT              -- FK to nodes
target_node_id  TEXT              -- FK to nodes
edge_type       TEXT              -- "tag_match", "ioc_match", etc.
match_value     TEXT              -- What matched
confidence      REAL              -- 0.0 - 1.0
created_at      DATETIME
author_id       TEXT              -- FK to users (manual edges only)
```

**extracted**
```sql
id              TEXT PRIMARY KEY  -- UUID
node_id         TEXT              -- FK to nodes
type            TEXT              -- Entity type (ipv4, domain, etc.)
value           TEXT              -- Normalized value
raw_value       TEXT              -- Original value from content
canonical_value TEXT              -- For aliases (threat actors)
created_at      DATETIME
```

### Authentication Tables (When Enabled)

**users**
```sql
id              TEXT PRIMARY KEY  -- UUID
email           TEXT UNIQUE       -- From SSO
display_name    TEXT
role            TEXT              -- admin, analyst, viewer
avatar_url      TEXT
is_active       BOOLEAN
created_at      DATETIME
last_login      DATETIME
```

**sessions**
```sql
id              TEXT PRIMARY KEY  -- UUID
user_id         TEXT              -- FK to users
access_token    TEXT
refresh_token   TEXT
expires_at      DATETIME
ip_address      TEXT
user_agent      TEXT
created_at      DATETIME
```

**audit_log**
```sql
id              TEXT PRIMARY KEY  -- UUID
user_id         TEXT              -- FK to users
action          TEXT              -- "create", "update", "delete"
resource_type   TEXT              -- "node", "tag", "edge"
resource_id     TEXT
details         TEXT              -- JSON with changes
created_at      DATETIME
```

### Supporting Tables

**threat_actor_aliases**
```sql
alias           TEXT PRIMARY KEY  -- "APT28", "Fancy Bear"
canonical_name  TEXT              -- "Forest Blizzard"
```

**rejected_tag_suggestions**
```sql
node_id         TEXT              -- FK to nodes
tag_name        TEXT
tag_value       TEXT
rejected_at     DATETIME
PRIMARY KEY (node_id, tag_name, tag_value)
```

**rejected_extracted_entity_suggestions**
```sql
node_id         TEXT              -- FK to nodes
entity_type     TEXT
entity_value    TEXT
rejected_at     DATETIME
PRIMARY KEY (node_id, entity_type, entity_value)
```

**user_preferences**
```sql
user_id         TEXT PRIMARY KEY  -- FK to users
theme           TEXT              -- "dark", "light", "system"
preferences     TEXT              -- JSON with other settings
```

## Entity Types

24+ entity types supported:

- **Network**: ipv4, ipv6, domain, url, email, asn
- **Files**: hash_md5, hash_sha1, hash_sha256, filename, file_path
- **Malware**: malware, tool, command
- **Threats**: threat_actor, campaign
- **Vulnerabilities**: cve, mitre_attack
- **Windows**: registry_key, mutex, user_agent
- **Geographic**: country

See [user-guide.md](user-guide.md) for complete list with examples.

## Edge Confidence Scoring

| Match Type | Confidence | Logic |
|------------|------------|-------|
| Exact IOC match | 1.0 | Same IP, hash, domain, etc. |
| Threat actor (canonical) | 1.0 | Normalized name match |
| Threat actor (alias) | 0.9 | Matched via alias table |
| Exact tag value | 0.8 | Same tag name + value |
| URL domain | 0.7 | Same domain, different path |
| Content overlap | 0.3-0.6 | Shared keywords (TF-IDF) |
| Manual link | 1.0 | User-created |

## Full-Text Search

Uses SQLite FTS5 for fast searching:
- **Content** indexed for quick text search
- **Tag values** indexed separately
- **Prefix matching** for autocomplete
- **Ranked results** by relevance

## Auto-Linking Algorithm

When a node is saved:

1. **Extract** - Pull IOCs and entities from content
2. **Normalize** - Convert to canonical forms (defang IOCs, resolve actor aliases)
3. **Match** - Query existing nodes for matches
4. **Score** - Calculate confidence based on match type
5. **Create edges** - Insert with confidence scores
6. **Notify** - Show user how many connections found

## Security Model

### Authentication Flow

1. User clicks "Login with SSO"
2. Redirected to SSO provider
3. User authenticates
4. Callback with authorization code
5. Exchange code for tokens
6. Verify user with userinfo endpoint
7. Create/update user record
8. Issue JWT access + refresh tokens
9. Client stores tokens
10. Subsequent requests use access token

### Authorization

- **Endpoint-level** - Decorators check role requirements
- **Resource-level** - Ownership checked for modifications
- **Role hierarchy** - Admin > Analyst > Viewer

### Token Management

- **Access tokens** - Short-lived (15 min default)
- **Refresh tokens** - Longer-lived (7 days default)
- **Automatic refresh** - Client renews before expiration
- **Session tracking** - All active sessions logged

## Performance Considerations

### Database

- **FTS5 indexes** - Fast full-text search
- **WAL mode** - Better concurrency
- **Indexes** - Foreign keys, frequently queried columns
- **Batch operations** - Bulk inserts/updates where possible

### Frontend

- **Code splitting** - Lazy load routes
- **React Query** - Caching and background refetch
- **Virtualization** - Render only visible items
- **Graph optimization** - Limit depth, use canvas rendering

### Scalability

SQLite works well for:
- Small teams (< 10 users)
- Moderate data (< 100k nodes)
- Low concurrency (< 10 concurrent requests)

For larger deployments:
- Consider PostgreSQL migration
- Add read replicas
- Implement caching layer (Redis)

## Development Practices

### Code Organization

- **API routes** - Organized by resource (nodes, tags, etc.)
- **Validators** - Separate concerns (extraction, validation, suggestion)
- **Schemas** - Pydantic models for type safety
- **Tests** - Unit and integration tests

### Error Handling

- **Exceptions** - FastAPI exception handlers
- **Validation** - Pydantic validates inputs
- **Logging** - Structured logging with context
- **User feedback** - Clear error messages

### Future Enhancements

- Import/Export (JSON, CSV, STIX)
- Webhooks for automation
- API access tokens
- PostgreSQL support
- Multi-tenancy
- Advanced analytics
- ML-powered suggestions

## Next Steps

- **Deploy**: [production-deployment.md](production-deployment.md)
- **Contribute**: Check GitHub for contribution guidelines
- **Extend**: Add custom extractors or validators
