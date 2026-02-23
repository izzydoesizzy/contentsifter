"""Content gates — validation passes that run on every draft before it's finalized.

Three gates:
1. AI Gate: Catches and rewrites AI-sounding patterns (em dashes, hedging, five-dollar words, etc.)
2. Voice Gate: Validates and rewrites to match the voice print
3. Hard Cleanup: Regex backstop that programmatically fixes all remaining violations

After gates run, verify_draft() checks for any remaining violations. If found, one
targeted LLM retry runs with specific violation feedback. Hard cleanup is the final
guaranteed backstop.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import NamedTuple

from contentsifter.config import CONTENT_DIR, MODEL_LIGHT
from contentsifter.llm.client import complete_with_retry, create_client

log = logging.getLogger(__name__)

AI_GATE_PATH = CONTENT_DIR / "ai-gate.md"

# ---------------------------------------------------------------------------
# Banned lists — derived from ai-gate.md Quick-Reference + Sections 2-15
# ---------------------------------------------------------------------------

BANNED_CHARS = {"—", "–"}

# Words that are ALWAYS banned regardless of context.
# Checked with word-boundary regex (\b) to avoid false positives.
BANNED_WORDS: frozenset[str] = frozenset({
    # Verbs (Section 3)
    "delve", "delving", "harness", "harnessing", "leverage", "leveraging",
    "utilize", "utilizing", "facilitate", "augment", "embark",
    "illuminate", "underscore", "bolster", "spearhead",
    "foster", "cultivate", "streamline", "empower", "elevate",
    "amplify", "curate", "catalyze", "galvanize",
    # Adjectives (Section 3)
    "robust", "seamless", "transformative",
    "groundbreaking", "exemplary", "invaluable", "commendable",
    "pivotal", "paramount", "multifaceted", "holistic", "synergistic",
    "ever-evolving", "thought-provoking",
    "unparalleled", "revolutionary", "unprecedented",
    # Nouns (Section 3)
    "tapestry", "realm", "beacon", "paradigm", "synergy", "synergies",
    "stakeholder", "nexus", "plethora", "cacophony",
    # Additional from writing style section
    "enlightening", "esteemed", "intricate", "elucidate",
})

# Formal connectors (Section 5) — always banned
BANNED_CONNECTORS: frozenset[str] = frozenset({
    "furthermore", "moreover", "additionally", "consequently",
    "nevertheless", "nonetheless", "notwithstanding", "subsequently",
    "accordingly", "hereby", "whereby",
    "undoubtedly", "arguably", "notably", "remarkably",
    "crucially", "importantly",
})

# Multi-word phrases — case-insensitive substring match
BANNED_PHRASES: tuple[str, ...] = (
    "it's important to note", "it's worth noting", "it's worth mentioning",
    "it's crucial to understand", "it is essential to consider",
    "in today's", "in the realm of", "serves as a",
    "at the end of the day", "in conclusion", "in closing", "in summary",
    "moving forward", "the bottom line", "navigate the", "embark on a journey",
    "unlock the potential", "harness the power", "at the forefront",
    "bridge the gap", "pave the way", "whether you're a seasoned",
    "as we navigate", "in an ever-evolving", "from a broader perspective",
    "generally speaking", "it could be argued", "needless to say",
    "it goes without saying", "for all intents and purposes",
    "at this point in time", "in order to", "due to the fact that",
    "has the ability to", "delve into", "shed light", "dive deep",
    "in a world where", "remains to be seen",
    # Bridge phrases (Section 5)
    "with that in mind", "on the flip side", "to put it simply",
    "to that end", "by the same token", "in the same vein", "along those lines",
    # Closers (Section 6)
    "to sum up", "in essence", "all things considered", "to wrap things up",
    "as we've seen", "final thoughts",
    # Hedging (Section 2)
    "perhaps you might want", "you may want to check", "one might argue",
    "it should be noted", "bearing in mind",
    "given the fact that", "as a matter of fact", "in light of the fact",
    # Openers (Section 4)
    "in the world of", "have you ever wondered",
    "when it comes to", "at its core",
)

# Safe mechanical word replacements — ONLY where the swap is always correct.
# Context-dependent words (landscape, dynamic, innovative, etc.) are excluded.
SAFE_WORD_SWAPS: dict[str, str] = {
    "utilize": "use", "utilizing": "using",
    "leverage": "use", "leveraging": "using",
    "harness": "use", "harnessing": "using",
    "facilitate": "help", "empower": "help",
    "embark": "start", "illuminate": "show",
    "underscore": "highlight", "bolster": "support",
    "foster": "build", "cultivate": "build",
    "streamline": "simplify", "elevate": "raise",
    "amplify": "increase", "curate": "pick",
    "catalyze": "start", "galvanize": "push",
    "spearhead": "lead", "augment": "add to",
    "delve": "dig", "delving": "digging",
    "robust": "strong", "seamless": "smooth",
    "transformative": "big",
    "groundbreaking": "new",
    "pivotal": "key", "paramount": "top",
    "multifaceted": "complex", "holistic": "whole",
    "unparalleled": "rare", "unprecedented": "new",
    "revolutionary": "new", "elucidate": "explain",
    # Connectors
    "furthermore": "and", "moreover": "and",
    "additionally": "also", "consequently": "so",
    "nevertheless": "but", "nonetheless": "but",
    "subsequently": "then", "accordingly": "so",
    "undoubtedly": "", "arguably": "",
    "notably": "", "remarkably": "",
    "crucially": "", "importantly": "",
    "hereby": "", "whereby": "where",
    "notwithstanding": "despite",
    # Nouns
    "tapestry": "mix", "realm": "area", "beacon": "guide",
    "paradigm": "model", "synergy": "teamwork", "synergies": "gains",
    "stakeholder": "person", "nexus": "center",
    "plethora": "lot", "cacophony": "noise",
}

# Safe mechanical phrase replacements
SAFE_PHRASE_SWAPS: dict[str, str] = {
    "in order to": "to",
    "due to the fact that": "because",
    "has the ability to": "can",
    "at this point in time": "now",
    "for all intents and purposes": "",
    "it goes without saying": "",
    "needless to say": "",
    "it's important to note that": "",
    "it's important to note": "",
    "it's worth noting that": "",
    "it's worth noting": "",
    "it's worth mentioning that": "",
    "it's worth mentioning": "",
    "from a broader perspective": "",
    "generally speaking": "",
    "it could be argued that": "",
    "it could be argued": "",
    "in conclusion": "",
    "in closing": "",
    "in summary": "",
    "moving forward": "",
    "the bottom line is": "",
    "the bottom line": "",
    "at the end of the day": "",
    "serves as a": "is a",
    "delve into": "dig into",
    "dive deep": "dig in",
    "shed light on": "show",
    "shed light": "show",
    "navigate the": "handle the",
    "harness the power": "use",
    "unlock the potential": "tap into",
    "in the realm of": "in",
    "in today's": "today,",
    "as we navigate": "as we work through",
    "bridge the gap": "close the gap",
    "pave the way": "open the door",
    "at the forefront of": "leading",
    "at the forefront": "leading",
    "all things considered": "",
    "to sum up": "",
    "to wrap things up": "",
    "final thoughts": "",
    "with that in mind": "so",
    "on the flip side": "but",
    "to put it simply": "",
    "to that end": "so",
    "by the same token": "similarly",
    "in the same vein": "similarly",
    "along those lines": "similarly",
    "in an ever-evolving": "in a changing",
    "ever-evolving": "changing",
    "remains to be seen": "is unclear",
    "in a world where": "when",
    "embark on a journey": "start",
}

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


class Violation(NamedTuple):
    """A single rule violation found in a draft."""
    category: str       # char, word, connector, phrase, semicolon, asterisk, emoji
    matched: str        # The text that triggered the violation
    line_number: int    # 1-indexed


def verify_draft(text: str) -> list[Violation]:
    """Check a draft against all instant-fail criteria.

    Returns a list of Violation tuples. Empty list means the draft passes.
    Pure string/regex matching — no LLM calls, very fast.
    """
    violations: list[Violation] = []
    lines = text.split("\n")

    for i, line in enumerate(lines, start=1):
        line_lower = line.lower()

        # Banned characters
        for ch in BANNED_CHARS:
            if ch in line:
                violations.append(Violation("char", ch, i))

        # Semicolons
        if ";" in line:
            violations.append(Violation("semicolon", ";", i))

        # Markdown bold/italic asterisks (not bullet point *)
        if re.search(r"\*{1,3}\S", line):
            violations.append(Violation("asterisk", "**", i))

        # Banned words (word-boundary, case-insensitive)
        for word in BANNED_WORDS:
            if re.search(r"\b" + re.escape(word) + r"\b", line_lower):
                violations.append(Violation("word", word, i))

        # Banned connectors
        for conn in BANNED_CONNECTORS:
            if re.search(r"\b" + re.escape(conn) + r"\b", line_lower):
                violations.append(Violation("connector", conn, i))

        # Banned phrases (substring)
        for phrase in BANNED_PHRASES:
            if phrase.lower() in line_lower:
                violations.append(Violation("phrase", phrase, i))

        # Decorative emoji
        if re.search(
            r"[🚀💪✨🔥💡🎯🙌👏👇👆🤔💰🎉🏆🌟⭐💥🔑📌🙏❤️🤝💼📈🧠👀🎁💎🫶🤷‍♀️🤷‍♂️🤷]",
            line,
        ):
            violations.append(Violation("emoji", "decorative emoji", i))

    return violations


def _format_violations_for_llm(violations: list[Violation]) -> str:
    """Format violations into a concise section for the LLM retry prompt."""
    if not violations:
        return ""

    by_cat: dict[str, list[Violation]] = {}
    for v in violations:
        by_cat.setdefault(v.category, []).append(v)

    labels = {
        "char": "Banned characters (ZERO em/en dashes)",
        "word": "Banned AI words (replace with simple alternatives)",
        "connector": "Formal connectors (replace with natural language)",
        "phrase": "Banned AI phrases (remove or rewrite)",
        "semicolon": "Semicolons (use periods instead)",
        "asterisk": "Markdown asterisks (use CAPS for emphasis)",
        "emoji": "Decorative emoji (remove all except checkmark/X)",
    }

    parts = ["The following violations MUST be fixed:\n"]
    for cat, viols in by_cat.items():
        parts.append(f"\n{labels.get(cat, cat)}:")
        seen: set[str] = set()
        for v in viols:
            if v.matched not in seen:
                seen.add(v.matched)
                parts.append(f"  - '{v.matched}' (line {v.line_number})")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# LLM system prompts
# ---------------------------------------------------------------------------

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
- Emoji: remove most emoji. Only keep ❌ and ✅ when used as list bullet points. Remove all other emoji
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

CRITICAL: Do NOT reintroduce AI writing patterns while matching the voice. \
Specifically: ZERO em dashes, ZERO markdown asterisks, ZERO formal connectors \
(furthermore, moreover, additionally, etc.), ZERO five-dollar words (utilize, \
leverage, harness, etc.).

Rules:
- Match the tone, vocabulary, sentence patterns, and energy level from the voice print
- Use the signature phrases and expressions naturally (don't force every one in)
- Match the formatting style for this content type (LinkedIn, newsletter, email, etc.)
- Keep the collaborative "we/let's" framing over "you should"
- Maintain conversational register — contractions, sentence fragments, casual connectors
- Keep the teaching pattern: Problem -> Reframe -> Steps -> Example -> Encouragement
- Preserve all factual content, structure, and approximate length
- Do NOT add new information or change the message
- Do NOT add commentary or notes — return ONLY the rewritten draft
- Preserve hashtags if present"""

