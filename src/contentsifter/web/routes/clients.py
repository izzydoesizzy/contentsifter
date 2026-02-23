"""Client management routes."""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from contentsifter.config import (
    create_client,
    list_clients,
    load_client,
    set_default_client,
    update_client,
)
from contentsifter.web.app import templates
from contentsifter.web.deps import content_summary, get_db

router = APIRouter()


@router.get("/")
async def clients_list(request: Request):
    """List all registered clients."""
    clients = list_clients()
    return templates.TemplateResponse("pages/clients.html", {
        "request": request,
        "clients": clients,
        "active_page": "clients",
        "current_client": None,
    })


@router.post("/")
async def clients_create(
    request: Request,
    slug: str = Form(...),
    name: str = Form(...),
    email: str = Form(""),
    description: str = Form(""),
):
    """Create a new client."""
    try:
        create_client(slug, name, email, description)
        # If htmx request, return updated table
        if request.headers.get("HX-Request"):
            clients = list_clients()
            return templates.TemplateResponse("pages/_clients_table.html", {
                "request": request,
                "clients": clients,
                "flash_message": f"Client '{name}' created",
                "flash_level": "success",
            })
        return RedirectResponse("/clients/", status_code=303)
    except ValueError as e:
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                f'<div class="rounded-lg px-4 py-3 text-sm bg-rose-50 text-rose-800 border border-rose-200 mb-4">{e}</div>',
            )
        return RedirectResponse("/clients/", status_code=303)


@router.get("/{slug}")
async def client_detail(request: Request, slug: str):
    """Show client detail page."""
    try:
        client = load_client(slug)
    except ValueError:
        return RedirectResponse("/clients/", status_code=302)

    with get_db(client) as db:
        summary = content_summary(db, client)

    return templates.TemplateResponse("pages/client_detail.html", {
        "request": request,
        "client": client,
        "summary": summary,
        "active_page": "clients",
        "current_client": client,
    })


@router.post("/{slug}/default")
async def set_default(request: Request, slug: str):
    """Set a client as the default."""
    try:
        set_default_client(slug)
    except ValueError:
        pass

    if request.headers.get("HX-Request"):
        return HTMLResponse(
            '<span class="text-sm text-emerald-600">Default updated</span>',
            headers={"HX-Redirect": f"/clients/{slug}"},
        )
    return RedirectResponse(f"/clients/{slug}", status_code=303)


@router.post("/{slug}/settings")
async def update_settings(
    request: Request,
    slug: str,
    api_key: str = Form(""),
):
    """Update client settings (API key)."""
    try:
        client = update_client(slug, api_key=api_key)
    except ValueError:
        return RedirectResponse("/clients/", status_code=302)

    if request.headers.get("HX-Request"):
        # Mask the key for display
        masked = _mask_key(api_key)
        return HTMLResponse(f"""
        <div class="rounded-lg px-4 py-3 text-sm bg-emerald-50 text-emerald-800 border border-emerald-200 mb-4" data-flash>
          API key updated{f' ({masked})' if api_key else ' (cleared)'}
        </div>
        """)

    return RedirectResponse(f"/clients/{slug}", status_code=303)


def _mask_key(key: str) -> str:
    """Mask an API key for display: sk-ant-...xxxx."""
    if not key or len(key) < 12:
        return "****"
    return key[:7] + "..." + key[-4:]
