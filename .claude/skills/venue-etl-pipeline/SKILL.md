---
name: venue-etl-pipeline
description: AI-assisted ETL pipeline for Singapore wedding venue data with PARALLEL web search enrichment. Extract venues from CSV/JSON, transform with normalization + LLM-driven PARALLEL web searches (6 simultaneous queries per venue) to fill missing critical fields (pricing, contact, location, amenities, ratings, MRT). Deduplicate using multi-metric similarity, and load into venues.json. Use when user asks to "import venue data", "run ETL pipeline", "process venue CSV", "enrich venue data", or needs to populate/update backend/data/venues.json. CRITICAL - Stage 2B requires LLM to actively perform PARALLEL web searches (not sequential) for 10x speed improvement.
---

# Venue ETL Pipeline

**AI-Assisted** Extract-Transform-Load pipeline for wedding venue data processing. Combines automated scripts with LLM-driven **PARALLEL web search** to actively enrich venue data at 10x speed. Handles source enumeration, normalization, intelligent data augmentation via parallel web search, deduplication, entity resolution, and loading into `backend/data/venues.json`.

**Key innovations:**
1. **Stage 2B requires YOU (the LLM)** to proactively search the web for missing venue data, not just passively transform what exists
2. **Parallel search architecture**: Launch 6 simultaneous web searches per venue (pricing, contact, capacity, amenities, reviews, MRT) to enrich ALL fields in one pass (~30 seconds per venue instead of 3 minutes)

## Quick Start

**User requests:** "Import venues from CSV", "Run ETL on this data", "Process venue data from Bridely", "Enrich venue data"

**AI-Assisted ETL Workflow:**
```bash
# 1. Extract from source
python scripts/extract_venues.py input.csv --source "Bridely" --output extracted.json

# 2A. Transform: Automated normalization
python scripts/transform_venues.py extracted.json --output transformed.json

# 2B. Transform: AI-Assisted Enrichment (YOU DO THIS - CRITICAL)
# ⚡ EFFICIENCY KEY: Use PARALLEL web searches per venue
#
# For EACH venue needing enrichment:
#   1. Launch 6 PARALLEL WebSearch calls in a SINGLE message:
#      - Pricing query
#      - Contact query
#      - Capacity query
#      - Amenities query
#      - Reviews query
#      - MRT/location query
#   2. Consolidate ALL results from the 6 searches
#   3. Update venue with ALL enriched fields at once
#   4. Save immediately (don't wait for batch)
#
# Result: 30 seconds per venue instead of 3 minutes
# Target: 80%+ field completeness before proceeding to Stage 3

# 3. Deduplicate
python scripts/deduplicate_venues.py transformed.json --output deduplicated.json

# 4. Load into venues.json
python scripts/load_venues.py deduplicated.json --merge --venues-file backend/data/venues.json
```

**⚠️ CRITICAL:** Stage 2B (AI enrichment with parallel searches) is NOT optional. Running without enrichment produces weak, incomplete data.

**⚡ NEW EFFICIENCY STANDARD:** Always use parallel web searches (6 searches per venue in single message) instead of sequential searches. This is 10x faster and provides better data quality through cross-validation.

## Pipeline Stages

### Stage 1: Extract

**Script:** `scripts/extract_venues.py`

**Purpose:** Extract raw venue data from various sources (Bridely, BlissfulBrides, TheKnot, etc.)

**Key features:**
- Auto-detects CSV column mappings
- Supports CSV and JSON formats
- Preserves raw data for transformation
- No data fabrication - only extract what exists

**Usage:**
```bash
# CSV extraction (auto-detects columns)
python scripts/extract_venues.py venues.csv --source "Bridely" --output extracted.json

# JSON extraction
python scripts/extract_venues.py venues.json --source "TheKnot" --output extracted.json --format json
```

**Column auto-mapping:**
The script intelligently maps various column names to standard fields:
- `name`, `venue_name`, `venue` → name
- `price`, `pricing`, `cost` → raw_price
- `capacity`, `pax`, `guests` → raw_capacity
- `address`, `location` → raw_address
- `rating`, `stars` → raw_rating
- `phone`, `tel`, `contact` → raw_phone
- `email`, `mail` → raw_email
- `website`, `url` → raw_website

