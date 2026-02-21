"""Configuration and constants for ContentSifter."""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_TRANSCRIPTS_DIR = PROJECT_ROOT / "transcripts"
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "contentsifter.db"
DEFAULT_EXPORTS_DIR = DEFAULT_DATA_DIR / "exports"

# Content planning output directories
CONTENT_DIR = PROJECT_ROOT / "content"
TEMPLATES_DIR = CONTENT_DIR / "templates"
NEWSLETTER_TEMPLATES_DIR = TEMPLATES_DIR / "newsletter"
CALENDAR_DIR = CONTENT_DIR / "calendar"
DRAFTS_DIR = CONTENT_DIR / "drafts"
VOICE_PRINT_PATH = CONTENT_DIR / "voice-print.md"

# Coach identification
COACH_NAME = "Izzy Piyale-Sheard"
COACH_EMAIL = "izzy@joinclearcareer.com"

# Call type mapping from filename patterns
CALL_TYPE_PATTERNS = {
    "weekly-group-q-a": "group_qa",
    "group-call": "group_call",
    "introductory-discovery-call": "discovery",
    "coaching-call": "coaching",
    "body-doubling": "body_doubling",
    "new-member-welcome": "welcome",
    "onboarding": "onboarding",
    "ask-a-recruiter": "workshop",
    "career-storytelling": "workshop",
    "notion-for": "workshop",
    "future-casting": "workshop",
}

# Processing stages
STAGES = ["parsed", "chunked", "extracted"]
