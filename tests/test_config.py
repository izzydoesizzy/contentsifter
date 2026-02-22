"""Tests for contentsifter.config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from contentsifter.config import (
    ClientConfig,
    create_client,
    list_clients,
    load_client,
    set_default_client,
)


class TestClientConfig:
    def test_properties(self, tmp_path):
        config = ClientConfig(
            slug="test", name="Test", db_path=tmp_path / "db.db",
            content_dir=tmp_path / "content",
        )
        assert config.voice_print_path == tmp_path / "content" / "voice-print.md"
        assert config.drafts_dir == tmp_path / "content" / "drafts"
        assert config.calendar_dir == tmp_path / "content" / "calendar"
        assert config.templates_dir == tmp_path / "content" / "templates"
        assert config.exports_dir == tmp_path / "exports"

    def test_ensure_dirs(self, tmp_path):
        config = ClientConfig(
            slug="test", name="Test",
            db_path=tmp_path / "data" / "db.db",
            content_dir=tmp_path / "content",
        )
        config.ensure_dirs()
        assert (tmp_path / "data").is_dir()
        assert (tmp_path / "content").is_dir()
        assert (tmp_path / "content" / "drafts").is_dir()
        assert (tmp_path / "content" / "calendar").is_dir()

    def test_default_field_values(self):
        config = ClientConfig(slug="s", name="N")
        assert config.email == ""
        assert config.description == ""


class TestLoadClient:
    def test_load_existing_client(self, tmp_clients_json):
        config = load_client("testclient")
        assert config.slug == "testclient"
        assert config.name == "Test Client"
        assert config.email == "test@example.com"

    def test_load_default_client(self, tmp_clients_json):
        config = load_client(None)
        assert config.slug == "testclient"

    def test_load_unknown_client_raises(self, tmp_clients_json):
        with pytest.raises(ValueError, match="Unknown client"):
            load_client("nonexistent")

    def test_izzy_fallback_without_registry(self, tmp_path, monkeypatch):
        """When no clients.json exists, 'izzy' should still work."""
        import contentsifter.config as config_mod
        monkeypatch.setattr(config_mod, "CLIENTS_JSON_PATH", tmp_path / "nope.json")
        config = load_client("izzy")
        assert config.slug == "izzy"
        assert config.name == "Izzy Piyale-Sheard"


class TestCreateClient:
    def test_create_new_client(self, tmp_clients_json):
        clients_json, tmp_path = tmp_clients_json
        config = create_client("newclient", "New Client", "new@example.com")
        assert config.slug == "newclient"
        assert config.name == "New Client"
        assert config.db_path.parent.is_dir()

        # Verify it's in the registry
        registry = json.loads(clients_json.read_text())
        assert "newclient" in registry["clients"]

    def test_create_duplicate_raises(self, tmp_clients_json):
        with pytest.raises(ValueError, match="already exists"):
            create_client("testclient", "Duplicate")


class TestListClients:
    def test_list_returns_all(self, tmp_clients_json):
        clients = list_clients()
        assert len(clients) == 1
        assert clients[0]["slug"] == "testclient"
        assert clients[0]["is_default"] is True

    def test_list_empty_registry(self, tmp_path, monkeypatch):
        import contentsifter.config as config_mod
        empty = tmp_path / "empty.json"
        empty.write_text(json.dumps({"default": "", "clients": {}}))
        monkeypatch.setattr(config_mod, "CLIENTS_JSON_PATH", empty)
        assert list_clients() == []


class TestSetDefaultClient:
    def test_set_default(self, tmp_clients_json):
        clients_json, _ = tmp_clients_json
        # Add a second client first
        create_client("second", "Second")
        set_default_client("second")
        registry = json.loads(clients_json.read_text())
        assert registry["default"] == "second"

    def test_set_unknown_raises(self, tmp_clients_json):
        with pytest.raises(ValueError, match="Unknown client"):
            set_default_client("ghost")
