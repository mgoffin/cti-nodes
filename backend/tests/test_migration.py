"""Test script for database migration."""

import asyncio
import aiosqlite
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

async def verify_migration():
    """Verify the migration created all expected tables and columns."""
    db_path = Path(__file__).parent.parent / "data" / "nodes.db"

    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("   Create some test data first before running migration")
        return False

    print(f"📁 Checking database: {db_path}")
    print()

    success = True

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # Check for new tables
        print("🔍 Checking for new tables...")
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row["name"] for row in await cursor.fetchall()]

        expected_tables = {
            "nodes", "tags", "edges", "extracted",
            "users", "sessions", "audit_log", "user_preferences",
            "nodes_fts", "tags_fts", "extracted_fts"
        }

        for table in expected_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - MISSING")
                success = False
        print()

        # Check for author columns in existing tables
        print("🔍 Checking for author columns...")
        tables_needing_author = ["nodes", "tags", "extracted", "edges"]

        for table in tables_needing_author:
            cursor = await db.execute(f"PRAGMA table_info({table})")
            columns = [row["name"] for row in await cursor.fetchall()]

            if "author" in columns:
                print(f"  ✅ {table}.author")
            else:
                print(f"  ❌ {table}.author - MISSING")
                success = False
        print()

        # Check for created_at column in tags
        print("🔍 Checking for tags.created_at...")
        cursor = await db.execute("PRAGMA table_info(tags)")
        columns = [row["name"] for row in await cursor.fetchall()]

        if "created_at" in columns:
            print(f"  ✅ tags.created_at")
        else:
            print(f"  ❌ tags.created_at - MISSING")
            success = False
        print()

        # Check indexes
        print("🔍 Checking for indexes...")
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        )
        indexes = [row["name"] for row in await cursor.fetchall()]

        expected_indexes = [
            "idx_nodes_author",
            "idx_tags_author",
            "idx_extracted_author",
            "idx_edges_author",
            "idx_users_username",
            "idx_users_email",
            "idx_sessions_user_id",
            "idx_sessions_refresh_token_hash",
            "idx_audit_timestamp",
            "idx_audit_user",
            "idx_audit_resource",
        ]

        found_indexes = 0
        for index in expected_indexes:
            if any(index in idx for idx in indexes):
                print(f"  ✅ {index}")
                found_indexes += 1
            else:
                print(f"  ⚠️  {index} - not found (may be expected if migration not run)")
        print()

        # Check table counts
        print("📊 Table statistics...")
        for table in ["nodes", "tags", "edges", "extracted"]:
            if table in tables:
                cursor = await db.execute(f"SELECT COUNT(*) as count FROM {table}")
                row = await cursor.fetchone()
                print(f"  {table}: {row['count']} rows")
        print()

        # Check users table structure
        if "users" in tables:
            print("👤 Users table structure:")
            cursor = await db.execute("PRAGMA table_info(users)")
            columns = await cursor.fetchall()
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")
            print()

        # Check sessions table structure
        if "sessions" in tables:
            print("🔑 Sessions table structure:")
            cursor = await db.execute("PRAGMA table_info(sessions)")
            columns = await cursor.fetchall()
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")
            print()

    print()
    if success:
        print("✅ Migration verification PASSED")
        print("   All expected tables and columns are present")
    else:
        print("❌ Migration verification FAILED")
        print("   Some tables or columns are missing - run migrate_v2_users.py")

    return success


if __name__ == "__main__":
    result = asyncio.run(verify_migration())
    sys.exit(0 if result else 1)
