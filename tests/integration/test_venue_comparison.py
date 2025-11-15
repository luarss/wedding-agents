"""
Integration tests for the Venue Comparison Flow
"""

import pytest
from backend.flows import run_venue_comparison


@pytest.mark.integration
def test_venue_comparison_valid():
    """Test the venue comparison flow with valid parameters"""

    result = run_venue_comparison(
        guest_count=180,
        total_budget=35000,
        location_preference="Central",
        style_preference="Modern, good MRT access",
        wedding_date="2025-11-15"
    )

    # Basic assertions
    assert result is not None, "Result should not be None"
    assert isinstance(result, str), "Result should be a string"
    assert len(result) > 0, "Result should not be empty"
    assert "venue" in result.lower(), "Result should mention venues"
