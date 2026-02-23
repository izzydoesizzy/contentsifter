"""Shared utilities for ContentSifter web UI."""

from __future__ import annotations

import html as html_mod
import re


def simple_md_to_html(md: str) -> str:
    """Minimal markdown to HTML for preview. Not a full parser."""
    lines = md.split("\n")
    result = []
    in_list = False

    for line in lines:
        escaped = html_mod.escape(line)

        # Headings
        if escaped.startswith("## "):
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(f'<h2 class="text-lg font-semibold text-zinc-800 mt-6 mb-2">{escaped[3:]}</h2>')
        elif escaped.startswith("# "):
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(f'<h1 class="text-xl font-bold text-zinc-900 mb-3">{escaped[2:]}</h1>')
        elif escaped.startswith("---"):
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append('<hr class="my-4 border-zinc-200">')
        elif escaped.startswith("- ") or escaped.startswith("  - "):
            if not in_list:
                result.append('<ul class="list-disc list-inside space-y-1 ml-2">')
                in_list = True
            text = escaped.lstrip(" -")
            result.append(f"<li>{_inline_format(text)}</li>")
        elif re.match(r"^\d+\. ", escaped):
            text = re.sub(r"^\d+\. ", "", escaped)
            result.append(f'<p class="ml-4">{_inline_format(text)}</p>')
        elif escaped.strip():
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(f"<p>{_inline_format(escaped)}</p>")
        else:
            if in_list:
                result.append("</ul>")
                in_list = False

    if in_list:
        result.append("</ul>")

    return "\n".join(result)


def _inline_format(text: str) -> str:
    """Apply inline markdown formatting (bold, italic)."""
    # Bold: **text**
    text = re.sub(r"\*\*(.+?)\*\*", r'<strong class="font-semibold text-zinc-900">\1</strong>', text)
    # Italic: *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text
