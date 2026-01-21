#!/bin/bash
# Nodes Database Health Check Script
#
# This script verifies your database is accessible and provides status information.
#
# Usage: ./check-database.sh

set -e

VOLUME_NAME="nodes-data"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔍 Checking Nodes database health..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "   Please start Docker Desktop or the Docker daemon."
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# Check if volume exists
if ! docker volume inspect ${VOLUME_NAME} > /dev/null 2>&1; then
    echo -e "${RED}❌ Volume '${VOLUME_NAME}' not found!${NC}"
    echo "   The database volume doesn't exist yet."
    echo "   Start your Nodes container to create it:"
    echo "   docker-compose -f docker/docker-compose.yml up -d"
    exit 1
fi
echo -e "${GREEN}✅ Volume '${VOLUME_NAME}' exists${NC}"

# Check if database file exists
DB_EXISTS=$(docker run --rm -v ${VOLUME_NAME}:/data alpine test -f /data/nodes.db && echo "yes" || echo "no")
if [ "$DB_EXISTS" = "no" ]; then
    echo -e "${YELLOW}⚠️  Database file not found in volume${NC}"
    echo "   The volume exists but nodes.db is missing."
    echo "   This is normal for a fresh installation."
    echo "   Start your Nodes container to initialize the database:"
    echo "   docker-compose -f docker/docker-compose.yml up -d"
    exit 0
fi
echo -e "${GREEN}✅ Database file exists${NC}"

# Get database size
DB_SIZE=$(docker run --rm -v ${VOLUME_NAME}:/data alpine du -sh /data/nodes.db | cut -f1)
echo -e "${GREEN}✅ Database size: ${DB_SIZE}${NC}"

# Check if container is running
CONTAINER_RUNNING=$(docker ps --filter "name=nodes-app" --filter "name=nodes-dev" --format "{{.Names}}" | head -n 1)
if [ -z "$CONTAINER_RUNNING" ]; then
    echo -e "${YELLOW}⚠️  No Nodes container is currently running${NC}"
    echo "   Start your container with:"
    echo "   docker-compose -f docker/docker-compose.yml up -d"
else
    echo -e "${GREEN}✅ Container '${CONTAINER_RUNNING}' is running${NC}"
fi

# List recent backups
BACKUP_COUNT=$(ls -1 nodes-backup-*.tar.gz 2>/dev/null | wc -l)
if [ $BACKUP_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ Found ${BACKUP_COUNT} backup(s)${NC}"
    echo "   Latest backups:"
    ls -lht nodes-backup-*.tar.gz 2>/dev/null | head -n 3 | awk '{print "   - "$9" ("$5")"}'
else
    echo -e "${YELLOW}⚠️  No backups found${NC}"
    echo "   Create a backup with: ./backup-database.sh"
fi

echo ""
echo -e "${GREEN}✨ Database is healthy!${NC}"
