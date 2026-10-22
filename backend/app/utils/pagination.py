"""Pagination utilities and decorators."""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Query
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("nebula.pagination")


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Query(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for SQL queries."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for SQL queries."""
        return self.page_size


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters."""
    cursor: Optional[str] = Query(None, description="Pagination cursor from previous response")
    limit: int = Query(20, ge=1, le=100, description="Items per page")


@dataclass
class PaginatedResponse:
    """Standardized paginated response."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None
    
    def to_dict(self, request=None) -> dict:
        """Convert to dictionary with optional links."""
        result = {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_previous": self.has_previous,
            }
        }
        
        if self.next_cursor or self.previous_cursor:
            result["pagination"]["cursors"] = {
                "next": self.next_cursor,
                "previous": self.previous_cursor,
            }
        
        return result


def paginate_query(
    query: str,
    params: PaginationParams,
    count_query: Optional[str] = None,
) -> tuple[str, tuple]:
    """
    Add pagination to SQL query.
    
    Args:
        query: Base SQL query
        params: Pagination parameters
        count_query: Optional count query (if None, wraps base query)
    
    Returns:
        Tuple of (paginated_query, query_params)
    """
    # Add LIMIT and OFFSET
    paginated_query = f"{query} LIMIT ? OFFSET ?"
    query_params = params.offset, params.limit
    
    return paginated_query, query_params


def paginate_cursor_query(
    query: str,
    cursor: Optional[str] = None,
    limit: int = 20,
    cursor_field: str = "id",
) -> tuple[str, tuple]:
    """
    Add cursor pagination to SQL query.
    
    Args:
        query: Base SQL query
        cursor: Cursor value from previous response
        limit: Max items to return
        cursor_field: Field to use for cursor
    
    Returns:
        Tuple of (paginated_query, query_params)
    """
    if cursor:
        # Add WHERE clause for cursor
        paginated_query = f"{query} WHERE {cursor_field} > ? ORDER BY {cursor_field} ASC LIMIT ?"
        query_params = (cursor, limit)
    else:
        # First page - no cursor
        paginated_query = f"{query} ORDER BY {cursor_field} ASC LIMIT ?"
        query_params = (limit,)
    
    return paginated_query, query_params


def create_pagination_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """
    Create standardized pagination response.
    
    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        page_size: Items per page
    
    Returns:
        Paginated response dictionary
    """
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    ).to_dict()


def create_cursor_pagination_response(
    items: list[Any],
    has_next: bool,
    cursor_field: str = "id",
) -> dict:
    """
    Create cursor-based pagination response.
    
    Args:
        items: List of items for current page
        has_next: Whether there are more items
        cursor_field: Field used for cursor
    
    Returns:
        Paginated response dictionary with cursors
    """
    next_cursor = None
    previous_cursor = None
    
    if items:
        if has_next:
            next_cursor = str(getattr(items[-1], cursor_field, items[-1].get(cursor_field) if isinstance(items[-1], dict) else None))
        if len(items) > 0:
            previous_cursor = str(getattr(items[0], cursor_field, items[0].get(cursor_field) if isinstance(items[0], dict) else None))
    
    return PaginatedResponse(
        items=items,
        total=len(items),  # Total not known in cursor pagination
        page=1,
        page_size=len(items),
        total_pages=1,
        has_next=has_next,
        has_previous=previous_cursor is not None,
        next_cursor=next_cursor,
        previous_cursor=previous_cursor,
    ).to_dict()


class PaginationMixin:
    """Mixin to add pagination capabilities to repository classes."""
    
    async def paginate(
        self,
        query: str,
        params: PaginationParams,
        count_query: Optional[str] = None,
        query_params: tuple = (),
    ) -> tuple[list[Any], int]:
        """
        Execute paginated query.
        
        Returns:
            Tuple of (items, total_count)
        """
        # Get total count
        count_query = count_query or f"SELECT COUNT(*) FROM ({query})"  # nosec B608
        count_row = await self._db.fetchone(count_query, query_params)
        total = count_row[0] if count_row else 0
        
        # Get paginated items
        paginated_query, paginated_params = paginate_query(query, params)
        items = await self._db.fetchall(paginated_query, query_params + paginated_params)
        
        return items, total
    
    async def paginate_cursor(
        self,
        query: str,
        cursor: Optional[str] = None,
        limit: int = 20,
        cursor_field: str = "id",
        query_params: tuple = (),
    ) -> tuple[list[Any], bool]:
        """
        Execute cursor-based paginated query.
        
        Returns:
            Tuple of (items, has_next)
        """
        paginated_query, paginated_params = paginate_cursor_query(
            query, cursor, limit, cursor_field
        )
        items = await self._db.fetchall(paginated_query, query_params + paginated_params)
        
        # Check if there are more items
        has_next = len(items) == limit
        
        return items, has_next