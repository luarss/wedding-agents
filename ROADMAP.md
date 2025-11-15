# Simplified MVP Architecture (No Vector DB, No Data Integration)

## Overview

This is a **radically simplified** MVP that removes the complex data infrastructure (Pinecone vector DB, GitHub sync, embeddings) and focuses on proving the core value proposition: **AI-powered wedding venue comparison**.

**Initial Scope**: Wedding venues ONLY (no photographers, caterers, makeup artists, etc.)

---

## What We're Removing

### ❌ Removed Components
1. **Vector Database (Pinecone)** - $70/month saved
2. **OpenAI Embeddings** - Reduced API costs
3. **GitHub Data Sync Module** - No automated syncing
4. **Data Integration Pipeline** - No ETL complexity
5. **ML Price Prediction Model** - Added in Phase 4, not MVP
6. **RAG (Retrieval-Augmented Generation)** - Semantic search removed

### ✅ What Stays
1. **CrewAI Multi-Agent System** - Core orchestration (3 agents only)
2. **Simple JSON Data** - Static venue files only
3. **FastAPI Backend** - API layer
4. **Next.js Frontend** - UI
5. **PostgreSQL** - User data only (profiles, bookings)
6. **LLM (GPT-4o)** - For agent intelligence

### 🎯 Ultra-Narrow MVP Focus
- **Only wedding venues** (banquet halls, hotels, restaurants)
- **Only 3 agents**: Venue Researcher, Budget Analyzer, Comparison Generator
- **No negotiation assistant** (Phase 2)
- **No timeline planner** (Phase 2)
- **No seating planner** (Phase 2)

---

## Simplified Architecture

```
┌─────────────────────────────────────────────────────┐
│                 User Interface Layer                 │
│              (Next.js + Shadcn/ui)                   │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│              API Gateway (FastAPI)                   │
│  - Request validation                                │
│  - Simple authentication                             │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│           Agent Orchestration Layer                  │
│              (CrewAI - 3 Agents Only)                │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │    Venue    │→ │   Budget     │→ │ Comparison │ │
│  │  Researcher │  │   Analyzer   │  │  Generator │ │
│  └─────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│               Simple Data Layer                      │
│                                                       │
│  ┌──────────────────────┐  ┌─────────────────────┐ │
│  │  Static JSON         │  │  PostgreSQL         │ │
│  │  (Venue Data ONLY)   │  │  (User Data)        │ │
│  │                      │  │                     │ │
│  │ - venues.json        │  │ - User profiles     │ │
│  │   (10-15 venues)     │  │ - Bookings          │ │
│  │                      │  │                     │ │
│  └──────────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## Simplified Data Approach

### Static Venue File

Instead of vector database + embeddings + GitHub sync, we use a **single JSON file** stored in the repo:

```
backend/data/
└── venues.json    # 10-15 wedding venues only
```

### Venue Data Schema (JSON)

**See `VENUE_SEARCH_FACTORS.md` for detailed research on what couples actually search for**

```json
{
  "venues": [
    {
      "id": "venue-001",
      "name": "The Clifford Pier",
      "venue_type": "restaurant",

      "pricing": {
        "price_per_table": 1200,
        "min_spend": 15000,
        "min_tables": 15
      },

      "capacity": {
        "min_tables": 15,
        "max_capacity": 200,
        "max_rounds": 20
      },

      "location": {
        "address": "80 Collyer Quay, The Fullerton Bay Hotel",
        "postal": "049326",
        "zone": "Central",
        "district": "Marina Bay",
        "nearest_mrt": "Raffles Place MRT",
        "mrt_distance": "5 min walk",
        "mrt_lines": ["NS", "EW"],
        "parking_lots": 200,
        "parking_cost": "$3/hr weekday"
      },

      "amenities": {
        "av_equipment": true,
        "bridal_suite": true,
        "in_house_catering": true,
        "outdoor_area": false,
        "air_conditioning": true,
        "valet_parking": true
      },

      "packages": [
        {
          "name": "Weekday Lunch",
          "price_per_table": 1000,
          "min_spend": 15000,
          "features": ["5-course menu", "Champagne toast", "Waterfront views", "In-house AV"]
        },
        {
          "name": "Weekend Dinner",
          "price_per_table": 1500,
          "min_spend": 25000,
          "features": ["7-course menu", "Premium wine pairing", "Extended venue hours"]
        }
      ],

      "description": "Iconic waterfront venue with heritage architecture and stunning Marina Bay views.",
      "reviews_summary": "Couples rave about the stunning location and excellent service.",
      "rating": 4.9,
      "review_count": 127,

      "restrictions": {
        "outside_catering": false,
        "decorations": "limited",
        "corkage": "not_allowed",
        "noise_curfew": "11pm"
      },

      "contact": {
        "email": "events@fullertonbayhotel.com",
        "phone": "+65 6597 5266",
        "website": "https://www.fullertonbayhotel.com"
      }
    }
  ]
}
```

**Phase 1 (MVP)**: Use static location data (manual entry)
**Phase 2**: Add OneMap API for geocoding and distance calculations (see `VENUE_SEARCH_FACTORS.md`)

### Simple Filtering Logic

Instead of semantic vector search, use **simple Python filtering**:

```python
import json

