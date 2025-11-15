# Technical Implementation Plan: AI Wedding Vendor Coordinator for Singapore

## Executive Summary

**Product Vision**: An AI-powered vendor comparison and coordination platform that reduces 20+ hours of research to minutes while preventing S$10K-S$30K budget overruns for budget-conscious Singapore couples.

**Core Value Proposition**: Real-time vendor comparison with intelligent negotiation assistance and automated coordination across 10-15 vendors.

**Target Market**: Singapore couples planning weddings in the S$20K-S$30K budget range.

**Technical Approach**: Multi-agent system using CrewAI for orchestration, RAG for vendor matching, and LangGraph for workflow automation.

**Data Advantage**: Leverages curated vendor dataset from `luarss/wedding-data` GitHub repository.

**Timeline**: 6 weeks to MVP (reduced from 8 weeks due to existing data)

---

## Technology Stack

### Core Frameworks
- **Backend**: FastAPI (Python 3.10+)
- **Multi-Agent Orchestration**: CrewAI
- **Workflow Management**: LangGraph
- **LLM Provider**: OpenAI GPT-4o
- **Vector Database**: Pinecone (or ChromaDB for local dev)
- **Embeddings**: OpenAI text-embedding-3-small
- **RAG Framework**: LangChain
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Task Queue**: Celery
- **API Documentation**: FastAPI auto-generated (Swagger/OpenAPI)

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **UI Components**: Shadcn/ui
- **Forms**: React Hook Form + Zod validation
- **State Management**: React Query (TanStack Query)
- **Charts**: Recharts
- **Calendar**: FullCalendar or react-big-calendar

### Infrastructure
- **Backend Hosting**: Railway or Render
- **Frontend Hosting**: Vercel
- **Database**: Supabase or Railway managed PostgreSQL
- **Vector DB**: Pinecone Serverless (AWS us-east-1)
- **Monitoring**: Sentry (error tracking)
- **Analytics**: Posthog or Mixpanel

### Development Tools
- **Package Management**: Poetry (Python), pnpm (JavaScript)
- **Testing**: pytest, Jest, React Testing Library
- **Linting**: Ruff (Python), ESLint (TypeScript)
- **Type Checking**: mypy (Python), TypeScript
- **API Testing**: pytest-asyncio, httpx
- **Version Control**: Git + GitHub
- **CI/CD**: GitHub Actions

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                 User Interface Layer                 │
│    (Next.js + Shadcn/ui + React Hook Form)          │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│              API Gateway (FastAPI)                   │
│  - Authentication (JWT)                              │
│  - Rate limiting                                     │
│  - Request validation (Pydantic)                     │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│           Agent Orchestration Layer                  │
│              (CrewAI Multi-Agent)                    │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Vendor    │→ │   Budget     │→ │ Comparison │ │
│  │  Researcher │  │   Analyzer   │  │  Generator │ │
│  └─────────────┘  └──────────────┘  └────────────┘ │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Negotiation │  │   Timeline   │  │  Seating   │ │
│  │   Expert    │  │   Planner    │  │  Planner   │ │
│  └─────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│            Data & Knowledge Layer                    │
│                                                       │
│  ┌─────────────────┐      ┌─────────────────────┐  │
│  │  Vector DB      │      │  PostgreSQL         │  │
│  │  (Pinecone)     │      │  (Relational Data)  │  │
│  │                 │      │                     │  │
│  │ - Vendor docs   │      │ - User profiles     │  │
│  │ - Reviews       │      │ - Bookings          │  │
│  │ - Pricing       │      │ - Negotiations      │  │
│  └─────────────────┘      └─────────────────────┘  │
│                                                       │
│  ┌─────────────────────────────────────────────┐   │
│  │     GitHub Data Sync (luarss/wedding-data)   │   │
│  │     - Daily automated sync                    │   │
│  │     - Change detection via content hashing    │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Module Structure

