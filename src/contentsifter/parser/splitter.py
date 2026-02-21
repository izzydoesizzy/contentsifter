"""Split merged markdown files into individual call records."""

import re
from pathlib import Path

from contentsifter.storage.models import RawCallRecord

# Pattern to match the SOURCE FILE markers
SPLIT_PATTERN = re.compile(
    r"<!-- =+ -->\s*\n"
    r"<!-- SOURCE FILE: (.+?) -->\s*\n"
    r"<!-- =+ -->",
)


def split_merged_file(filepath: Path) -> list[RawCallRecord]:
    """Split a merged markdown file into individual call records.

    Each section between <!-- SOURCE FILE --> markers becomes one record.
    """
    text = filepath.read_text(encoding="utf-8")
    markers = list(SPLIT_PATTERN.finditer(text))

    if not markers:
        return []

    records = []
    for i, match in enumerate(markers):
        filename = match.group(1).strip()
        start = match.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        raw_text = text[start:end].strip()

        if raw_text:
            records.append(
                RawCallRecord(
                    source_file=filepath.name,
                    original_filename=filename,
                    raw_text=raw_text,
                )
            )

    return records


def split_all_files(directory: Path) -> list[RawCallRecord]:
    """Split all merged markdown files in a directory."""
    records = []
    for filepath in sorted(directory.glob("merged_*.md")):
        records.extend(split_merged_file(filepath))
    return records
