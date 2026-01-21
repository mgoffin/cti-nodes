#!/bin/bash
# Nodes Database Backup Script
#
# This script creates a timestamped backup of your Nodes database
# from the Docker volume to your local filesystem.
#
# Usage: ./backup-database.sh

set -e

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="nodes-backup-${TIMESTAMP}.tar.gz"
VOLUME_NAME="nodes-data"

echo "🔍 Checking if Docker volume exists..."
if ! docker volume inspect ${VOLUME_NAME} > /dev/null 2>&1; then
    echo "❌ Error: Volume '${VOLUME_NAME}' not found!"
    echo "   Make sure your Nodes container has been started at least once."
    exit 1
fi

echo "📦 Creating backup: ${BACKUP_FILE}"
docker run --rm \
    -v ${VOLUME_NAME}:/data \
    -v $(pwd):/backup \
    alpine tar czf /backup/${BACKUP_FILE} -C /data .

if [ -f "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "✅ Backup created successfully!"
    echo "   File: ${BACKUP_FILE}"
    echo "   Size: ${SIZE}"
    echo ""
    echo "💡 To restore this backup:"
    echo "   docker-compose -f docker/docker-compose.yml down"
    echo "   docker run --rm -v ${VOLUME_NAME}:/data -v \$(pwd):/backup alpine tar xzf /backup/${BACKUP_FILE} -C /data"
    echo "   docker-compose -f docker/docker-compose.yml up -d"
else
    echo "❌ Backup failed!"
    exit 1
fi
