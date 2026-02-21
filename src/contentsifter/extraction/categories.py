"""Content categories and tag taxonomy for ContentSifter."""

CATEGORIES = {
    "qa": "Question & Answer",
    "testimonial": "Testimonial / Win",
    "playbook": "Playbook / Framework",
    "story": "Story / Anecdote",
}

# Predefined topic tags — AI can assign these to extracted content
TAGS = {
    # Core job search
    "linkedin": "LinkedIn profile, posting, networking on LinkedIn",
    "networking": "Networking strategy, events, connections",
    "resume": "Resume writing, formatting, tailoring",
    "interviews": "Interview preparation, techniques, follow-up",
    "cover_letter": "Cover letter writing",
    "salary_negotiation": "Salary negotiation, compensation discussion",
    # Personal development
    "mindset": "Mindset, motivation, overcoming doubt",
    "confidence": "Building confidence, self-advocacy",
    "personal_branding": "Personal brand, differentiation",
    "career_transition": "Changing careers, pivoting industries",
    # Tactics
    "job_search_strategy": "Overall job search approach, planning",
    "follow_up": "Following up with contacts, applications",
    "company_research": "Researching companies, due diligence",
    "recruiter": "Working with recruiters",
    "informational_interview": "Informational interviews, coffee chats",
    # Other
    "remote_work": "Remote work, hybrid arrangements",
    "portfolio": "Portfolio, work samples",
    "references": "References, recommendations",
    "onboarding": "Starting a new role",
    "rejection_handling": "Handling rejection, ghosting",
    "time_management": "Time management, productivity",
    "ai_tools": "AI tools for job search",
    "volunteer": "Volunteering, pro bono work",
    "entrepreneurship": "Entrepreneurship, starting a business",
    "freelancing": "Freelancing, contract work",
}

TAG_LIST_STR = ", ".join(sorted(TAGS.keys()))
