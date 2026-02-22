"""Tests for contentsifter.parser.metadata."""

from __future__ import annotations

from contentsifter.parser.metadata import (
    classify_call_type,
    extract_fathom_id,
    parse_metadata,
    parse_participants,
)


class TestClassifyCallType:
    def test_group_qa(self):
        assert classify_call_type("weekly-group-q-a-2024-03-15.md") == "group_qa"

    def test_coaching_call(self):
        assert classify_call_type("coaching-call-john-2024-01.md") == "coaching"

    def test_discovery(self):
        assert classify_call_type("introductory-discovery-call-2024.md") == "discovery"

    def test_workshop_types(self):
        assert classify_call_type("ask-a-recruiter-session.md") == "workshop"
        assert classify_call_type("career-storytelling-workshop.md") == "workshop"
        assert classify_call_type("notion-for-job-seekers.md") == "workshop"

    def test_body_doubling(self):
        assert classify_call_type("body-doubling-2024-03.md") == "body_doubling"

    def test_unknown(self):
        assert classify_call_type("random-meeting.md") == "other"

    def test_case_insensitive(self):
        assert classify_call_type("Weekly-Group-Q-A-2024.md") == "group_qa"


class TestExtractFathomId:
    def test_valid_id(self):
        assert extract_fathom_id("coaching-call_12345.md") == "12345"

    def test_long_id(self):
        assert extract_fathom_id("call_1234567890.md") == "1234567890"

    def test_no_id(self):
        assert extract_fathom_id("just-a-call.md") is None

    def test_short_number_not_matched(self):
        assert extract_fathom_id("call_123.md") is None


class TestParseParticipants:
    def test_basic_names(self):
        result = parse_participants("Alice, Bob, Charlie")
        assert len(result) == 3
        assert result[0].display_name == "Alice"
        assert result[0].is_coach is False

    def test_coach_detection_by_name(self):
        result = parse_participants(
            "Izzy Piyale-Sheard, Alice",
            coach_name="Izzy Piyale-Sheard",
        )
        assert result[0].is_coach is True
        assert result[1].is_coach is False

    def test_coach_detection_by_email(self):
        result = parse_participants(
            "izzy@joinclearcareer.com, alice@example.com",
            coach_email="izzy@joinclearcareer.com",
        )
        assert result[0].is_coach is True
        assert result[0].email == "izzy@joinclearcareer.com"

    def test_email_participant(self):
        result = parse_participants("user@example.com")
        assert result[0].email == "user@example.com"
        assert result[0].display_name is None

    def test_empty_string(self):
        assert parse_participants("") == []


class TestParseMetadata:
    def test_full_header(self):
        raw = """\
# coaching-call-2024-03-15_12345.md

# Weekly Q&A Session

**Date:** 2024-03-15
**ID:** 12345
**Participants:** Izzy Piyale-Sheard, Alice

## Transcript
"""
        meta = parse_metadata(raw, "merged_01.md", "coaching-call-2024-03-15_12345.md")
        assert meta.title == "Weekly Q&A Session"
        assert meta.call_date == "2024-03-15"
        assert meta.fathom_id == "12345"
        assert len(meta.participants) == 2

    def test_missing_date_returns_unknown(self):
        raw = "# Some Title\n\nNo date here."
        meta = parse_metadata(raw, "src.md", "test.md")
        assert meta.call_date == "unknown"

    def test_title_from_second_heading(self):
        raw = """\
# original-filename.md

# Human-Readable Title

Content.
"""
        meta = parse_metadata(raw, "src.md", "original-filename.md")
        assert meta.title == "Human-Readable Title"

    def test_fallback_title_to_filename(self):
        raw = "No headings at all, just text."
        meta = parse_metadata(raw, "src.md", "fallback.md")
        assert meta.title == "fallback.md"

    def test_call_type_from_filename(self):
        raw = "# Title\n"
        meta = parse_metadata(raw, "src.md", "weekly-group-q-a-2024.md")
        assert meta.call_type == "group_qa"
