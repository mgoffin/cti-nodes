# Data Persistence Guide

## 🛡️ Your Data is Safe!

Nodes uses Docker named volumes to ensure **your database persists even when containers are deleted or rebuilt**.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  Docker Host (Your Computer)                                │
│                                                              │
│  ┌────────────────┐         ┌──────────────────┐           │
│  │   Container    │         │   Named Volume   │           │
│  │   nodes-app    │         │   "nodes-data"   │           │
│  │                │         │                  │           │
│  │  /app/data/ ───┼────────>│  nodes.db       │ <── Persists!
│  │                │  mount  │  nodes.db-shm   │           │
│  │                │         │  nodes.db-wal   │           │
│  └────────────────┘         └──────────────────┘           │
│        │                             │                      │
│        │ Temporary                   │ Permanent            │
│        │ (deleted on                 │ (survives            │
│        │  container                  │  container           │
│        │  removal)                   │  removal)            │
│        ▼                             ▼                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Concepts

1. **Container** = Temporary
   - Contains application code and runtime
   - Deleted when you run `docker-compose down`
   - Rebuilt when you change code or run `--build`

2. **Named Volume** = Permanent
   - Stores your database file
   - Lives outside the container
   - Survives container deletion and rebuilds
   - Only deleted if you explicitly remove it

## What's Safe and What's Not

### ✅ SAFE Operations (Data Persists)

```bash
# Stop and remove containers
docker-compose down

# Rebuild and restart
docker-compose up --build

# Restart containers
docker-compose restart

# Switch between dev and production
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.dev.yml up

# Update Docker images
docker-compose pull
docker-compose up -d

# Remove all containers
docker rm -f $(docker ps -aq)
```

### ❌ DANGEROUS Operations (Data Loss)

```bash
# THE -v FLAG DELETES VOLUMES!
docker-compose down -v                    # ⚠️ DON'T USE -v FLAG

# Explicitly deleting the volume
docker volume rm nodes-data               # ⚠️ YOUR DATA IS GONE

# System-wide cleanup with volumes
docker system prune --volumes             # ⚠️ DELETES ALL UNUSED VOLUMES

# Removing the volume during compose down
docker-compose down --volumes             # ⚠️ SAME AS -v
```

## Daily Workflows

### Normal Development

```bash
# Start working
docker-compose -f docker/docker-compose.dev.yml up

# Make code changes
# (Files auto-reload, no rebuild needed!)

# Stop working
docker-compose -f docker/docker-compose.dev.yml down
# ✅ Your data is still in the volume!
```

### After Pulling Updates

```bash
# Stop current container
docker-compose down

# Pull latest code
git pull

# Rebuild and restart
docker-compose up --build
# ✅ Your data is still in the volume!
```

### Switching Modes

```bash
# Stop production
docker-compose -f docker/docker-compose.yml down

# Start development
docker-compose -f docker/docker-compose.dev.yml up
# ✅ Same database, same data!

# Both use the "nodes-data" volume
```

## Backup Strategy

### Quick Backup

```bash
# Linux/macOS
./backup-database.sh

# Windows
.\backup-database.ps1
```

Creates: `nodes-backup-YYYYMMDD-HHMMSS.tar.gz`

### Automated Backups

**Linux/macOS cron:**
```bash
# Add to crontab (daily at 2 AM)
0 2 * * * cd /path/to/nodes && ./backup-database.sh
```

**Windows Task Scheduler:**
```powershell
# Create scheduled task (daily at 2 AM)
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\path\to\nodes\backup-database.ps1" -WorkingDirectory "C:\path\to\nodes"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "NodesBackup" -Description "Daily backup of Nodes database"
```

### Restore from Backup

```bash
# 1. Stop containers
docker-compose down

# 2. Restore from backup
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    tar xzf /backup/nodes-backup-YYYYMMDD-HHMMSS.tar.gz -C /data

# 3. Restart
docker-compose up -d
```

## Verifying Your Data

### Check Volume Exists

```bash
docker volume ls | grep nodes-data
# Output: local     nodes-data
```

### Check Database File

