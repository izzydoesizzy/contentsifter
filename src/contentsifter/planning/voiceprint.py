"""Voice print analyzer — builds a voice profile from speaker turns and/or content items."""

from __future__ import annotations

import logging
from pathlib import Path

from contentsifter.config import COACH_EMAIL, COACH_NAME, VOICE_PRINT_PATH
from contentsifter.llm.client import complete_with_retry
from contentsifter.planning.prompts import (
    VOICE_PASS1_SYSTEM,
    VOICE_PASS1_USER,
    VOICE_PASS2_SYSTEM,
    VOICE_PASS2_USER,
    VOICE_PASS3_SYSTEM,
    VOICE_PASS3_USER,
)
from contentsifter.storage.database import Database

log = logging.getLogger(__name__)

# Max characters per sample bucket to keep within LLM context limits
MAX_CHARS_PER_BUCKET = 8000
MAX_TOTAL_CHARS = 50000


def get_coach_turn_stats(
    db: Database,
    coach_name: str = COACH_NAME,
    coach_email: str = COACH_EMAIL,
) -> dict:
    """Get basic stats about the coach's speaker turns."""
    row = db.conn.execute(
        """SELECT COUNT(*) as turn_count,
                  COALESCE(SUM(LENGTH(text)), 0) as total_chars,
                  COUNT(DISTINCT call_id) as call_count
           FROM speaker_turns
           WHERE speaker_name LIKE ? OR speaker_email = ?""",
        (f"%{coach_name}%", coach_email),
    ).fetchone()
    return dict(row) if row else {"turn_count": 0, "total_chars": 0, "call_count": 0}


def get_content_item_stats(db: Database) -> dict:
    """Get basic stats about ingested content items."""
    try:
        row = db.conn.execute(
            """SELECT COUNT(*) as item_count,
                      COALESCE(SUM(char_count), 0) as total_chars
               FROM content_items"""
        ).fetchone()
        return dict(row) if row else {"item_count": 0, "total_chars": 0}
    except Exception:
        return {"item_count": 0, "total_chars": 0}


def get_stratified_coach_sample(
    db: Database,
    per_bucket: int = 100,
    coach_name: str = COACH_NAME,
    coach_email: str = COACH_EMAIL,
) -> dict[str, list[dict]]:
    """Get categorized samples of the coach's speech patterns.

    Returns dict with keys: openings, closings, monologues, short, medium, questions
    """
    coach_filter = f"%{coach_name}%"
    samples: dict[str, list[dict]] = {}

    # 1. Openings — first 3 coach turns per call
    rows = db.conn.execute(
        """WITH ranked AS (
             SELECT text, call_id,
                    ROW_NUMBER() OVER (PARTITION BY call_id ORDER BY turn_index) as rn
             FROM speaker_turns
             WHERE speaker_name LIKE ? OR speaker_email = ?
           )
           SELECT text FROM ranked WHERE rn <= 3
           ORDER BY RANDOM() LIMIT ?""",
        (coach_filter, coach_email, per_bucket),
    ).fetchall()
    samples["openings"] = [dict(r) for r in rows]

    # 2. Closings — last 3 coach turns per call
    rows = db.conn.execute(
        """WITH ranked AS (
             SELECT text, call_id,
                    ROW_NUMBER() OVER (PARTITION BY call_id ORDER BY turn_index DESC) as rn
             FROM speaker_turns
             WHERE speaker_name LIKE ? OR speaker_email = ?
           )
           SELECT text FROM ranked WHERE rn <= 3
           ORDER BY RANDOM() LIMIT ?""",
        (coach_filter, coach_email, per_bucket),
    ).fetchall()
    samples["closings"] = [dict(r) for r in rows]

    # 3. Long monologues — turns > 500 chars
    rows = db.conn.execute(
        """SELECT text FROM speaker_turns
           WHERE (speaker_name LIKE ? OR speaker_email = ?)
             AND LENGTH(text) > 500
           ORDER BY RANDOM() LIMIT ?""",
        (coach_filter, coach_email, per_bucket),
    ).fetchall()
    samples["monologues"] = [dict(r) for r in rows]

    # 4. Short turns — < 100 chars
    rows = db.conn.execute(
        """SELECT text FROM speaker_turns
           WHERE (speaker_name LIKE ? OR speaker_email = ?)
             AND LENGTH(text) < 100
           ORDER BY RANDOM() LIMIT ?""",
        (coach_filter, coach_email, per_bucket),
    ).fetchall()
    samples["short"] = [dict(r) for r in rows]

    # 5. Medium turns — 100-500 chars
    rows = db.conn.execute(
        """SELECT text FROM speaker_turns
           WHERE (speaker_name LIKE ? OR speaker_email = ?)
             AND LENGTH(text) BETWEEN 100 AND 500
           ORDER BY RANDOM() LIMIT ?""",
        (coach_filter, coach_email, per_bucket),
    ).fetchall()
    samples["medium"] = [dict(r) for r in rows]

    # 6. Questions — turns containing ?
    rows = db.conn.execute(
        """SELECT text FROM speaker_turns
           WHERE (speaker_name LIKE ? OR speaker_email = ?)
             AND text LIKE '%?%'
             AND LENGTH(text) > 30
           ORDER BY RANDOM() LIMIT ?""",
        (coach_filter, coach_email, per_bucket),
    ).fetchall()
    samples["questions"] = [dict(r) for r in rows]

    return samples


