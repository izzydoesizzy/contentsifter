# Changelog

All notable changes to ContentSifter are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/).

---

## 2026-02-23 — Polish & Cleanup

### Changed
- Updated CLI, config, LLM client, semantic search, and web UI
- Replaced hardcoded API key with env var reference

---

## 2026-02-22 — Web UI, Multi-Client, Weekly Planner

### Added
- **Multi-client support** with per-client databases, content ingestion, and voice capture interviews
- **Web UI** with FastAPI, htmx, and Tailwind CSS — voice print, content generation, browse, drafts, gates
- **Weekly content planner** with drag-drop, batch draft management, and schema v2
- **Content gate verification** with retry loop and enhanced hard cleanup
- Full-text search with expand-in-place and polished voice print rendering
- Per-card generation, mandatory gates, and copy/save animations
- Onboard and pipeline commands for streamlined CLI workflow
- Comprehensive test suite (198 tests, 52% coverage)

### Fixed
- HTML entity double-escaping in saved drafts and stray period artifacts
- Redirect loop bug in web UI
- Browse/drafts/gates and multi-client management improvements

---

## 2026-02-21 — Initial Release

### Added
- **ContentSifter CLI** — transcript extraction and search with SQLite + FTS5
- **Content planning** — templates, voice print, calendar, and enhanced generation
- **Content gates** — AI detection and voice matching for generated drafts
- **Voice print** expanded with LinkedIn, email, and course data
- 2-week LinkedIn content plan with gated drafts
- Comprehensive README with full CLI reference and SQL query examples

---

## Activity Log

> Auto-generated commit log. Curated changelog entries are above.

### 2026-04-09
- chore: update CHANGELOG (`e69c7a9`, 1 files)
- chore: update CHANGELOG (`ed15dc5`, 1 files)

### 2026-04-01
- Activity log and work log updates (`ac7226b`, 1 files)
- chore: update CHANGELOG (`768a099`, 1 files)

### 2026-03-30
- Commit (`9c70f71`, 1 files)
- chore: update changelog (`8deb512`, 1 files)
- chore: update changelog (`9b8ee4d`, 1 files)
- Add content_blocks schema, dataclass, and staging scripts (`3fddcba`, 5 files)