def search_venues(guest_count, budget, location=None):
    """Simple JSON filtering - no vector search needed"""
    with open('data/venues.json') as f:
        data = json.load(f)
        venues = data['venues']

    # Calculate budget per table (assuming 10 guests per table)
    tables_needed = (guest_count + 9) // 10
    budget_per_table = budget / tables_needed

    # Filter by capacity and budget
    filtered = [
        v for v in venues
        if v['max_capacity'] >= guest_count
        and v['min_tables'] <= tables_needed
        and v['price_per_table'] <= budget_per_table * 1.2  # 20% buffer
    ]

    # Optional location filter
    if location:
        filtered = [v for v in filtered if location.lower() in v['location'].lower()]

    # Sort by rating
    filtered = sorted(filtered, key=lambda x: x['rating'], reverse=True)

    return filtered[:5]  # Top 5
```

**Trade-off**:
- ❌ No semantic understanding ("I want a garden wedding" won't auto-match descriptions)
- ✅ But capacity/budget/location filtering works perfectly
- ✅ Much simpler, no external dependencies
- ✅ LLM can still match preferences from the filtered results

---

## Agent Changes

### Agent 1: Venue Researcher (Simplified)

**Old approach**: Vector similarity search with embeddings
```python
# ❌ Complex - requires Pinecone + embeddings
vectorstore.similarity_search(
    query="waterfront venue with garden",
    filter={"category": "venue", "capacity": {"$gte": 150}}
)
```

**New approach**: Direct JSON filtering + LLM to pick best matches
```python
# ✅ Simple - just JSON filtering
def research_venues(guest_count, budget, preferences):
    # 1. Load from JSON
    all_venues = load_venues_from_json()

    # 2. Filter by capacity and budget
    tables_needed = (guest_count + 9) // 10
    budget_per_table = budget / tables_needed

    filtered = [
        v for v in all_venues
        if v['max_capacity'] >= guest_count
        and v['price_per_table'] <= budget_per_table * 1.2
    ]

    # 3. Let LLM pick top matches based on preferences
    prompt = f"""
    From these {len(filtered)} venues, select the top 3-5 that best match:
    Guest count: {guest_count}
    Total budget: ${budget}
    Preferences: {preferences}

    Venues:
    {json.dumps(filtered, indent=2)}
    """

    # LLM does the "semantic" matching
    return llm.invoke(prompt)