def get_stratified_content_sample(
    db: Database,
    per_bucket: int = 100,
) -> dict[str, list[dict]]:
    """Get categorized samples from content_items for voice analysis.

    Returns dict with keys: short_posts, medium_posts, long_form, openings, closings, questions
    """
    samples: dict[str, list[dict]] = {}

    try:
        # Short posts: < 500 chars
        rows = db.conn.execute(
            """SELECT text FROM content_items
               WHERE char_count < 500
               ORDER BY RANDOM() LIMIT ?""",
            (per_bucket,),
        ).fetchall()
        samples["short"] = [dict(r) for r in rows]

        # Medium posts: 500-2000 chars
        rows = db.conn.execute(
            """SELECT text FROM content_items
               WHERE char_count BETWEEN 500 AND 2000
               ORDER BY RANDOM() LIMIT ?""",
            (per_bucket,),
        ).fetchall()
        samples["medium"] = [dict(r) for r in rows]

        # Long form: > 2000 chars
        rows = db.conn.execute(
            """SELECT text FROM content_items
               WHERE char_count > 2000
               ORDER BY RANDOM() LIMIT ?""",
            (per_bucket,),
        ).fetchall()
        samples["monologues"] = [dict(r) for r in rows]

        # Openings: first 200 chars of each item
        rows = db.conn.execute(
            """SELECT SUBSTR(text, 1, 200) as text FROM content_items
               ORDER BY RANDOM() LIMIT ?""",
            (per_bucket,),
        ).fetchall()
        samples["openings"] = [dict(r) for r in rows]

        # Closings: last 200 chars of each item
        rows = db.conn.execute(
            """SELECT SUBSTR(text, MAX(1, char_count - 200)) as text FROM content_items
               WHERE char_count > 200
               ORDER BY RANDOM() LIMIT ?""",
            (per_bucket,),
        ).fetchall()
        samples["closings"] = [dict(r) for r in rows]

        # Questions: items containing ?
        rows = db.conn.execute(
            """SELECT text FROM content_items
               WHERE text LIKE '%?%'
               AND char_count > 30
               ORDER BY RANDOM() LIMIT ?""",
            (per_bucket,),
        ).fetchall()
        samples["questions"] = [dict(r) for r in rows]
    except Exception as e:
        log.warning("Could not sample content_items: %s", e)

    return samples


def _format_turns(turns: list[dict], max_chars: int = MAX_CHARS_PER_BUCKET) -> str:
    """Format a list of turns into text, respecting character limit."""
    lines = []
    total = 0
    for t in turns:
        text = t["text"].strip()
        if total + len(text) + 5 > max_chars:
            break
        lines.append(f"- {text}")
        total += len(text) + 5
    return "\n".join(lines)


