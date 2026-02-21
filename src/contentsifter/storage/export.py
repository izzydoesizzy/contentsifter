"""JSON export for ContentSifter data."""

from __future__ import annotations

import json
from pathlib import Path

from contentsifter.storage.database import Database


def export_all(db: Database, output_dir: Path):
    """Export entire database as organized JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Full export
    extractions = _get_all_extractions(db)
    _write_json(output_dir / "full_export.json", extractions)

    # By category
    by_cat_dir = output_dir / "by_category"
    by_cat_dir.mkdir(exist_ok=True)
    categories = {}
    for ext in extractions:
        cat = ext["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ext)

    for cat, items in categories.items():
        _write_json(by_cat_dir / f"{cat}.json", items)

    # By call
    by_call_dir = output_dir / "by_call"
    by_call_dir.mkdir(exist_ok=True)
    calls = {}
    for ext in extractions:
        call_key = f"{ext['call_date']}_{ext['call_id']}"
        if call_key not in calls:
            calls[call_key] = {
                "call_id": ext["call_id"],
                "call_title": ext["call_title"],
                "call_date": ext["call_date"],
                "extractions": [],
            }
        calls[call_key]["extractions"].append(ext)

    for key, data in calls.items():
        _write_json(by_call_dir / f"{key}.json", data)

    return {
        "total": len(extractions),
        "by_category": {k: len(v) for k, v in categories.items()},
        "calls_with_extractions": len(calls),
    }


def _get_all_extractions(db: Database) -> list[dict]:
    """Get all extractions with their tags and call info."""
    rows = db.conn.execute(
        """SELECT
            e.id, e.call_id, e.category, e.title, e.content,
            e.raw_quote, e.speaker, e.context_note, e.quality_score,
            c.title as call_title, c.call_date, c.call_type
        FROM extractions e
        JOIN calls c ON c.id = e.call_id
        ORDER BY c.call_date, e.id"""
    ).fetchall()

    results = []
    for row in rows:
        tag_rows = db.conn.execute(
            """SELECT t.name FROM tags t
               JOIN extraction_tags et ON t.id = et.tag_id
               WHERE et.extraction_id = ?""",
            (row["id"],),
        ).fetchall()

        results.append({
            "id": row["id"],
            "call_id": row["call_id"],
            "category": row["category"],
            "title": row["title"],
            "content": row["content"],
            "raw_quote": row["raw_quote"],
            "speaker": row["speaker"],
            "context_note": row["context_note"],
            "quality_score": row["quality_score"],
            "tags": [t["name"] for t in tag_rows],
            "call_title": row["call_title"],
            "call_date": row["call_date"],
            "call_type": row["call_type"],
        })

    return results


def _write_json(path: Path, data):
    """Write data as formatted JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
