"""Search suggestions and autocomplete API."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.indexing.inverted_index_builder import inverted_index_builder

logger = logging.getLogger("nebula.search.suggestions")
router = APIRouter(prefix="/suggestions", tags=["suggestions"])


class SuggestionResponse(BaseModel):
    """Autocomplete suggestion response."""
    suggestions: List[str]
    query: str


class ExpandedQueryResponse(BaseModel):
    """Expanded query response."""
    original_query: str
    expanded_terms: List[str]
    synonyms: List[str]


@router.get("/autocomplete", response_model=SuggestionResponse)
async def autocomplete(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
) -> SuggestionResponse:
    """
    Get autocomplete suggestions for a query prefix.
    
    Args:
        q: Query prefix
        limit: Maximum suggestions
        
    Returns:
        List of suggestions
    """
    try:
        suggestions = inverted_index_builder.get_suggestions(q, limit=limit)
        return SuggestionResponse(suggestions=suggestions, query=q)
    except Exception as exc:
        logger.error("Autocomplete failed: %s", exc)
        return SuggestionResponse(suggestions=[], query=q)


@router.get("/expand", response_model=ExpandedQueryResponse)
async def expand_query(
    q: str = Query(..., min_length=1, max_length=200),
) -> ExpandedQueryResponse:
    """
    Expand query with related terms and synonyms.
    
    Args:
        q: Query to expand
        
    Returns:
        Expanded query terms and synonyms
    """
    try:
        expanded = inverted_index_builder.get_expanded_query(q)
        
        # Get synonyms (simplified - would come from database in production)
        synonyms = []
        tokens = q.lower().split()
        for token in tokens:
            if token in inverted_index_builder._index:
                # Find related terms from co-occurrence
                docs = list(inverted_index_builder._index[token].keys())[:5]
                for doc_id in docs:
                    doc_tf = inverted_index_builder._term_frequencies.get(doc_id, {})
                    for term, freq in doc_tf.most_common(3):
                        if term != token and term not in synonyms:
                            synonyms.append(term)
        
        return ExpandedQueryResponse(
            original_query=q,
            expanded_terms=expanded,
            synonyms=synonyms[:10],
        )
    except Exception as exc:
        logger.error("Query expansion failed: %s", exc)
        return ExpandedQueryResponse(original_query=q, expanded_terms=q.split(), synonyms=[])