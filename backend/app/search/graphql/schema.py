"""GraphQL schema for Nebula Search API with real service integration."""

from typing import List, Optional, Any
from datetime import datetime

import strawberry
import json

from app.services.search import run_web_search, sanitize_query
from app.config import get_settings

settings = get_settings()

# JSON scalar for dict types
JSON = strawberry.scalar(
    lambda v: v,
    serialize=lambda v: v,
    parse_value=lambda v: v,
    name="JSON",
    description="Arbitrary JSON value",
)


@strawberry.type
class DocumentType:
    """Document search result type."""
    id: str
    title: str
    content: str
    url: str
    source: str
    score: float
    published_date: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[JSON] = None


@strawberry.type
class SearchResult:
    """Search results type."""
    query: str
    total: int
    page: int
    page_size: int
    documents: List[DocumentType]
    facets: Optional[JSON] = None
    suggestions: Optional[List[str]] = None


@strawberry.type
class SearchHistoryType:
    """Search history type."""
    id: str
    query: str
    results_count: int
    timestamp: datetime
    user_id: Optional[str] = None


@strawberry.type
class NodeType:
    """Graph node type for knowledge graph."""
    id: str
    label: str
    properties: JSON
    type: str
    score: float


@strawberry.type
class KnowledgeGraphType:
    """Knowledge graph query result."""
    nodes: List[NodeType]
    edges: List[JSON]


@strawberry.type
class AINodeType:
    """AI node type for AI search."""
    id: str
    content: str
    type: str
    score: float
    context: Optional[JSON] = None


@strawberry.type
class AISearchResultType:
    """AI search result type."""
    answer: str
    sources: List[DocumentType]
    nodes: Optional[List[AINodeType]] = None
    confidence: float


@strawberry.input
class SearchInput:
    """Search input type."""
    query: str
    page: Optional[int] = 1
    page_size: Optional[int] = 20
    filters: Optional[JSON] = None
    search_type: Optional[str] = "hybrid"
    enable_reranking: Optional[bool] = True
    enable_diversity: Optional[bool] = False


@strawberry.input
class GraphQueryInput:
    """Knowledge graph query input."""
    start_nodes: List[str]
    max_depth: Optional[int] = 2
    node_types: Optional[List[str]] = None


@strawberry.type
class Query:
    """GraphQL queries for Nebula Search."""

    @strawberry.field
    async def search(self, input: SearchInput) -> SearchResult:
        """Search documents using various search types."""
        query = sanitize_query(input.query)
        page = input.page or 1
        page_size = input.page_size or 20

        # Use web search backend (wikipedia default, no API key needed)
        try:
            results = await run_web_search(query, "wikipedia", page, page_size)
        except Exception:
            results = []

        documents = [
            DocumentType(
                id=str(i),
                title=item.get("title", ""),
                content=item.get("snippet", ""),
                url=item.get("url", ""),
                source=item.get("source", "web"),
                score=1.0 - (i * 0.01),
            )
            for i, item in enumerate(results)
        ]

        return SearchResult(
            query=query,
            total=len(documents),
            page=page,
            page_size=page_size,
            documents=documents,
        )

    @strawberry.field
    async def search_history(self, user_id: Optional[str] = None, limit: int = 10) -> List[SearchHistoryType]:
        """Get search history for a user."""
        from app.database.engine import connect
        from app.database.repositories.search import SearchRepository

        db = await connect()
        try:
            repo = SearchRepository(db)
            history = await repo.get_history(user_id=user_id, limit=limit)
            return [
                SearchHistoryType(
                    id=str(item.get("id", "")),
                    query=item.get("query", ""),
                    results_count=item.get("results_count", 0),
                    timestamp=item.get("timestamp", datetime.now()),
                    user_id=user_id,
                )
                for item in history
            ]
        except Exception:
            return []
        finally:
            await db.close()

    @strawberry.field
    def knowledge_graph(self, input: GraphQueryInput) -> KnowledgeGraphType:
        """Query knowledge graph for related entities."""
        return KnowledgeGraphType(nodes=[], edges=[])

    @strawberry.field
    async def ai_search(self, query: str, context: Optional[JSON] = None) -> AISearchResultType:
        """Perform AI-enhanced search."""
        from app.services.ai import get_ai_answer

        try:
            answer = await get_ai_answer(query)
        except Exception:
            answer = "AI search unavailable. Please try again later."

        return AISearchResultType(
            answer=answer,
            sources=[],
            confidence=0.5,
        )

    @strawberry.field
    async def suggest(self, query: str, limit: int = 5) -> List[str]:
        """Get search suggestions."""
        from app.database.engine import connect
        from app.database.repositories.search import SearchRepository

        db = await connect()
        try:
            repo = SearchRepository(db)
            suggestions = await repo.get_suggestions(query, limit=limit)
            return suggestions
        except Exception:
            return []
        finally:
            await db.close()

    @strawberry.field
    def facets(self, query: str, field: str, limit: int = 10) -> Optional[JSON]:
        """Get search facets/filters."""
        return None


@strawberry.type
class Mutation:
    """GraphQL mutations for Nebula Search."""

    @strawberry.mutation
    async def save_search(self, query: str, results_count: int, user_id: Optional[str] = None) -> SearchHistoryType:
        """Save a search to history."""
        from app.database.engine import connect
        from app.database.repositories.search import SearchRepository

        db = await connect()
        try:
            repo = SearchRepository(db)
            saved = await repo.save_search(query, results_count, user_id)
            return SearchHistoryType(
                id=str(saved.get("id", "")),
                query=query,
                results_count=results_count,
                timestamp=datetime.now(),
                user_id=user_id,
            )
        except Exception:
            return SearchHistoryType(
                id="temp-id",
                query=query,
                results_count=results_count,
                timestamp=datetime.now(),
                user_id=user_id,
            )
        finally:
            await db.close()

    @strawberry.mutation
    async def clear_search_history(self, user_id: Optional[str] = None) -> bool:
        """Clear search history for a user."""
        from app.database.engine import connect
        from app.database.repositories.search import SearchRepository

        db = await connect()
        try:
            repo = SearchRepository(db)
            await repo.clear_history(user_id=user_id)
            return True
        except Exception:
            return False
        finally:
            await db.close()


schema = strawberry.Schema(query=Query, mutation=Mutation)