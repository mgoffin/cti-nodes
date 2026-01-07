"""Database migration to add user management and author tracking.

This script migrates the database from v1 (no auth) to v2 (with auth support).

Migration steps:
1. Add author columns to existing tables (nodes, tags, extracted, edges)
2. Create new tables (users, sessions, audit_log, user_preferences)
3. Rebuild FTS indexes to include author field
4. Add necessary indexes for performance

This migration is NON-BREAKING:
- Existing data is preserved
- Platform continues to work with NODES_AUTH_ENABLED=false
- Default author value is used for existing content
"""

import asyncio
import aiosqlite
from pathlib import Path
from datetime import datetime, timezone
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


# New table schemas
USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    display_name TEXT,
    role TEXT NOT NULL DEFAULT 'analyst',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_login_at TEXT,
    sso_provider TEXT DEFAULT 'duo',
    sso_subject_id TEXT
)
"""

SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT
)
"""

AUDIT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    user_id TEXT,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    details TEXT
)
"""

USER_PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    display_name_override TEXT,
    avatar_url TEXT,
    theme_preference TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


async def migrate_v2_users(db: aiosqlite.Connection) -> None:
    """
    Run the migration to add user management schema.

    Args:
        db: Database connection
    """
    print("=" * 70)
    print("Starting migration to v2 (User Management)")
    print("=" * 70)
    print()

    # Check if migration already applied
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    )
    if await cursor.fetchone():
        print("✓ Migration already applied (users table exists)")
        return

    print("Step 1: Adding author columns to existing tables...")

    # Check if columns already exist before adding
    cursor = await db.execute("PRAGMA table_info(nodes)")
    columns = await cursor.fetchall()
    column_names = [col[1] for col in columns]

    if "author" not in column_names:
        await db.execute(
            f"ALTER TABLE nodes ADD COLUMN author TEXT NOT NULL DEFAULT '{settings.default_author}'"
        )
        print(f"  ✓ Added author column to nodes (default: '{settings.default_author}')")
    else:
        print("  • author column already exists in nodes")

    # Tags
    cursor = await db.execute("PRAGMA table_info(tags)")
    columns = await cursor.fetchall()
    column_names = [col[1] for col in columns]

    if "author" not in column_names:
        await db.execute(
            f"ALTER TABLE tags ADD COLUMN author TEXT NOT NULL DEFAULT '{settings.default_author}'"
        )
        print(f"  ✓ Added author column to tags")

    if "created_at" not in column_names:
        await db.execute("ALTER TABLE tags ADD COLUMN created_at TEXT")
        print("  ✓ Added created_at column to tags")

    if "updated_at" not in column_names:
        await db.execute("ALTER TABLE tags ADD COLUMN updated_at TEXT")
        print("  ✓ Added updated_at column to tags")

    # Extracted
    cursor = await db.execute("PRAGMA table_info(extracted)")
    columns = await cursor.fetchall()
    column_names = [col[1] for col in columns]

    if "author" not in column_names:
        await db.execute("ALTER TABLE extracted ADD COLUMN author TEXT NOT NULL DEFAULT 'System'")
        print("  ✓ Added author column to extracted (default: 'System')")

    if "created_at" not in column_names:
        await db.execute("ALTER TABLE extracted ADD COLUMN created_at TEXT")
        print("  ✓ Added created_at column to extracted")

    if "updated_at" not in column_names:
        await db.execute("ALTER TABLE extracted ADD COLUMN updated_at TEXT")
        print("  ✓ Added updated_at column to extracted")

    # Edges
    cursor = await db.execute("PRAGMA table_info(edges)")
    columns = await cursor.fetchall()
    column_names = [col[1] for col in columns]

    if "author" not in column_names:
        await db.execute("ALTER TABLE edges ADD COLUMN author TEXT NOT NULL DEFAULT 'System'")
        print("  ✓ Added author column to edges (default: 'System')")

    print()
    print("Step 2: Creating new tables...")

    await db.execute(USERS_TABLE)
    print("  ✓ Created users table")

    await db.execute(SESSIONS_TABLE)
    print("  ✓ Created sessions table")

    await db.execute(AUDIT_LOG_TABLE)
    print("  ✓ Created audit_log table")

    await db.execute(USER_PREFERENCES_TABLE)
    print("  ✓ Created user_preferences table")

    print()
    print("Step 3: Creating indexes...")

    indexes = [
        ("idx_nodes_author", "CREATE INDEX IF NOT EXISTS idx_nodes_author ON nodes(author)"),
        ("idx_users_username", "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"),
        ("idx_users_sso_subject", "CREATE INDEX IF NOT EXISTS idx_users_sso_subject ON users(sso_provider, sso_subject_id)"),
        ("idx_sessions_user_id", "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)"),
        ("idx_sessions_expires_at", "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)"),
        ("idx_audit_timestamp", "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)"),
        ("idx_audit_user", "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(username)"),
        ("idx_audit_resource", "CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id)"),
    ]

    for name, sql in indexes:
        await db.execute(sql)
        print(f"  ✓ Created index: {name}")

    print()
    print("Step 4: Rebuilding FTS index with author field...")
    print("  Note: This may take time for large databases")

    # Count existing nodes for time estimation
    cursor = await db.execute("SELECT COUNT(*) FROM nodes")
    node_count = (await cursor.fetchone())[0]
    estimated_seconds = max(1, node_count // 10000)
    print(f"  • Found {node_count} nodes")
    print(f"  • Estimated rebuild time: ~{estimated_seconds} second(s)")

    # Rebuild nodes_fts
    await db.execute("DROP TABLE IF EXISTS nodes_fts")
    await db.execute("""
        CREATE VIRTUAL TABLE nodes_fts USING fts5(
            content,
            author,
            content='nodes',
            content_rowid='rowid'
        )
    """)

    # Repopulate FTS
    await db.execute("""
        INSERT INTO nodes_fts(rowid, content, author)
        SELECT rowid, content, author FROM nodes
    """)

    print("  ✓ FTS index rebuilt successfully")

    # Commit all changes
    await db.commit()

    print()
    print("=" * 70)
    print("Migration completed successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Platform continues to work with NODES_AUTH_ENABLED=false (default)")
    print("  2. To enable authentication, configure SSO settings and set NODES_AUTH_ENABLED=true")
    print("  3. First user to log in will become Administrator")
    print()


async def main():
    """Run the migration."""
    db_path = settings.database_path

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please ensure the application has been run at least once to create the database.")
        sys.exit(1)

    print(f"Database: {db_path}")
    print(f"Default author: {settings.default_author}")
    print()

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        await migrate_v2_users(db)


if __name__ == "__main__":
    asyncio.run(main())
