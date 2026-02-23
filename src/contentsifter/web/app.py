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

# Register template globals after import
def _setup_template_globals():
    from contentsifter.config import list_clients

    def draft_count(client) -> int:
        """Count saved draft files for a client."""
        if client and hasattr(client, "drafts_dir") and client.drafts_dir.exists():
            return len(list(client.drafts_dir.glob("*.md")))
        return 0

    templates.env.globals["list_all_clients"] = list_clients
    templates.env.globals["draft_count"] = draft_count

_setup_template_globals()


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
