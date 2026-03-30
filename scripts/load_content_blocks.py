#!/usr/bin/env python3
"""Load extracted content blocks from JSON staging files into the SQLite database."""

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "contentsifter.db"
STAGING_DIRS = [
    PROJECT_ROOT / "data" / "staging" / "reference",
    PROJECT_ROOT / "data" / "staging" / "transcripts",
]

VALID_CATEGORIES = {
    "qa", "playbook", "story", "testimonial", "coaching_exchange",
    "tip", "mindset", "sales_copy", "template", "lesson",
}

VALID_TAGS = {
    "linkedin", "networking", "resume", "interviews", "cover_letter",
    "salary_negotiation", "mindset", "confidence", "personal_branding",
    "career_transition", "job_search_strategy", "follow_up",
    "company_research", "recruiter", "informational_interview",
    "remote_work", "portfolio", "references", "onboarding",
    "rejection_handling", "time_management", "ai_tools", "volunteer",
    "entrepreneurship", "freelancing",
}


def get_or_create_tag(conn: sqlite3.Connection, tag_name: str) -> int | None:
    """Get tag ID, creating it if needed. Returns None for invalid tags."""
    if tag_name not in VALID_TAGS:
        return None
    conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
    row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
    return row[0] if row else None


def insert_block(conn: sqlite3.Connection, block: dict) -> int | None:
    """Insert a single content block. Returns the new row ID."""
    category = block.get("category", "")
    if category not in VALID_CATEGORIES:
        print(f"  Skipping block with invalid category: {category!r}")
        return None

    full_text = block.get("full_text", "")
    if not full_text or len(full_text.strip()) < 20:
        return None

    context_json = json.dumps(block.get("context", {})) if block.get("context") else None

    cursor = conn.execute(
        """INSERT INTO content_blocks
           (source_type, call_id, chunk_id, content_item_id,
            category, title, full_text, summary, raw_quote,
            speaker, quality_score, word_count, context_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            block.get("source_type", "unknown"),
            block.get("call_id"),
            block.get("chunk_id"),
            block.get("content_item_id"),
            category,
            block.get("title", "Untitled"),
            full_text,
            block.get("summary"),
            block.get("raw_quote"),
            block.get("speaker"),
            block.get("quality_score", 3),
            block.get("word_count", len(full_text.split())),
            context_json,
        ),
    )
    block_id = cursor.lastrowid

    # Link tags
    for tag_name in block.get("tags", []):
        tag_id = get_or_create_tag(conn, tag_name)
        if tag_id:
            conn.execute(
                "INSERT OR IGNORE INTO content_block_tags (content_block_id, tag_id) VALUES (?, ?)",
                (block_id, tag_id),
            )

    return block_id


def load_json_file(conn: sqlite3.Connection, filepath: Path) -> int:
    """Load all content blocks from a single JSON file. Returns count inserted."""
    with open(filepath) as f:
        data = json.load(f)

    blocks = data if isinstance(data, list) else data.get("blocks", data.get("content_blocks", []))
    if not isinstance(blocks, list):
        print(f"  Warning: {filepath.name} has unexpected format, skipping")
        return 0

    count = 0
    for block in blocks:
        if insert_block(conn, block):
            count += 1

    return count


def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    total = 0
    categories: dict[str, int] = {}

    for staging_dir in STAGING_DIRS:
        if not staging_dir.exists():
            continue
        json_files = sorted(staging_dir.glob("*.json"))
        if not json_files:
            continue

        print(f"\nLoading from {staging_dir.relative_to(PROJECT_ROOT)}/")
        for filepath in json_files:
            count = load_json_file(conn, filepath)
            total += count
            print(f"  {filepath.name}: {count} blocks")

    conn.commit()

    # Report category breakdown
    rows = conn.execute(
        "SELECT category, COUNT(*) FROM content_blocks GROUP BY category ORDER BY COUNT(*) DESC"
    ).fetchall()
    print(f"\n{'='*40}")
    print(f"Total content blocks loaded: {total}")
    print(f"{'='*40}")
    for cat, cnt in rows:
        print(f"  {cat}: {cnt}")

    conn.close()


if __name__ == "__main__":
    main()
