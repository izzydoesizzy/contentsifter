"""Content planner routes — visual weekly calendar."""

from __future__ import annotations

import html as html_mod
import json
import logging
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, Response

from contentsifter.config import load_client
from contentsifter.planning.calendar import WEEKLY_SCHEDULE, select_content_for_day
from contentsifter.planning.voiceprint import load_voice_print
from contentsifter.web.app import templates
from contentsifter.web.deps import get_api_key, get_db, has_api_key
from contentsifter.web.utils import parse_draft

log = logging.getLogger(__name__)

router = APIRouter()

# Ordered schedule (Mon-Sat, skipping Sunday)
ACTIVE_DAYS = [
    (name, *info)
    for name, info in WEEKLY_SCHEDULE.items()
    if info[0] is not None
]


def _get_monday(week: str | None = None) -> datetime:
    """Get the Monday of the specified or current week."""
    if week:
        dt = datetime.strptime(week, "%Y-%m-%d")
        dt = dt - timedelta(days=dt.weekday())
        return dt
    today = datetime.now()
    return today - timedelta(days=today.weekday())


def _week_days(monday: datetime) -> list[dict]:
    """Build the list of day info dicts for the template."""
    days = []
    for i, (day_name, pillar, format_type, category, platform) in enumerate(ACTIVE_DAYS):
        days.append({
            "day_name": day_name,
            "date": (monday + timedelta(days=i if day_name != "Saturday" else 5)).strftime("%b %d"),
            "date_iso": (monday + timedelta(days=i if day_name != "Saturday" else 5)).strftime("%Y-%m-%d"),
            "pillar": pillar,
            "format_type": format_type,
            "category": category,
            "platform": platform,
        })
    return days


def _day_index(day_name: str) -> int:
    """Get the weekday offset (Mon=0 ... Sat=5)."""
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    return names.index(day_name) if day_name in names else 0


@router.get("/{slug}/planner")
async def planner_page(request: Request, slug: str, week: str = Query(None)):
    """Main planner page with weekly calendar grid."""
    client = load_client(slug)
    monday = _get_monday(week)
    week_start = monday.strftime("%Y-%m-%d")
    days = _week_days(monday)

    prev_week = (monday - timedelta(weeks=1)).strftime("%Y-%m-%d")
    next_week = (monday + timedelta(weeks=1)).strftime("%Y-%m-%d")

    # Load existing plan slots
    slots = {}
    with get_db(client) as db:
        rows = db.conn.execute(
            "SELECT * FROM calendar_plans WHERE week_start = ?", (week_start,)
        ).fetchall()
        for row in rows:
            slots[row["day_name"]] = dict(row)

    has_plan = len(slots) > 0

    # Load available drafts
    drafts = []
    if client.drafts_dir.exists():
        for p in sorted(client.drafts_dir.glob("*.md"), reverse=True):
            drafts.append(parse_draft(p))

    return templates.TemplateResponse("pages/planner.html", {
        "request": request,
        "current_client": client,
        "active_page": "planner",
        "week_start": week_start,
        "week_label": f"{monday.strftime('%b %d')} - {(monday + timedelta(days=5)).strftime('%b %d, %Y')}",
        "prev_week": prev_week,
        "next_week": next_week,
        "days": days,
        "slots": slots,
        "has_plan": has_plan,
        "has_api_key": has_api_key(client),
        "drafts": drafts,
    })


@router.post("/{slug}/planner/create-week")
async def create_week(request: Request, slug: str, week: str = Form(...)):
    """Create empty plan slots for a week."""
    client = load_client(slug)

    with get_db(client) as db:
        for day_name, pillar, format_type, category, platform in ACTIVE_DAYS:
            db.conn.execute(
                """INSERT OR IGNORE INTO calendar_plans
                   (week_start, day_name, pillar, format_type, platform, status)
                   VALUES (?, ?, ?, ?, ?, 'empty')""",
                (week, day_name, pillar, format_type, platform),
            )
        db.conn.commit()

    return HTMLResponse(
        status_code=303,
        headers={"HX-Redirect": f"/{slug}/planner?week={week}"},
    )


@router.get("/{slug}/planner/slot/{day_name}")
async def get_slot(request: Request, slug: str, day_name: str, week: str = Query(...)):
    """Return a slot card fragment."""
    client = load_client(slug)

    with get_db(client) as db:
        row = db.conn.execute(
            "SELECT * FROM calendar_plans WHERE week_start = ? AND day_name = ?",
            (week, day_name),
        ).fetchone()

    slot = dict(row) if row else None
    monday = _get_monday(week)
    day_info = None
    for d in _week_days(monday):
        if d["day_name"] == day_name:
            day_info = d
            break

    return templates.TemplateResponse("pages/_planner_card.html", {
        "request": request,
        "current_client": client,
        "slot": slot,
        "day": day_info,
        "week_start": week,
        "has_api_key": has_api_key(client),
    })


@router.put("/{slug}/planner/slot/{day_name}")
async def update_slot(
    request: Request,
    slug: str,
    day_name: str,
    week: str = Form(...),
    title: str = Form(""),
    content: str = Form(""),
    notes: str = Form(""),
    status: str = Form("draft"),
):
    """Update a slot's content/status."""
    client = load_client(slug)

    with get_db(client) as db:
        db.conn.execute(
            """UPDATE calendar_plans
               SET title = ?, content = ?, notes = ?, status = ?,
                   updated_at = datetime('now')
               WHERE week_start = ? AND day_name = ?""",
            (title, content, notes, status, week, day_name),
        )
        db.conn.commit()

    # Return the updated card
    return await get_slot(request, slug, day_name, week)


@router.post("/{slug}/planner/slot/{day_name}/generate")
async def generate_for_slot(
    request: Request,
    slug: str,
    day_name: str,
    week: str = Form(...),
):
    """Auto-select source content and generate a draft for this slot."""
    client = load_client(slug)

    key = get_api_key(client)
    if not key:
        return HTMLResponse(
            '<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200">'
            "Set an API key in client settings or ANTHROPIC_API_KEY env var"
            "</div>"
        )

    # Look up slot info
    with get_db(client) as db:
        row = db.conn.execute(
            "SELECT * FROM calendar_plans WHERE week_start = ? AND day_name = ?",
            (week, day_name),
        ).fetchone()

    if not row:
        return HTMLResponse('<div class="text-sm text-rose-600">Slot not found. Create a plan first.</div>')

    format_type = row["format_type"]

    # Find the category for this day from the schedule
    category = None
    for name, pillar, ft, cat, platform in ACTIVE_DAYS:
        if name == day_name:
            category = cat
            break

    # Select source content
    with get_db(client) as db:
        sources = select_content_for_day(db, category, used_ids=[], count=2 if day_name == "Saturday" else 1)

    if not sources:
        return HTMLResponse(
            '<div class="rounded-lg px-4 py-3 text-sm bg-amber-50 text-amber-800 border border-amber-200">'
            "No source material found for this content type."
            "</div>"
        )

    # Generate draft with voice print and gates
    voice_print = load_voice_print(client.voice_print_path)
    topic = sources[0]["title"]
    extraction_ids = [s["id"] for s in sources]

    try:
        from contentsifter.generate.drafts import generate_draft
        from contentsifter.llm.client import create_client as create_llm_client

        old_key = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = key
        try:
            llm = create_llm_client(mode="api")
            draft_text = generate_draft(
                results=sources,
                format_type=format_type,
                llm_client=llm,
                topic=topic,
                voice_print=voice_print,
            )
        finally:
            if old_key is not None:
                os.environ["ANTHROPIC_API_KEY"] = old_key
            elif "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]

        # Save to slot
        with get_db(client) as db:
            db.conn.execute(
                """UPDATE calendar_plans
                   SET title = ?, content = ?, status = 'draft',
                       extraction_ids = ?, topic = ?, updated_at = datetime('now')
                   WHERE week_start = ? AND day_name = ?""",
                (topic, draft_text, json.dumps(extraction_ids), topic, week, day_name),
            )
            db.conn.commit()

        return await get_slot(request, slug, day_name, week)

    except Exception as e:
        log.exception("Planner draft generation failed for %s", day_name)
        return HTMLResponse(
            f'<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200">'
            f"Generation failed: {type(e).__name__}: {html_mod.escape(str(e))}"
            f"</div>"
        )