```

**Why this works**:
- We only have 10-15 venues initially
- LLM can read all of them and intelligently match
- As we scale, we can add vector search later

---

## Simplified Tech Stack

### Removed Dependencies
```bash
# ❌ No longer needed
langchain-pinecone
pinecone-client
langchain          # Still use parts, but minimal
langchain-openai   # Just for GPT calls
apscheduler        # No automated sync
scikit-learn       # Phase 4, not MVP
```

### Minimal Dependencies
```bash
# ✅ MVP only - Venue comparison only
fastapi            # API framework
uvicorn            # Server
crewai             # Multi-agent orchestration
openai             # Direct GPT calls
pydantic           # Validation
sqlalchemy         # PostgreSQL ORM (optional for MVP)
python-jose        # JWT auth (optional for MVP)
```

**Even simpler for Week 1**: Just FastAPI + CrewAI + OpenAI

---

## Ultra-Simplified Workflow

### Phase 1: Venue Comparison Only (Week 1-2)

**Week 1: Core Agent System**
- [ ] Create `venues.json` with 10-15 Singapore wedding venues
  - Include location data: zone, MRT, parking (manual entry for now)
  - See `VENUE_SEARCH_FACTORS.md` for what couples actually care about
- [ ] Build simple `VenueService` class (loads JSON, filters by capacity/budget/location)
- [ ] Implement Agent 1 (Venue Researcher) - considers location accessibility
- [ ] Implement Agent 2 (Budget Analyzer) - Singapore venue pricing only
- [ ] Implement Agent 3 (Comparison Generator) - highlights location pros/cons
- [ ] Test full 3-agent crew workflow

**Week 2: API + Simple Frontend**
- [ ] FastAPI endpoint: `POST /api/venues/search`
  - Accept: guest_count, budget, location_preference (optional)
- [ ] Simple HTML/JavaScript form (skip Next.js initially)
- [ ] Display comparison results with location info
- [ ] Deploy to Railway/Render

**Success Criteria**:
- ✅ User can search venues by guest count + budget + location preference
- ✅ AI agents return top 3-5 venue recommendations
- ✅ Budget analysis shows per-table costs + Singapore surcharges
- ✅ Comparison mentions MRT proximity and parking
- ✅ < 30 seconds end-to-end

---

### Phase 2: Add Location Intelligence (Week 3)

**After MVP proves valuable**:
- [ ] Integrate OneMap API for geocoding
- [ ] Calculate actual MRT distances
- [ ] Add accessibility scoring
- [ ] Show venues on interactive map

See `VENUE_SEARCH_FACTORS.md` for implementation details.

---

### Phase 3: Expand Features (Week 4+)

**Only add if Phase 1 proves valuable**:
- [ ] Add negotiation assistant
- [ ] Add more vendor categories (photographers, etc.)
- [ ] Add timeline planner
- [ ] Add vector search if needed

---

## Data Management Strategy

### Initial Data Collection

**Recommended: Manual Entry (10-15 venues)**
- Focus on popular Singapore wedding venues
- Gather data from:
  - Venue websites
  - SingaporeBrides forum
  - Wedding blogs
  - Google reviews

**Example venues to research**:
- Hotels: Capella, Fullerton, Marina Bay Sands, Raffles
- Restaurants: Clifford Pier, Tung Lok, Lei Garden
- Unique: Gardens by the Bay, Sentosa venues, rooftop venues

### Updating Data

**Ultra-simple process**:
1. Edit `venues.json` directly
2. Commit to Git
3. Deploy updates

**No infrastructure needed** - just a JSON file

---

## Cost Savings

### Old Architecture (MVP)
- Railway Backend: $15/month
- PostgreSQL: $15/month
- Redis: $10/month
- OpenAI API: $50/month (embeddings + GPT)
- **Pinecone: $70/month** ❌
- **Total: $175/month**

### New Architecture (MVP)
- Railway Backend: $15/month
- PostgreSQL: $15/month
- OpenAI API: $30/month (GPT only, no embeddings)
- **Total: $60/month** ✅

**Savings: $115/month (66% reduction)**

---

## When to Add Vector DB Later

Add Pinecone/vector search when:

1. **Scale** - You have 200+ vendors per category
   - Passing all vendors to LLM becomes expensive
   - Need efficient filtering

2. **User feedback** - Users complain about search quality
   - "I searched for 'artistic colorful' but didn't find the right match"
   - Exact matching isn't good enough

3. **Revenue** - You're making money and can afford $70/month
   - Pinecone becomes a competitive advantage
   - Justifies the infrastructure cost

---

## Migration Path (Future)

When you're ready to add vector DB:

```python
# Step 1: Install dependencies
pip install langchain-pinecone pinecone-client langchain-openai

