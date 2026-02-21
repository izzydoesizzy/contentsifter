"""Static content planning templates — frameworks, hooks, and email sequences.

These are written to content/templates/ by the init-templates command.
No LLM call needed — this is curated best-practice content.
"""

from __future__ import annotations

from contentsifter.config import NEWSLETTER_TEMPLATES_DIR, TEMPLATES_DIR

# ---------------------------------------------------------------------------
# LinkedIn Frameworks
# ---------------------------------------------------------------------------

LINKEDIN_FRAMEWORKS = """\
# LinkedIn Content Frameworks

A complete reference for creating LinkedIn posts, carousels, articles, and polls.
Each framework includes the structure, a fill-in-the-blank template, and guidance
on when to use it.

---

## Text Post Frameworks (150-300 words)

Best for: daily posts, quick tips, hot takes, stories, engagement.
Post 3-5x per week. First line is everything — LinkedIn truncates after ~210
characters, so your hook must earn the "...see more" click.


### 1. PAS — Problem, Agitate, Solve

**When to use:** Addressing a common pain point your audience faces.

**Structure:**
```
[Hook — name the problem in one punchy line]

[Problem — 1-2 sentences: "Here's what happens..."]

[Agitate — 2-3 sentences making the reader feel seen.
 Use "you" language. Describe the frustration.]

[Solve — 3-5 bullet points or a short paragraph.
 Specific, actionable, immediately useful.]

[CTA — question or invitation to engage]

#hashtag1 #hashtag2 #hashtag3
```

**Fill-in template:**
```
[Pain point] is costing you [consequence].

You [describe the struggle]. You [describe the frustration].
And the worst part? [Twist that makes it feel personal].

Here's what actually works:

1. [Specific action]
2. [Specific action]
3. [Specific action]

[Closing insight or reframe]

What's been your experience with [topic]?

#careerchange #jobsearch #careertips
```


### 2. Story-Lesson

**When to use:** Sharing a client win, personal experience, or illustrative anecdote.

**Structure:**
```
[Hook — set the scene in one line. Create curiosity.]

[Story — 3-5 sentences. Concrete details: names (anonymized),
 numbers, emotions. Show, don't tell.]

[Pivot — "Here's what I learned:" or "The lesson?"]

[Lesson — 2-3 actionable takeaways]

[CTA — "Has this happened to you?" or "Save this for later."]
```

**Fill-in template:**
```
[Time reference], [person] came to me with [specific situation].

They had been [struggling with X] for [time period].
[One vivid detail that makes it real].

We [what you did together — 1-2 sentences].

[Time later], [the result].

Here's what made the difference:

- [Insight 1]
- [Insight 2]
- [Insight 3]

[Broader takeaway for the reader]

[Question for engagement]
```


### 3. Listicle

**When to use:** Sharing multiple tips, mistakes, or lessons. High save rate.

**Structure:**
```
[Hook: "X things that Y" or "X mistakes I see..."]

1. [Point] — [one-line explanation]
2. [Point] — [one-line explanation]
3. [Point] — [one-line explanation]
(5-7 items)

[Wrap-up line — the meta-lesson]
[CTA]
```

**Fill-in template:**
```
[Number] [things/mistakes/lessons] every [audience] needs to know:

1. [Item] — [Why it matters in one sentence]
2. [Item] — [Why it matters in one sentence]
3. [Item] — [Why it matters in one sentence]
4. [Item] — [Why it matters in one sentence]
5. [Item] — [Why it matters in one sentence]

The common thread? [Overarching insight].

Which one surprised you most?
```


### 4. Hot Take / Contrarian

**When to use:** Challenging conventional wisdom. High comment rate.

**Structure:**
```
[Bold claim that goes against the grain]

[Why most people believe the opposite — 1-2 sentences]

[Your argument — evidence, experience, examples]

[The nuance — acknowledge when the conventional view IS right]

[Restate your position. Invite debate.]
```

**Fill-in template:**
```
Unpopular opinion: [Conventional advice] is [wrong/outdated/incomplete].

Everyone says [the common belief].

But after [your experience/credential], here's what I've actually seen:

[Evidence point 1]
[Evidence point 2]
[Evidence point 3]

Now, [caveat — when the conventional view works].

But for [your audience], [your recommendation].

Agree or disagree? Tell me in the comments.
```


### 5. How-To / Tactical

**When to use:** Teaching a specific process. High save and share rate.

**Structure:**
```
[Hook: "How to [achieve result] in [timeframe/steps]"]

Here's the exact process:

Step 1: [Action] — [Brief explanation]
Step 2: [Action] — [Brief explanation]
Step 3: [Action] — [Brief explanation]

[Pro tip or common mistake to avoid]

[CTA: "Save this and try it today."]
```


### 6. Before/After

**When to use:** Showing transformation. Works for resumes, LinkedIn profiles, mindset shifts.

**Structure:**
```
[Hook: "Before vs. After" or a dramatic comparison]

Before:
- [Old state 1]
- [Old state 2]
- [Old state 3]

After:
- [New state 1]
- [New state 2]
- [New state 3]

What changed? [The key insight or action]

[CTA]
```

---

## Carousel / Document Post (8-12 slides)

Best for: step-by-step guides, frameworks, before/after comparisons, checklists.
Post 1-2x per week. Highest save rate of any LinkedIn format.

**Slide structure:**
- **Slide 1:** Hook headline — large, bold, attention-grabbing. Include a visual.
- **Slide 2:** Problem statement or "Do you ever..." question.
- **Slides 3-8:** One key point per slide. Large text. Keep under 30 words per slide.
- **Slide 9:** Summary checklist or key takeaways.
- **Slide 10:** CTA — "Follow for more" / "Save this" / "Share with someone who needs this"

**Design tips:**
- Use consistent brand colors and fonts
- One idea per slide — if you need two sentences, it's two slides
- Use arrows, numbers, or icons to guide the eye
- End every carousel with your name/handle for shareability

**Fill-in template (slide-by-slide):**
```
SLIDE 1: [Number] [Things] to [Achieve Result]
SLIDE 2: Most [audience] struggle with [problem]. Here's the fix.
SLIDE 3: #1 — [Point]. [One-sentence explanation.]
SLIDE 4: #2 — [Point]. [One-sentence explanation.]
SLIDE 5: #3 — [Point]. [One-sentence explanation.]
SLIDE 6: #4 — [Point]. [One-sentence explanation.]
SLIDE 7: #5 — [Point]. [One-sentence explanation.]
SLIDE 8: Quick recap: [Bullet summary of all points]
SLIDE 9: Save this. Share it with someone who needs it.
SLIDE 10: Follow [Name] for more [topic] tips.
```

---

## Poll

Best for: audience research, sparking engagement, testing content ideas.
Post 1x per week max. Always follow up on results.

**Structure:**
- Question: Clear, specific, relevant to your audience
- 3-4 options (not yes/no — make them interesting)
- Add context in the post body: why you're asking, what you'll do with results
- Follow up with a post sharing the results + your take

**Fill-in template:**
```
[Question about a real decision your audience faces]

[Brief context — why this matters]

Vote below:

[Option A — specific choice]
[Option B — specific choice]
[Option C — specific choice]
[Option D — "Other (tell me in comments)"]

I'll share what I've seen work best in [timeframe].
```

---

## Long-Form Article

Best for: deep-dive topics, SEO, establishing authority. Post 1-2x per month.

**Structure:**
1. Headline (8-12 words, benefit-driven)
2. Opening hook (2-3 sentences — story, stat, or bold claim)
3. The problem (why this matters now)
4. Your framework / approach (the meat — use headers, bullets, examples)
5. Case study or example (make it concrete)
6. Action steps (what to do Monday morning)
7. Closing + CTA

---

## Hashtag Strategy

### Primary (use on every post):
`#careerchange` `#jobsearch` `#careercoach` `#careertips`

### Secondary (rotate by topic):
`#linkedin` `#networking` `#resume` `#interviewing` `#salarynegotiation`
`#careeradvice` `#jobseekers` `#personaldevelopment` `#professionalgrowth`

### Rules:
- 3-5 hashtags per post (more looks spammy)
- Place at the end, not inline
- Mix high-volume (#jobsearch ~2M followers) with niche (#careercoach ~50K)
"""