```bash
docker run --rm -v nodes-data:/data alpine ls -lh /data/
# Output: -rw-r--r--  1 root  root  2.3M Dec 11 14:30 nodes.db
```

### Check Database Size

```bash
docker run --rm -v nodes-data:/data alpine du -sh /data/nodes.db
# Output: 2.3M    /data/nodes.db
```

### Run Health Check

```bash
# Linux/macOS
./check-database.sh

# Windows
.\check-database.ps1
```

## Troubleshooting

### I Lost My Database!

**Check if volume still exists:**
```bash
docker volume ls | grep nodes-data
```

**If volume exists, reconnect:**
```bash
docker-compose up -d
# Database should reappear!
```

**If volume is gone, restore from backup:**
```bash
docker volume create nodes-data
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    tar xzf /backup/nodes-backup-YYYYMMDD-HHMMSS.tar.gz -C /data
docker-compose up -d
```

### Volume Permissions Issues

```bash
# Fix permissions (Linux)
docker run --rm -v nodes-data:/data alpine chown -R 1000:1000 /data

# For SELinux systems
podman run -v nodes-data:/app/data:Z nodes-app
```

### Database is Locked

```bash
# Ensure only one container is running
docker ps

# Remove stale lock files
docker run --rm -v nodes-data:/data alpine sh -c "rm -f /data/nodes.db-shm /data/nodes.db-wal"
```

## Migration Guide

### From Non-Docker to Docker

```bash
# 1. Stop your manual installation

# 2. Copy database to current directory
cp /path/to/old/nodes.db ./nodes.db.import

# 3. Create Docker volume
docker volume create nodes-data

# 4. Import database into volume
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    cp /backup/nodes.db.import /data/nodes.db

# 5. Start Docker container
docker-compose up -d
```

### Between Docker Hosts

```bash
# On old host:
./backup-database.sh
# Copy nodes-backup-YYYYMMDD-HHMMSS.tar.gz to new host

# On new host:
git clone https://github.com/mgoffin/cti-nodes.git
cd cti-nodes
docker volume create nodes-data
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    tar xzf /backup/nodes-backup-YYYYMMDD-HHMMSS.tar.gz -C /data
docker-compose up -d
```

## Best Practices

### ✅ Do This

- Use `docker-compose` commands exclusively
- Run backups before major changes
- Test your restore process periodically
- Keep backups in multiple locations
- Monitor database growth
- Document your backup schedule

### ❌ Never Do This

- Use `docker-compose down -v` flag
- Manually delete the `nodes-data` volume
- Run `docker system prune --volumes` without checking
- Skip backups before updates
- Modify database files while container is running
- Share volumes between multiple containers

## Emergency Procedures

### Lost Database, No Backup

Unfortunately, if you've lost the volume and have no backup, your data cannot be recovered. This is why regular backups are critical.

**Prevention:**
1. Set up automated daily backups
2. Store backups off-system (cloud, external drive)
3. Test restore procedure quarterly
4. Monitor backup success/failure
5. Keep multiple backup generations (7 daily, 4 weekly, 12 monthly)

### Corrupted Database

```bash
# 1. Stop container
docker-compose down

# 2. Copy database out for forensics
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    cp /data/nodes.db /backup/nodes.db.corrupted

# 3. Try SQLite recovery
sqlite3 nodes.db.corrupted ".recover" | sqlite3 nodes.db.recovered

# 4. If recovery works, import back
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    cp /backup/nodes.db.recovered /data/nodes.db

# 5. If recovery fails, restore from backup
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    tar xzf /backup/nodes-backup-LATEST.tar.gz -C /data

# 6. Restart
docker-compose up -d
```

## Summary

🎯 **Remember:**
- Named volumes persist your data
- Always use `docker-compose` commands
- Never use the `-v` flag with `down`
- Backup regularly
- Test your backups

🚀 **Quick Commands:**
```bash
# Backup
./backup-database.sh

# Health Check
./check-database.sh

# Restart (safe)
docker-compose restart

# Rebuild (safe)
docker-compose up --build
```

Your data is precious. These tools and practices ensure you never lose it! 🛡️
