---
name: location-zone-classifier
description: Automatically classify Singapore wedding venues into location zones (Central/East/West/North) based on address, postal code, or venue name. Use when the user asks to "classify venue zones", "add location zones", "fill missing zones", or needs to populate the zone field in backend/data/venues.json.
---

# Location Zone Classifier

Systematically classify Singapore wedding venues into geographical zones by intelligently using postal codes, addresses, and web search to determine the correct zone for each venue in `backend/data/venues.json`.

## Quick Start

When the user asks to classify venue zones:

1. Read `backend/data/venues.json` and identify venues missing the `location.zone` field
2. For each venue, attempt classification using this priority order:
   - **First**: Use postal code mapping (if postal code exists)
   - **Second**: Parse address for known districts/areas (if address exists)
   - **Third**: Web search for venue name + "Singapore location"
3. Update venues.json with classified zones, creating a backup first
4. Report classification statistics and any venues needing manual review

## Singapore Zone System

Singapore is divided into 4 main zones for wedding venue search:

**Central** - Downtown core, city center, Orchard area
- Districts: City Hall, Bugis, Marina Bay, Orchard, Somerset, Tiong Bahru, Outram, Clarke Quay, River Valley, Tanjong Pagar, Raffles Place
- Postal districts: 01-28, 78

**East** - East Coast and northeastern areas
- Districts: Katong, Marine Parade, Bedok, Tampines, Pasir Ris, Changi, Paya Lebar, Geylang, Eunos, Kembangan, Simei
- Postal districts: 29-48

**North** - Northern and northeastern territories
- Districts: Woodlands, Yishun, Sembawang, Admiralty, Ang Mo Kio, Bishan, Serangoon, Hougang, Punggol, Sengkang
- Postal districts: 49-55, 79-80

**West** - Western and southwestern regions
- Districts: Jurong, Clementi, Bukit Batok, Bukit Panjang, Choa Chu Kang, Tuas, Boon Lay, Pioneer, Queenstown, Commonwealth
- Postal districts: 60-77

## Classification Strategy

### Priority 1: Postal Code Mapping

Use postal code (first 2 digits) to determine zone:

```python
postal_to_zone = {
    range(1, 29): "Central",     # 01-28
    78: "Central",
    range(29, 49): "East",        # 29-48
    range(49, 56): "North",       # 49-55
    range(60, 78): "West",        # 60-77
    79: "North",
    80: "North"
}
```

**Examples:**
- Postal `189560` → `18` → Central
- Postal `469662` → `46` → East
- Postal `738906` → `73` → West
- Postal `768019` → `76` → West
- Postal `798528` → `79` → North

### Priority 2: Address/District Parsing

Extract district/area from address and match to zone:

**Central indicators:**
- "Orchard Road", "Orchard Boulevard"
- "Bras Basah", "City Hall", "Bugis"
- "Marina Bay", "Raffles Place", "Shenton Way"
- "Somerset", "River Valley", "Clarke Quay"
- "Tiong Bahru", "Tanjong Pagar", "Outram"
- "Beach Road", "North Bridge Road" (downtown)
- "Tanglin", "Holland", "Dempsey"

**East indicators:**
- "East Coast", "Marine Parade", "Katong"
- "Bedok", "Tampines", "Pasir Ris", "Changi"
- "Geylang", "Paya Lebar", "Eunos"
- "Simei", "Kembangan"

**North indicators:**
- "Woodlands", "Yishun", "Sembawang", "Admiralty"
- "Ang Mo Kio", "AMK", "Bishan"
- "Serangoon", "Hougang", "Punggol", "Sengkang"
- "Mandai" (zoo area)

**West indicators:**
- "Jurong", "Clementi", "Bukit Batok", "Bukit Timah"
- "Bukit Panjang", "Choa Chu Kang", "CCK"
- "Tuas", "Boon Lay", "Pioneer"
- "Queenstown", "Commonwealth"
- "Sentosa" (technically south but classified as West for venue purposes)

### Priority 3: Web Search

If postal code and address are missing or unclear, search for:

```
"[Venue Name] Singapore location address postal code"
```

