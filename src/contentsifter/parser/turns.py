"""Parse speaker turn dict literals from transcript text."""

import ast
import logging
import re

from contentsifter.storage.models import SpeakerTurn

logger = logging.getLogger(__name__)

# Pattern to find the transcript section
TRANSCRIPT_HEADER = re.compile(r"^## Transcript\s*$", re.MULTILINE)


def timestamp_to_seconds(ts: str) -> int:
    """Convert HH:MM:SS timestamp to total seconds."""
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0


def extract_transcript_section(raw_text: str) -> str:
    """Extract the transcript portion from a call record."""
    match = TRANSCRIPT_HEADER.search(raw_text)
    if match:
        return raw_text[match.end() :].strip()
    return raw_text


def parse_speaker_turns(raw_text: str) -> list[SpeakerTurn]:
    """Parse speaker turn lines into structured SpeakerTurn objects.

    Each line is a Python dict literal like:
    {'speaker': {'display_name': 'Name', ...}, 'text': '...', 'timestamp': 'HH:MM:SS'}
    """
    transcript_text = extract_transcript_section(raw_text)
    turns = []

    for line in transcript_text.split("\n"):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue

        try:
            data = ast.literal_eval(line)
            speaker = data["speaker"]
            turns.append(
                SpeakerTurn(
                    turn_index=len(turns),
                    speaker_name=speaker["display_name"],
                    speaker_email=speaker.get("matched_calendar_invitee_email"),
                    text=data["text"],
                    timestamp=data["timestamp"],
                    timestamp_seconds=timestamp_to_seconds(data["timestamp"]),
                )
            )
        except (ValueError, SyntaxError, KeyError) as e:
            logger.debug(f"Skipping unparseable line: {e}")

    return turns
