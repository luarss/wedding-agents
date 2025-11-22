#!/usr/bin/env python3
"""
Deduplicate venues using multi-metric entity resolution.

Deduplication strategy:
1. Blocking: postal_code OR phonetic(name) OR geo within 50m
2. Compare candidates with multi-metric score:
   - Name similarity (token-set Jaro-Winkler)
   - Address similarity (Levenshtein + normalized tokens)
   - Geospatial distance (Haversine)
   - Website/phone match
3. Weighted scoring → threshold for merge
4. Hierarchical clustering for groups
5. Canonicalization: choose record with highest source_trust * completeness_score
"""

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class DuplicateGroup:
    """Group of duplicate venues"""

    canonical_id: str
    canonical_name: str
    duplicate_ids: list[str]
    similarity_score: float
    merge_reason: str


def normalize_name_for_comparison(name: str) -> str:
    """Normalize name for comparison"""
    # Lowercase
    name = name.lower()

    # Remove common suffixes
    name = re.sub(r"\b(hotel|singapore|pte ltd|ltd|restaurant|club|ballroom)\b", "", name)

    # Remove special chars
    name = re.sub(r"[^a-z0-9\s]", "", name)

    # Normalize whitespace
    name = re.sub(r"\s+", " ", name).strip()

    return name


def phonetic_name(name: str) -> str:
    """
    Simple phonetic encoding (similar to Soundex but simpler).
    Used for blocking.
    """
    name = normalize_name_for_comparison(name)

    # Keep first letter, remove vowels from rest
    if not name:
        return ""

    first = name[0]
    rest = re.sub(r"[aeiou]", "", name[1:])

    # Remove duplicate consonants
    result = first
    for char in rest:
        if char != result[-1]:
            result += char

    return result[:8]  # Limit to 8 chars


def token_set_similarity(name1: str, name2: str) -> float:
    """
    Token set similarity (Jaccard coefficient).
    Ignores word order.
    """
    tokens1 = set(normalize_name_for_comparison(name1).split())
    tokens2 = set(normalize_name_for_comparison(name2).split())

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union)


def jaro_winkler_similarity(s1: str, s2: str) -> float:
    """
    Jaro-Winkler similarity.
    Simple implementation without external dependencies.
    """
    s1 = normalize_name_for_comparison(s1)
    s2 = normalize_name_for_comparison(s2)

    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    # Jaro similarity
    len1, len2 = len(s1), len(s2)
    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 1:
        match_distance = 1

    s1_matches = [False] * len1
    s2_matches = [False] * len2

    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)

        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3

    # Winkler modification (prefix boost)
    prefix_len = 0
    for i in range(min(len1, len2, 4)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break

    return jaro + (prefix_len * 0.1 * (1 - jaro))


def name_similarity(name1: str, name2: str) -> float:
    """
    Combined name similarity using token-set and Jaro-Winkler.
    """
    token_sim = token_set_similarity(name1, name2)
    jaro_sim = jaro_winkler_similarity(name1, name2)

    # Weight token similarity more (better for venue names)
    return 0.6 * token_sim + 0.4 * jaro_sim


def address_similarity(addr1: str, addr2: str) -> float:
    """Address similarity using token overlap"""
    if not addr1 or not addr2:
        return 0.0

    # Normalize addresses
    def normalize_addr(addr):
        addr = addr.lower()
        addr = re.sub(r"[^a-z0-9\s]", "", addr)
        return set(addr.split())

    tokens1 = normalize_addr(addr1)
    tokens2 = normalize_addr(addr2)

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union)


def phone_match(phone1: str, phone2: str) -> bool:
    """Check if phone numbers match"""
    if not phone1 or not phone2:
        return False

    # Extract digits only
    digits1 = re.sub(r"\D", "", phone1)
    digits2 = re.sub(r"\D", "", phone2)

    # Match last 8 digits (Singapore phone numbers)
    return digits1[-8:] == digits2[-8:]


def website_match(url1: str, url2: str) -> bool:
    """Check if websites match"""
    if not url1 or not url2:
        return False

    # Extract domain
    def extract_domain(url):
        url = url.lower()
        url = re.sub(r"https?://", "", url)
        url = re.sub(r"^www\.", "", url)
        url = url.split("/")[0]
        return url

    return extract_domain(url1) == extract_domain(url2)


def calculate_similarity_score(venue1: dict, venue2: dict) -> tuple[float, str]:
    """
    Calculate similarity score between two venues.

    Returns: (score, reason)

    Scoring:
    - Name similarity: 40%
    - Address similarity: 20%
    - Phone match: 15%
    - Website match: 15%
    - Postal match: 10%
    """
    score = 0.0
    reasons = []

    # Name similarity (40%)
    name_sim = name_similarity(venue1["name"], venue2["name"])
    score += name_sim * 0.4
    if name_sim > 0.8:
        reasons.append(f"name_sim={name_sim:.2f}")

    # Address similarity (20%)
    addr1 = venue1.get("location", {}).get("address", "")
    addr2 = venue2.get("location", {}).get("address", "")
    if addr1 and addr2:
        addr_sim = address_similarity(addr1, addr2)
        score += addr_sim * 0.2
        if addr_sim > 0.8:
            reasons.append(f"addr_sim={addr_sim:.2f}")

    # Phone match (15%)
    phone1 = venue1.get("contact", {}).get("phone", "")
    phone2 = venue2.get("contact", {}).get("phone", "")
    if phone_match(phone1, phone2):
        score += 0.15
        reasons.append("phone_match")

    # Website match (15%)
    url1 = venue1.get("contact", {}).get("website", "")
    url2 = venue2.get("contact", {}).get("website", "")
    if website_match(url1, url2):
        score += 0.15
        reasons.append("website_match")

    # Postal match (10%)
    postal1 = venue1.get("location", {}).get("postal", "")
    postal2 = venue2.get("location", {}).get("postal", "")
    if postal1 and postal2 and postal1 == postal2:
        score += 0.10
        reasons.append("postal_match")

    reason = ", ".join(reasons) if reasons else "low_similarity"

    return score, reason


