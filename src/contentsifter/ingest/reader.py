"""Read and ingest content files into the database."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from contentsifter.ingest.formats import parse_content_file
from contentsifter.storage.database import Database

log = logging.getLogger(__name__)

# Auto-detect content type from filename prefix
FILENAME_TYPE_MAP = {
    "linkedin": "linkedin_post",
    "email": "email",
    "newsletter": "newsletter",
    "blog": "blog",
    "transcript": "transcript",
}

# CLI type flag to content_type value
CLI_TYPE_MAP = {
    "linkedin": "linkedin_post",
    "email": "email",
    "newsletter": "newsletter",
    "blog": "blog",
    "transcript": "transcript",
    "other": "other",
}


def detect_content_type(filepath: Path) -> str:
    """Auto-detect content type from filename patterns."""
    name = filepath.stem.lower()
    for prefix, content_type in FILENAME_TYPE_MAP.items():
        if name.startswith(prefix):
            return content_type
    return "other"


def ingest_path(
    db: Database,
    path: Path,
    content_type: str | None = None,
    author: str = "",
) -> list[dict]:
    """Ingest a file or directory of files into the content_items table.

    Args:
        db: Database connection
        path: File or directory to ingest
        content_type: Override content type (CLI --type flag value)
        author: Author name for all items

    Returns:
        List of inserted content item dicts.
    """
    resolved_type = CLI_TYPE_MAP.get(content_type, content_type) if content_type else None

    if path.is_dir():
        files = sorted(path.glob("**/*.md")) + sorted(path.glob("**/*.txt"))
        if not files:
            log.warning("No .md or .txt files found in %s", path)
            return []
    else:
        files = [path]

    all_items: list[dict] = []

    for filepath in files:
        file_type = resolved_type or detect_content_type(filepath)

        items = parse_content_file(filepath, file_type)

        for item in items:
            if not item.get("author"):
                item["author"] = author
            item["source_file"] = str(filepath)

            _insert_content_item(db, item)
            all_items.append(item)

    db.conn.commit()
    return all_items


def _insert_content_item(db: Database, item: dict) -> int:
    """Insert a single content item into the database."""
    import json

    text = item.get("text", "")
    metadata_json = json.dumps(item.get("metadata", {})) if item.get("metadata") else None

    cursor = db.conn.execute(
        """INSERT INTO content_items
           (source_file, content_type, title, text, author, date, metadata_json, char_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            item.get("source_file"),
            item.get("content_type", "other"),
            item.get("title"),
            text,
            item.get("author"),
            item.get("date"),
            metadata_json,
            len(text),
        ),
    )
    item["id"] = cursor.lastrowid
    return cursor.lastrowid
