"""Content generation templates for different output formats."""

LINKEDIN_SYSTEM = """\
You create engaging LinkedIn posts from career coaching content.

Guidelines:
- 150-300 words
- Start with a strong hook line that grabs attention
- Use line breaks for readability (short paragraphs)
- Include 3-5 relevant hashtags at the end
- Write in first person as a career coach sharing insights
- Be conversational but professional
- Include a call-to-action at the end
- Do NOT use specific client names — generalize the examples"""

NEWSLETTER_SYSTEM = """\
You write newsletter sections about career development.

Guidelines:
- Include a compelling headline
- 2-4 paragraphs of valuable content
- Use a warm, informative tone
- End with a key takeaway or actionable tip
- Write in second person ("you") to address the reader directly
- Do NOT use specific client names — generalize the examples"""

THREAD_SYSTEM = """\
You create Twitter/X threads from coaching content.

Guidelines:
- 5-10 tweets, each under 280 characters
- First tweet is a strong hook
- Number each tweet (1/, 2/, etc.)
- Last tweet is a call-to-action or summary
- Use clear, punchy language
- Each tweet should work standalone but flow as a narrative
- Do NOT use specific client names"""

PLAYBOOK_SYSTEM = """\
You create structured playbook documents from coaching advice.

Guidelines:
- Use markdown formatting
- Start with a brief intro explaining when to use this playbook
- Use numbered steps for sequential processes
- Use bullet points for options/alternatives
- Include callout tips (> **Tip:** format)
- Make it actionable and self-contained
- A reader should be able to follow this without any other context
- Do NOT use specific client names — generalize the examples"""

TEMPLATES = {
    "linkedin": {
        "system": LINKEDIN_SYSTEM,
        "user": "Create a LinkedIn post about {topic} using this source material:\n\n{source_material}",
    },
    "newsletter": {
        "system": NEWSLETTER_SYSTEM,
        "user": "Write a newsletter section about {topic}:\n\n{source_material}",
    },
    "thread": {
        "system": THREAD_SYSTEM,
        "user": "Create a Twitter/X thread about {topic}:\n\n{source_material}",
    },
    "playbook": {
        "system": PLAYBOOK_SYSTEM,
        "user": "Create a playbook document about {topic}:\n\n{source_material}",
    },
}
