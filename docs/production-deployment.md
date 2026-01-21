# Production Deployment

Best practices for deploying Nodes in production.

## Overview

For production deployments, you should:
1. Use HTTPS with a reverse proxy
2. Enable authentication for team access
3. Set up automated backups
4. Configure monitoring
5. Optimize resource allocation

## 1. Reverse Proxy with HTTPS

**Never expose Nodes directly to the internet.** Always use a reverse proxy with TLS certificates.

### Caddy (Easiest)

Caddy automatically handles HTTPS certificates.

**Caddyfile:**
```caddy
threat-intel.company.com {
    reverse_proxy localhost:8000

    # Optional: Restrict access by IP
    @internal {
        remote_ip 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16
    }
    handle @internal {
        reverse_proxy localhost:8000
    }
    respond 403
}
```

**Start Caddy:**
```bash
sudo caddy start --config /etc/caddy/Caddyfile
```

### Nginx

**`/etc/nginx/sites-available/nodes`:**
```nginx
server {
    listen 443 ssl http2;
    server_name threat-intel.company.com;

    ssl_certificate /etc/letsencrypt/live/threat-intel.company.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/threat-intel.company.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name threat-intel.company.com;
    return 301 https://$server_name$request_uri;
}
```

**Enable and restart:**
```bash
sudo ln -s /etc/nginx/sites-available/nodes /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Traefik

**docker-compose.yml:**
```yaml
services:
  nodes:
    # ... existing config ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.nodes.rule=Host(`threat-intel.company.com`)"
      - "traefik.http.routers.nodes.entrypoints=websecure"
      - "traefik.http.routers.nodes.tls.certresolver=letsencrypt"
      - "traefik.http.services.nodes.loadbalancer.server.port=8000"
```

## 2. Configure Authentication

Enable SSO for team access. See [configuration.md](configuration.md#authentication) for complete details.

**Example production auth config:**
```bash
# In .env
NODES_AUTH_ENABLED=true
NODES_SSO_PROVIDER=okta
NODES_SSO_DISPLAY_NAME="Company SSO"
NODES_SSO_CLIENT_ID=0oa1234567890abcdef
NODES_SSO_CLIENT_SECRET=your_secret_here
NODES_SSO_REDIRECT_URI=https://threat-intel.company.com/api/auth/callback
NODES_JWT_SECRET_KEY=$(openssl rand -hex 32)

# Security
NODES_ACCESS_TOKEN_EXPIRE_MINUTES=15
NODES_REFRESH_TOKEN_EXPIRE_DAYS=7
NODES_RATE_LIMIT_ENABLED=true
NODES_RATE_LIMIT_PER_MINUTE=60

# Audit
NODES_AUDIT_LOG_ENABLED=true
NODES_AUDIT_LOG_RETENTION_DAYS=90

# CORS
NODES_CORS_ORIGINS=["https://threat-intel.company.com"]
```

**Run migration if enabling on existing database:**
```bash
docker exec -it nodes-app /bin/bash
cd /app/backend
python migrate_v2_users.py
exit
```

## 3. Automated Backups

### Daily Backup Script

**`/usr/local/bin/backup-nodes.sh`:**
```bash
#!/bin/bash
BACKUP_DIR="/backups/nodes"
DATE=$(date +%Y%m%d-%H%M%S)

# Create backup
docker run --rm \
  -v nodes-data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/nodes-$DATE.tar.gz -C /data .

# Keep only last 30 days
find $BACKUP_DIR -name "nodes-*.tar.gz" -mtime +30 -delete

# Optional: Upload to S3
# aws s3 cp $BACKUP_DIR/nodes-$DATE.tar.gz s3://your-bucket/nodes-backups/

echo "Backup completed: nodes-$DATE.tar.gz"
```

**Make executable:**
```bash
sudo chmod +x /usr/local/bin/backup-nodes.sh
```

### Add to Crontab

```bash
sudo crontab -e
```

**Daily at 2 AM:**
```cron
0 2 * * * /usr/local/bin/backup-nodes.sh >> /var/log/nodes-backup.log 2>&1
```

### Test Backup

```bash
# Test backup
sudo /usr/local/bin/backup-nodes.sh

# Test restore
docker-compose down
docker run --rm -v nodes-data:/data -v /backups/nodes:/backup alpine \
    tar xzf /backup/nodes-YYYYMMDD-HHMMSS.tar.gz -C /data
docker-compose up -d
```

## 4. Monitoring and Health Checks

### Health Check Endpoint

Nodes provides `/api/health`:

```bash
curl https://threat-intel.company.com/api/health
# Response: {"status":"healthy","database":"connected"}
```

### Uptime Monitoring

**UptimeRobot / Pingdom:**
- Monitor: `https://threat-intel.company.com/api/health`
- Check interval: 5 minutes
- Alert on non-200 response

### Log Monitoring

**View logs:**
```bash
docker logs -f nodes-app
```

**Send to logging service:**
```yaml
# docker-compose.yml
services:
  nodes:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Metrics (Optional)

For Prometheus monitoring:

**docker-compose.yml:**
```yaml
services:
  nodes:
    ports:
      - "8000:8000"
      # Expose metrics endpoint if you add one
