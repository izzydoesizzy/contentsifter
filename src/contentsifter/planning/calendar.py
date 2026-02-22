"""Weekly content calendar generator."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from contentsifter.config import CALENDAR_DIR
from contentsifter.generate.drafts import format_source_material, generate_draft
from contentsifter.planning.voiceprint import load_voice_print
from contentsifter.storage.database import Database

log = logging.getLogger(__name__)

# Fixed weekly schedule: day_name -> (pillar, format_type, source_category, platform)
WEEKLY_SCHEDULE = {
    "Monday": ("Story", "linkedin", "story", "LinkedIn"),
    "Tuesday": ("Playbook", "carousel", "playbook", "LinkedIn"),
    "Wednesday": ("Video", "video-script", None, "TikTok/Reels/Shorts"),
    "Thursday": ("Q&A", "linkedin", "qa", "LinkedIn"),
    "Friday": ("Testimonial", "linkedin", "testimonial", "LinkedIn"),
    "Saturday": ("Newsletter", "email-weekly", None, "Email"),
    "Sunday": (None, None, None, None),  # Rest day
}

USED_IDS_FILE = ".used-ids.json"


def _get_monday(week_of: str | None = None) -> datetime:
    """Get the Monday of the specified or next week."""
    if week_of:
        dt = datetime.strptime(week_of, "%Y-%m-%d")
        # Snap to Monday of that week
        dt = dt - timedelta(days=dt.weekday())
        return dt
    # Next Monday from today
    today = datetime.now()
    days_ahead = 7 - today.weekday()
    if days_ahead == 7:
        days_ahead = 0
    return today + timedelta(days=days_ahead)


def _load_used_ids(calendar_dir: Path) -> list[int]:
    """Load previously used extraction IDs."""
    path = calendar_dir / USED_IDS_FILE
    if path.exists():
        return json.loads(path.read_text())
    return []


def _save_used_ids(calendar_dir: Path, ids: list[int]) -> None:
    """Save used extraction IDs."""
    calendar_dir.mkdir(parents=True, exist_ok=True)
    path = calendar_dir / USED_IDS_FILE
    path.write_text(json.dumps(ids))


def select_content_for_day(
    db: Database,
    category: str | None,
    used_ids: list[int],
    tag_filter: str | None = None,
    min_quality: int = 3,
    count: int = 1,
) -> list[dict]:
    """Select unused extractions for a day's content.

    If category is None, selects from any high-quality extraction.
    """
    params: list = []
    where_clauses = [f"e.quality_score >= {min_quality}"]

    if category:
        where_clauses.append("e.category = ?")
        params.append(category)

    if used_ids:
        placeholders = ",".join("?" * len(used_ids))
        where_clauses.append(f"e.id NOT IN ({placeholders})")
        params.extend(used_ids)

    where_sql = " AND ".join(where_clauses)

    if tag_filter:
        query = f"""
            SELECT e.id, e.category, e.title, e.content, e.raw_quote,
                   e.speaker, e.quality_score, e.context_note,
                   c.call_date, c.title as call_title
            FROM extractions e
            JOIN calls c ON c.id = e.call_id
            JOIN extraction_tags et ON e.id = et.extraction_id
            JOIN tags t ON et.tag_id = t.id
            WHERE {where_sql} AND t.name = ?
            ORDER BY e.quality_score DESC, RANDOM()
            LIMIT ?
        """
        params.extend([tag_filter, count])
    else:
        query = f"""
            SELECT e.id, e.category, e.title, e.content, e.raw_quote,
                   e.speaker, e.quality_score, e.context_note,
                   c.call_date, c.title as call_title
            FROM extractions e
            JOIN calls c ON c.id = e.call_id
            WHERE {where_sql}
            ORDER BY e.quality_score DESC, RANDOM()
            LIMIT ?
        """
        params.append(count)

    rows = db.conn.execute(query, params).fetchall()
    results = []
    for row in rows:
        d = dict(row)
        # Fetch tags for this extraction
        tag_rows = db.conn.execute(
            """SELECT t.name FROM tags t
               JOIN extraction_tags et ON t.id = et.tag_id
               WHERE et.extraction_id = ?""",
            (d["id"],),
        ).fetchall()
        d["tags"] = [r["name"] for r in tag_rows]
        results.append(d)
    return results


def select_content_for_week(
    db: Database,
    topic_focus: str | None = None,
    used_ids: list[int] | None = None,
) -> dict[str, list[dict]]:
    """Select content for each day of the week."""
    if used_ids is None:
        used_ids = _load_used_ids(CALENDAR_DIR)

    selections: dict[str, list[dict]] = {}
    newly_used: list[int] = []

    for day_name, (pillar, format_type, category, platform) in WEEKLY_SCHEDULE.items():
        if pillar is None:  # Rest day
            selections[day_name] = []
            continue

        if day_name == "Saturday":
            # Newsletter: pull one from each category
            items = []
            for cat in ["playbook", "qa", "testimonial", "story"]:
                result = select_content_for_day(
                    db, cat, used_ids + newly_used, tag_filter=topic_focus, count=1
                )
                if result:
                    items.extend(result)
                    newly_used.extend(r["id"] for r in result)
            selections[day_name] = items
        elif day_name == "Wednesday":
            # Video: any high-quality extraction
            result = select_content_for_day(
                db, None, used_ids + newly_used, tag_filter=topic_focus, count=1
            )
            selections[day_name] = result
            newly_used.extend(r["id"] for r in result)
        else:
            result = select_content_for_day(
                db, category, used_ids + newly_used, tag_filter=topic_focus, count=1
            )
            selections[day_name] = result
            newly_used.extend(r["id"] for r in result)

    return selections


def format_calendar_markdown(
    monday: datetime,
    selections: dict[str, list[dict]],
    drafts: dict[str, str] | None = None,
) -> str:
    """Render the weekly calendar as markdown."""
    lines = [f"# Content Calendar: Week of {monday.strftime('%Y-%m-%d')}\n"]

    for i, (day_name, (pillar, format_type, category, platform)) in enumerate(
        WEEKLY_SCHEDULE.items()
    ):
        day_date = monday + timedelta(days=i)
        lines.append(f"## {day_name} ({day_date.strftime('%b %d')}) — {pillar or 'Rest'} Day\n")

        if pillar is None:
            lines.append("*No content scheduled.*\n")
            lines.append("---\n")
            continue

        items = selections.get(day_name, [])
        lines.append(f"**Platform:** {platform}")
        lines.append(f"**Format:** {format_type}\n")

        if not items:
            lines.append("*No matching content found in database.*\n")
            lines.append("---\n")
            continue

        for item in items:
            lines.append(f"**Source:** {item['title']}")
            lines.append(f"**From:** {item.get('call_title', 'Unknown')} ({item.get('call_date', '')})")
            lines.append(f"**Speaker:** {item.get('speaker', 'Unknown')}")
            if item.get("tags"):
                lines.append(f"**Tags:** {', '.join('#' + t for t in item['tags'])}")
            lines.append("")
            lines.append("### Source Material\n")
            lines.append(f"> {item['content']}")
            if item.get("raw_quote"):
                lines.append(f'>\n> *Direct quote:* "{item["raw_quote"]}"')
            lines.append("")

        if drafts and drafts.get(day_name):
            lines.append("### Draft\n")
            lines.append(drafts[day_name])
            lines.append("")

        lines.append("---\n")

    return "\n".join(lines)


def generate_calendar(
    db: Database,
    week_of: str | None = None,
    topic_focus: str | None = None,
    llm_client=None,
    use_llm: bool = True,
    skip_gates: bool = False,
) -> tuple[str, Path]:
    """Generate a weekly content calendar.

    Returns (markdown_content, output_path).
    """
    monday = _get_monday(week_of)
    used_ids = _load_used_ids(CALENDAR_DIR)

    selections = select_content_for_week(db, topic_focus=topic_focus, used_ids=used_ids)

    # Generate drafts if LLM is available
    drafts: dict[str, str] = {}
    if use_llm and llm_client:
        voice_print = load_voice_print()

        for day_name, (pillar, format_type, category, platform) in WEEKLY_SCHEDULE.items():
            if pillar is None or not selections.get(day_name):
                continue

            items = selections[day_name]
            log.info("Generating %s draft for %s...", format_type, day_name)

            try:
                draft = generate_draft(
                    items,
                    format_type,
                    llm_client,
                    topic=items[0]["title"],
                    voice_print=voice_print,
                    skip_gates=skip_gates,
                )
                drafts[day_name] = draft
            except Exception as e:
                log.warning("Failed to generate draft for %s: %s", day_name, e)
                drafts[day_name] = f"*Draft generation failed: {e}*"

    # Render markdown
    markdown = format_calendar_markdown(monday, selections, drafts if drafts else None)

    # Save
    CALENDAR_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CALENDAR_DIR / f"week-{monday.strftime('%Y-%m-%d')}.md"
    output_path.write_text(markdown)

    # Update used IDs
    newly_used = []
    for items in selections.values():
        newly_used.extend(item["id"] for item in items)
    if newly_used:
        _save_used_ids(CALENDAR_DIR, used_ids + newly_used)

    return markdown, output_path
