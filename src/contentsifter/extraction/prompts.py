"""Prompt templates for topic chunking and content extraction."""

from contentsifter.extraction.categories import TAG_LIST_STR

# ── Topic Chunking ─────────────────────────────────────────────────

CHUNKING_SYSTEM_PROMPT = """\
You are an expert at analyzing coaching call transcripts.
Your task is to identify distinct topical segments in the conversation.

A topic segment is a coherent block of conversation about one subject, question,
or participant's situation. In group calls, each participant's turn to speak/ask
questions typically forms a natural segment boundary.

Rules:
- Each segment should be at least 3-4 speaker turns (skip trivial greetings unless
  they contain meaningful content).
- Merge very short related exchanges into one segment.
- The intro/welcome/small-talk at the start can be one segment labeled "Opening/Welcome".
- The closing/goodbye can be one segment labeled "Closing".
- For group calls, when different participants take turns asking questions,
  each participant's Q&A naturally forms a segment.

Output format: Return a JSON array of segments. Each segment has:
- "topic_title": short descriptive title (3-8 words)
- "summary": 1-2 sentence summary of what was discussed
- "start_turn": the turn_index number where this segment begins
- "end_turn": the turn_index number where this segment ends (inclusive)
- "primary_speaker": the main non-coach participant driving this segment (or "multiple" for group discussion)

Respond ONLY with the JSON array, no other text or markdown formatting."""

CHUNKING_USER_PROMPT = """\
This is a {call_type} call titled "{title}" on {date}.

Transcript (format: [turn_index] [timestamp] Speaker: text):
{transcript}

Identify the distinct topical segments in this conversation."""


# ── Content Extraction ─────────────────────────────────────────────

def get_extraction_system_prompt(coach_name: str = "", coach_email: str = "") -> str:
    """Build the extraction system prompt with the coach identity injected."""
    if not coach_name:
        coach_name = "the coach"
    identity = f"{coach_name}"
    if coach_email:
        identity += f" ({coach_email})"

    return f"""\
You are an expert content analyst specializing in career coaching content.
You extract valuable, reusable content from coaching call transcripts.

The coach is {identity}.

You extract content into exactly four categories:

1. **Q&A** ("qa"): A clear question someone asked and the coach's ({coach_name}'s) answer.
   - The question should be generalized (not person-specific) when possible.
   - The answer should capture {coach_name}'s key advice, frameworks, or recommendations.

2. **Testimonial/Win** ("testimonial"): Success stories, positive outcomes,
   job landing announcements, expressions of gratitude, before/after transformations.
   - Include who shared it and what the win was.
   - Preserve emotional impact and specific details.

3. **Playbook/Framework** ("playbook"): Step-by-step advice, methodologies,
   systems, or structured approaches that {coach_name} teaches.
   - These should be actionable and self-contained.
   - Include numbered steps or bullet points when the advice is sequential.

4. **Story/Anecdote** ("story"): Personal stories, client examples, analogies,
   or illustrative narratives that make a coaching point.
   - Capture the narrative arc and the lesson/point.

For each extraction, provide:
- "category": one of "qa", "testimonial", "playbook", "story"
- "title": short descriptive title (5-10 words)
- "content": the extracted content, well-written and self-contained
- "raw_quote": the most impactful direct quote(s) from the transcript
- "speaker": who delivered this content (usually {coach_name} for advice, the participant for wins)
- "quality_score": 1-5 rating of how valuable/reusable this content is
  (5 = highly reusable, quotable; 1 = marginally useful)
- "tags": list of relevant topic tags from this set:
  [{TAG_LIST_STR}]

IMPORTANT: Only extract content that is genuinely valuable and reusable.
Small talk, scheduling discussions, and technical difficulties are NOT extractable.
If a segment has no extractable content, return an empty array [].

Respond ONLY with a JSON array of extraction objects, no other text or markdown formatting."""


# Legacy constant for backward compatibility
EXTRACTION_SYSTEM_PROMPT = get_extraction_system_prompt("Izzy Piyale-Sheard", "izzy@joinclearcareer.com")

EXTRACTION_USER_PROMPT = """\
Call type: {call_type}
Call date: {date}
Topic segment: {topic}
Segment summary: {summary}

Transcript segment:
{transcript}

Extract all valuable content from this segment."""


# ── Content Item Extraction ─────────────────────────────────────────

def get_content_extraction_system_prompt(author_name: str = "") -> str:
    """Build extraction prompt for written content items (not transcripts)."""
    if not author_name:
        author_name = "the author"

    return f"""\
You are an expert content analyst. You extract key topics, opinions, frameworks,
and stories from written content by {author_name}.

You extract content into exactly four categories:

1. **Q&A** ("qa"): A question addressed and answered in the content.
   - Generalize the question when possible.

2. **Testimonial/Win** ("testimonial"): Success stories, case studies,
   positive outcomes, or proof of results mentioned in the content.

3. **Playbook/Framework** ("playbook"): Step-by-step advice, methodologies,
   systems, or structured approaches taught in the content.
   - These should be actionable and self-contained.

4. **Story/Anecdote** ("story"): Personal stories, examples, analogies,
   or illustrative narratives that make a point.

For each extraction, provide:
- "category": one of "qa", "testimonial", "playbook", "story"
- "title": short descriptive title (5-10 words)
- "content": the extracted content, well-written and self-contained
- "raw_quote": the most impactful direct quote from the content
- "speaker": "{author_name}"
- "quality_score": 1-5 rating of how valuable/reusable this content is
- "tags": list of relevant topic tags from this set:
  [{TAG_LIST_STR}]

Only extract genuinely valuable, reusable content. If the content has nothing
worth extracting, return an empty array [].

Respond ONLY with a JSON array of extraction objects, no other text or markdown formatting."""


CONTENT_EXTRACTION_USER_PROMPT = """\
Content type: {content_type}
Date: {date}
Title: {title}

Content:
{text}

Extract all valuable content from this piece."""


def format_turns_compact(turns: list[dict]) -> str:
    """Format speaker turns into compact prompt format.

    Converts verbose dict format into:
    [0] [00:05:23] Victor Perez: So I just sent you an email earlier.
    """
    lines = []
    for t in turns:
        idx = t.get("turn_index", t.get("turn_index", 0))
        ts = t.get("timestamp", "00:00:00")
        name = t.get("speaker_name", "Unknown")
        text = t.get("text", "")
        lines.append(f"[{idx}] [{ts}] {name}: {text}")
    return "\n".join(lines)
