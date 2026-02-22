"""Content extraction from topic chunks."""

from __future__ import annotations

import json
import logging
import re

from contentsifter.extraction.categories import TAGS
from contentsifter.extraction.prompts import (
    CONTENT_EXTRACTION_USER_PROMPT,
    EXTRACTION_USER_PROMPT,
    format_turns_compact,
    get_content_extraction_system_prompt,
    get_extraction_system_prompt,
)
from contentsifter.llm.client import complete_with_retry
from contentsifter.storage.models import Extraction

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"qa", "testimonial", "playbook", "story"}
VALID_TAGS = set(TAGS.keys())


def _extract_json_array(text: str) -> list:
    """Extract a JSON array from text, handling markdown code fences."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in response: {text[:200]}")

    return json.loads(text[start : end + 1])


def extract_from_chunk(
    turns: list[dict],
    call_type: str,
    call_date: str,
    topic_title: str,
    topic_summary: str,
    llm_client,
    coach_name: str = "",
    coach_email: str = "",
) -> list[Extraction]:
    """Extract categorized content from a topic chunk's turns."""
    formatted = format_turns_compact(turns)

    # Skip very short segments (likely just greetings)
    if len(turns) < 3 or len(formatted) < 100:
        return []

    system_prompt = get_extraction_system_prompt(coach_name, coach_email)

    response = complete_with_retry(
        llm_client,
        system=system_prompt,
        user=EXTRACTION_USER_PROMPT.format(
            call_type=call_type,
            date=call_date,
            topic=topic_title,
            summary=topic_summary or "No summary available",
            transcript=formatted,
        ),
    )

    return _parse_extractions(response.content)


def extract_from_content_item(
    item: dict,
    llm_client,
    author_name: str = "",
) -> list[Extraction]:
    """Extract categorized content from a content item (LinkedIn post, email, etc.)."""
    text = item.get("text", "")

    # Skip very short items
    if len(text) < 50:
        return []

    system_prompt = get_content_extraction_system_prompt(author_name)

    response = complete_with_retry(
        llm_client,
        system=system_prompt,
        user=CONTENT_EXTRACTION_USER_PROMPT.format(
            content_type=item.get("content_type", "other"),
            date=item.get("date", "unknown"),
            title=item.get("title", "Untitled"),
            text=text,
        ),
    )

    return _parse_extractions(response.content)


def _parse_extractions(response_text: str) -> list[Extraction]:
    """Parse Claude's extraction response into Extraction objects."""
    try:
        items = _extract_json_array(response_text)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse extraction response: {e}")
        return []

    extractions = []
    for item in items:
        category = item.get("category", "").lower()
        if category not in VALID_CATEGORIES:
            logger.warning(f"Skipping extraction with invalid category: {category}")
            continue

        # Filter tags to valid ones
        tags = [t for t in item.get("tags", []) if t in VALID_TAGS]

        extractions.append(
            Extraction(
                category=category,
                title=item.get("title", "Untitled"),
                content=item.get("content", ""),
                raw_quote=item.get("raw_quote"),
                speaker=item.get("speaker"),
                quality_score=min(5, max(1, item.get("quality_score", 3))),
                tags=tags,
            )
        )

    return extractions
