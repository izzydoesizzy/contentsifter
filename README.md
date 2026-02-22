# ContentSifter

A tool that turns any creator's existing content into a searchable content bank and generates publication-ready drafts that sound like they wrote it themselves.

You give it someone's LinkedIn posts, emails, newsletters, blog posts, or call transcripts. It learns how they write. Then it generates new content in their voice across 9 formats.

Includes a web UI for drag-and-drop intake, live search, and pipeline management. Or use the CLI for everything.

Built for the [ClearCareer](https://joinclearcareer.com) program, now extended to support multiple clients.

---

## Quick Start

### Install

```bash
git clone https://github.com/yourusername/contentsifter.git
cd contentsifter
python3 -m venv venv
source venv/bin/activate
pip install -e ".[web]"
```

### Set API Key (optional, needed for AI features)

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Option A: Start the Web UI

```bash
contentsifter web
# Open http://localhost:8000
```

### Option B: Use the CLI

```bash
# Onboard a new client (creates account + interview questionnaire)
contentsifter onboard jsmith --name "Jane Smith" --email jane@example.com

# Ingest their content
contentsifter -C jsmith ingest ./jane-posts.md --type linkedin

# Build voice print + generate
contentsifter -C jsmith voice-print
contentsifter -C jsmith generate -q "career change" -f linkedin
```

### Verify It Works

```bash
contentsifter --help
```

---

## How It Works

ContentSifter has three intake modes depending on what content you have:

### Mode 1: Written Content (LinkedIn posts, emails, blogs)

```
Content files (.md or .txt)
       |
 [INGEST] --> content items stored in database
       |
[VOICE-PRINT] --> Claude analyzes writing patterns
       |
[GENERATE] --> 9 content formats + voice-print matching
       |
 [GATES] --> AI detection rewrite + voice matching rewrite
       |
 Final draft
```

### Mode 2: Voice Capture Interview (no existing content needed)

```
[INTERVIEW GENERATE] --> 85+ question questionnaire (9 categories)
       |
 Client records answers with any voice transcription tool
       |
[INTERVIEW INGEST] --> parses transcript, matches Q&A pairs
       |
[VOICE-PRINT] --> Claude analyzes speaking patterns
       |
[GENERATE] --> 9 formats + voice matching
```

### Mode 3: Transcripts (coaching calls, meetings, podcasts)

```
Transcripts (.md files)
       |
 [PARSE] --> individual calls, metadata, speaker turns
       |
 [CHUNK] --> Claude identifies topic segments
       |
[EXTRACT] --> Q&As, playbooks, testimonials, stories
       |
[SEARCH / GENERATE] --> keyword search or content generation
```

All three modes produce the same output: drafts that sound like the person wrote them.

---

## Web UI

ContentSifter includes a browser-based interface built with FastAPI, htmx, and Tailwind CSS. No build step required.

```bash
contentsifter web                  # Start on localhost:8000
contentsifter web --port 3000     # Custom port
contentsifter web --reload        # Auto-reload during development
```

### Pages

| Page | What It Does |
|------|-------------|
| **Dashboard** | Client overview with stat cards, quick actions, content breakdown |
| **Clients** | Create and manage clients with an inline form |
| **Upload** | Drag-and-drop file upload with content type selector and AI auto-format |
| **Search** | Live full-text search with category filtering |
| **Interview** | Generate questionnaires and preview them in-browser |
| **Status** | Pipeline progress bars, content breakdown, next-step suggestions |

### Auto-Format on Upload

When you upload a raw file (a copy-paste of LinkedIn posts, an email dump, etc.), enable "Auto-format with AI" to have Claude restructure the text into the expected format with proper `---` dividers and frontmatter. Requires `ANTHROPIC_API_KEY`.

---

## Working with Clients

ContentSifter supports multiple clients. Each gets their own database, voice print, and content directory.

### Quick Start: Onboard a New Client

```bash
contentsifter onboard jsmith --name "Jane Smith" --email jane@example.com
```

Creates the client, generates an interview questionnaire, and optionally ingests files:

```bash
contentsifter onboard jsmith --name "Jane Smith" -i ./jane-posts.md -t linkedin
```

### Managing Clients

```bash
contentsifter client create jsmith --name "Jane Smith"    # Create
contentsifter client list                                  # List all
contentsifter client info jsmith                           # Show details
contentsifter client set-default jsmith                    # Set default
```

### Switching Between Clients

Use `-C` before any command:

```bash
contentsifter -C jsmith status
contentsifter -C acme generate -q "leadership" -f linkedin
```

### Pipeline Status

Shows current state and suggests next steps:

```bash
contentsifter -C jsmith pipeline
```

---

## Ingesting Content

### LinkedIn Posts

Create a markdown file with posts separated by `---`:

```markdown
date: 2026-01-15
title: The Power of Showing Up

I had the same conversation three times this week...

---

date: 2026-01-20
title: Your Resume Is an Ad

Stop treating your resume like a job description...
```

```bash
contentsifter -C jsmith ingest ./jane-posts.md --type linkedin
```

### Other Content Types

```bash
contentsifter -C jsmith ingest ./emails.md --type email          # Split on ---
contentsifter -C jsmith ingest ./newsletter.md --type newsletter  # One per file
contentsifter -C jsmith ingest ./blog-posts/ --type blog          # One per file
contentsifter -C jsmith ingest ./transcripts/ --type transcript   # Full parser
```

### Auto-Detection

Files named with a type prefix (e.g., `linkedin-posts.md`) are auto-detected:

```bash
contentsifter -C jsmith ingest ./linkedin-posts.md    # No --type needed
```

### Check What's Ingested

```bash
contentsifter -C jsmith ingest --status-only
```

---

## Voice Capture Interviews

For new clients with no existing written content. They just talk.

### Step 1: Generate the Questionnaire

```bash
contentsifter -C jsmith interview generate
```

Creates 85+ questions across 9 categories (warmup, origin story, expertise, client stories, problems, contrarian views, teaching moments, vision, quick-fire). Add niche-specific questions:

```bash
contentsifter -C jsmith interview generate --niche "financial planning"
```

### Step 2: Client Records Answers

Send the guide to the client. They open any voice transcription tool, read each question aloud, then answer naturally.

### Step 3: Ingest the Transcript

```bash
contentsifter -C jsmith interview ingest ./jane-transcript.txt
```

Fuzzy-matches each question from the questionnaire and stores each answer as a content item.

### Step 4: Build Voice Print + Generate

```bash
contentsifter -C jsmith voice-print
contentsifter -C jsmith generate -q "career change" -f linkedin
```

---

## Building a Voice Print

The voice print is what makes generated content sound like your client.

```bash
contentsifter -C jsmith voice-print
contentsifter -C jsmith voice-print --force          # Regenerate
contentsifter -C jsmith voice-print --sample-size 150  # More samples
```

ContentSifter runs a 3-pass analysis (vocabulary, structure, synthesis) using stratified sampling across openers, closers, monologues, short punchy writing, medium explanations, and questions.

The output is saved as `voice-print.md` in the client's content directory.

---

## Generating Content

```bash
contentsifter -C jsmith generate -q "networking tips" -f linkedin
```

1. Searches the client's content bank for matching source material
2. Generates a draft in the selected format
3. Runs content gates to remove AI patterns and match the client's voice

### Available Formats

| Format | Output |
|--------|--------|
| `linkedin` | LinkedIn post (~200 words) |
| `newsletter` | Email newsletter section |
| `thread` | Multi-part thread |
| `playbook` | Step-by-step guide |
| `video-script` | Short-form video script (30-60s) |
| `carousel` | LinkedIn carousel slides |
| `email-welcome` | Welcome email |
| `email-weekly` | Weekly digest |
| `email-sales` | Sales/follow-up email |

### Options

```bash
--save                    # Save draft to disk
-c playbook               # Only use playbook extractions as source
--min-quality 4           # Only use high-quality extractions
--no-voice-print          # Skip voice matching entirely
--skip-gates              # Keep voice context but skip rewrite gates
```

### Content Gates

Every draft passes through two gates:
1. **AI Gate** -- catches AI patterns (em dashes, hedging, five-dollar words)
2. **Voice Gate** -- rewrites to match the client's voice print

Use `--skip-gates` or `--no-voice-print` to bypass.

---

## Planning a Week of Content

```bash
contentsifter -C jsmith plan-week
```

| Day | Pillar | Format |
|-----|--------|--------|
| Mon | Story | LinkedIn text post |
| Tue | Playbook | LinkedIn carousel |
| Wed | Video | Short-form script |
| Thu | Q&A | LinkedIn text post |
| Fri | Testimonial | LinkedIn text post |
| Sat | Newsletter | Weekly email |
| Sun | Rest | -- |

### Options

```bash
--no-llm                  # Source material only, no AI drafts
--topic-focus networking   # Bias toward a topic tag
--week-of 2026-03-10      # Specific start date
--skip-gates              # Faster generation
```

---

## Searching Content

```bash
contentsifter -C jsmith search "leadership"                    # Keyword (FTS5)
contentsifter -C jsmith search "imposter syndrome" --semantic   # AI re-ranking
contentsifter -C jsmith search "resume" -c playbook            # Filter by category
contentsifter -C jsmith search "salary" -t linkedin            # Filter by tag
contentsifter -C jsmith search "resume" --output-format full   # Full content
contentsifter -C jsmith search "salary" --output-format json   # JSON output
```

---

## Transcript Pipeline (Advanced)

For coaching calls, meetings, or podcast transcripts:

```bash
contentsifter -C jsmith parse --input ./transcripts/   # Parse into DB
contentsifter -C jsmith chunk                          # AI topic segmentation
contentsifter -C jsmith extract                        # AI content extraction
contentsifter -C jsmith sift --input ./transcripts/    # All three at once
```

Extracts four content categories: Q&A, Testimonial, Playbook, Story. Each gets a quality score (1-5) and topic tags.

---

## Data Commands

```bash
contentsifter -C jsmith status       # Pipeline progress
contentsifter -C jsmith stats        # Detailed statistics
contentsifter -C jsmith export       # Export to JSON (full, by_category, by_call)
contentsifter init-templates         # Write content planning template files
```

---

## Global Options

| Option | Default | Description |
|--------|---------|-------------|
| `-C, --client SLUG` | from `clients.json` | Target client |
| `--db PATH` | from client config | Override database path |
| `--llm-mode MODE` | `auto` | LLM access: `auto`, `api`, `claude-code` |
| `--model MODEL` | `claude-sonnet-4-20250514` | Claude model |
| `-v, --verbose` | off | Debug logging |

---

## Database

Each client gets their own SQLite database with FTS5 full-text search.

```
data/contentsifter.db                    # Default client
data/clients/jsmith/contentsifter.db     # Per-client
```

### Tables

| Table | Purpose |
|-------|---------|
| `calls` | Individual calls (title, date, type, turn count) |
| `participants` | Per-call participants |
| `speaker_turns` | Every speaker turn with text and timestamps |
| `topic_chunks` | AI-identified topic segments |
| `content_items` | Ingested content (LinkedIn posts, emails, interview answers) |
| `extractions` | Extracted content from transcripts |
| `tags` / `extraction_tags` | Topic tags + links |
| `processing_log` | Pipeline stage tracking |
| `*_fts` | FTS5 search indexes (extractions, turns, content items) |

### Query Directly

```bash
sqlite3 data/clients/jsmith/contentsifter.db
```

```sql
SELECT category, COUNT(*) FROM extractions GROUP BY category;
SELECT id, title, char_count FROM content_items ORDER BY created_at DESC;
```

---

## Content Categories

| Category | Key | What It Is |
|----------|-----|-----------|
| Q&A | `qa` | Questions asked and answers given |
| Testimonial | `testimonial` | Success stories, wins, positive feedback |
| Playbook | `playbook` | Step-by-step advice, frameworks, how-tos |
| Story | `story` | Personal stories, anecdotes, examples |

## Topic Tags

`linkedin` `networking` `resume` `interviews` `cover_letter` `salary_negotiation` `mindset` `confidence` `personal_branding` `career_transition` `job_search_strategy` `follow_up` `company_research` `recruiter` `informational_interview` `remote_work` `portfolio` `references` `onboarding` `rejection_handling` `time_management` `ai_tools` `volunteer` `entrepreneurship` `freelancing`

---

## File Structure

```
contentsifter/
  clients.json                    # Client registry
  pyproject.toml                  # Package config
  CLAUDE.md                       # Developer reference
  README.md                       # This file
  transcripts/                    # Source transcript files (gitignored)
  data/                           # Databases and exports (gitignored)
    contentsifter.db
    clients/{slug}/contentsifter.db
  content/                        # Generated content
    voice-print.md                # Default client voice profile
    ai-gate.md                    # AI detection patterns (shared)
    templates/                    # Content planning frameworks
    calendar/                     # Weekly content calendars
    drafts/                       # Saved generated drafts
    clients/{slug}/               # Per-client content
  src/contentsifter/              # Source code
    cli.py                        # CLI commands
    config.py                     # Client config, paths
    ingest/                       # Content ingestion + auto-format
    parser/                       # Transcript parsing
    extraction/                   # AI content extraction
    llm/                          # LLM client abstraction
    storage/                      # Database, models, repository, export
    search/                       # FTS5 keyword + semantic search
    generate/                     # Draft generation + gates
    interview/                    # Voice capture interview system
    planning/                     # Calendar, voice print, templates
    web/                          # Web UI (FastAPI + htmx + Tailwind)
  tests/                          # 232 tests
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| [Click](https://click.palletsprojects.com/) | CLI framework |
| [Anthropic](https://docs.anthropic.com/) | Claude API access |
| [Rich](https://rich.readthedocs.io/) | Terminal output (tables, colors, progress) |
| [FastAPI](https://fastapi.tiangolo.com/) | Web framework (optional `[web]` install) |
| [uvicorn](https://www.uvicorn.org/) | ASGI server (optional `[web]` install) |
| [htmx](https://htmx.org/) | Minimal interactivity (CDN, no install) |
| [Tailwind CSS](https://tailwindcss.com/) | Utility CSS (CDN, no install) |

## LLM Access Modes

| Mode | How It Works |
|------|-------------|
| **API** | Uses `ANTHROPIC_API_KEY` env var |
| **Claude Code** | Calls `claude --print` subprocess |
| **Callback** | Python function injection via `process.py` |

`--llm-mode auto` (default) tries API key first, falls back to Claude Code.

---

## Troubleshooting

### "command not found: contentsifter"

Activate your virtual environment: `source venv/bin/activate`

### "No database found"

Ingest content first: `contentsifter -C jsmith ingest ./posts.md --type linkedin`

### "Unknown client: xyz"

Create it: `contentsifter client create xyz --name "Name Here"`

### AI commands hang or timeout

Inside Claude Code, set the API key directly: `export ANTHROPIC_API_KEY="your-key"`

---

## Development

```bash
pip install -e ".[dev,web]"    # Install all dependencies
pytest                          # Run all 232 tests (1.3s)
pytest tests/test_web.py        # Web tests only (27 tests)
pytest tests/test_cli.py        # CLI tests only (25 tests)
```

## License

Private project -- not for redistribution.
