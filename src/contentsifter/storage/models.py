"""Data models for ContentSifter."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SpeakerTurn:
    turn_index: int
    speaker_name: str
    speaker_email: Optional[str]
    text: str
    timestamp: str
    timestamp_seconds: int


@dataclass
class Participant:
    display_name: Optional[str]
    email: Optional[str]
    is_coach: bool = False


@dataclass
class CallMetadata:
    source_file: str
    original_filename: str
    fathom_id: Optional[str]
    title: str
    call_date: str  # YYYY-MM-DD
    call_type: str
    participants: list[Participant] = field(default_factory=list)


@dataclass
class RawCallRecord:
    source_file: str
    original_filename: str
    raw_text: str


@dataclass
class TopicChunk:
    chunk_index: int
    topic_title: str
    topic_summary: Optional[str]
    start_turn_index: int
    end_turn_index: int
    start_timestamp: Optional[str]
    end_timestamp: Optional[str]
    primary_speaker: Optional[str]


@dataclass
class Extraction:
    category: str  # "qa", "testimonial", "playbook", "story"
    title: str
    content: str
    raw_quote: Optional[str] = None
    speaker: Optional[str] = None
    context_note: Optional[str] = None
    quality_score: int = 0
    tags: list[str] = field(default_factory=list)


@dataclass
class SearchResult:
    extraction_id: int
    category: str
    title: str
    content: str
    raw_quote: Optional[str]
    quality_score: int
    tags: list[str]
    call_title: str
    call_date: str
    relevance_score: float = 0.0
