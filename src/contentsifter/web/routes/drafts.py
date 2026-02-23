"""Saved drafts browsing routes."""

from __future__ import annotations

import html as html_mod

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from contentsifter.config import load_client
from contentsifter.web.app import templates
from contentsifter.web.utils import parse_draft

router = APIRouter()


@router.get("/{slug}/drafts")
async def drafts_page(request: Request, slug: str):
    """Saved drafts browsing page."""
    client = load_client(slug)
    drafts_dir = client.drafts_dir

    drafts = []
    if drafts_dir.exists():
        for p in sorted(drafts_dir.glob("*.md"), reverse=True):
            drafts.append(parse_draft(p))

    return templates.TemplateResponse("pages/drafts.html", {
        "request": request,
        "current_client": client,
        "active_page": "drafts",
        "drafts": drafts,
    })


@router.get("/{slug}/drafts/{filename}")
async def draft_detail(request: Request, slug: str, filename: str):
    """Return full draft content as an HTML fragment (for expand-in-place)."""
    client = load_client(slug)
    path = client.drafts_dir / filename

    if not path.exists() or not path.is_file():
        return HTMLResponse('<p class="text-sm text-zinc-400">Draft not found.</p>')

    info = parse_draft(path)
    return HTMLResponse(
        f'<div class="mt-4 pt-4 border-t border-zinc-100">'
        f'<div class="text-sm text-zinc-700 whitespace-pre-wrap leading-relaxed">'
        f'{html_mod.escape(info["body"])}'
        f'</div></div>'
    )


@router.delete("/{slug}/drafts/{filename}")
async def delete_draft(request: Request, slug: str, filename: str):
    """Delete a saved draft."""
    client = load_client(slug)
    path = client.drafts_dir / filename

    if path.exists() and path.is_file():
        path.unlink()

    return HTMLResponse("")


@router.post("/{slug}/drafts/batch-delete")
async def batch_delete_drafts(request: Request, slug: str):
    """Delete multiple drafts at once."""
    client = load_client(slug)
    form = await request.form()
    filenames = form.getlist("filenames")

    deleted = 0
    for filename in filenames:
        path = client.drafts_dir / filename
        if path.exists() and path.is_file():
            path.unlink()
            deleted += 1

    # Return updated drafts list
    drafts = []
    if client.drafts_dir.exists():
        for p in sorted(client.drafts_dir.glob("*.md"), reverse=True):
            drafts.append(parse_draft(p))

    return templates.TemplateResponse("pages/_drafts_list.html", {
        "request": request,
        "current_client": client,
        "drafts": drafts,
        "flash_message": f"Deleted {deleted} draft{'s' if deleted != 1 else ''}.",
    })
