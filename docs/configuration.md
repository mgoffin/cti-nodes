# Configuration Guide

Nodes uses environment variables for configuration. All settings are optional with sensible defaults.

## Quick Configuration

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
nano .env  # or your preferred editor
```

## Core Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `NODES_DEBUG` | `false` | Enable debug mode with verbose logging |
| `NODES_HOST` | `0.0.0.0` | Host to bind to (0.0.0.0 = all interfaces) |
| `NODES_PORT` | `8000` | Port to listen on |
| `NODES_DATABASE_PATH` | `data/nodes.db` | SQLite database file path |
| `NODES_CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:8000"]` | Allowed CORS origins (JSON array) |

**Example:**
```bash
NODES_DEBUG=false
NODES_HOST=0.0.0.0
NODES_PORT=8000
NODES_DATABASE_PATH=/app/data/nodes.db
NODES_CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]
```

## Authentication

Nodes supports optional SSO-based authentication for team deployments.

### Enabling Authentication

```bash
NODES_AUTH_ENABLED=true
NODES_SSO_PROVIDER=duo  # duo, okta, azure, google
NODES_SSO_DISPLAY_NAME="Company SSO"
NODES_SSO_CLIENT_ID=your_client_id
NODES_SSO_CLIENT_SECRET=your_client_secret
NODES_SSO_REDIRECT_URI=https://your-domain.com/api/auth/callback
NODES_JWT_SECRET_KEY=your_generated_secret  # openssl rand -hex 32
```

### Supported SSO Providers

| Provider | Value | Notes |
|----------|-------|-------|
| Duo Security | `duo` | OAuth 2.0 via OIDC |
| Okta | `okta` | OAuth 2.0 via OIDC |
| Azure AD | `azure` | Microsoft identity platform |
| Google | `google` | Google OAuth 2.0 |

### SSO Provider Configuration

#### Duo Security

```bash
NODES_SSO_PROVIDER=duo
NODES_SSO_CLIENT_ID=your_duo_client_id
NODES_SSO_CLIENT_SECRET=your_duo_secret
NODES_SSO_REDIRECT_URI=https://your-domain.com/api/auth/callback
```

Configure in Duo Admin Panel:
- Create a new "Web SDK" application
- Set redirect URI to match `NODES_SSO_REDIRECT_URI`
- Copy Client ID and Secret

#### Okta

```bash
NODES_SSO_PROVIDER=okta
NODES_SSO_CLIENT_ID=0oa1234567890abcdef
NODES_SSO_CLIENT_SECRET=your_okta_secret
NODES_SSO_REDIRECT_URI=https://your-domain.com/api/auth/callback
```

Configure in Okta Admin Console:
- Create new "Web" application
- Add redirect URI
- Copy Client ID and Secret

#### Azure AD

```bash
NODES_SSO_PROVIDER=azure
NODES_SSO_CLIENT_ID=your_azure_app_id
NODES_SSO_CLIENT_SECRET=your_azure_secret
NODES_SSO_REDIRECT_URI=https://your-domain.com/api/auth/callback
```

Configure in Azure Portal:
- Register new application
- Add redirect URI under "Authentication"
- Create client secret under "Certificates & secrets"

#### Google

```bash
NODES_SSO_PROVIDER=google
NODES_SSO_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
NODES_SSO_CLIENT_SECRET=your_google_secret
NODES_SSO_REDIRECT_URI=https://your-domain.com/api/auth/callback
```

Configure in Google Cloud Console:
- Create OAuth 2.0 credentials
- Add authorized redirect URI
- Copy Client ID and Secret

### Generic OIDC (Advanced)

For providers not listed above, use generic OIDC endpoints:

```bash
NODES_SSO_PROVIDER=generic_oidc
NODES_SSO_AUTHORIZATION_URL=https://provider.com/oauth/authorize
NODES_SSO_TOKEN_URL=https://provider.com/oauth/token
NODES_SSO_USERINFO_URL=https://provider.com/oauth/userinfo
NODES_SSO_CLIENT_ID=your_client_id
NODES_SSO_CLIENT_SECRET=your_secret
NODES_SSO_REDIRECT_URI=https://your-domain.com/api/auth/callback
```

