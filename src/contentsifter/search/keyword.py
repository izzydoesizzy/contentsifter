"""FTS5-based keyword search for ContentSifter."""

from __future__ import annotations

from contentsifter.search.filters import SearchFilters
from contentsifter.storage.database import Database


def keyword_search(
    db: Database,
    query: str,
    filters: SearchFilters | None = None,
) -> list[dict]:
    """Full-text search using SQLite FTS5.

    Supports:
    - Simple queries: "linkedin profile"
    - Phrase matching: '"salary negotiation"'
    - Boolean: "resume AND interview"
    - Prefix: "network*"
    """
    if filters is None:
        filters = SearchFilters()

    filter_clause, filter_params = filters.to_sql_clauses()
    where = f"AND {filter_clause}" if filter_clause else ""

    sql = f"""
        SELECT
            e.id,
            e.category,
            e.title,
            e.content,
            e.raw_quote,
            e.speaker,
            e.quality_score,
            c.title as call_title,
            c.call_date,
            c.call_type,
            rank
        FROM extractions_fts fts
        JOIN extractions e ON e.id = fts.rowid
        JOIN calls c ON c.id = e.call_id
        WHERE extractions_fts MATCH ?
        {where}
        ORDER BY rank
        LIMIT ?
    """

    params = [query] + filter_params + [filters.limit]
    rows = db.conn.execute(sql, params).fetchall()

    results = []
    for row in rows:
        # Get tags for this extraction
        tag_rows = db.conn.execute(
            """SELECT t.name FROM tags t
               JOIN extraction_tags et ON t.id = et.tag_id
               WHERE et.extraction_id = ?""",
            (row["id"],),
        ).fetchall()

        results.append({
            "id": row["id"],
            "category": row["category"],
            "title": row["title"],
            "content": row["content"],
            "raw_quote": row["raw_quote"],
            "speaker": row["speaker"],
            "quality_score": row["quality_score"],
            "tags": [t["name"] for t in tag_rows],
            "call_title": row["call_title"],
            "call_date": row["call_date"],
            "call_type": row["call_type"],
        })

    return results


def search_raw_turns(
    db: Database,
    query: str,
    limit: int = 20,
) -> list[dict]:
    """Search raw speaker turns for a query."""
    sql = """
        SELECT
            st.id,
            st.speaker_name,
            st.text,
            st.timestamp,
            c.title as call_title,
            c.call_date
        FROM speaker_turns_fts fts
        JOIN speaker_turns st ON st.id = fts.rowid
        JOIN calls c ON c.id = st.call_id
        WHERE speaker_turns_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """
    rows = db.conn.execute(sql, (query, limit)).fetchall()
    return [dict(r) for r in rows]