def _merge_samples(
    turn_samples: dict[str, list[dict]],
    content_samples: dict[str, list[dict]],
) -> dict[str, list[dict]]:
    """Merge turn-based and content-based samples into one dict."""
    merged: dict[str, list[dict]] = {}
    all_keys = set(list(turn_samples.keys()) + list(content_samples.keys()))
    for key in all_keys:
        merged[key] = turn_samples.get(key, []) + content_samples.get(key, [])
    return merged


def analyze_voice(
    db: Database,
    llm_client,
    sample_per_bucket: int = 100,
    coach_name: str = COACH_NAME,
    coach_email: str = COACH_EMAIL,
) -> str:
    """Run 3-pass voice analysis and return the final voice print markdown."""
    # Gather samples from available sources
    turn_stats = get_coach_turn_stats(db, coach_name, coach_email)
    content_stats = get_content_item_stats(db)

    turn_samples: dict[str, list[dict]] = {}
    content_samples: dict[str, list[dict]] = {}

    if turn_stats["turn_count"] > 0:
        log.info(
            "Coach turn stats: %d turns, %d chars, %d calls",
            turn_stats["turn_count"], turn_stats["total_chars"], turn_stats["call_count"],
        )
        turn_samples = get_stratified_coach_sample(db, per_bucket=sample_per_bucket,
                                                    coach_name=coach_name, coach_email=coach_email)

    if content_stats["item_count"] > 0:
        log.info(
            "Content item stats: %d items, %d chars",
            content_stats["item_count"], content_stats["total_chars"],
        )
        content_samples = get_stratified_content_sample(db, per_bucket=sample_per_bucket)

    samples = _merge_samples(turn_samples, content_samples)

    log.info(
        "Combined samples: %s",
        {k: len(v) for k, v in samples.items()},
    )

    # --- Pass 1: Vocabulary and patterns ---
    all_general = samples.get("medium", []) + samples.get("short", []) + samples.get("monologues", [])
    general_text = _format_turns(all_general, max_chars=MAX_TOTAL_CHARS // 2)

    pass1_result = complete_with_retry(
        llm_client,
        system=VOICE_PASS1_SYSTEM,
        user=VOICE_PASS1_USER.format(
            turn_count=len(all_general),
            char_count=len(general_text),
            turns_text=general_text,
        ),
        max_tokens=4096,
    )
    log.info("Pass 1 complete: %d tokens", pass1_result.output_tokens)

    # --- Pass 2: Structural patterns ---
    pass2_result = complete_with_retry(
        llm_client,
        system=VOICE_PASS2_SYSTEM,
        user=VOICE_PASS2_USER.format(
            openings=_format_turns(samples.get("openings", [])),
            closings=_format_turns(samples.get("closings", [])),
            monologues=_format_turns(samples.get("monologues", [])),
            questions=_format_turns(samples.get("questions", [])),
        ),
        max_tokens=4096,
    )
    log.info("Pass 2 complete: %d tokens", pass2_result.output_tokens)

    # --- Pass 3: Synthesis ---
    pass3_result = complete_with_retry(
        llm_client,
        system=VOICE_PASS3_SYSTEM,
        user=VOICE_PASS3_USER.format(
            coach_name=coach_name,
            pass1_result=pass1_result.content,
            pass2_result=pass2_result.content,
        ),
        max_tokens=8192,
    )
    log.info("Pass 3 complete: %d tokens", pass3_result.output_tokens)

    return pass3_result.content


def save_voice_print(content: str, path: Path | None = None) -> Path:
    """Save the voice print markdown to disk."""
    out_path = path or VOICE_PRINT_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content)
    return out_path


def load_voice_print(path: Path | None = None) -> str | None:
    """Load voice print from disk, or return None if it doesn't exist."""
    vp_path = path or VOICE_PRINT_PATH
    if vp_path.exists():
        return vp_path.read_text()
    return None
