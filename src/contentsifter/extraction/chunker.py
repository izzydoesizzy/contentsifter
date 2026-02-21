"""Topic segmentation of coaching call transcripts."""

from __future__ import annotations

import json
import logging
import re

from contentsifter.extraction.prompts import (
    CHUNKING_SYSTEM_PROMPT,
    CHUNKING_USER_PROMPT,
    format_turns_compact,
)
from contentsifter.llm.client import complete_with_retry
from contentsifter.storage.models import TopicChunk

logger = logging.getLogger(__name__)


def _extract_json_array(text: str) -> list:
    """Extract a JSON array from text, handling markdown code fences."""
    # Strip markdown code fences if present
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    # Find the JSON array
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in response: {text[:200]}")

    return json.loads(text[start : end + 1])


def chunk_transcript(
    call_id: int,
    call_title: str,
    call_date: str,
    call_type: str,
    turns: list[dict],
    llm_client,
) -> list[TopicChunk]:
    """Identify topic segments in a transcript using Claude.

    Sends the full transcript (in compact format) and gets back
    a list of topic segments with turn index boundaries.
    """
    formatted = format_turns_compact(turns)

    # Check if the formatted text is too large (>600K chars ≈ 150K tokens)
    if len(formatted) > 600_000:
        logger.warning(
            f"Call {call_id} transcript is very large ({len(formatted)} chars). "
            "Using windowed chunking."
        )
        return _chunk_large_transcript(
            call_id, call_title, call_date, call_type, turns, llm_client
        )

    response = complete_with_retry(
        llm_client,
        system=CHUNKING_SYSTEM_PROMPT,
        user=CHUNKING_USER_PROMPT.format(
            call_type=call_type,
            title=call_title,
            date=call_date,
            transcript=formatted,
        ),
    )

    return _parse_chunks(response.content, turns)


def _parse_chunks(response_text: str, turns: list[dict]) -> list[TopicChunk]:
    """Parse the Claude chunking response into TopicChunk objects."""
    try:
        segments = _extract_json_array(response_text)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse chunking response: {e}")
        # Fallback: treat entire transcript as one chunk
        return [
            TopicChunk(
                chunk_index=0,
                topic_title="Full Conversation",
                topic_summary="Entire call as single segment (chunking failed)",
                start_turn_index=0,
                end_turn_index=len(turns) - 1,
                start_timestamp=turns[0]["timestamp"] if turns else None,
                end_timestamp=turns[-1]["timestamp"] if turns else None,
                primary_speaker="multiple",
            )
        ]

    chunks = []
    for i, seg in enumerate(segments):
        start_idx = seg.get("start_turn", 0)
        end_idx = seg.get("end_turn", len(turns) - 1)

        # Find timestamps for the boundaries
        start_ts = None
        end_ts = None
        for t in turns:
            if t["turn_index"] == start_idx:
                start_ts = t["timestamp"]
            if t["turn_index"] == end_idx:
                end_ts = t["timestamp"]

        chunks.append(
            TopicChunk(
                chunk_index=i,
                topic_title=seg.get("topic_title", f"Segment {i + 1}"),
                topic_summary=seg.get("summary"),
                start_turn_index=start_idx,
                end_turn_index=end_idx,
                start_timestamp=start_ts,
                end_timestamp=end_ts,
                primary_speaker=seg.get("primary_speaker"),
            )
        )

    return chunks


def _chunk_large_transcript(
    call_id: int,
    call_title: str,
    call_date: str,
    call_type: str,
    turns: list[dict],
    llm_client,
) -> list[TopicChunk]:
    """Handle transcripts too large for a single API call.

    Uses a sliding window approach with overlap.
    """
    window_size = 500  # turns per window
    overlap = 50
    all_chunks = []
    offset = 0
    chunk_counter = 0

    while offset < len(turns):
        window = turns[offset : offset + window_size]
        formatted = format_turns_compact(window)

        response = complete_with_retry(
            llm_client,
            system=CHUNKING_SYSTEM_PROMPT,
            user=CHUNKING_USER_PROMPT.format(
                call_type=call_type,
                title=call_title,
                date=call_date,
                transcript=formatted,
            ),
        )

        window_chunks = _parse_chunks(response.content, window)
        for chunk in window_chunks:
            chunk.chunk_index = chunk_counter
            chunk_counter += 1
            all_chunks.append(chunk)

        offset += window_size - overlap

    return all_chunks
