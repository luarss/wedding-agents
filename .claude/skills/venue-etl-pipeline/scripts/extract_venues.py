#!/usr/bin/env python3
"""
Extract venues from various wedding data sources.
Source enumeration: seed list from wedding-data from all sources.
Populate data that you know, do not make things up.
"""

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class VenueExtract:
    """Extracted venue data before transformation"""

    name: str
    source: str
    extracted_at: str

    # Raw extracted fields (may need transformation)
    raw_price: str = ""
    raw_capacity: str = ""
    raw_address: str = ""
    raw_location: str = ""
    raw_rating: str = ""
    raw_reviews: str = ""
    raw_phone: str = ""
    raw_email: str = ""
    raw_website: str = ""

    # Additional metadata
    source_url: str = ""
    notes: str = ""


def extract_from_csv(csv_path: Path, source: str) -> list[VenueExtract]:
    """
    Extract venues from CSV file (Bridely, BlissfulBrides, TheKnot, etc.)

    Automatically detects CSV column names and maps to VenueExtract fields.
    Common column mappings:
    - name, venue_name, venue -> name
    - price, pricing, cost -> raw_price
    - capacity, pax, guests -> raw_capacity
    - address, location -> raw_address
    - rating, stars -> raw_rating
    - reviews, review_count -> raw_reviews
    """
    venues = []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Auto-detect column mappings
        columns = reader.fieldnames or []
        col_map = _auto_map_columns(columns)

        for row in reader:
            name = _get_mapped_value(row, col_map, "name")
            if not name or name.strip() == "":
                continue

            venue = VenueExtract(
                name=name.strip(),
                source=source,
                extracted_at=datetime.now().isoformat(),
                raw_price=_get_mapped_value(row, col_map, "price"),
                raw_capacity=_get_mapped_value(row, col_map, "capacity"),
                raw_address=_get_mapped_value(row, col_map, "address"),
                raw_location=_get_mapped_value(row, col_map, "location"),
                raw_rating=_get_mapped_value(row, col_map, "rating"),
                raw_reviews=_get_mapped_value(row, col_map, "reviews"),
                raw_phone=_get_mapped_value(row, col_map, "phone"),
                raw_email=_get_mapped_value(row, col_map, "email"),
                raw_website=_get_mapped_value(row, col_map, "website"),
                source_url=_get_mapped_value(row, col_map, "url"),
            )

            venues.append(venue)

    return venues


def _auto_map_columns(columns: list[str]) -> dict[str, str]:
    """Auto-detect CSV column mappings"""
    col_map = {}

    name_patterns = ["name", "venue_name", "venue", "property"]
    price_patterns = ["price", "pricing", "cost", "rate", "package"]
    capacity_patterns = ["capacity", "pax", "guests", "seating", "size"]
    address_patterns = ["address", "location", "street", "postal"]
    rating_patterns = ["rating", "stars", "score", "venuerating"]
    review_patterns = ["reviews", "review_count", "testimonials"]
    phone_patterns = ["phone", "tel", "telephone", "contact", "mobile"]
    email_patterns = ["email", "mail", "contact_email"]
    website_patterns = ["website", "url", "web", "link", "site"]

    for col in columns:
        col_lower = col.lower().strip()

        if any(p in col_lower for p in name_patterns):
            col_map["name"] = col
        elif any(p in col_lower for p in price_patterns):
            col_map["price"] = col
        elif any(p in col_lower for p in capacity_patterns):
            col_map["capacity"] = col
        elif any(p in col_lower for p in address_patterns):
            if "location" in col_lower and "address" not in col_map:
                col_map["location"] = col
            else:
                col_map["address"] = col
        elif any(p in col_lower for p in rating_patterns):
            col_map["rating"] = col
        elif any(p in col_lower for p in review_patterns):
            col_map["reviews"] = col
        elif any(p in col_lower for p in phone_patterns):
            col_map["phone"] = col
        elif any(p in col_lower for p in email_patterns):
            col_map["email"] = col
        elif any(p in col_lower for p in website_patterns):
            col_map["website"] = col
            col_map["url"] = col

    return col_map


def _get_mapped_value(row: dict, col_map: dict, field: str) -> str:
    """Get value from row using column mapping"""
    if field in col_map and col_map[field] in row:
        return row[col_map[field]].strip()
    return ""


def extract_from_json(json_path: Path, source: str) -> list[VenueExtract]:
    """Extract venues from JSON file"""
    with open(json_path) as f:
        data = json.load(f)

    venues = []

    # Handle different JSON structures
    if isinstance(data, dict) and "venues" in data:
        items = data["venues"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data]

    for item in items:
        if not isinstance(item, dict):
            continue

        name = item.get("name") or item.get("venue_name") or item.get("title")
        if not name:
            continue

        venue = VenueExtract(
            name=str(name).strip(),
            source=source,
            extracted_at=datetime.now().isoformat(),
            raw_price=str(item.get("price") or item.get("pricing") or ""),
            raw_capacity=str(item.get("capacity") or item.get("max_capacity") or ""),
            raw_address=str(item.get("address") or item.get("location", {}).get("address") or ""),
            raw_location=str(item.get("location") or ""),
            raw_rating=str(item.get("rating") or ""),
            raw_reviews=str(item.get("reviews") or item.get("review_count") or ""),
            raw_phone=str(item.get("phone") or item.get("contact", {}).get("phone") or ""),
            raw_email=str(item.get("email") or item.get("contact", {}).get("email") or ""),
            raw_website=str(item.get("website") or item.get("url") or ""),
            source_url=str(item.get("source_url") or item.get("url") or ""),
        )

        venues.append(venue)

    return venues


def save_extracted_venues(venues: list[VenueExtract], output_path: Path):
    """Save extracted venues to JSON"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "extracted_at": datetime.now().isoformat(),
        "total_venues": len(venues),
        "sources": list(set(v.source for v in venues)),
        "venues": [asdict(v) for v in venues],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Extract venues from wedding data sources"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Input file (CSV or JSON)",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Data source name (e.g., 'Bridely', 'BlissfulBrides', 'TheKnot')",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("extracted_venues.json"),
        help="Output JSON file (default: extracted_venues.json)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "auto"],
        default="auto",
        help="Input format (default: auto-detect)",
    )

    args = parser.parse_args()

    # Auto-detect format
    if args.format == "auto":
        if args.input_file.suffix.lower() == ".csv":
            args.format = "csv"
        elif args.input_file.suffix.lower() == ".json":
            args.format = "json"
        else:
            print(f"❌ Could not auto-detect format for {args.input_file}")
            return

    # Extract venues
    print(f"📥 Extracting venues from {args.input_file} ({args.source})...")

    if args.format == "csv":
        venues = extract_from_csv(args.input_file, args.source)
    elif args.format == "json":
        venues = extract_from_json(args.input_file, args.source)
    else:
        print(f"❌ Unsupported format: {args.format}")
        return

    print(f"✅ Extracted {len(venues)} venues")

    # Save
    save_extracted_venues(venues, args.output)
    print(f"💾 Saved to {args.output}")

    # Print summary
    print("\n📊 Summary by source:")
    from collections import Counter
    sources = Counter(v.source for v in venues)
    for source, count in sources.most_common():
        print(f"  {source}: {count} venues")


if __name__ == "__main__":
    main()
