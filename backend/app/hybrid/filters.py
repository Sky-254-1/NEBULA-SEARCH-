"""
Filter Engine

Applies filters to search results based on metadata fields.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nebula.hybrid.filters")


class FilterEngine:
    """
    Filter search results based on various criteria.
    
    Supported filters:
    - File type
    - Date range
    - Language
    - Tags
    - Author
    - Category
    - Custom metadata fields
    """

    def __init__(self):
        """Initialize filter engine"""
        pass

    def apply_filters(
        self,
        results: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Apply filters to search results.
        
        Args:
            results: List of search results
            filters: Filter criteria
            
        Returns:
            Filtered results
        """
        if not filters or not results:
            return results
        
        filtered = results
        
        # Apply each filter
        for filter_type, filter_value in filters.items():
            filtered = self._apply_filter(filtered, filter_type, filter_value)
        
        return filtered

    def _apply_filter(
        self,
        results: List[Dict[str, Any]],
        filter_type: str,
        filter_value: Any,
    ) -> List[Dict[str, Any]]:
        """Apply a single filter"""
        if filter_type == "file_type":
            return self._filter_by_file_type(results, filter_value)
        elif filter_type == "date_range":
            return self._filter_by_date_range(results, filter_value)
        elif filter_type == "language":
            return self._filter_by_language(results, filter_value)
        elif filter_type == "tags":
            return self._filter_by_tags(results, filter_value)
        elif filter_type == "author":
            return self._filter_by_author(results, filter_value)
        elif filter_type == "category":
            return self._filter_by_category(results, filter_value)
        elif filter_type == "min_score":
            return self._filter_by_min_score(results, filter_value)
        elif filter_type == "has_embedding":
            return self._filter_by_embedding(results, filter_value)
        else:
            # Try custom metadata filter
            return self._filter_by_custom_field(results, filter_type, filter_value)

    def _filter_by_file_type(
        self,
        results: List[Dict[str, Any]],
        file_types: Any,
    ) -> List[Dict[str, Any]]:
        """Filter by file type"""
        if isinstance(file_types, str):
            file_types = [file_types]
        
        filtered = []
        for result in results:
            file_type = result.get("file_type", "")
            filename = result.get("filename", "")
            
            # Extract extension from filename
            if "." in filename:
                ext = filename.split(".")[-1].lower()
            else:
                ext = ""
            
            # Check if matches any filter
            if file_type.lower() in [ft.lower() for ft in file_types]:
                filtered.append(result)
            elif ext in [ft.lower().lstrip(".") for ft in file_types]:
                filtered.append(result)
        
        return filtered

    def _filter_by_date_range(
        self,
        results: List[Dict[str, Any]],
        date_range: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Filter by date range"""
        start_date = date_range.get("start")
        end_date = date_range.get("end")
        
        if not start_date and not end_date:
            return results
        
        filtered = []
        
        for result in results:
            date_field = result.get("updated_at") or result.get("created_at")
            
            if not date_field:
                continue
            
            # Parse date
            if isinstance(date_field, str):
                try:
                    doc_date = datetime.fromisoformat(date_field.replace('Z', '+00:00'))
                except Exception as exc:
                    logger.debug("Date field parse failed, skipping doc: %s", exc)
                    continue
            elif hasattr(date_field, "year"):
                doc_date = date_field
            else:
                continue
            
            # Check range
            if start_date:
                if isinstance(start_date, str):
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start = start_date
                
                if doc_date < start:
                    continue
            
            if end_date:
                if isinstance(end_date, str):
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    end = end_date
                
                if doc_date > end:
                    continue
            
            filtered.append(result)
        
        return filtered

    def _filter_by_language(
        self,
        results: List[Dict[str, Any]],
        languages: Any,
    ) -> List[Dict[str, Any]]:
        """Filter by language"""
        if isinstance(languages, str):
            languages = [languages]
        
        filtered = []
        for result in results:
            lang = result.get("language", "en").lower()
            if lang in [lang.lower() for lang in languages]:
                filtered.append(result)
        
        return filtered

    def _filter_by_tags(
        self,
        results: List[Dict[str, Any]],
        tags: Any,
    ) -> List[Dict[str, Any]]:
        """Filter by tags (AND or OR logic)"""
        if isinstance(tags, str):
            tags = [tags]
        
        filtered = []
        for result in results:
            result_tags = [str(t).lower() for t in result.get("tags", [])]
            
            # OR logic: match any tag
            if any(tag.lower() in result_tags for tag in tags):
                filtered.append(result)
        
        return filtered

    def _filter_by_author(
        self,
        results: List[Dict[str, Any]],
        authors: Any,
    ) -> List[Dict[str, Any]]:
        """Filter by author"""
        if isinstance(authors, str):
            authors = [authors]
        
        filtered = []
        for result in results:
            author = result.get("author", "").lower()
            if any(a.lower() in author for a in authors):
                filtered.append(result)
        
        return filtered

    def _filter_by_category(
        self,
        results: List[Dict[str, Any]],
        categories: Any,
    ) -> List[Dict[str, Any]]:
        """Filter by category"""
        if isinstance(categories, str):
            categories = [categories]
        
        filtered = []
        for result in results:
            result_cats = [str(c).lower() for c in result.get("categories", [])]
            if any(cat.lower() in result_cats for cat in categories):
                filtered.append(result)
        
        return filtered

    def _filter_by_min_score(
        self,
        results: List[Dict[str, Any]],
        min_score: float,
    ) -> List[Dict[str, Any]]:
        """Filter by minimum score"""
        return [r for r in results if r.get("score", 0.0) >= min_score]

    def _filter_by_embedding(
        self,
        results: List[Dict[str, Any]],
        has_embedding: bool,
    ) -> List[Dict[str, Any]]:
        """Filter by embedding presence"""
        if has_embedding:
            return [r for r in results if "embedding" in r or "vector" in r or r.get("has_embedding")]
        else:
            return [r for r in results if "embedding" not in r and "vector" not in r]

    def _filter_by_custom_field(
        self,
        results: List[Dict[str, Any]],
        field: str,
        value: Any,
    ) -> List[Dict[str, Any]]:
        """Filter by custom metadata field"""
        filtered = []
        
        for result in results:
            field_value = result.get(field)
            
            if field_value is None:
                continue
            
            # Handle different value types
            if isinstance(value, list):
                if field_value in value or str(field_value) in [str(v) for v in value]:
                    filtered.append(result)
            elif isinstance(value, dict):
                # Range filter
                if "min" in value and field_value < value["min"]:
                    continue
                if "max" in value and field_value > value["max"]:
                    continue
                filtered.append(result)
            else:
                if field_value == value or str(field_value) == str(value):
                    filtered.append(result)
        
        return filtered

    def validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate filter configuration.
        
        Args:
            filters: Filter criteria
            
        Returns:
            Validation result with errors if any
        """
        errors = []
        warnings = []
        
        # Validate date range
        if "date_range" in filters:
            date_range = filters["date_range"]
            if not isinstance(date_range, dict):
                errors.append("date_range must be a dictionary")
            else:
                if "start" not in date_range and "end" not in date_range:
                    errors.append("date_range must have 'start' or 'end'")
        
        # Validate min_score
        if "min_score" in filters:
            min_score = filters["min_score"]
            if not isinstance(min_score, (int, float)):
                errors.append("min_score must be a number")
            elif min_score < 0 or min_score > 1:
                warnings.append("min_score should be between 0 and 1")
        
        # Validate file_type
        if "file_type" in filters:
            file_type = filters["file_type"]
            if isinstance(file_type, list):
                for ft in file_type:
                    if not isinstance(ft, str):
                        errors.append("file_type list must contain strings")
                        break
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }