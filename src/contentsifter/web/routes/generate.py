"""Content generation routes."""

from __future__ import annotations

import html as html_mod
import logging
from datetime import datetime

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse

import os

from contentsifter.config import load_client
from contentsifter.planning.voiceprint import load_voice_print
from contentsifter.search.filters import SearchFilters
from contentsifter.search.keyword import keyword_search
from contentsifter.web.app import templates
from contentsifter.web.deps import get_api_key, get_db, has_api_key

log = logging.getLogger(__name__)

router = APIRouter()

FORMAT_OPTIONS = [
    ("linkedin", "LinkedIn Post"),
    ("newsletter", "Newsletter"),
    ("thread", "Twitter/X Thread"),
    ("playbook", "Playbook"),
    ("video-script", "Video Script"),
    ("carousel", "LinkedIn Carousel"),
    ("email-welcome", "Welcome Email"),
    ("email-weekly", "Weekly Email"),
    ("email-sales", "Sales Email"),
]


@router.get("/{slug}/generate")
async def generate_page(request: Request, slug: str):
    """Content generation page."""
    client = load_client(slug)
    has_voice_print = client.voice_print_path.exists()

    return templates.TemplateResponse("pages/generate.html", {
        "request": request,
        "current_client": client,
        "active_page": "generate",
        "format_options": FORMAT_OPTIONS,
        "has_api_key": has_api_key(client),
        "has_voice_print": has_voice_print,
    })


@router.post("/{slug}/generate/draft")
async def generate_draft_endpoint(
    request: Request,
    slug: str,
    topic: str = Form(...),
    format_type: str = Form("linkedin"),
    category: str = Form(""),
    limit: int = Form(10),
):
    """Generate a content draft. Always uses voice print and content gates."""
    client = load_client(slug)

    key = get_api_key(client)
    if not key:
        return HTMLResponse(
            '<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200">'
            "Set an API key in client settings or ANTHROPIC_API_KEY env var"
            "</div>"
        )

    # Search for source material
    filters = SearchFilters(limit=limit)
    if category:
        filters.categories = [category]

    with get_db(client) as db:
        try:
            results = keyword_search(db, topic, filters)
        except Exception:
            results = []

    if not results:
        return HTMLResponse(
            f'<div class="rounded-lg px-4 py-3 text-sm bg-amber-50 text-amber-800 border border-amber-200">'
            f'No source material found for &ldquo;{html_mod.escape(topic)}&rdquo;. '
            f"Try a different topic or upload more content."
            f"</div>"
        )

    # Always load voice print when available
    voice_print = load_voice_print(client.voice_print_path)

    try:
        from contentsifter.generate.drafts import generate_draft
        from contentsifter.llm.client import create_client as create_llm_client

        # Set client-specific key for LLM
        old_key = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = key
        try:
            llm = create_llm_client(mode="api")
            draft = generate_draft(
                results=results,
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

        # Find the display name for the format
        format_label = dict(FORMAT_OPTIONS).get(format_type, format_type)

        return templates.TemplateResponse("pages/_draft_result.html", {
            "request": request,
            "current_client": client,
            "draft": draft,
            "draft_escaped": html_mod.escape(draft),
            "topic": topic,
            "format_type": format_type,
            "format_label": format_label,
            "source_count": len(results),
        })

    except Exception as e:
        log.exception("Draft generation failed")
        return HTMLResponse(
            f'<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200">'
            f"Generation failed: {type(e).__name__}: {e}"
            f"</div>"
        )


@router.post("/{slug}/generate/from-extraction/{extraction_id}")
async def generate_from_extraction(
    request: Request,
    slug: str,
    extraction_id: int,
    format_type: str = Form("linkedin"),
):
    """Generate a content draft from a single extraction."""
    client = load_client(slug)

    key = get_api_key(client)
    if not key:
        return HTMLResponse(
            '<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200">'
            "Set an API key in client settings or ANTHROPIC_API_KEY env var"
            "</div>"
        )

    # Load the extraction directly
    with get_db(client) as db:
        row = db.conn.execute(
            """SELECT e.id, e.category, e.title, e.content, e.raw_quote,
                      e.speaker, e.quality_score
               FROM extractions e WHERE e.id = ?""",
            (extraction_id,),
        ).fetchone()

        if not row:
            return HTMLResponse(
                '<div class="rounded-lg px-4 py-3 text-sm bg-amber-50 text-amber-800 border border-amber-200">'
                "Extraction not found."
                "</div>"
            )

        # Get tags
        tag_rows = db.conn.execute(
            "SELECT t.name FROM tags t JOIN extraction_tags et ON t.id = et.tag_id WHERE et.extraction_id = ?",
            (extraction_id,),
        ).fetchall()

    results = [{
        "title": row["title"],
        "category": row["category"],
        "content": row["content"],
        "raw_quote": row["raw_quote"] or "",
        "tags": [t["name"] for t in tag_rows],
    }]
    topic = row["title"]

    voice_print = load_voice_print(client.voice_print_path)

    try:
        from contentsifter.generate.drafts import generate_draft
        from contentsifter.llm.client import create_client as create_llm_client

        old_key = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = key
        try:
            llm = create_llm_client(mode="api")
            draft = generate_draft(
                results=results,
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

        format_label = dict(FORMAT_OPTIONS).get(format_type, format_type)

        return templates.TemplateResponse("pages/_draft_result.html", {
            "request": request,
            "current_client": client,
            "draft": draft,
            "draft_escaped": html_mod.escape(draft),
            "topic": topic,
            "format_type": format_type,
            "format_label": format_label,
            "source_count": 1,
        })

    except Exception as e:
        log.exception("Draft generation from extraction %d failed", extraction_id)
        return HTMLResponse(
            f'<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200">'
            f"Generation failed: {type(e).__name__}: {e}"
            f"</div>"
        )


@router.post("/{slug}/generate/save")
async def save_draft(
    request: Request,
    slug: str,
    content: str = Form(...),
    topic: str = Form(""),
    format_type: str = Form("linkedin"),
):
    """Save a generated draft to disk."""
    client = load_client(slug)
    client.drafts_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{format_type}-{timestamp}.md"
    path = client.drafts_dir / filename

    path.write_text(f"# {topic}\n\n*Format: {format_type}*\n\n---\n\n{content}\n")

    return HTMLResponse(
        f'<div class="rounded-lg px-4 py-3 text-sm bg-emerald-50 text-emerald-800 border border-emerald-200 mt-3 flex items-center gap-2" data-flash>'
        f'<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>'
        f"Saved to {filename}"
        f"</div>"
    )


@router.get("/{slug}/generate/source-preview")
async def source_preview(
    request: Request,
    slug: str,
    q: str = Query(""),
    category: str = Query(""),
):
    """Preview available source material count."""
    client = load_client(slug)

    if not q.strip():
        return HTMLResponse("")

    filters = SearchFilters(limit=20)
    if category:
        filters.categories = [category]

    with get_db(client) as db:
        try:
            results = keyword_search(db, q, filters)
        except Exception:
            results = []

    count = len(results)
    if count == 0:
        return HTMLResponse(
            f'<span class="text-amber-600">No source material found for &ldquo;{html_mod.escape(q)}&rdquo;</span>'
        )

    cats = {}
    for r in results:
        cat = r.get("category", "other")
        cats[cat] = cats.get(cat, 0) + 1
    cat_text = ", ".join(f"{cnt} {cat}" for cat, cnt in cats.items())

    return HTMLResponse(
        f'<span class="text-emerald-600">{count} source items found ({cat_text})</span>'
    )
