"""
Wedding Venue Comparison using scalable agent architecture
Demonstrates the new tool registry and agent factory pattern
"""

from backend.agents.venue_comparison_agent import create_venue_comparison_agent, get_venue_comparison_prompt
from backend.observability import observability  # noqa: F401 - Initialize Langfuse instrumentation
from backend.tools import venue_tools  # noqa: F401 - Register tools


def run_venue_comparison(
    guest_count: int,
    total_budget: int,
    location_preference: str = "No strong preference",
    style_preference: str = "No specific preference",
    wedding_date: str | None = None,
    additional_context: str = "",
) -> str:
    """Run venue comparison using scalable agent architecture"""

    print(f"\n🔍 Starting venue comparison for {guest_count} guests with S${total_budget:,} budget...")
    print("🤖 Agent is working...\n")

    # Create agent using factory pattern
    agent = create_venue_comparison_agent()

    # Generate task prompt
    task_prompt = get_venue_comparison_prompt(
        guest_count=guest_count,
        total_budget=total_budget,
        location_preference=location_preference,
        style_preference=style_preference,
        wedding_date=wedding_date,
        additional_context=additional_context,
    )

    # Run the agent (Langfuse tracing happens automatically via instrumentation)
    result = agent.run(task_prompt)

    print("\n✅ Venue comparison complete!\n")

    return str(result)


# Example usage
if __name__ == "__main__":
    # Example: 180 guests, $35,000 budget, Central location preferred
    result = run_venue_comparison(
        guest_count=180,
        total_budget=35000,
        location_preference="Central",
        style_preference="Modern, good MRT access",
        wedding_date="2025-11-15",
        additional_context="Looking for good value, prefer venues with bridal suite",
    )

    print("\n" + "=" * 80)
    print("VENUE COMPARISON REPORT")
    print("=" * 80)
    print(result)
