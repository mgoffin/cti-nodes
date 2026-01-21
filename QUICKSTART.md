# Quick Start Guide

Get Nodes up and running in 5 minutes!

## Prerequisites

- **Docker Desktop** installed ([Download](https://www.docker.com/products/docker-desktop/))
- **Git** installed ([Download](https://git-scm.com/downloads))

## Installation (3 Steps)

### 1. Clone the Repository

```bash
git clone https://github.com/mgoffin/cti-nodes.git
cd cti-nodes
```

### 2. Start the Application

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### 3. Open in Browser

Navigate to: **http://localhost:8000**

That's it! You're ready to go.

## Creating Your First Node

1. Click **New Node** button
2. Paste or type your intelligence snippet
3. Add a **source** (required) - URL, person name, file path, etc.
4. Add custom **tags** (optional) - suggestions appear as you type
5. Click **Save**

The system will automatically:
- Extract IOCs (IPs, domains, hashes, URLs)
- Extract entities (threat actors, malware names, tools)
- Find and link related nodes
- Notify you of new connections found

## Exploring Connections

- **List View** (default) - See related nodes inline
- **Graph View** - Visual network graph with configurable depth
- Use the toggle button to switch between views

## Searching

Use the search bar with these patterns:

| Query | What it does |
|-------|--------------|
| `cobalt strike` | Search everywhere (content + tags) |
| `content="*apt28*"` | Search only in node content |
| `tag:source="*twitter*"` | Find nodes from Twitter |
| `tag:adversary=*` | Find all nodes tagged with adversary |

See [docs/user-guide.md](docs/user-guide.md) for advanced search syntax.

## What's Next?

- **Install Chrome Extension** - Capture intel while browsing ([docs/chrome-extension.md](docs/chrome-extension.md))
- **Set Up Backups** - Protect your data ([DATA_PERSISTENCE.md](DATA_PERSISTENCE.md))
- **Enable Authentication** - For team deployments ([docs/configuration.md](docs/configuration.md#authentication))
- **Learn the Platform** - Full user guide ([docs/user-guide.md](docs/user-guide.md))

## Stopping/Starting

```bash
# Stop
docker-compose -f docker/docker-compose.yml down

# Start
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

## Common Issues

### Port 8000 Already in Use

Change the port in your environment:
```bash
# Create .env file
echo "NODES_PORT=8080" > .env

# Restart with new port
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d
```

Access at: http://localhost:8080

### Can't Connect to Docker

Make sure Docker Desktop is running:
- **Windows/Mac**: Check system tray for Docker icon
- **Linux**: Run `sudo systemctl start docker`

### Need Help?

- Full documentation: [README.md](README.md)
- Troubleshooting guide: [docs/troubleshooting.md](docs/troubleshooting.md)
- FAQ: [docs/faq.md](docs/faq.md)

## Next Steps

🔒 **Protect Your Data**: Set up automated backups
```bash
./backup-database.sh  # Linux/macOS
.\backup-database.ps1  # Windows
```

📚 **Learn More**: Check out the [user guide](docs/user-guide.md) for advanced features

🚀 **Production Deployment**: See [production deployment guide](docs/production-deployment.md)
