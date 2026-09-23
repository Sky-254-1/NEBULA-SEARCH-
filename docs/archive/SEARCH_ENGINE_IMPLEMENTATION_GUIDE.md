# Nebula Search Engine - Implementation Guide

## Overview

This document provides a comprehensive guide to the Nebula search engine implementation, covering all phases from audit to production deployment.

## Implementation Status

### ✅ Completed Phases

#### Phase 1: Search Engine Audit
**Status:** Complete  
**Deliverable:** `SEARCH_ENGINE_AUDIT.md`

**Findings:**
- Query Understanding Pipeline: Fully implemented
- Web Search Integration: Fully implemented
- Semantic Search Foundation: Partially implemented
- Search Orchestration: Partially implemented
- Search API Endpoints: Partially implemented
- AI Integration: Partially implemented

**Critical Gaps Identified:**
1. Document Ingestion Pipeline
2. Background Indexing
3. Incremental Re-indexing
4. Advanced Ranking Engine
5. Missing Intelligence Modules (verified existing)

### ✅ Phase 2: Robust Document Ingestion
**Status:** Complete  
**File:** `backend/app/search/ingestion.py`

**Features Implemented:**
- Multi-format support (TXT, MD, HTML, PDF, DOCX, JSON, CSV)
- Metadata extraction (title, author, source, dates, tags, categories)
- Content normalization and sanitization
- File validation (size limits, checksums)
- Error handling and status tracking
- Async file processing with aiofiles

**Key Classes:**
- `DocumentIngester`: Main ingestion pipeline
- `Document`: Document data structure
- `DocumentMetadata`: Metadata container
- `DocumentStatus`: Processing status enum
- `FileType`: Supported file types enum

**Usage:**
```python
from app.search.ingestion import document_ingester

# Ingest a file
document = await document_ingester.ingest_file("/path/to/document.pdf")

# Ingest content directly
document = await document_ingester.ingest_content(
    content="Your content here",
    filename="document.txt",
    metadata=DocumentMetadata(title="My Document")
)
```

### ✅ Phase 3: Background Indexing
**Status:** Complete  
**File:** `backend/app/search/indexing.py`

**Features Implemented:**
- Asynchronous job queue with priority support
- Multiple background workers (configurable)
- Retry mechanism with exponential backoff
- Progress tracking via cache
- Failure recovery
- Job cancellation support
- Statistics and monitoring

**Key Classes:**
- `BackgroundIndexer`: Core indexing engine
- `IndexingJob`: Job definition and tracking
- `IndexingManager`: High-level management API
- `JobStatus`: Job state enum
- `JobPriority`: Priority levels enum

**Usage:**
```python
from app.search.indexing import indexing_manager

# Start indexing system
await indexing_manager.start()

# Submit document for indexing
job = await indexing_manager.index_document(
    document_id="doc-123",
    priority=JobPriority.HIGH
)

# Check status
status = await indexing_manager.get_status(job.id)

# Stop indexing system
await indexing_manager.stop()
```

### ✅ Phase 4: Incremental Re-indexing
**Status:** Complete  
**File:** `backend/app/search/reindexing.py`

**Features Implemented:**
- Change detection via checksums
- Version tracking for documents
- Timestamp-based incremental updates
- Partial re-indexing (only changed documents)
- Full re-index capability
- Batch processing
- Task status tracking

**Key Classes:**
- `IncrementalReindexer`: Core re-indexing engine
- `DocumentVersion`: Version tracking
- `ReindexTask`: Task definition
- `ChangeType`: Change type enum
- `ReindexStatus`: Status enum

**Usage:**
```python
from app.search.reindexing import incremental_reindexer

# Detect changes in documents
changes = await incremental_reindexer.detect_changes(documents)

# Re-index changed documents
task = await incremental_reindexer.reindex_changes(changes)

# Full re-index
task = await incremental_reindexer.full_reindex()

# Check task status
status = await incremental_reindexer.get_task_status(task.id)
```