# ---------------------------------------------------------------------------
# Newsletter Frameworks
# ---------------------------------------------------------------------------

NEWSLETTER_FRAMEWORKS = """\
# Newsletter Frameworks

Structures, patterns, and formulas for writing email newsletters that
get opened, read, and acted on.

---

## Email Structure Patterns

### 1. SOAP — Story, Observation, Application, Prompt

Best for: weekly editions. Creates emotional connection then delivers value.

```
SUBJECT: [Curiosity-driven, 6-10 words]
PREVIEW: [40-90 chars that complement, not repeat, the subject]

---

Hey [First Name],

**STORY** (3-4 sentences)
[Open with a client story, personal anecdote, or observation from the week.
 Use specific details — names (anonymized), settings, emotions.]

**OBSERVATION** (2-3 sentences)
[What pattern or insight does this reveal? Zoom out.
 Connect the specific to the universal.]

**APPLICATION** (bullet points or short numbered list)
[How can the reader apply this? Be specific.
 - Do [this] when [situation]
 - Try [action] this week
 - Avoid [mistake] because [reason]]

**PROMPT** (1-2 sentences)
[Close with a question, micro-challenge, or call-to-action.
 "This week, try..." or "Reply and tell me..."]

Talk soon,
[Name]

P.S. [Personal touch, teaser for next week, or soft coaching CTA]
```

### 2. Value-First

Best for: establishing expertise. Leads with an immediately useful tip.

```
SUBJECT: [Benefit-driven: "How to X" or "The Y that changes everything"]

---

**QUICK WIN** (first 2 sentences)
[Start with one thing they can do RIGHT NOW. No preamble.
 "Here's something you can do in the next 5 minutes..."]

**DEEP DIVE** (3-4 paragraphs, ~300-500 words)
[The main content. One focused topic.
 Use headers, bold text, and short paragraphs.
 Include a framework, process, or contrarian take.]

**RESOURCE** (1-2 sentences)
[Link to a tool, article, video, or template.
 "I found this helpful..." or "Here's a resource I send to every client..."]

**P.S.**
[Personal touch or teaser. This is the second-most-read part of the email.]
```

### 3. Curated Digest

Best for: when you don't have a deep-dive topic. Quick to write, high value.

```
SUBJECT: "[Topic] Digest: [Number] things I noticed this week"

---

**THIS WEEK'S INSIGHT** (1 original thought, 2-3 sentences)
[Your take on something happening in the job market / career world]

**FROM THE COACHING CALLS** (anonymized)
[One real Q&A or tip from a recent coaching session.
 Format as: "Q: [question]" / "A: [your advice]"]

**RESOURCE ROUNDUP** (3 items, each with 1-sentence commentary)
1. [Link] — [Why it's worth reading]
2. [Link] — [Why it's worth reading]
3. [Link] — [Why it's worth reading]

**WIN OF THE WEEK**
[Anonymized client success story. 2-3 sentences.
 Celebrate the action they took, not just the result.]

Until next time,
[Name]
```

---

## Subject Line Formulas

### Curiosity Gap
- "The [unexpected thing] about [topic]"
- "What [impressive person] taught me about [topic]"
- "I was wrong about [thing everyone believes]"

### Benefit-Driven
- "How to [achieve result] without [painful thing]"
- "[Number] [things] I tell every [audience member]"
- "The fastest way to [desired outcome]"

### Pain-Point
- "Why [common approach] isn't working for you"
- "Stop doing [thing]. Start doing [this]."
- "If you're [struggling with X], read this."

### Social Proof
- "[Client name] went from [before] to [after]"
- "What my most successful clients all do"
- "The advice I give more than any other"

### Personal/Relatable
- "An honest conversation about [hard topic]"
- "What I wish I'd known about [topic]"
- "A question I get asked every single week"

### Rules for subject lines:
- 6-10 words (40-60 characters ideal)
- Preview text should COMPLEMENT, not repeat
- Test: would YOU click this in a crowded inbox?
- Avoid: ALL CAPS, excessive punctuation!!!, clickbait you can't deliver on

---

## Open-Loop Patterns

Use these to keep readers engaged through the email:

- **Teaser in subject, deliver in body:** Subject says "the one thing..." — body reveals it halfway through
- **P.S. open loop:** "Next week, I'm sharing [something intriguing]..."
- **Nested story:** Start a story, pause to teach, finish the story at the end
- **Series:** "This is part 1 of 3..." (drives opens for the next emails)

---

## Segmentation Triggers

Questions to include that help you segment your list:

- "Reply with 'RESUME' if you want me to cover resume tips next week"
- "Click here if you're currently job searching / Click here if you're exploring"
- "What's your #1 challenge right now? [Link to poll]"
"""