```
wedding-ai-platform/
├── backend/
│   ├── agents/                    # CrewAI agent definitions
│   │   ├── vendor_researcher.py
│   │   ├── budget_analyzer.py
│   │   ├── comparison_generator.py
│   │   ├── negotiation_expert.py
│   │   ├── timeline_planner.py
│   │   └── seating_planner.py
│   ├── workflows/                 # LangGraph workflows
│   │   ├── vendor_search.py
│   │   ├── negotiation_flow.py
│   │   └── timeline_generation.py
│   ├── services/                  # Business logic layer
│   │   ├── vendor_service.py
│   │   ├── pricing_service.py
│   │   └── sync_service.py
│   ├── data/                      # Data layer
│   │   ├── github_loader.py
│   │   ├── vectorstore.py
│   │   └── quality_validator.py
│   ├── api/                       # API routes
│   │   ├── vendors.py
│   │   ├── negotiations.py
│   │   └── timeline.py
│   ├── models/                    # Pydantic models
│   └── tests/                     # Unit & integration tests
│       ├── test_agents/
│       ├── test_workflows/
│       └── test_api/
├── frontend/
│   ├── app/                       # Next.js app directory
│   │   ├── vendors/
│   │   ├── timeline/
│   │   └── seating/
│   ├── components/                # React components
│   │   ├── ui/                   # Shadcn components
│   │   ├── vendor-comparison/
│   │   ├── timeline-view/
│   │   └── seating-chart/
│   ├── lib/                       # Utilities
│   │   ├── api-client.ts
│   │   └── validators.ts
│   └── tests/
└── shared/
    ├── schemas/                   # Shared type definitions
    └── config/
```

---

## Phase 1: Smart Vendor Comparison Engine (Weeks 1-2)

### Objectives
Build AI agent system that aggregates vendor data from GitHub repository and provides intelligent, budget-aware comparisons across vendor categories.

### Key Components

#### 1.1 Data Integration Module
**Purpose**: Load and sync vendor data from `luarss/wedding-data` GitHub repository

**Libraries**:
- `pandas` - CSV processing
- `pydantic` - Data validation
- `requests` - GitHub API access
- `apscheduler` - Automated daily sync

**Key Classes**:
- `GitHubWeddingDataLoader` - Loads CSVs from repository
- `VendorSchemaValidator` - Validates data structure
- `AutomatedDataSync` - Daily sync with change detection
- `DataQualityValidator` - Validates completeness and quality

**Deliverables**:
- ✅ Load all vendor categories from GitHub repository
- ✅ Transform CSVs to standardized `Vendor` schema
- ✅ Automated daily sync with content hash-based change detection
- ✅ Data quality report (completeness %, issues, suggestions)
- ✅ ML-based pricing prediction for incomplete records

**Success Conditions**:
- All vendor categories load successfully (100% success rate)
- Data validation identifies 95%+ of quality issues
- Sync detects changes within 24 hours
- Schema validation catches malformed data before processing

**Testing Strategy**:
- Unit tests for each loader method
- Integration tests for full sync pipeline
- Mock GitHub responses for reproducible tests
- Validation tests with intentionally malformed data

---

#### 1.2 Vector Database Setup
**Purpose**: Create searchable knowledge base for vendor matching

**Libraries**:
- `langchain` - RAG framework
- `langchain-openai` - OpenAI embeddings
- `langchain-pinecone` - Pinecone integration
- `pinecone-client` - Vector database

**Key Components**:
- Vector index creation from GitHub data
- Rich document representations (vendor details + packages + reviews)
- Metadata filtering (category, price range, location, rating)
- Semantic search over vendor descriptions

**Deliverables**:
- ✅ Pinecone index populated with all vendors from GitHub
- ✅ Metadata filters for category, price, location, rating
- ✅ Document chunking optimized for retrieval (800 tokens, 100 overlap)
- ✅ Test queries validate search quality

**Success Conditions**:
- Search returns relevant vendors for 90%+ of test queries
- Metadata filtering works correctly (100% accuracy)
- Vector search latency < 500ms
- Embeddings created for all vendor records

**Testing Strategy**:
- Golden dataset of 20+ query-result pairs
- Precision/recall metrics for search quality
- Latency benchmarks
- Edge case testing (empty results, malformed queries)

---

#### 1.3 Multi-Agent System - Vendor Comparison
**Purpose**: Orchestrate three specialized agents to research, analyze, and compare vendors

**Libraries**:
- `crewai` - Multi-agent orchestration
- `langchain-openai` - GPT-4o integration

**Agents**:

