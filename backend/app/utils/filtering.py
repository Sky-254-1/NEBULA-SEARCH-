"""Filtering and sorting utilities for API endpoints."""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("nebula.filtering")


class FilterOperator(str, Enum):
    """Supported filter operators."""
    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    IN = "in"  # In list
    NIN = "nin"  # Not in list
    LIKE = "like"  # LIKE pattern
    ILIKE = "ilike"  # Case-insensitive LIKE
    BETWEEN = "between"  # Between two values
    IS_NULL = "is_null"  # IS NULL
    IS_NOT_NULL = "is_not_null"  # IS NOT NULL


@dataclass
class FilterCondition:
    """Single filter condition."""
    field: str
    operator: FilterOperator
    value: Any
    value2: Optional[Any] = None  # For BETWEEN operator
    
    def to_sql(self, param_index: int) -> tuple[str, tuple]:
        """
        Convert filter to SQL WHERE clause.
        
        Returns:
            Tuple of (sql_fragment, params)
        """
        # Validate field name to prevent SQL injection
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.field):
            raise ValueError(f"Invalid field name: {self.field}")
        
        operator_map = {
            FilterOperator.EQ: f"{self.field} = ?",
            FilterOperator.NE: f"{self.field} != ?",
            FilterOperator.GT: f"{self.field} > ?",
            FilterOperator.GTE: f"{self.field} >= ?",
            FilterOperator.LT: f"{self.field} < ?",
            FilterOperator.LTE: f"{self.field} <= ?",
            FilterOperator.IN: f"{self.field} IN ({','.join(['?'] * len(self.value))})",
            FilterOperator.NIN: f"{self.field} NOT IN ({','.join(['?'] * len(self.value))})",
            FilterOperator.LIKE: f"{self.field} LIKE ?",
            FilterOperator.ILIKE: f"LOWER({self.field}) LIKE LOWER(?)",
            FilterOperator.BETWEEN: f"{self.field} BETWEEN ? AND ?",
            FilterOperator.IS_NULL: f"{self.field} IS NULL",
            FilterOperator.IS_NOT_NULL: f"{self.field} IS NOT NULL",
        }
        
        sql_template = operator_map[self.operator]
        
        # Build params based on operator
        if self.operator in [FilterOperator.IN, FilterOperator.NIN]:
            params = tuple(self.value)
        elif self.operator == FilterOperator.BETWEEN:
            params = (self.value, self.value2)
        elif self.operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            params = ()
        else:
            params = (self.value,)
        
        return sql_template, params


@dataclass
class SortCondition:
    """Sort condition."""
    field: str
    direction: str = "asc"  # 'asc' or 'desc'
    
    def to_sql(self) -> str:
        """Convert to SQL ORDER BY clause."""
        # Validate field name
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.field):
            raise ValueError(f"Invalid sort field: {self.field}")
        
        direction = "DESC" if self.direction.lower() == "desc" else "ASC"
        return f"{self.field} {direction}"


class FilterSet:
    """Collection of filter conditions."""
    
    def __init__(self):
        self.filters: list[FilterCondition] = []
    
    def add(self, field: str, operator: FilterOperator, value: Any, value2: Optional[Any] = None):
        """Add a filter condition."""
        self.filters.append(FilterCondition(field, operator, value, value2))
        return self
    
    def eq(self, field: str, value: Any):
        """Filter by equality."""
        return self.add(field, FilterOperator.EQ, value)
    
    def ne(self, field: str, value: Any):
        """Filter by inequality."""
        return self.add(field, FilterOperator.NE, value)
    
    def gt(self, field: str, value: Any):
        """Filter by greater than."""
        return self.add(field, FilterOperator.GT, value)
    
    def gte(self, field: str, value: Any):
        """Filter by greater than or equal."""
        return self.add(field, FilterOperator.GTE, value)
    
    def lt(self, field: str, value: Any):
        """Filter by less than."""
        return self.add(field, FilterOperator.LT, value)
    
    def lte(self, field: str, value: Any):
        """Filter by less than or equal."""
        return self.add(field, FilterOperator.LTE, value)
    
    def in_(self, field: str, values: list):
        """Filter by IN list."""
        return self.add(field, FilterOperator.IN, values)
    
    def like(self, field: str, pattern: str):
        """Filter by LIKE pattern."""
        return self.add(field, FilterOperator.LIKE, pattern)
    
    def ilike(self, field: str, pattern: str):
        """Filter by case-insensitive LIKE."""
        return self.add(field, FilterOperator.ILIKE, pattern)
    
    def between(self, field: str, value1: Any, value2: Any):
        """Filter by BETWEEN."""
        return self.add(field, FilterOperator.BETWEEN, value1, value2)
    
    def is_null(self, field: str):
        """Filter by IS NULL."""
        return self.add(field, FilterOperator.IS_NULL, None)
    
    def is_not_null(self, field: str):
        """Filter by IS NOT NULL."""
        return self.add(field, FilterOperator.IS_NOT_NULL, None)
    
    def to_sql(self) -> tuple[str, tuple]:
        """
        Convert all filters to SQL WHERE clause.
        
        Returns:
            Tuple of (where_clause, params)
        """
        if not self.filters:
            return "", ()
        
        conditions = []
        params = []
        
        for i, filter_cond in enumerate(self.filters):
            sql_fragment, filter_params = filter_cond.to_sql(i)
            conditions.append(sql_fragment)
            params.extend(filter_params)
        
        where_clause = "WHERE " + " AND ".join(conditions)
        return where_clause, tuple(params)


