#!/usr/bin/env python3
"""Export topic chunks with their speaker turns for content extraction.

Creates batched JSON files in data/staging/chunks/ that subagents can process.
"""

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "contentsifter.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "staging" / "chunks"
BATCH_SIZE = 20  # chunks per batch file


def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Get all topic chunks with call metadata
    chunks = conn.execute("""
        SELECT tc.id as chunk_id, tc.call_id, tc.chunk_index,
               tc.topic_title, tc.topic_summary,
               tc.start_turn_index, tc.end_turn_index,
               tc.start_timestamp, tc.end_timestamp,
               tc.primary_speaker,
               c.title as call_title, c.call_date, c.call_type
        FROM topic_chunks tc
        JOIN calls c ON tc.call_id = c.id
        ORDER BY tc.call_id, tc.chunk_index
    """).fetchall()

    print(f"Found {len(chunks)} topic chunks across all calls")

    # Build batch files
    batch_num = 0
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[i:i + BATCH_SIZE]
        batch_num += 1
        batch_data = {"batch_id": batch_num, "chunks": []}

        for chunk in batch_chunks:
            chunk_dict = dict(chunk)

            # Get speaker turns for this chunk
            turns = conn.execute("""
                SELECT turn_index, speaker_name, text, timestamp
                FROM speaker_turns
                WHERE call_id = ? AND turn_index >= ? AND turn_index <= ?
                ORDER BY turn_index
            """, (chunk["call_id"], chunk["start_turn_index"], chunk["end_turn_index"])).fetchall()

            chunk_dict["turns"] = [dict(t) for t in turns]
            chunk_dict["turn_count"] = len(turns)
            batch_data["chunks"].append(chunk_dict)

        output_file = OUTPUT_DIR / f"batch_{batch_num:02d}.json"
        with open(output_file, "w") as f:
            json.dump(batch_data, f, indent=2)

        chunk_ids = [c["chunk_id"] for c in batch_chunks]
        print(f"  batch_{batch_num:02d}.json: {len(batch_chunks)} chunks (IDs {chunk_ids[0]}-{chunk_ids[-1]})")

    print(f"\nCreated {batch_num} batch files in {OUTPUT_DIR.relative_to(PROJECT_ROOT)}/")
    conn.close()


if __name__ == "__main__":
    main()
