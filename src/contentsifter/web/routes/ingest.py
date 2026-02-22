"""File upload and ingestion routes."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from contentsifter.config import load_client
from contentsifter.ingest.autoformat import auto_format_content, needs_formatting
from contentsifter.ingest.reader import CLI_TYPE_MAP, ingest_path
from contentsifter.web.app import templates
from contentsifter.web.deps import get_db

router = APIRouter()


@router.get("/{slug}/ingest")
async def ingest_page(request: Request, slug: str):
    """File upload page with drag/drop zone."""
    client = load_client(slug)

    # Get recent content items
    recent = []
    with get_db(client) as db:
        try:
            rows = db.conn.execute(
                "SELECT id, title, content_type, char_count, created_at "
                "FROM content_items ORDER BY created_at DESC LIMIT 20"
            ).fetchall()
            recent = [dict(r) for r in rows]
        except Exception:
            pass

    return templates.TemplateResponse("pages/ingest.html", {
        "request": request,
        "current_client": client,
        "active_page": "ingest",
        "recent_items": recent,
        "has_api_key": request.app.state.has_api_key,
    })


@router.post("/{slug}/ingest/upload")
async def upload_file(
    request: Request,
    slug: str,
    file: UploadFile = File(...),
    content_type: str = Form("other"),
    auto_format: bool = Form(False),
):
    """Handle file upload, optionally auto-formatting with Claude."""
    client = load_client(slug)
    resolved_type = CLI_TYPE_MAP.get(content_type, content_type)

    # Read uploaded file
    content = await file.read()
    try:
        raw_text = content.decode("utf-8")
    except UnicodeDecodeError:
        return HTMLResponse(
            '<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200">'
            'Unable to read file. Please upload a text file (.md or .txt).</div>'
        )

    formatted = False

    # Auto-format if requested and needed
    if auto_format and request.app.state.has_api_key:
        if needs_formatting(raw_text, resolved_type):
            try:
                from contentsifter.llm.client import create_client as create_llm_client
                llm = create_llm_client("api", "claude-sonnet-4-20250514")
                raw_text = auto_format_content(raw_text, resolved_type, llm)
                formatted = True
            except Exception:
                pass  # Fall through to raw ingest

    # Write to temp file and ingest
    suffix = Path(file.filename).suffix if file.filename else ".md"
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as tmp:
        tmp.write(raw_text)
        tmp_path = Path(tmp.name)

    try:
        with get_db(client) as db:
            items = ingest_path(db, tmp_path, content_type=content_type, author=client.name)
    finally:
        tmp_path.unlink(missing_ok=True)

    count = len(items)
    badge = ' <span class="badge badge-other">AI formatted</span>' if formatted else ""

    return HTMLResponse(f"""
    <div class="rounded-lg px-4 py-3 text-sm bg-emerald-50 text-emerald-800 border border-emerald-200 mb-4" data-flash>
      Ingested {count} item{"s" if count != 1 else ""} from {file.filename or "upload"}{badge}
    </div>
    <div hx-get="/{slug}/ingest/recent" hx-trigger="load" hx-swap="innerHTML"></div>
    """)


@router.get("/{slug}/ingest/recent")
async def recent_items(request: Request, slug: str):
    """Return recent content items as HTML fragment."""
    client = load_client(slug)
    recent = []
    with get_db(client) as db:
        try:
            rows = db.conn.execute(
                "SELECT id, title, content_type, char_count, created_at "
                "FROM content_items ORDER BY created_at DESC LIMIT 20"
            ).fetchall()
            recent = [dict(r) for r in rows]
        except Exception:
            pass

    if not recent:
        return HTMLResponse('<p class="text-sm text-zinc-400 py-4">No content items yet.</p>')

    rows_html = ""
    for item in recent:
        title = item.get("title") or "Untitled"
        if len(title) > 60:
            title = title[:57] + "..."
        ct = item.get("content_type", "other")
        chars = item.get("char_count", 0)
        date = (item.get("created_at") or "")[:10]
        rows_html += f"""
        <tr class="border-t border-zinc-50 hover:bg-zinc-50 transition-colors">
          <td class="px-4 py-2.5 text-sm text-zinc-900">{title}</td>
          <td class="px-4 py-2.5"><span class="badge badge-{ct}">{ct}</span></td>
          <td class="px-4 py-2.5 text-sm text-zinc-500 text-right">{chars:,}</td>
          <td class="px-4 py-2.5 text-sm text-zinc-400">{date}</td>
        </tr>"""

    return HTMLResponse(f"""
    <table class="w-full">
      <thead>
        <tr class="border-b border-zinc-100">
          <th class="text-left text-xs font-medium text-zinc-500 uppercase tracking-wider px-4 py-2">Title</th>
          <th class="text-left text-xs font-medium text-zinc-500 uppercase tracking-wider px-4 py-2">Type</th>
          <th class="text-right text-xs font-medium text-zinc-500 uppercase tracking-wider px-4 py-2">Chars</th>
          <th class="text-left text-xs font-medium text-zinc-500 uppercase tracking-wider px-4 py-2">Date</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    """)
