# Troubleshooting

Common issues and solutions.

## Docker/Podman Issues

### Port 8000 Already in Use

**Find what's using the port:**
```bash
# Windows
netstat -ano | findstr :8000

# Linux/macOS
sudo lsof -i :8000
```

**Solution 1 - Change Nodes port:**
```bash
echo "NODES_PORT=8080" >> .env
docker-compose down
docker-compose up -d
```

**Solution 2 - Map to different host port:**
```bash
docker run -p 8080:8000 nodes-app
```

### Permission Denied Accessing Volume

**Linux:**
```bash
docker run --rm -v nodes-data:/data alpine chown -R 1000:1000 /data
```

**Podman with SELinux:**
```bash
podman run -v nodes-data:/app/data:Z nodes-app
```

### Container Keeps Restarting

**Check logs:**
```bash
docker logs nodes-app
```

**Common causes:**
- Missing `.env` file
- Invalid configuration (check JSON syntax in CORS_ORIGINS)
- Port conflict (see above)
- Database corruption (restore from backup)

**Solution:**
1. Review logs for specific error
2. Verify `.env` matches `.env.example` format
3. Check port availability
4. Try restoring from backup if database is corrupted

## Database Issues

### Lost Database After Rebuilding Container

⚠️ Most common issue! Your database should be safe in the Docker volume.

**Check if volume exists:**
```bash
docker volume ls | grep nodes-data
```

**If volume exists, verify database file:**
```bash
docker run --rm -v nodes-data:/data alpine ls -lh /data/
```

**If you see nodes.db, reconnect to it:**
```bash
docker-compose up -d
```

**If database file exists but appears empty:**
1. Stop container
2. Check `NODES_DATABASE_PATH=/app/data/nodes.db` in `.env`
3. Rebuild and restart

```bash
docker-compose down
docker-compose up -d --build
```

**If volume was accidentally deleted:**
```bash
# Check for backups
ls -lh nodes-backup-*.tar.gz

# Restore from backup
docker volume create nodes-data
docker run --rm -v nodes-data:/data -v $(pwd):/backup alpine \
    tar xzf /backup/nodes-backup-YYYYMMDD-HHMMSS.tar.gz -C /data
docker-compose up -d
```

**Prevention:**
- Never use `docker-compose down -v` (the `-v` flag deletes volumes!)
- Set up automated backups
- Test backup/restore process regularly

See [DATA_PERSISTENCE.md](../DATA_PERSISTENCE.md) for complete details.

### Database Locked Errors

**Cause:** Multiple processes accessing SQLite simultaneously or stale lock files.

**Solution:**
```bash
# Ensure only one backend instance is running
docker ps

# Remove stale lock files
docker exec nodes-app rm -f /app/data/nodes.db-shm /app/data/nodes.db-wal

# Restart container
docker-compose restart
```

### Full-Text Search Not Working

**Rebuild FTS indexes:**
```bash
docker exec nodes-app python -c "
from app.core.database import get_db_connection
conn = get_db_connection()
conn.execute('INSERT INTO nodes_fts(nodes_fts) VALUES(\"rebuild\")')
conn.commit()
print('FTS index rebuilt')
"
```

### Migration Script Fails

**The migration script is idempotent - safe to run multiple times.**

**If it fails:**
1. Backup is automatically created at `nodes.db.backup.TIMESTAMP`
2. Restore if needed: `cp nodes.db.backup.TIMESTAMP nodes.db`
3. Check for table existence: `sqlite3 nodes.db ".tables"`
4. Report as bug if specific tables are missing

## Authentication Issues

### SSO Login Fails with "Invalid Redirect URI"

**Check these:**
- `NODES_SSO_REDIRECT_URI` exactly matches URI in SSO provider config
- URI includes protocol (`http://` or `https://`)
- SSO provider has URI in allowed list
- No trailing slashes mismatch

**Example:**
```bash
# In .env
NODES_SSO_REDIRECT_URI=https://threat-intel.company.com/api/auth/callback

# In SSO provider
# Should be exactly: https://threat-intel.company.com/api/auth/callback
```

### "First User Becomes Admin" Didn't Work

**Check if users already exist:**
```bash
docker exec nodes-app sqlite3 /app/data/nodes.db "SELECT * FROM users;"
```

**If users exist:**
- Delete test users and try again
- Or manually promote user to admin:

```bash
docker exec nodes-app sqlite3 /app/data/nodes.db \
    "UPDATE users SET role='admin' WHERE email='your@email.com';"
```

**Verify auth is enabled:**
```bash
# In .env
NODES_AUTH_ENABLED=true
```

### JWT Token Errors

