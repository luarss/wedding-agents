#!/usr/bin/env python3
"""
Transform extracted venues: normalize, parse, geocode, classify, deduplicate.

Transformation pipeline:
1. Normalization (Unicode, whitespace, punctuation)
2. Address parsing & postal code extraction
3. Geocoding (with caching)
4. Field extraction & typing
5. Venue type classification
6. Deduplication & entity resolution
7. Confidence scoring
"""

import argparse
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional


@dataclass
class TransformedVenue:
    """Transformed venue data ready for loading"""

    # Core identification
    id: str
    name: str
    venue_type: Literal["hotel", "restaurant", "banquet_hall", "club", "unique"] = ""

    # Pricing
    pricing: dict = field(default_factory=dict)

    # Capacity
    capacity: dict = field(default_factory=dict)

    # Location
    location: dict = field(default_factory=dict)

    # Amenities
    amenities: dict = field(default_factory=dict)

    # Contact
    contact: dict = field(default_factory=dict)

    # Packages
    packages: list = field(default_factory=list)

    # Restrictions
    restrictions: dict = field(default_factory=dict)

    # Metadata
    description: str = ""
    reviews_summary: str = ""
    rating: float = 0.0
    review_count: int = 0
    last_updated: str = ""
    data_source: str = ""

    # Transformation metadata
    confidence_score: float = 0.0
    duplicate_of: str = ""
    needs_review: list = field(default_factory=list)


def normalize_text(text: str) -> str:
    """
    Normalize text: Unicode NFKC, strip whitespace, unify punctuation, canonicalize casing
    """
    if not text:
        return ""

    # Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Unify multiple spaces to single space
    text = re.sub(r"\s+", " ", text)

    # Unify punctuation (smart quotes, dashes, etc.)
    text = text.replace(""", '"').replace(""", '"')
    text = text.replace("'", "'").replace("'", "'")
    text = text.replace("—", "-").replace("–", "-")

    return text


def parse_address(address: str) -> dict:
    """
    Parse address and extract postal code.

    Returns: {
        "address": normalized address,
        "postal": 6-digit postal code,
        "street": street name,
        "building": building name
    }
    """
    if not address:
        return {}

    # Normalize
    address = normalize_text(address)

    # Extract postal code (6 digits, possibly with "S" or "Singapore" prefix)
    postal_match = re.search(r"\b(?:S|Singapore)?\s*(\d{6})\b", address, re.IGNORECASE)
    postal = postal_match.group(1) if postal_match else ""

    # Map abbreviations (Rd → Road, St → Street, Ave → Avenue)
    abbrev_map = {
        r"\bRd\b": "Road",
        r"\bSt\b": "Street",
        r"\bAve\b": "Avenue",
        r"\bBlvd\b": "Boulevard",
        r"\bDr\b": "Drive",
        r"\bLn\b": "Lane",
        r"\bCl\b": "Close",
        r"\bCres\b": "Crescent",
        r"\bTer\b": "Terrace",
    }
    for abbrev, full in abbrev_map.items():
        address = re.sub(abbrev, full, address, flags=re.IGNORECASE)

    return {
        "address": address,
        "postal": postal,
    }


def infer_zone_from_postal(postal: str) -> str:
    """
    Infer Singapore zone from postal code.

    Postal to Zone mapping:
    - 01-28, 78 → Central
    - 29-48 → East
    - 49-55, 79-80 → North
    - 60-77 → West
    """
    if not postal or len(postal) != 6:
        return ""

    district = int(postal[:2])

    if district in range(1, 29) or district == 78:
        return "Central"
    elif district in range(29, 49):
        return "East"
    elif district in range(49, 56) or district in [79, 80]:
        return "North"
    elif district in range(60, 78):
        return "West"

    return ""