# ---------------------------------------------------------------------------
# Video Frameworks
# ---------------------------------------------------------------------------

VIDEO_FRAMEWORKS = """\
# Short-Form Video Frameworks

Script structures, hook patterns, and retention techniques for TikTok,
Instagram Reels, YouTube Shorts, and LinkedIn native video.

---

## The Golden Rules

1. **First 3 seconds decide everything.** Your hook must stop the scroll.
2. **One idea per video.** If you have three tips, make three videos.
3. **Spoken word + text overlay = maximum retention.** Always use captions.
4. **End with a reason to follow.** CTA or open loop.
5. **30-60 seconds is the sweet spot** for career advice content.

---

## Hook Patterns (first 3 seconds)

### Direct Challenge
> "Stop applying to jobs this way."
> "You're writing your resume wrong."
> "Delete this line from your LinkedIn."

### Shocking Stat or Claim
> "87% of resumes get rejected before a human sees them."
> "The average job posting gets 250 applications."
> "Recruiters spend 6 seconds on your resume."

### Story Loop
> "A client came to me after 200 applications and zero callbacks..."
> "Last week, someone got hired because of one email..."
> "I almost gave a client terrible advice. Here's what happened."

### POV / Relatable
> "POV: You just got ghosted after a final round interview"
> "POV: You're rewriting your resume for the 47th time"
> "That feeling when the recruiter says 'we went with another candidate'..."

### Pattern Interrupt
> [Start mid-sentence] "...and that's exactly why it doesn't work."
> [Unusual visual/action] + "Here's what nobody tells you about [topic]"
> [Hold up object/prop] "This is your resume. This is what recruiters actually see."

### Question Hook
> "Want to know the #1 thing recruiters look for?"
> "Why do some people land jobs in 2 weeks while others take 6 months?"
> "What would you say if a hiring manager asked you this?"

---

## Script Structures

### Quick Tip (30-45 seconds)

Best for: single actionable insight. Highest volume format.

```
[0-3s]  HOOK: "[Direct challenge or bold claim]"
[3-10s] SETUP: "Here's why this matters..." (1-2 sentences of context)
[10-30s] TIP: "[The actual advice — be specific and concrete]"
[30-40s] PROOF: "[Quick example or result]" (optional)
[40-45s] CTA: "Follow for more career tips" / "Save this"
```

**Fill-in template:**
```
HOOK: "Stop [common mistake]. Do [better thing] instead."

SETUP: "Most [audience] think [misconception].
        But [what's actually true]."

TIP: "Instead, try [specific action].
      [Step 1]. [Step 2]. [Step 3]."

CTA: "Follow for more [topic] tips."
```

### Story-Driven (45-60 seconds)

Best for: transformation stories, lessons learned. Highest share rate.

```
[0-3s]  HOOK: "[Dramatic setup — the before state]"
[3-15s] BEFORE: "[Paint the struggle. Make viewer feel it.]"
[15-30s] TURNING POINT: "[What changed — the insight, action, or conversation]"
[30-45s] AFTER: "[The result. Be specific: numbers, emotions, outcomes.]"
[45-55s] LESSON: "[The takeaway the viewer can apply]"
[55-60s] CTA: "Have you experienced this? Tell me in the comments."
```

**Fill-in template:**
```
HOOK: "[Person/client] was [struggling with X] for [time period]."

BEFORE: "They had tried [things that didn't work].
         [Vivid emotional detail — how it felt]."

TURNING POINT: "Then we [specific action or realization].
               The key was [insight]."

AFTER: "[Time later], they [specific positive result].
        [One emotional detail — how it felt now]."

LESSON: "The lesson? [Universal takeaway].
         If you're [in similar situation], try [action]."

CTA: "Save this if you needed to hear it today."
```

### Talking Head with Text Overlay

Best for: tips, explanations, opinion pieces. The workhorse format.

**Production checklist:**
- Face on camera, good lighting, clean background
- Key words appear as large text overlays as you say them
- Captions always on (80% of social video is watched on mute)
- Eye contact with camera lens (not screen)
- Change angle or zoom every 5-7 seconds to maintain attention
- 100-150 words total (30-60 seconds when spoken naturally)

**Text overlay strategy:**
- Overlay the KEYWORDS, not full sentences
- 3-5 words max per overlay
- Time overlays to appear as you say them
- Use bold, high-contrast text (white with black outline)

### Screen Share Tutorial

Best for: LinkedIn profile tips, resume reviews, tool demos.

**Structure:**
```
[0-3s]  HOOK: "Let me show you [what to do / what's wrong]"
[3-10s] SETUP: Show the screen. Point out the problem.
[10-40s] FIX: Walk through the steps. Narrate every click.
[40-50s] RESULT: Show the before/after side by side.
[50-60s] CTA: "Want me to review yours? Drop it in the comments."
```

### The "3 Types" Framework

Best for: categorization content. Very shareable.

```
[HOOK] "There are 3 types of [job seekers / networkers / interviewers]"
[TYPE 1] "[Description]" — [Visual or text: "Type 1: The ___"]
[TYPE 2] "[Description]" — [Visual or text: "Type 2: The ___"]
[TYPE 3] "[Description]" — [Visual or text: "Type 3: The ___"]
[REVEAL] "Which one are you? Comment below."
```

---

## Retention Techniques

These keep viewers watching past the first few seconds:

1. **Open loop in the hook:** "By the end of this video, you'll know exactly how to..."
   (Viewer stays to get the payoff)

2. **Visual changes every 3-5 seconds:** Zoom in/out, angle change, text pop,
   b-roll insert, hand gesture. Static frames lose viewers.

3. **Pattern interrupts:** Unexpected sound, jump cut, change in energy,
   on-screen text that contradicts what you're saying.

4. **Countdown/progression:** "Tip #1... Tip #2... Tip #3..."
   (Viewer stays to see all of them)

5. **Delayed payoff:** "The last one is the most important" or
   "But the real trick is..." (said at 70% mark)

6. **Save CTA:** "You're going to want to save this one."
   (Signals high value, increases saves which boosts algorithm)

---

## Platform-Specific Notes

### TikTok
- Trending sounds boost discoverability (even at low volume under voiceover)
- Hashtags: 3-5, mix broad (#careertok) with niche (#resumetips)
- Best posting times: 7-9 AM, 12-3 PM, 7-11 PM

### Instagram Reels
- Cover image matters (appears on profile grid)
- Use Instagram's native text tool for overlays
- Hashtags in caption, not on screen
- Cross-post from TikTok but remove watermark

### YouTube Shorts
- Title and first frame are critical (appear in Shorts shelf)
- Can be up to 60 seconds
- Add to a "Shorts" playlist for organization
- Drives subscribers better than other short-form platforms

### LinkedIn Native Video
- Vertical OR square format both work
- Add a text post alongside the video for context
- Captions are essential (autoplay is muted)
- Tag relevant people or companies
- Best for thought leadership and professional tips
"""

