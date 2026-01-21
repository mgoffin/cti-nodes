# Installing Nodes with Docker

Docker is the **recommended** installation method. It works on Windows, macOS, and Linux with minimal setup.

## Prerequisites

- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/downloads)

## Installation Steps

### Step 1: Clone the Repository

```bash
git clone https://github.com/mgoffin/cti-nodes.git
cd cti-nodes
```

### Step 2: Configure Environment (Optional)

Create a `.env` file to customize settings:

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

**Basic configuration:**
```bash
NODES_DEBUG=false
NODES_HOST=0.0.0.0
NODES_PORT=8000
NODES_DATABASE_PATH=/app/data/nodes.db
```

For authentication, CORS, and other options, see [Configuration Guide](../configuration.md).

### Step 3: Build and Run

```bash
# Build and start (detached mode)
docker-compose -f docker/docker-compose.yml up -d --build

# Or run in foreground to see logs
docker-compose -f docker/docker-compose.yml up --build
```

The application will be available at **http://localhost:8000**

### Step 4: Database Migration (If Enabling Authentication)

If you're enabling authentication on an existing database:

```bash
docker exec -it nodes-app /bin/bash
cd /app/backend
python migrate_v2_users.py
exit
```

## Docker Management Commands

### Starting and Stopping

```bash
# Stop containers (keeps data)
docker-compose -f docker/docker-compose.yml down

# Start containers
docker-compose -f docker/docker-compose.yml up -d

# Restart containers
docker-compose -f docker/docker-compose.yml restart
```

### Viewing Logs

```bash
# Follow logs in real-time
docker-compose -f docker/docker-compose.yml logs -f

# View last 100 lines
docker-compose -f docker/docker-compose.yml logs --tail=100
```

### Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker/docker-compose.yml up -d --build
```

Your data persists through updates! See [DATA_PERSISTENCE.md](../../DATA_PERSISTENCE.md) for details.

### Accessing Container Shell

```bash
docker exec -it nodes-app /bin/bash
```

## Development Mode

For development with hot-reload (code changes apply instantly):

```bash
# Start in development mode
docker-compose -f docker/docker-compose.dev.yml up

# The container will:
# - Mount source code as volumes
# - Auto-reload backend on Python file changes
# - Auto-reload frontend on TypeScript/React changes
# - Expose backend at http://localhost:8000
# - Expose frontend at http://localhost:5173
```

After initial build, omit `--build` for faster startup:
```bash
docker-compose -f docker/docker-compose.dev.yml up
```

Stop with `Ctrl+C`.

## Data Management

### Backing Up Your Database

**Easy method:**
```bash
./backup-database.sh  # Linux/macOS
.\backup-database.ps1  # Windows
```

**Manual method:**
```bash
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    tar czf /backup/nodes-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
```

### Restoring from Backup

```bash
# Stop containers
docker-compose -f docker/docker-compose.yml down

# Restore from backup
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    tar xzf /backup/nodes-backup-YYYYMMDD-HHMMSS.tar.gz -C /data

# Restart containers
docker-compose -f docker/docker-compose.yml up -d
```

### Verifying Database Health

```bash
./check-database.sh  # Linux/macOS
.\check-database.ps1  # Windows
```

## Data Persistence

⚠️ **Your database is safe from container rebuilds!**

Nodes uses a Docker named volume (`nodes-data`) to store your database. Your data persists through:
- ✅ `docker-compose down` (stops containers, keeps data)
- ✅ `docker-compose up --build` (rebuilds image, keeps data)
- ✅ Code updates and container restarts

**NEVER use:**
- ❌ `docker-compose down -v` (the `-v` flag **deletes** volumes!)
- ❌ `docker volume rm nodes-data` (permanently deletes database)

For complete information, see [DATA_PERSISTENCE.md](../../DATA_PERSISTENCE.md).

## Troubleshooting

### Port Already in Use

```bash
# Find what's using port 8000
netstat -ano | findstr :8000  # Windows
sudo lsof -i :8000            # Linux/macOS

# Change port in .env
echo "NODES_PORT=8080" > .env

# Or map to different host port
docker run -p 8080:8000 nodes-app
```

### Container Keeps Restarting

```bash
# Check logs for errors
docker logs nodes-app

# Common causes:
# - Missing .env file
# - Invalid configuration
# - Port conflict
# - Database corruption (restore from backup)
```

### Permission Denied (Linux)

```bash
# Fix volume permissions
docker run --rm -v nodes-data:/data alpine chown -R 1000:1000 /data
```

### Lost Database After Rebuild

See [Troubleshooting Guide](../troubleshooting.md#database-issues) for recovery steps.

## Next Steps

- **Set up backups**: [DATA_PERSISTENCE.md](../../DATA_PERSISTENCE.md)
- **Configure authentication**: [Configuration Guide](../configuration.md#authentication)
- **Production deployment**: [Production Guide](../production-deployment.md)
- **Start using Nodes**: [User Guide](../user-guide.md)