**Agent 1: Vendor Researcher**
- **Role**: Search GitHub vendor database via RAG
- **Tools**: Vector similarity search with metadata filters
- **Input**: User requirements (category, budget, date, preferences)
- **Output**: 5-7 relevant vendors with pricing and packages
- **No web scraping** - GitHub data only

**Agent 2: Budget Analyzer**
- **Role**: Calculate realistic costs using historical data
- **Tools**: Historical price analysis, Singapore peak/off-peak calculator
- **Input**: Vendor quotes, wedding date
- **Output**: Total cost breakdown with Singapore-specific surcharges
- **Features**:
  - GST (9%) and service charge (10%) calculation
  - Peak month surcharges (Nov-Dec: +15-20%)
  - Weekend surcharges (+20%)
  - Hungry Ghost Month discounts (Aug: -15%)
  - Historical price percentile ranking
  - Budget warnings (monsoon, peak season, CNY)

**Agent 3: Comparison Generator**
- **Role**: Create actionable vendor comparisons
- **Input**: Researched vendors, cost analysis
- **Output**: Structured comparison report (top 3 recommendations, pros/cons, next steps)

**Deliverables**:
- ✅ Three specialized agents with defined roles and tools
- ✅ Sequential workflow: Research → Analyze → Compare
- ✅ Vendor comparison report in markdown format
- ✅ Historical price comparison from GitHub data
- ✅ Singapore peak/off-peak pricing heuristics

**Success Conditions**:
- Agent workflow completes in < 30 seconds
- Budget analysis accuracy within 10% of actual costs
- Comparison includes at least 3 vendors when available
- Recommendations match user budget 80%+ of the time

**Testing Strategy**:
- Unit tests for each agent independently
- Integration tests for full crew workflow
- Mock LLM responses for deterministic testing
- A/B testing different prompts for quality
- Real couple scenario testing (5+ test cases)

---

#### 1.4 FastAPI Backend
**Purpose**: REST API for frontend consumption

**Libraries**:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Request/response validation
- `python-jose` - JWT authentication
- `asyncpg` - PostgreSQL async driver

**Key Endpoints**:
- `POST /api/v1/vendors/search` - Vendor search and comparison
- `GET /api/v1/vendors/{id}` - Vendor details
- `POST /api/v1/vendors/submit` - Community vendor submission
- `GET /api/v1/health` - Health check

**Deliverables**:
- ✅ RESTful API with OpenAPI documentation
- ✅ Request validation via Pydantic models
- ✅ JWT authentication
- ✅ Rate limiting (100 requests/hour per user)
- ✅ CORS configuration for Next.js frontend
- ✅ Error handling with structured responses

**Success Conditions**:
- API response time < 2 seconds for vendor search
- 100% request validation coverage
- Authentication prevents unauthorized access
- Auto-generated API docs are accurate

**Testing Strategy**:
- pytest with async support
- API integration tests
- Authentication flow testing
- Rate limiting verification
- Load testing (100 concurrent requests)

---

#### 1.5 Next.js Frontend
**Purpose**: User interface for vendor search and comparison

**Libraries**:
- `next` - React framework
- `react-hook-form` - Form management
- `zod` - Schema validation
- `@tanstack/react-query` - Data fetching
- `shadcn/ui` - UI components

**Key Pages**:
- `/vendors/search` - Search form and results
- `/vendors/[id]` - Vendor detail page
- `/vendors/compare` - Side-by-side comparison

**Deliverables**:
- ✅ Vendor search form with filters (category, budget, date, location)
- ✅ Loading states during AI agent processing
- ✅ Comparison results display (top 3 cards)
- ✅ Side-by-side comparison table
- ✅ Mobile-responsive design
- ✅ Error handling with user-friendly messages

**Success Conditions**:
- Search form submits successfully
- Results display within 3 seconds of agent completion
- Comparison table shows all key attributes
- Mobile layout works on 320px+ screens
- No console errors

**Testing Strategy**:
- Jest + React Testing Library
- Component unit tests
- Integration tests with mocked API
- Accessibility testing (WCAG AA)
- Cross-browser testing (Chrome, Safari, Firefox)

---