@router.post("/{slug}/planner/slot/{day_name}/assign-draft")
async def assign_draft_to_slot(
    request: Request,
    slug: str,
    day_name: str,
    week: str = Form(...),
    filename: str = Form(...),
):
    """Assign a saved draft file to a calendar slot."""
    client = load_client(slug)
    path = client.drafts_dir / filename

    if not path.exists():
        return HTMLResponse('<div class="text-sm text-rose-600">Draft file not found.</div>')

    info = parse_draft(path)

    with get_db(client) as db:
        db.conn.execute(
            """UPDATE calendar_plans
               SET title = ?, content = ?, status = 'draft',
                   source_draft = ?, updated_at = datetime('now')
               WHERE week_start = ? AND day_name = ?""",
            (info["title"], info["body"], filename, week, day_name),
        )
        db.conn.commit()

    return await get_slot(request, slug, day_name, week)


@router.delete("/{slug}/planner/slot/{day_name}/clear")
async def clear_slot(
    request: Request,
    slug: str,
    day_name: str,
    week: str = Query(...),
):
    """Clear a slot back to empty."""
    client = load_client(slug)

    with get_db(client) as db:
        db.conn.execute(
            """UPDATE calendar_plans
               SET title = NULL, content = NULL, status = 'empty',
                   source_draft = NULL, extraction_ids = NULL,
                   topic = NULL, notes = NULL, updated_at = datetime('now')
               WHERE week_start = ? AND day_name = ?""",
            (week, day_name),
        )
        db.conn.commit()

    return await get_slot(request, slug, day_name, week)


@router.get("/{slug}/planner/side-panel/{day_name}")
async def side_panel(request: Request, slug: str, day_name: str, week: str = Query(...)):
    """Return the editing side panel fragment."""
    client = load_client(slug)

    with get_db(client) as db:
        row = db.conn.execute(
            "SELECT * FROM calendar_plans WHERE week_start = ? AND day_name = ?",
            (week, day_name),
        ).fetchone()

    slot = dict(row) if row else None
    monday = _get_monday(week)
    day_info = None
    for d in _week_days(monday):
        if d["day_name"] == day_name:
            day_info = d
            break

    return templates.TemplateResponse("pages/_planner_side_panel.html", {
        "request": request,
        "current_client": client,
        "slot": slot,
        "day": day_info,
        "week_start": week,
        "has_api_key": has_api_key(client),
    })


@router.get("/{slug}/planner/available-drafts")
async def available_drafts(request: Request, slug: str):
    """Return the list of saved drafts as draggable cards."""
    client = load_client(slug)

    drafts = []
    if client.drafts_dir.exists():
        for p in sorted(client.drafts_dir.glob("*.md"), reverse=True):
            drafts.append(parse_draft(p))

    return templates.TemplateResponse("pages/_planner_drafts_drawer.html", {
        "request": request,
        "current_client": client,
        "drafts": drafts,
    })


@router.get("/{slug}/planner/export-pdf")
async def export_pdf(request: Request, slug: str, week: str = Query(...)):
    """Export the weekly plan as a PDF or printable HTML."""
    client = load_client(slug)
    monday = _get_monday(week)
    week_start = monday.strftime("%Y-%m-%d")
    days = _week_days(monday)

    slots = {}
    with get_db(client) as db:
        rows = db.conn.execute(
            "SELECT * FROM calendar_plans WHERE week_start = ?", (week_start,)
        ).fetchall()
        for row in rows:
            slots[row["day_name"]] = dict(row)

    html_content = templates.get_template("pages/planner_print.html").render(
        current_client=client,
        week_start=week_start,
        week_label=f"{monday.strftime('%b %d')} - {(monday + timedelta(days=5)).strftime('%b %d, %Y')}",
        days=days,
        slots=slots,
    )

    # Try server-side PDF via WeasyPrint
    try:
        from weasyprint import HTML as WeasyHTML
        pdf_bytes = WeasyHTML(string=html_content).write_pdf()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="content-plan-{week_start}.pdf"'},
        )
    except ImportError:
        # Fallback: printable HTML
        return HTMLResponse(html_content)
