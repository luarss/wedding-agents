#!/usr/bin/env python3
"""
Data models for venue enrichment ETL pipeline.

These models represent the state of enrichment jobs and can be
serialized for job queue systems like Redis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    """Status of an enrichment job."""

    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SearchQuery:
    """A single web search query for venue enrichment."""

    category: str  # e.g., "pricing", "contact", "capacity"
    query: str  # The actual search query string
    priority: int = 1  # Higher priority queries run first


@dataclass
class VenueResearchJob:
    """
    Represents a single venue research task.

    This can be serialized to JSON and queued in Redis for parallel processing.
    """

    venue_id: str
    venue_name: str
    missing_fields: list[str] = field(default_factory=list)
    search_queries: list[SearchQuery] = field(default_factory=list)
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    confidence_before: float = 0.0
    confidence_after: float | None = None
    enrichment_data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON/Redis storage."""
        return {
            "venue_id": self.venue_id,
            "venue_name": self.venue_name,
            "missing_fields": self.missing_fields,
            "search_queries": [
                {"category": q.category, "query": q.query, "priority": q.priority}
                for q in self.search_queries
            ],
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
            "enrichment_data": self.enrichment_data,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VenueResearchJob":
        """Deserialize from dict (from JSON/Redis storage)."""
        return cls(
            venue_id=data["venue_id"],
            venue_name=data["venue_name"],
            missing_fields=data.get("missing_fields", []),
            search_queries=[
                SearchQuery(
                    category=q["category"],
                    query=q["query"],
                    priority=q.get("priority", 1),
                )
                for q in data.get("search_queries", [])
            ],
            status=JobStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            confidence_before=data.get("confidence_before", 0.0),
            confidence_after=data.get("confidence_after"),
            enrichment_data=data.get("enrichment_data", {}),
            error_message=data.get("error_message"),
        )


@dataclass
class EnrichmentSession:
    """
    Tracks state for an entire enrichment session.

    This is the state that was previously embedded in the orchestration logic.
    """

    session_id: str
    venues_file: str
    min_confidence: float
    max_venues: int | None
    total_venues: int = 0
    venues_needing_enrichment: int = 0
    jobs: list[VenueResearchJob] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    def get_pending_jobs(self) -> list[VenueResearchJob]:
        """Get jobs that haven't been started yet."""
        return [j for j in self.jobs if j.status == JobStatus.PENDING]

    def get_completed_jobs(self) -> list[VenueResearchJob]:
        """Get jobs that have been completed."""
        return [j for j in self.jobs if j.status == JobStatus.COMPLETED]

    def get_failed_jobs(self) -> list[VenueResearchJob]:
        """Get jobs that have failed."""
        return [j for j in self.jobs if j.status == JobStatus.FAILED]

    def completion_percentage(self) -> float:
        """Calculate percentage of jobs completed."""
        if not self.jobs:
            return 0.0
        completed = len(self.get_completed_jobs())
        return (completed / len(self.jobs)) * 100

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON/Redis storage."""
        return {
            "session_id": self.session_id,
            "venues_file": self.venues_file,
            "min_confidence": self.min_confidence,
            "max_venues": self.max_venues,
            "total_venues": self.total_venues,
            "venues_needing_enrichment": self.venues_needing_enrichment,
            "jobs": [j.to_dict() for j in self.jobs],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnrichmentSession":
        """Deserialize from dict (from JSON/Redis storage)."""
        return cls(
            session_id=data["session_id"],
            venues_file=data["venues_file"],
            min_confidence=data["min_confidence"],
            max_venues=data.get("max_venues"),
            total_venues=data.get("total_venues", 0),
            venues_needing_enrichment=data.get("venues_needing_enrichment", 0),
            jobs=[VenueResearchJob.from_dict(j) for j in data.get("jobs", [])],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )
