#!/usr/bin/env python3
"""
Venue enrichment tool for Claude Agent SDK.

Provides MCP tools for coordinating parallel web searches to enrich venue data.
This tool orchestrates the Stage 2B enrichment process from the ETL pipeline.
"""

import json
from pathlib import Path
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool


@tool(
    name="get_venues_needing_enrichment",
    description="""
    Identify venues that need enrichment based on confidence score and missing fields.
    Returns a list of venues with confidence < 0.7 or missing critical fields.
    """,
    input_schema={
        "transformed_file": {
            "type": "string",
            "description": "Path to transformed.json file from Stage 2A",
        },
        "min_confidence": {
            "type": "number",
            "description": "Minimum confidence threshold (default: 0.7)",
        },
    },
)
async def get_venues_needing_enrichment(args: dict[str, Any]) -> dict[str, Any]:
    """
    Identify venues needing enrichment.

    Returns venues with low confidence scores or missing critical fields.
    """
    transformed_file = Path(args["transformed_file"])
    min_confidence = float(args.get("min_confidence", 0.7))

    if not transformed_file.exists():
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error: File not found: {transformed_file}",
                }
            ]
        }

    try:
        # Load transformed venues
        with open(transformed_file, encoding='utf-8') as f:
            data = json.load(f)

        # Handle both {"venues": [...]} and direct array formats
        if isinstance(data, dict):
            venues = data.get("venues", [])
        elif isinstance(data, list):
            venues = data
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Error: Unexpected data format. Expected dict or list, got {type(data)}",
                    }
                ]
            }

        # Calculate confidence scores and filter venues needing enrichment
        needs_enrichment = []
        for v in venues:
            # Skip if not a dict (defensive programming)
            if not isinstance(v, dict):
                continue

            # Calculate confidence score if not present
            if "confidence_score" not in v:
                v["confidence_score"] = _calculate_confidence_score(v)

            # Check if enrichment is needed
            if v["confidence_score"] < min_confidence or v.get("needs_review", []):
                needs_enrichment.append(v)
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error processing file: {str(e)}",
                }
            ]
        }

    # Build summary
    summary = {
        "total_venues": len(venues),
        "needs_enrichment": len(needs_enrichment),
        "percentage": round((len(needs_enrichment) / len(venues) * 100), 1)
        if venues
        else 0,
        "venues": [
            {
                "id": v.get("id"),
                "name": v.get("name"),
                "confidence_score": v.get("confidence_score", 0),
                "needs_review": v.get("needs_review", []),
                "missing_fields": _identify_missing_fields(v),
            }
            for v in needs_enrichment[:50]  # Limit to first 50
        ],
    }

    return {
        "content": [
            {
                "type": "text",
                "text": f"""🔍 Enrichment Analysis

**Summary:**
- Total venues: {summary['total_venues']}
- Need enrichment: {summary['needs_enrichment']} ({summary['percentage']}%)

**Top venues needing enrichment:**

{chr(10).join([
    f"  • {v['name']} (confidence: {v['confidence_score']:.2f})"
    f"    Missing: {', '.join(v['missing_fields'][:5])}"
    for v in summary['venues'][:10]
])}

**Full data:**
```json
{json.dumps(summary, indent=2)}
```

**Next step:** Use `enrich_single_venue` to enrich each venue with parallel web searches.
""",
            }
        ]
    }


