# Nebula Search Engine - Intelligent Search Implementation Plan

**Date:** 2026-07-06  
**Phase:** 2 - Intelligent Search Design  
**Status:** Ready for Implementation

---

## Executive Summary

This document provides the detailed implementation plan for integrating intelligent search capabilities into the existing Nebula Search Engine. The plan focuses on reusing existing code, extending functionality, and maintaining full backward compatibility.

**Implementation Strategy:**
- ✅ Reuse existing modules (synonym_expander, entity_extractor, intent_classifier)
- ✅ Extend existing services (search.py, ai.py)
- ✅ Add missing database tables
- ✅ Enhance existing APIs
- ✅ Maintain 100% backward compatibility

**Timeline:** 3-4 weeks for complete implementation  
**Risk Level:** Low (all changes are additive)

---

## Phase 2.1: Query Understanding Integration (Week 1)

### 2.1.1 Integrate Existing NLP Modules

**Current State:**
- Code exists in `backend/app/search/query_understanding/`
- Not integrated into search pipeline
- Modules are production-ready

**Implementation:**

#### Step 1: Create Query Preprocessing Pipeline

**File:** `backend/app/search/query_understanding/pipeline.py` (NEW)

```python
"""Query preprocessing pipeline for intelligent search."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.search.query_understanding.language_detector import LanguageDetector
from app.search.query_understanding.normalizer import Normalizer
from app.search.query_understanding.tokenizer import Tokenizer
from app.search.query_understanding.stemmer import Stemmer
from app.search.query_understanding.stopwords import StopwordRemover
from app.search.query_understanding.synonym_expander import SynonymExpander
from app.search.query_understanding.entity_extractor import EntityExtractor
from app.search.query_understanding.intent_classifier import IntentClassifier
from app.search.query_understanding.query_processor import QueryProcessor


class SearchIntent(str, Enum):
    """Search intent types."""
    INFORMATIONAL = "informational"
    NAVIGATIONAL = "navigational"
    TRANSACTIONAL = "transactional"
    COMPARISON = "comparison"
    LOCAL = "local"


@dataclass
class ProcessedQuery:
    """Processed query with all NLP enhancements."""
    original: str
    normalized: str
    tokens: List[str]
    stemmed: List[str]
    language: str
    intent: SearchIntent
    entities: List[Dict]
    synonyms: List[str]
    expanded_query: str
    filters: Dict


class QueryPreprocessor:
    """Query preprocessing pipeline."""
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self.normalizer = Normalizer()
        self.tokenizer = Tokenizer()
        self.stemmer = Stemmer()
        self.stopword_remover = StopwordRemover()
        self.synonym_expander = SynonymExpander()
        self.entity_extractor = EntityExtractor()
        self.intent_classifier = IntentClassifier()
        self.query_processor = QueryProcessor()
    
    async def process(self, query: str) -> ProcessedQuery:
        """Process query through full pipeline."""
        # 1. Language detection
        language = self.language_detector.detect(query)
        
        # 2. Normalization
        normalized = self.normalizer.normalize(query)
        
        # 3. Tokenization
        tokens = self.tokenizer.tokenize(normalized)
        
        # 4. Stopword removal
        filtered_tokens = self.stopword_remover.remove(tokens, language)
        
        # 5. Stemming
        stemmed = [self.stemmer.stem(token, language) for token in filtered_tokens]
        
        # 6. Entity extraction
        entities = self.entity_extractor.extract(normalized)
        
        # 7. Intent classification
        intent = self.intent_classifier.classify(normalized, entities)
        
        # 8. Synonym expansion
        synonyms = self.synonym_expander.expand(filtered_tokens, language)
        
        # 9. Query expansion
        expanded_query = self.query_processor.expand(
            normalized, synonyms, entities
        )
        
        # 10. Extract filters from entities
        filters = self._extract_filters(entities)
        
        return ProcessedQuery(
            original=query,
            normalized=normalized,
            tokens=filtered_tokens,
            stemmed=stemmed,
            language=language,
            intent=intent,
            entities=entities,
            synonyms=synonyms,
            expanded_query=expanded_query,
            filters=filters
        )
    
    def _extract_filters(self, entities: List[Dict]) -> Dict:
        """Extract search filters from entities."""
        filters = {}
        for entity in entities:
            entity_type = entity.get("type")
            entity_value = entity.get("value")
            
            if entity_type == "date":
                filters["date_range"] = entity_value
            elif entity_type == "location":
                filters["location"] = entity_value
            elif entity_type == "category":
                filters["category"] = entity_value
            elif entity_type == "file_type":
                filters["file_type"] = entity_value
        
        return filters
```