Extract postal code or district from search results, then apply Priority 1 or 2.

**Example searches:**
- "Shangri-La Hotel Singapore location address postal code"
- "HortPark Singapore postal code"
- "CHIJMES Singapore district location"

## Validation Rules

Before saving zone classification:

- ✅ **Must be one of**: `"Central"`, `"East"`, `"West"`, `"North"` (exact case)
- ✅ **Confidence check**: If postal and address suggest different zones, flag for review
- ✅ **Special cases**:
  - Sentosa → West (not South)
  - Changi → East
  - Gardens by the Bay → Central
  - Jewel Changi → East
- ❌ **Never guess** if no reliable data found - leave empty and flag for manual review

## Workflow Steps

### 1. Identify Venues Needing Classification

Read venues.json and find all venues where `location.zone` is missing or empty.

Report: "Found X venues needing zone classification"

### 2. Classify Zones

For each venue, attempt classification in priority order:

**Step 2a: Check postal code**
- If `location.postal` exists and is 6 digits
- Extract first 2 digits
- Map to zone using postal_to_zone mapping
- Set confidence: HIGH

**Step 2b: Parse address**
- If postal failed or unavailable, check `location.address`
- Search for district/area keywords
- Match to zone using indicators list
- Set confidence: MEDIUM

**Step 2c: Web search**
- If both postal and address failed
- Search: "[venue name] Singapore location postal code"
- Extract postal or district from results
- Apply postal/address mapping
- Set confidence: LOW to MEDIUM (depends on clarity of results)

**Step 2d: Flag for manual review**
- If all methods fail or results are ambiguous
- Note venue in "needs manual review" list
- Leave zone empty

### 3. Update Venues JSON

1. **Create backup first**: `backend/data/backups/venues_backup_[timestamp].json`
2. Update each venue's `location.zone` field
3. Set `last_updated` to current ISO timestamp
4. Save updated venues.json

### 4. Provide Classification Report

```
Zone Classification Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Classified: X venues
   - Via postal code: A venues (high confidence)
   - Via address parsing: B venues (medium confidence)
   - Via web search: C venues (varies)

📊 Zone Distribution:
   - Central: X venues
   - East: Y venues
   - West: Z venues
   - North: W venues

⚠️  Needs manual review: N venues
   - [Venue Name] (reason: no postal/address data)
   - [Venue Name] (reason: ambiguous location)
```

## Example Execution

**User:** "Classify venue zones" or "Fill missing zones"

**Expected output:**

