"""
Wedding Venue Comparison using smolagents
Simplified single-agent approach with custom tools
"""

import json
from typing import ClassVar

from smolagents import CodeAgent, LiteLLMModel, Tool

from backend.config import config
from backend.services.venue_service import VenueService


class SearchVenuesTool(Tool):
    name = "search_venues"
    description = """
    Search for wedding venues in Singapore that match the requirements.
    Returns a list of venues with details about capacity, pricing, location, and amenities.
    """
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


class CalculateCostTool(Tool):
    name = "calculate_venue_cost"
    description = """
    Calculate the total cost for a specific venue including Singapore surcharges (9% GST and 10% service charge).
    Provides detailed breakdown of base cost, GST, service charge, and total cost.
    """
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


def run_venue_comparison(
    guest_count: int,
    total_budget: int,
    location_preference: str = "No strong preference",
    style_preference: str = "No specific preference",
    wedding_date: str | None = None,
    additional_context: str = "",
) -> str:
    """Run venue comparison using smolagents CodeAgent"""

    # Calculate tables needed
    tables_needed = (guest_count + 9) // 10

    # Initialize the LLM model
    model = LiteLLMModel(model_id=config.get_llm_model_id(), api_key=config.get_llm_api_key(), temperature=0.7)

    # Initialize tools
    tools = [SearchVenuesTool(), CalculateCostTool()]

    # Create the agent
    agent = CodeAgent(tools=tools, model=model, max_steps=15, verbosity_level=2 if config.AGENT_VERBOSE else 0)

    # Create comprehensive task prompt
    task_prompt = f"""
You are a Singapore wedding venue expert helping a couple find the perfect wedding venue.

**Wedding Requirements:**
- Guest Count: {guest_count} guests ({tables_needed} tables needed - Singapore standard is 10 guests per table)
- Total Budget: S${total_budget:,}
- Location Preference: {location_preference}
- Style Preference: {style_preference}
- Wedding Date: {wedding_date or "Not specified"}
- Additional Context: {additional_context or "None"}

**Your Task:**
Follow these steps to provide a comprehensive venue comparison:

1. **Search for Venues**: Use the search_venues tool to find venues that match the guest count and budget.
   - Consider the location preference if specified
   - Look for venues with appropriate capacity

2. **Calculate Real Costs**: For each promising venue (select top 3-5), use calculate_venue_cost to get
   accurate pricing:
   - Remember Singapore pricing includes 9% GST and 10% service charge ("plus plus")
   - Some venues have "nett" pricing (already inclusive)
   - Calculate for the exact guest count

3. **Analyze Each Venue**: For each venue, consider:
   - Budget fit: Does it fit within S${total_budget:,}?
   - Location & Accessibility: MRT access, parking availability
   - Capacity: Can it comfortably host {guest_count} guests?
   - Amenities: What's included? (Bridal suite, AV equipment, decor, etc.)
   - Value for money: What do you get for the price?

4. **Create Comparison Report**: Generate a comprehensive markdown report with:
   - **Executive Summary**: Quick overview with top recommendation
   - **Top 3 Venues Ranked**: For each venue include:
     * Venue name and location
     * Pricing breakdown (base + GST + service charge = total)
     * Cost per guest
     * Pros and cons
     * Best for: (type of couple/wedding)
   - **Side-by-Side Comparison Table**: Compare key factors
   - **Budget Analysis**: How do costs compare to the S${total_budget:,} budget?
   - **Final Recommendation**: Which venue(s) to visit and why
   - **Next Steps**: What the couple should do next

**Singapore Wedding Context You Should Know:**
- Standard table size: 10 guests
- Pricing types: "plus plus" (add 9% GST + 10% service) vs "nett" (inclusive)
- Peak season: November-December (higher prices)
- Weekday vs weekend pricing differs significantly
- Location zones: Central (most convenient), East, West, North
- MRT accessibility is important for guests without cars

Provide a detailed, actionable report that helps the couple make an informed decision.
"""

    print(f"\n🔍 Starting venue comparison for {guest_count} guests with S${total_budget:,} budget...")
    print("🤖 Agent is working...\n")

    # Run the agent (Langfuse tracing happens automatically via instrumentation)
    result = agent.run(task_prompt)

    print("\n✅ Venue comparison complete!\n")

    return str(result)