# ---------------------------------------------------------------------------
# Master Hook Library
# ---------------------------------------------------------------------------

HOOKS = """\
# Master Hook Library

Proven hooks organized by emotion, platform, and content pillar.
Mix and match: pick an emotion + adapt for your platform + apply to your pillar.

---

## By Emotion

### Curiosity
- "Most people get this completely wrong about [topic]..."
- "The hidden reason your [thing] isn't working..."
- "What [expert/company] knows about [topic] that you don't..."
- "Nobody talks about this part of [topic]..."
- "I didn't believe this until I saw it myself..."
- "There's a trick to [thing] that most people miss..."
- "The real reason [common problem] keeps happening..."

### Fear of Missing Out (FOMO)
- "If you're [job searching / on LinkedIn] in 2026 and not doing [thing]..."
- "The [feature/strategy] nobody is using (but should)..."
- "While you're [doing X], top candidates are [doing Y]..."
- "This one change is why some people get hired 3x faster..."
- "Everyone is going to be talking about this in 6 months..."

### Empathy / Pain
- "I know the feeling of sending 50 applications and hearing nothing."
- "If you've ever been ghosted after an interview, read this."
- "That moment when you realize you've been doing it wrong..."
- "Nobody prepares you for how lonely job searching actually is."
- "You're not [lazy/stupid/unqualified]. You're just [real reason]."
- "It's okay to feel [emotion] about [situation]. Here's why."

### Authority / Credibility
- "After coaching 100+ career changers, here's what I know..."
- "I've reviewed thousands of resumes. This mistake appears in 80% of them."
- "I've seen this pattern in every successful job seeker I've worked with..."
- "In [X years] of coaching, this is the advice I give most..."
- "The top 1% of candidates all do this one thing differently..."

### Surprise / Counterintuitive
- "The worst career advice I ever received (that everyone gives)..."
- "Why I tell clients to STOP networking (and do this instead)..."
- "The best resume I've ever seen broke every rule..."
- "Your biggest weakness in interviews? It's not what you think."
- "The job search strategy that sounds lazy but actually works..."

### Motivation / Aspiration
- "A year from now, you'll wish you had started today."
- "You're closer than you think. Here's proof."
- "The difference between where you are and where you want to be is [one thing]."
- "What if I told you [dream outcome] was [timeframe] away?"

---

## By Platform

### LinkedIn (first line — max ~210 characters before "...see more")
The goal: earn the click to expand. Be specific, be bold, create a gap.

- "I got laid off 3 months ago. Today I accepted an offer at my dream company. Here's exactly what I did differently."
- "Your LinkedIn headline is a billboard. Most people use it as a tombstone. Here's the fix."
- "Unpopular opinion: cover letters aren't dead. They're just being written wrong."
- "97% of job seekers skip this step. It's the reason they don't get callbacks."
- "I made one change to my LinkedIn profile and got 5 recruiter messages in a week."

### Newsletter Subject Lines (6-10 words, 40-60 characters)
The goal: get opened. Compete with 50+ other emails in the inbox.

- "The 6-second resume test (are you passing?)"
- "What I wish I'd known before my career change"
- "Why your network isn't working (and the fix)"
- "The email that got my client hired"
- "3 things top candidates never do in interviews"
- "A hiring manager told me something shocking"
- "Your job search isn't broken. Your strategy is."
- "The LinkedIn trick that changes everything"

### Video Hooks (spoken — first 3 seconds, 10-15 words max)
The goal: stop the scroll. Facial expression and energy must match the words.

- "Stop doing this on your resume immediately."
- "This one LinkedIn trick changed my career."
- "Recruiters told me they hate when candidates do this."
- "Here's the email that got my client the job."
- "The worst interview answer I've ever heard was..."
- "Want to know what hiring managers actually look for?"
- "I reviewed 500 resumes. 90% made this mistake."

---

## By Content Pillar

### Job Search Strategy
- "You're not applying to enough jobs. You're applying to the wrong ones."
- "The hidden job market isn't hidden. You're just not looking in the right place."
- "Here's the exact job search system I teach every client..."
- "Stop spray-and-praying. Start [strategic approach]."

### LinkedIn / Personal Branding
- "Your LinkedIn profile is your digital handshake. Is yours firm or limp?"
- "I audit LinkedIn profiles daily. Here are the top 3 mistakes."
- "Your headline has 120 characters. Here's how to use every one."
- "The #1 LinkedIn feature that job seekers ignore..."

### Resume / Applications
- "Hiring managers don't read resumes. They scan them. Here's what they see."
- "Your resume isn't a biography. It's a marketing document."
- "The one resume section that matters more than your experience..."
- "I fixed one line on a client's resume. They got 3 interviews that week."

### Interviews
- "The interview starts before you walk in the room."
- "There's only one question in every interview. Everything else is a variation."
- "'Tell me about yourself' is not a casual question. Here's the formula."
- "The question you should ask at the end of every interview (and nobody does)."

### Networking
- "Networking isn't about asking for favors. It's about [reframe]."
- "The best networkers don't network. They [what they actually do]."
- "One coffee chat can replace 100 job applications. Here's how to get it right."
- "Stop saying 'I'd love to pick your brain.' Say this instead."

### Mindset / Confidence
- "Job searching is an emotional sport. Here's how to stay in the game."
- "Imposter syndrome doesn't go away. But you can learn to talk back to it."
- "Rejection is redirection. But only if you [specific action]."
- "The biggest lie in career advice: 'just be yourself.'"

### Career Transition
- "Changing careers doesn't mean starting over. It means [reframe]."
- "You don't need 10 years of experience. You need [what you actually need]."
- "The skills that got you here won't get you there. Here's what will."
- "Career change at [age]? Here's what nobody tells you."
"""