@tool(
    name="generate_enrichment_queries",
    description="""
    Generate 6 parallel web search queries for a specific venue.
    Returns optimized search queries for: pricing, contact, capacity, amenities, reviews, and MRT location.
    """,
    input_schema={
        "venue_name": {
            "type": "string",
            "description": "Name of the venue to enrich",
        },
        "missing_fields": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of missing field categories (e.g., 'pricing', 'contact')",
        },
    },
)
async def generate_enrichment_queries(args: dict[str, Any]) -> dict[str, Any]:
    """
    Generate optimized parallel search queries for a venue.

    Returns 6 queries designed to be executed in parallel via WebSearch.
    """
    venue_name = args["venue_name"]
    missing_fields = args.get("missing_fields", [])

    # Parse JSON string to list if needed (MCP passes arrays as strings sometimes)
    if isinstance(missing_fields, str):
        try:
            missing_fields = json.loads(missing_fields) if missing_fields else []
        except (json.JSONDecodeError, TypeError):
            # If it's a simple comma-separated string, split it
            missing_fields = [f.strip() for f in missing_fields.split(",")] if missing_fields else []

    # Map field names to query categories
    field_to_category = {
        "price_per_table": "pricing",
        "min_spend": "pricing",
        "pricing_type": "pricing",
        "phone": "contact",
        "email": "contact",
        "address": "contact",
        "postal": "contact",
        "max_capacity": "capacity",
        "min_tables": "capacity",
        "comfortable_capacity": "capacity",
        "av_equipment": "amenities",
        "bridal_suite": "amenities",
        "outdoor_area": "amenities",
        "parking_lots": "amenities",
        "nearest_mrt": "location",
        "mrt_distance": "location",
        "mrt_lines": "location",
    }

    # Build targeted queries based on missing fields
    queries = {
        "pricing": f'"{venue_name}" Singapore wedding ballroom pricing per table 2024 2025',
        "contact": f'"{venue_name}" Singapore contact phone email address postal code',
        "capacity": f'"{venue_name}" Singapore wedding capacity guest count minimum maximum',
        "amenities": f'"{venue_name}" Singapore wedding packages amenities bridal suite features',
        "reviews": f'"{venue_name}" Singapore wedding reviews rating testimonials',
        "location": f'"{venue_name}" Singapore MRT location nearest station distance',
    }

    # Filter to only missing fields if specified
    if missing_fields:
        # Convert field names to categories
        categories_needed = set()
        for field in missing_fields:
            category = field_to_category.get(field)
            if category:
                categories_needed.add(category)

        if categories_needed:
            queries = {k: v for k, v in queries.items() if k in categories_needed}

    return {
        "content": [
            {
                "type": "text",
                "text": f"""⚡ Parallel Search Queries for "{venue_name}"

**CRITICAL: Execute ALL queries in PARALLEL using a SINGLE message with multiple WebSearch tool calls.**

**Queries to execute:**
{chr(10).join([f'{i+1}. {category.upper()}: {query}' for i, (category, query) in enumerate(queries.items())])}

**Instructions:**
1. Launch {len(queries)} WebSearch calls in a SINGLE message (parallel execution)
2. Wait for ALL results before consolidating
3. Cross-validate data from multiple sources
4. Prefer official venue websites and trusted wedding directories
5. Use `consolidate_enrichment_results` tool after receiving all search results

**Queries JSON:**
```json
{json.dumps(queries, indent=2)}
```
""",
            }
        ]
    }


