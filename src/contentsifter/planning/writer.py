"""File writing utilities for content planning output."""

from __future__ import annotations

from pathlib import Path

from contentsifter.config import (
    CALENDAR_DIR,
    CONTENT_DIR,
    DRAFTS_DIR,
    NEWSLETTER_TEMPLATES_DIR,
    TEMPLATES_DIR,
)


def ensure_content_dirs() -> None:
    """Create the content output directory structure."""
    for d in [CONTENT_DIR, TEMPLATES_DIR, NEWSLETTER_TEMPLATES_DIR, CALENDAR_DIR, DRAFTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def write_markdown(path: Path, content: str, force: bool = False) -> bool:
    """Write markdown content to a file.

    Returns True if the file was written, False if skipped (already exists).
    """
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True
