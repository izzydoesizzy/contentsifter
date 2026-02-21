"""CRUD operations for the ContentSifter database."""

from __future__ import annotations

import hashlib
from datetime import datetime

from contentsifter.storage.database import Database
from contentsifter.storage.models import (
    CallMetadata,
    Extraction,
    SpeakerTurn,
    TopicChunk,
)


class Repository:
    """Database operations for ContentSifter."""

    def __init__(self, db: Database):
        self.db = db

    # ── Calls ──────────────────────────────────────────────────────

    def call_exists(self, original_filename: str) -> bool:
        row = self.db.conn.execute(
            "SELECT 1 FROM calls WHERE original_filename = ?",
            (original_filename,),
        ).fetchone()
        return row is not None

    def insert_call(
        self, metadata: CallMetadata, turns: list[SpeakerTurn]
    ) -> int:
        """Insert a call with its participants and speaker turns."""
        raw_text = "\n".join(t.text for t in turns)
        text_hash = hashlib.sha256(raw_text.encode()).hexdigest()

        duration = turns[-1].timestamp_seconds if turns else 0

        cursor = self.db.conn.execute(
            """INSERT INTO calls
               (source_file, original_filename, fathom_id, title, call_date,
                call_type, participant_count, turn_count, duration_seconds, raw_text_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                metadata.source_file,
                metadata.original_filename,
                metadata.fathom_id,
                metadata.title,
                metadata.call_date,
                metadata.call_type,
                len(metadata.participants),
                len(turns),
                duration,
                text_hash,
            ),
        )
        call_id = cursor.lastrowid

        # Insert participants
        for p in metadata.participants:
            self.db.conn.execute(
                """INSERT OR IGNORE INTO participants
                   (call_id, display_name, email, is_coach)
                   VALUES (?, ?, ?, ?)""",
                (call_id, p.display_name, p.email, int(p.is_coach)),
            )

        # Insert speaker turns
        for turn in turns:
            self.db.conn.execute(
                """INSERT INTO speaker_turns
                   (call_id, turn_index, speaker_name, speaker_email,
                    text, timestamp, timestamp_seconds)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    call_id,
                    turn.turn_index,
                    turn.speaker_name,
                    turn.speaker_email,
                    turn.text,
                    turn.timestamp,
                    turn.timestamp_seconds,
                ),
            )

        # Mark as parsed
        self.db.conn.execute(
            """INSERT OR REPLACE INTO processing_log
               (call_id, stage, status, completed_at)
               VALUES (?, 'parsed', 'completed', ?)""",
            (call_id, datetime.now().isoformat()),
        )

        self.db.conn.commit()
        return call_id

    def get_call_count(self) -> int:
        row = self.db.conn.execute("SELECT COUNT(*) FROM calls").fetchone()
        return row[0]

    def get_all_calls(self) -> list[dict]:
        rows = self.db.conn.execute(
            "SELECT * FROM calls ORDER BY call_date"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Topic Chunks ───────────────────────────────────────────────

    def insert_topic_chunks(
        self, call_id: int, chunks: list[TopicChunk]
    ) -> list[int]:
        """Insert topic chunks for a call."""
        chunk_ids = []
        for chunk in chunks:
            cursor = self.db.conn.execute(
                """INSERT INTO topic_chunks
                   (call_id, chunk_index, topic_title, topic_summary,
                    start_turn_index, end_turn_index, start_timestamp,
                    end_timestamp, primary_speaker)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    call_id,
                    chunk.chunk_index,
                    chunk.topic_title,
                    chunk.topic_summary,
                    chunk.start_turn_index,
                    chunk.end_turn_index,
                    chunk.start_timestamp,
                    chunk.end_timestamp,
                    chunk.primary_speaker,
                ),
            )
            chunk_ids.append(cursor.lastrowid)

        # Mark as chunked
        self.db.conn.execute(
            """INSERT OR REPLACE INTO processing_log
               (call_id, stage, status, completed_at)
               VALUES (?, 'chunked', 'completed', ?)""",
            (call_id, datetime.now().isoformat()),
        )

        self.db.conn.commit()
        return chunk_ids

    # ── Extractions ────────────────────────────────────────────────

    def insert_extractions(
        self, call_id: int, chunk_id: int | None, extractions: list[Extraction]
    ) -> list[int]:
        """Insert extracted content items with their tags."""
        extraction_ids = []
        for ext in extractions:
            cursor = self.db.conn.execute(
                """INSERT INTO extractions
                   (call_id, chunk_id, category, title, content,
                    raw_quote, speaker, context_note, quality_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    call_id,
                    chunk_id,
                    ext.category,
                    ext.title,
                    ext.content,
                    ext.raw_quote,
                    ext.speaker,
                    ext.context_note,
                    ext.quality_score,
                ),
            )
            extraction_id = cursor.lastrowid
            extraction_ids.append(extraction_id)

            # Insert tags
            for tag_name in ext.tags:
                # Ensure tag exists
                self.db.conn.execute(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)",
                    (tag_name,),
                )
                tag_row = self.db.conn.execute(
                    "SELECT id FROM tags WHERE name = ?", (tag_name,)
                ).fetchone()
                if tag_row:
                    self.db.conn.execute(
                        """INSERT OR IGNORE INTO extraction_tags
                           (extraction_id, tag_id) VALUES (?, ?)""",
                        (extraction_id, tag_row[0]),
                    )

        self.db.conn.commit()
        return extraction_ids

    def mark_extracted(self, call_id: int):
        """Mark a call as fully extracted."""
        self.db.conn.execute(
            """INSERT OR REPLACE INTO processing_log
               (call_id, stage, status, completed_at)
               VALUES (?, 'extracted', 'completed', ?)""",
            (call_id, datetime.now().isoformat()),
        )
        self.db.conn.commit()

    # ── Processing Progress ────────────────────────────────────────

    def get_calls_needing_stage(self, stage: str) -> list[int]:
        """Get call IDs that haven't completed the given stage."""
        prev_stages = {"chunked": "parsed", "extracted": "chunked"}
        prev_stage = prev_stages.get(stage)

        if prev_stage:
            # Must have completed previous stage but not this one
            rows = self.db.conn.execute(
                """SELECT c.id FROM calls c
                   JOIN processing_log pl ON c.id = pl.call_id
                     AND pl.stage = ? AND pl.status = 'completed'
                   LEFT JOIN processing_log pl2 ON c.id = pl2.call_id
                     AND pl2.stage = ? AND pl2.status = 'completed'
                   WHERE pl2.id IS NULL
                   ORDER BY c.call_date""",
                (prev_stage, stage),
            ).fetchall()
        else:
            # For 'parsed': calls not yet in DB are handled by the parser
            rows = []
        return [r[0] for r in rows]

    def get_progress_summary(self) -> dict:
        """Get counts per stage and status."""
        total = self.get_call_count()
        summary = {"total_calls": total, "stages": {}}

        for stage in ["parsed", "chunked", "extracted"]:
            row = self.db.conn.execute(
                """SELECT COUNT(*) FROM processing_log
                   WHERE stage = ? AND status = 'completed'""",
                (stage,),
            ).fetchone()
            summary["stages"][stage] = row[0]

        # Extraction counts by category
        rows = self.db.conn.execute(
            """SELECT category, COUNT(*) FROM extractions GROUP BY category"""
        ).fetchall()
        summary["extractions"] = {r[0]: r[1] for r in rows}
        summary["total_extractions"] = sum(summary["extractions"].values())

        return summary

    # ── Speaker Turns ──────────────────────────────────────────────

    def get_turns_for_call(self, call_id: int) -> list[dict]:
        rows = self.db.conn.execute(
            """SELECT * FROM speaker_turns
               WHERE call_id = ? ORDER BY turn_index""",
            (call_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_turns_for_range(
        self, call_id: int, start_index: int, end_index: int
    ) -> list[dict]:
        rows = self.db.conn.execute(
            """SELECT * FROM speaker_turns
               WHERE call_id = ? AND turn_index >= ? AND turn_index <= ?
               ORDER BY turn_index""",
            (call_id, start_index, end_index),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_call_by_id(self, call_id: int) -> dict | None:
        row = self.db.conn.execute(
            "SELECT * FROM calls WHERE id = ?", (call_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Topic Chunks ───────────────────────────────────────────────

    def get_chunks_for_call(self, call_id: int) -> list[dict]:
        rows = self.db.conn.execute(
            """SELECT * FROM topic_chunks
               WHERE call_id = ? ORDER BY chunk_index""",
            (call_id,),
        ).fetchall()
        return [dict(r) for r in rows]
