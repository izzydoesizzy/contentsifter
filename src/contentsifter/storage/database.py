"""SQLite database schema and connection management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- Individual coaching calls parsed from merged markdown files
CREATE TABLE IF NOT EXISTS calls (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file       TEXT NOT NULL,
    original_filename TEXT NOT NULL UNIQUE,
    fathom_id         TEXT,
    title             TEXT NOT NULL,
    call_date         TEXT NOT NULL,
    call_type         TEXT NOT NULL,
    participant_count INTEGER DEFAULT 0,
    turn_count        INTEGER DEFAULT 0,
    duration_seconds  INTEGER,
    raw_text_hash     TEXT,
    created_at        TEXT DEFAULT (datetime('now')),
    updated_at        TEXT DEFAULT (datetime('now'))
);

-- Participants in each call
CREATE TABLE IF NOT EXISTS participants (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id       INTEGER NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    display_name  TEXT,
    email         TEXT,
    is_coach      INTEGER DEFAULT 0,
    UNIQUE(call_id, display_name, email)
);

-- Individual speaker turns
CREATE TABLE IF NOT EXISTS speaker_turns (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id           INTEGER NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    turn_index        INTEGER NOT NULL,
    speaker_name      TEXT NOT NULL,
    speaker_email     TEXT,
    text              TEXT NOT NULL,
    timestamp         TEXT NOT NULL,
    timestamp_seconds INTEGER,
    UNIQUE(call_id, turn_index)
);

-- Topic segments identified by Claude
CREATE TABLE IF NOT EXISTS topic_chunks (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id          INTEGER NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    chunk_index      INTEGER NOT NULL,
    topic_title      TEXT NOT NULL,
    topic_summary    TEXT,
    start_turn_index INTEGER NOT NULL,
    end_turn_index   INTEGER NOT NULL,
    start_timestamp  TEXT,
    end_timestamp    TEXT,
    primary_speaker  TEXT,
    created_at       TEXT DEFAULT (datetime('now')),
    UNIQUE(call_id, chunk_index)
);

-- Extracted content items
CREATE TABLE IF NOT EXISTS extractions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id       INTEGER NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    chunk_id      INTEGER REFERENCES topic_chunks(id) ON DELETE SET NULL,
    category      TEXT NOT NULL,
    title         TEXT NOT NULL,
    content       TEXT NOT NULL,
    raw_quote     TEXT,
    speaker       TEXT,
    context_note  TEXT,
    quality_score INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now'))
);

-- Tags
CREATE TABLE IF NOT EXISTS tags (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    category TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS extraction_tags (
    extraction_id INTEGER NOT NULL REFERENCES extractions(id) ON DELETE CASCADE,
    tag_id        INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    confidence    REAL DEFAULT 1.0,
    PRIMARY KEY (extraction_id, tag_id)
);

-- Full-text search on extractions
CREATE VIRTUAL TABLE IF NOT EXISTS extractions_fts USING fts5(
    title,
    content,
    raw_quote,
    context_note,
    content=extractions,
    content_rowid=id,
    tokenize='porter unicode61'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS extractions_ai AFTER INSERT ON extractions BEGIN
    INSERT INTO extractions_fts(rowid, title, content, raw_quote, context_note)
    VALUES (new.id, new.title, new.content, new.raw_quote, new.context_note);
END;

CREATE TRIGGER IF NOT EXISTS extractions_ad AFTER DELETE ON extractions BEGIN
    INSERT INTO extractions_fts(extractions_fts, rowid, title, content, raw_quote, context_note)
    VALUES ('delete', old.id, old.title, old.content, old.raw_quote, old.context_note);
END;

CREATE TRIGGER IF NOT EXISTS extractions_au AFTER UPDATE ON extractions BEGIN
    INSERT INTO extractions_fts(extractions_fts, rowid, title, content, raw_quote, context_note)
    VALUES ('delete', old.id, old.title, old.content, old.raw_quote, old.context_note);
    INSERT INTO extractions_fts(rowid, title, content, raw_quote, context_note)
    VALUES (new.id, new.title, new.content, new.raw_quote, new.context_note);
END;

-- Full-text search on raw speaker turns
CREATE VIRTUAL TABLE IF NOT EXISTS speaker_turns_fts USING fts5(
    text,
    speaker_name,
    content=speaker_turns,
    content_rowid=id,
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS speaker_turns_ai AFTER INSERT ON speaker_turns BEGIN
    INSERT INTO speaker_turns_fts(rowid, text, speaker_name)
    VALUES (new.id, new.text, new.speaker_name);
END;

-- Processing state tracking
CREATE TABLE IF NOT EXISTS processing_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id        INTEGER NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    stage          TEXT NOT NULL,
    status         TEXT NOT NULL,
    error_message  TEXT,
    started_at     TEXT,
    completed_at   TEXT,
    api_tokens_used INTEGER DEFAULT 0,
    UNIQUE(call_id, stage)
);

-- Ingested content items (LinkedIn posts, emails, newsletters, blog posts, etc.)
CREATE TABLE IF NOT EXISTS content_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file    TEXT,
    content_type   TEXT NOT NULL,
    title          TEXT,
    text           TEXT NOT NULL,
    author         TEXT,
    date           TEXT,
    metadata_json  TEXT,
    char_count     INTEGER,
    is_extracted   INTEGER DEFAULT 0,
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS content_items_fts USING fts5(
    title,
    text,
    content=content_items,
    content_rowid=id,
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS content_items_ai AFTER INSERT ON content_items BEGIN
    INSERT INTO content_items_fts(rowid, title, text)
    VALUES (new.id, new.title, new.text);
END;

CREATE TRIGGER IF NOT EXISTS content_items_ad AFTER DELETE ON content_items BEGIN
    INSERT INTO content_items_fts(content_items_fts, rowid, title, text)
    VALUES ('delete', old.id, old.title, old.text);
END;

CREATE TRIGGER IF NOT EXISTS content_items_au AFTER UPDATE ON content_items BEGIN
    INSERT INTO content_items_fts(content_items_fts, rowid, title, text)
    VALUES ('delete', old.id, old.title, old.text);
    INSERT INTO content_items_fts(rowid, title, text)
    VALUES (new.id, new.title, new.text);
END;

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_content_items_type ON content_items(content_type);
CREATE INDEX IF NOT EXISTS idx_content_items_extracted ON content_items(is_extracted);
CREATE INDEX IF NOT EXISTS idx_calls_date ON calls(call_date);
CREATE INDEX IF NOT EXISTS idx_calls_type ON calls(call_type);
CREATE INDEX IF NOT EXISTS idx_speaker_turns_call ON speaker_turns(call_id);
CREATE INDEX IF NOT EXISTS idx_topic_chunks_call ON topic_chunks(call_id);
CREATE INDEX IF NOT EXISTS idx_extractions_call ON extractions(call_id);
CREATE INDEX IF NOT EXISTS idx_extractions_category ON extractions(category);
CREATE INDEX IF NOT EXISTS idx_extractions_chunk ON extractions(chunk_id);
CREATE INDEX IF NOT EXISTS idx_extraction_tags_tag ON extraction_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_participants_call ON participants(call_id);
CREATE INDEX IF NOT EXISTS idx_processing_log_status ON processing_log(status);
"""


class Database:
    """SQLite database connection manager."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def initialize(self):
        """Create all tables if they don't exist."""
        self.conn.executescript(SCHEMA_SQL)
        # Set schema version if not present
        row = self.conn.execute(
            "SELECT version FROM schema_version LIMIT 1"
        ).fetchone()
        if row is None:
            self.conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (SCHEMA_VERSION,),
            )
        self.conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, *args):
        self.close()