# ---------------------------------------------------------------------------
# Newsletter Launch Sequence (7 emails)
# ---------------------------------------------------------------------------

LAUNCH_SEQUENCE = """\
# Welcome Email Sequence

A 7-email onboarding sequence that turns new subscribers into engaged readers
and warm leads. Send over 12 days.

---

## Email 1: Welcome + Quick Win
**Send:** Immediately on signup
**Goal:** Deliver instant value, set expectations, build trust

```
SUBJECT: Welcome! Here's your first career win
PREVIEW: One thing you can do in the next 5 minutes

---

Hey [First Name],

Welcome to [Newsletter Name]!

I'm Izzy, and I help career changers and job seekers go from stuck and
overwhelmed to confident and hired.

Here's a quick win you can do right now — it takes less than 5 minutes:

[INSERT: One specific, immediately actionable tip. Examples:
 - "Open LinkedIn. Change your headline from your job title to:
   [What you do] | Helping [who] achieve [what] | [Key skill]"
 - "Go to your resume. Delete your objective statement. Replace it with
   a 2-sentence summary of your biggest professional achievement."
 - "Send one message today to someone you haven't talked to in 6 months.
   Just say: 'Hey! I was thinking about you. How are things going?'"]

Every [day of week], I'll send you actionable advice from real coaching
sessions with people just like you — career changers, job seekers, and
professionals ready for what's next.

Talk soon,
Izzy

P.S. Tomorrow I'm going to tell you why I started doing this — and the
moment that changed everything.
```

---

## Email 2: Origin Story
**Send:** Day 2
**Goal:** Build connection through vulnerability, establish credibility

```
SUBJECT: Why I became a career coach (the honest version)
PREVIEW: It started with a conversation I'll never forget

---

Hey [First Name],

[INSERT: Your origin story. Structure:

 Paragraph 1 — The moment. A specific conversation, event, or
 realization that set you on this path. Concrete details.

 Paragraph 2 — The problem you saw. What was broken about how
 people approached career changes? What frustrated you?

 Paragraph 3 — What you built. How the coaching program came
 to be. What makes your approach different.

 Paragraph 4 — The result. What your clients achieve.
 One specific outcome.]

I share this because I want you to know: the advice in these emails
comes from real experience — mine and the hundreds of people I've
coached through career transitions.

Hit reply and tell me: what's the #1 thing you're struggling with
right now in your career?

I read every response.

Izzy
```

---

## Email 3: Best Content / Quick Wins
**Send:** Day 4
**Goal:** Deliver concentrated value, show breadth of expertise

```
SUBJECT: The 3 things every job seeker needs to know
PREVIEW: I wish someone had told me #2 years ago

---

Hey [First Name],

I've distilled [time period] of career coaching into 3 things I wish
every job seeker knew from day one:

**1. [Key insight about job search strategy]**

[2-3 sentences explaining it. Make it specific and counterintuitive
if possible.]

**2. [Key insight about personal positioning]**

[2-3 sentences. Include a concrete action they can take.]

**3. [Key insight about mindset/resilience]**

[2-3 sentences. Make it human and empathetic.]

These aren't theoretical — they come straight from coaching sessions
with people who are now working in roles they love.

Want to go deeper? Here are my most popular resources:
- [Link to best article/post/resource]
- [Link to best article/post/resource]

More coming your way on [next email day].

Izzy
```

---

## Email 4: Social Proof
**Send:** Day 6
**Goal:** Build credibility through client results, show what's possible

```
SUBJECT: From 200 applications to hired in 6 weeks
PREVIEW: What [anonymized name] did differently

---

Hey [First Name],

I want to tell you about [Anonymized Name].

[INSERT: Client transformation story. Structure:

 Paragraph 1 — The "before." Where they were when they started.
 Paint the struggle. Make the reader see themselves.

 Paragraph 2 — What we worked on. 2-3 specific strategies or
 mindset shifts. Be concrete enough to be useful.

 Paragraph 3 — The "after." The specific result. Numbers if
 possible (interviews, offers, timeline).]

Why am I telling you this?

Because [Anonymized Name] isn't special (sorry, [Name]). They were
in the exact same spot you might be in right now. The difference
was having a system and someone in their corner.

If any of this resonates, hit reply. I'd love to hear your story.

Izzy
```

---

## Email 5: Methodology / Framework
**Send:** Day 8
**Goal:** Teach your unique approach, position as expert with a system

```
SUBJECT: My framework for going from stuck to hired
PREVIEW: The 4-step process behind every success story

---

Hey [First Name],

After working with hundreds of career changers, I noticed a pattern:
the ones who succeed all follow a similar path (whether they know it
or not).

I turned that pattern into a framework:

**Step 1: [Name of step]**
[What it involves. 2-3 sentences. Make it specific.]

**Step 2: [Name of step]**
[What it involves. 2-3 sentences.]

**Step 3: [Name of step]**
[What it involves. 2-3 sentences.]

**Step 4: [Name of step]**
[What it involves. 2-3 sentences.]

This week, try just Step 1. [Give a specific micro-action.]

If you want to go deeper, that's exactly what we do in the
[program name] — but more on that later.

For now, just start with Step 1.

Izzy

P.S. On [day], I'm going to share something I haven't talked
about publicly before. Keep an eye on your inbox.
```

---

## Email 6: Soft Pitch
**Send:** Day 10
**Goal:** Introduce coaching offer naturally, address objections

```
SUBJECT: Is this you?
PREVIEW: If 2 or more of these sound familiar...

---

Hey [First Name],

Be honest — do any of these sound like you?

- You know you need to make a change, but you don't know where to start
- You've been applying to jobs but hearing nothing back
- You feel qualified but can't seem to communicate your value
- You're overwhelmed by all the conflicting advice online
- You've been putting off updating your resume/LinkedIn for months

If you checked 2 or more, you're exactly who I built [Program Name] for.

**What it is:**
[2-3 sentences describing the program]

**What you get:**
- [Benefit 1 — specific deliverable]
- [Benefit 2 — specific deliverable]
- [Benefit 3 — specific deliverable]
- [Benefit 4 — community/support element]

**Who it's for:**
[1-2 sentences describing ideal client]

**Who it's NOT for:**
[1 sentence — shows you're selective, builds trust]

[CTA: Link to learn more / book a discovery call]

No pressure. The weekly emails aren't going anywhere — you'll keep
getting value every [day] either way.

Izzy
```

---

## Email 7: Transition to Weekly
**Send:** Day 12
**Goal:** Set expectations, recap value delivered, solidify the relationship

```
SUBJECT: What's next (and a quick thank you)
PREVIEW: You've been great — here's what to expect going forward

---

Hey [First Name],

Over the past [time period], you've gotten:

- [Recap of Email 1 quick win]
- [Recap of Email 3 key insights]
- [Recap of Email 5 framework]

Going forward, you'll hear from me every [day] with:

- Actionable career advice from real coaching sessions
- Stories and wins from the community (anonymized)
- Frameworks and tools you can use immediately
- Occasional updates about [Program Name] (I'll always keep it useful)

**One ask:** If these emails have been helpful, forward this to one
person who's going through a career change. It'd mean the world.

If they haven't been helpful... hit reply and tell me what you'd
rather hear about. I'll make it right.

Here's to your next chapter,
Izzy

P.S. [Teaser for next week's regular newsletter topic]
```
"""

