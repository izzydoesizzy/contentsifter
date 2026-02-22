"""Tests for contentsifter.parser.turns."""

from __future__ import annotations

from contentsifter.parser.turns import (
    extract_transcript_section,
    parse_speaker_turns,
    timestamp_to_seconds,
)


class TestTimestampToSeconds:
    def test_hhmmss(self):
        assert timestamp_to_seconds("01:30:45") == 5445

    def test_mmss(self):
        assert timestamp_to_seconds("05:30") == 330

    def test_zero(self):
        assert timestamp_to_seconds("00:00:00") == 0

    def test_invalid_returns_zero(self):
        assert timestamp_to_seconds("not-a-time") == 0

    def test_single_part_returns_zero(self):
        assert timestamp_to_seconds("123") == 0


class TestExtractTranscriptSection:
    def test_finds_transcript_header(self):
        text = "# Title\n\n**Date:** 2024-01-01\n\n## Transcript\n\nContent here."
        result = extract_transcript_section(text)
        assert result == "Content here."

    def test_no_header_returns_full_text(self):
        text = "Just some text without a transcript section."
        result = extract_transcript_section(text)
        assert result == text


class TestParseSpeakerTurns:
    def test_basic_turns(self):
        text = """\
## Transcript

{'speaker': {'display_name': 'Alice', 'matched_calendar_invitee_email': 'alice@example.com'}, 'text': 'Hello everyone!', 'timestamp': '00:00:05'}
{'speaker': {'display_name': 'Bob', 'matched_calendar_invitee_email': None}, 'text': 'Hi Alice!', 'timestamp': '00:00:10'}
"""
        turns = parse_speaker_turns(text)
        assert len(turns) == 2
        assert turns[0].speaker_name == "Alice"
        assert turns[0].speaker_email == "alice@example.com"
        assert turns[0].text == "Hello everyone!"
        assert turns[0].timestamp_seconds == 5
        assert turns[0].turn_index == 0
        assert turns[1].speaker_name == "Bob"
        assert turns[1].speaker_email is None
        assert turns[1].turn_index == 1

    def test_none_values_handled(self):
        """Python None should be handled by ast.literal_eval, not JSON."""
        text = """\
## Transcript

{'speaker': {'display_name': 'Alice', 'matched_calendar_invitee_email': None}, 'text': 'Test', 'timestamp': '00:01:00'}
"""
        turns = parse_speaker_turns(text)
        assert len(turns) == 1
        assert turns[0].speaker_email is None

    def test_skips_non_dict_lines(self):
        text = """\
## Transcript

Some random text
{'speaker': {'display_name': 'Alice', 'matched_calendar_invitee_email': None}, 'text': 'Valid', 'timestamp': '00:00:01'}
Another random line
"""
        turns = parse_speaker_turns(text)
        assert len(turns) == 1

    def test_empty_transcript(self):
        text = "## Transcript\n\n"
        assert parse_speaker_turns(text) == []

    def test_malformed_dict_skipped(self):
        """Malformed dicts that trigger ValueError/SyntaxError/KeyError are skipped."""
        text = """\
## Transcript

{'no_speaker_key': True}
{'speaker': {'display_name': 'Alice', 'matched_calendar_invitee_email': None}, 'text': 'Valid', 'timestamp': '00:00:01'}
"""
        turns = parse_speaker_turns(text)
        assert len(turns) == 1
        assert turns[0].speaker_name == "Alice"

    def test_string_speaker_causes_type_error(self):
        """When speaker is a string instead of dict, line should be skipped.

        Note: This currently raises TypeError which isn't caught by the parser.
        This test documents the current behavior.
        """
        text = """\
## Transcript

{'speaker': 'broken', 'text': 'hello', 'timestamp': '00:00:01'}
"""
        # Currently this raises TypeError because parser tries speaker["display_name"]
        # on a string. This is a known edge case.
        import pytest
        with pytest.raises(TypeError):
            parse_speaker_turns(text)

    def test_sequential_turn_indices(self):
        text = "## Transcript\n"
        for i in range(5):
            text += f"\n{{'speaker': {{'display_name': 'S{i}', 'matched_calendar_invitee_email': None}}, 'text': 'Turn {i}', 'timestamp': '00:0{i}:00'}}"
        turns = parse_speaker_turns(text)
        assert [t.turn_index for t in turns] == [0, 1, 2, 3, 4]
