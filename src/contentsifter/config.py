"""Configuration and constants for ContentSifter."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
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

# Coach identification (legacy defaults — use ClientConfig for multi-client)
COACH_NAME = "Izzy Piyale-Sheard"
COACH_EMAIL = "izzy@joinclearcareer.com"

# Client registry path
CLIENTS_JSON_PATH = PROJECT_ROOT / "clients.json"

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


@dataclass
class ClientConfig:
    """Configuration for a single client."""

    slug: str
    name: str
    email: str = ""
    description: str = ""
    db_path: Path = field(default_factory=lambda: DEFAULT_DB_PATH)
    content_dir: Path = field(default_factory=lambda: CONTENT_DIR)

    @property
    def voice_print_path(self) -> Path:
        return self.content_dir / "voice-print.md"

    @property
    def drafts_dir(self) -> Path:
        return self.content_dir / "drafts"

    @property
    def calendar_dir(self) -> Path:
        return self.content_dir / "calendar"

    @property
    def templates_dir(self) -> Path:
        return self.content_dir / "templates"

    @property
    def exports_dir(self) -> Path:
        return self.db_path.parent / "exports"

    def ensure_dirs(self):
        """Create all client directories if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.calendar_dir.mkdir(parents=True, exist_ok=True)


def _load_registry() -> dict:
    """Load the clients.json registry file."""
    if CLIENTS_JSON_PATH.exists():
        return json.loads(CLIENTS_JSON_PATH.read_text())
    return {"default": "izzy", "clients": {}}


def _save_registry(registry: dict):
    """Save the clients.json registry file."""
    CLIENTS_JSON_PATH.write_text(json.dumps(registry, indent=2) + "\n")


def load_client(slug: str | None = None) -> ClientConfig:
    """Load a client config by slug. If slug is None, use the default."""
    registry = _load_registry()

    if slug is None:
        slug = registry.get("default", "izzy")

    clients = registry.get("clients", {})
    if slug in clients:
        entry = clients[slug]
        return ClientConfig(
            slug=slug,
            name=entry["name"],
            email=entry.get("email", ""),
            description=entry.get("description", ""),
            db_path=PROJECT_ROOT / entry["db_path"],
            content_dir=PROJECT_ROOT / entry["content_dir"],
        )

    # Fallback for "izzy" even without clients.json
    if slug == "izzy":
        return ClientConfig(
            slug="izzy",
            name=COACH_NAME,
            email=COACH_EMAIL,
            description="ClearCareer career coaching",
            db_path=DEFAULT_DB_PATH,
            content_dir=CONTENT_DIR,
        )

    raise ValueError(f"Unknown client: {slug}")


def list_clients() -> list[dict]:
    """Return all registered clients as dicts."""
    registry = _load_registry()
    default = registry.get("default", "")
    result = []
    for slug, entry in registry.get("clients", {}).items():
        result.append({
            "slug": slug,
            "name": entry["name"],
            "email": entry.get("email", ""),
            "description": entry.get("description", ""),
            "is_default": slug == default,
        })
    return result


def create_client(slug: str, name: str, email: str = "", description: str = "") -> ClientConfig:
    """Register a new client and create their directories."""
    registry = _load_registry()
    clients = registry.setdefault("clients", {})

    if slug in clients:
        raise ValueError(f"Client '{slug}' already exists")

    db_path = f"data/clients/{slug}/contentsifter.db"
    content_dir = f"content/clients/{slug}"

    clients[slug] = {
        "name": name,
        "email": email,
        "db_path": db_path,
        "content_dir": content_dir,
        "description": description,
    }

    # Set as default if it's the first non-izzy client and no default is set
    if "default" not in registry:
        registry["default"] = slug

    _save_registry(registry)

    config = ClientConfig(
        slug=slug,
        name=name,
        email=email,
        description=description,
        db_path=PROJECT_ROOT / db_path,
        content_dir=PROJECT_ROOT / content_dir,
    )
    config.ensure_dirs()
    return config


def set_default_client(slug: str):
    """Set the default client in the registry."""
    registry = _load_registry()
    if slug not in registry.get("clients", {}):
        raise ValueError(f"Unknown client: {slug}")
    registry["default"] = slug
    _save_registry(registry)
