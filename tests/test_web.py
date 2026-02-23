"""Tests for ContentSifter web UI."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from contentsifter.storage.database import Database


@pytest.fixture
def web_env(tmp_path, monkeypatch):
    """Set up isolated environment for web tests."""
    import contentsifter.config as config_mod

    db_path = str(tmp_path / "data" / "contentsifter.db")
    content_dir = str(tmp_path / "content")
    registry = {
        "default": "testweb",
        "clients": {
            "testweb": {
                "name": "Web Test",
                "email": "test@example.com",
                "description": "Web testing",
                "db_path": db_path,
                "content_dir": content_dir,
            },
        },
    }
    clients_json = tmp_path / "clients.json"
    clients_json.write_text(json.dumps(registry))

    monkeypatch.setattr(config_mod, "CLIENTS_JSON_PATH", clients_json)
    monkeypatch.setattr(config_mod, "PROJECT_ROOT", tmp_path)

    return tmp_path


@pytest.fixture
def client(web_env):
    """Create a test client for the web app."""
    from contentsifter.web.app import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture
def web_env_with_db(web_env):
    """Web env with an initialized database."""
    db_path = Path(web_env / "data" / "contentsifter.db")
    with Database(db_path) as db:
        pass
    return web_env


@pytest.fixture
def client_with_db(web_env_with_db):
    """Test client with initialized database."""
    from contentsifter.web.app import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture
def web_env_with_extractions(web_env):
    """Web env with database containing test calls, extractions, and tags."""
    db_path = Path(web_env / "data" / "contentsifter.db")
    with Database(db_path) as db:
        db.conn.execute(
            "INSERT INTO calls (id, source_file, original_filename, title, call_date, call_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (1, "test.md", "test.md", "Test Call", "2025-01-15", "group_qa"),
        )
        db.conn.execute(
            "INSERT INTO extractions (id, call_id, category, title, content, raw_quote, speaker, quality_score) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (1, 1, "playbook", "Networking Tips", "Build relationships first.", "Just build relationships.", "Izzy", 4),
        )
        db.conn.execute(
            "INSERT INTO extractions (id, call_id, category, title, content, raw_quote, speaker, quality_score) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (2, 1, "qa", "Resume Question", "Use action verbs.", "Always use action verbs.", "Izzy", 3),
        )
        db.conn.execute("INSERT INTO tags (id, name) VALUES (?, ?)", (1, "networking"))
        db.conn.execute("INSERT INTO tags (id, name) VALUES (?, ?)", (2, "resume"))
        db.conn.execute("INSERT INTO extraction_tags (extraction_id, tag_id) VALUES (?, ?)", (1, 1))
        db.conn.execute("INSERT INTO extraction_tags (extraction_id, tag_id) VALUES (?, ?)", (2, 2))
        # Index for FTS
        db.conn.execute(
            "INSERT INTO extractions_fts (rowid, title, content, raw_quote, context_note) VALUES (?, ?, ?, ?, ?)",
            (1, "Networking Tips", "Build relationships first.", "Just build relationships.", ""),
        )
        db.conn.execute(
            "INSERT INTO extractions_fts (rowid, title, content, raw_quote, context_note) VALUES (?, ?, ?, ?, ?)",
            (2, "Resume Question", "Use action verbs.", "Always use action verbs.", ""),
        )
        db.conn.commit()
    return web_env


@pytest.fixture
def client_with_extractions(web_env_with_extractions):
    """Test client with database containing extractions."""
    from contentsifter.web.app import create_app

    app = create_app()
    return TestClient(app)


class TestDashboard:
    def test_root_redirects(self, client):
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/testweb" in resp.headers["location"]

    def test_dashboard_loads(self, client_with_db):
        resp = client_with_db.get("/testweb")
        assert resp.status_code == 200
        assert "Web Test" in resp.text
        assert "Dashboard" in resp.text

    def test_dashboard_unknown_client_redirects(self, client):
        resp = client.get("/nonexistent", follow_redirects=False)
        assert resp.status_code == 302


class TestClients:
    def test_clients_list(self, client):
        resp = client.get("/clients/")
        assert resp.status_code == 200
        assert "testweb" in resp.text
        assert "Web Test" in resp.text

    def test_create_client(self, client):
        resp = client.post("/clients/", data={
            "slug": "newclient",
            "name": "New Client",
            "email": "new@example.com",
            "description": "A new one",
        }, follow_redirects=False)
        assert resp.status_code == 303

    def test_create_client_htmx(self, client):
        resp = client.post("/clients/", data={
            "slug": "htmxclient",
            "name": "Htmx Client",
            "email": "",
            "description": "",
        }, headers={"HX-Request": "true"})
        assert resp.status_code == 200
        assert "Htmx Client" in resp.text

    def test_create_duplicate_client_htmx(self, client):
        resp = client.post("/clients/", data={
            "slug": "testweb",
            "name": "Duplicate",
            "email": "",
            "description": "",
        }, headers={"HX-Request": "true"})
        assert resp.status_code == 200
        assert "already exists" in resp.text

    def test_client_detail(self, client_with_db):
        resp = client_with_db.get("/clients/testweb")
        assert resp.status_code == 200
        assert "Web Test" in resp.text

    def test_set_default(self, client):
        # Create a second client first
        client.post("/clients/", data={
            "slug": "second",
            "name": "Second",
            "email": "",
            "description": "",
        }, follow_redirects=False)
        resp = client.post("/clients/second/default", follow_redirects=False)
        assert resp.status_code == 303


class TestIngest:
    def test_ingest_page_loads(self, client_with_db):
        resp = client_with_db.get("/testweb/ingest")
        assert resp.status_code == 200
        assert "Upload Content" in resp.text

    def test_upload_file(self, client_with_db):
        content = b"title: Test Post\n\nThis is test content for upload."
        resp = client_with_db.post(
            "/testweb/ingest/upload",
            files={"file": ("test.md", content, "text/markdown")},
            data={"content_type": "blog", "auto_format": "false"},
        )
        assert resp.status_code == 200
        assert "Ingested" in resp.text

    def test_upload_invalid_encoding(self, client_with_db):
        resp = client_with_db.post(
            "/testweb/ingest/upload",
            files={"file": ("test.bin", b"\xff\xfe\x00\x01", "application/octet-stream")},
            data={"content_type": "other", "auto_format": "false"},
        )
        assert resp.status_code == 200
        assert "Unable to read" in resp.text

    def test_recent_items(self, client_with_db):
        resp = client_with_db.get("/testweb/ingest/recent")
        assert resp.status_code == 200


class TestInterview:
    def test_interview_page_loads(self, client_with_db):
        resp = client_with_db.get("/testweb/interview")
        assert resp.status_code == 200
        assert "Interview" in resp.text

    def test_generate_questionnaire(self, client_with_db, web_env_with_db):
        # Ensure content dir exists
        content_dir = web_env_with_db / "content"
        content_dir.mkdir(parents=True, exist_ok=True)
        resp = client_with_db.post(
            "/testweb/interview/generate",
            data={"niche": ""},
        )
        assert resp.status_code == 200
        assert "generated" in resp.text.lower()

    def test_interview_preview_no_guide(self, client_with_db):
        resp = client_with_db.get("/testweb/interview/preview")
        assert resp.status_code == 200
        assert "No questionnaire" in resp.text


class TestInterviewPreview:
    def test_parse_questionnaire_sections(self):
        from contentsifter.web.routes.interview import _parse_questionnaire
        md = (
            "# Interview Guide\n\n## How to Use This Guide\nStuff\n\n---\n\n"
            "## Part 1: Warmup\n*Easy questions.*\n\n"
            "**Q1.** What is your name?\n\n"
            "**Q2.** What do you do?\n"
            "  - *Follow-up: What reaction do you get?*\n\n---\n\n"
            "## Part 2: Origin\n*Your journey.*\n\n"
            "**Q3.** How did you start?\n"
            "  - *Follow-up: Was there a specific event?*\n\n"
            "## You're Done!\nGreat work."
        )
        sections = _parse_questionnaire(md)
        assert len(sections) == 2
        assert sections[0]["title"] == "Part 1: Warmup"
        assert sections[0]["description"] == "Easy questions."
        assert len(sections[0]["questions"]) == 2
        assert sections[0]["questions"][0]["number"] == 1
        assert sections[0]["questions"][0]["text"] == "What is your name?"
        assert sections[0]["questions"][0]["followups"] == []
        assert sections[0]["questions"][1]["followups"] == ["What reaction do you get?"]
        assert sections[1]["title"] == "Part 2: Origin"
        assert len(sections[1]["questions"]) == 1

    def test_parse_questionnaire_empty(self):
        from contentsifter.web.routes.interview import _parse_questionnaire
        assert _parse_questionnaire("") == []
        assert _parse_questionnaire("Just some text") == []

    def test_interview_preview_renders_table(self, client_with_db, web_env_with_db):
        content_dir = web_env_with_db / "content"
        content_dir.mkdir(parents=True, exist_ok=True)
        guide = (
            "## Part 1: Warmup\n*Easy ones.*\n\n"
            "**Q1.** What is your name?\n\n"
            "**Q2.** What do you do?\n"
            "  - *Follow-up: How do people react?*\n"
        )
        (content_dir / "interview-guide.md").write_text(guide)
        resp = client_with_db.get("/testweb/interview/preview")
        assert resp.status_code == 200
        assert "<table" in resp.text
        assert "What is your name?" in resp.text
        assert "How do people react?" in resp.text
        assert "Part 1: Warmup" in resp.text


class TestSearch:
    def test_search_page_loads(self, client_with_db):
        resp = client_with_db.get("/testweb/search")
        assert resp.status_code == 200
        assert "Search" in resp.text

    def test_search_empty_query(self, client_with_db):
        resp = client_with_db.get("/testweb/search/results?q=")
        assert resp.status_code == 200
        assert "Type to search" in resp.text

    def test_search_no_results(self, client_with_db):
        resp = client_with_db.get("/testweb/search/results?q=nonexistent")
        assert resp.status_code == 200
        assert "No results" in resp.text


class TestStatus:
    def test_status_page_loads(self, client_with_db):
        resp = client_with_db.get("/testweb/status")
        assert resp.status_code == 200
        assert "Pipeline Status" in resp.text

    def test_status_empty_db(self, client_with_db):
        resp = client_with_db.get("/testweb/status")
        assert resp.status_code == 200
        assert "0" in resp.text


class TestRedirectFix:
    def test_clients_no_trailing_slash(self, client):
        """Regression: /clients must not cause redirect loop."""
        resp = client.get("/clients", follow_redirects=False)
        # Should redirect to /clients/ (trailing slash)
        assert resp.status_code == 307
        assert resp.headers["location"] == "/clients/"

    def test_favicon_returns_204(self, client):
        """Regression: /favicon.ico must not cause redirect loop."""
        resp = client.get("/favicon.ico", follow_redirects=False)
        assert resp.status_code == 204

    def test_unknown_slug_redirects_cleanly(self, client):
        """Unknown slug should redirect to /clients, not loop."""
        resp = client.get("/nonexistent", follow_redirects=False)
        assert resp.status_code == 302
        assert "/clients" in resp.headers["location"]


class TestVoicePrint:
    def test_voice_print_page_loads(self, client_with_db):
        resp = client_with_db.get("/testweb/voice-print")
        assert resp.status_code == 200
        assert "Voice Print" in resp.text

    def test_voice_print_shows_no_print(self, client_with_db):
        resp = client_with_db.get("/testweb/voice-print")
        assert resp.status_code == 200
        assert "None" in resp.text

    def test_voice_print_preview_empty(self, client_with_db):
        resp = client_with_db.get("/testweb/voice-print/preview")
        assert resp.status_code == 200
        assert "No voice print" in resp.text

    def test_voice_print_preview_with_file(self, client_with_db, web_env_with_db):
        content_dir = web_env_with_db / "content"
        content_dir.mkdir(parents=True, exist_ok=True)
        (content_dir / "voice-print.md").write_text("# Voice Print\n\nTest voice print content.")
        resp = client_with_db.get("/testweb/voice-print/preview")
        assert resp.status_code == 200
        assert "Test voice print content" in resp.text

    def test_generate_voice_print_no_api_key(self, client_with_db):
        resp = client_with_db.post("/testweb/voice-print/generate")
        assert resp.status_code == 200
        assert "ANTHROPIC_API_KEY" in resp.text


class TestGenerate:
    def test_generate_page_loads(self, client_with_db):
        resp = client_with_db.get("/testweb/generate")
        assert resp.status_code == 200
        assert "Generate" in resp.text

    def test_generate_page_shows_formats(self, client_with_db):
        resp = client_with_db.get("/testweb/generate")
        assert resp.status_code == 200
        assert "linkedin" in resp.text.lower()
        assert "newsletter" in resp.text.lower()
        assert "carousel" in resp.text.lower()

    def test_source_preview_empty_query(self, client_with_db):
        resp = client_with_db.get("/testweb/generate/source-preview?q=")
        assert resp.status_code == 200

    def test_source_preview_no_results(self, client_with_db):
        resp = client_with_db.get("/testweb/generate/source-preview?q=nonexistent")
        assert resp.status_code == 200
        assert "No source material" in resp.text

    def test_generate_draft_no_api_key(self, client_with_db):
        resp = client_with_db.post("/testweb/generate/draft", data={
            "topic": "networking",
            "format_type": "linkedin",
            "category": "",
            "use_voice_print": "off",
            "skip_gates": "off",
            "limit": "10",
        })
        assert resp.status_code == 200
        assert "ANTHROPIC_API_KEY" in resp.text

    def test_save_draft(self, client_with_db, web_env_with_db):
        drafts_dir = web_env_with_db / "content" / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        resp = client_with_db.post("/testweb/generate/save", data={
            "content": "Test draft content here.",
            "topic": "networking",
            "format_type": "linkedin",
        })
        assert resp.status_code == 200
        assert "Saved" in resp.text
        saved_files = list(drafts_dir.glob("linkedin-*.md"))
        assert len(saved_files) == 1


class TestMarkdownRenderer:
    def test_table_renders_html(self):
        from contentsifter.web.utils import simple_md_to_html
        md = "| Name | Age |\n|------|-----|\n| Alice | 30 |\n| Bob | 25 |"
        html = simple_md_to_html(md)
        assert "<table" in html
        assert "<th>" in html
        assert "Alice" in html
        assert "Bob" in html

    def test_blockquote_renders(self):
        from contentsifter.web.utils import simple_md_to_html
        md = "> This is a quote\n> Second line"
        html = simple_md_to_html(md)
        assert "<blockquote" in html
        assert "This is a quote" in html

    def test_paragraph_spacing(self):
        from contentsifter.web.utils import simple_md_to_html
        md = "First paragraph.\n\nSecond paragraph."
        html = simple_md_to_html(md)
        assert "mb-3" in html
        assert "First paragraph" in html
        assert "Second paragraph" in html

    def test_heading_ids(self):
        from contentsifter.web.utils import simple_md_to_html
        md = "## Quick Reference"
        html = simple_md_to_html(md)
        assert 'id="quick-reference"' in html

    def test_h3_renders(self):
        from contentsifter.web.utils import simple_md_to_html
        md = "### Sub Section"
        html = simple_md_to_html(md)
        assert "<h3" in html
        assert "Sub Section" in html

    def test_inline_code(self):
        from contentsifter.web.utils import simple_md_to_html
        md = "Use `contentsifter search` to find content."
        html = simple_md_to_html(md)
        assert "<code" in html
        assert "contentsifter search" in html


class TestSearchDetail:
    def test_search_detail_no_extraction(self, client_with_db):
        resp = client_with_db.get("/testweb/search/detail/99999")
        assert resp.status_code == 200
        assert "not found" in resp.text

    def test_search_results_returns_template(self, client_with_db):
        resp = client_with_db.get("/testweb/search/results?q=nonexistent")
        assert resp.status_code == 200
        assert "No results" in resp.text


class TestBrowseAndSuggestions:
    def test_browse_by_category(self, client_with_extractions):
        """Browse playbooks with no search term."""
        resp = client_with_extractions.get("/testweb/search/results?category=playbook")
        assert resp.status_code == 200
        assert "Networking Tips" in resp.text
        assert "playbook" in resp.text.lower()

    def test_browse_no_query_no_category_shows_prompt(self, client_with_db):
        """Empty query + no category shows prompt text."""
        resp = client_with_db.get("/testweb/search/results?q=&category=")
        assert resp.status_code == 200
        assert "Type to search" in resp.text or "select a category" in resp.text

    def test_search_with_category_filter(self, client_with_extractions):
        """FTS search with category filter."""
        resp = client_with_extractions.get("/testweb/search/results?q=relationships&category=playbook")
        assert resp.status_code == 200
        assert "Networking Tips" in resp.text

    def test_suggestions_endpoint(self, client_with_extractions):
        """Suggestions endpoint returns popular tags."""
        resp = client_with_extractions.get("/testweb/search/suggestions")
        assert resp.status_code == 200
        assert "networking" in resp.text
        assert "resume" in resp.text

    def test_suggestions_empty_db(self, client_with_db):
        """Suggestions endpoint with no tags returns empty."""
        resp = client_with_db.get("/testweb/search/suggestions")
        assert resp.status_code == 200

    def test_search_page_has_tabs(self, client_with_extractions):
        """Search page shows category tabs."""
        resp = client_with_extractions.get("/testweb/search")
        assert resp.status_code == 200
        assert "browse-tab" in resp.text
        assert "Playbook" in resp.text

    def test_browse_results_header(self, client_with_extractions):
        """Browse mode shows 'N playbooks' not 'N results for'."""
        resp = client_with_extractions.get("/testweb/search/results?category=playbook")
        assert resp.status_code == 200
        assert "playbook" in resp.text.lower()

    def test_search_detail_has_generate_with_api_key(self, web_env_with_extractions, monkeypatch):
        """Search detail shows per-card generate button when API key is set."""
        from contentsifter.web.app import create_app

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
        app = create_app()
        c = TestClient(app)
        resp = c.get("/testweb/search/detail/1")
        assert resp.status_code == 200
        assert "from-extraction/1" in resp.text
        assert "format_type" in resp.text

    def test_search_detail_no_generate_without_api_key(self, client_with_extractions):
        """Search detail hides generate button when no API key."""
        resp = client_with_extractions.get("/testweb/search/detail/1")
        assert resp.status_code == 200
        assert "from-extraction" not in resp.text


class TestAutoformat:
    def test_needs_formatting_linkedin_with_dividers(self):
        from contentsifter.ingest.autoformat import needs_formatting
        text = "Post one.\n---\nPost two."
        assert needs_formatting(text, "linkedin_post") is False

    def test_needs_formatting_linkedin_raw(self):
        from contentsifter.ingest.autoformat import needs_formatting
        text = "This is a raw dump of several LinkedIn posts with no structure at all."
        assert needs_formatting(text, "linkedin_post") is True

    def test_needs_formatting_blog_with_heading(self):
        from contentsifter.ingest.autoformat import needs_formatting
        text = "# My Blog Post\n\nSome content here."
        assert needs_formatting(text, "blog") is False

    def test_needs_formatting_blog_raw(self):
        from contentsifter.ingest.autoformat import needs_formatting
        text = "Just some raw text without any headings or frontmatter."
        assert needs_formatting(text, "blog") is True

    def test_needs_formatting_other_never(self):
        from contentsifter.ingest.autoformat import needs_formatting
        text = "Random content"
        assert needs_formatting(text, "other") is False

    def test_auto_format_no_llm(self):
        from contentsifter.ingest.autoformat import auto_format_content
        text = "Raw content"
        result = auto_format_content(text, "linkedin_post", None)
        assert result == text


class TestDrafts:
    def test_drafts_page_empty(self, client):
        resp = client.get("/testweb/drafts")
        assert resp.status_code == 200
        assert "No saved drafts yet" in resp.text

    def test_drafts_page_lists_files(self, web_env):
        """Drafts page shows saved draft files."""
        from contentsifter.web.app import create_app

        drafts_dir = Path(web_env / "content" / "drafts")
        drafts_dir.mkdir(parents=True, exist_ok=True)
        (drafts_dir / "linkedin-20260222-120000.md").write_text(
            "# Test Topic\n\n*Format: linkedin*\n\n---\n\nHello world draft content.\n"
        )
        (drafts_dir / "newsletter-20260221-100000.md").write_text(
            "# Newsletter Topic\n\n*Format: newsletter*\n\n---\n\nNewsletter body here.\n"
        )

        app = create_app()
        c = TestClient(app)
        resp = c.get("/testweb/drafts")
        assert resp.status_code == 200
        assert "Test Topic" in resp.text
        assert "Newsletter Topic" in resp.text
        assert "linkedin" in resp.text
        assert "2 saved drafts" in resp.text

    def test_draft_detail_returns_body(self, web_env):
        """Detail endpoint returns draft body content."""
        from contentsifter.web.app import create_app

        drafts_dir = Path(web_env / "content" / "drafts")
        drafts_dir.mkdir(parents=True, exist_ok=True)
        (drafts_dir / "test-draft.md").write_text(
            "# My Draft\n\n*Format: linkedin*\n\n---\n\nFull body content here.\n"
        )

        app = create_app()
        c = TestClient(app)
        resp = c.get("/testweb/drafts/test-draft.md")
        assert resp.status_code == 200
        assert "Full body content here." in resp.text

    def test_draft_detail_not_found(self, client):
        resp = client.get("/testweb/drafts/nonexistent.md")
        assert resp.status_code == 200
        assert "not found" in resp.text.lower()

    def test_delete_draft(self, web_env):
        """Delete endpoint removes draft file."""
        from contentsifter.web.app import create_app

        drafts_dir = Path(web_env / "content" / "drafts")
        drafts_dir.mkdir(parents=True, exist_ok=True)
        draft_path = drafts_dir / "to-delete.md"
        draft_path.write_text("# Delete Me\n\n*Format: linkedin*\n\n---\n\nGone.\n")

        app = create_app()
        c = TestClient(app)
        resp = c.delete("/testweb/drafts/to-delete.md")
        assert resp.status_code == 200
        assert not draft_path.exists()