RETRY_SYSTEM = """\
You are doing a CORRECTION PASS on a content draft. The draft was already edited \
but STILL contains banned patterns. Fix EVERY violation listed below. \
Keep the voice, tone, and meaning. Change as little as possible. \
Return ONLY the corrected draft.

RULES:
- ZERO em dashes (—) or en dashes (–). Replace with period, comma, colon, or parentheses
- ZERO markdown asterisks. Use CAPS for emphasis
- Replace every banned word with a simple alternative ("use" not "utilize")
- Remove every banned phrase or rewrite the sentence without it
- Replace formal connectors with natural language ("and", "but", "so", "then")
- Replace semicolons with periods
- Remove decorative emoji (keep only ✅ ❌)"""


# ---------------------------------------------------------------------------
# Gate functions
# ---------------------------------------------------------------------------


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


def _retry_fix(
    draft: str,
    llm_client,
    violations: list[Violation],
    ai_gate_doc: str | None = None,
    voice_print: str | None = None,
) -> str:
    """Targeted LLM call to fix specific violations."""
    feedback = _format_violations_for_llm(violations)

    system = RETRY_SYSTEM
    if ai_gate_doc:
        system += f"\n\n## AI Writing Reference (excerpt)\n\n{ai_gate_doc[:2000]}"
    if voice_print:
        system += f"\n\n## Voice Reference (excerpt)\n\n{voice_print[:2000]}"

    response = complete_with_retry(
        llm_client,
        system=system,
        user=f"{feedback}\n\n---\n\nFix all violations and return ONLY the corrected draft:\n\n{draft}",
        max_tokens=4096,
    )
    return response.content


