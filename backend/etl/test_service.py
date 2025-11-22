#!/usr/bin/env python3
"""
Quick test script for VenueEnrichmentService.

Tests the core functionality without requiring Claude Agent SDK.
"""

import json
from pathlib import Path

from backend.etl.enrichment_service import VenueEnrichmentService


def test_service():
    """Test the enrichment service with sample data."""
    venues_file = Path("backend/data/venues.json")

    if not venues_file.exists():
        print(f"❌ File not found: {venues_file}")
        return

    print("=" * 80)
    print("Testing VenueEnrichmentService")
    print("=" * 80)

    # Test 1: Create service
    print("\n1. Creating service...")
    service = VenueEnrichmentService(venues_file)
    print("✅ Service created")

    # Test 2: Get statistics
    print("\n2. Getting current statistics...")
    stats = service.get_enrichment_statistics()
    print(f"   Total venues: {stats['total_venues']}")
    print(f"   Need enrichment: {stats['needs_enrichment']} ({stats['enrichment_percentage']:.1f}%)")
    print(f"   Average confidence: {stats['average_confidence']:.2f}")

    # Test 3: Create enrichment session
    print("\n3. Creating enrichment session (max 3 venues)...")
    session = service.create_enrichment_session(min_confidence=0.7, max_venues=3)
    print(f"✅ Session created: {session.session_id}")
    print(f"   Jobs created: {len(session.jobs)}")

    if session.jobs:
        print(f"\n   First job:")
        job = session.jobs[0]
        print(f"   - Venue: {job.venue_name}")
        print(f"   - ID: {job.venue_id}")
        print(f"   - Confidence: {job.confidence_before:.2f}")
        print(f"   - Missing fields: {', '.join(job.missing_fields[:5])}")
        print(f"   - Search queries: {len(job.search_queries)}")

        # Test 4: Show search queries
        print(f"\n4. Search queries for '{job.venue_name}':")
        for i, query in enumerate(job.search_queries, 1):
            print(f"   {i}. [{query.category.upper()}] {query.query}")

        # Test 5: Test serialization
        print("\n5. Testing job serialization...")
        job_dict = job.to_dict()
        print(f"   ✅ Serialized to dict ({len(job_dict)} keys)")

        # Deserialize
        from backend.etl.models import VenueResearchJob

        job_restored = VenueResearchJob.from_dict(job_dict)
        print(f"   ✅ Deserialized from dict")
        print(f"   Match: {job_restored.venue_id == job.venue_id}")

        # Test 6: Test session serialization
        print("\n6. Testing session serialization...")
        session_dict = session.to_dict()
        print(f"   ✅ Serialized to dict ({len(session_dict)} keys)")

        # Check JSON serializable
        json_str = json.dumps(session_dict, indent=2)
        print(f"   ✅ JSON serializable ({len(json_str)} chars)")

    print("\n" + "=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    test_service()