@tool(
    name="consolidate_enrichment_results",
    description="""
    Consolidate web search results into structured venue enrichment data.
    Takes raw search results and extracts relevant venue information.
    """,
    input_schema={
        "venue_id": {
            "type": "string",
            "description": "ID of the venue being enriched",
        },
        "search_results": {
            "type": "object",
            "description": "Map of search category to results (e.g., {'pricing': '...', 'contact': '...'})",
        },
    },
)
async def consolidate_enrichment_results(args: dict[str, Any]) -> dict[str, Any]:
    """
    Consolidate search results into structured enrichment data.

    Returns structured data ready to merge into venue record.
    """
    venue_id = args["venue_id"]
    search_results = args.get("search_results", {})

    # Parse JSON string to dict if needed (MCP passes objects as strings)
    if isinstance(search_results, str):
        try:
            search_results = json.loads(search_results)
        except (json.JSONDecodeError, TypeError):
            search_results = {}

    # This tool provides guidance for LLM to structure the enrichment
    # The actual extraction is done by the LLM analyzing the search results

    return {
        "content": [
            {
                "type": "text",
                "text": f"""📊 Consolidation Instructions for Venue ID: {venue_id}

**Search results received:**
{chr(10).join([f'- {category}: {len(str(results))} chars' for category, results in search_results.items()])}

**Extraction guidelines:**

**1. PRICING** (from pricing search results):
   Extract:
   - price_per_table (int): Base price per table
   - weekday_price (int): Weekday price if available
   - weekend_price (int): Weekend price if available
   - pricing_type (str): "plus_plus" or "nett"
   - min_spend (int): Minimum spending requirement

**2. CONTACT** (from contact search results):
   Extract:
   - phone (str): Format as "+65 XXXX XXXX"
   - email (str): Venue email address
   - website (str): Official website URL

**3. LOCATION** (from contact + location results):
   Extract:
   - address (str): Full address
   - postal (str): 6-digit postal code
   - zone (str): Infer from postal (01-28,78→Central, 29-48→East, 49-55,79-80→North, 60-77→West)
   - nearest_mrt (str): Nearest MRT station name
   - mrt_distance (str): Walking distance/time

**4. CAPACITY** (from capacity search results):
   Extract:
   - max_capacity (int): Maximum guests
   - min_tables (int): Minimum tables required
   - max_rounds (int): Maximum tables (usually max_capacity / 10)

**5. AMENITIES** (from amenities search results):
   Extract boolean flags:
   - bridal_suite, av_equipment, in_house_catering, outdoor_area, air_conditioning, valet_parking

**6. REVIEWS** (from reviews search results):
   Extract:
   - rating (float): 0.0-5.0 rating
   - review_count (int): Number of reviews
   - description (str): Brief description of venue

**Validation rules:**
- ✅ Only use data from official sources or trusted wedding directories
- ✅ Mark year/date of pricing found
- ✅ Leave field empty if no reliable data found
- ❌ Never fabricate data
- ❌ Don't use outdated pricing (>2 years old)

**Output format:**
After analyzing the search results, use the `update_venue_data` tool to apply enrichments.
""",
            }
        ]
    }


@tool(
    name="update_venue_data",
    description="""
    Update a venue in transformed.json with enriched data.
    Merges enrichment data into existing venue record and updates confidence score.
    """,
    input_schema={
        "transformed_file": {
            "type": "string",
            "description": "Path to transformed.json file",
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
async def update_venue_data(args: dict[str, Any]) -> dict[str, Any]:
    """
    Update venue with enriched data and recalculate confidence score.
    """
    transformed_file = Path(args["transformed_file"])
    venue_id = args["venue_id"]
    enrichment_data = args.get("enrichment_data", {})

    # Parse JSON string to dict if needed (MCP passes objects as strings)
    if isinstance(enrichment_data, str):
        try:
            enrichment_data = json.loads(enrichment_data)
        except (json.JSONDecodeError, TypeError):
            enrichment_data = {}

    if not transformed_file.exists():
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error: File not found: {transformed_file}",
                }
            ]
        }

    # Load transformed venues
    with open(transformed_file) as f:
        data = json.load(f)

    venues = data.get("venues", [])

    # Find venue to update
    venue_index = None
    for i, v in enumerate(venues):
        if v.get("id") == venue_id:
            venue_index = i
            break

    if venue_index is None:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error: Venue not found: {venue_id}",
                }
            ]
        }

    # Merge enrichment data
    venue = venues[venue_index]
    old_confidence = venue.get("confidence_score", 0)

    # Deep merge enrichment data
    _deep_merge(venue, enrichment_data)

    # Recalculate confidence score
    new_confidence = _calculate_confidence_score(venue)
    venue["confidence_score"] = new_confidence

    # Clear needs_review if confidence improved significantly
    if new_confidence > 0.7:
        venue["needs_review"] = []

    # Update timestamp
    from datetime import datetime

    venue["last_updated"] = datetime.now().isoformat()

    # Save updated data
    data["venues"][venue_index] = venue

    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {
        "content": [
            {
                "type": "text",
                "text": f"""✅ Updated venue: {venue.get('name')}

**Enrichment summary:**
- Venue ID: {venue_id}
- Confidence: {old_confidence:.2f} → {new_confidence:.2f} ({'+' if new_confidence > old_confidence else ''}{new_confidence - old_confidence:.2f})
- Fields updated: {len(enrichment_data)}

**Updated fields:**
{chr(10).join([f'- {k}: {_summarize_value(v)}' for k, v in enrichment_data.items()])}

**File saved:** {transformed_file}
""",
            }
        ]
    }