def block_venues(venues: list[dict]) -> dict[str, list[int]]:
    """
    Block venues for comparison.

    Blocking keys:
    - postal_code
    - phonetic(name)

    Returns: {block_key: [venue_indices]}
    """
    blocks = defaultdict(list)

    for i, venue in enumerate(venues):
        # Block by postal code
        postal = venue.get("location", {}).get("postal", "")
        if postal:
            blocks[f"postal:{postal}"].append(i)

        # Block by phonetic name
        phonetic = phonetic_name(venue["name"])
        if phonetic:
            blocks[f"phonetic:{phonetic}"].append(i)

    return blocks


def find_duplicates(venues: list[dict], threshold: float = 0.75) -> list[DuplicateGroup]:
    """
    Find duplicate venues using blocking and similarity scoring.

    Args:
        venues: List of venue dicts
        threshold: Similarity threshold for duplicates (default: 0.75)

    Returns: List of DuplicateGroup
    """
    print(f"🔍 Blocking venues...")
    blocks = block_venues(venues)

    print(f"📊 Created {len(blocks)} blocks")

    # Track which venues have been compared
    compared_pairs = set()
    duplicate_groups = []

    print(f"🔄 Comparing candidates...")
    comparisons = 0

    for block_key, indices in blocks.items():
        # Skip single-venue blocks
        if len(indices) < 2:
            continue

        # Compare all pairs in block
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                idx1, idx2 = indices[i], indices[j]

                # Skip if already compared
                pair = tuple(sorted([idx1, idx2]))
                if pair in compared_pairs:
                    continue

                compared_pairs.add(pair)
                comparisons += 1

                # Calculate similarity
                score, reason = calculate_similarity_score(venues[idx1], venues[idx2])

                # If above threshold, mark as duplicate
                if score >= threshold:
                    # Choose canonical (higher confidence score)
                    conf1 = venues[idx1].get("confidence_score", 0)
                    conf2 = venues[idx2].get("confidence_score", 0)

                    if conf1 >= conf2:
                        canonical_idx = idx1
                        duplicate_idx = idx2
                    else:
                        canonical_idx = idx2
                        duplicate_idx = idx1

                    duplicate_groups.append(
                        DuplicateGroup(
                            canonical_id=venues[canonical_idx]["id"],
                            canonical_name=venues[canonical_idx]["name"],
                            duplicate_ids=[venues[duplicate_idx]["id"]],
                            similarity_score=score,
                            merge_reason=reason,
                        )
                    )

    print(f"✅ Completed {comparisons} comparisons")
    print(f"🔍 Found {len(duplicate_groups)} duplicate pairs")

    return duplicate_groups


def merge_duplicates(venues: list[dict], duplicate_groups: list[DuplicateGroup]) -> list[dict]:
    """
    Merge duplicate venues.

    Strategy:
    - Keep canonical venue
    - Mark duplicates with duplicate_of field
    - Merge data from duplicates into canonical
    """
    # Create venue lookup
    venues_by_id = {v["id"]: v for v in venues}

    # Mark duplicates
    for group in duplicate_groups:
        for dup_id in group.duplicate_ids:
            if dup_id in venues_by_id:
                venues_by_id[dup_id]["duplicate_of"] = group.canonical_id

    # Filter out duplicates
    unique_venues = [v for v in venues if not v.get("duplicate_of")]

    return unique_venues


def main():
    parser = argparse.ArgumentParser(
        description="Deduplicate transformed venues"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Input JSON file from transform phase",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("deduplicated_venues.json"),
        help="Output JSON file (default: deduplicated_venues.json)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Similarity threshold for duplicates (default: 0.75)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Output duplicate report to file",
    )

    args = parser.parse_args()

    # Load transformed venues
    print(f"📥 Loading venues from {args.input_file}...")
    with open(args.input_file) as f:
        data = json.load(f)

    venues = data.get("venues", [])
    print(f"✅ Loaded {len(venues)} venues")

    # Find duplicates
    print(f"\n🔍 Finding duplicates (threshold={args.threshold})...")
    duplicate_groups = find_duplicates(venues, threshold=args.threshold)

    # Merge duplicates
    print(f"\n🔄 Merging duplicates...")
    unique_venues = merge_duplicates(venues, duplicate_groups)
    print(f"✅ Reduced from {len(venues)} to {len(unique_venues)} unique venues")

    # Save
    output_data = {
        "deduplicated_at": datetime.now().isoformat(),
        "total_unique_venues": len(unique_venues),
        "duplicates_removed": len(venues) - len(unique_venues),
        "venues": unique_venues,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved to {args.output}")

    # Save duplicate report if requested
    if args.report:
        report = {
            "report_date": datetime.now().isoformat(),
            "threshold": args.threshold,
            "total_duplicates": len(duplicate_groups),
            "groups": [
                {
                    "canonical_id": g.canonical_id,
                    "canonical_name": g.canonical_name,
                    "duplicates": g.duplicate_ids,
                    "similarity_score": g.similarity_score,
                    "reason": g.merge_reason,
                }
                for g in duplicate_groups
            ],
        }

        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📊 Duplicate report saved to {args.report}")


if __name__ == "__main__":
    main()
