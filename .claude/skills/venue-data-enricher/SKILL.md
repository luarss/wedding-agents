---
name: venue-data-enricher
description: Automatically enrich Singapore wedding venue data by filling missing critical fields using web search. Use when the user asks to "enrich venue data", "update venue data", "populate missing venue fields", "fill venue gaps", or needs to improve data completeness in backend/data/venues.json.
---

# Venue Data Enricher

Systematically enrich Singapore wedding venue data by filling missing fields in `backend/data/venues.json` using web search.

## Quick Start

When the user asks to enrich venue data:

1. Read `backend/data/venues.json` and identify venues with missing critical/high-priority fields
2. For each incomplete venue, search the web for missing information
3. Update venues.json with found data, creating a backup first
4. Report completeness metrics and any venues needing manual review

## Data Priority Levels

Focus enrichment on these fields (from `data/GAP_ANALYSIS.md`):

**🔴 CRITICAL** (Required for core functionality):
- `pricing.pricing_type`, `location.zone`, `location.address`, `venue_type`

**🟡 HIGH PRIORITY** (Significantly improves UX):
- `pricing.weekday_price`, `pricing.weekend_price`, `pricing.min_spend`
- `location.nearest_mrt`, `location.mrt_distance`
- `contact.phone`, `contact.email`, `contact.website`

**🟢 MEDIUM PRIORITY** (Nice to have):
- `amenities.*`, `location.parking_lots`, `restrictions.*`

## Web Search Strategy

Use these proven search patterns per venue:

**For Pricing:**
```
"[Venue Name] Singapore wedding banquet pricing 2025 per table"
"[Venue Name] Singapore wedding package price"
```

**For Contact & Location:**
```
"[Venue Name] Singapore wedding contact email phone"
"[Venue Name] Singapore address postal code"
```

**For Amenities:**
```
"[Venue Name] Singapore wedding ballroom amenities MRT"
```

## Data Validation

Before saving, validate:

- **Pricing type**: Must be "plus_plus" or "nett"
- **Zone**: Must be Central/East/West/North (infer from postal code if needed)
- **Phone**: Format +65 XXXX XXXX
- **Postal**: 6 digits
- **MRT Lines**: Valid codes (NS, EW, CC, CE, DT, TE, NE, BP, SW, PE, SE)
- **Prices**: $500-$5,000 per table is reasonable range

**Postal to Zone mapping:**
- 01-28, 78 → Central
- 29-48 → East
- 49-55, 79-80 → North
- 60-77 → West

## Handling Uncertainty

- ✅ Leave field empty rather than guess
- ✅ Note venue in "needs manual review" list
- ❌ Never make up data
- ❌ Don't use outdated pricing (>2 years old)

## Singapore Wedding Context

**Pricing types:**
- "plus_plus" or "++" = Base + 9% GST + 10% service charge
- "nett" = All-inclusive

**MRT lines:** NS (Red), EW (Green), CC/CE (Orange), NE (Purple), DT (Blue), TE (Brown), BP/SW/PE/SE (LRT)

## Workflow Steps

### 1. Identify Incomplete Venues

Read venues.json and check each venue for missing critical/high-priority fields. Prioritize venues with most missing critical fields.

Report: "Found X venues needing enrichment"

### 2. Search for Missing Data

For each incomplete venue, run 2-3 web searches using the search patterns above to find missing fields.

### 3. Update Venues JSON

1. **Create backup first**: `backend/data/backups/venues_backup_[timestamp].json`
2. Update venue with all found information
3. Set `last_updated` to current ISO timestamp
4. Preserve existing data (don't overwrite unless new data is clearly better)
5. Save updated venues.json

Report per venue: "Updated [Venue Name]: filled X/Y missing fields"

### 4. Provide Summary Report

```
Summary Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Processed: X venues
✅ Fields filled: Y
✅ Critical fields: A% → B% complete
✅ High priority: C% → D% complete

⚠️  Needs manual review: Z venues
   - [Venue Name] (missing: field1, field2)
```

## Example Execution

**User:** "Enrich venue data"

**Expected output:**

```
Step 1: Analyzing current venue data...
✓ Read 10 venues from backend/data/venues.json

Found 3 venues needing enrichment:
1. ABC Hotel - Missing: pricing_type, nearest_mrt, contact info
2. XYZ Restaurant - Missing: zone, weekday_price
3. DEF Ballroom - Missing: address, phone

Step 2: Searching for missing data...

[Venue 1] ABC Hotel Singapore
 ✓ Found pricing: $1,588++ per table (pricing_type: plus_plus)
 ✓ Found contact: +65 6123 4567, events@abchotel.com
 ✓ Found MRT: Newton MRT, 5 min walk, NS line
 → Updated 6 fields

[Venue 2] XYZ Restaurant Singapore
 ✓ Found address: 123 Orchard Road, S238823
 ✓ Inferred zone: Central (postal 238823)
 ✓ Found pricing: $888 weekday, $1,088 weekend
 → Updated 4 fields

[Venue 3] DEF Ballroom Singapore
 ✓ Found address: 456 East Coast Road, S428789
 ✓ Found contact: +65 6234 5678
 ! Could not find website - needs manual review
 → Updated 3 fields

Step 3: Updating venues.json...
✓ Created backup: backend/data/backups/venues_backup_20251122_143000.json
✓ Saved 13 field updates across 3 venues

Summary Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Processed: 3 venues
✅ Fields filled: 13
✅ Critical fields: 90% → 100% complete
✅ High priority: 70% → 88% complete

⚠️  Needs manual review: 1 venue
   - DEF Ballroom (missing website)
```

## Important Notes

- **Always create backups** in `backend/data/backups/` before modifying venues.json
- **Batch operations**: Process multiple venues in one session for efficiency (5-10 venues recommended)
- **Preserve existing data**: Don't overwrite fields that already have valid data
- **Validate JSON**: Ensure valid JSON structure before saving
- **Report progress**: Show clear updates for each venue processed