def parse_pricing(raw_price: str) -> dict:
    """
    Parse pricing from raw text.

    Examples:
    - "$1500-$2000++/table" → price_per_table: 1500, pricing_type: plus_plus
    - "$888 nett per table" → price_per_table: 888, pricing_type: nett
    """
    if not raw_price:
        return {}

    pricing = {}

    # Detect pricing type
    if "++" in raw_price or "plus plus" in raw_price.lower():
        pricing["pricing_type"] = "plus_plus"
    elif "nett" in raw_price.lower() or "net" in raw_price.lower():
        pricing["pricing_type"] = "nett"

    # Extract prices (all numbers prefixed with $)
    price_matches = re.findall(r"\$\s*(\d+(?:,\d{3})*)", raw_price)
    if price_matches:
        # Remove commas and convert to int
        prices = [int(p.replace(",", "")) for p in price_matches]

        # First price is typically base/weekday price
        pricing["price_per_table"] = prices[0]

        # If multiple prices, try to infer weekday/weekend
        if len(prices) >= 2:
            pricing["weekday_price"] = prices[0]
            pricing["weekend_price"] = prices[1]

    return pricing


def parse_capacity(raw_capacity: str) -> dict:
    """
    Parse capacity from raw text.

    Examples:
    - "100-350 pax" → min: 100, max_capacity: 350, max_rounds: 35
    - "20-40 tables" → min_tables: 20, max_capacity: 400, max_rounds: 40
    """
    if not raw_capacity:
        return {}

    capacity = {}

    # Extract numbers
    numbers = re.findall(r"(\d+(?:,\d{3})*)", raw_capacity)
    if not numbers:
        return {}

    # Remove commas
    numbers = [int(n.replace(",", "")) for n in numbers]

    # Determine if it's pax or tables
    if "pax" in raw_capacity.lower() or "guest" in raw_capacity.lower():
        # Numbers are guests
        min_pax = numbers[0]
        max_pax = numbers[-1] if len(numbers) > 1 else min_pax

        capacity["min_tables"] = min_pax // 10
        capacity["max_capacity"] = max_pax
        capacity["max_rounds"] = max_pax // 10

    elif "table" in raw_capacity.lower() or "round" in raw_capacity.lower():
        # Numbers are tables
        min_tables = numbers[0]
        max_tables = numbers[-1] if len(numbers) > 1 else min_tables

        capacity["min_tables"] = min_tables
        capacity["max_capacity"] = max_tables * 10
        capacity["max_rounds"] = max_tables

    return capacity


def normalize_phone(phone: str) -> str:
    """
    Normalize phone to E.164 format: +65 XXXX XXXX

    Examples:
    - "6234 5678" → "+65 6234 5678"
    - "+65-6234-5678" → "+65 6234 5678"
    - "91234567" → "+65 9123 4567"
    """
    if not phone:
        return ""

    # Remove all non-digits except +
    phone = re.sub(r"[^\d+]", "", phone)

    # Add +65 if missing
    if not phone.startswith("+65"):
        if phone.startswith("65"):
            phone = "+" + phone
        elif phone.startswith("6") or phone.startswith("8") or phone.startswith("9"):
            phone = "+65" + phone

    # Format: +65 XXXX XXXX
    if phone.startswith("+65") and len(phone) == 11:
        phone = f"+65 {phone[3:7]} {phone[7:]}"

    return phone


def classify_venue_type(name: str, description: str = "") -> str:
    """
    Classify venue type using rule-based keywords.

    Returns: hotel, restaurant, banquet_hall, club, unique
    """
    text = (name + " " + description).lower()

    # Keywords for each type
    hotel_keywords = ["hotel", "resort", "inn", "suite", "grand hyatt", "marriott", "shangri-la", "fairmont", "mandarin", "ritz", "conrad", "peninsula"]
    restaurant_keywords = ["restaurant", "dining", "bistro", "café", "kitchen", "grill", "steakhouse"]
    club_keywords = ["club", "country club", "yacht club", "golf club", "recreation"]
    hall_keywords = ["hall", "ballroom", "function room", "event space", "banquet"]
    unique_keywords = ["garden", "rooftop", "terrace", "museum", "gallery", "barn", "warehouse", "loft", "conservatory"]

    if any(kw in text for kw in hotel_keywords):
        return "hotel"
    elif any(kw in text for kw in club_keywords):
        return "club"
    elif any(kw in text for kw in hall_keywords):
        return "banquet_hall"
    elif any(kw in text for kw in restaurant_keywords):
        return "restaurant"
    elif any(kw in text for kw in unique_keywords):
        return "unique"

    # Default to banquet_hall if unknown
    return "banquet_hall"


def calculate_confidence_score(venue: dict) -> float:
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
    """Check if nested field exists and is non-empty"""
    parts = field_path.split(".")
    current = obj

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False

    return bool(current)