# Step 2: One-time migration
from langchain_community.document_loaders import JSONLoader
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Load existing JSON vendors
loader = JSONLoader('data/vendors/photographers.json')
docs = loader.load()

# Create embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Upload to Pinecone
vectorstore = PineconeVectorStore.from_documents(
    docs, embeddings, index_name="vendors"
)

# Step 3: Update Agent 1 to use vectorstore instead of JSON
```

The beauty of this approach: **You can add it incrementally without rewriting everything**.

---

## Implementation Example

### Simplified VenueService

```python
# backend/services/venue_service.py
import json
from pathlib import Path

class VenueService:
    """Simple venue data loader - no vector DB, no pandas"""

    def __init__(self):
        self.data_file = Path(__file__).parent.parent / 'data' / 'venues.json'

    def load_all_venues(self) -> list[dict]:
        """Load all venues from JSON"""
        with open(self.data_file) as f:
            data = json.load(f)
        return data['venues']

    def search(
        self,
        guest_count: int,
        total_budget: int,
        location: str = None
    ) -> list[dict]:
        """Filter venues by capacity, budget, and location"""
        venues = self.load_all_venues()

        # Calculate tables needed (10 guests per table)
        tables_needed = (guest_count + 9) // 10
        budget_per_table = total_budget / tables_needed

        # Filter by capacity and budget
        filtered = [
            v for v in venues
            if v['max_capacity'] >= guest_count
            and v['min_tables'] <= tables_needed
            and v['price_per_table'] <= budget_per_table * 1.2  # 20% buffer
        ]

        # Optional location filter
        if location:
            filtered = [v for v in filtered if location.lower() in v['location'].lower()]

        # Sort by rating
        filtered = sorted(filtered, key=lambda x: x['rating'], reverse=True)

        return filtered[:10]  # Top 10
```

### Simplified Agent 1: Venue Researcher

```python
# backend/agents/venue_researcher.py
from crewai import Agent, Task
from services.venue_service import VenueService

class VenueResearcher:
    """Simplified - uses JSON data, no vector search"""

    def __init__(self):
        self.venue_service = VenueService()

        self.agent = Agent(
            role="Singapore Wedding Venue Expert",
            goal="Find the best wedding venues matching couple's guest count, budget, and preferences",
            backstory="Expert in Singapore wedding venues with deep knowledge of pricing and amenities",
            tools=[self.search_venues_tool]
        )

    def search_venues_tool(self, guest_count: int, total_budget: int, location: str = None):
        """Tool that agent calls to search venues"""
        venues = self.venue_service.search(
            guest_count=guest_count,
            total_budget=total_budget,
            location=location
        )
        return venues

    def research(self, guest_count: int, total_budget: int, preferences: str, location: str = None) -> list[dict]:
        """Main research method"""
        task = Task(
            description=f"""
            Find top 3-5 wedding venues that match:
            - Guest count: {guest_count}
            - Total budget: ${total_budget}
            - Location preference: {location or 'Any'}
            - Preferences: {preferences}

            Use the search_venues_tool to get candidates, then select the best matches.
            Consider venue type, amenities, restrictions, and value for money.
            """,
            agent=self.agent,
            expected_output="List of 3-5 venue recommendations with reasoning"
        )

        return task.execute()
```

---

## Testing Strategy (Simplified)

### Unit Tests
```python
def test_venue_service_loads_data():
    service = VenueService()
    venues = service.load_all_venues()
    assert len(venues) >= 10
    assert all('venue_type' in v for v in venues)

def test_venue_service_filters_by_capacity():
    service = VenueService()
    venues = service.search(guest_count=150, total_budget=30000)
    for v in venues:
        assert v['max_capacity'] >= 150
