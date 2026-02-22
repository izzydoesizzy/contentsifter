"""Tests for contentsifter.parser.splitter."""

from __future__ import annotations

from pathlib import Path

from contentsifter.parser.splitter import split_merged_file, split_all_files


class TestSplitMergedFile:
    def test_basic_split(self, tmp_path):
        content = """\
<!-- ============ -->
<!-- SOURCE FILE: call_one.md -->
<!-- ============ -->

# Call One

Some content here.

<!-- ============ -->
<!-- SOURCE FILE: call_two.md -->
<!-- ============ -->

# Call Two

Other content here.
"""
        f = tmp_path / "merged_01.md"
        f.write_text(content)

        records = split_merged_file(f)
        assert len(records) == 2
        assert records[0].original_filename == "call_one.md"
        assert records[1].original_filename == "call_two.md"
        assert "Call One" in records[0].raw_text
        assert "Call Two" in records[1].raw_text

    def test_source_file_field(self, tmp_path):
        content = """\
<!-- ============ -->
<!-- SOURCE FILE: test.md -->
<!-- ============ -->

Content.
"""
        f = tmp_path / "merged_02.md"
        f.write_text(content)
        records = split_merged_file(f)
        assert records[0].source_file == "merged_02.md"

    def test_empty_sections_skipped(self, tmp_path):
        content = """\
<!-- ============ -->
<!-- SOURCE FILE: has_content.md -->
<!-- ============ -->

Actual content.

<!-- ============ -->
<!-- SOURCE FILE: empty.md -->
<!-- ============ -->

"""
        f = tmp_path / "merged.md"
        f.write_text(content)
        records = split_merged_file(f)
        # Only the non-empty section should be returned
        assert len(records) == 1
        assert records[0].original_filename == "has_content.md"

    def test_no_markers_returns_empty(self, tmp_path):
        f = tmp_path / "plain.md"
        f.write_text("Just some text without markers.")
        assert split_merged_file(f) == []

    def test_single_record(self, tmp_path):
        content = """\
<!-- ============ -->
<!-- SOURCE FILE: only_one.md -->
<!-- ============ -->

The only call in this file.
"""
        f = tmp_path / "merged.md"
        f.write_text(content)
        records = split_merged_file(f)
        assert len(records) == 1
        assert "only call" in records[0].raw_text


class TestSplitAllFiles:
    def test_multiple_merged_files(self, tmp_path):
        for i in range(2):
            content = f"""\
<!-- ============ -->
<!-- SOURCE FILE: call_{i}.md -->
<!-- ============ -->

Content {i}.
"""
            (tmp_path / f"merged_{i:02d}.md").write_text(content)

        records = split_all_files(tmp_path)
        assert len(records) == 2

    def test_ignores_non_merged_files(self, tmp_path):
        (tmp_path / "notes.md").write_text("Not a merged file")
        content = """\
<!-- ============ -->
<!-- SOURCE FILE: real.md -->
<!-- ============ -->

Real content.
"""
        (tmp_path / "merged_01.md").write_text(content)
        records = split_all_files(tmp_path)
        assert len(records) == 1

    def test_empty_directory(self, tmp_path):
        assert split_all_files(tmp_path) == []