**Regenerate JWT secret:**
```bash
openssl rand -hex 32
# Add to .env as NODES_JWT_SECRET_KEY
```

**Clear browser cookies:**
- Open browser DevTools (F12)
- Application tab → Cookies
- Delete all Nodes cookies
- Try logging in again

**Check token expiry:**
```bash
# In .env - don't set these too short
NODES_ACCESS_TOKEN_EXPIRE_MINUTES=15
NODES_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Frontend Issues

### Blank Page or "Failed to Fetch"

**Check backend is running:**
```bash
curl http://localhost:8000/api/health
# Should return: {"status":"healthy","database":"connected"}
```

**Check CORS settings:**
```bash
# In .env
NODES_CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]
```

**Check browser console (F12):**
- Look for CORS errors
- Look for network failures
- Check if API URL is correct

**Try different browser:**
- Chrome/Edge recommended
- Firefox may have stricter CORS policies

### Auto-Linking Not Working

**Verify extractors are detecting entities:**
1. Create or edit a node with IOCs
2. View node detail
3. Check if entities appear in "Extracted Entities" section

**If no entities detected:**
- Check that content contains recognizable IOCs
- File a bug report with example content

**If entities detected but no edges created:**
- Check if there are related nodes to link to
- Try creating a second node with same IOC
- Check edge table: `SELECT * FROM edges LIMIT 10;`

## Performance Issues

### Slow Search with Large Database

**Verify FTS indexes exist:**
```bash
docker exec nodes-app sqlite3 /app/data/nodes.db \
    "SELECT * FROM nodes_fts LIMIT 1;"
```

**Check disk space:**
```bash
df -h  # Linux/macOS
```

SQLite requires free space for temporary files.

**Vacuum database to reclaim space:**
```bash
docker exec nodes-app sqlite3 /app/data/nodes.db "VACUUM;"
```

### Graph View Slow with Many Nodes

**Solutions:**
- Use depth slider to limit graph size
- Filter by tags before opening graph view
- Try different browser (Chrome recommended)
- Upgrade hardware (graph rendering is client-side)

### Slow Container Startup

**Development mode:**
- After first build, omit `--build` flag:

```bash
docker-compose -f docker/docker-compose.dev.yml up
```

**Production mode:**
- Only rebuild when code changes:

```bash
# Normal start (fast)
docker-compose up -d

# Rebuild only when needed
docker-compose up -d --build
```

## Chrome Extension Issues

### Extension Shows "Failed to Connect"

**Check:**
1. Nodes is running: `curl http://localhost:8000/api/health`
2. API URL configured correctly in extension popup
3. CORS settings allow extension

**Fix CORS:**
```bash
# In .env, add chrome-extension:// if needed
NODES_CORS_ORIGINS=["http://localhost:8000","chrome-extension://your-extension-id"]
```

### "Add to Nodes" Creates Empty Node

**Check:**
- Text is actually selected before right-clicking
- Page URL is accessible (not chrome:// or file://)
- Extension has permissions for current site

### Toast Notifications Don't Appear

**Check browser permissions:**
- Settings → Privacy → Notifications
- Allow for extension

## Development Issues

### Hot-Reload Not Working

**Backend (Python):**
- Ensure `NODES_DEBUG=true` in environment
- Check that you're using development compose file
- Verify volume mounts in `docker-compose.dev.yml`

**Frontend (React):**
- Ensure using `npm run dev` (not `npm run build`)
- Check Vite dev server is running on port 5173
- Clear browser cache (Ctrl+Shift+Delete)

### Module Not Found Errors

**Python:**
```bash
# Activate venv
source backend/venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

**JavaScript:**
```bash
# Clear and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Getting Help

Still having issues?

1. **Check logs:**
   ```bash
   docker logs nodes-app
   ```

2. **Verify configuration:**
   - Compare your `.env` to `.env.example`
   - Check for JSON syntax errors in array values

3. **Try without authentication:**
   ```bash
   NODES_AUTH_ENABLED=false
   ```

4. **Test with fresh database:**
   ```bash
   # Backup first!
   docker-compose down
   docker volume rm nodes-data
   docker volume create nodes-data
   docker-compose up -d
   ```

5. **Search GitHub issues** (link TBD)

6. **File a bug report** with:
   - Environment (Docker/Podman/Manual, OS, version)
   - Relevant logs
   - Steps to reproduce
   - Expected vs actual behavior

## Next Steps

- **Data safety**: [DATA_PERSISTENCE.md](../DATA_PERSISTENCE.md)
- **Configuration**: [configuration.md](configuration.md)
- **FAQ**: [faq.md](faq.md)
