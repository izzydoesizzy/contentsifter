"""FastAPI application factory for ContentSifter web UI."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="ContentSifter", docs_url=None, redoc_url=None)

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Store whether API key is available for auto-format feature
    app.state.has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

    # Make common data available to all templates
    @app.middleware("http")
    async def add_template_context(request, call_next):
        from contentsifter.config import list_clients

        request.state.clients = list_clients()
        request.state.has_api_key = app.state.has_api_key
        return await call_next(request)

    # Register all routes
    from contentsifter.web.routes import register_routes

    register_routes(app)

    return app
