"""
Venue Comparison Agent - Configured agent for wedding venue comparison
"""

from smolagents import CodeAgent

from backend.core.agent_factory import AgentConfig, AgentFactory
from backend.core.tool_registry import ToolRegistry

# Agent configuration
venue_comparison_config = AgentConfig(
    name="venue_comparison_agent",
    description="Singapore wedding venue expert that helps couples find the perfect wedding venue",
    tools=["search_venues", "calculate_venue_cost"],  # Tools from registry
    max_steps=15,
    verbosity_level=2,
    temperature=0.7,
)


def create_venue_comparison_agent() -> CodeAgent:
    """Create a venue comparison agent with all necessary tools"""
    return AgentFactory.create_agent(venue_comparison_config, ToolRegistry)


def get_venue_comparison_prompt(
    guest_count: int,
    total_budget: int,
    location_preference: str = "No strong preference",
    style_preference: str = "No specific preference",
    wedding_date: str | None = None,
    additional_context: str = "",
) -> str:
    """Generate the task prompt for venue comparison"""

    tables_needed = (guest_count + 9) // 10

    return f"""
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

4. **Create Comparison Report**: Use final_answer() with a comprehensive markdown report including:
   - **Executive Summary**: Quick overview with top recommendation
   - **Top 3 Venues Ranked**: For each venue include:
     * Venue name and location
     * Pricing breakdown (base + GST + service charge = total)
     * Cost per guest
     * Pros and cons
     * Best for: (type of couple/wedding)
   - **Quick Comparison**: Simple markdown comparison of key factors
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