# ---------------------------------------------------------------------------
# Hard cleanup — guaranteed programmatic backstop
# ---------------------------------------------------------------------------


def _hard_cleanup(text: str) -> str:
    """Regex backstop: programmatically fix anything the LLM gates missed.

    Runs after all LLM gates. Handles:
    - Safe phrase swaps (before word swaps to avoid partial matches)
    - Safe word swaps (word-boundary, case-insensitive)
    - Em/en dashes, semicolons, asterisks, decorative emoji, whitespace
    """
    # Phase 1: Phrase swaps (longest first to avoid partial matches)
    for phrase in sorted(SAFE_PHRASE_SWAPS, key=len, reverse=True):
        replacement = SAFE_PHRASE_SWAPS[phrase]
        text = re.sub(re.escape(phrase), replacement, text, flags=re.IGNORECASE)

    # Phase 2: Word swaps (word-boundary, case-insensitive)
    for word, replacement in SAFE_WORD_SWAPS.items():
        text = re.sub(
            r"\b" + re.escape(word) + r"\b", replacement, text, flags=re.IGNORECASE
        )

    # Phase 3: Em/en dashes -> period + space
    text = re.sub(r"\s*[—–]\s*", ". ", text)
    text = re.sub(r"\. ([a-z])", lambda m: ". " + m.group(1).upper(), text)
    text = re.sub(r"\.\s*\.", ".", text)
    text = re.sub(r"\.\s*,", ",", text)

    # Phase 4: Semicolons -> periods
    text = re.sub(r"\s*;\s*", ". ", text)
    text = re.sub(r"\. ([a-z])", lambda m: ". " + m.group(1).upper(), text)
    text = re.sub(r"\.\s*\.", ".", text)

    # Phase 5: Strip markdown bold/italic asterisks
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)

    # Phase 6: Strip decorative emoji (keep ❌ ✅ only)
    text = re.sub(
        r"[^\S\n]*[🚀💪✨🔥💡🎯🙌👏👇👆🤔💰🎉🏆🌟⭐💥🔑📌🙏❤️🤝💼📈🧠👀🎁💎🫶🤷‍♀️🤷‍♂️🤷]+[^\S\n]*",
        "",
        text,
    )

    # Phase 7: Whitespace cleanup
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\n +\n", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def _create_light_client():
    """Create a lightweight Haiku client for mechanical tasks like the AI gate."""
    try:
        return create_client(mode="auto", model=MODEL_LIGHT)
    except Exception:
        return None


