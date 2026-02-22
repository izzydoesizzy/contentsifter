"""Format-specific content file parsers."""

from __future__ import annotations

import re
from pathlib import Path


def parse_content_file(filepath: Path, content_type: str) -> list[dict]:
    """Parse a content file into individual content items.

    For most types, items are separated by --- dividers.
    Each item can optionally have YAML-like frontmatter (key: value lines at the top).
    """
    text = filepath.read_text()

    if content_type == "newsletter":
        # Each file is one newsletter
        return [_parse_single_item(text, content_type, filepath)]

    if content_type == "blog":
        # Each file is one blog post
        return [_parse_single_item(text, content_type, filepath)]

    # For linkedin_post, email, other: split on --- dividers
    sections = _split_on_dividers(text)

    items = []
    for section in sections:
        section = section.strip()
        if not section or len(section) < 10:
            continue
        items.append(_parse_single_item(section, content_type, filepath))

    return items


def _split_on_dividers(text: str) -> list[str]:
    """Split text on --- or *** line dividers."""
    # Match lines that are only ---, ***, or === (3+ chars)
    parts = re.split(r"\n\s*(?:---+|===+|\*\*\*+)\s*\n", text)
    return [p for p in parts if p.strip()]


def _parse_single_item(text: str, content_type: str, filepath: Path) -> dict:
    """Parse a single content item, extracting optional frontmatter."""
    lines = text.strip().split("\n")
    metadata = {}
    content_start = 0

    # Check for frontmatter-style key: value pairs at the top
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            content_start = i + 1
            break
        match = re.match(r"^(date|title|author|url|type|engagement|platform):\s*(.+)$", stripped, re.IGNORECASE)
        if match:
            metadata[match.group(1).lower()] = match.group(2).strip()
            content_start = i + 1
        else:
            break

    body = "\n".join(lines[content_start:]).strip()

    # If no body after frontmatter extraction, use the full text
    if not body:
        body = text.strip()
        metadata = {}

    # Extract title from first # heading if not in frontmatter
    title = metadata.pop("title", None)
    if not title:
        heading_match = re.match(r"^#+ (.+)$", body, re.MULTILINE)
        if heading_match:
            title = heading_match.group(1).strip()
        else:
            # Use first line (truncated) as title
            first_line = body.split("\n")[0].strip()
            title = first_line[:80] + ("..." if len(first_line) > 80 else "")

    return {
        "content_type": content_type,
        "title": title,
        "text": body,
        "date": metadata.pop("date", None),
        "author": metadata.pop("author", None),
        "metadata": metadata if metadata else None,
    }
