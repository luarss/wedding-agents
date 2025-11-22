# Venue Enrichment V2 Architecture

## Overview

Version 2 of the venue enrichment system separates state management from MCP tools, enabling future parallelization with Redis job queues.

## Architecture Components

### 1. Models (`models.py`)

**Data models for serializable job state:**

- `SearchQuery`: Individual web search query with category and priority
- `VenueResearchJob`: Complete research task for one venue
  - Contains venue ID, search queries, status, enrichment data
  - Serializable to JSON for Redis storage
- `EnrichmentSession`: Session state tracking multiple jobs
  - Session ID, progress tracking, job list
  - Serializable to JSON for Redis storage

**Key Feature**: All models have `to_dict()` and `from_dict()` methods for easy serialization.

### 2. Service Layer (`enrichment_service.py`)

**`VenueEnrichmentService` - State management and business logic:**

- `create_enrichment_session()`: Identify venues needing enrichment, create jobs
- `create_research_job()`: Generate search queries for a single venue
- `update_venue_with_enrichment()`: Save enrichment results, recalculate confidence
- `get_enrichment_statistics()`: Report overall progress

**Separation of Concerns:**
- File I/O happens here (not in MCP tools)
- Confidence calculation logic here (not in MCP tools)
- State tracking here (not in MCP tools)

### 3. MCP Tools (`tools/enrich_tool_v2.py`)

**Stateless tools that delegate to service layer:**

- `create_enrichment_session`: Creates session, returns jobs
- `get_research_job`: Gets job for specific venue with search queries
- `update_venue_with_results`: Saves enrichment data
- `get_enrichment_statistics`: Gets overall stats

**Design Principles:**
- Tools are thin wrappers around service methods
- No file I/O in tools (delegates to service)
- No state stored in tools
- Returns job specifications that can be queued

### 4. Orchestration (`enrich_venues_v2.py`)

**Claude Agent SDK workflow:**

1. Create enrichment session (identifies all venues needing work)
2. For each venue:
   - Get research job (with search queries)
   - Execute parallel WebSearch calls
   - Extract enrichment data
   - Update venue
3. Generate final statistics

## Current Workflow: Sequential Processing

Currently, venues are processed one-by-one:

```
For venue in venues_needing_enrichment:
    1. get_research_job(venue_id) → returns 6 queries
    2. Execute 6 WebSearch calls in PARALLEL
    3. Extract data from search results
    4. update_venue_with_results(enrichment_data)
    5. Move to next venue
```

**Parallel searches within a venue** (Step 2) but **sequential venue processing**.

## Future: Redis-Based Parallelization

### Architecture with Redis

```
┌─────────────────────┐
│  Orchestrator       │
│  (enrich_venues.py) │
└──────────┬──────────┘
           │
           │ 1. Create session
           ▼
┌─────────────────────────┐
│  VenueEnrichmentService │
│  - Creates jobs         │
│  - Generates queries    │
└──────────┬──────────────┘
           │
           │ 2. Queue jobs
           ▼
┌─────────────────────────┐
│  Redis Queue            │
│  - Job 1: Venue A       │
│  - Job 2: Venue B       │
│  - Job 3: Venue C       │
└──────────┬──────────────┘
           │
           │ 3. Workers pull jobs
           ▼
┌──────────────────────────────────────┐
│  Worker 1    Worker 2    Worker 3    │
│  ────────    ────────    ────────    │
│  Process     Process     Process     │
│  Venue A     Venue B     Venue C     │
│                                       │
│  Each worker:                         │
│  - Gets job from queue                │
│  - Executes 6 parallel WebSearches    │
│  - Extracts enrichment data           │
│  - Calls update_venue_with_results    │
│  - Marks job complete                 │
└───────────────────────────────────────┘
```

### Implementation Steps

#### Step 1: Add Redis Client

```python
import redis
from rq import Queue

redis_conn = redis.Redis(host='localhost', port=6379)
job_queue = Queue('venue_enrichment', connection=redis_conn)
```

#### Step 2: Create Worker Function

```python
async def process_venue_research_job(job_dict: dict):
    """
    Worker function to process a single venue research job.
    This runs in a separate process/container.
    """
    # Deserialize job
    job = VenueResearchJob.from_dict(job_dict)

    # Execute search queries (can be parallel or sequential)
    search_results = {}
    for query in job.search_queries:
        result = await web_search(query.query)
        search_results[query.category] = result

    # Extract enrichment data (could use LLM here)
    enrichment_data = extract_enrichment_data(search_results)

    # Update venue
    service = VenueEnrichmentService(Path(job.venues_file))
    service.update_venue_with_enrichment(
        venue_id=job.venue_id,
        enrichment_data=enrichment_data
    )

    return job.venue_id
```

#### Step 3: Queue Jobs in Orchestrator

