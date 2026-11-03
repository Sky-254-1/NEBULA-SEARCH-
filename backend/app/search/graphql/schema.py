"""GraphQL schema for Nebula Search API with real service integration."""

from typing import List, NewType, Optional
from datetime import datetime

import strawberry
import json
from graphql import GraphQLError
from strawberry.schema.config import StrawberryConfig
from strawberry.types import Info

JSONValue = NewType("JSONValue", object)
JSON_SCALAR = strawberry.scalar(
    serialize=lambda v: v,
    parse_value=lambda v: v,
    name="JSON",
    description="Arbitrary JSON value",
)

from app.services.search import run_web_search, sanitize_query
from app.config import get_settings

settings = get_settings()


async def _history_owner(info: Info, requested_user_id: Optional[str]):
    """Resolve an authenticated owner and reject attempts to choose another."""
    principal = info.context.get("user")
    email = principal.get("sub") if isinstance(principal, dict) else None
    if not email:
        raise GraphQLError("Authentication required")

    from app.database.engine import connect
    from app.database.repositories.user import UserRepository

    db = await connect()
    try:
        user_id = await UserRepository(db).get_id_by_email(email)
        if user_id is None:
            raise GraphQLError("Authentication required")
        if requested_user_id is not None and requested_user_id != str(user_id):
            raise GraphQLError("Access denied")
        return db, user_id
    except BaseException:
        await db.close()
        raise

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
    metadata: Optional[JSONValue] = None


@strawberry.type
class SearchResult:
    """Search results type."""
    query: str
    total: int
    page: int
    page_size: int
    documents: List[DocumentType]
    facets: Optional[JSONValue] = None
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
    properties: JSONValue
    type: str
    score: float


@strawberry.type
class KnowledgeGraphType:
    """Knowledge graph query result."""
    nodes: List[NodeType]
    edges: List[JSONValue]


@strawberry.type
class AINodeType:
    """AI node type for AI search."""
    id: str
    content: str
    type: str
    score: float
    context: Optional[JSONValue] = None


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
    filters: Optional[JSONValue] = None
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
    async def search_history(
        self, info: Info, user_id: Optional[str] = None, limit: int = 10
    ) -> List[SearchHistoryType]:
        """Get search history for a user."""
        from app.database.repositories.search_history import SearchHistoryRepository

        if limit < 1 or limit > 100:
            raise GraphQLError("Limit must be between 1 and 100")
        db, owner_id = await _history_owner(info, user_id)
        try:
            history = await SearchHistoryRepository(db).get_user_history(
                user_id=owner_id, limit=limit
            )
            return [
                SearchHistoryType(
                    id=str(item.get("id", "")),
                    query=item.get("query", ""),
                    results_count=item.get("result_count", 0),
                    timestamp=(
                        datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                        if isinstance(item.get("created_at"), str)
                        else item.get("created_at", datetime.now())
                    ),
                    user_id=str(owner_id),
                )
                for item in history
            ]
        finally:
            await db.close()

    @strawberry.field
    def knowledge_graph(self, input: GraphQueryInput) -> KnowledgeGraphType:
        """Query knowledge graph for related entities."""
        return KnowledgeGraphType(nodes=[], edges=[])

    @strawberry.field
    async def ai_search(self, query: str, context: Optional[JSONValue] = None) -> AISearchResultType:
        """Perform AI-enhanced search."""
        from app.services.ai import get_ai_answer

        try:
            answer_text, _provider = await get_ai_answer(query)
            answer = answer_text or "AI search unavailable. Please try again later."
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
    def facets(self, query: str, field: str, limit: int = 10) -> Optional[JSONValue]:
        """Get search facets/filters."""
        return None


@strawberry.type
class Mutation:
    """GraphQL mutations for Nebula Search."""

    @strawberry.mutation
    async def save_search(
        self,
        info: Info,
        query: str,
        results_count: int,
        user_id: Optional[str] = None,
    ) -> SearchHistoryType:
        """Save a search to history."""
        from app.database.repositories.search_history import SearchHistoryRepository

        db, owner_id = await _history_owner(info, user_id)
        try:
            saved_id = await SearchHistoryRepository(db).record_search(
                user_id=owner_id,
                query=query,
                result_count=results_count,
            )
            return SearchHistoryType(
                id=str(saved_id),
                query=query,
                results_count=results_count,
                timestamp=datetime.now(),
                user_id=str(owner_id),
            )
        finally:
            await db.close()

    @strawberry.mutation
    async def clear_search_history(self, info: Info, user_id: Optional[str] = None) -> bool:
        """Clear search history for a user."""
        from app.database.repositories.search_history import SearchHistoryRepository

        db, owner_id = await _history_owner(info, user_id)
        try:
            await SearchHistoryRepository(db).clear_user_history(user_id=owner_id)
            return True
        finally:
            await db.close()


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    config=StrawberryConfig(
        scalar_map={JSONValue: JSON_SCALAR},
    ),
)
