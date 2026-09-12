"""
CodeBridge V1 - Embedded SQLite Database Layer
Uses aiosqlite with WAL mode enabled for concurrent, low-latency queries.
"""
import aiosqlite
from typing import AsyncGenerator
from backend.app.config import DB_PATH, DEFAULT_PROVIDER

INIT_SCRIPTS = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_path TEXT NOT NULL,
    executive_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    language TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    plain_summary TEXT,
    business_domain TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id);
CREATE INDEX IF NOT EXISTS idx_files_domain ON files(business_domain);

CREATE TABLE IF NOT EXISTS symbols (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    name TEXT NOT NULL,
    symbol_type TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    signature TEXT,
    parameters_json TEXT,
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);

CREATE TABLE IF NOT EXISTS translations_cache (
    id TEXT PRIMARY KEY,
    cache_key TEXT UNIQUE NOT NULL,
    summary_text TEXT NOT NULL,
    inputs_text TEXT NOT NULL,
    outputs_text TEXT NOT NULL,
    business_rule_text TEXT NOT NULL,
    mermaid_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_key ON translations_cache(cache_key);

CREATE TABLE IF NOT EXISTS provider_settings (
    id TEXT PRIMARY KEY DEFAULT 'active_config',
    provider_type TEXT NOT NULL,
    base_url TEXT NOT NULL,
    api_key TEXT,
    model_name TEXT NOT NULL,
    temperature REAL DEFAULT 0.2,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async generator yielding a database connection with row factory enabled."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db() -> None:
    """Initializes the database tables and populates default provider settings if empty."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(INIT_SCRIPTS)

        # Check if active_config already exists
        cursor = await db.execute("SELECT id FROM provider_settings WHERE id = 'active_config'")
        row = await cursor.fetchone()
        if not row:
            await db.execute(
                """
                INSERT INTO provider_settings (id, provider_type, base_url, api_key, model_name, temperature)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "active_config",
                    DEFAULT_PROVIDER.provider_type,
                    DEFAULT_PROVIDER.base_url,
                    DEFAULT_PROVIDER.api_key,
                    DEFAULT_PROVIDER.model_name,
                    DEFAULT_PROVIDER.temperature,
                ),
            )
            await db.commit()
