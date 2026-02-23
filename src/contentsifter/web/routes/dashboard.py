"""Dashboard routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response

from contentsifter.config import list_clients, load_client
from contentsifter.web.app import templates
from contentsifter.web.deps import content_summary, get_db

router = APIRouter()


@router.get("/favicon.ico")
async def favicon():
    """Return empty response for favicon requests."""
    return Response(status_code=204)


@router.get("/")
async def index(request: Request):
    """Redirect to default client dashboard."""
    clients = list_clients()
    if not clients:
        return RedirectResponse("/clients/", status_code=302)

    default = next((c for c in clients if c["is_default"]), clients[0])
    return RedirectResponse(f"/{default['slug']}", status_code=302)


# Paths that should never be treated as client slugs
_RESERVED = {"clients", "static"}


@router.get("/{slug}")
async def dashboard(request: Request, slug: str):
    """Client dashboard with overview stats."""
    if slug in _RESERVED:
        return RedirectResponse(f"/{slug}/", status_code=307)

    try:
        client = load_client(slug)
    except (ValueError, FileNotFoundError):
        return RedirectResponse("/clients/", status_code=302)

    with get_db(client) as db:
        summary = content_summary(db, client)

    return templates.TemplateResponse("pages/dashboard.html", {
        "request": request,
        "current_client": client,
        "active_page": "dashboard",
        "summary": summary,
    })
