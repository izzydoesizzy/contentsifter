"""Claude-powered semantic search for ContentSifter."""

from __future__ import annotations

import json
import logging
import re

from contentsifter.llm.client import complete_with_retry
from contentsifter.search.filters import SearchFilters
from contentsifter.search.keyword import keyword_search
from contentsifter.storage.database import Database

logger = logging.getLogger(__name__)

QUERY_EXPANSION_SYSTEM = """\
You are a search query expert. Given a natural language question about career coaching content,
generate an FTS5 search query that will find relevant results.

The content database contains career coaching extractions in these categories:
- Q&As (questions and answers about job search)
- Testimonials (success stories, wins)
- Playbooks (step-by-step advice, frameworks)
- Stories (anecdotes, examples)

Common topics: linkedin, networking, resume, interviews, salary negotiation,
mindset, confidence, personal branding, career transition, job search strategy,
follow up, company research, recruiter, informational interviews.

Return ONLY a JSON object with:
- "fts_query": an FTS5 query string (use OR for synonyms, quotes for phrases)
- "keywords": list of key terms to search for

Example: For "what should I do when a company ghosts me after an interview"
{
  "fts_query": "ghost* OR \"no response\" OR \"follow up\" OR rejection OR \"after interview\"",
  "keywords": ["ghosting", "follow up", "no response", "rejection", "interview"]
}"""

RERANK_SYSTEM = """\
You are ranking search results for relevance to a user's query about career coaching content.

Score each result from 0.0 to 1.0 based on how well it answers the query.
Return ONLY a JSON array of objects with "id" and "score" fields, ordered by score descending.

Only include results with score >= 0.3."""


def semantic_search(
    db: Database,
    query: str,
    llm_client,
    filters: SearchFilters | None = None,
) -> list[dict]:
    """Two-stage semantic search:
    1. Expand query into FTS5 terms using Claude
    2. Retrieve candidates via FTS5
    3. Re-rank candidates using Claude
    """
    if filters is None:
        filters = SearchFilters()

    # Stage 1: Query expansion
    expansion_response = complete_with_retry(
        llm_client,
        system=QUERY_EXPANSION_SYSTEM,
        user=f"User query: {query}",
        max_tokens=512,
    )

    try:
        text = expansion_response.content.strip()
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        expansion = json.loads(text)
        fts_query = expansion.get("fts_query", query)
    except (json.JSONDecodeError, KeyError):
        fts_query = query

    # Stage 2: Retrieve candidates (get more than needed for re-ranking)
    original_limit = filters.limit
    filters.limit = min(original_limit * 3, 60)
    candidates = keyword_search(db, fts_query, filters)
    filters.limit = original_limit

    if not candidates:
        return []

    # Stage 3: Re-rank with Claude
    candidate_summaries = []
    for c in candidates:
        candidate_summaries.append({
            "id": c["id"],
            "category": c["category"],
            "title": c["title"],
            "content": c["content"][:500],
        })

    rerank_response = complete_with_retry(
        llm_client,
        system=RERANK_SYSTEM,
        user=f"Query: {query}\n\nResults:\n{json.dumps(candidate_summaries, indent=2)}",
        max_tokens=2048,
    )

    try:
        text = rerank_response.content.strip()
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        rankings = json.loads(text)
    except (json.JSONDecodeError, KeyError):
        # If re-ranking fails, return candidates as-is
        return candidates[:original_limit]

    # Build ranked results
    candidate_map = {c["id"]: c for c in candidates}
    ranked_results = []
    for r in rankings[:original_limit]:
        cid = r.get("id")
        if cid in candidate_map:
            result = candidate_map[cid]
            result["relevance_score"] = r.get("score", 0.0)
            ranked_results.append(result)

    return ranked_results
