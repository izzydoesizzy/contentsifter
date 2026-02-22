"""Tests for contentsifter.generate (drafts + templates)."""

from __future__ import annotations

import pytest

from contentsifter.generate.drafts import format_source_material, _inject_voice_context
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
