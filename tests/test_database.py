"""Tests for contentsifter.storage.database."""

from __future__ import annotations

from pathlib import Path

from contentsifter.storage.database import Database


class TestDatabase:
    def test_context_manager_creates_tables(self, tmp_path):
        db_path = tmp_path / "test.db"
        with Database(db_path) as db:
            tables = db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            table_names = {r[0] for r in tables}
            assert "calls" in table_names
            assert "speaker_turns" in table_names
            assert "extractions" in table_names
            assert "tags" in table_names
            assert "processing_log" in table_names
            assert "content_items" in table_names

    def test_fts5_tables_exist(self, tmp_path):
        db_path = tmp_path / "test.db"
        with Database(db_path) as db:
            tables = db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'"
            ).fetchall()
            fts_names = {r[0] for r in tables}
            assert "extractions_fts" in fts_names
            assert "speaker_turns_fts" in fts_names

    def test_creates_parent_directories(self, tmp_path):
        db_path = tmp_path / "deep" / "nested" / "test.db"
        with Database(db_path) as db:
            assert db_path.parent.is_dir()

    def test_row_factory_returns_dicts(self, tmp_path):
        db_path = tmp_path / "test.db"
        with Database(db_path) as db:
            db.conn.execute("INSERT INTO tags (name) VALUES ('test')")
            row = db.conn.execute("SELECT * FROM tags WHERE name = 'test'").fetchone()
            assert row["name"] == "test"

    def test_wal_mode_enabled(self, tmp_path):
        db_path = tmp_path / "test.db"
        with Database(db_path) as db:
            mode = db.conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode == "wal"

    def test_foreign_keys_enabled(self, tmp_path):
        db_path = tmp_path / "test.db"
        with Database(db_path) as db:
            fk = db.conn.execute("PRAGMA foreign_keys").fetchone()[0]
            assert fk == 1

    def test_close_and_reopen(self, tmp_path):
        db_path = tmp_path / "test.db"
        with Database(db_path) as db:
            db.conn.execute("INSERT INTO tags (name) VALUES ('persist')")
            db.conn.commit()

        # Reopen and verify data persists
        with Database(db_path) as db:
            row = db.conn.execute("SELECT * FROM tags WHERE name = 'persist'").fetchone()
            assert row is not None

    def test_content_items_fts_exists(self, tmp_path):
        db_path = tmp_path / "test.db"
        with Database(db_path) as db:
            tables = db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = 'content_items_fts'"
            ).fetchall()
            assert len(tables) == 1
