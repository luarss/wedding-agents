#!/usr/bin/env python3
"""
Automated venue enrichment using Claude Agent SDK.

This script enriches venue data in backend/data/venues.json by using the
Claude Agent SDK to coordinate parallel web searches for missing venue information.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from backend.etl.tools.enrich_tool import create_enrichment_server


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
    Enrich venues using Claude Agent SDK with parallel web searches.

    Args:
        venues_file: Path to venues.json
        min_confidence: Minimum confidence threshold for enrichment
        max_venues: Maximum number of venues to enrich (None = all)
        interactive: Ask for confirmation before each venue enrichment
    """
    _print_verbose_message(
        "🚀 Starting venue enrichment with Claude Agent SDK\n"
        f"📂 Input file: {venues_file}\n"
        f"🎯 Target confidence: {min_confidence}\n"
        f"{'🔢 Max venues: ' + str(max_venues) if max_venues else ''}\n"
        f"🔄 Mode: {'Interactive' if interactive else 'Automated'}"
    )

    # Load system prompt
    _print_verbose_message("📝 Loading system prompt...")
    prompt_file = Path(__file__).parent / "prompts" / "enrichment_agent_prompt.md"
    with open(prompt_file) as f:
        system_prompt = f.read()
    _print_verbose_message(f"✓ Loaded system prompt from {prompt_file}")

    # Create MCP server with enrichment tools
    _print_verbose_message("🔧 Creating enrichment MCP server...")
    enrichment_server = create_enrichment_server()
    _print_verbose_message("✓ MCP server created")

    # Configure agent options
    _print_verbose_message("⚙️  Configuring agent options...")
    _print_verbose_message("🔨 Creating ClaudeAgentOptions...")
    options = ClaudeAgentOptions(
        mcp_servers={
            "venue_enrichment": enrichment_server  # enrichment_server is already the config dict
        },
        allowed_tools=[
            # Enrichment tools
            "mcp__venue_enrichment__get_venues_needing_enrichment",
            "mcp__venue_enrichment__generate_enrichment_queries",
            "mcp__venue_enrichment__consolidate_enrichment_results",
            "mcp__venue_enrichment__update_venue_data",
            # Web search
            "WebSearch",
            # File operations (for reading/writing JSON)
            "Read",
            "Write",
        ],
        system_prompt=system_prompt,
        permission_mode="default",  # Require approval for file writes
    )
    _print_verbose_message("✓ Options created successfully")

    # Create agent client
    _print_verbose_message("🔌 Connecting to Claude SDK Client...")
    async with ClaudeSDKClient(options=options) as client:
        _print_verbose_message("✓ Connected to Claude SDK Client")
        # Step 1: Identify venues needing enrichment
        print("📊 Step 1: Identifying venues needing enrichment...\n")

        await client.query(
            f"""
            Use the get_venues_needing_enrichment tool to identify venues that need enrichment.

            Parameters:
            - transformed_file: {venues_file}
            - min_confidence: {min_confidence}

            Show me the summary and list the top 10 venues needing enrichment.
            """
        )

        # Process response
        async for message in client.receive_response():
            print(message, flush=True)

        # Step 2: Enrich venues with parallel searches
        print("\n⚡ Step 2: Enriching venues with parallel web searches...\n")

        if interactive:
            response = input(
                "\nProceed with automated enrichment? This will use parallel web searches for each venue. (y/n): "
            )
            if response.lower() != "y":
                print("❌ Enrichment cancelled.")
                return

        enrichment_instruction = f"""
        Now enrich the venues identified in the previous step.

        CRITICAL INSTRUCTIONS:
        1. Process venues ONE AT A TIME
        2. For EACH venue:
           a. Use generate_enrichment_queries to get 6 search queries
           b. Launch ALL 6 WebSearch calls in a SINGLE message (parallel execution)
           c. Wait for ALL results
           d. Use consolidate_enrichment_results for extraction guidance
           e. Extract data from all search results
           f. Use update_venue_data to save enrichment
           g. Report progress
        3. Continue until {'first ' + str(max_venues) if max_venues else 'all'} venues are enriched or target confidence is reached

        Target: 80%+ high-priority field completeness
        """

        await client.query(enrichment_instruction)

        # Stream progress updates
        async for message in client.receive_response():
            print(message, flush=True)

        # Step 3: Final report
        print("\n📈 Step 3: Generating final report...\n")

        await client.query(
            f"""
            Generate a final enrichment report:
            1. Load {venues_file}
            2. Calculate completeness statistics
            3. Show before/after comparison
            4. List any venues still needing enrichment

            Use the get_venues_needing_enrichment tool to get current statistics.
            """
        )

        async for message in client.receive_response():
            print(message, flush=True)

    print("\n✅ Enrichment process complete!")


async def main():
    """CLI entry point for venue enrichment."""
    parser = argparse.ArgumentParser(
        description="Enrich venues using Claude Agent SDK with parallel web searches",
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