### ✅ Phase 5: High-Quality Ranking
**Status:** Complete  
**File:** `backend/app/search/ranking_service.py`

**Features Implemented:**
- BM25 scoring algorithm
- Freshness scoring with exponential decay
- Popularity scoring (views + CTR)
- Metadata quality scoring
- Personalization scoring
- Configurable feature weights
- Score normalization

**Key Classes:**
- `RankingService`: Main ranking engine
- `BM25Scorer`: BM25 implementation
- `FreshnessScorer`: Time-based scoring
- `PopularityScorer`: Engagement-based scoring
- `MetadataScorer`: Quality-based scoring
- `RankingConfig`: Configuration

**Usage:**
```python
from app.search.ranking_service import ranking_service

# Rank search results
ranked = await ranking_service.rank(
    query="machine learning",
    results=search_results,
    user_profile=user_profile
)

# Update popularity metrics
ranking_service.update_popularity_metrics(
    document_id="doc-123",
    views=150,
    click_through_rate=0.35
)
```

### ✅ Phase 6: Semantic Search
**Status:** Already Implemented  
**File:** `backend/app/search/semantic/engine.py`

**Features:**
- Multiple embedding providers (OpenAI, Cohere, HuggingFace, Ollama)
- Multiple vector stores (PGVector, Qdrant, Milvus, Elasticsearch)
- Document indexing with embeddings
- Semantic search with similarity thresholds
- Reranking with semantic similarity
- Cosine similarity calculation
- Caching support

### ✅ Phase 7: Hybrid Search
**Status:** Complete  
**File:** `backend/app/search/hybrid_search.py`

**Features Implemented:**
- Parallel web and vector search
- Score normalization across sources
- Intelligent result merging
- Configurable lexical/semantic weighting
- Deduplication
- Integration with ranking service
- Low-latency design

**Key Classes:**
- `HybridSearchEngine`: Main hybrid search engine

**Usage:**
```python
from app.search.hybrid_search import hybrid_search_engine

# Perform hybrid search
results = await hybrid_search_engine.search(
    query="artificial intelligence",
    db=database_connection,
    user_id=user_id,
    top_k=20
)

# Update weights
hybrid_search_engine.update_weights(
    lexical_weight=0.6,
    semantic_weight=0.4
)
```

### ✅ Phase 8: Autocomplete
**Status:** Already Implemented  
**File:** `backend/app/search/intelligence.py` (AutocompleteEngine class)

**Features:**
- Prefix matching using trie data structure
- Popular searches
- Recent searches
- Typo tolerance
- Ranked suggestions
- Caching

### ✅ Phase 9: Spell Correction
**Status:** Already Implemented  
**File:** `backend/app/search/intelligence.py` (SpellCorrector class)

**Features:**
- Edit distance algorithm
- Word frequency dictionary
- Context-aware correction
- "Did you mean" functionality
- Caching

### ✅ Phase 10: Query Suggestions
**Status:** Already Implemented  
**File:** `backend/app/search/intelligence.py` (QuerySuggestionEngine class)

**Features:**
- Autocomplete suggestions
- Spell-corrected versions
- User search history
- Trending queries
- Related searches
- Synonym expansion

### ✅ Phase 11: Search Analytics
**Status:** Already Implemented  
**File:** `backend/app/search/intelligence.py` (SearchAnalytics class)

**Features:**
- Search event logging
- Trending queries
- User search history
- Click-through rate calculation
- Popular queries
- Analytics caching

### ⚠️ Phase 12: Highlighted Search Snippets
**Status:** Basic Implementation  
**File:** `backend/app/routes/search_unified.py` (_highlight function)

**Current Implementation:**
- Simple keyword matching
- Basic snippet generation

**Enhancement Needed:**
- Context-aware snippets
- Multiple match handling
- Ellipsis trimming
- HTML-safe output
- Configurable snippet length

