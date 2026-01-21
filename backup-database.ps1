# Nodes Database Backup Script (PowerShell)
#
# This script creates a timestamped backup of your Nodes database
# from the Docker volume to your local filesystem.
#
# Usage: .\backup-database.ps1

$ErrorActionPreference = "Stop"

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupFile = "nodes-backup-$Timestamp.tar.gz"
$VolumeName = "nodes-data"

Write-Host "🔍 Checking if Docker volume exists..." -ForegroundColor Cyan
$volumeExists = docker volume inspect $VolumeName 2>$null
if (-not $volumeExists) {
    Write-Host "❌ Error: Volume '$VolumeName' not found!" -ForegroundColor Red
    Write-Host "   Make sure your Nodes container has been started at least once."
    exit 1
}

Write-Host "📦 Creating backup: $BackupFile" -ForegroundColor Cyan
docker run --rm `
    -v ${VolumeName}:/data `
    -v ${PWD}:/backup `
    alpine tar czf /backup/$BackupFile -C /data .

if (Test-Path $BackupFile) {
    $Size = (Get-Item $BackupFile).Length / 1MB
    Write-Host "✅ Backup created successfully!" -ForegroundColor Green
    Write-Host "   File: $BackupFile"
    Write-Host "   Size: $($Size.ToString('0.00')) MB"
    Write-Host ""
    Write-Host "💡 To restore this backup:" -ForegroundColor Yellow
    Write-Host "   docker-compose -f docker/docker-compose.yml down"
    Write-Host "   docker run --rm -v ${VolumeName}:/data -v `${PWD}:/backup alpine tar xzf /backup/$BackupFile -C /data"
    Write-Host "   docker-compose -f docker/docker-compose.yml up -d"
} else {
    Write-Host "❌ Backup failed!" -ForegroundColor Red
    exit 1
}
