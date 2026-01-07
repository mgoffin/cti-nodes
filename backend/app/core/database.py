"""SQLite database connection and initialization."""

import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Current database schema version
CURRENT_DB_VERSION = 2


# SQL schema for creating tables
SCHEMA = """
-- Database version tracking
CREATE TABLE IF NOT EXISTS db_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- Nodes table: stores the main content
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    author TEXT DEFAULT 'Anonymous'
);

-- Tags table: key-value pairs associated with nodes
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    author TEXT DEFAULT 'Anonymous',
    created_at TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- Edges table: relationships between nodes
CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    match_value TEXT,
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    author TEXT DEFAULT 'Anonymous',
    FOREIGN KEY (source_node_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- Extracted table: IOCs and entities extracted from node content
CREATE TABLE IF NOT EXISTS extracted (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    type TEXT NOT NULL,
    value TEXT NOT NULL,
    raw_value TEXT NOT NULL,
    canonical_value TEXT,
    author TEXT DEFAULT 'Anonymous',
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- Threat actor aliases reference table
CREATE TABLE IF NOT EXISTS threat_actor_aliases (
    alias TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL
);

-- Rejected suggestions table: tracks suggestions user has dismissed
CREATE TABLE IF NOT EXISTS rejected_suggestions (
    id TEXT PRIMARY KEY,
    extracted_id TEXT NOT NULL,
    suggestion_type TEXT NOT NULL,  -- 'refang', 'type_change'
    suggested_value TEXT,           -- the suggested new value
    suggested_type TEXT,            -- the suggested new type (for type_change)
    created_at TEXT NOT NULL,
    FOREIGN KEY (extracted_id) REFERENCES extracted(id) ON DELETE CASCADE
);

-- Index for rejected suggestions lookup
CREATE INDEX IF NOT EXISTS idx_rejected_extracted ON rejected_suggestions(extracted_id);

-- Rejected tag suggestions table: tracks tag suggestions user has dismissed
CREATE TABLE IF NOT EXISTS rejected_tag_suggestions (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    tag_value TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- Index for rejected tag suggestions lookup
CREATE INDEX IF NOT EXISTS idx_rejected_tag_node ON rejected_tag_suggestions(node_id);

-- Authentication tables (v2+)
-- Users table: stores user accounts
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_login_at TEXT,
    sso_provider TEXT,
    sso_subject_id TEXT UNIQUE
);

-- Sessions table: tracks active user sessions
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_accessed_at TEXT,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Audit log table: tracks all modifications
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    user_id TEXT,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    details TEXT
);

-- User preferences table: stores per-user settings
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    display_name_override TEXT,
    avatar_url TEXT,
    theme_preference TEXT DEFAULT 'system',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for auth tables
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_username ON audit_log(username);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- FTS5 virtual tables for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    content,
    content='nodes',
    content_rowid='rowid'
);

CREATE VIRTUAL TABLE IF NOT EXISTS tags_fts USING fts5(
    name,
    value,
    content='tags',
    content_rowid='rowid'
);

CREATE VIRTUAL TABLE IF NOT EXISTS extracted_fts USING fts5(
    value,
    canonical_value,
    content='extracted',
    content_rowid='rowid'
);

-- Triggers to keep FTS tables in sync
CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, content) VALUES (new.rowid, new.content);
END;

CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, content) VALUES('delete', old.rowid, old.content);
END;

CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, content) VALUES('delete', old.rowid, old.content);
    INSERT INTO nodes_fts(rowid, content) VALUES (new.rowid, new.content);
END;

CREATE TRIGGER IF NOT EXISTS tags_ai AFTER INSERT ON tags BEGIN
    INSERT INTO tags_fts(rowid, name, value) VALUES (new.rowid, new.name, new.value);
END;

CREATE TRIGGER IF NOT EXISTS tags_ad AFTER DELETE ON tags BEGIN
    INSERT INTO tags_fts(tags_fts, rowid, name, value) VALUES('delete', old.rowid, old.name, old.value);
END;

CREATE TRIGGER IF NOT EXISTS tags_au AFTER UPDATE ON tags BEGIN
    INSERT INTO tags_fts(tags_fts, rowid, name, value) VALUES('delete', old.rowid, old.name, old.value);
    INSERT INTO tags_fts(rowid, name, value) VALUES (new.rowid, new.name, new.value);
END;

CREATE TRIGGER IF NOT EXISTS extracted_ai AFTER INSERT ON extracted BEGIN
    INSERT INTO extracted_fts(rowid, value, canonical_value) VALUES (new.rowid, new.value, new.canonical_value);
END;

CREATE TRIGGER IF NOT EXISTS extracted_ad AFTER DELETE ON extracted BEGIN
    INSERT INTO extracted_fts(extracted_fts, rowid, value, canonical_value) VALUES('delete', old.rowid, old.value, old.canonical_value);
END;

CREATE TRIGGER IF NOT EXISTS extracted_au AFTER UPDATE ON extracted BEGIN
    INSERT INTO extracted_fts(extracted_fts, rowid, value, canonical_value) VALUES('delete', old.rowid, old.value, old.canonical_value);
    INSERT INTO extracted_fts(rowid, value, canonical_value) VALUES (new.rowid, new.value, new.canonical_value);
END;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_tags_node_id ON tags(node_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
CREATE INDEX IF NOT EXISTS idx_tags_value ON tags(value);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_extracted_node_id ON extracted(node_id);
CREATE INDEX IF NOT EXISTS idx_extracted_type ON extracted(type);
CREATE INDEX IF NOT EXISTS idx_extracted_value ON extracted(value);
CREATE INDEX IF NOT EXISTS idx_extracted_canonical ON extracted(canonical_value);
"""