#### Step 2: Integrate into Search Orchestrator

**File:** `backend/app/search/orchestrator.py` (MODIFY)

```python
# Add to imports
from app.search.query_understanding.pipeline import QueryPreprocessor

# Add to SearchOrchestrator.__init__
self.query_preprocessor = QueryPreprocessor()

# Modify search method to use preprocessing
async def search(self, query: str, search_type: str = "hybrid", **kwargs):
    # Preprocess query
    processed = await self.query_preprocessor.process(query)
    
    # Use expanded query for search
    search_query = processed.expanded_query
    
    # Extract filters from query
    filters = {**kwargs.get("filters", {}), **processed.filters}
    
    # Route to appropriate search type
    if search_type == "keyword":
        results = await self.keyword_search(search_query, filters)
    elif search_type == "semantic":
        results = await self.semantic_search(search_query, filters)
    elif search_type == "vector":
        results = await self.vector_search(search_query, filters)
    else:  # hybrid
        results = await self.hybrid_search(search_query, filters)
    
    # Add metadata
    for result in results:
        result.metadata = {
            "intent": processed.intent.value,
            "language": processed.language,
            "entities": processed.entities
        }
    
    return results
```

### 2.1.2 Database Schema Updates

**File:** `database/migrations/004_add_search_intelligence.sql` (NEW)

```sql
-- Search history tracking
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    normalized_query TEXT,
    search_type VARCHAR(50),
    filters JSONB,
    results_count INTEGER,
    clicked_results JSONB,
    intent VARCHAR(50),
    language VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_search_history_user_id (user_id),
    INDEX idx_search_history_created_at (created_at)
);

-- Synonyms table
CREATE TABLE IF NOT EXISTS synonyms (
    id SERIAL PRIMARY KEY,
    term VARCHAR(255) NOT NULL,
    synonym VARCHAR(255) NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(term, synonym, language)
);

-- Entities table
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,
    entity_value TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entities_user_id (user_id),
    INDEX idx_entities_type (entity_type)
);

-- Personalization table
CREATE TABLE IF NOT EXISTS personalization (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    interests JSONB,
    preferred_categories JSONB,
    search_preferences JSONB,
    ranking_weights JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Search facets table
CREATE TABLE IF NOT EXISTS search_facets (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL,
    facet_name VARCHAR(100) NOT NULL,
    facet_value VARCHAR(255) NOT NULL,
    count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(query_hash, facet_name, facet_value)
);

-- Insert default synonyms
INSERT INTO synonyms (term, synonym, language) VALUES
    ('car', 'automobile', 'en'),
    ('car', 'vehicle', 'en'),
    ('phone', 'mobile', 'en'),
    ('phone', 'smartphone', 'en'),
    ('laptop', 'notebook', 'en'),
    ('laptop', 'computer', 'en'),
    ('buy', 'purchase', 'en'),
    ('cheap', 'affordable', 'en'),
    ('fast', 'quick', 'en'),
    ('big', 'large', 'en')
ON CONFLICT DO NOTHING;
```

---

## Phase 2.2: Enhanced Ranking Engine (Week 1-2)

### 2.2.1 ML-Based Ranking

**File:** `backend/app/search/ranking/ranker.py` (NEW)