### ⚠️ Phase 13: Search API
**Status:** Partially Implemented  
**File:** `backend/app/routes/search_unified.py`

**Implemented Endpoints:**
- POST /api/v1/search/ - Unified search
- GET /api/v1/search/suggestions - Query suggestions
- GET /api/v1/search/autocomplete - Autocomplete
- GET /api/v1/search/history - Search history
- POST /api/v1/search/save - Save search
- GET /api/v1/search/saved - List saved searches
- DELETE /api/v1/search/saved/{id} - Delete saved search

**Missing Endpoints:**
- POST /api/v1/search/ingest - Document ingestion
- POST /api/v1/search/index - Index management
- GET /api/v1/search/analytics - Analytics dashboard
- GET /api/v1/search/index/status - Index status
- POST /api/v1/search/reindex - Re-index trigger

### ⏳ Phase 14: Performance
**Status:** Needs Implementation

**Required:**
- Redis caching for embeddings
- Connection pooling
- Query optimization
- Efficient pagination
- Performance monitoring

### ⏳ Phase 15: Testing
**Status:** Needs Implementation

**Required:**
- Unit tests for ingestion
- Unit tests for indexing
- Unit tests for re-indexing
- Unit tests for ranking
- Integration tests for search
- Performance tests
- Security tests

### ⏳ Phase 16: Documentation
**Status:** In Progress

**Completed:**
- SEARCH_ENGINE_AUDIT.md
- This implementation guide

**Required:**
- API documentation
- Architecture diagrams
- Deployment guide
- Performance tuning guide
- User manual

## Architecture

```
backend/app/search/
├── __init__.py
├── ingestion.py              # Document ingestion pipeline
├── indexing.py               # Background indexing system
├── reindexing.py             # Incremental re-indexing
├── ranking_service.py        # Advanced ranking engine
├── hybrid_search.py          # Hybrid search engine
├── orchestrator.py           # Search orchestration
├── search_service.py         # Unified search service
├── intelligence.py           # Autocomplete, spell correction, analytics
├── query_understanding/      # NLP pipeline
│   ├── pipeline.py
│   ├── language_detector.py
│   ├── normalizer.py
│   ├── tokenizer.py
│   ├── stemmer.py
│   ├── stopwords.py
│   ├── synonym_expander.py
│   ├── entity_extractor.py
│   ├── intent_classifier.py
│   └── query_processor.py
└── semantic/                 # Semantic search
    ├── engine.py
    ├── indexer.py
    ├── embeddings/           # Embedding providers
    └── vector_store/         # Vector store backends
```

## Integration Points

### 1. Document Ingestion → Indexing

```python
from app.search.ingestion import document_ingester
from app.search.indexing import indexing_manager

# Ingest document
document = await document_ingester.ingest_file("document.pdf")

# Queue for indexing
job = await indexing_manager.index_document(
    document_id=document.id,
    priority=JobPriority.HIGH
)
```

### 2. Indexing → Semantic Search

```python
from app.search.semantic.engine import semantic_engine

# In indexing worker
await semantic_engine.index_documents([{
    "id": document_id,
    "content": content,
    "metadata": metadata
}])
```

### 3. Search → Hybrid → Ranking

```python
from app.search.hybrid_search import hybrid_search_engine
from app.search.ranking_service import ranking_service

# Hybrid search
results = await hybrid_search_engine.search(query, db, user_id)

# Apply ranking
ranked = await ranking_service.rank(query, results, user_profile)
```

### 4. Query Processing → Search

```python
from app.search.query_understanding.pipeline import get_query_preprocessor

# Preprocess query
preprocessor = get_query_preprocessor()
processed = await preprocessor.process(query)

# Use expanded query for search
results = await search_service.search(
    query=processed.expanded_query,
    mode="hybrid"
)
```

## Configuration

### Environment Variables

