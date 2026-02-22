"""Dashboard routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from contentsifter.config import list_clients, load_client
from contentsifter.web.app import templates
from contentsifter.web.deps import content_summary, get_db

router = APIRouter()


@router.get("/")
async def index(request: Request):
    """Redirect to default client dashboard."""
    clients = list_clients()
    if not clients:
        return RedirectResponse("/clients", status_code=302)

    default = next((c for c in clients if c["is_default"]), clients[0])
    return RedirectResponse(f"/{default['slug']}", status_code=302)


@router.get("/{slug}")
async def dashboard(request: Request, slug: str):
    """Client dashboard with overview stats."""
    try:
        client = load_client(slug)
    except ValueError:
        return RedirectResponse("/clients", status_code=302)

    with get_db(client) as db:
        summary = content_summary(db, client)

    return templates.TemplateResponse("pages/dashboard.html", {
        "request": request,
        "current_client": client,
        "active_page": "dashboard",
        "summary": summary,
    })
