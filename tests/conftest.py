"""Shared test fixtures for ContentSifter."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from contentsifter.storage.database import Database
from contentsifter.storage.models import (
    CallMetadata,
    Extraction,
    Participant,
    SpeakerTurn,
    TopicChunk,
)
from contentsifter.storage.repository import Repository


@pytest.fixture
def tmp_db(tmp_path):
    """Create an in-memory-like temp database with schema initialized."""
    db_path = tmp_path / "test.db"
    with Database(db_path) as db:
        yield db


@pytest.fixture
def repo(tmp_db):
    """Repository backed by the temp database."""
    return Repository(tmp_db)


@pytest.fixture
def sample_metadata():
    """A minimal CallMetadata for testing."""
    return CallMetadata(
        source_file="merged_01.md",
        original_filename="weekly-group-q-a-2024-03-15_12345.md",
        fathom_id="12345",
        title="Weekly Group Q&A — March 15",
        call_date="2024-03-15",
        call_type="group_qa",
        participants=[
            Participant(display_name="Izzy Piyale-Sheard", email="izzy@joinclearcareer.com", is_coach=True),
            Participant(display_name="Alice", email="alice@example.com", is_coach=False),
        ],
    )


@pytest.fixture
def sample_turns():
    """A few SpeakerTurn objects for testing."""
    return [
        SpeakerTurn(
            turn_index=0,
            speaker_name="Izzy Piyale-Sheard",
            speaker_email="izzy@joinclearcareer.com",
            text="Welcome everyone! Let's get started.",
            timestamp="00:00:05",
            timestamp_seconds=5,
        ),
        SpeakerTurn(
            turn_index=1,
            speaker_name="Alice",
            speaker_email="alice@example.com",
            text="How do I improve my LinkedIn profile?",
            timestamp="00:01:30",
            timestamp_seconds=90,
        ),
        SpeakerTurn(
            turn_index=2,
            speaker_name="Izzy Piyale-Sheard",
            speaker_email="izzy@joinclearcareer.com",
            text="Great question! First, make sure your headline tells people what you do, not your job title.",
            timestamp="00:02:00",
            timestamp_seconds=120,
        ),
    ]


@pytest.fixture
def sample_chunks():
    """TopicChunk objects for testing."""
    return [
        TopicChunk(
            chunk_index=0,
            topic_title="LinkedIn Profile Optimization",
            topic_summary="Discussion about improving LinkedIn profiles",
            start_turn_index=0,
            end_turn_index=2,
            start_timestamp="00:00:05",
            end_timestamp="00:02:00",
            primary_speaker="Izzy Piyale-Sheard",
        ),
    ]


@pytest.fixture
def sample_extractions():
    """Extraction objects for testing."""
    return [
        Extraction(
            category="qa",
            title="How to improve LinkedIn profile",
            content="Make your headline about what you do, not your title.",
            raw_quote="Make sure your headline tells people what you do",
            speaker="Izzy Piyale-Sheard",
            quality_score=4,
            tags=["linkedin", "personal_branding"],
        ),
        Extraction(
            category="playbook",
            title="LinkedIn headline formula",
            content="Step 1: Remove your job title. Step 2: Write what you help people do.",
            speaker="Izzy Piyale-Sheard",
            quality_score=5,
            tags=["linkedin", "resume"],
        ),
    ]


@pytest.fixture
def populated_db(tmp_db, repo, sample_metadata, sample_turns, sample_chunks, sample_extractions):
    """Database with one call, chunks, and extractions inserted."""
    call_id = repo.insert_call(sample_metadata, sample_turns)
    chunk_ids = repo.insert_topic_chunks(call_id, sample_chunks)
    repo.insert_extractions(call_id, chunk_ids[0], sample_extractions)
    repo.mark_extracted(call_id)
    return tmp_db, call_id


@pytest.fixture
def tmp_clients_json(tmp_path, monkeypatch):
    """Set up a temp clients.json for config tests."""
    registry = {
        "default": "testclient",
        "clients": {
            "testclient": {
                "name": "Test Client",
                "email": "test@example.com",
                "description": "A test client",
                "db_path": f"{tmp_path}/data/clients/testclient/contentsifter.db",
                "content_dir": f"{tmp_path}/content/clients/testclient",
            }
        },
    }
    clients_json = tmp_path / "clients.json"
    clients_json.write_text(json.dumps(registry))

    import contentsifter.config as config_mod
    monkeypatch.setattr(config_mod, "CLIENTS_JSON_PATH", clients_json)
    monkeypatch.setattr(config_mod, "PROJECT_ROOT", tmp_path)
    return clients_json, tmp_path