```python
"""ML-based ranking engine for search results."""

from typing import List, Dict, Any
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.models.schemas import SearchResult


@dataclass
class RankingFeatures:
    """Features for ranking model."""
    bm25_score: float
    semantic_score: float
    vector_score: float
    recency: float
    popularity: float
    user_relevance: float
    personalization_score: float


class MLRanker:
    """Machine learning-based ranking engine."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.weights = {
            "bm25": 0.3,
            "semantic": 0.25,
            "vector": 0.25,
            "recency": 0.1,
            "popularity": 0.05,
            "personalization": 0.05
        }
    
    def rank(
        self,
        query: str,
        results: List[SearchResult],
        user_id: int = None,
        context: Dict = None
    ) -> List[SearchResult]:
        """Rank search results using ML model."""
        if not results:
            return results
        
        # Extract features
        features_list = []
        for result in results:
            features = self._extract_features(query, result, user_id, context)
            features_list.append(features)
        
        # Calculate scores
        scores = self._calculate_scores(features_list)
        
        # Sort by score
        ranked_results = sorted(
            zip(results, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Update result scores
        for i, (result, score) in enumerate(ranked_results):
            result.score = score
            result.rank = i + 1
        
        return [r for r, _ in ranked_results]
    
    def _extract_features(
        self,
        query: str,
        result: SearchResult,
        user_id: int,
        context: Dict
    ) -> RankingFeatures:
        """Extract ranking features."""
        return RankingFeatures(
            bm25_score=result.keyword_score or 0.0,
            semantic_score=result.semantic_score or 0.0,
            vector_score=result.vector_score or 0.0,
            recency=self._calculate_recency(result),
            popularity=self._calculate_popularity(result),
            user_relevance=self._calculate_user_relevance(result, user_id),
            personalization_score=self._calculate_personalization(result, user_id)
        )
    
    def _calculate_scores(self, features_list: List[RankingFeatures]) -> List[float]:
        """Calculate final ranking scores."""
        scores = []
        for features in features_list:
            score = (
                self.weights["bm25"] * features.bm25_score +
                self.weights["semantic"] * features.semantic_score +
                self.weights["vector"] * features.vector_score +
                self.weights["recency"] * features.recency +
                self.weights["popularity"] * features.popularity +
                self.weights["personalization"] * features.personalization_score
            )
            scores.append(score)
        
        # Normalize scores to 0-1
        if scores:
            max_score = max(scores)
            if max_score > 0:
                scores = [s / max_score for s in scores]
        
        return scores
    
    def _calculate_recency(self, result: SearchResult) -> float:
        """Calculate recency score (0-1)."""
        # Implementation depends on document metadata
        return 0.5
    
    def _calculate_popularity(self, result: SearchResult) -> float:
        """Calculate popularity score (0-1)."""
        # Implementation depends on click tracking
        return 0.5
    
    def _calculate_user_relevance(self, result: SearchResult, user_id: int) -> float:
        """Calculate user-specific relevance (0-1)."""
        # Implementation depends on user behavior
        return 0.5
    
    def _calculate_personalization(self, result: SearchResult, user_id: int) -> float:
        """Calculate personalization score (0-1)."""
        # Implementation depends on user preferences
        return 0.5
```

### 2.2.2 Personalization Engine

**File:** `backend/app/search/personalization/engine.py` (NEW)

```python
"""Personalization engine for search results."""

from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.database.repositories.user import UserRepository
from app.database.repositories.search_history import SearchHistoryRepository


class PersonalizationEngine:
    """User personalization engine."""
    
    def __init__(self):
        self.user_repo = UserRepository
        self.history_repo = SearchHistoryRepository
    
    async def get_user_interests(self, user_id: int, db) -> List[str]:
        """Get user interests based on search history."""
        # Get last 100 searches
        history = await self.history_repo.get_recent_searches(db, user_id, limit=100)
        
        # Extract categories from queries
        interests = {}
        for entry in history:
            query = entry["query"]
            # Extract categories from query
            categories = self._extract_categories(query)
            for category in categories:
                interests[category] = interests.get(category, 0) + 1
        
        # Sort by frequency
        sorted_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)
        return [interest[0] for interest in sorted_interests[:10]]
    
    async def get_personalized_weights(self, user_id: int, db) -> Dict[str, float]:
        """Get personalized ranking weights."""
        interests = await self.get_user_interests(user_id, db)
        
        # Adjust weights based on user interests
        weights = {
            "bm25": 0.3,
            "semantic": 0.25,
            "vector": 0.25,
            "recency": 0.1,
            "popularity": 0.05,
            "personalization": 0.05
        }
        
        # If user has strong interests, increase personalization weight
        if len(interests) > 5:
            weights["personalization"] = 0.15
            weights["bm25"] = 0.25
            weights["semantic"] = 0.2
            weights["vector"] = 0.2
        
        return weights
    
    def _extract_categories(self, query: str) -> List[str]:
        """Extract categories from query."""
        # Implementation depends on entity extraction
        return []
    
    async def track_search(self, user_id: int, query: str, results: List[Dict], db):
        """Track user search for personalization."""
        await self.history_repo.create(db, user_id, query, results)
```

