"""Auto-format uploaded content using Claude."""

from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)

FORMAT_PROMPTS = {
    "linkedin_post": {
        "system": (
            "You are a content formatting assistant. Your job is to take raw text that "
            "contains multiple LinkedIn posts and format them into a structured markdown file.\n\n"
            "Rules:\n"
            "- Separate each post with a line containing only `---`\n"
            "- Add frontmatter to each post: `title:` (first line summary) and `date:` (if detectable)\n"
            "- Preserve the original text exactly — do not rewrite or edit the content\n"
            "- If the text is a single post, just add the frontmatter header\n"
            "- Remove any obvious copy-paste artifacts (navigation text, ad text, etc.)"
        ),
    },
    "email": {
        "system": (
            "You are a content formatting assistant. Your job is to take raw text that "
            "contains email content and format it into structured markdown.\n\n"
            "Rules:\n"
            "- Separate each email with a line containing only `---`\n"
            "- Add frontmatter to each email: `title:` (subject line) and `date:` (if detectable)\n"
            "- Preserve the original text exactly — do not rewrite\n"
            "- Clean up any forwarding artifacts or email headers into the frontmatter"
        ),
    },
    "newsletter": {
        "system": (
            "You are a content formatting assistant. Format this newsletter content.\n\n"
            "Rules:\n"
            "- Ensure the file has `title:` and `date:` frontmatter at the top\n"
            "- Use `#` heading for the newsletter title if not already present\n"
            "- Preserve the original text exactly — do not rewrite"
        ),
    },
    "blog": {
        "system": (
            "You are a content formatting assistant. Format this blog post content.\n\n"
            "Rules:\n"
            "- Ensure the file has `title:` and `date:` frontmatter at the top\n"
            "- Use `#` heading for the post title if not already present\n"
            "- Preserve the original text exactly — do not rewrite"
        ),
    },
    "transcript": {
        "system": (
            "You are a content formatting assistant. Clean up this transcript.\n\n"
            "Rules:\n"
            "- Fix obvious transcription errors if identifiable\n"
            "- Add speaker labels if speakers are identifiable\n"
            "- Add `title:` and `date:` frontmatter if detectable\n"
            "- Preserve the original meaning exactly — do not add or remove content"
        ),
    },
}


def needs_formatting(text: str, content_type: str) -> bool:
    """Check if the text is already in the expected format for its content type."""
    if not text.strip():
        return False

    # Check for frontmatter (title: or date: at the top)
    has_frontmatter = bool(re.match(r"^(title|date|author):\s", text.strip(), re.IGNORECASE))
    # Check for markdown heading
    has_heading = bool(re.match(r"^#+\s", text.strip()))
    # Check for dividers
    has_dividers = bool(re.search(r"\n---+\n", text))

    if content_type in ("linkedin_post", "email"):
        # Multi-item formats should have dividers if there's enough content
        if has_dividers:
            return False
        # If short (single item) and has frontmatter, it's fine
        if has_frontmatter and len(text) < 2000:
            return False
        return True

    if content_type in ("newsletter", "blog"):
        # Single-item formats just need frontmatter or heading
        if has_frontmatter or has_heading:
            return False
        return True

    if content_type == "transcript":
        # Transcripts need frontmatter
        if has_frontmatter:
            return False
        return True

    # For "other" type, never auto-format
    return False


def auto_format_content(raw_text: str, content_type: str, llm_client) -> str:
    """Use Claude to reformat raw text into the expected structure.

    Returns the formatted text, or the original text if formatting fails.
    """
    if not llm_client:
        log.warning("No LLM client available for auto-formatting")
        return raw_text

    prompt_config = FORMAT_PROMPTS.get(content_type)
    if not prompt_config:
        log.info("No auto-format prompt for content type: %s", content_type)
        return raw_text

    try:
        from contentsifter.llm.client import complete_with_retry

        result = complete_with_retry(
            llm_client,
            system=prompt_config["system"],
            user=f"Format the following content:\n\n{raw_text}",
            max_tokens=8192,
        )

        formatted = result.content.strip()

        # Strip markdown code fences if present
        if formatted.startswith("```"):
            formatted = formatted.split("\n", 1)[1]
            formatted = formatted.rsplit("```", 1)[0].strip()

        return formatted

    except Exception as e:
        log.warning("Auto-format failed: %s", e)
        return raw_text
