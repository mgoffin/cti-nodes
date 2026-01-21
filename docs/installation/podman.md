# Installing Nodes with Podman

Podman is a daemonless Docker alternative that's especially popular on RHEL/Fedora systems. It offers rootless container execution for better security.

## Installing Podman

### Linux (Fedora/RHEL/CentOS)
```bash
sudo dnf install podman podman-compose
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install podman podman-compose
```

### macOS
```bash
brew install podman podman-compose
podman machine init
podman machine start
```

### Windows
Download from [Podman Desktop](https://podman-desktop.io/) or use Chocolatey:
```powershell
choco install podman-desktop
```

## Installation Steps

### Step 1: Clone and Configure

```bash
git clone https://github.com/mgoffin/cti-nodes.git
cd cti-nodes

# Configure environment
cp .env.example .env
# Edit .env with your settings (see Configuration Guide)
```

### Step 2: Build and Run

Podman commands are nearly identical to Docker:

```bash
# Build and run with podman-compose
podman-compose -f docker/docker-compose.yml up -d --build

# Or run in foreground
podman-compose -f docker/docker-compose.yml up --build
```

**Alternative: Use Podman directly without compose:**

```bash
# Build the image
podman build -t nodes-app -f docker/Dockerfile .

# Create volume for data persistence
podman volume create nodes-data

# Run the container
podman run -d \
  --name nodes-app \
  -p 8000:8000 \
  -v nodes-data:/app/data:Z \
  --env-file .env \
  nodes-app

# Note: The :Z flag is important for SELinux systems (Fedora/RHEL)
```

Access at: **http://localhost:8000**

### Step 3: Database Migration (If Enabling Authentication)

```bash
podman exec -it nodes-app /bin/bash
cd /app/backend
python migrate_v2_users.py
exit
```

## Podman Management Commands

### Starting and Stopping

```bash
# Stop containers
podman-compose -f docker/docker-compose.yml down
# Or: podman stop nodes-app

# Start containers
podman-compose -f docker/docker-compose.yml up -d
# Or: podman start nodes-app

# Restart
podman-compose -f docker/docker-compose.yml restart
# Or: podman restart nodes-app
```

### Viewing Logs

```bash
# With compose
podman-compose -f docker/docker-compose.yml logs -f

# Direct command
podman logs -f nodes-app
```

### Updating

```bash
git pull
podman-compose -f docker/docker-compose.yml up -d --build
```

### Accessing Container Shell

```bash
podman exec -it nodes-app /bin/bash
```

## Data Management

### Backing Up

```bash
# Podman volumes work the same as Docker
podman run --rm -v nodes-data:/data -v $(pwd):/backup:Z alpine \
    tar czf /backup/nodes-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
```

### Restoring

```bash
podman-compose -f docker/docker-compose.yml down
podman run --rm -v nodes-data:/data -v $(pwd):/backup:Z alpine \
    tar xzf /backup/nodes-backup-YYYYMMDD-HHMMSS.tar.gz -C /data
podman-compose -f docker/docker-compose.yml up -d
```

## Podman-Specific Features

### Rootless Mode (Linux)

Podman runs containers without root privileges by default:

```bash
# Check if running rootless
podman info | grep rootless

# All commands work the same, but containers run as your user
```

### Generate Systemd Service (Linux)

Run Nodes as a system service that starts on boot:

```bash
# Generate service file
podman generate systemd --new --name nodes-app > ~/.config/systemd/user/nodes-app.service

# Enable and start
systemctl --user daemon-reload
systemctl --user enable nodes-app.service
systemctl --user start nodes-app.service

# Check status
systemctl --user status nodes-app.service
```

### Podman Desktop (GUI)

[Podman Desktop](https://podman-desktop.io/) provides a Docker Desktop-like experience with:
- Container management
- Image building
- Volume inspection
- Compose file support

## Troubleshooting

### SELinux Permission Denied

Use the `:Z` flag on volume mounts:
```bash
podman run -v nodes-data:/app/data:Z nodes-app
```

### Machine Not Running (macOS/Windows)

```bash
# Start the Podman machine
podman machine start

# List machines
podman machine list
```

### Port Already in Use

Same as Docker - change `NODES_PORT` in `.env` or map to different host port.

## Next Steps

- **Set up backups**: [DATA_PERSISTENCE.md](../../DATA_PERSISTENCE.md)
- **Configure settings**: [Configuration Guide](../configuration.md)
- **Production deployment**: [Production Guide](../production-deployment.md)
- **Start using Nodes**: [User Guide](../user-guide.md)
