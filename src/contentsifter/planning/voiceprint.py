"""Voice print analyzer — builds a voice profile from coach's speaker turns."""

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


def get_coach_turn_stats(db: Database) -> dict:
    """Get basic stats about the coach's speaker turns."""
    row = db.conn.execute(
        """SELECT COUNT(*) as turn_count,
                  SUM(LENGTH(text)) as total_chars,
                  COUNT(DISTINCT call_id) as call_count
           FROM speaker_turns
           WHERE speaker_name LIKE ? OR speaker_email = ?""",
        (f"%{COACH_NAME}%", COACH_EMAIL),
    ).fetchone()
    return dict(row) if row else {"turn_count": 0, "total_chars": 0, "call_count": 0}


def get_stratified_coach_sample(db: Database, per_bucket: int = 100) -> dict[str, list[dict]]:
    """Get categorized samples of the coach's speech patterns.

    Returns dict with keys: openings, closings, monologues, short, medium, questions
    """
    coach_filter = f"%{COACH_NAME}%"
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
        (coach_filter, COACH_EMAIL, per_bucket),
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
        (coach_filter, COACH_EMAIL, per_bucket),
    ).fetchall()
    samples["closings"] = [dict(r) for r in rows]

    # 3. Long monologues — turns > 500 chars
    rows = db.conn.execute(
        """SELECT text FROM speaker_turns
           WHERE (speaker_name LIKE ? OR speaker_email = ?)
             AND LENGTH(text) > 500
           ORDER BY RANDOM() LIMIT ?""",
        (coach_filter, COACH_EMAIL, per_bucket),
    ).fetchall()
    samples["monologues"] = [dict(r) for r in rows]

    # 4. Short turns — < 100 chars
    rows = db.conn.execute(
        """SELECT text FROM speaker_turns
           WHERE (speaker_name LIKE ? OR speaker_email = ?)
             AND LENGTH(text) < 100
           ORDER BY RANDOM() LIMIT ?""",
        (coach_filter, COACH_EMAIL, per_bucket),
    ).fetchall()
    samples["short"] = [dict(r) for r in rows]

    # 5. Medium turns — 100-500 chars
    rows = db.conn.execute(
        """SELECT text FROM speaker_turns
           WHERE (speaker_name LIKE ? OR speaker_email = ?)
             AND LENGTH(text) BETWEEN 100 AND 500
           ORDER BY RANDOM() LIMIT ?""",
        (coach_filter, COACH_EMAIL, per_bucket),
    ).fetchall()
    samples["medium"] = [dict(r) for r in rows]

    # 6. Questions — turns containing ?
    rows = db.conn.execute(
        """SELECT text FROM speaker_turns
           WHERE (speaker_name LIKE ? OR speaker_email = ?)
             AND text LIKE '%?%'
             AND LENGTH(text) > 30
           ORDER BY RANDOM() LIMIT ?""",
        (coach_filter, COACH_EMAIL, per_bucket),
    ).fetchall()
    samples["questions"] = [dict(r) for r in rows]

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


def analyze_voice(
    db: Database,
    llm_client,
    sample_per_bucket: int = 100,
) -> str:
    """Run 3-pass voice analysis and return the final voice print markdown."""
    stats = get_coach_turn_stats(db)
    log.info(
        "Coach stats: %d turns, %d chars, %d calls",
        stats["turn_count"], stats["total_chars"], stats["call_count"],
    )

    samples = get_stratified_coach_sample(db, per_bucket=sample_per_bucket)
    log.info(
        "Samples: %s",
        {k: len(v) for k, v in samples.items()},
    )

    # --- Pass 1: Vocabulary and patterns ---
    # Combine medium + short + monologue turns for general vocabulary analysis
    all_general = samples["medium"] + samples["short"] + samples["monologues"]
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
            openings=_format_turns(samples["openings"]),
            closings=_format_turns(samples["closings"]),
            monologues=_format_turns(samples["monologues"]),
            questions=_format_turns(samples["questions"]),
        ),
        max_tokens=4096,
    )
    log.info("Pass 2 complete: %d tokens", pass2_result.output_tokens)

    # --- Pass 3: Synthesis ---
    pass3_result = complete_with_retry(
        llm_client,
        system=VOICE_PASS3_SYSTEM,
        user=VOICE_PASS3_USER.format(
            coach_name=COACH_NAME,
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