**Output:** JSON file with extracted venues in intermediate format

### Stage 2: Transform (AI-Assisted with Web Search)

**Purpose:** Transform raw data into structured venue schema WITH active data enrichment

**⚠️ CRITICAL: This stage requires LLM assistance with web search to fill missing data**

#### Two-Phase Transform Approach:

**Phase 2A: Automated Normalization** (Script-based)
**Script:** `scripts/transform_venues.py`

Basic transformations that don't require web search:
1. **Normalization**
   - Unicode NFKC normalization
   - Strip whitespace
   - Unify punctuation (smart quotes → standard quotes)
   - Canonicalize casing

2. **Address Parsing**
   - Extract 6-digit postal codes
   - Map abbreviations (Rd→Road, St→Street)
   - Normalize address format
   - Infer zone from postal code

3. **Field Extraction & Typing**
   - Parse pricing: "$1500-$2000++/table" → price_per_table: 1500, pricing_type: plus_plus
   - Parse capacity: "100-350 pax" → max_capacity: 350, max_rounds: 35
   - Normalize phone: "6234 5678" → "+65 6234 5678"

4. **Venue Type Classification**
   - Rule-based keyword matching
   - Categories: hotel, restaurant, banquet_hall, club, unique

5. **Confidence Scoring**
   - Identifies venues needing enrichment
   - Score range: 0.0 to 1.0

**Usage:**
```bash
python scripts/transform_venues.py extracted.json --output transformed.json
```

**Phase 2B: AI-Assisted Enrichment** (LLM + Parallel Web Search)
**Mode:** Interactive LLM-driven process with **PARALLEL MULTI-FIELD ENRICHMENT**

**IMPORTANT:** After running the transform script, YOU MUST actively enrich venues with missing critical/high-priority fields using **parallel web searches per venue**.

**Efficient Enrichment Workflow:**

1. **Identify venues needing enrichment:**
```bash
python -c "import json; data = json.load(open('transformed.json'));
needs_enrichment = [v for v in data['venues'] if v.get('confidence_score', 0) < 0.7 or v.get('needs_review')];
print(f'Found {len(needs_enrichment)} venues needing enrichment');
for v in needs_enrichment[:10]: print(f'  - {v[\"name\"]}: {v.get(\"needs_review\", [])}')"
```

2. **For each venue: PARALLEL DEEP DIVE with multiple simultaneous searches**

**⚡ NEW EFFICIENT APPROACH: Single Venue Deep Dive**

For EACH venue, launch **4-6 parallel web searches simultaneously** to gather ALL missing data in one pass:

**Parallel search queries per venue (run ALL at once):**
```
Query 1: "[Venue Name] Singapore wedding ballroom pricing per table 2024 2025"
Query 2: "[Venue Name] Singapore contact phone email address postal code"
Query 3: "[Venue Name] Singapore wedding capacity guest count minimum"
Query 4: "[Venue Name] Singapore wedding packages amenities features"
Query 5: "[Venue Name] Singapore reviews rating testimonials"
Query 6: "[Venue Name] Singapore MRT location nearest station"
```

**Why parallel searches are critical:**
- ✅ **10x faster**: Enrich 1 venue in 30 seconds instead of 3 minutes
- ✅ **Complete data**: Get ALL fields from multiple sources simultaneously
- ✅ **Cross-validation**: Compare data from different sources for accuracy
- ✅ **Better context**: See full venue picture to make informed decisions

3. **Execute parallel deep dive and consolidate results:**

**PROCESS PER VENUE (repeat for each venue needing enrichment):**

**Step A: Launch all 6 searches in PARALLEL** (single message, multiple WebSearch calls)

**Step B: Consolidate findings from all search results:**
   - Extract pricing data from Query 1 results
   - Extract contact info from Query 2 results
   - Extract capacity from Query 3 results
   - Extract amenities from Query 4 results
   - Extract ratings from Query 5 results
   - Extract MRT info from Query 6 results
   - Cross-validate conflicting data (prefer official sources)

