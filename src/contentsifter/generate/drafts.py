"""Content draft generation from search results."""

from __future__ import annotations

from contentsifter.generate.templates import TEMPLATES
from contentsifter.llm.client import complete_with_retry


def format_source_material(results: list[dict]) -> str:
    """Format search results into source material for generation."""
    sections = []
    for r in results:
        section = f"### {r['title']} [{r['category'].upper()}]\n"
        section += f"{r['content']}\n"
        if r.get("raw_quote"):
            section += f'\n> Direct quote: "{r["raw_quote"]}"\n'
        if r.get("tags"):
            section += f"Tags: {', '.join(r['tags'])}\n"
        sections.append(section)
    return "\n---\n".join(sections)


def generate_draft(
    results: list[dict],
    format_type: str,
    llm_client,
    topic: str | None = None,
) -> str:
    """Generate a content draft from search results.

    Args:
        results: Search results to use as source material
        format_type: One of "linkedin", "newsletter", "thread", "playbook"
        llm_client: The LLM client to use
        topic: Optional topic/title override
    """
    if format_type not in TEMPLATES:
        raise ValueError(f"Unknown format: {format_type}. Choose from: {list(TEMPLATES.keys())}")

    template = TEMPLATES[format_type]
    source_material = format_source_material(results)

    if not topic:
        # Derive topic from the most common title themes
        topic = results[0]["title"] if results else "career coaching insights"

    response = complete_with_retry(
        llm_client,
        system=template["system"],
        user=template["user"].format(
            topic=topic,
            source_material=source_material,
        ),
        max_tokens=2048,
    )

    return response.content