class SortSet:
    """Collection of sort conditions."""
    
    def __init__(self):
        self.sorts: list[SortCondition] = []
        self.allowed_fields: set[str] = set()
    
    def add(self, field: str, direction: str = "asc"):
        """Add a sort condition."""
        if self.allowed_fields and field not in self.allowed_fields:
            raise ValueError(f"Sorting by '{field}' is not allowed")
        
        self.sorts.append(SortCondition(field, direction))
        return self
    
    def asc(self, field: str):
        """Sort ascending."""
        return self.add(field, "asc")
    
    def desc(self, field: str):
        """Sort descending."""
        return self.add(field, "desc")
    
    def set_allowed_fields(self, fields: list[str]):
        """Set allowed sort fields for security."""
        self.allowed_fields = set(fields)
    
    def to_sql(self) -> str:
        """Convert to SQL ORDER BY clause."""
        if not self.sorts:
            return ""
        
        order_clauses = [sort.to_sql() for sort in self.sorts]
        return "ORDER BY " + ", ".join(order_clauses)


def parse_filter_params(
    filter_str: Optional[str] = None,
    allowed_fields: Optional[list[str]] = None,
) -> FilterSet:
    """
    Parse filter string into FilterSet.
    
    Format: field:operator:value (e.g., "status:eq:active", "created_at:gte:2024-01-01")
    Multiple filters separated by comma.
    
    Args:
        filter_str: Filter string
        allowed_fields: List of allowed filter fields (None = all allowed)
    
    Returns:
        FilterSet instance
    """
    if not filter_str:
        return FilterSet()
    
    filter_set = FilterSet()
    
    # Split by comma for multiple filters
    filter_parts = [f.strip() for f in filter_str.split(",") if f.strip()]
    
    for part in filter_parts:
        # Parse field:operator:value
        segments = part.split(":", 2)
        if len(segments) != 3:
            logger.warning(f"Invalid filter format: {part}")
            continue
        
        field, operator_str, value = segments
        
        # Validate field
        if allowed_fields and field not in allowed_fields:
            logger.warning(f"Filter field not allowed: {field}")
            continue
        
        # Validate operator
        try:
            operator = FilterOperator(operator_str)
        except ValueError:
            logger.warning(f"Invalid filter operator: {operator_str}")
            continue
        
        # Parse value based on operator
        try:
            if operator in [FilterOperator.IN, FilterOperator.NIN]:
                # Split by | for list
                parsed_value = [v.strip() for v in value.split("|")]
            elif operator == FilterOperator.BETWEEN:
                # Split by | for range
                parts = value.split("|")
                if len(parts) != 2:
                    raise ValueError("BETWEEN requires two values separated by |")
                parsed_value = parts[0].strip()
                parsed_value2 = parts[1].strip()
            else:
                parsed_value = value
                parsed_value2 = None
            
            if operator == FilterOperator.BETWEEN:
                filter_set.add(field, operator, parsed_value, parsed_value2)
            else:
                filter_set.add(field, operator, parsed_value)
        
        except Exception as e:
            logger.warning(f"Failed to parse filter {part}: {e}")
            continue
    
    return filter_set


def parse_sort_params(
    sort_str: Optional[str] = None,
    allowed_fields: Optional[list[str]] = None,
    default_sort: str = "id:asc",
) -> SortSet:
    """
    Parse sort string into SortSet.
    
    Format: field:direction (e.g., "created_at:desc", "name:asc")
    Multiple sorts separated by comma.
    
    Args:
        sort_str: Sort string
        allowed_fields: List of allowed sort fields (None = all allowed)
        default_sort: Default sort if none provided
    
    Returns:
        SortSet instance
    """
    sort_set = SortSet()
    
    if allowed_fields:
        sort_set.set_allowed_fields(allowed_fields)
    
    if not sort_str:
        # Use default sort
        field, direction = default_sort.split(":")
        sort_set.add(field, direction)
        return sort_set
    
    # Parse multiple sorts
    sort_parts = [s.strip() for s in sort_str.split(",") if s.strip()]
    
    for part in sort_parts:
        segments = part.split(":")
        if len(segments) != 2:
            logger.warning(f"Invalid sort format: {part}")
            continue
        
        field, direction = segments
        
        # Validate field
        if allowed_fields and field not in allowed_fields:
            logger.warning(f"Sort field not allowed: {field}")
            continue
        
        # Validate direction
        if direction.lower() not in ["asc", "desc"]:
            logger.warning(f"Invalid sort direction: {direction}")
            continue
        
        sort_set.add(field, direction.lower())
    
    return sort_set