### Phase 1 Success Metrics
- ✅ **Data Coverage**: 100+ vendors across 6+ categories from GitHub
- ✅ **Search Quality**: 90%+ relevant results for test queries
- ✅ **Performance**: < 30 seconds end-to-end vendor comparison
- ✅ **Cost Accuracy**: Budget analysis within 10% of actual costs
- ✅ **User Experience**: < 3 seconds to see results after agent processing

---

## Phase 2: Intelligent Negotiation Assistant (Weeks 3-4)

### Objectives
Build AI agent that helps couples negotiate better prices using Singapore-specific heuristics and market insights.

### Key Components

#### 2.1 Singapore Wedding Negotiation Heuristics
**Purpose**: Estimate negotiation opportunities without historical vendor flexibility data

**Libraries**:
- `numpy` - Statistical calculations
- `datetime` - Date-based logic

**Heuristic Rules**:

**Peak Season Patterns** (from research):
- **Peak months**: March, May, June, July, Sept, Nov, Dec (+15-20% surcharge)
- **Super peak**: Nov-Dec (+20-25% surcharge)
- **Off-peak**: Jan, Feb, Apr, Aug, Oct (-10-15% discount potential)
- **Hungry Ghost Month** (August): -15-20% discount potential

**Day of Week Patterns**:
- **Saturday**: Premium pricing (baseline)
- **Friday/Sunday**: -10-15% potential
- **Thursday**: -15-20% potential (sweet spot)
- **Mon-Wed**: -15-20% potential

**Vendor Category Flexibility**:
- Photographers: 5-15% discount potential
- Venues: 5-20% (significant weekday discounts)
- Caterers: 5-10% (less flexible)
- Makeup Artists: 10-20% (more flexible)

**Deliverables**:
- ✅ Negotiation strength calculator (0-1 score based on date)
- ✅ Discount potential estimator by category
- ✅ Leverage point identifier (off-peak, weekday, bundle, early booking)
- ✅ Optimal contact timing suggester
- ✅ Singapore-appropriate email template generator

**Success Conditions**:
- Negotiation strength score correlates with actual market conditions
- Email templates are culturally appropriate and polite
- Leverage points are accurate for given wedding dates
- Discount estimates are realistic (verified against 10+ real cases)

**Testing Strategy**:
- Test date scenarios across all months
- Verify peak/off-peak classifications
- Validate discount ranges against market research
- A/B test email templates for response rates

---

#### 2.2 Negotiation Strategy Generator
**Purpose**: Create personalized negotiation strategies for each vendor interaction

**Libraries**:
- `crewai` - Agent framework
- `langchain` - LLM integration

**Agent: Negotiation Expert**
- **Role**: Singapore wedding vendor negotiation specialist
- **Input**: Vendor quote, user budget, wedding date
- **Output**: Complete negotiation strategy

**Strategy Components**:
- Suggested ask price (realistic discount applied)
- 3-5 leverage points specific to the date/vendor
- Optimal contact timing recommendation
- Culturally-appropriate email template
- Alternative value-adds if price negotiation fails
- Confidence assessment (high/medium/low)

**Deliverables**:
- ✅ Negotiation strategy API endpoint
- ✅ Leverage point database (off-peak, weekday, bundle opportunities)
- ✅ Email template library (by vendor category)
- ✅ Alternative value-add suggestions (upgrades, extras, extended hours)
- ✅ Bundle deal optimizer (multi-vendor discounts)

**Success Conditions**:
- Strategies generate in < 5 seconds
- Email templates require minimal editing (user satisfaction > 80%)
- Suggested prices are within realistic negotiation range
- Leverage points are relevant to user's specific situation

**Testing Strategy**:
- Real couple feedback on email templates
- Simulate negotiations with various date/vendor combinations
- Validate against successful real negotiations
- User satisfaction surveys

---

#### 2.3 Bundle Deal Optimizer
**Purpose**: Identify opportunities for multi-vendor discounts

**Key Features**:
- Same-company service bundling (photo + video)
- Partner network discounts (vendors who commonly work together)
- Volume discount identification
- Early booking incentives

**Deliverables**:
- ✅ Bundle opportunity detector
- ✅ Estimated savings calculator for bundles
- ✅ Contact strategy for bundle requests

**Success Conditions**:
- Identifies bundle opportunities for 50%+ of vendor selections
- Savings estimates are realistic (5-15% for bundles)
- Suggestions are actionable

