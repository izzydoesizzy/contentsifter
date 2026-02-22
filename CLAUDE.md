# ContentSifter

A multi-client content pipeline that turns existing content (transcripts, posts, emails, blogs) and voice capture interviews into a searchable content bank, then generates publication-ready drafts in the client's voice across 9 formats.

Built for [ClearCareer](https://joinclearcareer.com), extended to support any number of clients.

## Project Structure
- `src/contentsifter/` - Main package
- `transcripts/` - Source merged markdown files (10 files, ~19MB, 113 transcripts)
- `data/` - Databases and exports (gitignored)
- `data/contentsifter.db` - Default client SQLite database with FTS5
- `data/clients/{slug}/contentsifter.db` - Per-client databases
- `clients.json` - Client registry (project root)
- `content/` - Generated content, voice prints, calendars, drafts
- `content/ai-gate.md` - AI detection patterns (shared across clients)
- `content/clients/{slug}/` - Per-client content directories

## Multi-Client Support

All commands accept `-C <slug>` before the command name to target a specific client.
Without `-C`, commands use the default client from `clients.json`.

### Client Management
```bash
contentsifter client create jsmith --name "Jane Smith" --email jane@example.com
contentsifter client list
contentsifter client info jsmith
contentsifter client set-default jsmith
```

### Per-Client Data Layout
```
data/clients/{slug}/contentsifter.db    # Client's database
content/clients/{slug}/voice-print.md   # Client's voice profile
content/clients/{slug}/drafts/          # Generated drafts
content/clients/{slug}/calendar/        # Weekly calendars
content/clients/{slug}/interview-guide.md  # Generated questionnaire
```

## Voice Capture Interview Commands
```bash
# Generate a questionnaire (85+ questions across 9 categories)
contentsifter -C jsmith interview generate
contentsifter -C jsmith interview generate --niche "financial planning"  # Add niche-specific Qs

# Ingest a completed voice transcript
contentsifter -C jsmith interview ingest ./transcript.txt
contentsifter -C jsmith interview ingest ./transcript.txt --questionnaire ./custom-guide.md

# Check interview ingestion status
contentsifter -C jsmith interview status
```

### Interview Workflow
1. `interview generate` creates a markdown questionnaire
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
# Check what needs processing:
get_pending_summary()
# Process calls (Claude Code provides the LLM client):
process_calls(call_ids=[3,4,5], llm_client=llm)
```

## Architecture
- **Config:** `config.py` — ClientConfig dataclass, client registry (`clients.json`), path resolution
- **Parser:** splits merged markdown files, parses metadata and speaker turns
- **Chunker:** uses Claude to identify topic segments in each call
- **Extractor:** uses Claude to extract Q&As, testimonials, playbooks, stories
- **Ingest:** reads content files (.md, .txt), auto-detects type, splits on `---`, stores in DB
- **Interview:** 85-question prompt library, questionnaire generator, fuzzy-match transcript parser
- **Storage:** SQLite with FTS5 for full-text search, content_items table for ingested content
- **Search:** keyword (FTS5 with Porter stemming) + semantic (Claude-powered re-ranking)
- **Generate:** content drafts in 9 formats with voice-print matching and content gates
- **Planning:** template bank, 3-pass voice analysis, weekly content calendar

### Generate Format Options
`linkedin`, `newsletter`, `thread`, `playbook`, `video-script`, `carousel`, `email-welcome`, `email-weekly`, `email-sales`

### Content Gates
Every generated draft passes through two validation gates (in order):
1. **AI Gate** (`content/ai-gate.md`) — Catches AI-sounding patterns (em dashes, hedging, five-dollar words, formulaic structure)
2. **Voice Gate** (client's `voice-print.md`) — Rewrites to match client's voice (tone, vocabulary, sentence patterns, energy)

Gates run automatically when voice print is enabled. Use `--skip-gates` to bypass.

### Weekly Calendar Schedule
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
pip install -e ".[dev]"
pytest
```
