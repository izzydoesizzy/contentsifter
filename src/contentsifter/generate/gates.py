"""Content gates — validation passes that run on every draft before it's finalized.

Two gates:
1. AI Gate: Catches and rewrites AI-sounding patterns (em dashes, hedging, five-dollar words, etc.)
2. Voice Gate: Validates and rewrites to match the voice print

Both gates are implemented as LLM calls that take the draft + reference doc and return a rewritten version.
"""

from __future__ import annotations

import logging
from pathlib import Path

from contentsifter.config import CONTENT_DIR
from contentsifter.llm.client import complete_with_retry

log = logging.getLogger(__name__)

AI_GATE_PATH = CONTENT_DIR / "ai-gate.md"

AI_GATE_SYSTEM = """\
You are a strict content editor. Your ONLY job is to rewrite the draft so it does \
NOT sound like AI-generated text.

You have a comprehensive reference document of AI writing tells — banned words, \
banned phrases, structural patterns, and anti-patterns. Apply ALL of these rules \
to the draft.

Rules:
- Remove or replace every banned word and phrase from the reference
- ZERO em dashes (—) or en dashes (–) allowed. Replace every single one with a period, comma, colon, or parentheses
- ZERO markdown asterisks (**bold** or *italic*). Remove all asterisks. Use CAPS for emphasis instead (e.g., "this is HUGE" not "this is **huge**")
- Emoji: remove most emoji. Only keep ❌ and ✅ when used as list bullet points. Remove all other emoji (💪 ✨ 🚀 🔥 etc.)
- Kill all hedging language. Be direct
- Replace five-dollar words with simple ones ("use" not "utilize", "help" not "empower")
- Break up uniform list formatting. Vary sentence length
- Remove formulaic openings and closings
- Cut filler phrases that add nothing
- Use active voice throughout
- Keep the SAME content, meaning, structure, and approximate length
- Do NOT add new information or change the message
- Do NOT add commentary or notes — return ONLY the rewritten draft
- Preserve CAPS emphasis, line breaks, and hashtags"""

VOICE_GATE_SYSTEM = """\
You are a voice-matching editor. Your ONLY job is to rewrite the draft so it \
sounds exactly like the person described in the voice print reference.

Rules:
- Match the tone, vocabulary, sentence patterns, and energy level from the voice print
- Use the signature phrases and expressions naturally (don't force every one in)
- Match the formatting style for this content type (LinkedIn, newsletter, email, etc.)
- Keep the collaborative "we/let's" framing over "you should"
- Maintain conversational register — contractions, sentence fragments, casual connectors
- Keep the teaching pattern: Problem → Reframe → Steps → Example → Encouragement
- Preserve all factual content, structure, and approximate length
- Do NOT add new information or change the message
- Do NOT add commentary or notes — return ONLY the rewritten draft
- Preserve hashtags if present"""


def load_ai_gate() -> str | None:
    """Load the AI gate reference document from disk."""
    if AI_GATE_PATH.exists():
        return AI_GATE_PATH.read_text()
    return None


def run_ai_gate(draft: str, llm_client, ai_gate_doc: str | None = None) -> str:
    """Run the AI detection gate on a draft.

    Rewrites the draft to remove AI-sounding patterns.
    """
    if ai_gate_doc is None:
        ai_gate_doc = load_ai_gate()

    if not ai_gate_doc:
        log.warning("No ai-gate.md found at %s — skipping AI gate", AI_GATE_PATH)
        return draft

    response = complete_with_retry(
        llm_client,
        system=AI_GATE_SYSTEM + f"\n\n## AI Writing Reference\n\n{ai_gate_doc}",
        user=f"Rewrite this draft to remove all AI-sounding patterns:\n\n{draft}",
        max_tokens=4096,
    )
    return response.content


def run_voice_gate(draft: str, llm_client, voice_print: str | None = None) -> str:
    """Run the voice print gate on a draft.

    Rewrites the draft to match the voice print.
    """
    if not voice_print:
        log.warning("No voice print provided — skipping voice gate")
        return draft

    response = complete_with_retry(
        llm_client,
        system=VOICE_GATE_SYSTEM + f"\n\n## Voice Print Reference\n\n{voice_print}",
        user=f"Rewrite this draft to match the voice print:\n\n{draft}",
        max_tokens=4096,
    )
    return response.content


def _hard_cleanup(text: str) -> str:
    """Regex backstop: catch anything the LLM gates missed.

    Runs after all LLM gates. Handles em dashes, asterisks, and decorative emoji
    that the LLM sometimes preserves despite instructions.
    """
    import re

    # Em dashes → period + space
    text = text.replace("—", ". ")
    text = text.replace("–", ". ")
    # Clean up double periods or period-comma from replacement
    text = re.sub(r"\.\s*\.", ".", text)
    text = re.sub(r"\.\s*,", ",", text)

    # Strip markdown bold/italic asterisks (preserve ❌ ✅ list bullets)
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)

    # Strip decorative emoji (keep ❌ ✅ only)
    text = re.sub(r"[^\S\n]*[🚀💪✨🔥💡🎯🙌👏👇👆🤔💰🎉🏆🌟⭐💥🔑📌🙏❤️🤝💼📈🧠👀🎁💎🫶🤷‍♀️🤷‍♂️🤷]+[^\S\n]*", "", text)

    # Clean up leftover whitespace
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def run_content_gates(
    draft: str,
    llm_client,
    voice_print: str | None = None,
    ai_gate_doc: str | None = None,
) -> str:
    """Run content gates in sequence: AI gate → voice gate → hard cleanup.

    Returns the final gated draft.
    """
    log.info("Running AI gate...")
    gated = run_ai_gate(draft, llm_client, ai_gate_doc=ai_gate_doc)

    if voice_print:
        log.info("Running voice gate...")
        gated = run_voice_gate(gated, llm_client, voice_print=voice_print)

    log.info("Running hard cleanup...")
    gated = _hard_cleanup(gated)

    return gated
