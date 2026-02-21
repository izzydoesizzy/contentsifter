"""LLM prompts for content planning — voice print analysis and calendar generation."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Voice Print — Pass 1: Vocabulary and Patterns
# ---------------------------------------------------------------------------

VOICE_PASS1_SYSTEM = """\
You are a linguistic analyst specializing in identifying voice patterns and \
writing signatures. You analyze spoken transcripts to extract the speaker's \
unique characteristics.

Focus on:
- Signature phrases and expressions they repeat
- Vocabulary choices (formal vs casual, technical vs plain)
- Sentence length tendencies
- Use of metaphors, analogies, and imagery
- Filler words and verbal tics (but note these as "spoken only" — not for written content)
- How they reference tools, people, and concepts
- Emotional register (warm, direct, playful, authoritative, etc.)

Output your analysis as structured markdown with clear sections and examples \
quoted directly from the transcripts."""

VOICE_PASS1_USER = """\
Analyze the vocabulary and language patterns of this career coach based on \
their spoken words from coaching calls.

Here is a sample of {turn_count} spoken turns ({char_count} characters):

{turns_text}

Provide a detailed analysis with these sections:

## Signature Phrases
Phrases they repeat frequently. List each with an example context.

## Vocabulary Profile
- Words and expressions they favor
- Register (casual, professional, conversational, etc.)
- Any jargon or domain-specific language
- Words they seem to avoid

## Sentence Patterns
- Typical sentence length and rhythm
- How they structure explanations
- How they structure questions to clients

## Metaphors and Analogies
Any metaphors, analogies, or imagery they use. Quote examples.

## Emotional Tone
How they express encouragement, redirection, celebration, and urgency."""

# ---------------------------------------------------------------------------
# Voice Print — Pass 2: Structural Patterns
# ---------------------------------------------------------------------------

VOICE_PASS2_SYSTEM = """\
You are a communication style analyst. You study how speakers structure their \
coaching conversations — how they open topics, close them, handle emotional \
moments, and deliver advice.

Focus on STRUCTURAL patterns — not vocabulary (that was analyzed separately). \
Look at how ideas are organized, how transitions happen, and what the overall \
coaching approach looks like.

Output your analysis as structured markdown with examples quoted from the transcripts."""

VOICE_PASS2_USER = """\
Analyze the structural communication patterns of this career coach. You are \
given different categories of their spoken turns.

### OPENING TURNS (how they start coaching sessions):
{openings}

### CLOSING TURNS (how they wrap up):
{closings}

### LONG MONOLOGUES (when they explain frameworks or tell stories):
{monologues}

### QUESTIONS (how they probe and guide):
{questions}

Provide analysis with these sections:

## Opening Patterns
How do they typically start a session or topic? What's the pattern?

## Closing Patterns
How do they wrap up topics or sessions? What do they leave people with?

## Teaching Style
When delivering a framework or process, how do they structure it? \
(numbered steps, narrative, Q&A, etc.)

## Questioning Approach
What types of questions do they ask? How do they guide through questions?

## Emotional Handling
How do they respond to wins, struggles, vulnerability, and frustration?

## Energy and Pacing
How does their energy shift throughout a conversation? When are they fast \
vs slow, brief vs expansive?"""

# ---------------------------------------------------------------------------
# Voice Print — Pass 3: Synthesis
# ---------------------------------------------------------------------------

VOICE_PASS3_SYSTEM = """\
You are a writing style consultant who creates voice guides for content \
creators. You take raw linguistic analysis and distill it into a practical \
reference document that a writer can use to match someone's voice in written content.

Important: The voice guide is for WRITTEN content (LinkedIn posts, newsletters, \
video scripts) — not spoken conversation. Filter out spoken-only patterns \
(filler words, incomplete sentences) and translate the coach's natural voice \
into its written equivalent.

The output should be a complete, standalone markdown document."""

VOICE_PASS3_USER = """\
Create a comprehensive voice print document for {coach_name}, a career coach, \
based on the following linguistic analysis.

The voice print will be used as a reference when writing LinkedIn posts, \
newsletter emails, and short-form video scripts in this coach's voice.

### VOCABULARY AND LANGUAGE ANALYSIS:
{pass1_result}

### STRUCTURAL AND COMMUNICATION ANALYSIS:
{pass2_result}

Generate a complete voice print document with these sections:

# Voice Print: {coach_name}

## Quick Reference
A 5-6 bullet summary: tone, register, sentence length, energy, key traits.

## Signature Phrases
Table format: | Phrase | When to Use | Example |

## Vocabulary Profile
### Words and Expressions to Use
### Words and Expressions to Avoid
### Register Notes

## Sentence Patterns
### Short Punchy (for emphasis) — with examples
### Conversational Medium (for explanation) — with examples
### Longer Narrative (for stories) — with examples

## How to Open Content
Patterns for starting LinkedIn posts, email intros, and video hooks.

## How to Close Content
Patterns for CTAs, sign-offs, and final thoughts.

## Emotional Tone Guide
### When Encouraging
### When Challenging / Redirecting
### When Celebrating Wins
### When Addressing Struggles

## Metaphors and Analogies
List with usage context.

## DO / DON'T Writing Guide
### DO — with concrete examples
### DON'T — with concrete examples of what to avoid

Make every section specific and actionable. Include direct examples \
(adapted from spoken to written form) wherever possible."""

# ---------------------------------------------------------------------------
# Calendar Generation
# ---------------------------------------------------------------------------

CALENDAR_DRAFT_SYSTEM = """\
You create ready-to-publish content drafts for a career coaching brand. \
You write in the coach's authentic voice, based on coaching session insights.

Rules:
- Do NOT use specific client names — generalize examples
- Be specific and actionable — no fluff
- Match the format requirements exactly
{voice_context}"""

CALENDAR_DRAFT_USER = """\
Create a {format_type} about the following topic, using this source material \
from a real coaching session.

**Topic:** {topic}
**Format:** {format_type}
**Platform:** {platform}

### Source Material:
{source_material}

### Format Requirements:
{format_requirements}

Write the complete draft, ready to publish."""
