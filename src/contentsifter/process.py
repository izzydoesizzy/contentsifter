"""Batch processing functions for running extraction from Claude Code.

These functions are designed to be called directly by Claude Code
in conversation, bypassing the CLI for the AI-dependent steps.
The non-AI CLI commands (parse, search, status, export, stats) work standalone.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from contentsifter.extraction.chunker import chunk_transcript
from contentsifter.extraction.extractor import extract_from_chunk
from contentsifter.storage.database import Database
from contentsifter.storage.repository import Repository

DEFAULT_DB = Path(__file__).parent.parent.parent / "data" / "contentsifter.db"


def process_calls(
    call_ids: list[int] | None = None,
    stages: list[str] | None = None,
    limit: int | None = None,
    db_path: Path = DEFAULT_DB,
    llm_client=None,
) -> dict:
    """Process calls through chunking and extraction.

    Args:
        call_ids: Specific call IDs to process. If None, processes all pending.
        stages: Which stages to run. Default: ["chunk", "extract"]
        limit: Max calls to process.
        db_path: Path to the database.
        llm_client: An LLM client instance (required).

    Returns:
        Summary dict with counts of what was processed.
    """
    if stages is None:
        stages = ["chunk", "extract"]

    results = {"chunked": 0, "chunks_created": 0, "extracted": 0, "extractions_created": 0, "errors": []}

    with Database(db_path) as db:
        repo = Repository(db)

        # Chunking
        if "chunk" in stages:
            if call_ids:
                chunk_ids = call_ids
            else:
                chunk_ids = repo.get_calls_needing_stage("chunked")
            if limit:
                chunk_ids = chunk_ids[:limit]

            for cid in chunk_ids:
                call = repo.get_call_by_id(cid)
                if not call:
                    continue

                turns = repo.get_turns_for_call(cid)
                print(f"Chunking call {cid}: {call['title'][:60]}... ({len(turns)} turns)")

                try:
                    chunks = chunk_transcript(
                        cid, call["title"], call["call_date"],
                        call["call_type"], turns, llm_client,
                    )
                    repo.insert_topic_chunks(cid, chunks)
                    results["chunked"] += 1
                    results["chunks_created"] += len(chunks)
                    print(f"  -> {len(chunks)} topic segments")
                except Exception as e:
                    results["errors"].append(f"Chunk call {cid}: {e}")
                    print(f"  -> ERROR: {e}")

        # Extraction
        if "extract" in stages:
            if call_ids:
                extract_ids = call_ids
            else:
                extract_ids = repo.get_calls_needing_stage("extracted")
            if limit:
                extract_ids = extract_ids[:limit]

            for cid in extract_ids:
                call = repo.get_call_by_id(cid)
                if not call:
                    continue

                chunks = repo.get_chunks_for_call(cid)
                if not chunks:
                    continue

                print(f"Extracting call {cid}: {call['title'][:60]}... ({len(chunks)} chunks)")
                call_count = 0

                for chunk_data in chunks:
                    turns = repo.get_turns_for_range(
                        cid, chunk_data["start_turn_index"], chunk_data["end_turn_index"]
                    )
                    if not turns:
                        continue

                    try:
                        extractions = extract_from_chunk(
                            turns, call["call_type"], call["call_date"],
                            chunk_data["topic_title"], chunk_data["topic_summary"],
                            llm_client,
                        )
                        if extractions:
                            repo.insert_extractions(cid, chunk_data["id"], extractions)
                            call_count += len(extractions)
                    except Exception as e:
                        results["errors"].append(f"Extract call {cid} chunk '{chunk_data['topic_title']}': {e}")

                repo.mark_extracted(cid)
                results["extracted"] += 1
                results["extractions_created"] += call_count
                print(f"  -> {call_count} items extracted")

    return results


def get_pending_summary(db_path: Path = DEFAULT_DB) -> dict:
    """Get a summary of what still needs processing."""
    with Database(db_path) as db:
        repo = Repository(db)
        needs_chunking = repo.get_calls_needing_stage("chunked")
        needs_extraction = repo.get_calls_needing_stage("extracted")
        summary = repo.get_progress_summary()

        return {
            "total_calls": summary["total_calls"],
            "needs_chunking": len(needs_chunking),
            "needs_extraction": len(needs_extraction),
            "chunking_ids": needs_chunking[:10],  # first 10 for reference
            "extraction_ids": needs_extraction[:10],
            "stages": summary["stages"],
            "extractions": summary["extractions"],
            "total_extractions": summary["total_extractions"],
        }