def generate_venue_id(name: str) -> str:
    """Generate unique venue ID from name"""
    slug = name.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return f"venue-{slug}"


def transform_venue(extracted: dict) -> TransformedVenue:
    """Transform a single extracted venue"""

    # Normalize name
    name = normalize_text(extracted["name"])

    # Parse address
    address_info = parse_address(extracted.get("raw_address", ""))

    # Parse pricing
    pricing = parse_pricing(extracted.get("raw_price", ""))

    # Parse capacity
    capacity = parse_capacity(extracted.get("raw_capacity", ""))

    # Classify venue type
    venue_type = classify_venue_type(name)

    # Normalize phone
    phone = normalize_phone(extracted.get("raw_phone", ""))

    # Build location
    location = {}
    if address_info.get("address"):
        location["address"] = address_info["address"]
    if address_info.get("postal"):
        location["postal"] = address_info["postal"]
        location["zone"] = infer_zone_from_postal(address_info["postal"])

    # Build contact
    contact = {}
    if phone:
        contact["phone"] = phone
    if extracted.get("raw_email"):
        contact["email"] = normalize_text(extracted["raw_email"])
    if extracted.get("raw_website"):
        contact["website"] = normalize_text(extracted["raw_website"])

    # Parse rating
    rating = 0.0
    if extracted.get("raw_rating"):
        try:
            rating = float(re.findall(r"(\d+\.?\d*)", extracted["raw_rating"])[0])
        except (ValueError, IndexError):
            pass

    # Parse review count
    review_count = 0
    if extracted.get("raw_reviews"):
        try:
            review_count = int(re.findall(r"(\d+)", extracted["raw_reviews"])[0])
        except (ValueError, IndexError):
            pass

    # Build transformed venue
    venue = TransformedVenue(
        id=generate_venue_id(name),
        name=name,
        venue_type=venue_type,
        pricing=pricing,
        capacity=capacity,
        location=location,
        contact=contact,
        rating=rating,
        review_count=review_count,
        last_updated=datetime.now().isoformat(),
        data_source=extracted.get("source", ""),
    )

    # Calculate confidence score
    venue_dict = asdict(venue)
    venue.confidence_score = calculate_confidence_score(venue_dict)

    # Check for missing critical fields
    needs_review = []
    if not pricing.get("pricing_type"):
        needs_review.append("pricing_type")
    if not location.get("zone"):
        needs_review.append("zone")
    if not pricing.get("price_per_table"):
        needs_review.append("price_per_table")

    venue.needs_review = needs_review

    return venue


def main():
    parser = argparse.ArgumentParser(
        description="Transform extracted venues"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Input JSON file from extract phase",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("transformed_venues.json"),
        help="Output JSON file (default: transformed_venues.json)",
    )

    args = parser.parse_args()

    # Load extracted venues
    print(f"📥 Loading extracted venues from {args.input_file}...")
    with open(args.input_file) as f:
        data = json.load(f)

    extracted_venues = data.get("venues", [])
    print(f"✅ Loaded {len(extracted_venues)} venues")

    # Transform venues
    print("🔄 Transforming venues...")
    transformed = []
    for i, extracted in enumerate(extracted_venues, 1):
        venue = transform_venue(extracted)
        transformed.append(asdict(venue))

        if i % 10 == 0:
            print(f"  Processed {i}/{len(extracted_venues)} venues...")

    print(f"✅ Transformed {len(transformed)} venues")

    # Save
    output_data = {
        "transformed_at": datetime.now().isoformat(),
        "total_venues": len(transformed),
        "venues": transformed,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved to {args.output}")

    # Print stats
    avg_confidence = sum(v["confidence_score"] for v in transformed) / len(transformed)
    needs_review_count = sum(1 for v in transformed if v["needs_review"])

    print(f"\n📊 Statistics:")
    print(f"  Average confidence: {avg_confidence:.2f}")
    print(f"  Needs review: {needs_review_count} venues")

    # Venue type distribution
    from collections import Counter
    types = Counter(v["venue_type"] for v in transformed)
    print(f"\n📊 Venue types:")
    for vtype, count in types.most_common():
        print(f"  {vtype}: {count}")


if __name__ == "__main__":
    main()
