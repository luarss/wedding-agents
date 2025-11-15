"""
Wedding Venue Comparison Crew

This module contains the CrewAI setup for wedding venue comparison,
including agents, tasks, and tools.
"""

from .venue_comparison.crew import VenueComparisonCrew, run_venue_comparison

__all__ = ['VenueComparisonCrew', 'run_venue_comparison']
