"""Tests for contentsifter.search (keyword + filters)."""

from __future__ import annotations

from contentsifter.search.filters import SearchFilters
from contentsifter.search.keyword import keyword_search, search_raw_turns
from contentsifter.storage.repository import Repository


class TestSearchFilters:
    def test_empty_filters(self):
        f = SearchFilters()
        clause, params = f.to_sql_clauses()
        assert clause == ""
        assert params == []

    def test_category_filter(self):
        f = SearchFilters(categories=["qa", "playbook"])
        clause, params = f.to_sql_clauses()
        assert "e.category IN" in clause
        assert params == ["qa", "playbook"]

    def test_tag_filter(self):
        f = SearchFilters(tags=["linkedin"])
        clause, params = f.to_sql_clauses()
        assert "t.name IN" in clause
        assert params == ["linkedin"]

    def test_date_filters(self):
        f = SearchFilters(date_from="2024-01-01", date_to="2024-12-31")
        clause, params = f.to_sql_clauses()
        assert "c.call_date >=" in clause
        assert "c.call_date <=" in clause
        assert "2024-01-01" in params
        assert "2024-12-31" in params

    def test_quality_filter(self):
        f = SearchFilters(min_quality=4)
        clause, params = f.to_sql_clauses()
        assert "e.quality_score >= ?" in clause
        assert params == [4]

    def test_call_type_filter(self):
        f = SearchFilters(call_types=["group_qa"])
        clause, params = f.to_sql_clauses()
        assert "c.call_type IN" in clause

    def test_combined_filters(self):
        f = SearchFilters(categories=["qa"], min_quality=3, date_from="2024-01-01")
        clause, params = f.to_sql_clauses()
        # Should have 3 AND-separated clauses
        assert clause.count("AND") == 2
        assert len(params) == 3

    def test_default_limit(self):
        f = SearchFilters()
        assert f.limit == 20


class TestKeywordSearch:
    def test_basic_search(self, populated_db):
        db, call_id = populated_db
        results = keyword_search(db, "linkedin")
        assert len(results) >= 1
        assert any("linkedin" in r["title"].lower() or "linkedin" in r["content"].lower()
                    for r in results)

    def test_search_returns_tags(self, populated_db):
        db, _ = populated_db
        results = keyword_search(db, "linkedin")
        assert any(len(r["tags"]) > 0 for r in results)

    def test_search_with_category_filter(self, populated_db):
        db, _ = populated_db
        filters = SearchFilters(categories=["qa"])
        results = keyword_search(db, "linkedin", filters)
        assert all(r["category"] == "qa" for r in results)

    def test_search_with_quality_filter(self, populated_db):
        db, _ = populated_db
        filters = SearchFilters(min_quality=5)
        results = keyword_search(db, "linkedin", filters)
        assert all(r["quality_score"] >= 5 for r in results)

    def test_search_no_results(self, populated_db):
        db, _ = populated_db
        results = keyword_search(db, "xyznonexistent")
        assert results == []

    def test_search_with_limit(self, populated_db):
        db, _ = populated_db
        filters = SearchFilters(limit=1)
        results = keyword_search(db, "linkedin", filters)
        assert len(results) <= 1


class TestSearchRawTurns:
    def test_search_turns(self, populated_db):
        db, _ = populated_db
        results = search_raw_turns(db, "headline")
        assert len(results) >= 1
        assert results[0]["speaker_name"] is not None

    def test_search_turns_empty(self, populated_db):
        db, _ = populated_db
        results = search_raw_turns(db, "xyznonexistent")
        assert results == []