---

## Phase 2.3: Enhanced Analytics (Week 2)

### 2.3.1 Search Quality Metrics

**File:** `backend/app/analytics/quality_metrics.py` (NEW)

```python
"""Search quality metrics calculator."""

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class SearchQualityMetrics:
    """Search quality metrics."""
    precision_at_5: float
    precision_at_10: float
    recall: float
    f1_score: float
    mrr: float  # Mean Reciprocal Rank
    ndcg: float  # Normalized Discounted Cumulative Gain
    click_through_rate: float
    average_click_position: float


class QualityMetricsCalculator:
    """Calculate search quality metrics."""
    
    def calculate(
        self,
        query: str,
        results: List[Dict],
        clicked_results: List[int],
        relevant_docs: List[int]
    ) -> SearchQualityMetrics:
        """Calculate quality metrics for a search."""
        if not results:
            return SearchQualityMetrics(0, 0, 0, 0, 0, 0, 0, 0)
        
        # Precision@K
        precision_5 = self._precision_at_k(results, clicked_results, 5)
        precision_10 = self._precision_at_k(results, clicked_results, 10)
        
        # Recall
        recall = self._recall(results, relevant_docs)
        
        # F1 Score
        f1 = 2 * (precision_10 * recall) / (precision_10 + recall) if (precision_10 + recall) > 0 else 0
        
        # MRR
        mrr = self._mrr(results, clicked_results)
        
        # NDCG
        ndcg = self._ndcg(results, clicked_results)
        
        # CTR
        ctr = len(clicked_results) / len(results) if results else 0
        
        # Average click position
        avg_click_pos = sum(clicked_results) / len(clicked_results) if clicked_results else 0
        
        return SearchQualityMetrics(
            precision_at_5=precision_5,
            precision_at_10=precision_10,
            recall=recall,
            f1_score=f1,
            mrr=mrr,
            ndcg=ndcg,
            click_through_rate=ctr,
            average_click_position=avg_click_pos
        )
    
    def _precision_at_k(self, results: List[Dict], clicked: List[int], k: int) -> float:
        """Calculate precision@k."""
        if not results or k == 0:
            return 0.0
        
        top_k = results[:k]
        relevant_in_top_k = sum(1 for r in top_k if r["id"] in clicked)
        return relevant_in_top_k / k
    
    def _recall(self, results: List[Dict], relevant: List[int]) -> float:
        """Calculate recall."""
        if not relevant:
            return 0.0
        
        result_ids = {r["id"] for r in results}
        relevant_found = sum(1 for r_id in relevant if r_id in result_ids)
        return relevant_found / len(relevant)
    
    def _mrr(self, results: List[Dict], clicked: List[int]) -> float:
        """Calculate Mean Reciprocal Rank."""
        if not clicked or not results:
            return 0.0
        
        # Find first clicked result
        for i, result in enumerate(results):
            if result["id"] in clicked:
                return 1.0 / (i + 1)
        
        return 0.0
    
    def _ndcg(self, results: List[Dict], clicked: List[int]) -> float:
        """Calculate Normalized Discounted Cumulative Gain."""
        if not results or not clicked:
            return 0.0
        
        # Calculate DCG
        dcg = 0.0
        for i, result in enumerate(results):
            if result["id"] in clicked:
                dcg += 1.0 / np.log2(i + 2)  # i+2 because log2(1) = 0
        
        # Calculate IDCG (ideal DCG)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(clicked), len(results))))
        
        return dcg / idcg if idcg > 0 else 0.0
```

---

## Phase 2.4: Performance Optimization (Week 2-3)

### 2.4.1 Query Performance Monitoring

**File:** `backend/app/monitoring/query_monitor.py` (NEW)

