# ContentSifter

A multi-client content pipeline that turns existing content (transcripts, posts, emails, blogs) and voice capture interviews into a searchable content bank, then generates publication-ready drafts in the client's voice across 9 formats. Includes a web UI for drag/drop intake, live search, and pipeline management.

Built for [ClearCareer](https://joinclearcareer.com), extended to support any number of clients.

## Project Structure

```
src/contentsifter/
  cli.py                         # Click CLI commands
  config.py                      # Paths, client config, constants
  process.py                     # Batch processing for Claude Code
  ingest/
    reader.py                    # File reading + DB insertion
    formats.py                   # Format-specific parsers (split on ---, frontmatter)
    autoformat.py                # AI-powered format detection + Claude reformatting
  parser/
    splitter.py                  # Split merged markdown files
    metadata.py                  # Parse date, title, participants
    turns.py                     # Parse speaker turns (ast.literal_eval)
  extraction/
    chunker.py                   # Topic segmentation via Claude
    extractor.py                 # Content extraction per chunk
    prompts.py / categories.py   # Prompt templates + tag definitions
  llm/
    client.py                    # API, Claude Code, callback modes
  storage/
    database.py                  # SQLite schema, FTS5, triggers
    models.py                    # Dataclasses
    repository.py                # CRUD operations
    export.py                    # JSON export
  search/
    keyword.py                   # FTS5 keyword search (Porter stemming)
    semantic.py                  # Claude-powered re-ranking
    filters.py                   # SearchFilters dataclass
  generate/
    drafts.py                    # Draft generation + gate integration
    templates.py                 # 9 format templates
    gates.py                     # AI detection + voice matching gates
  interview/
    prompts.py                   # 85-question prompt library (9 categories)
    generator.py                 # Questionnaire markdown generator
    parser.py                    # Fuzzy-match transcript parser
  planning/
    calendar.py                  # Weekly calendar generator
    voiceprint.py                # 3-pass voice analysis
    templates_static.py          # Curated content frameworks
    prompts.py / writer.py       # Voice analysis prompts + file I/O
  web/
    app.py                       # FastAPI app factory
    deps.py                      # Dependency injection (get_db, content_summary)
    routes/
      dashboard.py               # Client dashboard
      clients.py                 # Client CRUD
      ingest.py                  # File upload + auto-format
      interview.py               # Questionnaire generation + preview
      search.py                  # Live FTS5 search
      status.py                  # Pipeline progress
    templates/                   # Jinja2 templates (base + components + pages)
    static/                      # CSS + JS (dropzone, flash messages)
```

### Data Layout
```
clients.json                               # Client registry
data/contentsifter.db                      # Default client DB
data/clients/{slug}/contentsifter.db       # Per-client databases
content/voice-print.md                     # Default client voice profile
content/ai-gate.md                         # AI detection patterns (shared)
content/clients/{slug}/voice-print.md      # Per-client voice profiles
content/clients/{slug}/drafts/             # Generated drafts
content/clients/{slug}/calendar/           # Weekly calendars
content/clients/{slug}/interview-guide.md  # Generated questionnaire
```

## Multi-Client Support

All commands accept `-C <slug>` before the command name. Without `-C`, uses the default from `clients.json`.

### Client Management
```bash
contentsifter client create jsmith --name "Jane Smith" --email jane@example.com
contentsifter client list
contentsifter client info jsmith
contentsifter client set-default jsmith
```

### Workflow Commands
```bash
# Guided onboarding: creates client + questionnaire + optional ingest
contentsifter onboard jsmith --name "Jane Smith" --email jane@example.com
contentsifter onboard jsmith --name "Jane" -i ./posts.md -t linkedin
contentsifter onboard jsmith --name "Jane" --niche "financial planning"

# Pipeline status: shows everything + suggests next steps
contentsifter -C jsmith pipeline
```

## Web UI

```bash
pip install -e ".[web]"           # Install web dependencies (FastAPI, uvicorn, Jinja2, htmx)
contentsifter web                  # Start on localhost:8000
contentsifter web --port 3000     # Custom port
contentsifter web --host 0.0.0.0  # Allow external access
contentsifter web --reload        # Auto-reload on code changes (development)
```

### Pages
| URL | Page | Description |
|-----|------|-------------|
| `/` | Redirect | Redirects to default client dashboard |
| `/{slug}` | Dashboard | Stat cards, quick actions, content breakdown |
| `/clients/` | Clients | Client list table with inline create form (htmx) |
| `/clients/{slug}` | Client Detail | Client info, stats, set-default button |
| `/{slug}/ingest` | Upload | Drag/drop file upload with content type selector |
| `/{slug}/search` | Search | Live FTS5 search with category filter dropdown |
| `/{slug}/interview` | Interview | Generate questionnaire, inline markdown preview |
| `/{slug}/status` | Status | Pipeline progress bars, content breakdown, suggestions |

### Auto-Format (AI Upload)
When uploading files, the "Auto-format with AI" checkbox uses Claude to restructure raw text into the expected format (adding `---` dividers, `title:`/`date:` frontmatter, etc.).
- Requires `ANTHROPIC_API_KEY` env var (checkbox disabled without it)
- Logic in `ingest/autoformat.py`: `needs_formatting()` detects if text is already structured, `auto_format_content()` calls Claude to reformat
- Format-specific prompts for linkedin, email, newsletter, blog, transcript

### Tech Stack
- FastAPI + Jinja2 (server-rendered) + htmx (CDN) + Tailwind CSS (CDN)
- No build step. All frontend deps via CDN.
- Design: zinc/indigo palette, fixed sidebar (240px), cards with subtle borders

## Voice Capture Interview Commands
```bash
contentsifter -C jsmith interview generate
contentsifter -C jsmith interview generate --niche "financial planning"
contentsifter -C jsmith interview ingest ./transcript.txt
contentsifter -C jsmith interview ingest ./transcript.txt --questionnaire ./custom-guide.md
contentsifter -C jsmith interview status
```

### Interview Workflow
1. `interview generate` creates a markdown questionnaire (85+ questions, 9 categories)
2. Client records answers using any voice transcription tool
3. `interview ingest` fuzzy-matches questions in the transcript and stores answers
4. Standard pipeline takes over: `voice-print` → `generate` → `plan-week`

### Interview Prompt Categories (9)
warmup (5), origin_story (10), expertise (12), client_stories (10), problems (10), contrarian (8), teaching (12), vision (8), quickfire (10) = 85 universal prompts

## Content Ingestion Commands
```bash
contentsifter -C jsmith ingest ./posts.md --type linkedin      # LinkedIn posts (split on ---)
contentsifter -C jsmith ingest ./emails/ --type email           # Email files
contentsifter -C jsmith ingest ./newsletter.md --type newsletter # One newsletter per file
contentsifter -C jsmith ingest ./blog/ --type blog              # One blog post per file
contentsifter -C jsmith ingest ./transcripts/ --type transcript  # Delegates to transcript parser
contentsifter -C jsmith ingest --status-only                    # Show ingested content counts
```

Content types: `linkedin`, `email`, `newsletter`, `blog`, `transcript`, `other`
Auto-detection from filename prefix (e.g., `linkedin-posts.md` → linkedin_post).

## Standalone CLI Commands (no AI needed)
```bash
contentsifter parse --input ./transcripts/    # Parse transcripts into DB
contentsifter status                           # Show processing progress
contentsifter export --output ./data/exports/  # Export to JSON
contentsifter stats                            # Detailed database statistics
contentsifter search "query"                   # Keyword search (FTS5)
contentsifter search "query" -c playbook       # Filter by category
contentsifter search "query" -t linkedin       # Filter by tag
contentsifter search "query" --output-format full  # Full content display
contentsifter search "query" --output-format json  # JSON output
contentsifter init-templates                   # Write content planning templates
contentsifter init-templates --force           # Overwrite existing templates
contentsifter plan-week --no-llm               # Weekly calendar with source material only
```

## AI-Powered Commands (need API key or Claude Code)
```bash
contentsifter chunk                             # Topic segmentation
contentsifter extract                           # Content extraction
contentsifter sift --input ./transcripts/       # Full pipeline (parse + chunk + extract)
contentsifter search "query" --semantic         # Semantic search (Claude re-ranking)
contentsifter generate -q "topic" -f linkedin   # Generate drafts
contentsifter generate -q "topic" -f video-script --save  # Generate + save to drafts/
contentsifter generate -q "topic" -f carousel --no-voice-print  # Without voice matching
contentsifter generate -q "topic" -f linkedin --skip-gates     # Skip content gates
contentsifter voice-print                       # Generate voice profile
contentsifter voice-print --force               # Regenerate voice profile
contentsifter voice-print --sample-size 150     # More samples per bucket
contentsifter plan-week                         # Full weekly calendar with LLM drafts
contentsifter plan-week --topic-focus networking  # Focus on a specific tag
contentsifter plan-week --skip-gates            # Skip content gates
contentsifter plan-week --week-of 2026-03-10    # Specific week
```

## Global Options
| Option | Default | Description |
|--------|---------|-------------|
| `-C, --client SLUG` | from `clients.json` | Target client |
| `--db PATH` | from client config | Override database path |
| `--llm-mode MODE` | `auto` | LLM access: `auto`, `api`, or `claude-code` |
| `--model MODEL` | `claude-sonnet-4-20250514` | Claude model |
| `-v, --verbose` | off | Debug logging |

## Running Extraction via Claude Code
When running inside Claude Code (no API key), use `process.py` directly:
```python
from contentsifter.process import process_calls, get_pending_summary
get_pending_summary()
process_calls(call_ids=[3,4,5], llm_client=llm)
```

## Generate Format Options
`linkedin`, `newsletter`, `thread`, `playbook`, `video-script`, `carousel`, `email-welcome`, `email-weekly`, `email-sales`

## Content Gates
Every generated draft passes through two validation gates (in order):
1. **AI Gate** (`content/ai-gate.md`) — Catches AI-sounding patterns (em dashes, hedging, five-dollar words, formulaic structure)
2. **Voice Gate** (client's `voice-print.md`) — Rewrites to match client's voice (tone, vocabulary, sentence patterns, energy)

Gates run automatically when voice print is enabled. Use `--skip-gates` to bypass.

## Weekly Calendar Schedule
| Day | Pillar | Format | Source Category |
|-----|--------|--------|-----------------|
| Mon | Story | LinkedIn text post | `story` |
| Tue | Playbook | LinkedIn carousel | `playbook` |
| Wed | Video | Short-form script | Any high-quality |
| Thu | Q&A | LinkedIn text post | `qa` |
| Fri | Testimonial | LinkedIn text post | `testimonial` |
| Sat | Newsletter | Weekly email | Mix of all |
| Sun | Rest | — | — |

## Content Categories
- **Q&A** (`qa`): Questions people ask and answers given
- **Testimonial** (`testimonial`): Success stories, wins, positive feedback
- **Playbook** (`playbook`): Step-by-step advice, frameworks, methodologies
- **Story** (`story`): Personal stories, anecdotes, illustrative examples

## Tag Taxonomy
linkedin, networking, resume, interviews, cover_letter, salary_negotiation, mindset, confidence, personal_branding, career_transition, job_search_strategy, follow_up, company_research, recruiter, informational_interview, remote_work, portfolio, references, onboarding, rejection_handling, time_management, ai_tools, volunteer, entrepreneurship, freelancing

## Data Format
Transcripts use Python dict literals for speaker turns — must use `ast.literal_eval`, NOT `json.loads` (data has `None` not `null`).
Each call is separated by `<!-- SOURCE FILE: ... -->` markers.

## Database Tables
| Table | What It Stores |
|-------|---------------|
| `calls` | Individual coaching calls |
| `participants` | Per-call participants |
| `speaker_turns` | Every speaker turn with text and timestamps |
| `topic_chunks` | AI-identified topic segments |
| `content_items` | Ingested written content + interview answers |
| `extractions` | Extracted content items from transcripts |
| `tags` | Topic tag definitions |
| `extraction_tags` | Links between extractions and tags |
| `processing_log` | Pipeline stage tracking |
| `extractions_fts` | FTS5 index for extractions |
| `speaker_turns_fts` | FTS5 index for raw transcripts |
| `content_items_fts` | FTS5 index for ingested content |

## Development
```bash
pip install -e ".[dev,web]"
pytest                             # Run all 232 tests
pytest tests/test_web.py           # Web tests only (27 tests)
pytest tests/test_cli.py           # CLI tests only (25 tests)
```
