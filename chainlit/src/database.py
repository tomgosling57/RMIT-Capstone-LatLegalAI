"""
LatMatrix Database Layer - SQLite schema and data layer configuration.

Provides Chainlit's SQLAlchemyDataLayer connection configuration.
The database schema and admin user are created by
``verify_db_schema.py --migrate`` (run in the Docker entrypoint),
not at import time.
"""

import os

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

from .storage import LocalStorageClient

# Database path — configure via env var for different environments.
_CHAINLIT_DB_PATH = os.environ.get("CHAINLIT_DB_PATH", "./data/chainlit.db")

# Upload storage path — configure via env var; defaults to /app/data/uploads.
_CHAINLIT_UPLOAD_PATH = os.environ.get("CHAINLIT_UPLOAD_PATH", "/app/data/uploads")

# SQL schema for Chainlit's SQLAlchemyDataLayer.
# The data layer uses raw SQL and does NOT auto-create tables.
# This constant is consumed by chainlit/src/scripts/verify_db_schema.py.
_CHAINLIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    "id" TEXT PRIMARY KEY,
    "identifier" TEXT NOT NULL UNIQUE,
    "createdAt" TEXT NOT NULL,
    "metadata" TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS threads (
    "id" TEXT PRIMARY KEY,
    "createdAt" TEXT NOT NULL DEFAULT (datetime('now')),
    "name" TEXT,
    "userId" TEXT,
    "userIdentifier" TEXT,
    "tags" TEXT,
    "metadata" TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS steps (
    "id" TEXT PRIMARY KEY,
    "name" TEXT,
    "type" TEXT,
    "threadId" TEXT,
    "parentId" TEXT,
    "streaming" INTEGER DEFAULT 0,
    "waitForAnswer" INTEGER DEFAULT 0,
    "isError" INTEGER DEFAULT 0,
    "metadata" TEXT DEFAULT '{}',
    "tags" TEXT,
    "input" TEXT,
    "output" TEXT,
    "createdAt" TEXT,
    "start" TEXT,
    "end" TEXT,
    "showInput" TEXT,
    "language" TEXT,
    "generation" TEXT DEFAULT '{}',
    "defaultOpen" INTEGER DEFAULT 0,
    "autoCollapse" INTEGER DEFAULT 0,
    "command" TEXT,
    "modes" TEXT,
    "icon" TEXT
);

CREATE TABLE IF NOT EXISTS feedbacks (
    "id" TEXT PRIMARY KEY,
    "forId" TEXT,
    "value" INTEGER,
    "comment" TEXT
);

CREATE TABLE IF NOT EXISTS elements (
    "id" TEXT PRIMARY KEY,
    "threadId" TEXT,
    "type" TEXT,
    "chainlitKey" TEXT,
    "url" TEXT,
    "objectKey" TEXT,
    "name" TEXT,
    "display" TEXT,
    "size" TEXT,
    "language" TEXT,
    "autoPlay" INTEGER DEFAULT 0,
    "playerConfig" TEXT,
    "page" INTEGER,
    "props" TEXT DEFAULT '{}',
    "mime" TEXT,
    "forId" TEXT
);
"""


@cl.data_layer
def get_data_layer() -> SQLAlchemyDataLayer:
    """Configure the Chainlit data layer to persist conversations in SQLite."""
    db_url = f"sqlite+aiosqlite:///{_CHAINLIT_DB_PATH}"
    storage_provider = LocalStorageClient(
        storage_path=_CHAINLIT_UPLOAD_PATH,
        base_url="/chat/uploads",
    )
    return SQLAlchemyDataLayer(conninfo=db_url, storage_provider=storage_provider)