```

## 5. Resource Requirements

| Deployment Size | Users | Nodes | CPU | Memory | Disk |
|----------------|-------|-------|-----|--------|------|
| **Small** | 1-3 | < 10k | 1 core | 512MB | 1GB |
| **Medium** | 3-10 | 10k-100k | 2 cores | 1GB | 5GB |
| **Large** | 10+ | 100k+ | 4+ cores | 2GB | 20GB+ |

**SQLite** performs well for < 10 concurrent users. For larger teams (20+), consider PostgreSQL migration (planned feature).

### Docker Resource Limits

**docker-compose.yml:**
```yaml
services:
  nodes:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 6. Systemd Service (Linux)

For bare metal/VM deployments, use systemd.

### Docker Compose Service

**`/etc/systemd/system/nodes.service`:**
```ini
[Unit]
Description=Nodes Threat Intelligence Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/cti-nodes
ExecStart=/usr/local/bin/docker-compose -f docker/docker-compose.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker/docker-compose.yml down
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable nodes
sudo systemctl start nodes
sudo systemctl status nodes
```

### Manual Installation Service

**`/etc/systemd/system/nodes.service`:**
```ini
[Unit]
Description=Nodes Threat Intelligence Platform
After=network.target

[Service]
Type=simple
User=nodes
Group=nodes
WorkingDirectory=/opt/cti-nodes/backend
Environment="PATH=/opt/cti-nodes/backend/venv/bin"
EnvironmentFile=/opt/cti-nodes/.env
ExecStart=/opt/cti-nodes/backend/venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 7. Security Hardening

### Firewall

**Only expose reverse proxy:**
```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Block direct access to Nodes port
# (Only allow from localhost, reverse proxy accesses it)
```

### File Permissions

```bash
# Secure .env file
chmod 600 .env
chown root:root .env  # or appropriate user

# Secure backup directory
chmod 700 /backups/nodes
```

### Docker Security

**docker-compose.yml:**
```yaml
services:
  nodes:
    security_opt:
      - no-new-privileges:true
    read_only: false  # Needs write access to /tmp
    tmpfs:
      - /tmp
```

### Regular Updates

```bash
# Update Nodes
cd /opt/cti-nodes
git pull
docker-compose down
docker-compose up -d --build

# Update system packages
sudo apt update && sudo apt upgrade -y  # Debian/Ubuntu
sudo dnf update -y  # RHEL/Fedora
```

## 8. High Availability (Advanced)

For critical deployments:

### Database Replication

SQLite doesn't support replication. For HA, consider:
- PostgreSQL migration (planned feature)
- Scheduled backups with fast restore
- Standby server with replication

### Load Balancing

For > 10 concurrent users:
- Deploy multiple Nodes instances
- Use shared PostgreSQL backend
- Load balance with nginx/HAProxy

**This requires PostgreSQL migration (planned feature).**

## 9. Disaster Recovery

### Recovery Time Objective (RTO)

How fast can you recover?

**With backups:**
1. Provision new server (5-10 min)
2. Install Docker (2 min)
3. Clone repo (1 min)
4. Restore from backup (2 min)
5. Start container (1 min)

**Total: ~15-20 minutes**

### Recovery Point Objective (RPO)

How much data can you lose?

- **Daily backups**: Up to 24 hours of data loss
- **Hourly backups**: Up to 1 hour of data loss
- **Real-time replication**: Near-zero data loss (requires PostgreSQL)

### Test DR Plan

**Quarterly:**
1. Spin up test server
2. Restore from backup
3. Verify all data accessible
4. Time the process
5. Document any issues

## 10. Compliance

### Data Retention

Configure audit log retention:
```bash
NODES_AUDIT_LOG_RETENTION_DAYS=90  # or per your policy
```

### Access Control

- Use SSO for authentication
- Assign appropriate roles (Admin/Analyst/Viewer)
- Review user access quarterly

### Audit Logging

When auth enabled:
- All modifications logged
- Includes user, timestamp, changes
- Queryable via API or database

### Data Encryption

- **In transit**: HTTPS via reverse proxy
- **At rest**: Consider full-disk encryption for host

SQLite database is not encrypted by default. For encryption:
- Use LUKS/dm-crypt for full-disk encryption
- Or use SQLCipher (requires code changes)

## Deployment Checklist

- [ ] HTTPS configured with valid certificate
- [ ] Authentication enabled and tested
- [ ] Automated daily backups configured
- [ ] Backup restore tested successfully
- [ ] Health check monitoring enabled
- [ ] Firewall rules configured
- [ ] `.env` file permissions restricted (600)
- [ ] Systemd service configured (if applicable)
- [ ] Resource limits set appropriately
- [ ] Logging configured
- [ ] DR plan documented
- [ ] Team trained on using the platform

## Next Steps

- **Configure settings**: [configuration.md](configuration.md)
- **User training**: [user-guide.md](user-guide.md)
- **Monitor health**: Set up monitoring
- **Test backups**: Verify restore process works
