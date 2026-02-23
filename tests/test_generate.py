"""Tests for contentsifter.generate (drafts + templates)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from contentsifter.generate.drafts import format_source_material, _inject_voice_context
from contentsifter.generate.gates import (
    _hard_cleanup,
    verify_draft,
    _format_violations_for_llm,
    run_content_gates,
)
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
        assert result == "work. Life"

    def test_removes_en_dashes(self):
        result = _hard_cleanup("work – life")
        assert "–" not in result
        assert result == "work. Life"

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

    def test_replaces_banned_words(self):
        assert "use" in _hard_cleanup("You should utilize this tool.")
        assert "utilize" not in _hard_cleanup("You should utilize this tool.").lower()

    def test_replaces_banned_words_case_insensitive(self):
        result = _hard_cleanup("UTILIZE the framework.")
        assert "utilize" not in result.lower()
        assert "use" in result.lower()

    def test_replaces_banned_phrases(self):
        result = _hard_cleanup("In order to succeed, work hard.")
        assert "in order to" not in result.lower()
        assert "to succeed" in result.lower()

    def test_replaces_due_to_the_fact(self):
        result = _hard_cleanup("Due to the fact that it rained, we stayed in.")
        assert "due to the fact that" not in result.lower()
        assert "because" in result.lower()

    def test_removes_semicolons(self):
        result = _hard_cleanup("First point; second point")
        assert ";" not in result
        assert "." in result

    def test_replaces_connectors(self):
        result = _hard_cleanup("Furthermore, this is important.")
        assert "furthermore" not in result.lower()

    def test_phrase_before_word_ordering(self):
        """Phrase 'delve into' should become 'dig into', not 'dig into' from word swap."""
        result = _hard_cleanup("Let's delve into the topic.")
        assert "delve" not in result.lower()
        assert "dig into" in result.lower()

    def test_does_not_touch_context_dependent_words(self):
        """Words like 'landscape' and 'dynamic' are not in SAFE_WORD_SWAPS."""
        result = _hard_cleanup("The landscape of this area is beautiful.")
        assert "landscape" in result

    def test_hard_cleanup_then_verify_passes(self):
        """After hard cleanup, verify_draft should find zero violations for safe-swappable content."""
        dirty = (
            "Furthermore, you should utilize this robust framework.\n"
            "In order to succeed — leverage your network.\n"
            "**This is key**; the bottom line is clear 🚀"
        )
        result = _hard_cleanup(dirty)
        violations = verify_draft(result)
        # Filter to only violations that hard cleanup should fix
        fixable = [v for v in violations if v.category in ("char", "semicolon", "asterisk", "emoji")]
        assert fixable == [], f"Hard cleanup missed: {fixable}"


class TestVerifyDraft:
    def test_clean_draft_passes(self):
        assert verify_draft("This is a clean draft with no issues.") == []

    def test_detects_em_dash(self):
        violations = verify_draft("work — life balance")
        cats = [v.category for v in violations]
        assert "char" in cats

    def test_detects_en_dash(self):
        violations = verify_draft("work – life balance")
        cats = [v.category for v in violations]
        assert "char" in cats

    def test_detects_banned_word(self):
        violations = verify_draft("You should utilize this strategy.")
        matched = [v.matched for v in violations]
        assert "utilize" in matched

    def test_word_boundary_no_false_positive(self):
        """'dynamic' inside 'aerodynamic' should NOT trigger."""
        violations = verify_draft("The aerodynamic design is sleek.")
        matched = [v.matched for v in violations]
        # "dynamic" is not in BANNED_WORDS (it's context-dependent),
        # but even if it were, word boundary should prevent matching inside "aerodynamic"
        assert "aerodynamic" not in " ".join(matched)

    def test_detects_banned_phrase(self):
        violations = verify_draft("In today's competitive market, you need to stand out.")
        matched = [v.matched for v in violations]
        assert "in today's" in matched

    def test_detects_connector(self):
        violations = verify_draft("Furthermore, this approach works well.")
        matched = [v.matched for v in violations]
        assert "furthermore" in matched

    def test_detects_semicolon(self):
        violations = verify_draft("First point; second point.")
        cats = [v.category for v in violations]
        assert "semicolon" in cats

    def test_detects_asterisks(self):
        violations = verify_draft("This is **bold** text.")
        cats = [v.category for v in violations]
        assert "asterisk" in cats

    def test_detects_decorative_emoji(self):
        violations = verify_draft("Great job 🚀")
        cats = [v.category for v in violations]
        assert "emoji" in cats

    def test_preserves_checkmark_emoji(self):
        violations = verify_draft("✅ Do this\n❌ Not that")
        assert violations == []

    def test_case_insensitive(self):
        violations = verify_draft("UTILIZE your skills.")
        matched = [v.matched for v in violations]
        assert "utilize" in matched

    def test_multiple_violations_same_line(self):
        violations = verify_draft("Furthermore — utilize your robust network.")
        cats = [v.category for v in violations]
        assert "char" in cats
        assert "connector" in cats or "word" in cats

    def test_line_numbers(self):
        violations = verify_draft("Clean line.\nDirty line — with dash.")
        dash_viols = [v for v in violations if v.category == "char"]
        assert dash_viols[0].line_number == 2


class TestFormatViolations:
    def test_formats_violations(self):
        from contentsifter.generate.gates import Violation
        violations = [
            Violation("char", "—", 1),
            Violation("word", "utilize", 2),
        ]
        result = _format_violations_for_llm(violations)
        assert "MUST be fixed" in result
        assert "—" in result
        assert "utilize" in result

    def test_empty_violations(self):
        assert _format_violations_for_llm([]) == ""


class TestRunContentGatesRetry:
    """Test the verify-retry flow with mocked LLM clients."""

    def _make_llm(self, responses: list[str]):
        """Create a mock LLM that returns responses in sequence."""
        from contentsifter.llm.client import LLMResponse
        mock = MagicMock()
        side_effects = [
            LLMResponse(content=r, input_tokens=100, output_tokens=100, model="test")
            for r in responses
        ]
        mock.create.side_effect = side_effects
        return mock

    def test_no_retry_when_clean(self, monkeypatch):
        """If gates produce clean output, no retry happens."""
        call_count = 0

        def mock_complete(client, system, user, max_tokens):
            nonlocal call_count
            call_count += 1
            from contentsifter.llm.client import LLMResponse
            return LLMResponse(
                content="Clean output with no violations.",
                input_tokens=100, output_tokens=100, model="test",
            )

        monkeypatch.setattr("contentsifter.generate.gates.complete_with_retry", mock_complete)
        monkeypatch.setattr("contentsifter.generate.gates._create_light_client", lambda: None)

        result = run_content_gates(
            "Some draft.",
            llm_client=MagicMock(),
            voice_print="Match this voice.",
            ai_gate_doc="AI gate rules.",
        )
        # AI gate + voice gate = 2 calls. No retry.
        assert call_count == 2
        assert "Clean output" in result

    def test_retry_on_violations(self, monkeypatch):
        """If gates produce violations, one retry fires."""
        call_count = 0

        def mock_complete(client, system, user, max_tokens):
            nonlocal call_count
            call_count += 1
            from contentsifter.llm.client import LLMResponse
            if call_count <= 2:
                # AI gate and voice gate return dirty text
                return LLMResponse(
                    content="You should utilize this — it's robust.",
                    input_tokens=100, output_tokens=100, model="test",
                )
            else:
                # Retry returns cleaner text
                return LLMResponse(
                    content="You should use this. It's strong.",
                    input_tokens=100, output_tokens=100, model="test",
                )

        monkeypatch.setattr("contentsifter.generate.gates.complete_with_retry", mock_complete)
        monkeypatch.setattr("contentsifter.generate.gates._create_light_client", lambda: None)

        result = run_content_gates(
            "Some draft.",
            llm_client=MagicMock(),
            voice_print="Voice print.",
            ai_gate_doc="AI gate rules.",
        )
        # AI gate + voice gate + retry = 3 calls
        assert call_count == 3

    def test_hard_cleanup_catches_everything(self, monkeypatch):
        """Even if LLM retry fails, hard cleanup fixes safe-swappable violations."""
        def mock_complete(client, system, user, max_tokens):
            from contentsifter.llm.client import LLMResponse
            # LLM always returns dirty text
            return LLMResponse(
                content="Furthermore, utilize this robust framework — it's seamless.",
                input_tokens=100, output_tokens=100, model="test",
            )

        monkeypatch.setattr("contentsifter.generate.gates.complete_with_retry", mock_complete)
        monkeypatch.setattr("contentsifter.generate.gates._create_light_client", lambda: None)

        result = run_content_gates(
            "Some draft.",
            llm_client=MagicMock(),
            voice_print="Voice print.",
            ai_gate_doc="AI gate rules.",
        )
        # Hard cleanup should have fixed the safe-swappable items
        assert "—" not in result
        assert "utilize" not in result.lower()
        assert "furthermore" not in result.lower()
        assert "robust" not in result.lower()
        assert "seamless" not in result.lower()
