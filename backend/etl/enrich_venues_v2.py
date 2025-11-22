#!/usr/bin/env python3
"""
Automated venue enrichment using Claude Agent SDK - Version 2.

This version uses stateless MCP tools and a service layer for state management.
Research jobs can be executed in sequence (and later parallelized with Redis).

Key improvements:
- State tracking moved to VenueEnrichmentService
- MCP tools are stateless and return job specifications
- Each venue research uses sequential MCP tool calls
- Designed for future Redis-based parallelization
"""

import argparse
import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from backend.etl.tools.enrich_tool_v2 import create_enrichment_server_v2


def _print_verbose_message(message: str) -> None:
    """Write a framed message to stderr for better visibility."""
    if not message:
        return

    lines = [line.rstrip() for line in message.splitlines()] or ["<empty message>"]
    width = max(len(line) for line in lines)
    border = "+" + "-" * (width + 4) + "+"

    print(border, file=sys.stderr)
    for line in lines:
        print(f"|  {line.ljust(width)}  |", file=sys.stderr)
    print(border, file=sys.stderr)
    sys.stderr.flush()


async def enrich_venues(
    venues_file: Path,
    min_confidence: float = 0.7,
    max_venues: int | None = None,
    interactive: bool = False,
):
    """
    Enrich venues using stateless MCP tools and service layer.

    Args:
        venues_file: Path to venues.json
        min_confidence: Minimum confidence threshold for enrichment
        max_venues: Maximum number of venues to enrich (None = all)
        interactive: Ask for confirmation before each venue enrichment
    """
    _print_verbose_message(
        "🚀 Starting venue enrichment with Claude Agent SDK (V2)\n"
        f"📂 Input file: {venues_file}\n"
        f"🎯 Target confidence: {min_confidence}\n"
        f"{'🔢 Max venues: ' + str(max_venues) if max_venues else ''}\n"
        f"🔄 Mode: {'Interactive' if interactive else 'Automated'}"
    )

    # Load system prompt
    _print_verbose_message("📝 Loading system prompt...")
    prompt_file = Path(__file__).parent / "prompts" / "enrichment_agent_prompt_v2.md"
    with open(prompt_file) as f:
        system_prompt = f.read()
    _print_verbose_message(f"✓ Loaded system prompt from {prompt_file}")

    # Create MCP server with enrichment tools (v2)
    _print_verbose_message("🔧 Creating enrichment MCP server (v2 - stateless)...")
    enrichment_server = create_enrichment_server_v2()
    _print_verbose_message("✓ MCP server created")

    # Configure agent options
    _print_verbose_message("⚙️  Configuring agent options...")
    options = ClaudeAgentOptions(
        mcp_servers={
            "venue_enrichment": enrichment_server
        },
        allowed_tools=[
            # V2 Enrichment tools (stateless)
            "mcp__venue_enrichment__create_enrichment_session",
            "mcp__venue_enrichment__get_research_job",
            "mcp__venue_enrichment__update_venue_with_results",
            "mcp__venue_enrichment__get_enrichment_statistics",
            # Web search
            "WebSearch",
        ],
        system_prompt=system_prompt,
        permission_mode="default",
    )
    _print_verbose_message("✓ Options created successfully")

    # Create agent client
    _print_verbose_message("🔌 Connecting to Claude SDK Client...")
    async with ClaudeSDKClient(options=options) as client:
        _print_verbose_message("✓ Connected to Claude SDK Client")

        # Step 1: Create enrichment session
        print("📊 Step 1: Creating enrichment session...\n")

        await client.query(
            f"""
            Use the create_enrichment_session tool to create a new enrichment session.

            Parameters:
            - venues_file: {venues_file}
            - min_confidence: {min_confidence}
            {'- max_venues: ' + str(max_venues) if max_venues else ''}

            This will identify all venues needing enrichment and create research jobs for them.
            Show me the session summary.
            """
        )

        async for message in client.receive_response():
            print(message, flush=True)

        # Step 2: Process venues one by one
        print("\n⚡ Step 2: Processing venues with sequential research jobs...\n")

        if interactive:
            response = input(
                "\nProceed with automated enrichment? (y/n): "
            )
            if response.lower() != "y":
                print("❌ Enrichment cancelled.")
                return

        enrichment_instruction = f"""
        Now process each venue that needs enrichment.

        WORKFLOW FOR EACH VENUE:
        1. Use get_research_job(venues_file="{venues_file}", venue_id="<venue_id>") to get the research job
        2. The tool will return search queries to execute
        3. Execute ALL search queries in PARALLEL (multiple WebSearch calls in one message)
        4. Analyze the search results and extract enrichment data
        5. Use update_venue_with_results to save the enrichment
        6. Move to next venue

        CRITICAL: For each venue, launch ALL WebSearch calls in a SINGLE message for parallel execution.

        Continue until {'first ' + str(max_venues) if max_venues else 'all'} venues are enriched.

        Report progress after every 5 venues.
        """

        await client.query(enrichment_instruction)

        # Stream progress updates
        async for message in client.receive_response():
            print(message, flush=True)

        # Step 3: Final report
        print("\n📈 Step 3: Generating final report...\n")

        await client.query(
            f"""
            Generate a final enrichment report using get_enrichment_statistics tool.

            Parameters:
            - venues_file: {venues_file}

            Show:
            1. Overall statistics (total venues, enriched count, average confidence)
            2. Before/after comparison
            3. Any venues still needing enrichment
            """
        )

        async for message in client.receive_response():
            print(message, flush=True)

    print("\n✅ Enrichment process complete!")


async def main():
    """CLI entry point for venue enrichment."""
    parser = argparse.ArgumentParser(
        description="Enrich venues using Claude Agent SDK (V2 - stateless with service layer)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enrich all venues with confidence < 0.7 (uses backend/data/venues.json by default)
  %(prog)s

  # Enrich venues from a specific file
  %(prog)s path/to/venues.json

  # Enrich first 10 venues only
  %(prog)s --max-venues 10

  # Interactive mode (ask before enriching)
  %(prog)s --interactive

  # Custom confidence threshold
  %(prog)s --min-confidence 0.8
        """,
    )

    parser.add_argument(
        "venues_file",
        type=Path,
        nargs="?",
        default=Path("backend/data/venues.json"),
        help="Path to venues.json (default: backend/data/venues.json)",
    )

    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.7,
        help="Minimum confidence threshold for enrichment (default: 0.7)",
    )

    parser.add_argument(
        "--max-venues",
        type=int,
        help="Maximum number of venues to enrich (default: all)",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Ask for confirmation before enrichment",
    )

    args = parser.parse_args()

    # Validate input file
    if not args.venues_file.exists():
        print(f"❌ Error: File not found: {args.venues_file}")
        return 1

    # Run enrichment
    try:
        await enrich_venues(
            venues_file=args.venues_file,
            min_confidence=args.min_confidence,
            max_venues=args.max_venues,
            interactive=args.interactive,
        )
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Enrichment interrupted by user.")
        print(
            "💡 Progress is saved incrementally. You can resume by running the script again."
        )
        return 1
    except Exception as e:
        print(f"\n❌ Error during enrichment: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
