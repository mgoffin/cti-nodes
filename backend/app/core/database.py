"""SQLite database connection and initialization."""

import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .config import settings


# SQL schema for creating tables
SCHEMA = """
-- Nodes table: stores the main content
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Tags table: key-value pairs associated with nodes
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    name TEXT NOT NULL,
    value TEXT NOT NULL,
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
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- Threat actor aliases reference table
CREATE TABLE IF NOT EXISTS threat_actor_aliases (
    alias TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL
);

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


async def init_database() -> None:
    """Initialize the database with schema."""
    db_path = settings.database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Get a database connection."""
    db = await aiosqlite.connect(settings.database_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
