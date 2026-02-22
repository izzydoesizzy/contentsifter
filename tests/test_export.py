"""Tests for contentsifter.storage.export."""

from __future__ import annotations

import json
from pathlib import Path

from contentsifter.storage.export import export_all
from contentsifter.storage.repository import Repository


class TestExportAll:
    def test_creates_output_directory(self, populated_db, tmp_path):
        db, _ = populated_db
        output_dir = tmp_path / "exports"
        export_all(db, output_dir)
        assert output_dir.is_dir()

    def test_full_export_file(self, populated_db, tmp_path):
        db, _ = populated_db
        output_dir = tmp_path / "exports"
        export_all(db, output_dir)
        full = output_dir / "full_export.json"
        assert full.exists()
        data = json.loads(full.read_text())
        assert len(data) == 2  # 2 extractions in sample

    def test_by_category_files(self, populated_db, tmp_path):
        db, _ = populated_db
        output_dir = tmp_path / "exports"
        export_all(db, output_dir)
        cat_dir = output_dir / "by_category"
        assert cat_dir.is_dir()
        assert (cat_dir / "qa.json").exists()
        assert (cat_dir / "playbook.json").exists()

    def test_by_call_files(self, populated_db, tmp_path):
        db, _ = populated_db
        output_dir = tmp_path / "exports"
        export_all(db, output_dir)
        call_dir = output_dir / "by_call"
        assert call_dir.is_dir()
        call_files = list(call_dir.glob("*.json"))
        assert len(call_files) == 1

    def test_summary_return(self, populated_db, tmp_path):
        db, _ = populated_db
        output_dir = tmp_path / "exports"
        summary = export_all(db, output_dir)
        assert summary["total"] == 2
        assert "qa" in summary["by_category"]
        assert "playbook" in summary["by_category"]
        assert summary["calls_with_extractions"] == 1
