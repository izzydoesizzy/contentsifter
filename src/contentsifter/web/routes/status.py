"""Status and pipeline routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from contentsifter.config import load_client
from contentsifter.web.app import templates
from contentsifter.web.deps import content_summary, get_db, get_repo

router = APIRouter()


@router.get("/{slug}/status")
async def status_page(request: Request, slug: str):
    """Detailed processing status page."""
    client = load_client(slug)

    with get_db(client) as db:
        repo = get_repo(db)
        summary = content_summary(db, client)

        # Pipeline progress
        pipeline = None
        if summary["calls"] > 0:
            prog = repo.get_progress_summary()
            total = prog["total_calls"]
            pipeline = {
                "total": total,
                "stages": {},
            }
            for stage in ["parsed", "chunked", "extracted"]:
                done = prog["stages"].get(stage, 0)
                pipeline["stages"][stage] = {
                    "done": done,
                    "total": total,
                    "pct": int(done / total * 100) if total else 0,
                    "complete": done == total,
                }

        # Suggestions
        suggestions = _build_suggestions(summary, pipeline, client)

    return templates.TemplateResponse("pages/status.html", {
        "request": request,
        "current_client": client,
        "active_page": "status",
        "summary": summary,
        "pipeline": pipeline,
        "suggestions": suggestions,
    })


def _build_suggestions(summary: dict, pipeline: dict | None, client) -> list[str]:
    """Build actionable suggestions based on current state."""
    suggestions = []

    if summary["content_items"] == 0 and summary["extractions"] == 0:
        suggestions.append("Upload content files to get started")
        if not summary["has_questionnaire"]:
            suggestions.append("Generate an interview questionnaire")

    if pipeline:
        for stage in ["chunked", "extracted"]:
            info = pipeline["stages"][stage]
            if not info["complete"]:
                suggestions.append(
                    f"{info['total'] - info['done']} calls need {stage.rstrip('ed')}ing "
                    f"(run `contentsifter -C {client.slug} {'chunk' if stage == 'chunked' else 'extract'}`)"
                )

    total_source = summary["content_items"] + summary["extractions"]
    if not summary["has_voice_print"] and total_source >= 5:
        suggestions.append(
            f'Ready for voice print — <a href="/{client.slug}/voice-print" class="text-indigo-600 hover:text-indigo-800 font-medium">generate one</a>'
        )
    elif summary["has_voice_print"] and total_source > 0:
        suggestions.append(
            f'<a href="/{client.slug}/generate" class="text-indigo-600 hover:text-indigo-800 font-medium">Generate content</a> from your source material'
        )

    return suggestions
