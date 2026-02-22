"""Tests for contentsifter.interview.generator."""

from __future__ import annotations

from pathlib import Path

from contentsifter.interview.generator import (
    generate_questionnaire,
    _format_instructions,
    _format_category_section,
)
from contentsifter.interview.prompts import CATEGORIES, get_prompt_count


class TestFormatInstructions:
    def test_includes_client_name(self):
        result = _format_instructions("Jane Smith", 85)
        assert "Jane Smith" in result

    def test_includes_total_questions(self):
        result = _format_instructions(None, 85)
        assert "85" in result

    def test_includes_instructions(self):
        result = _format_instructions(None, 85)
        assert "Voice Capture Interview Guide" in result
        assert "voice transcription" in result.lower() or "recording" in result.lower()


class TestFormatCategorySection:
    def test_basic_section(self):
        prompts = [
            {"question": "What do you do?", "follow_up": "How long?"},
            {"question": "Why?", "follow_up": None},
        ]
        meta = {"name": "Warmup", "description": "Easy questions", "order": 1}
        section, next_num = _format_category_section("warmup", meta, prompts, 1)
        assert "**Q1.**" in section
        assert "**Q2.**" in section
        assert "What do you do?" in section
        assert "Follow-up:" in section
        assert next_num == 3

    def test_numbering_starts_at_given(self):
        prompts = [{"question": "Test?", "follow_up": None}]
        meta = {"name": "Test", "description": "Desc", "order": 1}
        section, next_num = _format_category_section("test", meta, prompts, 10)
        assert "**Q10.**" in section
        assert next_num == 11

    def test_includes_category_header(self):
        prompts = [{"question": "Q?", "follow_up": None}]
        meta = {"name": "My Category", "description": "About this", "order": 3}
        section, _ = _format_category_section("test", meta, prompts, 1)
        assert "Part 3: My Category" in section
        assert "About this" in section


class TestGenerateQuestionnaire:
    def test_generates_markdown(self):
        markdown, saved = generate_questionnaire(client_name="Test")
        assert "# Voice Capture Interview Guide" in markdown
        assert "**Q1.**" in markdown
        assert saved is None  # No output_path given

    def test_saves_to_file(self, tmp_path):
        out = tmp_path / "guide.md"
        markdown, saved = generate_questionnaire(output_path=out)
        assert saved == out
        assert out.exists()
        assert out.read_text() == markdown

    def test_all_categories_present(self):
        markdown, _ = generate_questionnaire()
        for cat_meta in CATEGORIES.values():
            assert cat_meta["name"] in markdown

    def test_question_count_matches(self):
        markdown, _ = generate_questionnaire()
        count = get_prompt_count()
        # Last question should be Qn where n = count
        assert f"**Q{count}.**" in markdown

    def test_follow_ups_included(self):
        markdown, _ = generate_questionnaire()
        assert "Follow-up:" in markdown

    def test_closing_section(self):
        markdown, _ = generate_questionnaire()
        assert "You're Done!" in markdown

    def test_without_niche(self):
        """Without niche, no niche section should appear."""
        markdown, _ = generate_questionnaire()
        assert "Your Industry" not in markdown
