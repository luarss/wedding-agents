#!/usr/bin/env python3
"""
Venue enrichment tool for Claude Agent SDK - Version 2 (Stateless).

Provides MCP tools that are stateless and delegate state management to VenueEnrichmentService.
This design supports parallelization via job queue systems like Redis.

Key changes from V1:
- Tools are stateless - no file I/O in tools themselves
- Tools return job specifications that can be queued
- State tracking happens in VenueEnrichmentService
- Designed for parallel execution of research jobs
"""

from pathlib import Path
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from backend.etl.enrichment_service import VenueEnrichmentService
from backend.etl.models import JobStatus


@tool(
    name="create_enrichment_session",
    description="""
    Create a new enrichment session by identifying venues needing enrichment.
    Returns a session with research jobs ready to be executed in parallel.
    """,
    input_schema={
        "venues_file": {
            "type": "string",
            "description": "Path to venues.json file",
        },
        "min_confidence": {
            "type": "number",
            "description": "Minimum confidence threshold (default: 0.7)",
        },
        "max_venues": {
            "type": "number",
            "description": "Maximum number of venues to enrich (optional)",
        },
    },
)
async def create_enrichment_session(args: dict[str, Any]) -> dict[str, Any]:
    """
    Create enrichment session with research jobs.

    Returns session data including all jobs ready for parallel execution.
    """
    venues_file = Path(args["venues_file"])
    min_confidence = float(args.get("min_confidence", 0.7))
    max_venues = int(args["max_venues"]) if args.get("max_venues") else None

    if not venues_file.exists():
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error: File not found: {venues_file}",
                }
            ]
        }

    try:
        service = VenueEnrichmentService(venues_file)
        session = service.create_enrichment_session(
            min_confidence=min_confidence,
            max_venues=max_venues,
        )

        # Format response
        summary_text = f"""🔍 Enrichment Session Created

**Session ID:** `{session.session_id}`

**Summary:**
- Total venues: {session.total_venues}
- Need enrichment: {session.venues_needing_enrichment} ({session.venues_needing_enrichment / session.total_venues * 100:.1f}%)
- Research jobs created: {len(session.jobs)}

**Research Jobs (ready for parallel execution):**

{chr(10).join([
    f"**Job {i+1}: {job.venue_name}**"
    f"  - Venue ID: `{job.venue_id}`"
    f"  - Confidence: {job.confidence_before:.2f}"
    f"  - Missing fields: {', '.join(job.missing_fields[:5])}"
    f"  - Search queries: {len(job.search_queries)}"
    for i, job in enumerate(session.jobs[:10])
])}

{f'... and {len(session.jobs) - 10} more jobs' if len(session.jobs) > 10 else ''}

**Next step:** Use `get_research_job` to get a job, then execute its search queries in parallel using WebSearch.
"""

        return {
            "content": [
                {
                    "type": "text",
                    "text": summary_text,
                },
                {
                    "type": "text",
                    "text": f"```json\n{str(session.to_dict())}\n```",
                },
            ]
        }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error creating session: {str(e)}",
                }
            ]
        }


