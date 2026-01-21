# Nodes Database Health Check Script (PowerShell)
#
# This script verifies your database is accessible and provides status information.
#
# Usage: .\check-database.ps1

$ErrorActionPreference = "Stop"

$VolumeName = "nodes-data"

Write-Host "🔍 Checking Nodes database health..." -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info 2>&1 | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running!" -ForegroundColor Red
    Write-Host "   Please start Docker Desktop or the Docker daemon."
    exit 1
}

# Check if volume exists
$volumeExists = docker volume inspect $VolumeName 2>$null
if (-not $volumeExists) {
    Write-Host "❌ Volume '$VolumeName' not found!" -ForegroundColor Red
    Write-Host "   The database volume doesn't exist yet."
    Write-Host "   Start your Nodes container to create it:"
    Write-Host "   docker-compose -f docker/docker-compose.yml up -d"
    exit 1
}
Write-Host "✅ Volume '$VolumeName' exists" -ForegroundColor Green

# Check if database file exists
$dbExists = docker run --rm -v ${VolumeName}:/data alpine test -f /data/nodes.db
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Database file not found in volume" -ForegroundColor Yellow
    Write-Host "   The volume exists but nodes.db is missing."
    Write-Host "   This is normal for a fresh installation."
    Write-Host "   Start your Nodes container to initialize the database:"
    Write-Host "   docker-compose -f docker/docker-compose.yml up -d"
    exit 0
}
Write-Host "✅ Database file exists" -ForegroundColor Green

# Get database size
$dbSizeOutput = docker run --rm -v ${VolumeName}:/data alpine du -sh /data/nodes.db
$dbSize = ($dbSizeOutput -split '\s+')[0]
Write-Host "✅ Database size: $dbSize" -ForegroundColor Green

# Check if container is running
$containerRunning = docker ps --filter "name=nodes-app" --filter "name=nodes-dev" --format "{{.Names}}" | Select-Object -First 1
if ([string]::IsNullOrEmpty($containerRunning)) {
    Write-Host "⚠️  No Nodes container is currently running" -ForegroundColor Yellow
    Write-Host "   Start your container with:"
    Write-Host "   docker-compose -f docker/docker-compose.yml up -d"
} else {
    Write-Host "✅ Container '$containerRunning' is running" -ForegroundColor Green
}

# List recent backups
$backups = Get-ChildItem -Path "nodes-backup-*.tar.gz" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($backups.Count -gt 0) {
    Write-Host "✅ Found $($backups.Count) backup(s)" -ForegroundColor Green
    Write-Host "   Latest backups:"
    $backups | Select-Object -First 3 | ForEach-Object {
        $sizeMB = ($_.Length / 1MB).ToString("0.00")
        Write-Host "   - $($_.Name) ($sizeMB MB)"
    }
} else {
    Write-Host "⚠️  No backups found" -ForegroundColor Yellow
    Write-Host "   Create a backup with: .\backup-database.ps1"
}

Write-Host ""
Write-Host "✨ Database is healthy!" -ForegroundColor Green
