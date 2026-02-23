"""Search routes."""

from __future__ import annotations

import html as html_mod

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from contentsifter.config import load_client
from contentsifter.search.filters import SearchFilters
from contentsifter.search.keyword import keyword_search
from contentsifter.web.app import templates
from contentsifter.web.deps import get_db
from contentsifter.web.utils import simple_md_to_html

router = APIRouter()


@router.get("/{slug}/search")
async def search_page(request: Request, slug: str):
    """Search page with live search."""
    client = load_client(slug)
    return templates.TemplateResponse("pages/search.html", {
        "request": request,
        "current_client": client,
        "active_page": "search",
    })


@router.get("/{slug}/search/results")
async def search_results(
    request: Request,
    slug: str,
    q: str = Query(""),
    category: str = Query(""),
):
    """Return search results as HTML fragment (htmx)."""
    client = load_client(slug)

    if not q.strip():
        return HTMLResponse('<p class="text-sm text-zinc-400 py-4">Type to search...</p>')

    filters = SearchFilters()
    if category:
        filters.categories = [category]

    with get_db(client) as db:
        try:
            results = keyword_search(db, q, filters)
        except Exception:
            results = []

    if not results:
        return HTMLResponse(
            f'<p class="text-sm text-zinc-400 py-4">No results for &ldquo;{q}&rdquo;</p>'
        )

    # Build display-ready results with snippet
    display_results = []
    for r in results:
        content = r.get("content", "")
        snippet = content[:200] + "..." if len(content) > 200 else content
        display_results.append({
            **r,
            "snippet": snippet,
        })

    return templates.TemplateResponse("pages/_search_results.html", {
        "request": request,
        "results": display_results,
        "query": q,
        "slug": slug,
    })


@router.get("/{slug}/search/detail/{extraction_id}")
async def search_detail(request: Request, slug: str, extraction_id: int):
    """Return full extraction detail as HTML fragment (htmx expand-in-place)."""
    client = load_client(slug)

    with get_db(client) as db:
        row = db.conn.execute(
            """SELECT e.id, e.category, e.title, e.content, e.raw_quote,
                      e.speaker, e.quality_score, e.context_note,
                      c.title as call_title, c.call_date, c.call_type
               FROM extractions e
               JOIN calls c ON c.id = e.call_id
               WHERE e.id = ?""",
            (extraction_id,),
        ).fetchone()

        if not row:
            return HTMLResponse(
                '<p class="text-sm text-zinc-400 py-2">Extraction not found.</p>'
            )

        # Get all tags
        tag_rows = db.conn.execute(
            """SELECT t.name FROM tags t
               JOIN extraction_tags et ON t.id = et.tag_id
               WHERE et.extraction_id = ?""",
            (extraction_id,),
        ).fetchall()

    tags = [t["name"] for t in tag_rows]
    content_html = simple_md_to_html(row["content"]) if row["content"] else ""
    raw_quote = html_mod.escape(row["raw_quote"]) if row["raw_quote"] else ""

    # Build metadata line
    meta_parts = []
    if row["speaker"]:
        meta_parts.append(f'<span class="font-medium">{html_mod.escape(row["speaker"])}</span>')
    if row["call_title"]:
        meta_parts.append(html_mod.escape(row["call_title"]))
    if row["call_type"]:
        meta_parts.append(html_mod.escape(row["call_type"]))
    meta_html = " &middot; ".join(meta_parts)

    # Tags
    tags_html = " ".join(
        f'<span class="tag-pill">{html_mod.escape(t)}</span>'
        for t in tags
    )

    # Build detail HTML
    sections = []

    # Divider
    sections.append('<hr class="my-4 border-zinc-100">')

    # Full content
    if content_html:
        sections.append(f"""
        <div class="mb-4">
          <p class="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">Full Content</p>
          <div class="prose-custom">{content_html}</div>
        </div>
        """)

    # Raw quote
    if raw_quote:
        sections.append(f"""
        <div class="mb-4">
          <p class="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">Original Quote</p>
          <blockquote class="prose-blockquote">
            <p>{raw_quote}</p>
          </blockquote>
        </div>
        """)

    # Context note
    if row["context_note"]:
        sections.append(f"""
        <div class="mb-4">
          <p class="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">Context</p>
          <p class="text-sm text-zinc-600">{html_mod.escape(row["context_note"])}</p>
        </div>
        """)

    # Metadata footer
    if meta_html or tags_html:
        sections.append(f"""
        <div class="flex flex-wrap items-center gap-3 pt-3 border-t border-zinc-100">
          <span class="text-xs text-zinc-500">{meta_html}</span>
          {f'<div class="flex flex-wrap gap-1.5">{tags_html}</div>' if tags_html else ''}
        </div>
        """)

    return HTMLResponse("\n".join(sections))
