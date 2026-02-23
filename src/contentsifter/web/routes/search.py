"""Search routes."""

from __future__ import annotations

import html as html_mod

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from contentsifter.config import load_client
from contentsifter.search.filters import SearchFilters
from contentsifter.search.keyword import browse_extractions, keyword_search
from contentsifter.web.app import templates
from contentsifter.web.deps import get_db, has_api_key
from contentsifter.web.routes.generate import FORMAT_OPTIONS  # used in search_detail
from contentsifter.web.utils import simple_md_to_html

router = APIRouter()


CATEGORY_LABELS = {
    "qa": "Q&A",
    "playbook": "Playbook",
    "story": "Story",
    "testimonial": "Testimonial",
}

CATEGORY_PLURALS = {
    "qa": "Q&As",
    "playbook": "playbooks",
    "story": "stories",
    "testimonial": "testimonials",
}


@router.get("/{slug}/search")
async def search_page(request: Request, slug: str):
    """Search page with live search and browse."""
    client = load_client(slug)

    # Get category counts for tabs
    cat_counts = {}
    with get_db(client) as db:
        try:
            rows = db.conn.execute(
                "SELECT category, COUNT(*) as cnt FROM extractions GROUP BY category"
            ).fetchall()
            for r in rows:
                cat_counts[r["category"]] = r["cnt"]
        except Exception:
            pass

    return templates.TemplateResponse("pages/search.html", {
        "request": request,
        "current_client": client,
        "active_page": "search",
        "cat_counts": cat_counts,
        "cat_labels": CATEGORY_LABELS,
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

    has_query = bool(q.strip())
    has_category = bool(category)

    if not has_query and not has_category:
        return HTMLResponse(
            '<p class="text-sm text-zinc-400 py-4">Type to search or select a category to browse.</p>'
        )

    filters = SearchFilters()
    if has_category:
        filters.categories = [category]

    with get_db(client) as db:
        try:
            if has_query:
                results = keyword_search(db, q, filters)
            else:
                # Browse mode: no search term, filter by category
                results = browse_extractions(db, filters)
        except Exception:
            results = []

    if not results:
        label = CATEGORY_LABELS.get(category, category) if has_category else ""
        if has_query:
            msg = f'No results for &ldquo;{html_mod.escape(q)}&rdquo;'
            if label:
                msg += f" in {label}"
        else:
            msg = f"No {label} extractions found" if label else "No extractions found"
        return HTMLResponse(f'<p class="text-sm text-zinc-400 py-4">{msg}</p>')

    # Build display-ready results with snippet
    display_results = []
    for r in results:
        content = r.get("content", "")
        snippet = content[:200] + "..." if len(content) > 200 else content
        display_results.append({
            **r,
            "snippet": snippet,
        })

    # Header context
    mode = "search" if has_query else "browse"
    category_label = CATEGORY_LABELS.get(category, "") if has_category else ""
    category_plural = CATEGORY_PLURALS.get(category, "extractions") if has_category else "extractions"

    return templates.TemplateResponse("pages/_search_results.html", {
        "request": request,
        "results": display_results,
        "query": q,
        "slug": slug,
        "mode": mode,
        "category_label": category_label,
        "category_plural": category_plural,
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

    # Generate bar (per-card)
    if has_api_key(client):
        options_html = "".join(
            f'<option value="{v}">{l}</option>' for v, l in FORMAT_OPTIONS
        )
        eid = extraction_id
        sections.append(f"""
        <div class="mt-4 pt-4 border-t border-zinc-100" onclick="event.stopPropagation()">
          <form hx-post="/{slug}/generate/from-extraction/{eid}"
                hx-target="#card-draft-{eid}"
                hx-swap="innerHTML"
                hx-indicator="#card-gen-spinner-{eid}"
                hx-timeout="120000"
                class="flex items-center gap-3">
            <span class="text-xs font-medium text-zinc-500 uppercase tracking-wider shrink-0">Generate</span>
            <select name="format_type"
                    class="px-2 py-1 text-xs border border-zinc-200 rounded-lg bg-white text-zinc-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
              {options_html}
            </select>
            <button type="submit" hx-disabled-elt="this"
                    class="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
              Draft
            </button>
            <div id="card-gen-spinner-{eid}" class="htmx-indicator">
              <svg class="animate-spin h-4 w-4 text-indigo-500" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
            </div>
          </form>
          <div id="card-draft-{eid}" class="mt-3"></div>
        </div>
        """)

    return HTMLResponse("\n".join(sections))


@router.get("/{slug}/search/suggestions")
async def search_suggestions(request: Request, slug: str):
    """Return popular tags as clickable suggestion chips."""
    client = load_client(slug)

    popular_tags: list[dict] = []
    with get_db(client) as db:
        try:
            rows = db.conn.execute(
                """SELECT t.name, COUNT(*) as cnt FROM tags t
                   JOIN extraction_tags et ON t.id = et.tag_id
                   GROUP BY t.id
                   ORDER BY cnt DESC
                   LIMIT 15"""
            ).fetchall()
            popular_tags = [{"name": r["name"], "count": r["cnt"]} for r in rows]
        except Exception:
            pass

    if not popular_tags:
        return HTMLResponse("")

    return templates.TemplateResponse("pages/_search_suggestions.html", {
        "request": request,
        "tags": popular_tags,
    })
