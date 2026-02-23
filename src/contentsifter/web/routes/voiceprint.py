"""Voice print generation and management routes."""

from __future__ import annotations

import logging
import os
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
from contentsifter.web.deps import get_api_key, get_db, has_api_key
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
        "has_api_key": has_api_key(client),
    })


@router.post("/{slug}/voice-print/generate")
async def generate_voice_print(request: Request, slug: str):
    """Generate or regenerate the voice print."""
    client = load_client(slug)
    key = get_api_key(client)

    if not key:
        return HTMLResponse(
            '<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200">'
            "Set an API key in client settings or ANTHROPIC_API_KEY env var"
            "</div>"
        )

    try:
        from contentsifter.llm.client import create_client as create_llm_client

        # Set the key in env for the LLM client to pick up
        old_key = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = key
        try:
            llm = create_llm_client(mode="api")

            with get_db(client) as db:
                content = analyze_voice(
                    db, llm, coach_name=client.name, coach_email=client.email
                )
        finally:
            # Restore original env
            if old_key is not None:
                os.environ["ANTHROPIC_API_KEY"] = old_key
            elif "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]

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
    <div class="prose-custom max-w-none">
      {html}
    </div>
    """)
