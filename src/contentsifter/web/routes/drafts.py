"""Saved drafts browsing routes."""

from __future__ import annotations

import html as html_mod
import re
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from contentsifter.config import load_client
from contentsifter.web.app import templates

router = APIRouter()


def _parse_draft(path: Path) -> dict:
    """Parse a saved draft markdown file into metadata + content."""
    text = path.read_text()
    lines = text.split("\n")

    title = path.stem
    format_type = ""
    body = text

    # Extract title from first H1
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()

    # Extract format from *Format: ...* line
    for line in lines[1:6]:
        m = re.match(r"\*Format:\s*(.+?)(?:\s*\|.*)?\*", line)
        if m:
            format_type = m.group(1).strip()
            break

    # Body is everything after the --- separator
    separator_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "---" and i > 0:
            separator_idx = i
            break
    if separator_idx is not None:
        body = "\n".join(lines[separator_idx + 1 :]).strip()
    else:
        body = "\n".join(lines[2:]).strip()

    # Try to extract date from filename (2026-02-23-mon-... or linkedin-20260222-...)
    date_str = ""
    fname = path.stem
    m = re.match(r"(\d{4}-\d{2}-\d{2})", fname)
    if m:
        date_str = m.group(1)
    else:
        m = re.search(r"(\d{4})(\d{2})(\d{2})", fname)
        if m:
            date_str = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    return {
        "filename": path.name,
        "title": title,
        "format_type": format_type,
        "date": date_str,
        "body": body,
        "snippet": body[:200].replace("\n", " ").strip(),
        "mtime": path.stat().st_mtime,
    }


@router.get("/{slug}/drafts")
async def drafts_page(request: Request, slug: str):
    """Saved drafts browsing page."""
    client = load_client(slug)
    drafts_dir = client.drafts_dir

    drafts = []
    if drafts_dir.exists():
        for p in sorted(drafts_dir.glob("*.md"), reverse=True):
            drafts.append(_parse_draft(p))

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

    info = _parse_draft(path)
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