async def get_db_version(db: aiosqlite.Connection) -> int:
    """Get current database version."""
    try:
        cursor = await db.execute("SELECT MAX(version) as version FROM db_version")
        row = await cursor.fetchone()
        return row["version"] if row and row["version"] is not None else 0
    except aiosqlite.OperationalError:
        # db_version table doesn't exist yet
        return 0


async def set_db_version(db: aiosqlite.Connection, version: int) -> None:
    """Set database version."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT OR REPLACE INTO db_version (version, applied_at) VALUES (?, ?)",
        (version, now)
    )
    await db.commit()


async def migrate_v1_to_v2(db: aiosqlite.Connection) -> None:
    """
    Migrate from v1 (no author columns, no auth tables) to v2 (with author columns and auth tables).
    
    Adds:
    - author columns to nodes, tags, extracted, and edges tables
    - created_at column to tags table
    - Auth tables: users, sessions, audit_log, user_preferences
    """
    logger.info("Migrating database from v1 to v2...")
    
    # Add author columns to existing tables
    cursor = await db.execute("PRAGMA table_info(nodes)")
    columns = {row[1] for row in await cursor.fetchall()}
    
    if 'author' not in columns:
        logger.info("Adding author column to nodes table...")
        await db.execute("ALTER TABLE nodes ADD COLUMN author TEXT DEFAULT 'Anonymous'")
        logger.info("✓ Added author to nodes")
    
    # Tags table
    cursor = await db.execute("PRAGMA table_info(tags)")
    columns = {row[1] for row in await cursor.fetchall()}
    
    if 'author' not in columns:
        logger.info("Adding author column to tags table...")
        await db.execute("ALTER TABLE tags ADD COLUMN author TEXT DEFAULT 'Anonymous'")
        logger.info("✓ Added author to tags")
    
    if 'created_at' not in columns:
        logger.info("Adding created_at column to tags table...")
        await db.execute("ALTER TABLE tags ADD COLUMN created_at TEXT")
        logger.info("✓ Added created_at to tags")
    
    # Extracted table
    cursor = await db.execute("PRAGMA table_info(extracted)")
    columns = {row[1] for row in await cursor.fetchall()}
    
    if 'author' not in columns:
        logger.info("Adding author column to extracted table...")
        await db.execute("ALTER TABLE extracted ADD COLUMN author TEXT DEFAULT 'Anonymous'")
        logger.info("✓ Added author to extracted")
    
    # Edges table
    cursor = await db.execute("PRAGMA table_info(edges)")
    columns = {row[1] for row in await cursor.fetchall()}
    
    if 'author' not in columns:
        logger.info("Adding author column to edges table...")
        await db.execute("ALTER TABLE edges ADD COLUMN author TEXT DEFAULT 'Anonymous'")
        logger.info("✓ Added author to edges")
    
    # Create or update auth tables
    logger.info("Setting up authentication tables...")
    
    # Always check and fix audit_log table schema
    try:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
        audit_exists = await cursor.fetchone()
        
        if audit_exists:
            # Check if audit_log has the correct schema
            cursor = await db.execute("PRAGMA table_info(audit_log)")
            columns = {row[1] for row in await cursor.fetchall()}
            
            required_columns = {'id', 'timestamp', 'user_id', 'username', 'action', 'resource_type', 'resource_id', 'details'}
            missing_columns = required_columns - columns
            
            if missing_columns:
                logger.info(f"Audit log missing columns: {missing_columns}. Recreating table...")
                # Backup existing data if any
                cursor = await db.execute("SELECT COUNT(*) FROM audit_log")
                count = (await cursor.fetchone())[0]
                
                if count > 0:
                    logger.info(f"Backing up {count} existing audit log entries...")
                    # Create temporary backup
                    await db.execute("CREATE TABLE audit_log_backup AS SELECT * FROM audit_log")
                
                # Drop and recreate with correct schema
                await db.execute("DROP TABLE IF EXISTS audit_log")
                await db.execute("""
                    CREATE TABLE audit_log (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        user_id TEXT,
                        username TEXT NOT NULL,
                        action TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        resource_id TEXT,
                        details TEXT
                    )
                """)
                
                # Try to migrate old data if backup exists
                try:
                    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log_backup'")
                    if await cursor.fetchone():
                        # Migrate what we can from old schema
                        await db.execute("""
                            INSERT INTO audit_log (id, timestamp, user_id, username, action, resource_type, resource_id, details)
                            SELECT 
                                id,
                                COALESCE(timestamp, datetime('now')),
                                NULL as user_id,
                                username,
                                action,
                                resource_type,
                                resource_id,
                                details
                            FROM audit_log_backup
                        """)
                        await db.execute("DROP TABLE audit_log_backup")
                        logger.info("✓ Migrated existing audit log entries")
                except Exception as e:
                    logger.warning(f"Could not migrate old audit logs: {e}")
                
                logger.info("✓ Recreated audit_log table with correct schema")
    except Exception as e:
        logger.warning(f"Error checking audit_log: {e}")
    
    # Create auth tables with full schema
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_login_at TEXT,
            sso_provider TEXT,
            sso_subject_id TEXT UNIQUE
        );
        
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_accessed_at TEXT,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            user_id TEXT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            details TEXT
        );
        
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id TEXT PRIMARY KEY,
            display_name_override TEXT,
            avatar_url TEXT,
            theme_preference TEXT DEFAULT 'system',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
        CREATE INDEX IF NOT EXISTS idx_audit_log_username ON audit_log(username);
        CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);
    """)
    logger.info("✓ Authentication tables ready")
    
    await db.commit()
    logger.info("✓ Migration v1 → v2 complete")


async def apply_migrations(db: aiosqlite.Connection) -> None:
    """Apply all pending database migrations."""
    current_version = await get_db_version(db)
    logger.info(f"Current database version: {current_version}")
    
    if current_version < CURRENT_DB_VERSION:
        logger.info(f"Database needs migration: v{current_version} → v{CURRENT_DB_VERSION}")
        
        # Apply migrations in order
        if current_version < 1:
            # v0 → v1: Initial schema (handled by init_database)
            await set_db_version(db, 1)
            logger.info("✓ Set initial version to v1")
        
        if current_version < 2:
            # v1 → v2: Add author columns
            await migrate_v1_to_v2(db)
            await set_db_version(db, 2)
        
        logger.info(f"✓ Database migrated to v{CURRENT_DB_VERSION}")
    else:
        logger.info("Database is up to date")


async def init_database() -> None:
    """Initialize the database with schema and apply migrations."""
    db_path = settings.database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        
        # Create base schema (idempotent)
        await db.executescript(SCHEMA)
        await db.commit()
        
        # Apply any pending migrations
        await apply_migrations(db)


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Get a database connection."""
    db = await aiosqlite.connect(settings.database_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