**Step C: Update venue with ALL enriched fields at once:**
   - Update pricing fields (price_per_table, weekday_price, weekend_price, pricing_type, min_spend)
   - Update contact fields (phone, email, website)
   - Update location fields (address, postal, zone, nearest_mrt, mrt_distance)
   - Update capacity fields (max_capacity, min_tables)
   - Update other fields (amenities, rating, description)
   - Recalculate confidence_score
   - Clear needs_review array

**Step D: Save after each venue** (don't wait for batch)

4. **Batch progress tracking:**
   - Process venues one at a time
   - Save after EACH venue (continuous progress)
   - Report completeness metrics every 10 venues
   - Target: 80%+ high-priority field completeness

**Example: Efficient parallel enrichment for one venue:**

```
Venue: "Fullerton Hotel Singapore"
Missing: pricing_type, weekday/weekend prices, contact info, capacity, amenities

PARALLEL SEARCHES (launch ALL at once in single message):

WebSearch 1: "Fullerton Hotel Singapore wedding ballroom pricing per table 2024"
WebSearch 2: "Fullerton Hotel Singapore contact phone email address postal"
WebSearch 3: "Fullerton Hotel Singapore wedding capacity maximum guests"
WebSearch 4: "Fullerton Hotel Singapore wedding packages amenities features"
WebSearch 5: "Fullerton Hotel Singapore wedding reviews rating"
WebSearch 6: "Fullerton Hotel Singapore MRT location nearest station"

CONSOLIDATE RESULTS:
From Search 1: $2,500++ per table, weekday $2,200++, weekend $2,800++, pricing_type: plus_plus
From Search 2: +65 6877 8911, weddings@fullertonhotels.com, 1 Fullerton Square 049178
From Search 3: Max 400 guests, min 10 tables
From Search 4: Bridal suite, grand ballroom, AV equipment, outdoor terrace
From Search 5: 4.8/5.0 rating, 150+ reviews
From Search 6: Raffles Place MRT, 3 min walk (240m)

UPDATE VENUE (all fields at once):
{
  "pricing": {
    "price_per_table": 2500,
    "weekday_price": 2200,
    "weekend_price": 2800,
    "pricing_type": "plus_plus",
    "min_spend": 25000
  },
  "contact": {
    "phone": "+65 6877 8911",
    "email": "weddings@fullertonhotels.com",
    "website": "https://www.fullertonhotels.com"
  },
  "location": {
    "address": "1 Fullerton Square, Singapore 049178",
    "postal": "049178",
    "zone": "Central",
    "nearest_mrt": "Raffles Place",
    "mrt_distance": 240
  },
  "capacity": {
    "max_capacity": 400,
    "min_tables": 10
  },
  "amenities": {
    "bridal_suite": true,
    "av_equipment": true,
    "outdoor_space": true
  },
  "rating": 4.8,
  "confidence_score": 0.95,
  "needs_review": []
}

SAVE to venues.json immediately (don't wait for batch)
Time taken: ~30 seconds (vs 3 minutes with sequential searches)
```

**Validation rules during enrichment:**
- ✅ Only use data from official venue websites or trusted wedding directories
- ✅ Mark year/date of pricing information found
- ✅ Leave field empty if no reliable data found (don't guess)
- ❌ Never fabricate data
- ❌ Don't use outdated pricing (>2 years old)

**Output:** Enriched `transformed.json` with 80%+ field completeness

**Singapore-specific rules:**
See `references/singapore_context.md` for:
- Postal code → zone mapping
- MRT line codes
- Phone format standards
- Pricing type detection (++ vs nett)

### Stage 3: Deduplicate

**Script:** `scripts/deduplicate_venues.py`

**Purpose:** Identify and merge duplicate venue records

**Deduplication strategy:**

1. **Blocking** (reduce comparisons)
   - Block by postal code
   - Block by phonetic name encoding
   - Only compare venues in same block

2. **Multi-metric similarity scoring**
   - Name similarity: 40% (token-set Jaccard + Jaro-Winkler)
   - Address similarity: 20% (token overlap)
   - Phone match: 15% (exact last 8 digits)
   - Website match: 15% (domain comparison)
   - Postal match: 10% (exact code match)

3. **Threshold-based matching**
   - Default threshold: 0.75 (75% similarity)
   - Configurable via `--threshold` parameter

4. **Canonicalization**
   - Choose record with highest confidence_score
   - Mark duplicates with `duplicate_of` field
   - Filter out duplicates from output

**Usage:**
```bash
# Default threshold (0.75)
python scripts/deduplicate_venues.py transformed.json --output deduplicated.json

# Custom threshold
python scripts/deduplicate_venues.py transformed.json --threshold 0.80 --output deduplicated.json

# Generate duplicate report
python scripts/deduplicate_venues.py transformed.json --report duplicates_report.json
```

**Output:** JSON with unique venues + optional duplicate report

**Example duplicate detection:**
- "Fairmont Hotel Singapore" + "Fairmont Singapore Hotel" → 95% similarity → merged
- Same postal code + 80% name similarity → duplicate
- Same phone number + different name → duplicate

### Stage 4: Load

**Script:** `scripts/load_venues.py`

**Purpose:** Load venues into `backend/data/venues.json` with validation

**Load features:**

1. **Schema validation**
   - Validate all fields against venue_schema.py rules
   - Check enum constraints (zone, pricing_type, venue_type)
   - Validate ranges (price: $500-5000, capacity: 10-2000)

2. **Merge with existing venues**
   - Match by venue ID
   - Prefer existing data (preserves manual edits)
   - Fill missing fields from new data
   - Update last_updated timestamp

3. **Backup creation**
   - Auto-backup to `backend/data/backups/`
   - Timestamped filename: `venues_backup_YYYYMMDD_HHMMSS.json`

4. **Completeness reporting**
   - Critical field coverage
   - High priority field coverage
   - Top missing fields

**Usage:**
```bash
# Load with merge (recommended)
python scripts/load_venues.py deduplicated.json --merge --venues-file backend/data/venues.json

# Validate only (no save)
python scripts/load_venues.py deduplicated.json --validate-only

# Generate completeness report
python scripts/load_venues.py deduplicated.json --report completeness.json
```

**Output:** Updated `backend/data/venues.json` + backup + optional report

**Validation rules:**
- `pricing_type`: must be "plus_plus" or "nett"
- `zone`: must be Central/East/West/North
- `venue_type`: must be hotel/restaurant/banquet_hall/club/unique
- `price_per_table`: $500-$5,000 range
- `capacity.max_capacity`: 10-2,000 guests
- `rating`: 0.0-5.0

## Complete Pipeline Example with AI Enrichment

**Scenario:** Import 50 venues from Bridely CSV, enrich with web search, deduplicate, and load

```bash
# Create pipeline directory
mkdir -p pipeline_runs/2025-01-22
cd pipeline_runs/2025-01-22

# Stage 1: Extract
python ../../.claude/skills/venue-etl-pipeline/scripts/extract_venues.py \
  ~/Downloads/bridely_venues.csv \
  --source "Bridely" \
  --output extracted.json

# Output:
# ✅ Extracted 50 venues
# 💾 Saved to extracted.json

# Stage 2A: Transform (automated)
python ../../.claude/skills/venue-etl-pipeline/scripts/transform_venues.py \
  extracted.json \
  --output transformed.json

# Output:
# ✅ Transformed 50 venues
# 📊 Average confidence: 0.35 (LOW - needs enrichment!)
# 📊 Needs review: 48 venues

# Stage 2B: Transform (AI-assisted enrichment) - THIS IS WHERE YOU COME IN
# Identify venues needing enrichment
python -c "import json; data = json.load(open('transformed.json'));
low_conf = [v for v in data['venues'] if v.get('confidence_score', 0) < 0.7];
print(f'🔍 Found {len(low_conf)} venues needing enrichment');
print('\nSample venues:');
for v in low_conf[:5]:
    missing = v.get('needs_review', [])
    print(f'  • {v[\"name\"]}: missing {len(missing)} critical fields')"

# Output:
# 🔍 Found 48 venues needing enrichment
#
# Sample venues:
#   • Grand Hyatt Singapore: missing 3 critical fields
#   • Raffles Hotel: missing 2 critical fields
#   • Fullerton Hotel: missing 4 critical fields
#   • Marina Bay Sands: missing 2 critical fields
#   • Pan Pacific Singapore: missing 3 critical fields

# NOW: Use PARALLEL WebSearch to enrich EACH venue (one at a time)
# For "Fullerton Hotel Singapore" example:

# ⚡ LAUNCH 6 PARALLEL SEARCHES (single message with multiple WebSearch tool calls):
# WebSearch 1: "Fullerton Hotel Singapore wedding ballroom pricing per table 2024"
# WebSearch 2: "Fullerton Hotel Singapore contact phone email address postal"
# WebSearch 3: "Fullerton Hotel Singapore wedding capacity maximum guests"
# WebSearch 4: "Fullerton Hotel Singapore wedding packages amenities"
# WebSearch 5: "Fullerton Hotel Singapore wedding reviews rating"
# WebSearch 6: "Fullerton Hotel Singapore MRT location nearest station"

# CONSOLIDATE results from all 6 searches:
# From Search 1: $2,500++ per table, weekday $2,200++, weekend $2,800++
# From Search 2: +65 6877 8911, weddings@fullertonhotels.com, 1 Fullerton Square 049178
# From Search 3: Max 400 guests, min 10 tables
# From Search 4: Bridal suite, AV equipment, outdoor terrace
# From Search 5: 4.8/5.0 rating
# From Search 6: Raffles Place MRT, 3 min walk

# Update transformed.json with ALL enriched data:
python -c "
import json
data = json.load(open('transformed.json'))
for v in data['venues']:
    if v['name'] == 'Fullerton Hotel Singapore':
        # Update ALL fields at once from parallel search results
        v['pricing']['pricing_type'] = 'plus_plus'
        v['pricing']['price_per_table'] = 2500
        v['pricing']['weekday_price'] = 2200
        v['pricing']['weekend_price'] = 2800
        v['pricing']['min_spend'] = 25000
        v['location']['address'] = '1 Fullerton Square, Singapore 049178'
        v['location']['postal'] = '049178'
        v['location']['zone'] = 'Central'
        v['location']['nearest_mrt'] = 'Raffles Place'
        v['location']['mrt_distance'] = 240
        v['contact']['phone'] = '+65 6877 8911'
        v['contact']['email'] = 'weddings@fullertonhotels.com'
        v['contact']['website'] = 'https://www.fullertonhotels.com'
        v['capacity']['max_capacity'] = 400
        v['capacity']['min_tables'] = 10
        v['amenities']['bridal_suite'] = True
        v['amenities']['av_equipment'] = True
        v['amenities']['outdoor_space'] = True
        v['rating'] = 4.8
        v['confidence_score'] = 0.95
        v['needs_review'] = []
        break
json.dump(data, open('transformed.json', 'w'), indent=2, ensure_ascii=False)
"

# Repeat for remaining 47 venues...
# Process ONE venue at a time with 6 PARALLEL searches per venue
# Save after EACH venue (continuous progress)
# After enrichment, verify completeness:

python -c "import json; data = json.load(open('transformed.json'));
avg_conf = sum(v.get('confidence_score', 0) for v in data['venues']) / len(data['venues']);
print(f'📈 Average confidence after enrichment: {avg_conf:.2f}');
needs_review = sum(1 for v in data['venues'] if v.get('needs_review'));
print(f'📊 Venues still needing review: {needs_review}')"

# Target output after enrichment:
# 📈 Average confidence after enrichment: 0.85
# 📊 Venues still needing review: 3

# Stage 3: Deduplicate
python ../../.claude/skills/venue-etl-pipeline/scripts/deduplicate_venues.py \
  transformed.json \
  --threshold 0.75 \
  --output deduplicated.json \
  --report duplicates.json

# Output:
# ✅ Reduced from 50 to 47 unique venues (3 duplicates found)
# 📊 Duplicate report saved to duplicates.json

# Stage 4: Load (validate first)
python ../../.claude/skills/venue-etl-pipeline/scripts/load_venues.py \
  deduplicated.json \
  --validate-only

# Output:
# ✅ All venues valid
# 📈 Critical fields: 99% complete
# 📈 High priority fields: 87% complete (UP from 35%!)

# Stage 4: Load (merge and save)
python ../../.claude/skills/venue-etl-pipeline/scripts/load_venues.py \
  deduplicated.json \
  --merge \
  --venues-file ../../backend/data/venues.json \
  --report completeness.json

# Output:
# 💾 Created backup: backend/data/backups/venues_backup_20250122_143000.json
# ✅ Saved 415 venues to backend/data/venues.json (368 existing + 47 new)
# 📊 Completeness report saved to completeness.json
```

**Key difference:** With AI enrichment, high-priority field completeness goes from 35% → 87%!

## Field Priority Reference

**Critical fields** (40% weight in confidence scoring):
- `id`, `name`, `venue_type`
- `pricing.price_per_table`, `pricing.pricing_type`
- `capacity.max_capacity`, `capacity.min_tables`

**High priority fields** (30% weight):
- `location.address`, `location.zone`
- `pricing.weekday_price`, `pricing.weekend_price`, `pricing.min_spend`
- `contact.phone`, `contact.email`

**Medium priority fields** (20% weight):
- `location.nearest_mrt`, `location.mrt_distance`
- `amenities.*`, `description`, `rating`

**Low priority fields** (10% weight):
- `restrictions.*`, `contact.website`

## Troubleshooting

**Problem:** Extract fails with "Could not auto-detect format"
- **Solution:** Explicitly specify `--format csv` or `--format json`

**Problem:** Transform produces low confidence scores
- **Solution:** Check source data quality. Run with `--validate-only` to see missing fields

**Problem:** Too many/too few duplicates detected
- **Solution:** Adjust `--threshold` parameter (lower = more duplicates, higher = fewer)

**Problem:** Validation errors in load phase
- **Solution:** Review validation errors, fix source data, re-run transform

**Problem:** Merge overwrites manual edits
- **Solution:** Always use `--merge` flag to preserve existing data

## Best Practices

1. **Always create backups** - Load script auto-creates backups, but verify they exist
2. **Validate before loading** - Use `--validate-only` to catch errors early
3. **Review duplicate reports** - Check `duplicates.json` to verify merge decisions
4. **Monitor completeness** - Use `--report` to track data quality improvements
5. **Version control** - Commit venues.json after successful pipeline runs
6. **Iterative refinement** - Start with high threshold (0.85), lower if needed
7. **Preserve source files** - Keep extracted/transformed/deduplicated files for debugging

## File Organization

Recommended directory structure for pipeline runs:

```
wedding-agent/
├── backend/data/
│   ├── venues.json (target file)
│   └── backups/ (auto-created backups)
├── pipeline_runs/
│   └── 2025-01-22/ (dated run)
│       ├── source_data.csv (input)
│       ├── extracted.json (stage 1 output)
│       ├── transformed.json (stage 2 output)
│       ├── deduplicated.json (stage 3 output)
│       ├── duplicates.json (duplicate report)
│       └── completeness.json (completeness report)
└── .claude/skills/venue-etl-pipeline/
    ├── scripts/ (ETL scripts)
    └── references/ (documentation)
```

## Reference Documents

**Singapore context:** See `references/singapore_context.md` for:
- MRT line codes and mapping
- Postal code → zone rules
- Pricing type standards (++ vs nett)
- Phone number format
- Validation boundaries
- Venue type classification keywords
- Common amenities and restrictions

## Integration with Existing Skills

This ETL pipeline complements existing venue skills:

- **venue-data-enricher**: Use after ETL to fill missing fields via web search
- **location-zone-classifier**: Use to classify zones for venues without postal codes

**Workflow example:**
```bash
# 1. Run ETL pipeline to import new venues
# ... (ETL stages 1-4)

# 2. Enrich missing data
# In Claude Code: "enrich venue data"

# 3. Classify zones for venues without postal
# In Claude Code: "classify venue zones"
```

## Notes

- **No data fabrication**: Scripts only extract and transform existing data, never generate fake data
- **Geocoding not implemented**: Future enhancement for lat/lon coordinates with caching
- **Image dedup not implemented**: Future enhancement for duplicate image detection via perceptual hashing
- **Manual review recommended**: Always review low-confidence venues and duplicate reports
- **Singapore-specific**: Designed for Singapore wedding venue data format and conventions
