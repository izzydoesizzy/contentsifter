"""Route registration for ContentSifter web UI."""

from __future__ import annotations

from fastapi import FastAPI


def register_routes(app: FastAPI):
    """Include all route modules."""
    from contentsifter.web.routes import (
        clients,
        dashboard,
        ingest,
        interview,
        search,
        status,
    )

    app.include_router(dashboard.router)
    app.include_router(clients.router, prefix="/clients")
    app.include_router(ingest.router)
    app.include_router(interview.router)
    app.include_router(search.router)
    app.include_router(status.router)