```python
"""Query performance monitoring."""

import time
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QueryMetrics:
    """Query performance metrics."""
    query: str
    execution_time: float
    timestamp: datetime
    user_id: int
    search_type: str
    result_count: int
    cache_hit: bool


class QueryMonitor:
    """Monitor query performance."""
    
    def __init__(self):
        self.metrics: List[QueryMetrics] = []
        self.slow_query_threshold = 0.2  # 200ms
    
    async def track_query(
        self,
        query: str,
        user_id: int,
        search_type: str,
        execution_time: float,
        result_count: int,
        cache_hit: bool
    ):
        """Track query execution."""
        metric = QueryMetrics(
            query=query,
            execution_time=execution_time,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            search_type=search_type,
            result_count=result_count,
            cache_hit=cache_hit
        )
        
        self.metrics.append(metric)
        
        # Alert on slow queries
        if execution_time > self.slow_query_threshold:
            await self._alert_slow_query(metric)
    
    async def _alert_slow_query(self, metric: QueryMetrics):
        """Alert on slow query."""
        # Implementation: log, send alert, etc.
        pass
    
    def get_stats(self, last_hours: int = 24) -> Dict:
        """Get query statistics."""
        cutoff = datetime.utcnow() - timedelta(hours=last_hours)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff]
        
        if not recent_metrics:
            return {}
        
        execution_times = [m.execution_time for m in recent_metrics]
        
        return {
            "total_queries": len(recent_metrics),
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "p95_execution_time": sorted(execution_times)[int(len(execution_times) * 0.95)],
            "p99_execution_time": sorted(execution_times)[int(len(execution_times) * 0.99)],
            "cache_hit_ratio": sum(1 for m in recent_metrics if m.cache_hit) / len(recent_metrics),
            "slow_queries": sum(1 for m in recent_metrics if m.execution_time > self.slow_query_threshold)
        }
```

### 2.4.2 Cache Warming

**File:** `backend/app/services/cache.py` (MODIFY)

```python
# Add to CacheService class

async def warm_cache(self, keys: List[str], ttl: int = 300):
    """Pre-warm cache with frequently accessed data."""
    for key in keys:
        # Check if already cached
        if await self.get(key):
            continue
        
        # Load from database
        data = await self._load_from_db(key)
        if data:
            await self.set(key, data, ttl)

async def _load_from_db(self, key: str) -> Any:
    """Load data from database for cache warming."""
    # Implementation depends on key pattern
    pass

async def get_or_set(self, key: str, factory, ttl: int = 300):
    """Get from cache or compute and cache."""
    # Try cache first
    cached = await self.get(key)
    if cached is not None:
        return cached
    
    # Compute value
    value = await factory()
    
    # Cache it
    await self.set(key, value, ttl)
    
    return value
```

---

## Phase 2.5: Frontend UI Enhancements (Week 3)

### 2.5.1 Faceted Search Component

**File:** `frontend/src/components/FacetedSearch.jsx` (NEW)

```jsx
import React, { useState, useEffect } from 'react';

const FacetedSearch = ({ facets, onFilterChange }) => {
  const [selectedFilters, setSelectedFilters] = useState({});

  const handleFilterChange = (facetName, value) => {
    const newFilters = { ...selectedFilters };
    
    if (selectedFilters[facetName]?.includes(value)) {
      newFilters[facetName] = selectedFilters[facetName].filter(v => v !== value);
    } else {
      newFilters[facetName] = [...(selectedFilters[facetName] || []), value];
    }
    
    setSelectedFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="faceted-search">
      <h3>Filters</h3>
      
      {facets.map(facet => (
        <div key={facet.name} className="facet">
          <h4>{facet.name}</h4>
          {facet.values.map(value => (
            <label key={value.value}>
              <input
                type="checkbox"
                checked={selectedFilters[facet.name]?.includes(value.value) || false}
                onChange={() => handleFilterChange(facet.name, value.value)}
              />
              {value.value} ({value.count})
            </label>
          ))}
        </div>
      ))}
    </div>
  );
};

export default FacetedSearch;
```

### 2.5.2 Search History Component

**File:** `frontend/src/components/SearchHistory.jsx` (NEW)

```jsx
import React, { useState, useEffect } from 'react';

const SearchHistory = ({ userId, onSearchClick }) => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchSearchHistory();
  }, [userId]);

  const fetchSearchHistory = async () => {
    const response = await fetch(`/api/v1/features/search-history?user_id=${userId}`);
    const data = await response.json();
    setHistory(data.history);
  };

  return (
    <div className="search-history">
      <h3>Recent Searches</h3>
      <ul>
        {history.map(entry => (
          <li key={entry.id} onClick={() => onSearchClick(entry.query)}>
            {entry.query}
            <span className="timestamp">
              {new Date(entry.created_at).toLocaleDateString()}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SearchHistory;
```

