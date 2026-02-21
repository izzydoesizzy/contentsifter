"""Parse metadata headers from individual call records."""

import re
from typing import Optional

from contentsifter.config import CALL_TYPE_PATTERNS, COACH_EMAIL, COACH_NAME
from contentsifter.storage.models import CallMetadata, Participant

TITLE_PATTERN = re.compile(r"^# (.+?)$", re.MULTILINE)
DATE_PATTERN = re.compile(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})")
ID_PATTERN = re.compile(r"\*\*ID:\*\*\s*(\d+)")
PARTICIPANTS_PATTERN = re.compile(r"\*\*Participants:\*\*\s*(.+)")


def classify_call_type(filename: str) -> str:
    """Determine call type from the original filename."""
    lower = filename.lower()
    for pattern, call_type in CALL_TYPE_PATTERNS.items():
        if pattern in lower:
            return call_type
    return "other"


def parse_participants(raw: str) -> list[Participant]:
    """Parse the participants string into Participant objects."""
    participants = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue

        is_coach = (
            COACH_NAME.lower() in part.lower() or COACH_EMAIL.lower() in part.lower()
        )

        # Check if it looks like an email
        if "@" in part:
            participants.append(
                Participant(display_name=None, email=part, is_coach=is_coach)
            )
        else:
            participants.append(
                Participant(display_name=part, email=None, is_coach=is_coach)
            )

    return participants


def extract_fathom_id(filename: str) -> Optional[str]:
    """Extract the numeric Fathom ID from the filename."""
    match = re.search(r"_(\d{5,})\.md$", filename)
    return match.group(1) if match else None


def parse_metadata(raw_text: str, source_file: str, original_filename: str) -> CallMetadata:
    """Extract structured metadata from a call record's header."""
    # Find all titles (first is filename, second is human-readable)
    titles = TITLE_PATTERN.findall(raw_text)
    title = titles[1] if len(titles) > 1 else titles[0] if titles else original_filename

    date_match = DATE_PATTERN.search(raw_text)
    call_date = date_match.group(1) if date_match else "unknown"

    id_match = ID_PATTERN.search(raw_text)
    fathom_id = id_match.group(1) if id_match else extract_fathom_id(original_filename)

    participants_match = PARTICIPANTS_PATTERN.search(raw_text)
    participants = (
        parse_participants(participants_match.group(1))
        if participants_match
        else []
    )

    call_type = classify_call_type(original_filename)

    return CallMetadata(
        source_file=source_file,
        original_filename=original_filename,
        fathom_id=fathom_id,
        title=title,
        call_date=call_date,
        call_type=call_type,
        participants=participants,
    )
