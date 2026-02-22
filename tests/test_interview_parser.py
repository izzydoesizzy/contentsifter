"""Tests for contentsifter.interview.parser."""

from __future__ import annotations

from pathlib import Path

from contentsifter.interview.parser import (
    MIN_ANSWER_CHARS,
    _fuzzy_find,
    _skip_question_text,
    extract_questions_from_questionnaire,
    match_questions_in_transcript,
)


class TestExtractQuestionsFromQuestionnaire:
    def test_basic_extraction(self, tmp_path):
        guide = tmp_path / "guide.md"
        guide.write_text("""\
# Interview Guide

## Part 1: Warmup

**Q1.** What's your name?

**Q2.** What do you do for a living?

**Q3.** How did you get into this field?
""")
        questions = extract_questions_from_questionnaire(guide)
        assert len(questions) == 3
        assert questions[0]["q_number"] == 1
        assert questions[0]["question"] == "What's your name?"
        assert questions[2]["q_number"] == 3

    def test_follow_up_in_full_text(self, tmp_path):
        guide = tmp_path / "guide.md"
        guide.write_text("""\
**Q1.** What's your biggest achievement?
  - *Follow-up: How long did it take?*

**Q2.** Next question?
""")
        questions = extract_questions_from_questionnaire(guide)
        assert len(questions) == 2
        # First line only goes into question
        assert "biggest achievement" in questions[0]["question"]
        # Full text includes follow-up
        assert "Follow-up" in questions[0]["full_text"]

    def test_empty_file(self, tmp_path):
        guide = tmp_path / "empty.md"
        guide.write_text("# Empty Guide\n\nNo questions here.")
        assert extract_questions_from_questionnaire(guide) == []


class TestMatchQuestionsInTranscript:
    def test_marker_matching(self):
        transcript = """\
OK let's start. Q1 What's your name? My name is Jane Smith and I work in tech.

Q2 What do you do? I help companies build better software teams.
"""
        questions = [
            {"q_number": 1, "question": "What's your name?"},
            {"q_number": 2, "question": "What do you do?"},
        ]
        matches = match_questions_in_transcript(transcript, questions)
        assert len(matches) >= 1

    def test_question_number_marker(self):
        transcript = "Question 1 tell me about yourself. I'm a software engineer with 10 years of experience."
        questions = [{"q_number": 1, "question": "Tell me about yourself"}]
        matches = match_questions_in_transcript(transcript, questions)
        assert len(matches) == 1

    def test_no_matches_returns_empty(self):
        transcript = "This transcript has no question markers at all."
        questions = [{"q_number": 1, "question": "Completely different question?"}]
        matches = match_questions_in_transcript(transcript, questions)
        assert matches == []

    def test_answers_between_questions(self):
        transcript = """\
Q1 What's your name? My name is Jane and I love working in technology. I've been in the field for ten years now.

Q2 What do you do? I write code and build software for startups.
"""
        questions = [
            {"q_number": 1, "question": "What's your name?"},
            {"q_number": 2, "question": "What do you do?"},
        ]
        matches = match_questions_in_transcript(transcript, questions)
        assert len(matches) >= 2
        # Second answer should contain "code" or "software"
        assert "code" in matches[1]["answer"].lower() or "software" in matches[1]["answer"].lower()

    def test_results_sorted_by_position(self):
        transcript = "Q2 second question answer two. Q1 first question answer one."
        questions = [
            {"q_number": 1, "question": "first question"},
            {"q_number": 2, "question": "second question"},
        ]
        matches = match_questions_in_transcript(transcript, questions)
        if len(matches) >= 2:
            assert matches[0]["start_pos"] < matches[1]["start_pos"]


class TestFuzzyFind:
    def test_exact_match(self):
        pos = _fuzzy_find("hello world", "hello world", threshold=0.5)
        assert pos is not None
        assert pos == 0

    def test_approximate_match(self):
        pos = _fuzzy_find("what is your name", "so whats your name then", threshold=0.5)
        assert pos is not None

    def test_no_match(self):
        pos = _fuzzy_find("completely different", "nothing related at all to this", threshold=0.8)
        assert pos is None

    def test_empty_needle(self):
        assert _fuzzy_find("", "some text") is None

    def test_empty_haystack(self):
        assert _fuzzy_find("needle", "") is None


class TestSkipQuestionText:
    def test_skips_past_question(self):
        transcript = "Q1 What's your name and what do you do for a living? My name is Jane."
        pos = _skip_question_text(transcript, 2, "What's your name and what do you do for a living?")
        assert pos > 2
        # Should be past the question
        remaining = transcript[pos:]
        assert "Jane" in remaining or pos > 20