# ---------------------------------------------------------------------------
# Weekly Newsletter Template
# ---------------------------------------------------------------------------

WEEKLY_TEMPLATE = """\
# Weekly Newsletter Template

Copy this structure each week. Fill in the [BRACKETED] sections.
Aim for a 3-5 minute read (~500-800 words total).

---

```
SUBJECT: [Use a subject line formula from newsletter-frameworks.md]
PREVIEW: [40-90 characters that complement the subject]

---

Hey [First Name],

[OPENING — 2-3 sentences]
[Start with one of: a personal observation, a quick story, a surprising
 fact, or a question. Set the tone and tease the main topic.]

Example: "I had the same conversation three times this week — with three
different clients, in three different industries. That's how I know this
one's going to hit home."

---

## [MAIN TOPIC HEADLINE]

[MAIN CONTENT — 300-500 words on one focused topic]

[Structure options:
 - Problem → Why it happens → What to do instead
 - Story → Lesson → Action steps
 - Framework → How to use it → Example
 - Myth → Truth → Practical application]

[Use bold for key phrases. Use bullet points for lists.
 Keep paragraphs to 2-3 sentences max.]

---

### From the Coaching Calls

> **Q:** "[Real question from a recent coaching session, anonymized]"
>
> **A:** "[Your answer — practical, specific, 3-5 sentences]"

---

### Quick Win of the Week

[One thing they can do TODAY, right now, in under 5 minutes.
 Be extremely specific: "Open LinkedIn → Go to → Click → Change [X] to [Y]"]

---

### Win Spotlight

[Anonymized client success. 2-3 sentences.
 Focus on the action they took, not just the result.
 Example: "A member of our community sent 15 personalized outreach
 messages last week. She got 6 responses and 3 coffee chats booked.
 The trick? She mentioned a specific article each person had written."]

---

Until next time,
Izzy

P.S. [Choose one:
 - Teaser for next week's topic
 - Link to a recent LinkedIn post
 - Soft mention of coaching program
 - Personal note / vulnerability moment
 - "Reply and tell me [question]"]
```
"""

