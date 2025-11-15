"""
Integration tests for the Venue Comparison Flow (smolagents)
"""

import pytest

from backend.flows import run_venue_comparison


@pytest.mark.integration
def test_venue_comparison_valid():
    """Test the venue comparison flow with valid parameters using smolagents"""

    result = run_venue_comparison(
        guest_count=180,
        total_budget=35000,
        location_preference="Central",
        style_preference="Modern, good MRT access",
        wedding_date="2025-11-15",
    )

    # Basic assertions
    assert result is not None, "Result should not be None"
    assert isinstance(result, str), "Result should be a string"
    assert len(result) > 0, "Result should not be empty"

    # Check that the result contains venue-related content
    result_lower = result.lower()
    assert any(keyword in result_lower for keyword in ["venue", "hotel", "wedding"]), (
        "Result should mention venues or hotels"
    )


@pytest.mark.integration
def test_venue_comparison_tools_used():
    """Test that the agent uses the custom tools (search_venues, calculate_venue_cost)"""

    result = run_venue_comparison(guest_count=150, total_budget=30000, location_preference="East")

    # The result should contain cost information (indicates calculate_venue_cost was used)
    result_lower = result.lower()
    assert any(keyword in result_lower for keyword in ["cost", "price", "budget", "$", "s$"]), (
        "Result should contain cost information"
    )


@pytest.mark.integration
def test_venue_comparison_budget_conscious():
    """Test venue comparison with lower budget"""

    result = run_venue_comparison(guest_count=200, total_budget=25000, location_preference="West")

    assert result is not None
    assert len(result) > 0

    # Should still provide meaningful results even with lower budget
    result_lower = result.lower()
    assert any(keyword in result_lower for keyword in ["venue", "budget", "recommendation"]), (
        "Result should provide budget-conscious recommendations"
    )
