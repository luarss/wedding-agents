#!/usr/bin/env python3
"""
Load deduplicated venues into venues.json.

Load phase:
1. Validate against schema
2. Merge with existing venues (preserve manual edits)
3. Create backup
4. Update venues.json
5. Generate completeness report
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


# Validation rules (from venue_schema.py)
VALIDATION_RULES = {
    "pricing.price_per_table": {"min": 500, "max": 5000, "message": "Price per table should be S$500-5000"},
    "pricing.min_tables": {"min": 1, "max": 200, "message": "Min tables should be 1-200"},
    "capacity.max_capacity": {"min": 10, "max": 2000, "message": "Max capacity should be 10-2000 guests"},
    "rating": {"min": 0.0, "max": 5.0, "message": "Rating should be 0-5"},
    "location.zone": {
        "enum": ["Central", "East", "West", "North"],
        "message": "Zone must be Central, East, West, or North",
    },
    "pricing.pricing_type": {"enum": ["plus_plus", "nett"], "message": "Pricing type must be plus_plus or nett"},
    "venue_type": {
        "enum": ["hotel", "restaurant", "banquet_hall", "club", "unique"],
        "message": "Venue type must be hotel, restaurant, banquet_hall, club, or unique",
    },
}

# Field priorities (from venue_schema.py)
CRITICAL_FIELDS = [
    "id",
    "name",
    "venue_type",
    "pricing.price_per_table",
    "pricing.min_spend",
    "pricing.pricing_type",
    "capacity.max_capacity",
    "capacity.min_tables",
]

HIGH_PRIORITY_FIELDS = [
    "location.address",
    "location.zone",
    "pricing.weekday_price",
    "pricing.weekend_price",
    "contact.phone",
    "contact.email",
]


def get_nested_value(obj: dict, path: str) -> Any:
    """Get nested dictionary value using dot notation"""
    parts = path.split(".")
    current = obj

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def validate_venue(venue: dict) -> list[str]:
    """
    Validate venue against schema rules.

    Returns: List of validation errors (empty if valid)
    """
    errors = []

    # Check required fields
    if not venue.get("id"):
        errors.append("Missing required field: id")
    if not venue.get("name"):
        errors.append("Missing required field: name")

    # Validate against rules
    for field_path, rules in VALIDATION_RULES.items():
        value = get_nested_value(venue, field_path)

        if value is None:
            continue  # Skip validation for missing optional fields

        # Enum validation
        if "enum" in rules and value not in rules["enum"]:
            errors.append(f"{field_path}: {rules['message']} (got: {value})")

        # Range validation
        if "min" in rules and isinstance(value, (int, float)) and value < rules["min"]:
            errors.append(f"{field_path}: {rules['message']} (got: {value})")

        if "max" in rules and isinstance(value, (int, float)) and value > rules["max"]:
            errors.append(f"{field_path}: {rules['message']} (got: {value})")

    return errors


def calculate_completeness(venues: list[dict]) -> dict:
    """Calculate field completeness statistics"""

    def count_filled(field_path: str) -> int:
        count = 0
        for venue in venues:
            value = get_nested_value(venue, field_path)
            if value is not None and value != "" and value != []:
                count += 1
        return count

    total = len(venues)

    critical_stats = {}
    for field in CRITICAL_FIELDS:
        filled = count_filled(field)
        critical_stats[field] = {
            "filled": filled,
            "total": total,
            "percentage": round((filled / total * 100), 1) if total > 0 else 0,
        }

    high_priority_stats = {}
    for field in HIGH_PRIORITY_FIELDS:
        filled = count_filled(field)
        high_priority_stats[field] = {
            "filled": filled,
            "total": total,
            "percentage": round((filled / total * 100), 1) if total > 0 else 0,
        }

    # Overall completeness
    critical_avg = sum(s["percentage"] for s in critical_stats.values()) / len(critical_stats)
    high_priority_avg = sum(s["percentage"] for s in high_priority_stats.values()) / len(high_priority_stats)

    return {
        "total_venues": total,
        "critical_fields": critical_stats,
        "high_priority_fields": high_priority_stats,
        "critical_avg": round(critical_avg, 1),
        "high_priority_avg": round(high_priority_avg, 1),
    }


def merge_with_existing(new_venues: list[dict], existing_venues: list[dict]) -> list[dict]:
    """
    Merge new venues with existing ones.

    Strategy:
    - For existing venues (matched by ID), prefer existing data (manual edits preserved)
    - Only fill missing fields from new data
    - Add completely new venues
    """
    existing_by_id = {v["id"]: v for v in existing_venues}
    merged = []

    # Process existing venues
    for existing in existing_venues:
        venue_id = existing["id"]

        # Find matching new venue
        new_venue = next((v for v in new_venues if v["id"] == venue_id), None)

        if new_venue:
            # Merge: prefer existing data, fill missing fields from new data
            merged_venue = merge_venue_data(existing, new_venue)
        else:
            # Keep existing venue as-is
            merged_venue = existing

        merged.append(merged_venue)

    # Add new venues not in existing
    existing_ids = set(v["id"] for v in existing_venues)
    for new_venue in new_venues:
        if new_venue["id"] not in existing_ids:
            merged.append(new_venue)

    return merged


def merge_venue_data(existing: dict, new: dict) -> dict:
    """
    Merge data from two venue records.

    Strategy:
    - Prefer existing values (manual edits)
    - Fill missing fields from new data
    - Update last_updated timestamp
    """
    merged = existing.copy()

    # Recursively merge nested dicts
    def merge_dict(target: dict, source: dict):
        for key, value in source.items():
            if key not in target or target[key] == "" or target[key] == [] or target[key] == {}:
                # Missing or empty in target, use source value
                target[key] = value
            elif isinstance(value, dict) and isinstance(target[key], dict):
                # Both are dicts, merge recursively
                merge_dict(target[key], value)
            # Otherwise keep existing value

    merge_dict(merged, new)

    # Update last_updated
    merged["last_updated"] = datetime.now().isoformat()

    return merged


def create_backup(venues_file: Path, backup_dir: Path):
    """Create backup of venues.json"""
    if not venues_file.exists():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"venues_backup_{timestamp}.json"

    shutil.copy2(venues_file, backup_file)

    return backup_file


def main():
    parser = argparse.ArgumentParser(
        description="Load deduplicated venues into venues.json"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Input JSON file from deduplicate phase",
    )
    parser.add_argument(
        "--venues-file",
        type=Path,
        default=Path("backend/data/venues.json"),
        help="Target venues.json file (default: backend/data/venues.json)",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing venues (preserves manual edits)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate, don't save",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Output completeness report to file",
    )

    args = parser.parse_args()

    # Load new venues
    print(f"📥 Loading venues from {args.input_file}...")
    with open(args.input_file) as f:
        data = json.load(f)

    new_venues = data.get("venues", [])
    print(f"✅ Loaded {len(new_venues)} venues")

    # Validate venues
    print(f"\n🔍 Validating venues...")
    all_errors = []
    for i, venue in enumerate(new_venues):
        errors = validate_venue(venue)
        if errors:
            all_errors.append((i, venue["name"], errors))

    if all_errors:
        print(f"⚠️  Found {len(all_errors)} venues with validation errors:")
        for i, name, errors in all_errors[:10]:  # Show first 10
            print(f"  [{i}] {name}:")
            for error in errors:
                print(f"    - {error}")

        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more")

        if args.validate_only:
            return
    else:
        print(f"✅ All venues valid")

    # Load existing venues if merging
    final_venues = new_venues

    if args.merge and args.venues_file.exists():
        print(f"\n🔄 Merging with existing venues from {args.venues_file}...")

        with open(args.venues_file) as f:
            existing_data = json.load(f)

        existing_venues = existing_data.get("venues", [])
        print(f"  Found {len(existing_venues)} existing venues")

        final_venues = merge_with_existing(new_venues, existing_venues)
        print(f"  Merged to {len(final_venues)} total venues")

    # Calculate completeness
    print(f"\n📊 Calculating completeness...")
    completeness = calculate_completeness(final_venues)

    print(f"\n📈 Completeness Report:")
    print(f"  Total venues: {completeness['total_venues']}")
    print(f"  Critical fields: {completeness['critical_avg']}% complete")
    print(f"  High priority fields: {completeness['high_priority_avg']}% complete")

    # Show top gaps
    print(f"\n🔴 Top missing critical fields:")
    critical_sorted = sorted(
        completeness["critical_fields"].items(),
        key=lambda x: x[1]["percentage"],
    )
    for field, stats in critical_sorted[:5]:
        print(f"  {field}: {stats['percentage']}% ({stats['filled']}/{stats['total']})")

    # Save completeness report if requested
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(completeness, f, indent=2, ensure_ascii=False)
        print(f"\n📊 Completeness report saved to {args.report}")

    # Exit if validate-only
    if args.validate_only:
        print(f"\n✅ Validation complete (no changes made)")
        return

    # Create backup
    backup_dir = args.venues_file.parent / "backups"
    backup_file = create_backup(args.venues_file, backup_dir)

    if backup_file:
        print(f"\n💾 Created backup: {backup_file}")

    # Save venues.json
    print(f"\n💾 Saving to {args.venues_file}...")

    output_data = {"venues": final_venues}

    args.venues_file.parent.mkdir(parents=True, exist_ok=True)

    with open(args.venues_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(final_venues)} venues to {args.venues_file}")


if __name__ == "__main__":
    main()
