---
name: venue-etl-pipeline
description: Automated ETL pipeline for Singapore wedding venue data. Extract venues from CSV/JSON sources, transform with normalization/deduplication/geocoding, and load into venues.json. Use when the user asks to "import venue data", "run ETL pipeline", "process venue CSV", "normalize venue data", "deduplicate venues", or needs to populate/update backend/data/venues.json from external sources.
---

# Venue ETL Pipeline

Automated Extract-Transform-Load pipeline for wedding venue data processing. Handles source enumeration, normalization, deduplication, entity resolution, and loading into `backend/data/venues.json`.

## Quick Start

**User requests:** "Import venues from CSV", "Run ETL on this data", "Process venue data from Bridely"

**Basic workflow:**
```bash
# 1. Extract from source
python scripts/extract_venues.py input.csv --source "Bridely" --output extracted.json

# 2. Transform (normalize, parse, classify)
python scripts/transform_venues.py extracted.json --output transformed.json

# 3. Deduplicate
python scripts/deduplicate_venues.py transformed.json --output deduplicated.json

# 4. Load into venues.json
python scripts/load_venues.py deduplicated.json --merge --venues-file backend/data/venues.json
```

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

### Stage 2: Transform

**Script:** `scripts/transform_venues.py`

**Purpose:** Transform raw data into structured venue schema

**Transformations applied:**

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
   - Weighted by field completeness
   - Critical fields: 40%, High priority: 30%, Medium: 20%, Low: 10%
   - Score range: 0.0 to 1.0

**Usage:**
```bash
python scripts/transform_venues.py extracted.json --output transformed.json
```

**Output:** JSON with normalized, parsed venues + confidence scores

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

## Complete Pipeline Example

**Scenario:** Import 50 venues from Bridely CSV, deduplicate, and load into existing venues.json

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

# Stage 2: Transform
python ../../.claude/skills/venue-etl-pipeline/scripts/transform_venues.py \
  extracted.json \
  --output transformed.json

# Output:
# ✅ Transformed 50 venues
# 📊 Average confidence: 0.78
# 📊 Needs review: 5 venues

# Stage 3: Deduplicate
python ../../.claude/skills/venue-etl-pipeline/scripts/deduplicate_venues.py \
  transformed.json \
  --threshold 0.75 \
  --output deduplicated.json \
  --report duplicates.json

# Output:
# ✅ Reduced from 50 to 42 unique venues
# 📊 Duplicate report saved to duplicates.json

# Stage 4: Load (validate first)
python ../../.claude/skills/venue-etl-pipeline/scripts/load_venues.py \
  deduplicated.json \
  --validate-only

# Output:
# ✅ All venues valid
# 📈 Critical fields: 95% complete
# 📈 High priority fields: 82% complete

# Stage 4: Load (merge and save)
python ../../.claude/skills/venue-etl-pipeline/scripts/load_venues.py \
  deduplicated.json \
  --merge \
  --venues-file ../../backend/data/venues.json \
  --report completeness.json

# Output:
# 💾 Created backup: backend/data/backups/venues_backup_20250122_143000.json
# ✅ Saved 410 venues to backend/data/venues.json (368 existing + 42 new)
# 📊 Completeness report saved to completeness.json
```

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
