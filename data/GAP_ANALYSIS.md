# Wedding Data Gap Analysis

**Generated:** 2025-11-18
**Analyzed datasets:** BB (BlissfulBrides), BLY (Bridely), TWN (TheWeddingNotebook)

## Executive Summary

We currently have **247 unique Singapore venues** across two main sources (BB: 218, BLY: 247 with overlap). While we have good coverage of venue names and basic pricing, we have significant gaps in critical fields needed for intelligent venue comparison.

**Key Findings:**
- ❌ **Location data is critically incomplete** (only 14% in BB, 0% in BLY)
- ❌ **No amenities data** in any scraped source
- ❌ **No contact information** (email, phone, website)
- ❌ **Pricing format is inconsistent** and needs parsing/normalization
- ⚠️ **Venue types are missing** (can't distinguish hotels vs restaurants vs banquet halls)
- ✅ **Good coverage** of names, capacity ranges, and user ratings

## Detailed Gap Analysis by Field Category

### 🔴 CRITICAL GAPS (Blocking core functionality)

| Field | Required | BB Coverage | BLY Coverage | Impact |
|-------|----------|-------------|--------------|--------|
| `pricing.pricing_type` | ✅ | 0% | 0% | Cannot calculate accurate total costs (GST+service) |
| `pricing.price_per_table` | ✅ | 76% | 68% | Need to parse from text (e.g., "$1588++") |
| `location.zone` | ✅ | 0% | 0% | Cannot filter by area (Central/East/West/North) |
| `location.address` | ✅ | 14% | 0% | Cannot show venue location or calculate accessibility |
| `venue_type` | ✅ | 0% | 0% | Cannot categorize venues (hotel/restaurant/club) |
| `capacity.max_capacity` | ✅ | 74% | 70% | Need to parse "10-40 tables" → "400 guests" |

### 🟡 HIGH PRIORITY GAPS (Significantly limits usefulness)

| Field | BB | BLY | What's Missing |
|-------|-------|-----|----------------|
| `pricing.weekday_price` | ⚠️ | 0% | Need to parse from text like "$1588++Mon-Fri" |
| `pricing.weekend_price` | ⚠️ | 0% | Need to parse from text like "$1788++Sat-Sun" |
| `pricing.min_spend` | 0% | 0% | Critical for budget filtering |
| `pricing.min_tables` | 74% | 0% | Needed to validate guest count feasibility |
| `location.nearest_mrt` | 0% | 0% | Important for guests without cars |
| `location.mrt_distance` | 0% | 0% | Affects accessibility scoring |
| `location.postal` | 0% | 0% | Needed for precise mapping |
| `contact.phone` | 0% | 0% | Cannot provide booking contact |
| `contact.email` | 0% | 0% | Cannot facilitate inquiries |
| `contact.website` | 0% | 0% | Cannot link to official venue site |

### 🟢 MEDIUM PRIORITY GAPS (Nice to have, enhances comparisons)

| Field | BB | BLY | Notes |
|-------|-----|-----|-------|
| `amenities.*` (all) | 0% | 0% | No structured amenities data available |
| `packages` | 47% | 0% | BB has PDF links but not parsed |
| `description` | 0% | 0% | Would help LLM provide context |
| `restrictions.*` | 0% | 0% | Outside catering, corkage, etc. |
| `reviews_summary` | 0% | 0% | BLY has review counts but no text |

### ✅ GOOD COVERAGE (Working well)

| Field | BB | BLY | Quality |
|-------|-----|-----|---------|
| `name` | 100% | 100% | ✅ Clean, consistent |
| `rating` | 37% | 78% | ✅ BLY has venue/service/food ratings |
| `review_count` | 0% | 100% | ✅ BLY has counts (e.g., "141 reviews") |
| `price` (raw text) | 76% | 68% | ⚠️ Needs parsing/normalization |
| `capacity` (raw text) | 74% | 70% | ⚠️ Needs parsing to structured format |

## Data Quality Issues

### 1. Pricing Format Inconsistencies

**BB Examples:**
```
"$1588++Mon - Fri$1788++Sat - Sun"
"$988–$1588Mon - Sun"
"$1588++Mon - Thu$1688++Friday$1988++Saturday$1788++Sunday"
```

**BLY Examples:**
```
"$238-$298++/pax"  ← Per person, not per table!
"$1500-$2000++/table"
```

**Action needed:** Parser to extract:
- Base price (weekday/weekend)
- Pricing type (++/nett)
- Per-table vs per-pax
- Day-specific pricing

### 2. Capacity Format Inconsistencies

**BB Examples:**
```
"10 - 40- Sun"  ← Parsing error in scraper
"16 - 40Mon - Sun"
```

**BLY Examples:**
```
"100-350 pax"  ← Need to convert to tables (÷10)
```

**Action needed:** Parser to extract:
- Min/max tables or guests
- Convert pax ↔ tables (÷10 or ×10)

### 3. Location Data Completeness

Only **32/218 (14%)** BB venues have location data. BLY has **zero** location data.

**Example good data (BB):**
```
"PARKROYAL on Beach Road: 7500 Beach Road, Singapore 199591"
```

**What's missing:**
- Zone classification (Central/East/West/North)
- Nearest MRT + walking distance
- Parking availability
- District names

### 4. Missing Venue Type Classification

Cannot distinguish between:
- Hotels (typically higher-end, multiple ballrooms)
- Restaurants (Chinese restaurants common for weddings)
- Banquet halls (standalone venues)
- Clubs (country clubs, golf clubs)
- Unique venues (Gardens by the Bay, museums, etc.)

This is critical for venue personality matching.

## Dataset Statistics

| Metric | BB | BLY | TWN | Combined |
|--------|-----|-----|-----|----------|
| **Total venues** | 218 | 247 | 84 | ~400-500 (with deduplication) |
| **Singapore venues** | 218 | 247 | 0 | 465 |
| **Malaysia venues** | 0 | 0 | 83 | 83 |
| **Has pricing** | 76% | 68% | 100% | - |
| **Has capacity** | 74% | 70% | 100% | - |
| **Has location** | 14% | 0% | 100% | - |
| **Has ratings** | 37% | 78% | 0% | - |
| **Has contact** | 0% | 0% | 0% | - |

**Note:** TWN data is all Malaysia, not useful for Singapore weddings.

## Recommended Data Sources to Add

### 🎯 High Priority (Free, High Value)

1. **HitcheeD.com** (Singapore)
   - Status: Strategy documented, scraper not implemented
   - Value: Comprehensive vendor profiles, photos, pricing
   - Coverage: Hotels, venues, vendors across categories
   - Data: `/professionals/{venue-name}` pages with structured data
   - Plan: `/home/luars/wedding-data/claude/plans/hitcheed-scraping-strategy-2025-10-21.md`

2. **PerfectWeddings.sg** (Singapore)
   - Status: Strategy documented, scraper not implemented
   - Value: Detailed venue listings with reviews
   - Coverage: Singapore-focused wedding venues
   - Plan: `/home/luars/wedding-data/claude/plans/perfectweddings-scraping-plan-2025-11-16.md`

3. **SingaporeBrides.com** (Singapore)
   - Status: Directory exists (`data/sb/`) but **empty**
   - Value: Longest-running Singapore wedding forum
   - Coverage: Extensive user reviews and real pricing data
   - Data: Forum threads, vendor directories, real wedding stories

4. **Google Maps Places API** (Free tier: 28,000 requests/month)
   - **Critical missing data it provides:**
     - ✅ Exact addresses with postal codes
     - ✅ Geographic coordinates (lat/lng)
     - ✅ Nearest MRT calculation (via distance matrix)
     - ✅ Opening hours
     - ✅ Phone numbers
     - ✅ Websites
     - ✅ Photos
     - ✅ User reviews with ratings
   - **Implementation:**
     ```python
     # Match existing venues to Places API
     for venue in venues:
         places = search_google_places(venue.name + " Singapore")
         venue.location = extract_location_data(places[0])
     ```
   - **Cost:** Free up to 28K requests/month (enough for monthly updates)

### 🔍 Medium Priority (Requires Web Scraping)

5. **The Wedding Scoop** (Singapore)
   - URL: theweddingscoop.com
   - Value: Curated venue recommendations, pricing guides
   - Coverage: Premium venues with detailed write-ups

6. **WeddingDay.sg**
   - Value: Local marketplace with verified vendors
   - Coverage: Venues, photographers, florists, etc.

7. **Carousell Wedding Services**
   - Value: Real market pricing (actual vendor offers)
   - Coverage: Second-hand decor, budget vendors, real prices
   - Data: Vendor listings with contact info

### 📊 Alternative Data Enhancement

8. **OneMap API** (Singapore Government, Free)
   - **What it provides:**
     - ✅ Address → Postal code
     - ✅ Postal code → Zone/District
     - ✅ Routing (venue → nearest MRT)
     - ✅ Accurate Singapore geography
   - **Use case:** Enrich existing partial addresses
   - **Cost:** Free, official government API
   - **Docs:** developers.onemap.sg

9. **LTA DataMall API** (Singapore, Free)
   - **What it provides:**
     - ✅ Real-time public transport data
     - ✅ MRT station locations
     - ✅ Walking distances
     - ✅ Parking availability
   - **Use case:** Calculate venue accessibility scores
   - **Cost:** Free with registration
   - **Docs:** datamall.lta.gov.sg

## Proposed Data Enrichment Pipeline

### Phase 1: Clean & Normalize Existing Data (Immediate)

1. **Price parser** for BB/BLY formats → structured pricing schema
2. **Capacity parser** for "10-40 tables" → `{min_tables: 10, max_tables: 40}`
3. **Deduplicate venues** across BB/BLY (e.g., "PARKROYAL on Beach Road" appears in both)
4. **Extract postal codes** from existing BB addresses (14% have them)

**Expected improvement:** 218 venues → ~180 deduplicated with cleaner data

### Phase 2: Enrich with Government APIs (High impact, low effort)

1. **OneMap API**: Match venue names → addresses → postal codes → zones
   ```
   Input: "Marina Bay Sands"
   Output: {
     address: "10 Bayfront Avenue",
     postal: "018956",
     zone: "Central",
     district: "Marina Bay"
   }
   ```

2. **LTA DataMall**: Calculate MRT accessibility
   ```
   Input: postal code "018956"
   Output: {
     nearest_mrt: "Bayfront MRT",
     mrt_lines: ["CE", "DT"],
     walking_distance: "3 min"
   }
   ```

**Expected improvement:** 180 venues → 150+ with location data (83% coverage)

### Phase 3: Add New Free Sources (Medium effort)

1. Implement **HitcheeD scraper** (plan already exists)
2. Implement **PerfectWeddings scraper** (plan already exists)
3. Fix **SingaporeBrides scraper** (currently broken/empty)

**Expected improvement:** +100-150 unique venues, better amenities data

### Phase 4: Enhance with Google Places API (High value)

1. Match existing venues to Google Places
2. Extract missing contact info (phone, email, website)
3. Get user photos and recent reviews
4. Validate/correct addresses and names

**Expected improvement:** Near-complete contact info, validated addresses

## Critical Fields Mapping Plan

### How to fill critical gaps with proposed sources:

| Field | Current | HitcheeD | SingaporeBrides | Google Places | OneMap | LTA |
|-------|---------|----------|-----------------|---------------|--------|-----|
| `pricing.pricing_type` | 0% | ⚠️ | ✅ | ❌ | ❌ | ❌ |
| `location.zone` | 0% | ❌ | ❌ | ❌ | ✅ | ❌ |
| `location.address` | 14% | ✅ | ⚠️ | ✅ | ✅ | ❌ |
| `location.nearest_mrt` | 0% | ❌ | ❌ | ⚠️ | ❌ | ✅ |
| `location.mrt_distance` | 0% | ❌ | ❌ | ❌ | ✅ | ✅ |
| `contact.phone` | 0% | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| `contact.email` | 0% | ✅ | ❌ | ⚠️ | ❌ | ❌ |
| `contact.website` | 0% | ✅ | ❌ | ✅ | ❌ | ❌ |
| `amenities.*` | 0% | ⚠️ | ✅ | ❌ | ❌ | ❌ |
| `venue_type` | 0% | ⚠️ | ⚠️ | ✅ | ❌ | ❌ |
| `packages` | 47%* | ✅ | ✅ | ❌ | ❌ | ❌ |

*BB has PDF links, not parsed data

Legend:
- ✅ Reliably available
- ⚠️ Sometimes available / needs parsing
- ❌ Not available

## Cost-Benefit Analysis

| Data Source | Setup Effort | Ongoing Cost | Data Quality | Estimated Venues Added |
|-------------|--------------|--------------|--------------|------------------------|
| Price/capacity parsing | Low | Free | High | 0 (improves existing) |
| OneMap API | Low | Free | High | 0 (enriches existing) |
| LTA DataMall | Low | Free | High | 0 (enriches existing) |
| HitcheeD scraper | Medium | Free | Medium-High | +50-80 |
| PerfectWeddings scraper | Medium | Free | Medium | +30-50 |
| SingaporeBrides fix | Medium | Free | High | +50-100 |
| Google Places API | Low-Medium | Free* | Very High | 0 (enriches existing) |
| Manual venue research | High | Free | Very High | +10-20 premium venues |

*28,000 requests/month free tier

## Recommended Action Plan

### Quick Wins (1-2 days)
1. ✅ Parse existing price/capacity text → structured data
2. ✅ Deduplicate venues across BB/BLY
3. ✅ Integrate OneMap API for zone/district mapping
4. ✅ Integrate LTA DataMall for MRT accessibility

### High Impact (1 week)
5. ✅ Implement Google Places API integration
6. ✅ Implement HitcheeD scraper (plan exists)
7. ✅ Fix SingaporeBrides scraper (directory exists but empty)

### Medium Impact (2 weeks)
8. ✅ Implement PerfectWeddings scraper (plan exists)
9. ✅ Parse BB PDF price lists (47% of venues have PDFs)
10. ✅ Add manual data for top 10-20 premium venues (Four Seasons, Raffles, etc.)

### Future Enhancements
- Real-time pricing updates (quarterly scrapes)
- User-submitted data collection
- Venue photo scraping/curation
- Integration with venue booking APIs (if available)

## Sample Enhanced Venue Record

**Before (current BLY data):**
```json
{
  "name": "Mandarin Oriental Singapore",
  "price": "$238-$298++/pax",
  "capacity": "100-350 pax",
  "venueRating": "4.5",
  "reviews": "141"
}
```

**After (with all enhancements):**
```json
{
  "id": "venue-mandarin-oriental-sg",
  "name": "Mandarin Oriental Singapore",
  "venue_type": "hotel",
  "pricing": {
    "price_per_table": 2500,
    "weekday_price": 2380,
    "weekend_price": 2980,
    "min_spend": 25000,
    "min_tables": 10,
    "pricing_type": "plus_plus"
  },
  "capacity": {
    "min_tables": 10,
    "max_capacity": 350,
    "max_rounds": 35,
    "comfortable_capacity": 300
  },
  "location": {
    "address": "5 Raffles Avenue, Singapore 039797",
    "postal": "039797",
    "zone": "Central",
    "district": "Marina Bay",
    "nearest_mrt": "Esplanade MRT",
    "mrt_distance": "5 min walk",
    "mrt_lines": ["CC"],
    "parking_lots": 150,
    "parking_cost": "$3-5/hr"
  },
  "amenities": {
    "av_equipment": true,
    "bridal_suite": true,
    "in_house_catering": true,
    "pillar_free": true,
    "city_view": true,
    "waterfront_view": true
  },
  "contact": {
    "phone": "+65 6338 0066",
    "email": "mosin-events@mohg.com",
    "website": "https://www.mandarinoriental.com/singapore",
    "booking_url": "https://www.mandarinoriental.com/singapore/marina-bay/luxury-hotel/events"
  },
  "rating": 4.5,
  "review_count": 141,
  "data_source": "Bridely + Google Places + OneMap"
}
```

**Data completeness: 22% → 95%**

## Conclusion

Our current dataset provides a good foundation (465 Singapore venues) but has critical gaps that limit the AI agent's effectiveness:

**Biggest Blockers:**
1. Missing location zones (can't filter by area)
2. Missing pricing types (can't calculate accurate costs)
3. Missing contact info (can't facilitate bookings)
4. Missing amenities (can't match venue features to requirements)

**Best Path Forward:**
1. **Phase 1-2 (Government APIs)** can fix location gaps with minimal effort
2. **Phase 3 (New scrapers)** adds more venues and amenities data
3. **Phase 4 (Google Places)** completes contact info and validation

**Estimated timeline:** 2-3 weeks to achieve 90%+ data completeness across all critical fields.

**Free data sources available:** All recommended sources are free (scraping or government APIs), no budget required.
