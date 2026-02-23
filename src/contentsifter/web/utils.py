"""Shared utilities for ContentSifter web UI."""

from __future__ import annotations

import html as html_mod
import re


def simple_md_to_html(md: str) -> str:
    """Minimal markdown to HTML for preview. Not a full parser.

    Supports: headings, lists, tables, blockquotes, bold/italic,
    horizontal rules, and paragraph spacing.
    """
    lines = md.split("\n")
    result: list[str] = []
    in_list = False
    in_table = False
    in_blockquote = False
    table_has_header = False

    for line in lines:
        stripped = line.rstrip()
        escaped = html_mod.escape(stripped)

        # --- Close open blocks if line type changes ---

        # Table: detect by leading |
        is_table_line = escaped.startswith("|") and escaped.endswith("|")
        is_separator = is_table_line and re.match(
            r"^\|[\s\-:|]+\|$", escaped
        )

        if in_table and not is_table_line:
            result.append("</tbody></table></div>")
            in_table = False
            table_has_header = False

        if in_blockquote and not escaped.startswith("&gt; ") and escaped.strip():
            result.append("</blockquote>")
            in_blockquote = False

        # --- Parse line ---

        # Headings (### before ## before #)
        if escaped.startswith("### "):
            _close_list(result, in_list)
            in_list = False
            text = escaped[4:]
            slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            result.append(
                f'<h3 id="{slug}" class="text-base font-semibold text-zinc-800 mt-5 mb-2">'
                f"{_inline_format(text)}</h3>"
            )
        elif escaped.startswith("## "):
            _close_list(result, in_list)
            in_list = False
            text = escaped[3:]
            slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            result.append(
                f'<h2 id="{slug}" class="text-lg font-semibold text-zinc-800 mt-8 mb-3">'
                f"{_inline_format(text)}</h2>"
            )
        elif escaped.startswith("# "):
            _close_list(result, in_list)
            in_list = False
            text = escaped[2:]
            slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            result.append(
                f'<h1 id="{slug}" class="text-xl font-bold text-zinc-900 mb-4">'
                f"{_inline_format(text)}</h1>"
            )

        # Horizontal rule
        elif re.match(r"^-{3,}$", escaped):
            _close_list(result, in_list)
            in_list = False
            result.append('<hr class="my-6 border-zinc-200">')

        # Table separator row (skip — already handled header)
        elif is_separator:
            table_has_header = True

        # Table rows
        elif is_table_line:
            cells = [c.strip() for c in escaped.split("|")[1:-1]]
            if not in_table:
                result.append(
                    '<div class="overflow-x-auto my-4">'
                    '<table class="prose-table">'
                )
                # First row is always the header
                result.append("<thead><tr>")
                for cell in cells:
                    result.append(f"<th>{_inline_format(cell)}</th>")
                result.append("</tr></thead><tbody>")
                in_table = True
            elif table_has_header or not any(
                c.strip() == "---" or re.match(r"^[-:]+$", c.strip())
                for c in cells
            ):
                result.append("<tr>")
                for cell in cells:
                    result.append(f"<td>{_inline_format(cell)}</td>")
                result.append("</tr>")

        # Blockquote
        elif escaped.startswith("&gt; "):
            _close_list(result, in_list)
            in_list = False
            text = escaped[5:]
            if not in_blockquote:
                result.append('<blockquote class="prose-blockquote">')
                in_blockquote = True
            result.append(f"<p>{_inline_format(text)}</p>")

        # Unordered list
        elif escaped.startswith("- ") or escaped.startswith("  - "):
            if not in_list:
                result.append(
                    '<ul class="list-disc list-inside space-y-1.5 ml-2 my-3 text-zinc-700">'
                )
                in_list = True
            text = escaped.lstrip(" -")
            result.append(f"<li>{_inline_format(text)}</li>")

        # Ordered list
        elif re.match(r"^\d+\. ", escaped):
            text = re.sub(r"^\d+\. ", "", escaped)
            result.append(
                f'<p class="ml-4 mb-1 text-zinc-700">{_inline_format(text)}</p>'
            )

        # Non-empty text → paragraph
        elif escaped.strip():
            _close_list(result, in_list)
            in_list = False
            result.append(
                f'<p class="mb-3 text-zinc-700 leading-relaxed">'
                f"{_inline_format(escaped)}</p>"
            )

        # Empty line
        else:
            _close_list(result, in_list)
            in_list = False

    # Close any remaining open blocks
    _close_list(result, in_list)
    if in_table:
        result.append("</tbody></table></div>")
    if in_blockquote:
        result.append("</blockquote>")

    return "\n".join(result)


def _close_list(result: list[str], in_list: bool) -> None:
    """Close an open <ul> if needed."""
    if in_list:
        result.append("</ul>")


def _inline_format(text: str) -> str:
    """Apply inline markdown formatting (bold, italic, code, links)."""
    # Code: `text`
    text = re.sub(
        r"`(.+?)`",
        r'<code class="px-1 py-0.5 bg-zinc-100 rounded text-sm font-mono">\1</code>',
        text,
    )
    # Bold: **text**
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r'<strong class="font-semibold text-zinc-900">\1</strong>',
        text,
    )
    # Italic: *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text
