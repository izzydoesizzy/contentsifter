"""Content draft generation from search results."""

from __future__ import annotations

import logging
from pathlib import Path

from contentsifter.generate.gates import load_ai_gate, run_content_gates
from contentsifter.generate.templates import TEMPLATES
from contentsifter.llm.client import complete_with_retry

log = logging.getLogger(__name__)


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


def _inject_voice_context(system_prompt: str, voice_print: str | None) -> str:
    """Inject voice print into a system prompt's {voice_context} placeholder."""
    voice_context = ""
    if voice_print:
        voice_context = f"\n\nWrite in this voice (reference guide below):\n\n{voice_print}"

    if "{voice_context}" in system_prompt:
        return system_prompt.format(voice_context=voice_context)
    elif voice_print:
        return system_prompt + voice_context
    return system_prompt


def generate_draft(
    results: list[dict],
    format_type: str,
    llm_client,
    topic: str | None = None,
    voice_print: str | None = None,
    save_to: Path | None = None,
) -> str:
    """Generate a content draft from search results.

    All drafts pass through content gates (AI detection + voice matching +
    hard cleanup). Voice print and gates are never skipped.

    Args:
        results: Search results to use as source material
        format_type: One of the TEMPLATES keys
        llm_client: The LLM client to use
        topic: Optional topic/title override
        voice_print: Optional voice print content for tone matching
        save_to: Optional path to save the draft as a markdown file
    """
    if format_type not in TEMPLATES:
        raise ValueError(f"Unknown format: {format_type}. Choose from: {list(TEMPLATES.keys())}")

    template = TEMPLATES[format_type]
    source_material = format_source_material(results)
    system_prompt = _inject_voice_context(template["system"], voice_print)

    if not topic:
        topic = results[0]["title"] if results else "career coaching insights"

    response = complete_with_retry(
        llm_client,
        system=system_prompt,
        user=template["user"].format(
            topic=topic,
            source_material=source_material,
        ),
        max_tokens=2048,
    )

    draft = response.content

    # Always run content gates (AI detection + voice matching + hard cleanup)
    log.info("Running content gates on %s draft...", format_type)
    ai_gate_doc = load_ai_gate()
    draft = run_content_gates(
        draft, llm_client, voice_print=voice_print, ai_gate_doc=ai_gate_doc
    )

    if save_to:
        save_to.parent.mkdir(parents=True, exist_ok=True)
        save_to.write_text(f"# {topic}\n\n*Format: {format_type}*\n\n---\n\n{draft}\n")

    return draft