---

## Phase 2.6: Testing & Validation (Week 3-4)

### 2.6.1 Unit Tests

**File:** `backend/tests/unit/test_query_preprocessor.py` (NEW)

```python
import pytest
from app.search.query_understanding.pipeline import QueryPreprocessor


@pytest.fixture
def preprocessor():
    return QueryPreprocessor()


@pytest.mark.asyncio
async def test_query_preprocessing(preprocessor):
    """Test query preprocessing pipeline."""
    result = await preprocessor.process("artificial intelligence")
    
    assert result.original == "artificial intelligence"
    assert result.language == "en"
    assert len(result.tokens) > 0
    assert result.intent is not None


@pytest.mark.asyncio
async def test_entity_extraction(preprocessor):
    """Test entity extraction."""
    result = await preprocessor.process("Python programming in New York")
    
    assert len(result.entities) > 0
    entity_types = [e["type"] for e in result.entities]
    assert "location" in entity_types or "technology" in entity_types


@pytest.mark.asyncio
async def test_synonym_expansion(preprocessor):
    """Test synonym expansion."""
    result = await preprocessor.process("buy car")
    
    assert "automobile" in result.synonyms or "vehicle" in result.synonyms
```

### 2.6.2 Integration Tests

**File:** `backend/tests/integration/test_search_integration.py` (NEW)

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_hybrid_search_with_preprocessing(client):
    """Test hybrid search with query preprocessing."""
    response = client.post(
        "/api/v1/search",
        json={
            "query": "artificial intelligence",
            "type": "hybrid"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "metadata" in data
    assert data["metadata"]["intent"] is not None


def test_search_with_synonyms(client):
    """Test search with synonym expansion."""
    response = client.post(
        "/api/v1/search",
        json={
            "query": "buy automobile",
            "type": "hybrid"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) > 0
```

---

## Implementation Checklist

### Week 1: Query Understanding
- [ ] Create query preprocessing pipeline
- [ ] Integrate synonym expander
- [ ] Integrate entity extractor
- [ ] Integrate intent classifier
- [ ] Update search orchestrator
- [ ] Add database migrations
- [ ] Write unit tests

### Week 2: Ranking & Analytics
- [ ] Implement ML-based ranking
- [ ] Add personalization engine
- [ ] Create quality metrics calculator
- [ ] Add query performance monitoring
- [ ] Implement cache warming
- [ ] Write unit tests

### Week 3: UI & Integration
- [ ] Create faceted search component
- [ ] Create search history component
- [ ] Add search filters UI
- [ ] Integrate all components
- [ ] Run integration tests

### Week 4: Testing & Validation
- [ ] Run full test suite
- [ ] Performance testing
- [ ] Security testing
- [ ] Documentation updates
- [ ] Deployment preparation

---

## Success Criteria

### Functional Requirements
- ✅ All existing features work (100% backward compatibility)
- ✅ Query understanding integrated (synonyms, entities, intent)
- ✅ ML-based ranking implemented
- ✅ Personalization working
- ✅ Analytics enhanced
- ✅ Performance optimized

### Performance Requirements
- ✅ Search latency <200ms (p95)
- ✅ Throughput >1,000 RPS
- ✅ Cache hit ratio >70%
- ✅ No memory leaks

### Quality Requirements
- ✅ Test coverage >80%
- ✅ All tests passing
- ✅ No security vulnerabilities
- ✅ Documentation complete

---

## Risk Mitigation

### Low Risk Items
- Query understanding integration (code exists)
- Analytics enhancements (additive changes)
- UI enhancements (new components)

### Medium Risk Items
- ML-based ranking (requires testing)
- Personalization (requires user data)

### Mitigation Strategies
- Feature flags for gradual rollout
- A/B testing for ranking algorithms
- Comprehensive testing before deployment
- Rollback plan for each feature

---

## Next Steps

1. **Review this plan** with team
2. **Prioritize features** based on business value
3. **Create feature branches** for each phase
4. **Begin implementation** with query understanding
5. **Test continuously** throughout development
6. **Deploy to staging** for validation
7. **Monitor production** after deployment

---

**Status:** Phase 2 Design Complete - Ready for Implementation

**Next Document:** Implementation progress will be tracked in NEBULA_IMPLEMENTATION_STATUS.md