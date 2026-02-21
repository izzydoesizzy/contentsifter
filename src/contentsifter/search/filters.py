"""Search filter builder for ContentSifter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchFilters:
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    call_types: list[str] = field(default_factory=list)
    participants: list[str] = field(default_factory=list)
    min_quality: Optional[int] = None
    limit: int = 20

    def to_sql_clauses(self) -> tuple[str, list]:
        """Return (WHERE clause fragments, parameters) for SQL queries.

        Fragments are joined with AND by the caller.
        """
        clauses = []
        params = []

        if self.categories:
            placeholders = ",".join("?" for _ in self.categories)
            clauses.append(f"e.category IN ({placeholders})")
            params.extend(self.categories)

        if self.tags:
            placeholders = ",".join("?" for _ in self.tags)
            clauses.append(
                f"e.id IN (SELECT et.extraction_id FROM extraction_tags et "
                f"JOIN tags t ON et.tag_id = t.id WHERE t.name IN ({placeholders}))"
            )
            params.extend(self.tags)

        if self.date_from:
            clauses.append("c.call_date >= ?")
            params.append(self.date_from)

        if self.date_to:
            clauses.append("c.call_date <= ?")
            params.append(self.date_to)

        if self.call_types:
            placeholders = ",".join("?" for _ in self.call_types)
            clauses.append(f"c.call_type IN ({placeholders})")
            params.extend(self.call_types)

        if self.min_quality is not None:
            clauses.append("e.quality_score >= ?")
            params.append(self.min_quality)

        return " AND ".join(clauses) if clauses else "", params
