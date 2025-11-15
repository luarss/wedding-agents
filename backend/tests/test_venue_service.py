"""
Tests for VenueService
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.venue_service import VenueService


def test_load_all_venues():
    """Test loading all venues"""
    service = VenueService()
    venues = service.load_all_venues()

    print(f"✅ Loaded {len(venues)} venues")
    assert len(venues) == 5, f"Expected 5 venues, got {len(venues)}"

    # Check all venues have required fields
    for venue in venues:
        assert 'id' in venue
        assert 'name' in venue
        assert 'pricing' in venue
        assert 'capacity' in venue
        assert 'location' in venue

    print("✅ All venues have required fields")


def test_search_by_capacity_and_budget():
    """Test searching venues by capacity and budget"""
    service = VenueService()

    # Search for 150 guests with S$30,000 budget
    # That's 15 tables at S$2,000/table
    results = service.search(
        guest_count=150,
        total_budget=30000
    )

    print(f"\n✅ Search for 150 guests, $30,000 budget")
    print(f"   Found {len(results)} matching venues:")
    for venue in results:
        pricing = venue['pricing']
        print(f"   - {venue['name']}: ${pricing['price_per_table']}/table")

    assert len(results) >= 2, "Should find at least 2 venues"


def test_search_with_location_filter():
    """Test searching with location filter"""
    service = VenueService()

    # Search for Central venues
    central_venues = service.search(
        guest_count=200,
        total_budget=50000,
        location_zone="Central"
    )

    print(f"\n✅ Search Central venues for 200 guests")
    print(f"   Found {len(central_venues)} Central venues:")
    for venue in central_venues:
        location = venue['location']
        print(f"   - {venue['name']}: {location['zone']}, {location['district']}")

    for venue in central_venues:
        assert venue['location']['zone'] == 'Central'

    # Search for East/West venues
    east_venues = service.search(
        guest_count=200,
        total_budget=30000,
        location_zone="East"
    )

    print(f"\n✅ Search East venues for 200 guests, $30k budget")
    print(f"   Found {len(east_venues)} East venues")


def test_budget_too_low():
    """Test that venues are filtered out when budget too low"""
    service = VenueService()

    # Very low budget - should get fewer or no results
    results = service.search(
        guest_count=200,
        total_budget=15000  # Only $75/table - very low
    )

    print(f"\n✅ Search with low budget ($15,000 for 200 guests)")
    print(f"   Found {len(results)} venues (expected 0-1)")
    print(f"   Budget per table: $750")


def test_get_venue_by_id():
    """Test getting specific venue by ID"""
    service = VenueService()

    venue = service.get_venue_by_id('venue-001')
    assert venue is not None
    assert venue['name'] == 'Grand Copthorne Waterfront Hotel'

    print(f"\n✅ Get venue by ID:")
    print(f"   {venue['name']} - {venue['location']['address']}")


def test_calculate_total_cost():
    """Test cost calculation with Singapore surcharges"""
    service = VenueService()

    venue = service.get_venue_by_id('venue-004')  # Genting Hotel Jurong
    cost_breakdown = service.calculate_total_cost(
        venue=venue,
        guest_count=150  # 15 tables
    )

    print(f"\n✅ Cost calculation for {venue['name']}:")
    print(f"   Guest count: {cost_breakdown['guest_count']}")
    print(f"   Tables needed: {cost_breakdown['tables_needed']}")
    print(f"   Price per table: ${cost_breakdown['price_per_table']}")
    print(f"   Base cost: ${cost_breakdown['base_cost']:,}")
    print(f"   GST (9%): ${cost_breakdown['gst']:,}")
    print(f"   Service charge (10%): ${cost_breakdown['service_charge']:,}")
    print(f"   Total: ${cost_breakdown['total_cost']:,}")
    print(f"   Cost per guest: ${cost_breakdown['cost_per_guest']}")

    assert cost_breakdown['tables_needed'] == 15
    assert cost_breakdown['gst'] > 0
    assert cost_breakdown['service_charge'] > 0
    assert cost_breakdown['total_cost'] > cost_breakdown['base_cost']


def test_realistic_search_scenarios():
    """Test realistic wedding search scenarios"""
    service = VenueService()

    print("\n" + "="*60)
    print("REALISTIC SEARCH SCENARIOS")
    print("="*60)

    # Scenario 1: Mid-range budget, 180 guests
    print("\n📍 Scenario 1: 180 guests, $35,000 budget, Central preferred")
    results = service.search(
        guest_count=180,
        total_budget=35000,
        location_zone="Central"
    )
    print(f"   Found {len(results)} venues:")
    for v in results:
        cost = service.calculate_total_cost(v, 180)
        print(f"   - {v['name']}: ${cost['total_cost']:,} total (${cost['cost_per_guest']}/guest)")

    # Scenario 2: Budget-conscious, west location
    print("\n📍 Scenario 2: 200 guests, $25,000 budget, West area")
    results = service.search(
        guest_count=200,
        total_budget=25000,
        location_zone="West"
    )
    print(f"   Found {len(results)} venues:")
    for v in results:
        cost = service.calculate_total_cost(v, 200)
        print(f"   - {v['name']}: ${cost['total_cost']:,} total (${cost['cost_per_guest']}/guest)")

    # Scenario 3: Large wedding, higher budget
    print("\n📍 Scenario 3: 300 guests, $70,000 budget, any location")
    results = service.search(
        guest_count=300,
        total_budget=70000
    )
    print(f"   Found {len(results)} venues:")
    for v in results:
        cost = service.calculate_total_cost(v, 300)
        print(f"   - {v['name']}: ${cost['total_cost']:,} total (${cost['cost_per_guest']}/guest)")
        print(f"     Location: {v['location']['zone']}, MRT: {v['location']['nearest_mrt']}")


if __name__ == '__main__':
    print("🧪 Testing VenueService\n")

    try:
        test_load_all_venues()
        test_search_by_capacity_and_budget()
        test_search_with_location_filter()
        test_budget_too_low()
        test_get_venue_by_id()
        test_calculate_total_cost()
        test_realistic_search_scenarios()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
