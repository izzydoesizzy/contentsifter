# ContentSifter

A CLI tool that turns any creator's existing content into a searchable content bank and generates publication-ready drafts that sound like they wrote it themselves.

You give it someone's LinkedIn posts, emails, newsletters, blog posts, or call transcripts. It learns how they write. Then it generates new content in their voice across 9 formats.

Built for the [ClearCareer](https://joinclearcareer.com) program, now extended to support multiple clients.

## How It Works

ContentSifter has two modes depending on what kind of content you're working with:

### Mode 1: Transcripts (coaching calls, meetings, podcasts)

```
Transcripts (.md files)
       |
 [PARSE] --> individual calls, metadata, speaker turns
       |
 [CHUNK] --> Claude identifies topic segments
       |
[EXTRACT] --> Q&As, playbooks, testimonials, stories
       |
[SEARCH] --> keyword (FTS5) or semantic (Claude re-ranking)
       |
[GENERATE] --> 9 content formats + voice-print matching
       |
 [GATES] --> AI detection rewrite + voice matching rewrite
       |
 Final draft (LinkedIn post, newsletter, video script, etc.)
```

### Mode 2: Written Content (LinkedIn posts, emails, blogs)

```
Content files (.md or .txt)
       |
 [INGEST] --> individual content items stored in database
       |
[VOICE-PRINT] --> Claude analyzes writing patterns
       |
[GENERATE] --> 9 content formats + voice-print matching
       |
 [GATES] --> AI detection rewrite + voice matching rewrite
       |
 Final draft (LinkedIn post, newsletter, video script, etc.)
```

### Mode 3: Voice Capture Interview (no existing content needed)

```
[INTERVIEW GENERATE] --> 85+ question questionnaire (9 categories)
       |
 Client records answers with any voice transcription tool
       |
[INTERVIEW INGEST] --> parses transcript, matches Q&A pairs
       |
[VOICE-PRINT] --> Claude analyzes speaking patterns
       |
[GENERATE] --> 9 content formats + voice-print matching
       |
 [GATES] --> AI detection rewrite + voice matching rewrite
       |
 Final draft (LinkedIn post, newsletter, video script, etc.)
```

All three modes produce the same output: drafts that sound like the person actually wrote them. Mode 3 is ideal for new clients who don't have existing written content — they just talk.

---

## Quick Start

### What You Need

- **Python 3.10 or higher.** Check with `python3 --version`. If you don't have it, install it from [python.org](https://www.python.org/downloads/).
- **An Anthropic API key** (for AI-powered commands like voice-print, generate, and extract). Get one at [console.anthropic.com](https://console.anthropic.com/). You can skip this if you only need to parse, search, and export.

### Step 1: Clone and Install

Open your terminal and run these commands one at a time:

```bash
# Download the project
git clone https://github.com/yourusername/contentsifter.git

# Move into the project folder
cd contentsifter

# Create a virtual environment (keeps dependencies separate from your system Python)
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install ContentSifter and its dependencies
pip install -e .
```

### Step 2: Set Your API Key

If you plan to use AI-powered commands (voice-print, generate, extract, chunk, semantic search):

```bash
# Add this to your shell profile (~/.zshrc or ~/.bashrc) so it persists:
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Or set it just for this session:
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Step 3: Verify It Works

```bash
contentsifter --help
```

You should see a list of commands. If you get "command not found", make sure your virtual environment is activated (you should see `(venv)` at the start of your terminal prompt).

---

## Working with Clients

ContentSifter supports multiple clients. Each client gets their own database, voice print, and content directory. This means you can manage content for many people from one installation.

### Quick Start: Onboard a New Client

The fastest way to set up a new client is the `onboard` command. It creates the client, generates an interview questionnaire, and optionally ingests files — all in one step:

```bash
contentsifter onboard jsmith --name "Jane Smith" --email jane@example.com
```

You'll be prompted for any missing details. To also ingest existing content:

```bash
contentsifter onboard jsmith --name "Jane Smith" -i ./jane-posts.md -t linkedin
```

### Creating a Client Manually

If you prefer step-by-step control:

```bash
contentsifter client create jsmith --name "Jane Smith" --email jane@example.com
```

This does three things:
1. Registers Jane in the client registry (`clients.json`)
2. Creates a database at `data/clients/jsmith/contentsifter.db`
3. Creates a content directory at `content/clients/jsmith/`

### Seeing All Your Clients

```bash
contentsifter client list
```

This shows a table of every client, their email, and which one is set as the default.

### Getting Details About a Client

```bash
contentsifter client info jsmith
```

This shows the client's database path, content directory, how many items have been ingested, and whether a voice print exists.

### Setting a Default Client

If you're working with one client all day, set them as the default so you don't have to type `-C jsmith` on every command:

```bash
contentsifter client set-default jsmith
```

Now `contentsifter status` is the same as `contentsifter -C jsmith status`.

### Switching Between Clients

Use the `-C` flag (capital C) before any command to target a specific client:

```bash
# Work with Jane
contentsifter -C jsmith status

# Work with another client
contentsifter -C acme status

# Work with the default client (no flag needed)
contentsifter status
```

The `-C` flag must come **before** the command name, not after it.

### Checking Pipeline Status

The `pipeline` command shows everything about a client's current state — what's been ingested, what's been extracted, whether a voice print exists — and suggests what to do next:

```bash
contentsifter -C jsmith pipeline
```

This is the best command to run when you're picking up work on a client after a break.

---

## Ingesting Content

This is how you get a client's content into ContentSifter. The process depends on what kind of content they have.

### LinkedIn Posts

Create a markdown file with their posts separated by `---` dividers:

```markdown
date: 2026-01-15
title: The Power of Showing Up

I had the same conversation three times this week.

"I know I should be networking, but I just... can't."

Here's what I tell everyone: you don't need to be good at networking.
You just need to show up.

---

date: 2026-01-20
title: Your Resume Is an Ad

Stop treating your resume like a job description.
It's not a list of responsibilities. It's an AD.
```

Then ingest it:

```bash
contentsifter -C jsmith ingest ./jane-linkedin-posts.md --type linkedin
```

Each section between `---` dividers becomes one content item in the database. The `date:` and `title:` lines at the top of each section are optional but helpful for organizing later.

### Emails and Newsletters

Same format. Put each email in its own section separated by `---`:

```bash
contentsifter -C jsmith ingest ./jane-emails.md --type email
```

Or if each newsletter is its own file, point to the directory:

```bash
contentsifter -C jsmith ingest ./jane-newsletters/ --type newsletter
```

With `--type newsletter`, each file becomes one content item (no splitting on `---`).

### Blog Posts

Same as newsletters. Each file is one blog post:

```bash
contentsifter -C jsmith ingest ./jane-blog-posts/ --type blog
```

### Transcripts (Coaching Calls, Meetings, Podcasts)

If the client has call transcripts in the same merged-markdown format that ContentSifter uses:

```bash
contentsifter -C jsmith ingest ./jane-transcripts/ --type transcript
```

This delegates to the full transcript parser (the same one used for coaching calls), which extracts speaker turns, metadata, and timestamps.

### Checking What's Been Ingested

```bash
contentsifter -C jsmith ingest --status-only
```

This shows a table of how many items of each type have been imported and their total character count.

### Auto-Detection

If your files are named with prefixes like `linkedin-posts.md`, `email-outreach.md`, `newsletter-jan.md`, or `blog-leadership.md`, ContentSifter will auto-detect the type:

```bash
# No --type needed if the filename starts with the content type
contentsifter -C jsmith ingest ./linkedin-posts.md
```

---

## Voice Capture Interviews

The biggest challenge with new clients is getting enough source material. Voice capture interviews solve this: you generate a questionnaire, the client talks through it using any voice transcription tool, and you ingest the transcript. In 60-90 minutes, you have a goldmine of stories, expertise, and opinions in their natural voice.

### Step 1: Generate the Questionnaire

```bash
contentsifter -C jsmith interview generate
```

This creates `content/clients/jsmith/interview-guide.md` — a markdown file with 85+ questions across 9 categories:

| Category | Questions | What It Captures |
|----------|-----------|-----------------|
| Warmup & Identity | 5 | Who they are, their elevator pitch |
| Origin Story | 10 | Career journey, pivotal moments, failures |
| Expertise & Method | 12 | Frameworks, processes, what makes them unique |
| Client Stories & Wins | 10 | Transformations, before/after, results |
| Problems & Pain Points | 10 | What their audience struggles with |
| Contrarian Views & Hot Takes | 8 | Unpopular opinions, industry critiques |
| Teaching Moments | 12 | Lessons learned, mistakes, tips |
| Vision & Values | 8 | Why they do this work, where they're headed |
| Quick-Fire Round | 10 | Short punchy answers, favorites, superlatives |

The questions draw from proven content frameworks: Dickie Bush's 4A Framework, Nicolas Cole's Endless Idea Generator, PipDecks Storyteller Tactics, StoryBrand (Donald Miller), Matthew Dicks' Storyworthy, Justin Welsh's Content Matrix, and SME interview techniques.

### Adding Niche-Specific Questions

If the client works in a specific industry, you can generate additional targeted questions:

```bash
contentsifter -C jsmith interview generate --niche "financial planning"
```

This adds 10-15 industry-specific questions to the end of the guide (requires API key).

### Step 2: Client Records Their Answers

Send the interview guide to the client. They should:

1. Open any voice transcription tool (phone dictation, Otter.ai, Whisper, etc.)
2. Start recording
3. Read each question out loud, then answer it naturally
4. Save the transcript as a `.txt` or `.md` file when done

The guide includes detailed instructions and tips at the top.

### Step 3: Ingest the Transcript

```bash
contentsifter -C jsmith interview ingest ./jane-transcript.txt
```

This parses the transcript by fuzzy-matching each question from the questionnaire, then stores each answer as a content item in the database. Answers shorter than 30 characters (like "skip") are automatically filtered out.

You can point to a different questionnaire if needed:

```bash
contentsifter -C jsmith interview ingest ./transcript.txt --questionnaire ./custom-guide.md
```

### Step 4: Check What Was Captured

```bash
contentsifter -C jsmith interview status
```

This shows how many answers were captured, broken down by category, with average answer length.

### What Comes Next

After ingesting the interview, the standard pipeline takes over:

```bash
# Build voice print from interview answers
contentsifter -C jsmith voice-print

# Generate content in their voice
contentsifter -C jsmith generate -q "career change" -f linkedin
contentsifter -C jsmith plan-week
```

---

## Building a Voice Print

The voice print is what makes ContentSifter's output sound like your client instead of like generic AI. It's a detailed analysis of how they write and speak.

### How It Works

ContentSifter runs a 3-pass analysis using Claude:

1. **Pass 1 (Vocabulary):** Identifies signature phrases, word choice patterns, register (casual vs. formal), metaphors, and tone
2. **Pass 2 (Structure):** Analyzes how they open and close content, their teaching methodology, question patterns, and paragraph structure
3. **Pass 3 (Synthesis):** Combines both passes into a single actionable voice profile document

The analysis uses stratified sampling. It doesn't just grab random text. It specifically samples:
- How they open content
- How they close content
- Their longest, most in-depth writing (monologues)
- Their short, punchy writing
- Their medium-length explanations
- Their questions

### Generating a Voice Print

Make sure you've ingested enough content first. More content = better voice print. Aim for at least 20-30 pieces of content.

```bash
contentsifter -C jsmith voice-print
```

This takes a few minutes. The output is saved to `content/clients/jsmith/voice-print.md`.

If you want to regenerate the voice print after adding more content:

```bash
contentsifter -C jsmith voice-print --force
```

You can control how many samples go into each bucket:

```bash
contentsifter -C jsmith voice-print --sample-size 150
```

The default is 100 samples per bucket. More samples = more accurate voice print, but uses more API tokens.

### What the Voice Print Contains

The voice print is a markdown file that describes:

- Quick reference (tone, register, energy, sentence length)
- Signature phrases and when to use them
- Vocabulary profile (words to use, words to avoid)
- Metaphors they use and what they mean
- Formatting preferences (emoji, bold, caps, lists)
- Sentence patterns (short punchy vs. medium vs. long narrative)
- How they open and close different types of content
- Emotional tone guide (encouraging, challenging, celebrating, addressing struggles)

Every generated draft uses this voice print to match the client's natural writing style.

---

## Generating Content

Once you have content ingested and a voice print built, you can generate drafts.

### Basic Generation

```bash
contentsifter -C jsmith generate -q "networking tips" -f linkedin
```

This does three things:
1. **Searches** the client's content bank for items matching "networking tips"
2. **Generates** a LinkedIn post draft using the matched source material
3. **Runs content gates** to remove AI-sounding patterns and match the client's voice

The `-q` flag is the search query for finding relevant source material.
The `-f` flag is the output format.

### Available Formats

| Format | What It Produces |
|--------|-----------------|
| `linkedin` | LinkedIn post (~200 words, hook + insight + CTA) |
| `newsletter` | Email newsletter section (longer, more detailed) |
| `thread` | Multi-part thread (numbered posts) |
| `playbook` | Step-by-step guide with structured sections |
| `video-script` | Short-form video script (30-60 seconds) |
| `carousel` | LinkedIn carousel slide deck (slide-by-slide) |
| `email-welcome` | Welcome email for new subscribers |
| `email-weekly` | Weekly digest email |
| `email-sales` | Sales or follow-up email |

### Saving Drafts to Disk

Add `--save` to write the draft to a timestamped file:

```bash
contentsifter -C jsmith generate -q "leadership" -f linkedin --save
```

The file is saved to `content/clients/jsmith/drafts/linkedin-20260222-143052.md`.

### Filtering Source Material

You can narrow which content items are used as source material:

```bash
# Only use playbook-type extractions as source
contentsifter -C jsmith generate -q "interview prep" -f video-script -c playbook

# Only use high-quality (4-5) extractions
contentsifter -C jsmith generate -q "resume" -f carousel --min-quality 4

# Use more source items for richer context
contentsifter -C jsmith generate -q "salary" -f newsletter --limit 20
```

### Controlling Voice Matching

```bash
# Generate without voice matching (faster, no gates)
contentsifter -C jsmith generate -q "networking" -f linkedin --no-voice-print

# Keep voice context but skip the rewrite gates (faster)
contentsifter -C jsmith generate -q "networking" -f linkedin --skip-gates
```

### Content Gates

Every generated draft passes through two validation gates (in this order):

1. **AI Gate** -- Catches and rewrites AI-sounding patterns. Checks for: em dashes (zero tolerance), hedging language ("It's important to note that..."), five-dollar words ("utilize" instead of "use"), formulaic openings/closings, passive voice, and 50+ other patterns. The reference document is `content/ai-gate.md`.

2. **Voice Gate** -- Rewrites the draft to match the client's voice print. Matches: tone, vocabulary, sentence patterns, energy level, formatting style, signature phrases, and teaching structure.

Gates run automatically when a voice print exists. Use `--skip-gates` to bypass them for faster generation, or `--no-voice-print` to disable both voice matching and gates entirely.

---

## Searching Content

### Keyword Search

```bash
contentsifter -C jsmith search "leadership"
```

This uses SQLite FTS5 (full-text search with Porter stemming). It matches against extraction titles, content, raw quotes, and context notes.

### Semantic Search (AI)

```bash
contentsifter -C jsmith search "how do I deal with imposter syndrome" --semantic
```

Semantic search is a 3-stage pipeline:
1. Claude expands your query into related terms
2. FTS5 retrieves candidate matches (3x your limit)
3. Claude re-ranks the candidates by actual relevance

This is much better for natural language questions, but uses API tokens.

### Filtering Results

```bash
# By category
contentsifter -C jsmith search "networking" -c playbook
contentsifter -C jsmith search "success" -c testimonial -c story

# By tag
contentsifter -C jsmith search "resume" -t linkedin -t personal_branding

# By date range
contentsifter -C jsmith search "interview" --date-from 2024-01-01 --date-to 2024-12-31

# By quality score
contentsifter -C jsmith search "salary" --min-quality 4

# Combine filters
contentsifter -C jsmith search "networking" -c playbook -t linkedin --min-quality 3
```

### Output Formats

```bash
# Table view (default) -- shows title, category, quality, date
contentsifter -C jsmith search "resume"

# Full view -- shows complete content, raw quotes, and tags
contentsifter -C jsmith search "resume" --output-format full --limit 5

# JSON -- pipe to a file or another tool
contentsifter -C jsmith search "salary" --output-format json > salary_results.json
```

---

## Planning a Week of Content

ContentSifter can generate a full week of content following a fixed schedule:

| Day | Content Pillar | Format | Source Category |
|-----|---------------|--------|-----------------|
| Monday | Story | LinkedIn text post | `story` |
| Tuesday | Playbook | LinkedIn carousel | `playbook` |
| Wednesday | Video | Short-form script | Any high-quality |
| Thursday | Q&A | LinkedIn text post | `qa` |
| Friday | Testimonial | LinkedIn text post | `testimonial` |
| Saturday | Newsletter | Weekly email | Mix of all |
| Sunday | Rest | -- | -- |

### Generate a Full Calendar

```bash
contentsifter -C jsmith plan-week
```

This selects high-quality unused extractions for each day, generates a draft for each one using the voice print, and saves the full calendar to `content/clients/jsmith/calendar/week-2026-02-23.md`.

ContentSifter tracks which content items have been used, so running `plan-week` again will pull different source material. No repeats.

### Calendar Without AI Drafts

If you just want the source material selected for each day (no API calls):

```bash
contentsifter -C jsmith plan-week --no-llm
```

### Focus on a Topic

```bash
contentsifter -C jsmith plan-week --topic-focus networking
```

This biases the content selection toward items tagged with "networking".

### Generate for a Specific Week

```bash
contentsifter -C jsmith plan-week --week-of 2026-03-10
```

### Skip Gates for Speed

```bash
contentsifter -C jsmith plan-week --skip-gates
```

---

## The Transcript Pipeline (Advanced)

If your client has coaching calls, meetings, or podcast transcripts, you can run the full extraction pipeline. This is what was originally built for the ClearCareer coaching program.

### Step 1: Parse Transcripts

```bash
contentsifter -C jsmith parse --input ./jane-transcripts/
```

This reads markdown files, splits them into individual calls (using `<!-- SOURCE FILE: ... -->` markers), parses metadata (date, title, participants, call type) and speaker turns, and stores everything in SQLite.

It's idempotent: re-running skips already-parsed calls.

### Step 2: Topic Chunking (AI)

```bash
contentsifter -C jsmith chunk
```

This sends each call's transcript to Claude, which identifies distinct topical segments. For example, in a group Q&A call, each participant's question-and-answer session becomes a separate chunk.

### Step 3: Content Extraction (AI)

```bash
contentsifter -C jsmith extract
```

This processes each topic chunk and extracts categorized content items:
- **Q&A** (`qa`): Questions asked and answers given
- **Testimonial** (`testimonial`): Success stories, wins, positive feedback
- **Playbook** (`playbook`): Step-by-step advice, frameworks, methodologies
- **Story** (`story`): Personal stories, anecdotes, illustrative examples

Each extraction gets a quality score (1-5) and topic tags.

### Run All Three Steps at Once

```bash
contentsifter -C jsmith sift --input ./jane-transcripts/
```

### Check Progress

```bash
contentsifter -C jsmith status
```

---

## Content Templates

ContentSifter includes curated content planning templates (not AI-generated). These are reference frameworks you can use alongside the generated drafts.

```bash
contentsifter init-templates
```

This writes templates to `content/templates/`:
- **LinkedIn frameworks:** PAS (Problem-Agitate-Solve), Story-Lesson, tips lists, case studies, carousels
- **Newsletter frameworks:** Weekly structure, subject line patterns
- **Video frameworks:** Short-form hooks, CTAs, visual cues
- **Hooks library:** Opening patterns organized by type
- **Email templates:** Welcome sequence, weekly digest, sales/launch emails

Use `--force` to overwrite existing template files.

---

## Data Commands

### Check Processing Status

```bash
contentsifter -C jsmith status
```

Shows:
- Pipeline progress (how many calls are parsed/chunked/extracted)
- Ingested content item counts by type
- Extraction breakdown by category

### Detailed Statistics

```bash
contentsifter -C jsmith stats
```

Shows:
- Calls broken down by type
- Date range of all calls
- Total speaker turns
- Top 20 most-used tags

### Export to JSON

```bash
contentsifter -C jsmith export
contentsifter -C jsmith export --output ./my-exports/
```

Creates three outputs:
- `full_export.json` -- every extraction in one file
- `by_category/` -- one JSON file per category (qa.json, playbook.json, etc.)
- `by_call/` -- one JSON file per call with its extractions

---

## Global Options

These options go between `contentsifter` and the command name:

| Option | Default | What It Does |
|--------|---------|-------------|
| `-C, --client SLUG` | from `clients.json` | Which client to work with |
| `--db PATH` | from client config | Override the database path |
| `--llm-mode MODE` | `auto` | How to access Claude: `auto`, `api`, or `claude-code` |
| `--model MODEL` | `claude-sonnet-4-20250514` | Which Claude model to use |
| `-v, --verbose` | off | Show debug logging |

Example:

```bash
contentsifter -C jsmith --verbose generate -q "networking" -f linkedin
```

---

## How the Database Works

Each client gets their own SQLite database. You never need to touch it directly, but it's a standard SQLite file if you want to query it.

### Where Databases Live

```
data/contentsifter.db                          # Default client (Izzy)
data/clients/jsmith/contentsifter.db           # Jane Smith
data/clients/acme/contentsifter.db             # Acme Corp
```

### Database Tables

| Table | What It Stores |
|-------|---------------|
| `calls` | Individual coaching calls (title, date, type, turn count) |
| `participants` | Per-call participants (name, email, coach flag) |
| `speaker_turns` | Every speaker turn with text and timestamps |
| `topic_chunks` | AI-identified topic segments per call |
| `content_items` | Ingested written content (LinkedIn posts, emails, etc.) |
| `extractions` | Extracted content items (the core output for generation) |
| `tags` | Topic tag definitions |
| `extraction_tags` | Links between extractions and tags |
| `processing_log` | Pipeline stage tracking |
| `extractions_fts` | Full-text search index for extractions |
| `speaker_turns_fts` | Full-text search index for raw transcripts |
| `content_items_fts` | Full-text search index for ingested content |

### Querying Directly

```bash
sqlite3 data/clients/jsmith/contentsifter.db
```

```sql
.mode column
.headers on

-- See all ingested content
SELECT id, content_type, title, char_count, date FROM content_items;

-- See all extractions ranked by quality
SELECT id, category, quality_score, title FROM extractions ORDER BY quality_score DESC;

-- Count extractions by category
SELECT category, COUNT(*) as count FROM extractions GROUP BY category ORDER BY count DESC;

-- Full-text search
SELECT id, title, snippet(extractions_fts, 1, '>>>', '<<<', '...', 30) as match
FROM extractions_fts
JOIN extractions ON extractions_fts.rowid = extractions.id
WHERE extractions_fts MATCH 'networking'
ORDER BY rank;

-- See which tags are most used
SELECT t.name, COUNT(*) as usage_count
FROM tags t
JOIN extraction_tags et ON t.id = et.tag_id
GROUP BY t.name
ORDER BY usage_count DESC;
```

---

## Content Categories

Every extraction is classified into one of four categories:

| Category | Key | What It Is | Example |
|----------|-----|-----------|---------|
| Q&A | `qa` | A question someone asked and the answer given | "How do I follow up after a recruiter ghosts me?" |
| Testimonial | `testimonial` | Success stories, wins, positive feedback | "Client landed a Director role with a $30K raise" |
| Playbook | `playbook` | Step-by-step advice, frameworks, how-tos | "5-step post-interview follow-up email template" |
| Story | `story` | Personal stories, anecdotes, examples | "The time I showed up to a job in a Pikachu costume" |

## Topic Tags

Extractions are tagged with relevant topics for filtering:

`linkedin` `networking` `resume` `interviews` `cover_letter` `salary_negotiation` `mindset` `confidence` `personal_branding` `career_transition` `job_search_strategy` `follow_up` `company_research` `recruiter` `informational_interview` `remote_work` `portfolio` `references` `onboarding` `rejection_handling` `time_management` `ai_tools` `volunteer` `entrepreneurship` `freelancing`

---

## File Structure

```
contentsifter/
  clients.json                      # Client registry (who your clients are)
  pyproject.toml                    # Python package config
  CLAUDE.md                        # Instructions for Claude Code
  README.md                        # This file
  transcripts/                     # Source transcript files (gitignored)
  data/                            # Databases and exports (gitignored)
    contentsifter.db               #   Default client database
    clients/                       #   Per-client databases
      jsmith/
        contentsifter.db
  content/                         # Generated content
    voice-print.md                 #   Default client voice profile
    ai-gate.md                     #   AI detection patterns (shared)
    templates/                     #   Content planning frameworks
    calendar/                      #   Weekly content calendars
    drafts/                        #   Saved generated drafts
    clients/                       #   Per-client content
      jsmith/
        voice-print.md
        drafts/
        calendar/
  src/contentsifter/               # Source code
    cli.py                         #   Click CLI commands
    config.py                      #   Paths, client config, constants
    process.py                     #   Batch processing for Claude Code
    ingest/                        #   Content ingestion module
      reader.py                    #     File reading + DB insertion
      formats.py                   #     Format-specific parsers
    parser/                        #   Transcript parsing
      splitter.py                  #     Split merged markdown files
      metadata.py                  #     Parse date, title, participants
      turns.py                     #     Parse speaker turns
    extraction/                    #   AI-powered content extraction
      chunker.py                   #     Topic segmentation via Claude
      extractor.py                 #     Content extraction per chunk
      prompts.py                   #     Prompt templates
      categories.py                #     Category + tag definitions
    llm/                           #   LLM client abstraction
      client.py                    #     API, Claude Code, callback modes
    storage/                       #   Database layer
      database.py                  #     SQLite schema, FTS5, triggers
      models.py                    #     Dataclasses
      repository.py                #     CRUD operations
      export.py                    #     JSON export
    search/                        #   Search functionality
      keyword.py                   #     FTS5 keyword search
      semantic.py                  #     Claude-powered re-ranking
      filters.py                   #     SearchFilters dataclass
    generate/                      #   Content generation
      drafts.py                    #     Draft generation + gate integration
      templates.py                 #     9 format templates
      gates.py                     #     AI detection + voice matching gates
    interview/                     #   Voice capture interview system
      prompts.py                   #     85-question prompt library (9 categories)
      generator.py                 #     Questionnaire markdown generator
      parser.py                    #     Fuzzy-match transcript parser
    planning/                      #   Content planning
      calendar.py                  #     Weekly calendar generator
      voiceprint.py                #     3-pass voice analysis
      templates_static.py          #     Curated content frameworks
      prompts.py                   #     Voice analysis prompts
      writer.py                    #     File I/O helpers
```

---

## End-to-End Walkthrough: New Client from Scratch

Here's the complete process for taking a new client from zero to generated content:

### 1. Create the Client

```bash
contentsifter client create jsmith --name "Jane Smith" --email jane@example.com
```

### 2. Prepare Their Content

Gather the client's existing content. The more you have, the better the voice print and the richer the content bank.

Create a markdown file with their LinkedIn posts:

```markdown
date: 2026-01-15
title: Why I Stopped Chasing Promotions

I spent 8 years climbing a ladder that was leaning against the wrong wall.

Every promotion felt hollow. More money, more stress, less purpose.

Then I asked myself one question: "If I had to do this for 20 more years, would I?"

The answer changed everything.

---

date: 2026-01-22
title: The Meeting That Changed My Career

Three years ago I walked into a coffee shop to meet someone I'd cold-emailed on LinkedIn.

I was terrified. My hands were shaking.

That person became my mentor, then my business partner, then my closest friend.

All because I sent one awkward message.

Just send the message.
```

### 3. Ingest the Content

```bash
contentsifter -C jsmith ingest ./jane-posts.md --type linkedin
```

### 4. Check What Got Imported

```bash
contentsifter -C jsmith ingest --status-only
```

### 5. Build the Voice Print

```bash
contentsifter -C jsmith voice-print
```

Wait a few minutes. When it's done, open `content/clients/jsmith/voice-print.md` to review the analysis.

### 6. Generate a Draft

```bash
contentsifter -C jsmith generate -q "career change" -f linkedin
```

The output should sound like Jane, not like AI.

### 7. Save Drafts You Like

```bash
contentsifter -C jsmith generate -q "mentorship" -f linkedin --save
contentsifter -C jsmith generate -q "leadership" -f newsletter --save
```

Saved drafts go to `content/clients/jsmith/drafts/`.

### 8. Plan a Full Week

```bash
contentsifter -C jsmith plan-week
```

The calendar is saved to `content/clients/jsmith/calendar/`.

---

## Dependencies

| Package | What It Does |
|---------|-------------|
| [Click](https://click.palletsprojects.com/) | Powers the CLI (command parsing, options, help text) |
| [Anthropic](https://docs.anthropic.com/en/docs/client-sdks/python) | Talks to Claude for AI-powered features |
| [Rich](https://rich.readthedocs.io/) | Makes terminal output look good (tables, colors, progress bars) |

## LLM Access Modes

ContentSifter supports three ways to access Claude:

| Mode | How It Works | When to Use |
|------|-------------|-------------|
| **API** | Uses `ANTHROPIC_API_KEY` env var | Default. Set the key and go. |
| **Claude Code** | Calls `claude --print` as a subprocess | When you don't have an API key but have Claude Code installed |
| **Callback** | Python function injection | For programmatic use via `process.py` |

`--llm-mode auto` (the default) tries the API key first. If it's not set, it falls back to Claude Code.

---

## Troubleshooting

### "command not found: contentsifter"

Your virtual environment isn't activated. Run:

```bash
source venv/bin/activate
```

### "No database found. Run 'parse' or 'ingest' first."

You haven't imported any content yet. See the [Ingesting Content](#ingesting-content) section.

### "Unknown client: xyz"

The client doesn't exist in `clients.json`. Create it first:

```bash
contentsifter client create xyz --name "Name Here"
```

### "No content found. Ingest some content or parse transcripts first."

The voice-print command needs content to analyze. Make sure you've ingested at least some content items or parsed some transcripts first.

### AI commands hang or timeout

If you're running inside Claude Code, the `claude --print` subprocess approach doesn't work. Set `ANTHROPIC_API_KEY` directly instead:

```bash
export ANTHROPIC_API_KEY="your-key"
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

Private project -- not for redistribution.