# Helper functions


def _identify_missing_fields(venue: dict) -> list[str]:
    """Identify missing critical/high-priority fields in a venue."""
    missing = []

    # Helper to safely get nested dict
    def safe_get_dict(obj: dict, key: str) -> dict:
        val = obj.get(key, {})
        return val if isinstance(val, dict) else {}

    # Check critical fields
    pricing = safe_get_dict(venue, "pricing")
    if not pricing.get("pricing_type"):
        missing.append("pricing_type")
    if not pricing.get("price_per_table"):
        missing.append("price_per_table")

    capacity = safe_get_dict(venue, "capacity")
    if not capacity.get("max_capacity"):
        missing.append("max_capacity")

    # Check high-priority fields
    location = safe_get_dict(venue, "location")
    if not location.get("zone"):
        missing.append("zone")
    if not location.get("address"):
        missing.append("address")

    contact = safe_get_dict(venue, "contact")
    if not contact.get("phone"):
        missing.append("phone")
    if not contact.get("email"):
        missing.append("email")

    return missing


def _deep_merge(target: dict, source: dict):
    """Deep merge source dict into target dict."""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


def _calculate_confidence_score(venue: dict) -> float:
    """
    Calculate confidence score based on field completeness.

    Scoring:
    - Critical fields: 40% weight
    - High priority fields: 30% weight
    - Medium priority fields: 20% weight
    - Low priority fields: 10% weight
    """
    score = 0.0

    # Critical fields (40%)
    critical_fields = [
        "name",
        "venue_type",
        "pricing.price_per_table",
        "pricing.pricing_type",
        "capacity.max_capacity",
    ]
    critical_filled = sum(1 for f in critical_fields if _has_field(venue, f))
    score += (critical_filled / len(critical_fields)) * 0.4

    # High priority fields (30%)
    high_fields = [
        "location.address",
        "location.zone",
        "pricing.min_spend",
        "contact.phone",
        "contact.email",
    ]
    high_filled = sum(1 for f in high_fields if _has_field(venue, f))
    score += (high_filled / len(high_fields)) * 0.3

    # Medium priority fields (20%)
    medium_fields = [
        "location.nearest_mrt",
        "amenities.bridal_suite",
        "description",
        "rating",
    ]
    medium_filled = sum(1 for f in medium_fields if _has_field(venue, f))
    score += (medium_filled / len(medium_fields)) * 0.2

    # Low priority fields (10%)
    low_fields = ["restrictions.outside_catering", "contact.website"]
    low_filled = sum(1 for f in low_fields if _has_field(venue, f))
    score += (low_filled / len(low_fields)) * 0.1

    return round(score, 2)


def _has_field(obj: dict, field_path: str) -> bool:
    """Check if nested field exists and is non-empty."""
    parts = field_path.split(".")
    current = obj

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False

    return bool(current) and current != "" and current != [] and current != {}


def _summarize_value(value: Any) -> str:
    """Summarize a value for display."""
    if isinstance(value, dict):
        return f"dict with {len(value)} keys"
    elif isinstance(value, list):
        return f"list with {len(value)} items"
    elif isinstance(value, str) and len(value) > 50:
        return f"{value[:50]}..."
    else:
        return str(value)


# Create MCP server with all enrichment tools
def create_enrichment_server():
    """Create MCP server for venue enrichment tools."""
    return create_sdk_mcp_server(
        name="venue_enrichment",
        tools=[
            get_venues_needing_enrichment,
            generate_enrichment_queries,
            consolidate_enrichment_results,
            update_venue_data,
        ],
    )
