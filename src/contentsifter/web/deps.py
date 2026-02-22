"""Dependency injection for web routes."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from contentsifter.config import ClientConfig, load_client
from contentsifter.storage.database import Database
from contentsifter.storage.repository import Repository


def get_client(slug: str | None = None) -> ClientConfig:
    """Load client config by slug (or default)."""
    return load_client(slug)


@contextmanager
def get_db(client: ClientConfig):
    """Open a database connection for a client, ensuring it's closed."""
    db_path = client.db_path
    if not db_path.exists():
        # Create fresh DB with schema
        with Database(db_path) as db:
            yield db
        return
    with Database(db_path) as db:
        yield db


def get_repo(db: Database) -> Repository:
    """Create a repository for database operations."""
    return Repository(db)


def content_summary(db: Database, client: ClientConfig) -> dict:
    """Gather content summary for a client. Mirrors cli.py:_content_summary."""
    summary = {
        "content_items": 0,
        "content_by_type": {},
        "total_chars": 0,
        "extractions": 0,
        "extractions_by_cat": {},
        "calls": 0,
        "has_voice_print": client.voice_print_path.exists(),
        "has_questionnaire": (client.content_dir / "interview-guide.md").exists(),
    }

    try:
        rows = db.conn.execute(
            "SELECT content_type, COUNT(*) as cnt, COALESCE(SUM(char_count), 0) as chars "
            "FROM content_items GROUP BY content_type"
        ).fetchall()
        for r in rows:
            summary["content_by_type"][r["content_type"]] = r["cnt"]
            summary["content_items"] += r["cnt"]
            summary["total_chars"] += r["chars"]
    except Exception:
        pass

    try:
        rows = db.conn.execute(
            "SELECT category, COUNT(*) as cnt FROM extractions GROUP BY category"
        ).fetchall()
        for r in rows:
            summary["extractions_by_cat"][r["category"]] = r["cnt"]
            summary["extractions"] += r["cnt"]
    except Exception:
        pass

    try:
        row = db.conn.execute("SELECT COUNT(*) as cnt FROM calls").fetchone()
        summary["calls"] = row["cnt"]
    except Exception:
        pass

    return summary