def run_content_gates(
    draft: str,
    llm_client,
    voice_print: str | None = None,
    ai_gate_doc: str | None = None,
) -> str:
    """Run content gates with verification and retry.

    Flow:
    1. AI gate (Haiku) — remove AI patterns
    2. Voice gate (Sonnet) — match client voice
    3. Verify — check for remaining violations
    4. If violations: one targeted LLM retry with specific feedback
    5. Hard cleanup — guaranteed programmatic fix
    6. Final verify — log warning if anything remains
    """
    if ai_gate_doc is None:
        ai_gate_doc = load_ai_gate()

    # AI gate (lightweight model)
    log.info("Running AI gate...")
    light_client = _create_light_client() or llm_client
    gated = run_ai_gate(draft, light_client, ai_gate_doc=ai_gate_doc)

    # Voice gate (main model)
    if voice_print:
        log.info("Running voice gate...")
        gated = run_voice_gate(gated, llm_client, voice_print=voice_print)

    # Verify after both gates
    violations = verify_draft(gated)
    if violations:
        log.info(
            "Found %d violations after gates, running targeted retry...",
            len(violations),
        )
        gated = _retry_fix(
            gated, light_client, violations,
            ai_gate_doc=ai_gate_doc, voice_print=voice_print,
        )
        post_retry = verify_draft(gated)
        if post_retry:
            log.info(
                "%d violations remain after retry, hard cleanup will fix...",
                len(post_retry),
            )

    # Hard cleanup (guaranteed backstop)
    log.info("Running hard cleanup...")
    gated = _hard_cleanup(gated)

    # Final verification
    final = verify_draft(gated)
    if final:
        log.warning(
            "UNEXPECTED: %d violations remain after hard cleanup: %s",
            len(final),
            [f"{v.category}:{v.matched}" for v in final[:10]],
        )

    return gated
