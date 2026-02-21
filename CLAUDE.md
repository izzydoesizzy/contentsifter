# ContentSifter

ContentSifter is a Python CLI tool for extracting and searching through career coaching call transcripts from the ClearCareer program.

## Project Structure
- `src/contentsifter/` - Main package
- `transcripts/` - Source merged markdown files (10 files, ~19MB, 113 transcripts)
- `data/` - Generated database and exports (gitignored)
- `data/contentsifter.db` - SQLite database with FTS5

## Standalone CLI Commands (no AI needed)
```bash
contentsifter parse --input ./transcripts/    # Parse transcripts into DB
contentsifter status                           # Show processing progress
contentsifter export --output ./data/exports/  # Export to JSON
contentsifter stats                            # Detailed database statistics
contentsifter search "query"                   # Keyword search (FTS5)
contentsifter search "query" -c playbook       # Filter by category
contentsifter search "query" --output-format full  # Full content display
```

## AI-Powered Commands (need API key or Claude Code)
```bash
# These require ANTHROPIC_API_KEY env var:
contentsifter chunk                             # Topic segmentation
contentsifter extract                           # Content extraction
contentsifter sift --input ./transcripts/       # Full pipeline
contentsifter search "query" --semantic         # Semantic search
contentsifter generate -q "topic" -f linkedin   # Generate drafts
```

## Running Extraction via Claude Code
When running inside Claude Code (no API key), use `process.py` directly:
```python
from contentsifter.process import process_calls, get_pending_summary
# Check what needs processing:
get_pending_summary()
# Process calls (Claude Code provides the LLM client):
process_calls(call_ids=[3,4,5], llm_client=llm)
```

## Architecture
- **Parser:** splits merged markdown files, parses metadata and speaker turns
- **Chunker:** uses Claude to identify topic segments in each call
- **Extractor:** uses Claude to extract Q&As, testimonials, playbooks, stories
- **Storage:** SQLite with FTS5 for full-text search
- **Search:** keyword (FTS5) + semantic (Claude-powered re-ranking)
- **Generate:** content drafts (LinkedIn, newsletter, thread, playbook)

## Data Format
Transcripts use Python dict literals for speaker turns — must use `ast.literal_eval`, NOT `json.loads` (data has `None` not `null`).
Each call is separated by `<!-- SOURCE FILE: ... -->` markers.

## Content Categories
- **Q&A** (`qa`): Questions people ask and answers Izzy gives
- **Testimonial** (`testimonial`): Success stories, wins, positive feedback
- **Playbook** (`playbook`): Step-by-step advice, frameworks, methodologies
- **Story** (`story`): Personal stories, anecdotes, illustrative examples

## Tag Taxonomy
linkedin, networking, resume, interviews, cover_letter, salary_negotiation, mindset, confidence, personal_branding, career_transition, job_search_strategy, follow_up, company_research, recruiter, informational_interview, remote_work, portfolio, references, onboarding, rejection_handling, time_management, ai_tools, volunteer, entrepreneurship, freelancing

## Development
```bash
pip install -e ".[dev]"
pytest
```
