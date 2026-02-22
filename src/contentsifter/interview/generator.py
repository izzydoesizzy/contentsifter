"""Questionnaire markdown generator.

Assembles interview prompts into a ready-to-use markdown file
with instructions, numbered questions, and optional niche-specific prompts.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from contentsifter.interview.prompts import (
    CATEGORIES,
    NICHE_GENERATION_SYSTEM,
    NICHE_GENERATION_USER,
    get_all_prompts,
    get_prompt_count,
)
from contentsifter.llm.client import complete_with_retry

log = logging.getLogger(__name__)


def generate_niche_prompts(
    niche: str,
    llm_client,
    count: int = 15,
) -> list[dict]:
    """Generate niche-specific prompts via LLM.

    Returns list of prompt dicts compatible with the prompt library format.
    """
    existing = get_all_prompts()
    existing_text = "\n".join(f"- {p['question']}" for p in existing)

    result = complete_with_retry(
        llm_client,
        system=NICHE_GENERATION_SYSTEM.format(count=count),
        user=NICHE_GENERATION_USER.format(
            niche=niche,
            existing_questions=existing_text,
            count=count,
        ),
        max_tokens=4096,
    )

    try:
        content = result.content.strip()
        # Handle markdown code fences
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        prompts = json.loads(content)
    except (json.JSONDecodeError, IndexError):
        log.warning("Failed to parse niche prompts from LLM response")
        return []

    # Normalize into prompt library format
    niche_prompts = []
    for i, p in enumerate(prompts, 1):
        niche_prompts.append({
            "id": f"niche_{i:02d}",
            "category": "niche",
            "question": p.get("question", ""),
            "follow_up": p.get("follow_up"),
            "framework": "llm_generated",
            "content_type": p.get("content_type", "qa"),
            "estimated_minutes": 2,
            "tags": p.get("tags", []),
        })

    return niche_prompts


def _format_instructions(client_name: str | None, total_questions: int) -> str:
    """Build the instruction header for the questionnaire."""
    est_minutes = 60 + (total_questions - 80) * 0.75 if total_questions > 80 else 60
    est_minutes = max(45, min(120, est_minutes))

    header = "# Voice Capture Interview Guide\n"
    if client_name:
        header += f"**Client:** {client_name}\n"
    header += f"**Date generated:** {datetime.now().strftime('%Y-%m-%d')}\n"
    header += f"**Total questions:** {total_questions}\n"

    header += """
## How to Use This Guide

1. Open your voice transcription tool (phone dictation, Otter.ai, or any speech-to-text app)
2. Start recording
3. For each question below:
   - **Read the question number and question out loud** (this helps us split the transcript later)
   - Then answer it naturally — speak as if you're talking to a friend
   - Take as long as you need — longer answers give us more to work with
   - If a question doesn't apply to you, just say "skip" and move to the next one
4. When you're done, save the transcript as a text or markdown file
5. Send the transcript file back for processing

### Tips for Great Answers

- **Don't overthink it** — your first instinct is usually the most authentic
- **Use specific names, numbers, and examples** whenever possible
- **Stories are gold** — "tell me about a time when..." deserves a real story, not a summary
- **It's OK to ramble** — we'll extract the best parts
- **If a follow-up question is listed**, answer that too — it helps draw out more detail
- **Take breaks** if you need to — you can pause recording and come back"""

    header += f"\n- **Estimated time:** {int(est_minutes)}-{int(est_minutes + 30)} minutes\n"

    return header


def _format_category_section(
    category_key: str,
    category_meta: dict,
    prompts: list[dict],
    start_number: int,
) -> tuple[str, int]:
    """Format one category section. Returns (markdown, next_question_number)."""
    lines = []
    part_num = category_meta["order"]
    lines.append(f"\n---\n\n## Part {part_num}: {category_meta['name']}")
    lines.append(f"*{category_meta['description']}*\n")

    q_num = start_number
    for prompt in prompts:
        lines.append(f"**Q{q_num}.** {prompt['question']}")
        if prompt.get("follow_up"):
            lines.append(f"  - *Follow-up: {prompt['follow_up']}*")
        lines.append("")
        q_num += 1

    return "\n".join(lines), q_num


def generate_questionnaire(
    client_name: str | None = None,
    niche: str | None = None,
    llm_client=None,
    output_path: Path | None = None,
) -> tuple[str, Path | None]:
    """Generate a complete interview questionnaire as markdown.

    Args:
        client_name: Client's name for the header.
        niche: Optional niche/industry for generating additional targeted prompts.
        llm_client: LLM client (required for niche prompt generation).
        output_path: Where to save the markdown file.

    Returns:
        (markdown_content, output_path or None if not saved)
    """
    all_prompts = get_all_prompts()

    # Generate niche prompts if requested
    niche_prompts: list[dict] = []
    if niche and llm_client:
        log.info("Generating niche-specific prompts for: %s", niche)
        niche_prompts = generate_niche_prompts(niche, llm_client)
        log.info("Generated %d niche prompts", len(niche_prompts))
    elif niche and not llm_client:
        log.warning("Niche prompts requested but no LLM client available — skipping")

    total = get_prompt_count() + len(niche_prompts)

    # Build markdown
    sections = []
    sections.append(_format_instructions(client_name, total))

    # Render each category
    q_num = 1
    sorted_categories = sorted(CATEGORIES.items(), key=lambda x: x[1]["order"])
    for cat_key, cat_meta in sorted_categories:
        cat_prompts = [p for p in all_prompts if p["category"] == cat_key]
        if not cat_prompts:
            continue
        section, q_num = _format_category_section(cat_key, cat_meta, cat_prompts, q_num)
        sections.append(section)

    # Add niche section if we have prompts
    if niche_prompts:
        niche_meta = {
            "name": f"Your Industry: {niche.title()}",
            "description": f"These questions are tailored specifically to your work in {niche}.",
            "order": 10,
        }
        section, q_num = _format_category_section("niche", niche_meta, niche_prompts, q_num)
        sections.append(section)

    # Closing
    sections.append("\n---\n")
    sections.append("## You're Done!")
    sections.append("")
    sections.append("Stop your recording and save the transcript. Great work — this material")
    sections.append("will be the foundation for all the content we create in your voice.")

    markdown = "\n".join(sections)

    # Save if path provided
    saved_path = None
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown)
        saved_path = output_path

    return markdown, saved_path
