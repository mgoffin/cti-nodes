# Manual Installation

Install Nodes directly on your system without containers. Best for development or when Docker/Podman isn't available.

## Prerequisites

- **Python 3.14+** - [Download](https://www.python.org/downloads/)
- **Node.js 22+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/downloads)

## Installation

### Linux / macOS

```bash
# Clone repository
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

# Configure (optional)
cd ..
cp .env.example .env
# Edit .env if needed
```

### Windows (Command Prompt)

```cmd
:: Clone repository
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

:: Configure (optional)
cd ..
copy .env.example .env
:: Edit .env if needed
```

### Windows (PowerShell)

```powershell
# Clone repository
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

# Configure (optional)
cd ..
cp .env.example .env
# Edit .env if needed
```

## Running the Application

### Production Mode

**Linux/macOS:**
```bash
cd backend
source venv/bin/activate
python -m app.main
```

**Windows (Command Prompt):**
```cmd
cd backend
venv\Scripts\activate
python -m app.main
```

**Windows (PowerShell):**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m app.main
```

Access at: **http://localhost:8000**

### Development Mode (Hot-Reload)

Run backend and frontend separately for instant code changes:

**Terminal 1 - Backend:**
```bash
# Linux/macOS
cd backend
source venv/bin/activate
NODES_DEBUG=true python -m app.main

# Windows (Command Prompt)
cd backend
venv\Scripts\activate
set NODES_DEBUG=true
python -m app.main

# Windows (PowerShell)
cd backend
.\venv\Scripts\Activate.ps1
$env:NODES_DEBUG="true"
python -m app.main
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Frontend dev server: **http://localhost:5173**

## Using Make (Optional)

If you have `make` installed (Linux/macOS):

```bash
# Install all dependencies
make install

# Build frontend
make build

# Run application
make run
```

For Windows with Make:
```cmd
make install-backend-win
make install-frontend
make build
make run-backend-win
```

## Data Management

### Database Location

By default, the database is created at:
- **Linux/macOS**: `backend/data/nodes.db`
- **Windows**: `backend\data\nodes.db`

Change location with `NODES_DATABASE_PATH` in `.env`.

### Backing Up

```bash
# Stop the application first
# Then copy the database file

# Linux/macOS
cp backend/data/nodes.db backup/nodes-$(date +%Y%m%d-%H%M%S).db

# Windows (PowerShell)
Copy-Item backend\data\nodes.db -Destination backup\nodes-$(Get-Date -Format 'yyyyMMdd-HHmmss').db

# Compress
gzip backup/nodes-*.db
```

### Restoring

```bash
# Stop the application
# Copy backup to original location

# Linux/macOS
gunzip -c backup/nodes-YYYYMMDD-HHMMSS.db.gz > backend/data/nodes.db

# Windows (PowerShell)
# Use 7-Zip or similar to decompress
Copy-Item backup\nodes-YYYYMMDD-HHMMSS.db -Destination backend\data\nodes.db
```

## Running as a Service

### Linux (systemd)

Create `/etc/systemd/system/nodes.service`:

```ini
[Unit]
Description=Nodes Threat Intelligence Platform
After=network.target

[Service]
Type=simple
User=your_username
Group=your_group
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

### Windows (Task Scheduler)

Create a scheduled task to run at startup:

```powershell
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-File C:\path\to\cti-nodes\run-nodes.ps1" `
    -WorkingDirectory "C:\path\to\cti-nodes"

$trigger = New-ScheduledTaskTrigger -AtStartup

Register-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -TaskName "Nodes" `
    -Description "Nodes Threat Intelligence Platform"
```

Create `run-nodes.ps1`:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m app.main
```

## Troubleshooting

### Module Not Found Errors

```bash
# Ensure virtual environment is activated
# Linux/macOS
source backend/venv/bin/activate

# Windows
backend\venv\Scripts\activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Port Already in Use

Change port in `.env`:
```bash
NODES_PORT=8080
```

### Frontend Build Fails

```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Database Permission Errors

```bash
# Ensure data directory exists and is writable
mkdir -p backend/data
chmod 755 backend/data  # Linux/macOS
```

## Next Steps

- **Configure settings**: [Configuration Guide](../configuration.md)
- **Set up production deployment**: [Production Guide](../production-deployment.md)
- **Start using Nodes**: [User Guide](../user-guide.md)
