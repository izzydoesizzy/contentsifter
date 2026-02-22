"""Search routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from contentsifter.config import load_client
from contentsifter.search.filters import SearchFilters
from contentsifter.search.keyword import keyword_search
from contentsifter.web.app import templates
from contentsifter.web.deps import get_db

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
        return HTMLResponse(f'<p class="text-sm text-zinc-400 py-4">No results for &ldquo;{q}&rdquo;</p>')

    cards = []
    for r in results:
        title = r.get("title", "Untitled")
        cat = r.get("category", "other")
        content = r.get("content", "")
        if len(content) > 200:
            content = content[:197] + "..."
        tags = r.get("tags", [])
        quality = r.get("quality_score", 0)
        call_title = r.get("call_title", "")
        call_date = r.get("call_date", "")

        tags_html = " ".join(
            f'<span class="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-zinc-100 text-zinc-600">{t}</span>'
            for t in tags[:5]
        )

        import html as html_mod
        cards.append(f"""
        <div class="bg-white rounded-xl border border-zinc-200 p-5 hover:border-indigo-200 transition-colors">
          <div class="flex items-start justify-between mb-2">
            <h3 class="text-sm font-medium text-zinc-900">{html_mod.escape(title)}</h3>
            <span class="badge badge-{cat} ml-2 shrink-0">{cat}</span>
          </div>
          <p class="text-sm text-zinc-600 mb-3 leading-relaxed">{html_mod.escape(content)}</p>
          <div class="flex items-center justify-between">
            <div class="flex flex-wrap gap-1">{tags_html}</div>
            <span class="text-xs text-zinc-400">{html_mod.escape(call_date[:10] if call_date else "")}</span>
          </div>
        </div>
        """)

    count_text = f'{len(results)} result{"s" if len(results) != 1 else ""}'
    return HTMLResponse(
        f'<p class="text-xs text-zinc-400 mb-3">{count_text}</p>'
        f'<div class="space-y-3">{"".join(cards)}</div>'
    )
