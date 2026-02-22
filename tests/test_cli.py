"""CLI integration tests using Click's CliRunner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from contentsifter.cli import cli
from contentsifter.storage.database import Database
from contentsifter.storage.repository import Repository


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    """Set up isolated environment for CLI tests."""
    import contentsifter.config as config_mod

    # Create clients.json
    db_path = str(tmp_path / "data" / "contentsifter.db")
    content_dir = str(tmp_path / "content")
    registry = {
        "default": "testcli",
        "clients": {
            "testcli": {
                "name": "CLI Test",
                "email": "test@example.com",
                "description": "CLI testing",
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


class TestHelpCommands:
    def test_main_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ContentSifter" in result.output

    def test_client_help(self, runner):
        result = runner.invoke(cli, ["client", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output
        assert "list" in result.output

    def test_interview_help(self, runner):
        result = runner.invoke(cli, ["interview", "--help"])
        assert result.exit_code == 0
        assert "generate" in result.output
        assert "ingest" in result.output
        assert "status" in result.output


class TestClientCommands:
    def test_client_list(self, runner, cli_env):
        result = runner.invoke(cli, ["client", "list"])
        assert result.exit_code == 0
        assert "testcli" in result.output

    def test_client_create(self, runner, cli_env):
        result = runner.invoke(cli, ["client", "create", "newone", "--name", "New One"])
        assert result.exit_code == 0
        assert "Created client" in result.output

    def test_client_create_duplicate(self, runner, cli_env):
        result = runner.invoke(cli, ["client", "create", "testcli", "--name", "Dup"])
        assert result.exit_code == 0
        assert "already exists" in result.output

    def test_client_info(self, runner, cli_env):
        result = runner.invoke(cli, ["client", "info", "testcli"])
        assert result.exit_code == 0
        assert "CLI Test" in result.output

    def test_client_set_default(self, runner, cli_env):
        # Create a second client first
        runner.invoke(cli, ["client", "create", "second", "--name", "Second"])
        result = runner.invoke(cli, ["client", "set-default", "second"])
        assert result.exit_code == 0
        assert "Default client set to" in result.output


class TestStatusCommand:
    def test_status_no_db(self, runner, cli_env):
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "No database found" in result.output

    def test_status_with_db(self, runner, cli_env):
        tmp_path = cli_env
        db_path = Path(tmp_path / "data" / "contentsifter.db")
        with Database(db_path) as db:
            pass  # Just creates the schema
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "Processing Progress" in result.output or "Status" in result.output


class TestIngestCommand:
    def test_ingest_status_only_no_db(self, runner, cli_env):
        result = runner.invoke(cli, ["ingest", "--status-only"])
        assert result.exit_code == 0
        assert "No database found" in result.output

    def test_ingest_no_args(self, runner, cli_env):
        result = runner.invoke(cli, ["ingest"])
        assert result.exit_code == 0
        assert "Provide a file" in result.output or "Error" in result.output

    def test_ingest_file(self, runner, cli_env):
        tmp_path = cli_env
        f = tmp_path / "test-post.md"
        f.write_text("title: Test\n\nThis is test content for ingestion.")
        result = runner.invoke(cli, ["ingest", str(f), "--type", "blog"])
        assert result.exit_code == 0
        assert "Ingested" in result.output


class TestInterviewCommands:
    def test_interview_generate(self, runner, cli_env):
        result = runner.invoke(cli, ["interview", "generate"])
        assert result.exit_code == 0
        assert "Questionnaire saved" in result.output or "saved to" in result.output.lower()

    def test_interview_status_no_db(self, runner, cli_env):
        result = runner.invoke(cli, ["interview", "status"])
        assert result.exit_code == 0
        assert "No database found" in result.output

    def test_interview_ingest_missing_questionnaire(self, runner, cli_env):
        tmp_path = cli_env
        transcript = tmp_path / "transcript.txt"
        transcript.write_text("Q1 What is your name? My name is Jane.")
        # Without generating a questionnaire first, this should error
        result = runner.invoke(cli, ["interview", "ingest", str(transcript)])
        assert "not found" in result.output.lower() or result.exit_code != 0


class TestSearchCommand:
    def test_search_no_db(self, runner, cli_env):
        """Search when no database exists should still succeed (creates DB on fly)."""
        result = runner.invoke(cli, ["search", "test"])
        assert result.exit_code == 0
        assert "No results" in result.output or "results" in result.output.lower()


class TestExportCommand:
    def test_export_no_db(self, runner, cli_env):
        """Export with empty DB should succeed with 0 extractions."""
        result = runner.invoke(cli, ["export"])
        assert result.exit_code == 0
        assert "Exported" in result.output or "0" in result.output