### JWT Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `NODES_JWT_SECRET_KEY` | - | Secret key for signing JWTs (required if auth enabled) |
| `NODES_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `NODES_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

**Generate a secure secret:**
```bash
openssl rand -hex 32
```

⚠️ **Never commit your JWT secret to git!**

### Role-Based Access Control

When authentication is enabled, users are assigned roles:

- **Administrator** - Full access, user management, audit logs
- **Analyst** - Create/edit/delete own content, view all content
- **Viewer** - Read-only access

**First user to log in becomes Administrator automatically.**

### Database Migration

When enabling authentication on existing database:

```bash
# Docker
docker exec -it nodes-app /bin/bash
cd /app/backend
python migrate_v2_users.py
exit

# Manual installation
cd backend
source venv/bin/activate  # or activate script for Windows
python migrate_v2_users.py
```

Migration:
- Backs up database to `nodes.db.backup.TIMESTAMP`
- Adds auth tables
- Assigns existing content to "Anonymous"
- Is idempotent (safe to run multiple times)

## Security Settings

### Audit Logging

```bash
NODES_AUDIT_LOG_ENABLED=true
NODES_AUDIT_LOG_RETENTION_DAYS=90
```

Tracks all create/update/delete operations when auth is enabled.

### Rate Limiting

```bash
NODES_RATE_LIMIT_ENABLED=true
NODES_RATE_LIMIT_PER_MINUTE=60
```

Prevents abuse by limiting requests per user/IP.

### SSO Health Monitoring

```bash
NODES_SSO_FALLBACK_MODE=require_sso  # or fallback_anonymous
NODES_SSO_HEALTH_CHECK_INTERVAL=300  # seconds
```

- `require_sso` - Block access when SSO is down
- `fallback_anonymous` - Allow anonymous access as fallback

## Production Configuration Example

```bash
# Application
NODES_DEBUG=false
NODES_HOST=0.0.0.0
NODES_PORT=8000
NODES_DATABASE_PATH=/app/data/nodes.db
NODES_CORS_ORIGINS=["https://threat-intel.company.com"]

# Authentication (Okta)
NODES_AUTH_ENABLED=true
NODES_SSO_PROVIDER=okta
NODES_SSO_DISPLAY_NAME="Company SSO"
NODES_SSO_CLIENT_ID=0oa1234567890abcdef
NODES_SSO_CLIENT_SECRET=super_secret_key_here
NODES_SSO_REDIRECT_URI=https://threat-intel.company.com/api/auth/callback
NODES_JWT_SECRET_KEY=randomly_generated_hex_string_here

# Security
NODES_ACCESS_TOKEN_EXPIRE_MINUTES=15
NODES_REFRESH_TOKEN_EXPIRE_DAYS=7
NODES_RATE_LIMIT_ENABLED=true
NODES_RATE_LIMIT_PER_MINUTE=60

# Audit
NODES_AUDIT_LOG_ENABLED=true
NODES_AUDIT_LOG_RETENTION_DAYS=90
```

## Security Best Practices

1. **Generate unique JWT secret** - Never use defaults:
   ```bash
   openssl rand -hex 32
   ```

2. **Secure .env file** - Restrict permissions:
   ```bash
   chmod 600 .env
   ```

3. **Use HTTPS in production** - Always use TLS for SSO redirect URIs

4. **Restrict CORS origins** - Only include trusted domains

5. **Keep secrets out of git** - `.env` is already in `.gitignore`

## Disabling Authentication

To run in single-user mode (no auth required):

```bash
NODES_AUTH_ENABLED=false
```

Or simply don't set authentication variables. The platform works perfectly without authentication!

## Next Steps

- **Set up production deployment**: [Production Guide](production-deployment.md)
- **Configure reverse proxy**: See production guide for nginx/Caddy examples
- **Set up backups**: [DATA_PERSISTENCE.md](../DATA_PERSISTENCE.md)