# ---------------------------------------------------------------------------
# Sales / Promotional Email Templates
# ---------------------------------------------------------------------------

SALES_EMAILS = """\
# Sales & Promotional Email Templates

Use these sparingly — 1-2x per month max, always sandwiched between
high-value content emails. Each template addresses a different
motivation for buying.

---

## Template 1: Pain-Point Pitch

**Best for:** People who are actively struggling and ready for help.

```
SUBJECT: Tired of [specific pain point]?
PREVIEW: There's a better way (and I can prove it)

---

Hey [First Name],

Let me ask you something:

How many hours have you spent this month [describe the struggle]?

[Specific pain point example — make them feel seen]
[Another example]
[And another]

It doesn't have to be this way.

[Bridge to your solution — 2-3 sentences about what you offer
 and WHY it works]

Here's what you get:

- [Specific deliverable 1]
- [Specific deliverable 2]
- [Specific deliverable 3]
- [Specific deliverable 4]

[Social proof — ONE specific client result, anonymized]

[CTA button/link: "Book a free discovery call" or "Learn more"]

[Scarcity/urgency — but only if genuine:
 "I take on [X] new clients per month to keep things personal."
 "The next cohort starts [date]."]

Izzy

P.S. Not sure if it's right for you? Reply to this email and tell me
what you're working on. I'll give you an honest answer.
```

---

## Template 2: Testimonial-Led

**Best for:** Social proof-driven prospects who need to see results first.

```
SUBJECT: "[Specific result]" — how [Anonymized Name] did it in [timeframe]
PREVIEW: Their exact path from [before] to [after]

---

Hey [First Name],

[Anonymized Name] told me something during our first call that I hear
all the time:

"[Direct quote expressing a common fear/frustration — anonymized]"

Sound familiar?

Here's what happened next:

**Month 1:** [What they worked on. Specific actions.]
**Month 2:** [The turning point. What shifted.]
**Month 3:** [The result. Specific outcomes.]

[Name] isn't an outlier. Here's what a few others have said:

> "[Short testimonial quote 1]"
> "[Short testimonial quote 2]"
> "[Short testimonial quote 3]"

If you're in a similar spot, I'd love to help you write a similar story.

[CTA: Book a discovery call / Learn about the program]

Izzy
```

---

## Template 3: FAQ / Objection Handler

**Best for:** People who are interested but have hesitations.

```
SUBJECT: Your questions about [program name], answered honestly
PREVIEW: Including the one everyone's afraid to ask

---

Hey [First Name],

I get a lot of questions about [Program Name]. Here are the most
common ones — answered honestly:

**"Is it worth the investment?"**
[Answer — reframe around cost of NOT acting. Use a specific example.]

**"I don't have time for a program right now."**
[Answer — address the time commitment realistically. Show how it
 actually saves time.]

**"What if I'm not ready to make a change yet?"**
[Answer — meet them where they are. Show it works for explorers too.]

**"How is this different from [alternative]?"**
[Answer — honest differentiation. Don't bash competitors.]

**"What if it doesn't work for me?"**
[Answer — address risk. Guarantees, testimonials, or flexible options.]

Still have questions? Hit reply. I answer every email personally.

Or if you're ready: [CTA link]

Izzy

P.S. The question nobody asks but everyone thinks: "[Common unspoken
concern]." My answer: [Honest, empathetic response.]
```
"""

# ---------------------------------------------------------------------------
# Template registry — maps file paths to content
# ---------------------------------------------------------------------------

ALL_TEMPLATES: dict[str, tuple[str, str]] = {
    "linkedin-frameworks": (str(TEMPLATES_DIR / "linkedin-frameworks.md"), LINKEDIN_FRAMEWORKS),
    "newsletter-frameworks": (str(TEMPLATES_DIR / "newsletter-frameworks.md"), NEWSLETTER_FRAMEWORKS),
    "video-frameworks": (str(TEMPLATES_DIR / "video-frameworks.md"), VIDEO_FRAMEWORKS),
    "hooks": (str(TEMPLATES_DIR / "hooks.md"), HOOKS),
    "launch-sequence": (str(NEWSLETTER_TEMPLATES_DIR / "launch-sequence.md"), LAUNCH_SEQUENCE),
    "weekly-template": (str(NEWSLETTER_TEMPLATES_DIR / "weekly-template.md"), WEEKLY_TEMPLATE),
    "sales-emails": (str(NEWSLETTER_TEMPLATES_DIR / "sales-emails.md"), SALES_EMAILS),
}