```
Step 1: Analyzing venues for zone classification...
✓ Read 379 venues from backend/data/venues.json
✓ Found 168 venues missing zone classification

Step 2: Classifying zones...

Batch 1/17 (Processing 10 venues)

[1/10] Shangri-La Hotel
 → No postal code found
 → Searching web: "Shangri-La Hotel Singapore location postal code"
 → Found: 22 Orange Grove Road, S(258350)
 → Postal 258350 → Central
 ✅ Classified: Central (via web search)

[2/10] HortPark
 → No postal code or address found
 → Searching web: "HortPark Singapore location postal code"
 → Found: 33 Hyderabad Road, S(119578)
 → Postal 119579 → Central
 ✅ Classified: Central (via web search)

[3/10] The Coastal Settlement
 → No postal code found
 → Address found: "200 Netheravon Road"
 → Matched: "Changi" → East
 ✅ Classified: East (via address parsing)

[4/10] ORTO
 → No postal or address found
 → Searching web: "ORTO Singapore venue location"
 → Found: 81 Lorong Chencharu, S(769198)
 → Postal 769198 → North
 ✅ Classified: North (via web search)

[5/10] Sentosa Beach Villas
 → Address: "Sentosa Island"
 → Matched: "Sentosa" → West (special case)
 ✅ Classified: West (via address parsing)

[6/10] Ya Ge Restaurant
 → No postal found
 → Address: "Orchard Hotel"
 → Matched: "Orchard" → Central
 ✅ Classified: Central (via address parsing)

[7/10] The Summerhouse
 → No postal or clear address
 → Searching web: "The Summerhouse Singapore wedding venue location"
 → Found: 3 Park Lane, S(798387)
 → Postal 798387 → North
 ✅ Classified: North (via web search)

[8/10] Jewel Cloud9 Piazza
 → Venue name contains "Jewel"
 → Known location: Jewel Changi Airport
 → Changi → East
 ✅ Classified: East (via venue name inference)

[9/10] Royal Albatross - Luxury Tall Ship
 ⚠️  Mobile venue (yacht/ship)
 → Likely berths: Sentosa Cove or Marina Bay
 ⚠️  Flagged for manual review (ambiguous location)

[10/10] Civil Service Club @ Bukit Batok
 → Venue name contains "Bukit Batok"
 → Matched: "Bukit Batok" → West
 ✅ Classified: West (via venue name parsing)

Progress: 9/10 classified, 1 flagged

[Processing continues for remaining batches...]

Step 3: Updating venues.json...
✓ Created backup: backend/data/backups/venues_backup_20251122_150000.json
✓ Updated 165 venues with zone classifications

Zone Classification Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Classified: 165 venues
   - Via postal code: 0 venues (high confidence)
   - Via address parsing: 48 venues (medium confidence)
   - Via web search: 112 venues (varies)
   - Via venue name: 5 venues (medium confidence)

📊 Zone Distribution:
   - Central: 87 venues (52.7%)
   - East: 31 venues (18.8%)
   - West: 28 venues (17.0%)
   - North: 19 venues (11.5%)

⚠️  Needs manual review: 3 venues
   - Royal Albatross - Luxury Tall Ship (mobile venue)
   - Yacht Bookings Singapore (mobile venue)
   - Beach Wedding (unclear specific location)
```

## Important Notes

- **Always create backups** in `backend/data/backups/` before modifying venues.json
- **Batch processing**: Process venues in batches of 10 for clarity (avoid rate limiting on web searches)
- **Preserve existing zones**: Don't overwrite if `location.zone` already exists unless explicitly asked
- **Validate JSON**: Ensure valid JSON structure before saving
- **Mobile venues**: Yachts, ships, and mobile event spaces should be flagged for manual review
- **Use context clues**: Venue names often contain district/area hints (e.g., "Club @ Bukit Batok")
- **Singapore-specific knowledge**: Apply special case rules (Sentosa=West, Gardens by the Bay=Central)

## Singapore Postal Code Reference

Quick reference for postal district mapping:

| Postal Range | Zone    | Key Areas |
|--------------|---------|-----------|
| 01-28, 78    | Central | CBD, Orchard, Marina, River Valley |
| 29-48        | East    | Katong, Marine Parade, Bedok, Tampines, Changi |
| 49-55, 79-80 | North   | Woodlands, Yishun, Ang Mo Kio, Bishan, Punggol |
| 60-77        | West    | Jurong, Clementi, Bukit Batok, Queenstown |

## Known Special Cases

Handle these venues with specific rules:

- **Sentosa** (any venue) → West
- **Jewel Changi Airport** → East
- **Gardens by the Bay** → Central
- **Marina Bay Sands** → Central
- **Resorts World Sentosa** → West
- **Singapore Zoo / Mandai** → North
- **Changi Airport** area → East
- **Civil Service Club** branches → Use branch location suffix

## Web Search Tips

For best results when searching:

1. **Include "Singapore"** in all searches
2. **Add "postal code"** to get structured address data
3. **Use official venue names** (avoid abbreviations)
4. **Check multiple sources** if results conflict
5. **Look for .sg domains** for more accurate Singapore data
6. **Government/official sites** (OneMap, URA) are authoritative

## Troubleshooting

**If classification seems wrong:**
- Double-check postal code extraction (ensure 6 digits, first 2 used)
- Verify district keywords match Singapore geography
- Cross-reference with Google Maps if uncertain

**If web search fails:**
- Try searching without "postal code" for general location
- Search for parent organization (e.g., hotel chain)
- Look for venue mentions on wedding forums/directories

**If venue is genuinely ambiguous:**
- Flag for manual review
- Don't force a classification
- Provide reason for flagging in report