```bash
# Search Configuration
SEARCH_MODE=hybrid  # web, vector, hybrid, ai
SEARCH_CACHE_TTL=3600
SEARCH_RESULTS_LIMIT=50

# Embedding Configuration
EMBEDDING_PROVIDER=openai  # openai, cohere, huggingface, ollama
EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_API_KEY=your-api-key

# Vector Store Configuration
VECTOR_STORE_BACKEND=pgvector  # pgvector, qdrant, milvus, elasticsearch
DATABASE_URL=postgresql://user:pass@localhost/db

# Indexing Configuration
INDEXING_WORKERS=4
INDEXING_QUEUE_SIZE=1000
INDEXING_BATCH_SIZE=100

# Ranking Configuration
RANKING_LEXICAL_WEIGHT=0.5
RANKING_SEMANTIC_WEIGHT=0.5
RANKING_FRESHNESS_HALF_LIFE=7
```

### Ranking Configuration

```python
from app.search.ranking_service import RankingConfig

config = RankingConfig(
    bm25_k1=1.5,
    bm25_b=0.75,
    keyword_weight=0.35,
    semantic_weight=0.25,
    freshness_weight=0.10,
    popularity_weight=0.10,
    personalization_weight=0.10,
    metadata_weight=0.10,
    freshness_half_life=7
)

ranking_service = RankingService(config)
```

## Deployment

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
# Apply migrations
alembic upgrade head

# Or use the provided script
./scripts/migrations.sh
```

### 3. Start Services

```bash
# Start Redis (for caching and job queue)
redis-server

# Start background indexer
python -c "from app.search.indexing import indexing_manager; import asyncio; asyncio.run(indexing_manager.start())"

# Start API server
uvicorn app.main:app --reload
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Test search
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "mode": "hybrid"}'
```

## Monitoring

### Key Metrics

1. **Search Performance**
   - Response time (p50, p95, p99)
   - Query throughput
   - Cache hit rate
   - Error rate

2. **Indexing Performance**
   - Queue size
   - Worker utilization
   - Job completion rate
   - Average indexing time

3. **Quality Metrics**
   - Zero-result search rate
   - Click-through rate
   - User satisfaction
   - Result relevance

### Health Checks

```python
# Search service health
from app.search.ranking_service import ranking_service
from app.search.hybrid_search import hybrid_search_engine
from app.search.indexing import indexing_manager

async def health_check():
    return {
        "ranking_service": ranking_service is not None,
        "hybrid_search": hybrid_search_engine is not None,
        "indexing": indexing_manager is not None,
        "queue_size": await indexing_manager.get_queue_size(),
    }
```

## Troubleshooting

### Common Issues

1. **Slow Search Performance**
   - Check cache hit rate
   - Verify vector store connection
   - Review ranking complexity
   - Check database query performance

2. **Indexing Failures**
   - Check worker logs
   - Verify embedding provider API keys
   - Check vector store capacity
   - Review error messages in job status

3. **Poor Search Results**
   - Adjust ranking weights
   - Review BM25 parameters
   - Check embedding quality
   - Verify query preprocessing

## Next Steps

1. **Immediate (Phase 14-16)**
   - Implement Redis caching for embeddings
   - Create comprehensive test suite
   - Complete API documentation
   - Performance optimization

2. **Short-term**
   - Add more embedding providers
   - Implement A/B testing framework
   - Add advanced filtering
   - Implement personalization engine

3. **Long-term**
   - Multi-tenancy support
   - Distributed indexing
   - Advanced ML ranking
   - Real-time indexing

## References

- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Vector Search Best Practices](https://docs.pinecone.io/guides/vector-search)
- [Semantic Search Guide](https://www.sbert.net/)
- [Elasticsearch Relevance](https://elastic.co/blog/understanding-relevance-score)

## Support

For issues and questions:
- Check documentation in `docs/`
- Review test files in `tests/`
- Consult audit report: `SEARCH_ENGINE_AUDIT.md`