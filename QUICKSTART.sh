#!/bin/bash
# QUICKSTART - Nodes Intelligence Platform
#
# This script helps you get started with Nodes quickly and safely.

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║                    NODES QUICKSTART GUIDE                        ║
║            Threat Intelligence Knowledge Graph                   ║
╚══════════════════════════════════════════════════════════════════╝

🚀 FIRST TIME SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Configure (optional):
   cp .env.example .env
   # Edit .env to customize settings

2. Start the application:
   docker-compose -f docker/docker-compose.yml up -d

3. Open in browser:
   http://localhost:8000

4. Start capturing threat intelligence!

📦 DATABASE PERSISTENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Your database is SAFE and persists in a Docker volume!

Safe commands:
  docker-compose down              ✅ Stops, data stays
  docker-compose up --build        ✅ Rebuilds, data stays
  docker-compose restart           ✅ Restarts, data stays

NEVER use:
  docker-compose down -v           ❌ DELETES YOUR DATA!
  docker volume rm nodes-data      ❌ DELETES YOUR DATA!

📚 Read more: DATA_PERSISTENCE.md

🛡️  BACKUP YOUR DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Create backup:
  ./backup-database.sh             (Linux/macOS)
  .\backup-database.ps1            (Windows)

Check health:
  ./check-database.sh              (Linux/macOS)
  .\check-database.ps1             (Windows)

💡 Run backups regularly, especially before updates!

🔧 DAILY COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Start:     docker-compose up -d
Stop:      docker-compose down
Restart:   docker-compose restart
Logs:      docker-compose logs -f
Update:    git pull && docker-compose up -d --build

Development mode (hot-reload):
  docker-compose -f docker/docker-compose.dev.yml up

📖 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Getting Started:
  QUICKSTART.md                    - 5-minute setup guide
  docs/installation/docker.md      - Docker installation (recommended)
  docs/installation/podman.md      - Podman alternative
  docs/installation/manual.md      - Manual installation

Configuration & Usage:
  docs/configuration.md            - Settings and authentication
  docs/user-guide.md               - Complete platform guide
  docs/chrome-extension.md         - Browser extension

Data Safety & Production:
  DATA_PERSISTENCE.md              - Critical data safety info
  docs/production-deployment.md    - Production best practices

Help:
  docs/troubleshooting.md          - Common issues
  docs/faq.md                      - FAQ
  docs/architecture.md             - Technical deep dive

🆘 HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Lost database?   See DATA_PERSISTENCE.md → Troubleshooting
Port conflicts?  See README.md → Troubleshooting
Auth issues?     See README.md → Authentication

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