```python
# In enrich_venues_v2.py
async def enrich_venues_parallel(venues_file: Path, ...):
    service = VenueEnrichmentService(venues_file)
    session = service.create_enrichment_session(...)

    # Queue all jobs
    for job in session.jobs:
        job_queue.enqueue(
            process_venue_research_job,
            job.to_dict(),
            job_timeout='10m'
        )

    # Monitor progress
    while not all_jobs_complete():
        stats = service.get_enrichment_statistics()
        print(f"Progress: {stats['completed']}/{stats['total']}")
        await asyncio.sleep(5)
```

#### Step 4: Run Workers

```bash
# Terminal 1: Start Redis
docker run -p 6379:6379 redis

# Terminal 2-5: Start workers
rq worker venue_enrichment  # Worker 1
rq worker venue_enrichment  # Worker 2
rq worker venue_enrichment  # Worker 3
rq worker venue_enrichment  # Worker 4

# Terminal 6: Queue jobs
python backend/etl/enrich_venues_v2.py --parallel
```

### Benefits of Redis Parallelization

1. **Speed**: Process multiple venues simultaneously (4 workers = 4x faster)
2. **Scalability**: Add more workers as needed
3. **Resilience**: Failed jobs can be retried
4. **Observability**: Monitor queue depth, job status via Redis
5. **Cost control**: Rate limit API calls across workers

## Migration Path

### Current State (V1)
- State embedded in MCP tools
- Hard to parallelize
- Tools do file I/O

### V2 (Current Implementation)
- ✅ State in service layer
- ✅ Stateless MCP tools
- ✅ Sequential processing
- ✅ Ready for Redis integration

### V3 (Future with Redis)
- Queue jobs to Redis
- Workers pull and process jobs in parallel
- Same models and service layer (no changes needed!)

## Usage

### Current Sequential Processing

```bash
# Process all venues needing enrichment
python backend/etl/enrich_venues_v2.py

# Process first 10 venues only
python backend/etl/enrich_venues_v2.py --max-venues 10

# Interactive mode
python backend/etl/enrich_venues_v2.py --interactive
```

### Future Parallel Processing (with Redis)

```bash
# Queue all enrichment jobs
python backend/etl/enrich_venues_v2.py --parallel --workers 4

# Monitor progress
python backend/etl/monitor_enrichment.py

# Resume failed jobs
python backend/etl/enrich_venues_v2.py --retry-failed
```

## Key Design Decisions

### Why Separate State from Tools?

**Problem**: MCP tools with embedded state can't be parallelized:
- Each tool call processes one venue
- Next venue waits for previous to complete
- Can't distribute work across workers

**Solution**: Stateless tools + service layer:
- Tools return job specifications
- Jobs can be queued and distributed
- Workers execute jobs independently
- State managed centrally by service

### Why Sequential MCP Calls per Venue?

**Current**: Get job → Search → Update (3 MCP calls per venue)

This enables:
1. **Clear workflow**: Each step is explicit
2. **Redis compatibility**: Each step can be a separate job
3. **Debugging**: See exactly which step failed
4. **Flexibility**: Can modify workflow without changing tools

### Why Keep Parallel WebSearches?

Within each venue research job, we still execute 6 searches in parallel:
- Reduces latency per venue (30s vs 3min)
- Maximizes throughput
- Redis workers can also run these in parallel

## Files Changed

### New Files
- `backend/etl/models.py` - Data models
- `backend/etl/enrichment_service.py` - Service layer
- `backend/etl/tools/enrich_tool_v2.py` - Stateless tools
- `backend/etl/enrich_venues_v2.py` - V2 orchestration
- `backend/etl/prompts/enrichment_agent_prompt_v2.md` - Updated prompt

### Preserved Files (V1)
- `backend/etl/tools/enrich_tool.py` - Original implementation
- `backend/etl/enrich_venues.py` - Original orchestration
- `backend/etl/prompts/enrichment_agent_prompt.md` - Original prompt

Both V1 and V2 can coexist during transition.

## Testing

### Test Service Layer

```python
from backend.etl.enrichment_service import VenueEnrichmentService
from pathlib import Path

service = VenueEnrichmentService(Path("backend/data/venues.json"))

# Test session creation
session = service.create_enrichment_session(min_confidence=0.7)
print(f"Created {len(session.jobs)} jobs")

# Test job creation
venue = service.get_venue("venue-fullerton-hotel")
job = service.create_research_job(venue)
print(f"Generated {len(job.search_queries)} queries")

# Test update
service.update_venue_with_enrichment(
    venue_id="venue-fullerton-hotel",
    enrichment_data={"pricing": {"price_per_table": 2500}}
)
```

### Test Full Workflow

```bash
# Run V2 enrichment on test data
cp backend/data/venues.json backend/data/venues_test.json
python backend/etl/enrich_venues_v2.py backend/data/venues_test.json --max-venues 2
```

## Next Steps

1. ✅ Implement V2 architecture (done)
2. Test V2 with small dataset
3. Add Redis integration
4. Implement worker function
5. Add monitoring and retry logic
6. Performance testing with parallel workers
7. Migrate from V1 to V2 in production
