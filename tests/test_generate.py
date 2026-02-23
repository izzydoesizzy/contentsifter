"""Tests for contentsifter.generate (drafts + templates)."""

from __future__ import annotations

import pytest

from contentsifter.generate.drafts import format_source_material, _inject_voice_context
from contentsifter.generate.gates import _hard_cleanup
from contentsifter.generate.templates import TEMPLATES


class TestTemplates:
    def test_all_nine_formats_exist(self):
        expected = {
            "linkedin", "newsletter", "thread", "playbook", "video-script",
            "carousel", "email-welcome", "email-weekly", "email-sales",
        }
        assert set(TEMPLATES.keys()) == expected

    def test_templates_have_system_and_user(self):
        for name, tmpl in TEMPLATES.items():
            assert "system" in tmpl, f"Template '{name}' missing 'system'"
            assert "user" in tmpl, f"Template '{name}' missing 'user'"

    def test_user_templates_have_placeholders(self):
        for name, tmpl in TEMPLATES.items():
            assert "{topic}" in tmpl["user"], f"Template '{name}' missing {{topic}} placeholder"
            assert "{source_material}" in tmpl["user"], f"Template '{name}' missing {{source_material}} placeholder"

    def test_system_prompts_have_voice_context(self):
        for name, tmpl in TEMPLATES.items():
            assert "{voice_context}" in tmpl["system"], f"Template '{name}' missing {{voice_context}} placeholder"


class TestFormatSourceMaterial:
    def test_basic_formatting(self):
        results = [
            {
                "title": "Test Title",
                "category": "qa",
                "content": "Test content here.",
                "raw_quote": "A direct quote",
                "tags": ["linkedin", "networking"],
            },
        ]
        output = format_source_material(results)
        assert "### Test Title [QA]" in output
        assert "Test content here." in output
        assert "A direct quote" in output
        assert "linkedin" in output

    def test_multiple_results_separated(self):
        results = [
            {"title": "First", "category": "qa", "content": "One", "tags": []},
            {"title": "Second", "category": "playbook", "content": "Two", "tags": []},
        ]
        output = format_source_material(results)
        assert "---" in output
        assert "First" in output
        assert "Second" in output

    def test_missing_raw_quote(self):
        results = [
            {"title": "No Quote", "category": "story", "content": "Content", "tags": []},
        ]
        output = format_source_material(results)
        assert "Direct quote" not in output

    def test_empty_results(self):
        assert format_source_material([]) == ""


class TestInjectVoiceContext:
    def test_with_placeholder(self):
        system = "Write content.{voice_context}"
        result = _inject_voice_context(system, "Voice print data here")
        assert "Voice print data here" in result
        assert "{voice_context}" not in result

    def test_without_placeholder_appends(self):
        system = "Write content."
        result = _inject_voice_context(system, "Voice data")
        assert "Voice data" in result

    def test_no_voice_print(self):
        system = "Write content.{voice_context}"
        result = _inject_voice_context(system, None)
        assert "{voice_context}" not in result
        assert "voice" not in result.lower() or "voice_context" not in result


class TestHardCleanup:
    def test_removes_em_dashes(self):
        result = _hard_cleanup("work — life")
        assert "—" not in result
        assert "work" in result and "life" in result

    def test_removes_en_dashes(self):
        result = _hard_cleanup("work – life")
        assert "–" not in result
        assert "work" in result and "life" in result

    def test_no_double_periods(self):
        result = _hard_cleanup("end.— start")
        assert ".." not in result

    def test_strips_bold_asterisks(self):
        assert _hard_cleanup("this is **important**") == "this is important"

    def test_strips_italic_asterisks(self):
        assert _hard_cleanup("this is *important*") == "this is important"

    def test_strips_bold_italic_asterisks(self):
        assert _hard_cleanup("***wow***") == "wow"

    def test_removes_decorative_emoji(self):
        result = _hard_cleanup("Great job 🚀💪✨🔥")
        assert "🚀" not in result
        assert "💪" not in result
        assert "✨" not in result
        assert "🔥" not in result

    def test_preserves_checkmark_and_x_emoji(self):
        result = _hard_cleanup("✅ Good\n❌ Bad")
        assert "✅" in result
        assert "❌" in result

    def test_collapses_extra_whitespace(self):
        assert "a b" in _hard_cleanup("a     b")

    def test_collapses_extra_newlines(self):
        result = _hard_cleanup("a\n\n\n\n\nb")
        assert "\n\n\n" not in result
        assert "a\n\nb" == result

    def test_full_draft_cleanup(self):
        draft = "**5 Tips** for your career 💪\n\nFirst — know yourself.\nSecond — network 🚀.\n\n\n\n✅ Do this\n❌ Not that"
        result = _hard_cleanup(draft)
        assert "**" not in result
        assert "—" not in result
        assert "💪" not in result
        assert "🚀" not in result
        assert "✅" in result
        assert "❌" in result
        assert "\n\n\n" not in result
