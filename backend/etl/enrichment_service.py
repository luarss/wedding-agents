#!/usr/bin/env python3
"""
Venue Enrichment Service - State management for venue research jobs.

This service handles all state tracking that was previously embedded in MCP tools.
It provides methods to:
- Identify venues needing enrichment
- Generate research jobs with search queries
- Track job status and progress
- Update venue data with enrichment results

The service is designed to work with job queue systems like Redis for parallel execution.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.etl.models import (
    EnrichmentSession,
    JobStatus,
    SearchQuery,
    VenueResearchJob,
)


class VenueEnrichmentService:
    """Service for managing venue enrichment state and operations."""

    def __init__(self, venues_file: Path):
        """
        Initialize the enrichment service.

        Args:
            venues_file: Path to venues.json file
        """
        self.venues_file = venues_file
        self._venues_cache: list[dict[str, Any]] | None = None

    def _load_venues(self, force_reload: bool = False) -> list[dict[str, Any]]:
        """Load venues from JSON file with caching."""
        if self._venues_cache is None or force_reload:
            with open(self.venues_file, encoding="utf-8") as f:
                data = json.load(f)

            # Handle both {"venues": [...]} and direct array formats
            if isinstance(data, dict):
                venues = data.get("venues", [])
                self._venues_cache = venues if isinstance(venues, list) else []
            elif isinstance(data, list):
                self._venues_cache = data
            else:
                raise ValueError(f"Unexpected data format. Expected dict or list, got {type(data)}")

        return self._venues_cache if self._venues_cache is not None else []

    def _save_venues(self, venues: list[dict[str, Any]]) -> None:
        """Save venues back to JSON file."""
        with open(self.venues_file, "w", encoding="utf-8") as f:
            json.dump({"venues": venues}, f, indent=2, ensure_ascii=False)
        self._venues_cache = None  # Invalidate cache

    def create_enrichment_session(
        self,
        min_confidence: float = 0.7,
        max_venues: int | None = None,
    ) -> EnrichmentSession:
        """
        Create a new enrichment session by identifying venues needing enrichment.

        Args:
            min_confidence: Minimum confidence threshold
            max_venues: Maximum number of venues to enrich (None = all)

        Returns:
            EnrichmentSession with jobs for venues needing enrichment
        """
        venues = self._load_venues()

        # Filter venues needing enrichment
        needs_enrichment = []
        for v in venues:
            if not isinstance(v, dict):
                continue

            # Calculate confidence score if not present
            if "confidence_score" not in v:
                v["confidence_score"] = self._calculate_confidence_score(v)

            # Check if enrichment is needed
            if v["confidence_score"] < min_confidence or v.get("needs_review", []):
                needs_enrichment.append(v)

        # Create session
        session_id = f"enrichment-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        session = EnrichmentSession(
            session_id=session_id,
            venues_file=str(self.venues_file),
            min_confidence=min_confidence,
            max_venues=max_venues,
            total_venues=len(venues),
            venues_needing_enrichment=len(needs_enrichment),
        )

        # Limit venues if max_venues specified
        venues_to_enrich = needs_enrichment[:max_venues] if max_venues else needs_enrichment

        # Create research jobs for each venue
        for venue in venues_to_enrich:
            job = self.create_research_job(venue)
            session.jobs.append(job)

        return session

    def create_research_job(self, venue: dict[str, Any]) -> VenueResearchJob:
        """
        Create a research job for a single venue.

        Args:
            venue: Venue dictionary with id, name, and existing data

        Returns:
            VenueResearchJob with search queries generated
        """
        venue_id = venue.get("id", "")
        venue_name = venue.get("name", "")
        confidence = venue.get("confidence_score", 0.0)
        missing_fields = self._identify_missing_fields(venue)

        # Generate search queries
        search_queries = self._generate_search_queries(venue_name, missing_fields)

        return VenueResearchJob(
            venue_id=venue_id,
            venue_name=venue_name,
            missing_fields=missing_fields,
            search_queries=search_queries,
            confidence_before=confidence,
            status=JobStatus.PENDING,
        )

    def _generate_search_queries(
        self,
        venue_name: str,
        missing_fields: list[str],
    ) -> list[SearchQuery]:
        """
        Generate optimized search queries for a venue.

        Returns 6 queries designed to be executed in parallel.
        """
        # Map field names to query categories
        field_to_category = {
            "price_per_table": "pricing",
            "min_spend": "pricing",
            "pricing_type": "pricing",
            "phone": "contact",
            "email": "contact",
            "address": "contact",
            "postal": "contact",
            "max_capacity": "capacity",
            "min_tables": "capacity",
            "comfortable_capacity": "capacity",
            "av_equipment": "amenities",
            "bridal_suite": "amenities",
            "outdoor_area": "amenities",
            "parking_lots": "amenities",
            "nearest_mrt": "location",
            "mrt_distance": "location",
            "mrt_lines": "location",
        }

        # Build targeted queries based on missing fields
        query_templates = {
            "pricing": f'"{venue_name}" Singapore wedding ballroom pricing per table 2024 2025',
            "contact": f'"{venue_name}" Singapore contact phone email address postal code',
            "capacity": f'"{venue_name}" Singapore wedding capacity guest count minimum maximum',
            "amenities": f'"{venue_name}" Singapore wedding packages amenities bridal suite features',
            "reviews": f'"{venue_name}" Singapore wedding reviews rating testimonials',
            "location": f'"{venue_name}" Singapore MRT location nearest station distance',
        }

        # Determine which categories are needed
        if missing_fields:
            categories_needed = set()
            for field in missing_fields:
                category = field_to_category.get(field)
                if category:
                    categories_needed.add(category)

            # Always include reviews for description/rating
            categories_needed.add("reviews")

            # If we have specific needs, filter to those
            if categories_needed:
                query_templates = {k: v for k, v in query_templates.items() if k in categories_needed}

        # Create SearchQuery objects
        search_queries = [
            SearchQuery(category=category, query=query, priority=1 if category in ["pricing", "contact"] else 2)
            for category, query in query_templates.items()
        ]

        return search_queries

    def update_venue_with_enrichment(
        self,
        venue_id: str,
        enrichment_data: dict[str, Any],
    ) -> tuple[float, float]:
        """
        Update a venue with enriched data.

        Args:
            venue_id: ID of venue to update
            enrichment_data: Enriched data to merge

        Returns:
            Tuple of (old_confidence, new_confidence)
        """
        venues = self._load_venues(force_reload=True)

        # Find venue to update
        venue_index = None
        for i, v in enumerate(venues):
            if v.get("id") == venue_id:
                venue_index = i
                break

        if venue_index is None:
            raise ValueError(f"Venue not found: {venue_id}")

        # Merge enrichment data
        venue = venues[venue_index]
        old_confidence = venue.get("confidence_score", 0.0)

        self._deep_merge(venue, enrichment_data)

        # Recalculate confidence score
        new_confidence = self._calculate_confidence_score(venue)
        venue["confidence_score"] = new_confidence

        # Clear needs_review if confidence improved significantly
        if new_confidence > 0.7:
            venue["needs_review"] = []

        # Update timestamp
        venue["last_updated"] = datetime.now().isoformat()

        # Save updated data
        venues[venue_index] = venue
        self._save_venues(venues)

        return old_confidence, new_confidence

    def get_venue(self, venue_id: str) -> dict[str, Any] | None:
        """Get a specific venue by ID."""
        venues = self._load_venues()
        for v in venues:
            if v.get("id") == venue_id:
                return v
        return None

    def get_enrichment_statistics(self) -> dict[str, Any]:
        """Get current enrichment statistics for all venues."""
        venues = self._load_venues(force_reload=True)

        total = len(venues)
        confidence_scores = []
        needs_enrichment = 0

        for v in venues:
            if not isinstance(v, dict):
                continue

            score = v.get("confidence_score", 0.0)
            confidence_scores.append(score)

            if score < 0.7 or v.get("needs_review", []):
                needs_enrichment += 1

        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        return {
            "total_venues": total,
            "needs_enrichment": needs_enrichment,
            "enrichment_percentage": (needs_enrichment / total * 100) if total > 0 else 0,
            "average_confidence": round(avg_confidence, 2),
        }

    # Helper methods

    def _identify_missing_fields(self, venue: dict) -> list[str]:
        """Identify missing critical/high-priority fields in a venue."""
        missing = []

        def safe_get_dict(obj: dict, key: str) -> dict:
            val = obj.get(key, {})
            return val if isinstance(val, dict) else {}

        # Check critical fields
        pricing = safe_get_dict(venue, "pricing")
        if not pricing.get("pricing_type"):
            missing.append("pricing_type")
        if not pricing.get("price_per_table"):
            missing.append("price_per_table")

        capacity = safe_get_dict(venue, "capacity")
        if not capacity.get("max_capacity"):
            missing.append("max_capacity")

        # Check high-priority fields
        location = safe_get_dict(venue, "location")
        if not location.get("zone"):
            missing.append("zone")
        if not location.get("address"):
            missing.append("address")

        contact = safe_get_dict(venue, "contact")
        if not contact.get("phone"):
            missing.append("phone")
        if not contact.get("email"):
            missing.append("email")

        return missing

    def _deep_merge(self, target: dict, source: dict):
        """Deep merge source dict into target dict."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _calculate_confidence_score(self, venue: dict) -> float:
        """
        Calculate confidence score based on field completeness.

        Scoring:
        - Critical fields: 40% weight
        - High priority fields: 30% weight
        - Medium priority fields: 20% weight
        - Low priority fields: 10% weight
        """
        score = 0.0

        # Critical fields (40%)
        critical_fields = [
            "name",
            "venue_type",
            "pricing.price_per_table",
            "pricing.pricing_type",
            "capacity.max_capacity",
        ]
        critical_filled = sum(1 for f in critical_fields if self._has_field(venue, f))
        score += (critical_filled / len(critical_fields)) * 0.4

        # High priority fields (30%)
        high_fields = [
            "location.address",
            "location.zone",
            "pricing.min_spend",
            "contact.phone",
            "contact.email",
        ]
        high_filled = sum(1 for f in high_fields if self._has_field(venue, f))
        score += (high_filled / len(high_fields)) * 0.3

        # Medium priority fields (20%)
        medium_fields = [
            "location.nearest_mrt",
            "amenities.bridal_suite",
            "description",
            "rating",
        ]
        medium_filled = sum(1 for f in medium_fields if self._has_field(venue, f))
        score += (medium_filled / len(medium_fields)) * 0.2

        # Low priority fields (10%)
        low_fields = ["restrictions.outside_catering", "contact.website"]
        low_filled = sum(1 for f in low_fields if self._has_field(venue, f))
        score += (low_filled / len(low_fields)) * 0.1

        return round(score, 2)

    def _has_field(self, obj: dict, field_path: str) -> bool:
        """Check if nested field exists and is non-empty."""
        parts = field_path.split(".")
        current = obj

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False

        return bool(current) and current != "" and current != [] and current != {}
