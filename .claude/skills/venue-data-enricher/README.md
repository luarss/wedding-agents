# Venue Data Enricher Skill

A Claude Code skill that automatically enriches Singapore wedding venue data by filling in missing critical fields using web search.

## Overview

This skill reads your `backend/data/venues.json` file, identifies incomplete venues based on `data/GAP_ANALYSIS.md`, and uses web search to populate missing:
- Pricing information (pricing_type, weekday/weekend prices, min spend)
- Location data (zone, address, postal, nearest MRT)
- Contact information (phone, email, website)
- Amenities and venue features
- Capacity and restrictions

## Usage

Invoke the skill in Claude Code by saying:

```
enrich venue data
```

Or use these alternative triggers:
- "update venue data"
- "populate missing venue fields"
- "fill venue gaps"

## What It Does

1. **Analyzes** current venue data for missing fields
2. **Searches** the web for missing information using Singapore-specific queries
3. **Validates** data against venue schema rules
4. **Updates** venues.json with found data
5. **Reports** progress and completeness metrics

## Example Output

```
Step 1: Analyzing current venue data...
✓ Read 10 venues from backend/data/venues.json

Found 3 venues needing enrichment:
1. Conrad Singapore - Missing: pricing_type, weekday_price, nearest_mrt
2. PARKROYAL on Pickering - Missing: contact.email, amenities
3. Pan Pacific Singapore - Missing: zone, mrt_distance

Step 2: Searching for missing data...

[Venue 1] Conrad Singapore
 ✓ Found pricing: $2,188++ weekday, $2,488++ weekend (plus_plus)
 ✓ Found MRT: Promenade MRT, 3 min walk, CC/DT lines
 → Updated 4 fields

[continues for all venues...]

Summary Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Processed: 3 venues
✅ Fields filled: 12
✅ Critical fields: 90% → 100% complete
✅ High priority: 75% → 95% complete
```

## Features

### 🔍 Smart Web Search
- Uses proven search query templates
- Targets official venue websites and wedding directories
- Extracts data from Singapore wedding pricing lists

### ✅ Data Validation
- Validates pricing types (plus_plus/nett)
- Checks zone classifications
- Verifies MRT line codes
- Ensures phone number formats

### 🛡️ Safety Features
- Always creates backups before modifications
- Preserves existing good data
- Never guesses uncertain data
- Validates JSON format before saving

### 📊 Comprehensive Reporting
- Shows progress for each venue
- Reports data completeness metrics
- Lists venues needing manual review
- Suggests next steps

## Data Priorities

Based on GAP_ANALYSIS.md:

### 🔴 Critical (Required)
- pricing.pricing_type
- location.zone
- location.address
- venue_type

### 🟡 High Priority (Recommended)
- pricing.weekday_price / weekend_price
- pricing.min_spend
- location.nearest_mrt
- contact.phone / email / website

### 🟢 Medium Priority (Nice to have)
- amenities.*
- restrictions.*
- location.parking_lots

## Configuration

Edit `skill_config.json` to customize:

```json
{
  "settings": {
    "maxVenuesPerSession": 10,  // Max venues to process at once
    "alwaysCreateBackup": true,  // Always backup before changes
    "validateJSON": true,        // Validate JSON before saving
    "minDataQuality": "critical_fields_only"  // Minimum fields to fill
  }
}
```

## Requirements

### Tools Used
- **WebSearch** - For finding venue information
- **Read** - For reading venues.json and GAP_ANALYSIS.md
- **Edit** - For updating venue records
- **Write** - For saving modified venues.json
- **Bash** (optional) - For JSON validation

### Files Accessed
- `backend/data/venues.json` - Main venue database
- `data/GAP_ANALYSIS.md` - Data gap priorities
- `data/annotation_backups/` - Backup directory

## Singapore Wedding Context

The skill understands Singapore-specific context:

### Pricing Types
- **plus_plus (++)** = Base price + 9% GST + 10% service charge
- **nett** = All-inclusive pricing

### Zone Classification
Automatically infers zone from postal code:
- 01-28, 78 → Central
- 29-48 → East
- 49-55, 79-80 → North
- 60-77 → West

### MRT System
Recognizes all MRT line codes:
- NS, EW, NE, CC, CE, DT, TE (major lines)
- BP, SW, PE, SE (LRT lines)

## Best Practices

### When to Use
✅ After scraping new venue data
✅ When venues are missing critical fields
✅ Before testing the wedding agent
✅ Quarterly to refresh pricing data

### What to Check After
1. Review the summary report
2. Check venues flagged for manual review
3. Verify critical field completeness is >90%
4. Test agent queries with enriched data

### Tips for Best Results
- Run on venues with at least a name and location
- Process 5-10 venues per session for best results
- Review and validate manually after first run
- Re-run for seasonal pricing updates

## Troubleshooting

### Skill Not Finding Data
- Check venue name spelling in venues.json
- Try running skill multiple times (web results vary)
- Some venues may need manual research

### JSON Validation Errors
- Skill creates backups automatically
- Check `data/annotation_backups/` for last good version
- Use `python3 -m json.tool venues.json` to validate

### Incomplete Results
- Some fields are harder to find (e.g., amenities)
- Mark venues for manual review
- Use the Streamlit annotation tool for manual entry

## Related Tools

- **Streamlit Annotation Tool** (`annotate_venues.py`) - Manual data entry UI
- **CSV Importer** (`scripts/import_venues_from_csv.py`) - Import from scraped CSVs
- **GAP Analysis** (`data/GAP_ANALYSIS.md`) - Data completeness report

## Version History

- **v1.0.0** (2025-11-18) - Initial release
  - Web search for missing venue data
  - Singapore-specific context awareness
  - Automatic backups and validation
  - Comprehensive reporting

## Contributing

To improve this skill:

1. Update `skill.md` with better search queries
2. Add new validation rules in skill.md
3. Enhance error handling
4. Add support for new data sources

## License

Part of the wedding-agent project.
