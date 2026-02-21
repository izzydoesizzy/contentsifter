# ContentSifter

A Python CLI tool that extracts searchable content from coaching call transcripts and generates draft content for repurposing. Built for the [ClearCareer](https://joinclearcareer.com) career coaching program.

ContentSifter processes raw transcript files through an AI-powered pipeline that identifies topics, extracts valuable content (Q&As, playbooks, testimonials, stories), and stores everything in a searchable SQLite database with full-text search.

## What It Does

1. **Parses** merged markdown transcript files into individual call records
2. **Chunks** each call into topic segments using Claude AI
3. **Extracts** reusable content: Q&As, playbooks, testimonials, and stories
4. **Searches** the content bank via keyword (FTS5) or semantic (Claude-powered) search
5. **Generates** draft content in multiple formats (LinkedIn posts, newsletters, threads, playbooks)

## Quick Start

### Prerequisites

- Python 3.10+
- [Anthropic API key](https://console.anthropic.com/) (for AI-powered commands)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/contentsifter.git
cd contentsifter

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install the package in editable mode
pip install -e .

# Set your API key (required for AI commands)
export ANTHROPIC_API_KEY="your-key-here"
```

### Verify installation

```bash
contentsifter --help
```

## Usage

### Step 1: Parse transcripts into the database

Place your merged markdown transcript files in the `transcripts/` directory, then run:

```bash
contentsifter parse --input ./transcripts/
```

This reads all `.md` files, splits them on `<!-- SOURCE FILE: ... -->` markers, parses metadata (date, title, participants, call type) and speaker turns, and stores everything in the SQLite database at `data/contentsifter.db`.

**What gets stored:** Each call's title, date, type, participants, and every speaker turn with timestamps.

### Step 2: Run the AI extraction pipeline

You can run each stage individually or all at once:

```bash
# All-in-one: parse + chunk + extract
contentsifter sift --input ./transcripts/

# Or run stages separately:
contentsifter chunk      # Topic segmentation via Claude
contentsifter extract    # Content extraction from chunks
```

**What happens:**
- **Chunking** sends each transcript to Claude to identify topic segments (e.g., "LinkedIn profile optimization", "handling interview rejection")
- **Extraction** processes each topic chunk and pulls out categorized content items with quality scores

### Step 3: Check progress

```bash
contentsifter status
```

Shows a progress table with counts for each pipeline stage (parsed, chunked, extracted) and a breakdown of extractions by category.

### Step 4: Search your content bank

```bash
contentsifter search "linkedin"
```

See the [Search Reference](#search-reference) below for all search options.

### Step 5: Generate content drafts

```bash
contentsifter generate -q "networking tips" -f linkedin
```

See the [Generate Reference](#generate-reference) below for all format options.

---

## Command Reference

### Global Options

Every command supports these options:

| Option | Default | Description |
|--------|---------|-------------|
| `--db PATH` | `data/contentsifter.db` | Path to the SQLite database |
| `--llm-mode [auto\|api\|claude-code]` | `auto` | How to access Claude (`auto` tries API key first) |
| `--model MODEL` | `claude-sonnet-4-20250514` | Claude model to use |
| `-v, --verbose` | off | Enable debug logging |

### `parse` — Import transcripts

```bash
contentsifter parse --input ./transcripts/
contentsifter parse --input ./transcripts/specific-file.md
```

| Option | Required | Description |
|--------|----------|-------------|
| `-i, --input PATH` | Yes | Transcript file or directory to parse |

Idempotent — re-running skips already-parsed calls.

### `chunk` — Topic segmentation (requires AI)

```bash
contentsifter chunk                  # Process all un-chunked calls
contentsifter chunk --call-id 42     # Process a specific call
contentsifter chunk --limit 10       # Process up to 10 calls
contentsifter chunk --force          # Re-process already chunked calls
```

| Option | Description |
|--------|-------------|
| `--call-id INT` | Process a specific call by ID |
| `--limit INT` | Max number of calls to process |
| `--force` | Re-process already chunked calls |

### `extract` — Content extraction (requires AI)

```bash
contentsifter extract                # Process all chunked-but-not-extracted calls
contentsifter extract --call-id 42   # Extract from a specific call
contentsifter extract --limit 5      # Process up to 5 calls
```

Same options as `chunk`.

### `sift` — Full pipeline (parse + chunk + extract)

```bash
contentsifter sift --input ./transcripts/
contentsifter sift --input ./transcripts/ --limit 10
contentsifter sift --dry-run         # Preview what would be processed
```

| Option | Description |
|--------|-------------|
| `-i, --input PATH` | Transcript directory (triggers parse step) |
| `--limit INT` | Max calls per stage |
| `--dry-run` | Show what would be processed without doing it |

### `status` — Processing progress

```bash
contentsifter status
```

No options. Shows pipeline progress and extraction category counts.

### `stats` — Database statistics

```bash
contentsifter stats
```

Shows detailed breakdowns: calls by type, date range, total speaker turns, and top tags.

### `export` — JSON export

```bash
contentsifter export                            # Export to default location
contentsifter export --output ./my-exports/     # Custom output directory
```

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output PATH` | `data/exports/` | Output directory |

Creates three outputs:
- `full_export.json` — all extractions in a single file
- `by_category/` — one JSON file per category (qa.json, playbook.json, etc.)
- `by_call/` — one JSON file per call with its extractions

---

## Search Reference

### Basic keyword search

```bash
contentsifter search "linkedin"
```

Uses SQLite FTS5 full-text search with Porter stemming. Matches against extraction titles, content, raw quotes, and context notes.

### Semantic search (requires AI)

```bash
contentsifter search "how do I deal with being ghosted after interviews" --semantic
```

Expands your query using Claude, runs multiple FTS5 searches, then re-ranks results by relevance using Claude. Better for natural language questions.

### Filter options

| Option | Description | Example |
|--------|-------------|---------|
| `-c, --category CAT` | Filter by content category | `-c playbook -c qa` |
| `-t, --tag TAG` | Filter by tag | `-t linkedin -t networking` |
| `--date-from DATE` | Calls from this date | `--date-from 2024-06-01` |
| `--date-to DATE` | Calls up to this date | `--date-to 2024-12-31` |
| `--call-type TYPE` | Filter by call type | `--call-type group_qa` |
| `--min-quality INT` | Minimum quality score (1-5) | `--min-quality 4` |
| `--limit INT` | Max results (default: 20) | `--limit 50` |
| `--output-format FMT` | `table`, `json`, or `full` | `--output-format full` |

### Output formats

- **`table`** (default) — compact table with category, quality score, title, date, tags
- **`full`** — complete content with raw quotes and metadata
- **`json`** — raw JSON output for piping to other tools

### Search examples

```bash
# Find all high-quality playbooks about LinkedIn
contentsifter search "linkedin" -c playbook --min-quality 4

# Find testimonials from group Q&A calls
contentsifter search "landed" -c testimonial --call-type group_qa

# Find networking advice from 2024
contentsifter search "networking" --date-from 2024-01-01 --date-to 2024-12-31

# Semantic search for complex questions
contentsifter search "what should I do when a recruiter stops responding" --semantic

# Get full details including raw quotes
contentsifter search "resume" --output-format full --limit 5

# Export search results as JSON
contentsifter search "salary" --output-format json > salary_results.json

# Combine multiple filters
contentsifter search "interview" -c playbook -c qa -t interviews --min-quality 3 --limit 30
```

### Available categories

| Category | Key | Description |
|----------|-----|-------------|
| Q&A | `qa` | Questions asked and answers given |
| Testimonial | `testimonial` | Success stories, wins, positive feedback |
| Playbook | `playbook` | Step-by-step advice, frameworks, methodologies |
| Story | `story` | Personal stories, anecdotes, illustrative examples |

### Available tags

| Tag | Description |
|-----|-------------|
| `linkedin` | LinkedIn profile, posting, networking on LinkedIn |
| `networking` | Networking strategy, events, connections |
| `resume` | Resume writing, formatting, tailoring |
| `interviews` | Interview preparation, techniques, follow-up |
| `cover_letter` | Cover letter writing |
| `salary_negotiation` | Salary negotiation, compensation discussion |
| `mindset` | Mindset, motivation, overcoming doubt |
| `confidence` | Building confidence, self-advocacy |
| `personal_branding` | Personal brand, differentiation |
| `career_transition` | Changing careers, pivoting industries |
| `job_search_strategy` | Overall job search approach, planning |
| `follow_up` | Following up with contacts, applications |
| `company_research` | Researching companies, due diligence |
| `recruiter` | Working with recruiters |
| `informational_interview` | Informational interviews, coffee chats |
| `remote_work` | Remote work, hybrid arrangements |
| `portfolio` | Portfolio, work samples |
| `references` | References, recommendations |
| `onboarding` | Starting a new role |
| `rejection_handling` | Handling rejection, ghosting |
| `time_management` | Time management, productivity |
| `ai_tools` | AI tools for job search |
| `volunteer` | Volunteering, pro bono work |
| `entrepreneurship` | Entrepreneurship, starting a business |
| `freelancing` | Freelancing, contract work |

### Available call types

| Call Type | Description |
|-----------|-------------|
| `group_qa` | Weekly group Q&A sessions |
| `group_call` | General group calls |
| `discovery` | Introductory discovery calls |
| `coaching` | 1-on-1 coaching calls |
| `workshop` | Workshops (Ask a Recruiter, Career Storytelling, etc.) |
| `body_doubling` | Body doubling co-working sessions |
| `welcome` | New member welcome calls |
| `onboarding` | Onboarding calls |

---

## Generate Reference

Generate content drafts from your extracted content bank.

```bash
contentsifter generate -q "QUERY" -f FORMAT [OPTIONS]
```

| Option | Required | Description |
|--------|----------|-------------|
| `-q, --query TEXT` | Yes | Search query to find source material |
| `-f, --format FORMAT` | Yes | Output format (see below) |
| `--topic TEXT` | No | Topic/title for the generated content |
| `-c, --category CAT` | No | Filter source material by category |
| `--min-quality INT` | No | Minimum quality score (default: 3) |
| `--limit INT` | No | Max source items to use (default: 10) |

### Available formats

| Format | Description |
|--------|-------------|
| `linkedin` | LinkedIn post (~200 words, hook + insight + CTA) |
| `newsletter` | Email newsletter section (longer, more detailed) |
| `thread` | Multi-part thread format (numbered posts) |
| `playbook` | Step-by-step guide with structured sections |

### Generate examples

```bash
# LinkedIn post about networking
contentsifter generate -q "networking" -f linkedin

# Newsletter section about interview prep using only playbook extractions
contentsifter generate -q "interview preparation" -f newsletter -c playbook

# Thread from high-quality testimonials
contentsifter generate -q "success story" -f thread -c testimonial --min-quality 4

# Playbook guide about LinkedIn optimization
contentsifter generate -q "linkedin profile" -f playbook --topic "LinkedIn Profile Optimization"
```

---

## Direct Database Access

The database is a standard SQLite file at `data/contentsifter.db`. You can query it directly for advanced use cases.

### Open the database

```bash
sqlite3 data/contentsifter.db
```

Enable useful settings:

```sql
.mode column
.headers on
```

### Useful queries

**List all calls:**
```sql
SELECT id, call_date, call_type, title, turn_count
FROM calls
ORDER BY call_date;
```

**View all extractions:**
```sql
SELECT e.id, e.category, e.quality_score, e.title, c.call_date
FROM extractions e
JOIN calls c ON e.call_id = c.id
ORDER BY e.quality_score DESC;
```

**Extractions by category:**
```sql
SELECT category, COUNT(*) as count
FROM extractions
GROUP BY category
ORDER BY count DESC;
```

**Top-quality extractions (score 5):**
```sql
SELECT e.category, e.title, e.content, c.title as call_title, c.call_date
FROM extractions e
JOIN calls c ON e.call_id = c.id
WHERE e.quality_score = 5
ORDER BY c.call_date DESC;
```

**Full-text search on extractions:**
```sql
SELECT e.id, e.category, e.title, snippet(extractions_fts, 1, '>>>', '<<<', '...', 30) as match
FROM extractions_fts
JOIN extractions e ON extractions_fts.rowid = e.id
WHERE extractions_fts MATCH 'linkedin networking'
ORDER BY rank;
```

**Full-text search on raw transcript text:**
```sql
SELECT st.speaker_name, st.timestamp, snippet(speaker_turns_fts, 0, '>>>', '<<<', '...', 30) as match
FROM speaker_turns_fts
JOIN speaker_turns st ON speaker_turns_fts.rowid = st.id
WHERE speaker_turns_fts MATCH 'salary negotiation'
ORDER BY rank
LIMIT 20;
```

**Extractions with their tags:**
```sql
SELECT e.id, e.category, e.title, GROUP_CONCAT(t.name, ', ') as tags
FROM extractions e
LEFT JOIN extraction_tags et ON e.id = et.extraction_id
LEFT JOIN tags t ON et.tag_id = t.id
GROUP BY e.id
ORDER BY e.quality_score DESC;
```

**Find extractions by tag:**
```sql
SELECT e.category, e.title, e.quality_score, c.call_date
FROM extractions e
JOIN extraction_tags et ON e.id = et.extraction_id
JOIN tags t ON et.tag_id = t.id
JOIN calls c ON e.call_id = c.id
WHERE t.name = 'linkedin'
ORDER BY e.quality_score DESC;
```

**Tag frequency:**
```sql
SELECT t.name, COUNT(*) as usage_count
FROM tags t
JOIN extraction_tags et ON t.id = et.tag_id
GROUP BY t.name
ORDER BY usage_count DESC;
```

**Calls by type with extraction counts:**
```sql
SELECT c.call_type, COUNT(DISTINCT c.id) as calls, COUNT(e.id) as extractions
FROM calls c
LEFT JOIN extractions e ON c.id = e.call_id
GROUP BY c.call_type
ORDER BY calls DESC;
```

**Processing pipeline status:**
```sql
SELECT stage, status, COUNT(*) as count
FROM processing_log
GROUP BY stage, status
ORDER BY stage;
```

**Find a specific speaker's contributions:**
```sql
SELECT c.title, c.call_date, st.timestamp, st.text
FROM speaker_turns st
JOIN calls c ON st.call_id = c.id
WHERE st.speaker_name LIKE '%Izzy%'
ORDER BY c.call_date, st.turn_index
LIMIT 50;
```

**Extractions with full context (call + chunk + tags):**
```sql
SELECT
    e.id,
    e.category,
    e.title,
    e.content,
    e.raw_quote,
    e.quality_score,
    e.speaker,
    tc.topic_title as chunk_topic,
    c.title as call_title,
    c.call_date,
    c.call_type,
    GROUP_CONCAT(t.name, ', ') as tags
FROM extractions e
JOIN calls c ON e.call_id = c.id
LEFT JOIN topic_chunks tc ON e.chunk_id = tc.id
LEFT JOIN extraction_tags et ON e.id = et.extraction_id
LEFT JOIN tags t ON et.tag_id = t.id
GROUP BY e.id
ORDER BY e.quality_score DESC, c.call_date DESC;
```

**Date range statistics:**
```sql
SELECT
    strftime('%Y-%m', call_date) as month,
    COUNT(*) as calls,
    SUM(turn_count) as total_turns
FROM calls
GROUP BY month
ORDER BY month;
```

---

## Database Schema

The SQLite database contains these tables:

| Table | Description |
|-------|-------------|
| `calls` | Individual coaching calls (title, date, type, turn count) |
| `participants` | Per-call participant list (name, email, is_coach flag) |
| `speaker_turns` | Every speaker turn with text and timestamps |
| `topic_chunks` | AI-identified topic segments per call |
| `extractions` | Extracted content items (the core output) |
| `tags` | Topic tag definitions |
| `extraction_tags` | Many-to-many link between extractions and tags |
| `processing_log` | Pipeline stage tracking (parsed/chunked/extracted) |
| `extractions_fts` | FTS5 virtual table for extraction full-text search |
| `speaker_turns_fts` | FTS5 virtual table for raw transcript search |

---

## Architecture

```
transcripts/*.md
       │
       ▼
   ┌────────┐     Split on <!-- SOURCE FILE --> markers,
   │ Parser │     parse metadata + speaker turns
   └────┬───┘
        │
        ▼
   ┌────────┐     Claude identifies topic boundaries
   │Chunker │     in each transcript
   └────┬───┘
        │
        ▼
  ┌──────────┐    Claude extracts Q&As, playbooks,
  │Extractor │    testimonials, stories per chunk
  └─────┬────┘
        │
        ▼
  ┌──────────┐    SQLite + FTS5, searchable
  │ Database │    via CLI or direct SQL
  └─────┬────┘
        │
        ▼
  ┌──────────┐    LinkedIn, newsletter, thread,
  │Generator │    playbook format drafts
  └──────────┘
```

### Project structure

```
contentsifter/
├── pyproject.toml                    # Build config & dependencies
├── CLAUDE.md                         # AI assistant context
├── src/contentsifter/
│   ├── cli.py                        # Click CLI commands
│   ├── config.py                     # Paths, constants, call type mapping
│   ├── process.py                    # Batch processing helper
│   ├── parser/
│   │   ├── splitter.py               # Split merged markdown files
│   │   ├── metadata.py               # Parse date, title, participants
│   │   └── turns.py                  # Parse speaker turn dicts
│   ├── extraction/
│   │   ├── chunker.py                # Topic segmentation via Claude
│   │   ├── extractor.py              # Content extraction per chunk
│   │   ├── prompts.py                # Prompt templates
│   │   └── categories.py             # Category & tag definitions
│   ├── llm/
│   │   └── client.py                 # Claude API client
│   ├── storage/
│   │   ├── database.py               # SQLite schema, FTS5
│   │   ├── models.py                 # Dataclasses
│   │   ├── repository.py             # CRUD operations
│   │   └── export.py                 # JSON export
│   ├── search/
│   │   ├── keyword.py                # FTS5 keyword search
│   │   ├── semantic.py               # Claude-powered semantic search
│   │   └── filters.py                # Filter builder
│   └── generate/
│       ├── drafts.py                 # Content generation
│       └── templates.py              # Format templates
└── data/                             # Generated (gitignored)
    ├── contentsifter.db
    └── exports/
```

## Dependencies

| Package | Purpose |
|---------|---------|
| [Click](https://click.palletsprojects.com/) | CLI framework |
| [Anthropic](https://docs.anthropic.com/en/docs/client-sdks/python) | Claude API client |
| [Rich](https://rich.readthedocs.io/) | Terminal formatting (tables, progress bars, colors) |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run a specific test
pytest tests/test_parser.py -v
```

## License

Private project — not for redistribution.