```

---

## File Structure (Ultra-Minimal MVP)

```
wedding-agent/
├── backend/
│   ├── agents/
│   │   ├── venue_researcher.py       # Agent 1
│   │   ├── budget_analyzer.py        # Agent 2
│   │   └── comparison_generator.py   # Agent 3
│   ├── services/
│   │   └── venue_service.py          # Simple JSON loader
│   ├── api/
│   │   └── venues.py                 # Single endpoint
│   ├── data/
│   │   └── venues.json               # 10-15 venues
│   ├── main.py                       # FastAPI app
│   └── tests/
│       └── test_venue_service.py
├── frontend/                         # Week 2
│   └── index.html                    # Simple HTML form (or Next.js later)
├── pyproject.toml
└── README.md
```

---

## Success Metrics (Venue-Only MVP)

### Week 1 - Core Functionality
- ✅ `venues.json` with 10-15 Singapore wedding venues
- ✅ Venue search works with guest count + budget filtering
- ✅ 3 AI agents return 3-5 relevant venue recommendations
- ✅ Budget analysis shows per-table costs + Singapore surcharges (GST, service charge)
- ✅ < 30 seconds end-to-end search
- ✅ Comparison explains pros/cons of each venue

### Week 2 - API + Frontend
- ✅ FastAPI endpoint deployed and working
- ✅ Simple web form accepts user input
- ✅ Results display venue comparisons clearly
- ✅ Works on mobile (responsive)

### User Validation
- ✅ 5 beta users test the tool
- ✅ 3/5 say recommendations are helpful
- ✅ Users understand the comparison output

---

## Key Decisions

### ✅ What to Keep Simple
1. **Data storage** - JSON files, not vector DB
2. **Data updates** - Manual, not automated sync
3. **Search** - Filter then LLM match, not semantic embeddings
4. **Auth** - Simple JWT, not OAuth2
5. **Infrastructure** - Railway, not complex k8s

### 🎯 What to Get Right
1. **Agent orchestration** - This is the core value
2. **Singapore-specific logic** - Peak pricing, ROM requirements
3. **User experience** - Fast, clear, helpful
4. **Data quality** - Better to have 10 great vendors than 100 mediocre ones

---

## Timeline (2 Weeks to Venue MVP)

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | Core agents + venue data | `venues.json`, 3 agents, venue comparison working |
| 2 | API + Simple UI | FastAPI endpoint, HTML form, deployed to Railway |

**Then decide**: Does this prove value? If yes, expand. If no, pivot.

---

## FAQs

**Q: Won't search quality be bad without vector DB?**
A: Initially yes, but:
- You only have 10-20 vendors per category
- LLM can read all of them (cheap with GPT-4o mini)
- Exact/substring matching works for most queries
- Add vector search later if users complain

**Q: How do I update vendor data?**
A:
- Edit JSON files directly
- Commit to Git
- Redeploy (takes 2 minutes on Railway)
- Later: build admin panel for editing

**Q: What if I want to use the GitHub data repo?**
A:
- Pull one-time snapshot
- Convert CSVs to JSON
- No automated sync - manual updates monthly

**Q: When should I add vector DB?**
A:
- 200+ vendors per category (LLM context gets expensive)
- Users complain about search quality
- You have revenue to justify $70/month

---

## Next Steps

### Week 1 - Day 1
1. ✅ Create `backend/data/venues.json` with first 3 venues
2. ✅ Build `VenueService` class
3. ✅ Test loading and filtering

### Week 1 - Days 2-5
4. ✅ Build Agent 1 (Venue Researcher)
5. ✅ Build Agent 2 (Budget Analyzer)
6. ✅ Build Agent 3 (Comparison Generator)
7. ✅ Test full crew workflow

### Week 2
8. ✅ FastAPI endpoint
9. ✅ Simple HTML form
10. ✅ Deploy to Railway
11. ✅ Get 5 beta users to test

**The goal: Prove venue comparison is valuable in 2 weeks, then decide next steps.**