**Testing Strategy**:
- Test with real vendor combinations
- Verify partner networks exist
- Validate savings estimates

---

### Phase 2 Success Metrics
- ✅ **Strategy Generation**: < 5 seconds per negotiation strategy
- ✅ **Email Quality**: 80%+ user satisfaction with generated emails
- ✅ **Savings Potential**: Average S$500-S$2,000 in identified opportunities
- ✅ **Success Rate**: 30%+ of couples report successful negotiations using the tool
- ✅ **User Adoption**: 60%+ of users try negotiation feature

---

## Phase 3: Automated Timeline & Seating Planner (Weeks 5-6)

### Objectives
Build LangGraph-powered workflow system for wedding timeline generation based on SingaporeBrides 25-step checklist, plus intelligent seating arrangement planner.

### Key Components

#### 3.1 Singapore Wedding Timeline Generator
**Purpose**: Generate personalized planning timeline following Singapore wedding norms

**Libraries**:
- `langgraph` - Workflow orchestration
- `datetime` - Date calculations

**Checklist Structure** (from SingaporeBrides):

**Big Picture** (12-18 months before):
- Set budget & priorities
- Create guest list
- Choose venue
- Set wedding date

**Primary Vendors** (10-12 months):
- Book photographer
- Book videographer
- Select bridal boutique
- Book makeup artist

**Secondary Vendors** (6-9 months):
- Florist
- Decorator
- Entertainment (band/DJ/emcee)
- Wedding favors

**Details** (3-6 months):
- Wedding attire selection
- Invitations design & printing
- Plan gate-crash/tea ceremony
- Book hen's/stag parties

**Legal Requirements** (21+ days):
- File Notice of Marriage with ROM (MANDATORY)
- Submit documents to Registry of Marriages
- Verify documents

**Final Preparations** (1-3 months):
- Final venue meeting
- Final guest count to venue (2 weeks before)
- Write vows & speeches
- Confirm all vendors (1 week before)
- Pack wedding day essentials
- Delegate responsibilities to bridal party

