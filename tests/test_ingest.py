"""Tests for contentsifter.ingest (reader + formats)."""

from __future__ import annotations

from pathlib import Path

from contentsifter.ingest.formats import parse_content_file, _split_on_dividers
from contentsifter.ingest.reader import detect_content_type, ingest_path
from contentsifter.storage.database import Database


class TestDetectContentType:
    def test_linkedin(self):
        assert detect_content_type(Path("linkedin-posts.md")) == "linkedin_post"

    def test_email(self):
        assert detect_content_type(Path("email-outreach.md")) == "email"

    def test_newsletter(self):
        assert detect_content_type(Path("newsletter-jan.md")) == "newsletter"

    def test_blog(self):
        assert detect_content_type(Path("blog-leadership.md")) == "blog"

    def test_transcript(self):
        assert detect_content_type(Path("transcript-call.md")) == "transcript"

    def test_unknown_prefix(self):
        assert detect_content_type(Path("random-notes.md")) == "other"

    def test_case_insensitive(self):
        assert detect_content_type(Path("LinkedIn-Posts.md")) == "linkedin_post"


class TestSplitOnDividers:
    def test_triple_dash(self):
        parts = _split_on_dividers("Part 1\n\n---\n\nPart 2")
        assert len(parts) == 2

    def test_long_dash(self):
        parts = _split_on_dividers("Part 1\n\n------\n\nPart 2")
        assert len(parts) == 2

    def test_triple_star(self):
        parts = _split_on_dividers("Part 1\n\n***\n\nPart 2")
        assert len(parts) == 2

    def test_triple_equals(self):
        parts = _split_on_dividers("Part 1\n\n===\n\nPart 2")
        assert len(parts) == 2

    def test_no_dividers(self):
        parts = _split_on_dividers("Just one section")
        assert len(parts) == 1


class TestParseContentFile:
    def test_linkedin_split(self, tmp_path):
        f = tmp_path / "posts.md"
        f.write_text("""\
date: 2026-01-15
title: First Post

This is the first post content.

---

date: 2026-01-20
title: Second Post

This is the second post content.
""")
        items = parse_content_file(f, "linkedin_post")
        assert len(items) == 2
        assert items[0]["title"] == "First Post"
        assert items[0]["date"] == "2026-01-15"
        assert "first post content" in items[0]["text"].lower()
        assert items[1]["title"] == "Second Post"

    def test_newsletter_single_item(self, tmp_path):
        f = tmp_path / "newsletter.md"
        f.write_text("""\
title: Weekly Update

# Weekly Update

Welcome to this week's newsletter.

---

This divider should NOT split the newsletter.
""")
        items = parse_content_file(f, "newsletter")
        assert len(items) == 1

    def test_blog_single_item(self, tmp_path):
        f = tmp_path / "blog.md"
        f.write_text("# My Blog Post\n\nContent here.")
        items = parse_content_file(f, "blog")
        assert len(items) == 1
        assert items[0]["title"] == "My Blog Post"

    def test_frontmatter_extraction(self, tmp_path):
        f = tmp_path / "post.md"
        f.write_text("""\
date: 2026-02-01
title: Test Title
author: Jane

The body text here.
""")
        items = parse_content_file(f, "linkedin_post")
        assert items[0]["title"] == "Test Title"
        assert items[0]["date"] == "2026-02-01"
        assert items[0]["author"] == "Jane"
        assert "body text" in items[0]["text"]

    def test_title_from_heading(self, tmp_path):
        f = tmp_path / "post.md"
        f.write_text("# My Heading\n\nContent under heading.")
        items = parse_content_file(f, "linkedin_post")
        assert items[0]["title"] == "My Heading"

    def test_title_from_first_line(self, tmp_path):
        f = tmp_path / "post.md"
        f.write_text("Just a normal first line without heading\n\nMore content.")
        items = parse_content_file(f, "linkedin_post")
        assert items[0]["title"].startswith("Just a normal first line")

    def test_short_sections_filtered(self, tmp_path):
        f = tmp_path / "posts.md"
        f.write_text("Real content that is long enough.\n\n---\n\nShort\n\n---\n\nAnother real section with enough text.")
        items = parse_content_file(f, "linkedin_post")
        # Sections < 10 chars should be filtered
        assert all(len(item["text"]) >= 10 for item in items)


class TestIngestPath:
    def test_ingest_single_file(self, tmp_db, tmp_path):
        f = tmp_path / "linkedin-posts.md"
        f.write_text("""\
title: Test Post

This is a test LinkedIn post with enough content.

---

title: Another Post

Another post with different content here.
""")
        items = ingest_path(tmp_db, f, content_type="linkedin", author="Jane")
        assert len(items) == 2
        assert all(item.get("id") is not None for item in items)

    def test_ingest_directory(self, tmp_db, tmp_path):
        (tmp_path / "post1.md").write_text("title: Post One\n\nFirst post content here.")
        (tmp_path / "post2.md").write_text("title: Post Two\n\nSecond post content here.")
        items = ingest_path(tmp_db, tmp_path, content_type="blog", author="Jane")
        assert len(items) == 2

    def test_auto_detect_type(self, tmp_db, tmp_path):
        f = tmp_path / "linkedin-posts.md"
        f.write_text("title: Auto Post\n\nAuto-detected content type test.")
        items = ingest_path(tmp_db, f, author="Jane")
        assert items[0]["content_type"] == "linkedin_post"

    def test_author_assignment(self, tmp_db, tmp_path):
        f = tmp_path / "post.md"
        f.write_text("title: Authored\n\nContent with author.")
        items = ingest_path(tmp_db, f, content_type="blog", author="Bob")
        assert items[0]["author"] == "Bob"

    def test_items_persisted_to_db(self, tmp_db, tmp_path):
        f = tmp_path / "post.md"
        f.write_text("title: Persisted\n\nThis should be in the database.")
        ingest_path(tmp_db, f, content_type="blog", author="Jane")
        row = tmp_db.conn.execute(
            "SELECT * FROM content_items WHERE title = 'Persisted'"
        ).fetchone()
        assert row is not None
        assert row["author"] == "Jane"
