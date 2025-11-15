"""
Wedding Venue Comparison Crew
Orchestrates 3 agents to provide comprehensive venue comparison
"""

from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task

from backend.config import config
from backend.services.venue_service import VenueService
from crewai.tools import tool


@tool("Search Wedding Venues")
def search_venues_tool(guest_count: int, total_budget: int, location_zone: str = None) -> str:
    """
    Search for wedding venues that match the requirements.

    Args:
        guest_count: Number of guests attending
        total_budget: Total budget for the venue
        location_zone: Optional location preference (Central, East, West, North)

    Returns:
        JSON string of matching venues
    """
    service = VenueService()
    venues = service.search(
        guest_count=guest_count,
        total_budget=total_budget,
        location_zone=location_zone
    )

    import json
    return json.dumps(venues, indent=2)


@tool("Calculate Venue Cost")
def calculate_cost_tool(venue_id: str, guest_count: int, package_name: str = None) -> str:
    """
    Calculate the total cost for a specific venue including Singapore surcharges.

    Args:
        venue_id: Venue ID (e.g., 'venue-001')
        guest_count: Number of guests
        package_name: Optional package name (e.g., 'Weekend Dinner')

    Returns:
        JSON string with cost breakdown including GST and service charge
    """
    service = VenueService()
    venue = service.get_venue_by_id(venue_id)

    if not venue:
        import json
        return json.dumps({"error": f"Venue {venue_id} not found"})

    cost_breakdown = service.calculate_total_cost(
        venue=venue,
        guest_count=guest_count,
        package_name=package_name
    )

    # Add venue name for context
    cost_breakdown['venue_name'] = venue['name']
    cost_breakdown['venue_id'] = venue_id

    import json
    return json.dumps(cost_breakdown, indent=2)


@CrewBase
class VenueComparisonCrew():
    """Venue Comparison Crew for Wedding Planning"""
    agents_config = 'backend/flows/venue_comparison/agents.yaml'
    tasks_config = 'backend/flows/venue_comparison/tasks.yaml'

    @agent
    def venue_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['venue_researcher'],
            llm=config.get_llm_model(),
            tools=[search_venues_tool]
        )

    @agent
    def budget_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['budget_analyzer'],
            llm=config.get_llm_model(),
            tools=[calculate_cost_tool]
        )

    @agent
    def comparison_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['comparison_generator'],
            llm=config.get_llm_model()
        )

    @task
    def research_venues(self) -> Task:
        return Task(config=self.tasks_config['research_venues'])

    @task
    def analyze_budget(self) -> Task:
        return Task(config=self.tasks_config['analyze_budget'])

    @task
    def generate_comparison(self) -> Task:
        return Task(config=self.tasks_config['generate_comparison'])

    @crew
    def crew(self) -> Crew:
        """Creates the Wedding Venue Comparison crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=config.CREW_VERBOSE
        )


def run_venue_comparison(
    guest_count: int,
    total_budget: int,
    location_preference: str = "No strong preference",
    style_preference: str = "No specific preference",
    wedding_date: str = None,
    additional_context: str = ""
) -> str:
    """Convenience function to run venue comparison"""

    # Calculate tables needed
    tables_needed = (guest_count + 9) // 10

    # Format venue IDs for all venues
    venue_ids = "venue-001, venue-002, venue-003, venue-004, venue-005"

    # Prepare inputs for YAML variable substitution
    inputs = {
        'guest_count': guest_count,
        'total_budget': total_budget,
        'location_preference': location_preference,
        'style_preference': style_preference,
        'tables_needed': tables_needed,
        'venue_ids': venue_ids,
        'wedding_date': wedding_date or "Not specified",
        'additional_context': additional_context or "None"
    }

    print(f"\n🔍 Starting venue comparison for {guest_count} guests with S${total_budget:,} budget...")
    print("🤖 Agents are working...\n")

    crew = VenueComparisonCrew()
    result = crew.crew().kickoff(inputs=inputs)

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
        additional_context="Looking for good value, prefer venues with bridal suite"
    )

    print("\n" + "="*80)
    print("VENUE COMPARISON REPORT")
    print("="*80)
    print(result)
