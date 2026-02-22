"""Tests for contentsifter.storage.repository."""

from __future__ import annotations

import pytest

from contentsifter.storage.models import (
    CallMetadata,
    Extraction,
    Participant,
    SpeakerTurn,
    TopicChunk,
)
from contentsifter.storage.repository import Repository


class TestCallOperations:
    def test_insert_call_returns_id(self, repo, sample_metadata, sample_turns):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        assert isinstance(call_id, int)
        assert call_id > 0

    def test_call_exists(self, repo, sample_metadata, sample_turns):
        repo.insert_call(sample_metadata, sample_turns)
        assert repo.call_exists(sample_metadata.original_filename) is True
        assert repo.call_exists("nonexistent.md") is False

    def test_get_call_count(self, repo, sample_metadata, sample_turns):
        assert repo.get_call_count() == 0
        repo.insert_call(sample_metadata, sample_turns)
        assert repo.get_call_count() == 1

    def test_get_call_by_id(self, repo, sample_metadata, sample_turns):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        call = repo.get_call_by_id(call_id)
        assert call is not None
        assert call["title"] == sample_metadata.title
        assert call["call_date"] == sample_metadata.call_date
        assert call["turn_count"] == len(sample_turns)

    def test_get_call_by_id_missing(self, repo):
        assert repo.get_call_by_id(999) is None

    def test_get_all_calls(self, repo, sample_metadata, sample_turns):
        repo.insert_call(sample_metadata, sample_turns)
        calls = repo.get_all_calls()
        assert len(calls) == 1
        assert calls[0]["title"] == sample_metadata.title

    def test_insert_call_stores_participants(self, repo, sample_metadata, sample_turns):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        rows = repo.db.conn.execute(
            "SELECT * FROM participants WHERE call_id = ?", (call_id,)
        ).fetchall()
        assert len(rows) == 2
        coach = [r for r in rows if r["is_coach"]]
        assert len(coach) == 1

    def test_insert_call_stores_turns(self, repo, sample_metadata, sample_turns):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        turns = repo.get_turns_for_call(call_id)
        assert len(turns) == 3
        assert turns[0]["speaker_name"] == "Izzy Piyale-Sheard"
        assert turns[0]["turn_index"] == 0


class TestTopicChunks:
    def test_insert_and_retrieve(self, repo, sample_metadata, sample_turns, sample_chunks):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        chunk_ids = repo.insert_topic_chunks(call_id, sample_chunks)
        assert len(chunk_ids) == 1

        chunks = repo.get_chunks_for_call(call_id)
        assert len(chunks) == 1
        assert chunks[0]["topic_title"] == "LinkedIn Profile Optimization"


class TestExtractions:
    def test_insert_extractions(self, repo, sample_metadata, sample_turns,
                                sample_chunks, sample_extractions):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        chunk_ids = repo.insert_topic_chunks(call_id, sample_chunks)
        ext_ids = repo.insert_extractions(call_id, chunk_ids[0], sample_extractions)
        assert len(ext_ids) == 2

    def test_extractions_have_tags(self, repo, sample_metadata, sample_turns,
                                   sample_chunks, sample_extractions):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        chunk_ids = repo.insert_topic_chunks(call_id, sample_chunks)
        ext_ids = repo.insert_extractions(call_id, chunk_ids[0], sample_extractions)

        # Check tags for first extraction
        tags = repo.db.conn.execute(
            """SELECT t.name FROM tags t
               JOIN extraction_tags et ON t.id = et.tag_id
               WHERE et.extraction_id = ?""",
            (ext_ids[0],),
        ).fetchall()
        tag_names = {t["name"] for t in tags}
        assert "linkedin" in tag_names
        assert "personal_branding" in tag_names

    def test_mark_extracted(self, repo, sample_metadata, sample_turns):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        repo.mark_extracted(call_id)
        row = repo.db.conn.execute(
            "SELECT * FROM processing_log WHERE call_id = ? AND stage = 'extracted'",
            (call_id,),
        ).fetchone()
        assert row is not None
        assert row["status"] == "completed"


class TestProcessingProgress:
    def test_get_calls_needing_chunking(self, repo, sample_metadata, sample_turns):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        # After insert_call, parsed is logged; should need chunking
        needing = repo.get_calls_needing_stage("chunked")
        assert call_id in needing

    def test_chunked_call_not_needing_chunking(self, repo, sample_metadata,
                                                sample_turns, sample_chunks):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        repo.insert_topic_chunks(call_id, sample_chunks)
        needing = repo.get_calls_needing_stage("chunked")
        assert call_id not in needing

    def test_get_calls_needing_extraction(self, repo, sample_metadata,
                                          sample_turns, sample_chunks):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        repo.insert_topic_chunks(call_id, sample_chunks)
        needing = repo.get_calls_needing_stage("extracted")
        assert call_id in needing

    def test_progress_summary(self, populated_db):
        db, call_id = populated_db
        repo = Repository(db)
        summary = repo.get_progress_summary()
        assert summary["total_calls"] == 1
        assert summary["stages"]["parsed"] == 1
        assert summary["stages"]["chunked"] == 1
        assert summary["stages"]["extracted"] == 1
        assert summary["total_extractions"] == 2
        assert "qa" in summary["extractions"]
        assert "playbook" in summary["extractions"]


class TestSpeakerTurns:
    def test_get_turns_for_call(self, repo, sample_metadata, sample_turns):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        turns = repo.get_turns_for_call(call_id)
        assert len(turns) == 3

    def test_get_turns_for_range(self, repo, sample_metadata, sample_turns):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        turns = repo.get_turns_for_range(call_id, 0, 1)
        assert len(turns) == 2
        assert turns[0]["turn_index"] == 0
        assert turns[1]["turn_index"] == 1

    def test_get_turns_empty_range(self, repo, sample_metadata, sample_turns):
        call_id = repo.insert_call(sample_metadata, sample_turns)
        turns = repo.get_turns_for_range(call_id, 10, 20)
        assert turns == []
