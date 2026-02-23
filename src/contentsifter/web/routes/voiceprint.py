"""Voice print generation and management routes."""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from contentsifter.config import load_client
from contentsifter.planning.voiceprint import (
    analyze_voice,
    get_coach_turn_stats,
    get_content_item_stats,
    load_voice_print,
    save_voice_print,
)
from contentsifter.web.app import templates
from contentsifter.web.deps import get_db
from contentsifter.web.utils import simple_md_to_html

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{slug}/voice-print")
async def voice_print_page(request: Request, slug: str):
    """Voice print management page."""
    client = load_client(slug)

    vp_exists = client.voice_print_path.exists()
    vp_modified = None
    vp_size = 0
    if vp_exists:
        stat = client.voice_print_path.stat()
        vp_modified = datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %Y %H:%M")
        vp_size = stat.st_size

    with get_db(client) as db:
        coach_stats = get_coach_turn_stats(db, client.name, client.email)
        content_stats = get_content_item_stats(db)

    total_source = coach_stats["turn_count"] + content_stats["item_count"]

    return templates.TemplateResponse("pages/voice_print.html", {
        "request": request,
        "current_client": client,
        "active_page": "voice-print",
        "vp_exists": vp_exists,
        "vp_modified": vp_modified,
        "vp_size": vp_size,
        "coach_stats": coach_stats,
        "content_stats": content_stats,
        "total_source": total_source,
        "has_api_key": request.app.state.has_api_key,
    })


@router.post("/{slug}/voice-print/generate")
async def generate_voice_print(request: Request, slug: str):
    """Generate or regenerate the voice print."""
    client = load_client(slug)

    if not request.app.state.has_api_key:
        return HTMLResponse(
            '<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200">'
            "Set ANTHROPIC_API_KEY to generate voice prints"
            "</div>"
        )

    try:
        from contentsifter.llm.client import create_client as create_llm_client

        llm = create_llm_client(mode="api")

        with get_db(client) as db:
            content = analyze_voice(
                db, llm, coach_name=client.name, coach_email=client.email
            )

        save_voice_print(content, client.voice_print_path)

        return HTMLResponse(f"""
        <div class="rounded-lg px-4 py-3 text-sm bg-emerald-50 text-emerald-800 border border-emerald-200 mb-4" data-flash>
          Voice print generated successfully
        </div>
        <div hx-get="/{slug}/voice-print/preview" hx-trigger="load" hx-swap="innerHTML"></div>
        """)

    except Exception as e:
        log.exception("Voice print generation failed")
        return HTMLResponse(
            f'<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200">'
            f"Generation failed: {type(e).__name__}: {e}"
            f"</div>"
        )


@router.get("/{slug}/voice-print/preview")
async def voice_print_preview(request: Request, slug: str):
    """Return voice print content as rendered HTML fragment."""
    client = load_client(slug)
    content = load_voice_print(client.voice_print_path)

    if not content:
        return HTMLResponse(
            '<p class="text-sm text-zinc-400 py-4">No voice print generated yet.</p>'
        )

    html = simple_md_to_html(content)
    return HTMLResponse(f"""
    <div class="prose prose-sm max-w-none text-zinc-700 leading-relaxed">
      {html}
    </div>
    """)
