"""Tests for contentsifter.interview.prompts."""

from __future__ import annotations

from contentsifter.interview.prompts import (
    CATEGORIES,
    PROMPT_LIBRARY,
    get_all_prompts,
    get_category_counts,
    get_prompt_count,
    get_prompts_by_category,
)


class TestPromptLibrary:
    def test_all_prompts_have_required_fields(self):
        required = {"id", "category", "question", "framework", "content_type", "estimated_minutes", "tags"}
        for prompt in PROMPT_LIBRARY:
            missing = required - set(prompt.keys())
            assert not missing, f"Prompt {prompt.get('id', '?')} missing fields: {missing}"

    def test_all_categories_in_library(self):
        used_categories = {p["category"] for p in PROMPT_LIBRARY}
        for cat_key in CATEGORIES:
            assert cat_key in used_categories, f"Category '{cat_key}' has no prompts"

    def test_prompt_ids_unique(self):
        ids = [p["id"] for p in PROMPT_LIBRARY]
        assert len(ids) == len(set(ids)), "Duplicate prompt IDs found"

    def test_valid_content_types(self):
        valid = {"qa", "playbook", "story", "testimonial"}
        for p in PROMPT_LIBRARY:
            assert p["content_type"] in valid, f"Prompt {p['id']} has invalid content_type: {p['content_type']}"

    def test_questions_are_nonempty(self):
        for p in PROMPT_LIBRARY:
            assert len(p["question"]) > 10, f"Prompt {p['id']} has empty/short question"


class TestCategories:
    def test_category_fields(self):
        required = {"name", "description", "estimated_minutes", "order"}
        for key, meta in CATEGORIES.items():
            missing = required - set(meta.keys())
            assert not missing, f"Category '{key}' missing: {missing}"

    def test_category_order_unique(self):
        orders = [meta["order"] for meta in CATEGORIES.values()]
        assert len(orders) == len(set(orders)), "Duplicate category orders"

    def test_nine_categories(self):
        assert len(CATEGORIES) == 9


class TestAccessFunctions:
    def test_get_all_prompts_returns_list(self):
        prompts = get_all_prompts()
        assert isinstance(prompts, list)
        assert len(prompts) == len(PROMPT_LIBRARY)

    def test_get_all_prompts_sorted_by_category_order(self):
        prompts = get_all_prompts()
        category_order = {k: v["order"] for k, v in CATEGORIES.items()}
        orders = [category_order[p["category"]] for p in prompts]
        assert orders == sorted(orders)

    def test_get_prompts_by_category(self):
        warmup = get_prompts_by_category("warmup")
        assert all(p["category"] == "warmup" for p in warmup)
        assert len(warmup) > 0

    def test_get_prompts_by_unknown_category(self):
        result = get_prompts_by_category("nonexistent")
        assert result == []

    def test_get_prompt_count(self):
        count = get_prompt_count()
        assert count == len(PROMPT_LIBRARY)
        assert count >= 80  # Should have at least 80 prompts

    def test_get_category_counts(self):
        counts = get_category_counts()
        assert isinstance(counts, dict)
        total = sum(counts.values())
        assert total == len(PROMPT_LIBRARY)
        assert "warmup" in counts
        assert "origin_story" in counts
