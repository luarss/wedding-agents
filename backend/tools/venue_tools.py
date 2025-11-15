"""
Wedding Venue Tools - Reusable tools for venue search and cost calculation
"""

import json
from typing import ClassVar

from backend.core.tool_registry import BaseTool, register_tool
from backend.services.venue_service import VenueService


@register_tool
class SearchVenuesTool(BaseTool):
    """Tool for searching wedding venues"""

    name = "search_venues"
    description = """
    Search for wedding venues in Singapore that match the requirements.
    Returns a list of venues with details about capacity, pricing, location, and amenities.
    """
    category = "venue"
    tags: ClassVar[list[str]] = ["wedding", "venue", "search"]
    inputs: ClassVar[dict] = {
        "guest_count": {"type": "integer", "description": "Number of guests attending the wedding"},
        "total_budget": {"type": "integer", "description": "Total budget for the venue in Singapore Dollars"},
        "location_zone": {
            "type": "string",
            "description": "Optional location preference: Central, East, West, or North. Can be None.",
            "nullable": True,
        },
    }
    output_type = "string"

    def forward(self, guest_count: int, total_budget: int, location_zone: str | None = None):
        """Search for matching venues"""
        service = VenueService()
        venues = service.search(guest_count=guest_count, total_budget=total_budget, location_zone=location_zone)
        return json.dumps(venues, indent=2)


@register_tool
class CalculateCostTool(BaseTool):
    """Tool for calculating venue costs with Singapore surcharges"""

    name = "calculate_venue_cost"
    description = """
    Calculate the total cost for a specific venue including Singapore surcharges (9% GST and 10% service charge).
    Provides detailed breakdown of base cost, GST, service charge, and total cost.
    """
    category = "venue"
    tags: ClassVar[list[str]] = ["wedding", "venue", "cost", "pricing"]
    inputs: ClassVar[dict] = {
        "venue_id": {"type": "string", "description": "Venue ID (e.g., 'venue-001')"},
        "guest_count": {"type": "integer", "description": "Number of guests"},
        "package_name": {
            "type": "string",
            "description": "Optional package name (e.g., 'Weekend Dinner'). Can be None.",
            "nullable": True,
        },
    }
    output_type = "string"

    def forward(self, venue_id: str, guest_count: int, package_name: str | None = None):
        """Calculate cost breakdown for a venue"""
        service = VenueService()
        venue = service.get_venue_by_id(venue_id)

        if not venue:
            return json.dumps({"error": f"Venue {venue_id} not found"})

        cost_breakdown = service.calculate_total_cost(venue=venue, guest_count=guest_count, package_name=package_name)

        # Add venue context
        cost_breakdown["venue_name"] = venue["name"]
        cost_breakdown["venue_id"] = venue_id

        return json.dumps(cost_breakdown, indent=2)
