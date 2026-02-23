"""Interview management routes."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from contentsifter.config import load_client
from contentsifter.interview.generator import generate_questionnaire
from contentsifter.web.app import templates
from contentsifter.web.deps import get_db
from contentsifter.web.utils import simple_md_to_html

router = APIRouter()


@router.get("/{slug}/interview")
async def interview_page(request: Request, slug: str):
    """Interview management page."""
    client = load_client(slug)

    # Check for existing questionnaire
    guide_path = client.content_dir / "interview-guide.md"
    questionnaire = None
    question_count = 0

    if guide_path.exists():
        content = guide_path.read_text()
        questionnaire = {
            "path": str(guide_path),
            "modified": guide_path.stat().st_mtime,
            "content": content,
        }
        # Count questions
        question_count = len(re.findall(r"\*\*Q\d+\.\*\*", content))

    # Count interview content items
    interview_items = 0
    with get_db(client) as db:
        try:
            row = db.conn.execute(
                "SELECT COUNT(*) as cnt FROM content_items WHERE content_type = 'transcript'"
            ).fetchone()
            interview_items = row["cnt"]
        except Exception:
            pass

    return templates.TemplateResponse("pages/interview.html", {
        "request": request,
        "current_client": client,
        "active_page": "interview",
        "questionnaire": questionnaire,
        "question_count": question_count,
        "interview_items": interview_items,
    })


@router.post("/{slug}/interview/generate")
async def generate_interview(request: Request, slug: str, niche: str = Form("")):
    """Generate a new interview questionnaire."""
    client = load_client(slug)
    output_path = client.content_dir / "interview-guide.md"

    markdown, saved = generate_questionnaire(
        client_name=client.name,
        niche=niche or None,
        output_path=output_path,
    )

    question_count = len(re.findall(r"\*\*Q\d+\.\*\*", markdown))

    return HTMLResponse(f"""
    <div class="rounded-lg px-4 py-3 text-sm bg-emerald-50 text-emerald-800 border border-emerald-200 mb-4" data-flash>
      Questionnaire generated with {question_count} questions
    </div>
    <div hx-get="/{slug}/interview/preview" hx-trigger="load" hx-swap="innerHTML"></div>
    """)


@router.get("/{slug}/interview/preview")
async def interview_preview(request: Request, slug: str):
    """Return questionnaire content as HTML fragment."""
    client = load_client(slug)
    guide_path = client.content_dir / "interview-guide.md"

    if not guide_path.exists():
        return HTMLResponse('<p class="text-sm text-zinc-400 py-4">No questionnaire generated yet.</p>')

    content = guide_path.read_text()
    # Simple markdown to HTML: convert headings, bold, italic, lists
    html = simple_md_to_html(content)

    return HTMLResponse(f"""
    <div class="prose prose-sm max-w-none text-zinc-700 leading-relaxed">
      {html}
    </div>
    """)