**Deliverables**:
- ✅ 25-step checklist adapted to user's wedding date
- ✅ Dynamic deadline calculation based on months until wedding
- ✅ Task dependencies (e.g., can't book photographer until venue confirmed)
- ✅ Singapore-specific notes (ROM requirements, peak booking periods)
- ✅ Progress tracking (X% complete)
- ✅ Automated reminders for upcoming deadlines

**Success Conditions**:
- Timeline adapts correctly to any wedding date (tested 6-18 months out)
- All 25 milestones are generated with appropriate deadlines
- ROM filing reminder appears at correct time (21+ days before)
- Task dependencies prevent premature bookings
- Progress calculation is accurate

**Testing Strategy**:
- Test with various wedding dates (3 months, 6 months, 12 months, 18 months)
- Verify ROM deadline is never < 21 days
- Validate task ordering matches SingaporeBrides guide
- Check edge cases (wedding in < 3 months)

---

#### 3.2 Timeline Conflict Detection
**Purpose**: Identify scheduling conflicts and deadline clustering

**Features**:
- Overdue task detection
- Deadline clustering warnings (5+ tasks in same week)
- Vendor booking urgency alerts
- Milestone dependency validation

**Deliverables**:
- ✅ Conflict detection algorithm
- ✅ Notification system for warnings
- ✅ Suggested task redistributions
- ✅ Urgency scoring for tasks

**Success Conditions**:
- Detects all overdue tasks (100% accuracy)
- Identifies deadline clusters correctly
- Suggestions reduce clustering by 30%+

**Testing Strategy**:
- Create timelines with intentional conflicts
- Verify all conflicts are detected
- Test notification triggers

---

#### 3.3 Intelligent Seating Arrangement Planner
**Purpose**: Optimize wedding seating for 10-person round tables (Singapore standard)

**Libraries**:
- `networkx` - Graph algorithms for compatibility
- `numpy` - Optimization calculations

**Constraint Types**:
- **Hard constraints**:
  - Must sit together (families, couples)
  - Must separate (ex-partners, feuding relatives)
  - VIP placement (parents/grandparents near stage)
  - Table capacity (10 guests max per table in Singapore)

- **Soft constraints** (optimization goals):
  - Maximize comfort (guests sit with people they know)
  - Age group mixing (avoid all-elderly or all-children tables)
  - Language grouping (English, Mandarin, Malay, Tamil)
  - Dietary requirements (easier service)

**Algorithm Approach**:
1. Build compatibility graph (who knows whom)
2. Apply hard constraints first (VIPs, must-sit groups)
3. Use community detection (Louvain algorithm) to cluster compatible guests
4. Balance tables for age/language diversity
5. Calculate comfort scores (0-100) for each table
6. Provide improvement suggestions for low-comfort tables

**Deliverables**:
- ✅ Guest profile management (relationships, dietary needs, connections)
- ✅ Constraint definition interface (must-sit, must-separate, VIP status)
- ✅ Automated seating optimization algorithm
- ✅ Visual seating chart (interactive drag-and-drop)
- ✅ Comfort score per table (0-100)
- ✅ Improvement suggestions for problematic tables
- ✅ Export to PDF/Excel for venue

**Success Conditions**:
- Satisfies 100% of hard constraints (must-sit, must-separate, capacity)
- Achieves average comfort score > 70 for all tables
- Generates seating plan in < 10 seconds for 200 guests
- Identifies isolated guests (0 connections at table)
- Suggestions improve comfort scores by 10+ points

**Testing Strategy**:
- Test datasets: 50, 100, 200, 300 guests
- Edge cases: uneven guest counts, conflicting constraints
- Validate all hard constraints are satisfied
- Measure comfort score improvements
- Real couple feedback on seating quality

---

#### 3.4 Google Calendar Integration
**Purpose**: Sync timeline milestones to couple's calendar

**Libraries**:
- `google-auth` - OAuth2 authentication
- `google-api-python-client` - Calendar API

**Features**:
- Create dedicated wedding planning calendar
- Sync all milestones as calendar events
- Set reminders (1 week, 3 days before deadlines)
- Vendor meeting scheduling

**Deliverables**:
- ✅ OAuth2 flow for Google Calendar access
- ✅ Calendar creation and event syncing
- ✅ Automated reminder configuration
- ✅ Two-way sync (updates in calendar reflect in app)

**Success Conditions**:
- Successfully authenticates 95%+ of users
- All milestones sync to calendar correctly
- Reminders trigger at configured times
- Calendar updates propagate to app

**Testing Strategy**:
- Test OAuth flow with multiple Google accounts
- Verify event creation and updates
- Test reminder notifications
- Handle calendar API errors gracefully

---

### Phase 3 Success Metrics
- ✅ **Timeline Generation**: < 3 seconds to generate full 25-step checklist
- ✅ **Checklist Accuracy**: Matches SingaporeBrides guide (manual verification)
- ✅ **Seating Optimization**: Average comfort score > 70 across all tables
- ✅ **Constraint Satisfaction**: 100% of hard constraints honored
- ✅ **Calendar Sync**: 95%+ successful authentication and sync rate
- ✅ **User Satisfaction**: 80%+ find seating suggestions helpful

---

## Phase 4: Advanced Features & Polish (Weeks 7-8)

### Objectives
Add ML-powered features, monitoring, and production-ready polish.

### Key Components

#### 4.1 Price Prediction Model
**Purpose**: Predict realistic vendor pricing for incomplete data

**Libraries**:
- `scikit-learn` - Random Forest Regressor
- `pandas` - Feature engineering

**Features**:
- Feature engineering (category, date, guest count, package features)
- Train on historical GitHub data
- Predict price ranges with confidence intervals
- Identify overpriced vs good-deal vendors

**Deliverables**:
- ✅ Trained ML model (Random Forest)
- ✅ Price range predictions (low, expected, high)
- ✅ Confidence scores
- ✅ Model retraining pipeline

**Success Conditions**:
- R² score > 0.75 on test set
- Predictions within ±15% of actual prices
- Model updates monthly as new data arrives

**Testing Strategy**:
- Train/test split validation
- Cross-validation (5-fold)
- Compare predictions to real vendor quotes

---

#### 4.2 Real-time Availability Tracking
**Purpose**: Monitor vendor availability and alert couples when vendors become free

**Libraries**:
- `redis` - Caching
- `celery` - Background tasks

**Features**:
- Vendor availability watchlist
- Background monitoring (6-hour intervals)
- Email notifications when watched vendor becomes available
- Alternative date suggestions

**Deliverables**:
- ✅ Watchlist management API
- ✅ Background availability checker (Celery task)
- ✅ Notification system (email/SMS)
- ✅ Alternative date finder

**Success Conditions**:
- Checks run every 6 hours reliably
- Notifications sent within 1 hour of availability change
- Zero missed availability changes

**Testing Strategy**:
- Mock availability changes
- Test notification delivery
- Verify Celery task scheduling

---

#### 4.3 Budget Optimization Engine
**Purpose**: Suggest budget reallocations to meet goals

**Features**:
- Category allocation optimizer based on priorities
- Trade-off suggester (reduce X to afford Y)
- Impact descriptions (human-readable)
- Feasibility scoring for each suggestion

**Deliverables**:
- ✅ Budget allocation optimizer
- ✅ Trade-off calculator
- ✅ Impact descriptions
- ✅ Feasibility scoring

**Success Conditions**:
- Suggestions keep total within budget (100% accuracy)
- Trade-offs are actionable (user can implement them)
- Feasibility scores correlate with user feedback

**Testing Strategy**:
- Test various budget scenarios
- Verify math accuracy
- User testing for suggestion quality

---

#### 4.4 Analytics Dashboard
**Purpose**: Track wedding planning progress and health

**Metrics**:
- Budget health (on track vs over budget)
- Timeline status (% complete, overdue tasks)
- Vendor booking progress
- AI-generated recommendations

**Deliverables**:
- ✅ Dashboard page with key metrics
- ✅ Progress visualization (charts)
- ✅ Budget vs spending tracker
- ✅ Personalized recommendations

**Success Conditions**:
- Dashboard loads in < 2 seconds
- All metrics update in real-time
- Recommendations are actionable

**Testing Strategy**:
- Test with various planning states
- Verify metric calculations
- Performance testing

---

#### 4.5 Monitoring & Error Tracking
**Purpose**: Production monitoring and debugging

**Libraries**:
- `sentry-sdk` - Error tracking
- `prometheus-client` - Metrics
- `structlog` - Structured logging

**Deliverables**:
- ✅ Sentry integration for error tracking
- ✅ API performance monitoring
- ✅ LLM usage tracking (tokens, cost)
- ✅ User analytics (Posthog/Mixpanel)

**Success Conditions**:
- 100% of errors captured in Sentry
- API performance metrics tracked
- LLM costs monitored and alerted if exceeding budget

---

### Phase 4 Success Metrics
- ✅ **ML Accuracy**: Price predictions within ±15% of actual
- ✅ **Availability Monitoring**: Zero missed availability changes
- ✅ **Dashboard Performance**: < 2 second load time
- ✅ **Error Tracking**: 100% error capture rate
- ✅ **Cost Monitoring**: LLM costs stay within S$200/month budget

---

## Testing Strategy

### Unit Testing
**Framework**: pytest (Python), Jest (TypeScript)

**Coverage Targets**:
- Agent logic: 90%+ coverage
- API endpoints: 95%+ coverage
- Business logic: 90%+ coverage
- Utilities: 85%+ coverage

**Approach**:
- Mock external dependencies (LLM, database, APIs)
- Test edge cases and error conditions
- Parameterized tests for multiple scenarios

---

### Integration Testing
**Framework**: pytest-asyncio, React Testing Library

**Test Scenarios**:
- Full agent workflows (research → analyze → compare)
- API request/response cycles
- Database transactions
- Frontend-backend integration

**Approach**:
- Use test database
- Mock LLM responses for consistency
- Test realistic user flows

---

### End-to-End Testing
**Framework**: Playwright or Cypress

**User Flows**:
- Complete vendor search and comparison
- Negotiation strategy generation
- Timeline generation and sync
- Seating arrangement creation

**Approach**:
- Automated browser testing
- Real user journey simulation
- Cross-browser testing

---

### Performance Testing
**Tools**: Locust, Apache Bench

**Benchmarks**:
- API response time: < 2 seconds (p95)
- Vendor search: < 30 seconds end-to-end
- Concurrent users: 100 without degradation
- Vector search: < 500ms

---

### A/B Testing
**What to Test**:
- Agent prompt variations
- Email template effectiveness
- UI layouts for conversions
- Recommendation algorithms

**Tools**: Statsig, Optimizely, or custom feature flags

---

## Deployment Strategy

### Environment Setup
- **Development**: Local Docker Compose
- **Staging**: Railway/Render with test database
- **Production**: Railway/Render with production database

### CI/CD Pipeline (GitHub Actions)
1. Run linters (Ruff, ESLint)
2. Run type checkers (mypy, TypeScript)
3. Run unit tests
4. Run integration tests
5. Build Docker images
6. Deploy to staging (on merge to `develop`)
7. Deploy to production (on merge to `main`)

### Database Migrations
**Tool**: Alembic (SQLAlchemy migrations)

**Process**:
- Generate migration on schema changes
- Review migration SQL
- Test on staging first
- Apply to production with rollback plan

### Monitoring Checklist
- ✅ Sentry error tracking configured
- ✅ API performance monitoring active
- ✅ Database connection pooling optimized
- ✅ Rate limiting configured
- ✅ Cost alerts for LLM usage
- ✅ Backup strategy in place

---

## Cost Estimates

### MVP Monthly Costs (First 100 Users)
- Railway/Render Backend: S$15/month
- Vercel Frontend: S$0 (Hobby plan)
- PostgreSQL Database: S$15/month
- Redis Cache: S$10/month
- **OpenAI API (GPT-4o)**: S$50/month
  - ~1000 searches/month × 5 agent calls × S$0.01 per call
- **Pinecone Vector DB**: S$70/month (Starter plan)
- SendGrid Email: S$15/month
- **Total MVP**: ~S$175/month

### At Scale (1000 Users)
- Infrastructure: S$100/month
- OpenAI API: S$500/month (10× usage)
- Pinecone: S$70/month (same tier)
- Email: S$50/month
- **Total at 1000 users**: ~S$720/month

---

## Success Metrics (Overall)

### Technical Metrics
- ✅ API uptime: 99.5%+
- ✅ Average response time: < 2 seconds
- ✅ Error rate: < 1%
- ✅ Test coverage: > 85%
- ✅ Page load time: < 3 seconds

### Product Metrics
- ✅ Time saved per user: 20+ hours
- ✅ Average budget savings identified: S$1,500
- ✅ User satisfaction: 4.0+ / 5.0
- ✅ Feature adoption: 60%+ use negotiation tool
- ✅ Seating planner: 70%+ find it helpful

### Business Metrics
- ✅ User retention: 40%+ return after first search
- ✅ Vendor submission rate: 10+ per month
- ✅ Data quality: 90%+ vendor records complete
- ✅ Cost efficiency: < S$1 per active user

---

## Risk Mitigation

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM API rate limits | High | Implement caching, queue requests, use GPT-3.5 fallback |
| Vector search latency | Medium | Optimize chunk sizes, use Pinecone caching |
| GitHub data staleness | Low | Daily sync, manual update option |
| Database scaling | Medium | Connection pooling, read replicas |

### Product Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Low vendor data coverage | High | Community submissions, manual curation |
| Inaccurate price predictions | Medium | Display confidence intervals, validate regularly |
| Poor negotiation success rate | Low | A/B test email templates, gather feedback |
| Seating constraints too complex | Medium | Progressive disclosure, guided wizard |

---

## Next Steps

### Immediate (Week 1)
1. Set up development environment
2. Initialize Git repository
3. Configure CI/CD pipeline
4. Load initial vendor data from GitHub
5. Set up Pinecone vector database

### Short-term (Weeks 2-3)
1. Build and test Agent 1 (Vendor Researcher)
2. Build and test Agent 2 (Budget Analyzer)
3. Implement basic API endpoints
4. Create vendor search UI

### Medium-term (Weeks 4-6)
1. Complete Phase 2 (Negotiation Assistant)
2. Complete Phase 3 (Timeline & Seating)
3. End-to-end testing
4. Beta testing with 5-10 couples

### Long-term (Post-MVP)
1. Gather user feedback
2. Optimize agent prompts
3. Add more vendor categories
4. Build community features
5. Explore monetization (vendor leads, premium features)