@tool(
    name="get_research_job",
    description="""
    Get a specific research job with its search queries.
    Returns the job details and queries to execute in parallel via WebSearch.
    """,
    input_schema={
        "venues_file": {
            "type": "string",
            "description": "Path to venues.json file",
        },
        "venue_id": {
            "type": "string",
            "description": "ID of the venue to research",
        },
    },
)
async def get_research_job(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get a research job for a specific venue.

    Returns job with search queries ready for parallel execution.
    """
    venues_file = Path(args["venues_file"])
    venue_id = args["venue_id"]

    if not venues_file.exists():
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error: File not found: {venues_file}",
                }
            ]
        }

    try:
        service = VenueEnrichmentService(venues_file)
        venue = service.get_venue(venue_id)

        if not venue:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Error: Venue not found: {venue_id}",
                    }
                ]
            }

        # Create research job
        job = service.create_research_job(venue)

        # Format search queries for parallel execution
        queries_text = "\n".join(
            [f"{i+1}. **{q.category.upper()}**: `{q.query}`" for i, q in enumerate(job.search_queries)]
        )

        response_text = f"""⚡ Research Job: {job.venue_name}

**Venue Details:**
- ID: `{job.venue_id}`
- Current confidence: {job.confidence_before:.2f}
- Missing fields: {', '.join(job.missing_fields) if job.missing_fields else 'None'}

**Search Queries (execute ALL in PARALLEL):**

{queries_text}

**CRITICAL: Execute ALL {len(job.search_queries)} WebSearch calls in a SINGLE message for parallel execution.**

After receiving all search results, use `update_venue_with_results` to save the enrichment.
"""

        return {
            "content": [
                {
                    "type": "text",
                    "text": response_text,
                },
                {
                    "type": "text",
                    "text": f"```json\n{str(job.to_dict())}\n```",
                },
            ]
        }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error getting research job: {str(e)}",
                }
            ]
        }


@tool(
    name="update_venue_with_results",
    description="""
    Update a venue with enrichment data extracted from search results.
    This saves the enrichment and recalculates the confidence score.
    """,
    input_schema={
        "venues_file": {
            "type": "string",
            "description": "Path to venues.json file",
        },
        "venue_id": {
            "type": "string",
            "description": "ID of venue to update",
        },
        "enrichment_data": {
            "type": "object",
            "description": "Enriched data to merge (pricing, contact, location, capacity, amenities, etc.)",
        },
    },
)
async def update_venue_with_results(args: dict[str, Any]) -> dict[str, Any]:
    """
    Update venue with enriched data and recalculate confidence score.
    """
    venues_file = Path(args["venues_file"])
    venue_id = args["venue_id"]
    enrichment_data = args.get("enrichment_data", {})

    if not venues_file.exists():
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error: File not found: {venues_file}",
                }
            ]
        }

    try:
        service = VenueEnrichmentService(venues_file)
        venue = service.get_venue(venue_id)

        if not venue:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Error: Venue not found: {venue_id}",
                    }
                ]
            }

        # Update venue with enrichment
        old_confidence, new_confidence = service.update_venue_with_enrichment(
            venue_id=venue_id,
            enrichment_data=enrichment_data,
        )

        # Summarize updates
        def summarize_value(value: Any) -> str:
            if isinstance(value, dict):
                return f"dict with {len(value)} keys"
            elif isinstance(value, list):
                return f"list with {len(value)} items"
            elif isinstance(value, str) and len(value) > 50:
                return f"{value[:50]}..."
            else:
                return str(value)

        response_text = f"""✅ Updated venue: {venue.get('name')}

**Enrichment summary:**
- Venue ID: `{venue_id}`
- Confidence: {old_confidence:.2f} → {new_confidence:.2f} ({'+' if new_confidence > old_confidence else ''}{new_confidence - old_confidence:.2f})
- Fields updated: {len(enrichment_data)}

**Updated fields:**
{chr(10).join([f'- `{k}`: {summarize_value(v)}' for k, v in enrichment_data.items()])}

**File saved:** `{venues_file}`

**Next:** Move to the next venue or generate final report.
"""

        return {
            "content": [
                {
                    "type": "text",
                    "text": response_text,
                }
            ]
        }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error updating venue: {str(e)}",
                }
            ]
        }


@tool(
    name="get_enrichment_statistics",
    description="""
    Get current enrichment statistics for all venues.
    Shows overall progress and venues still needing enrichment.
    """,
    input_schema={
        "venues_file": {
            "type": "string",
            "description": "Path to venues.json file",
        },
    },
)
async def get_enrichment_statistics(args: dict[str, Any]) -> dict[str, Any]:
    """Get enrichment statistics for reporting."""
    venues_file = Path(args["venues_file"])

    if not venues_file.exists():
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error: File not found: {venues_file}",
                }
            ]
        }

    try:
        service = VenueEnrichmentService(venues_file)
        stats = service.get_enrichment_statistics()

        response_text = f"""📊 Enrichment Statistics

**Overall Progress:**
- Total venues: {stats['total_venues']}
- Need enrichment: {stats['needs_enrichment']} ({stats['enrichment_percentage']:.1f}%)
- Average confidence: {stats['average_confidence']:.2f}

**Status:**
{
    '✅ All venues meet minimum confidence threshold!' if stats['needs_enrichment'] == 0
    else f"⚠️  {stats['needs_enrichment']} venues still need enrichment"
}
"""

        return {
            "content": [
                {
                    "type": "text",
                    "text": response_text,
                }
            ]
        }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error getting statistics: {str(e)}",
                }
            ]
        }


# Create MCP server with all enrichment tools
def create_enrichment_server_v2():
    """Create MCP server for venue enrichment tools (v2 - stateless)."""
    return create_sdk_mcp_server(
        name="venue_enrichment",
        tools=[
            create_enrichment_session,
            get_research_job,
            update_venue_with_results,
            get_enrichment_statistics,
        ],
    )
