"""
Metadata Extractor

Extracts and processes metadata from documents for boosting and filtering.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nebula.hybrid.metadata")


class MetadataExtractor:
    """
    Extract metadata from documents.
    
    Supports:
    - Standard fields (title, author, tags, categories)
    - Custom metadata fields
    - Date parsing
    - Content analysis
    """

    def __init__(self):
        """Initialize metadata extractor"""
        self.standard_fields = {
            "title",
            "author",
            "description",
            "snippet",
            "tags",
            "categories",
            "created_at",
            "updated_at",
            "filename",
            "url",
            "file_type",
            "language",
        }

    def extract(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from a document.
        
        Args:
            document: Document dictionary
            
        Returns:
            Extracted metadata
        """
        metadata = {
            "id": document.get("id"),
            "title": document.get("title"),
            "author": document.get("author"),
            "description": document.get("description", document.get("snippet")),
            "tags": document.get("tags", []),
            "categories": document.get("categories", []),
            "created_at": self._parse_date(document.get("created_at")),
            "updated_at": self._parse_date(document.get("updated_at")),
            "filename": document.get("filename"),
            "url": document.get("url"),
            "file_type": self._extract_file_type(document),
            "language": document.get("language", "en"),
            "word_count": self._count_words(document),
            "has_embedding": "embedding" in document or "vector" in document,
        }
        
        # Extract custom metadata
        custom_fields = {
            k: v for k, v in document.items() if k not in self.standard_fields
        }
        metadata["custom"] = custom_fields
        
        # Calculate quality score
        metadata["quality_score"] = self._calculate_quality_score(metadata)
        
        return metadata

    def _parse_date(self, date_value: Any) -> Optional[str]:
        """Parse date value to ISO format string"""
        if not date_value:
            return None
        
        if isinstance(date_value, str):
            # Already a string
            return date_value
        
        # Handle datetime objects
        if hasattr(date_value, "isoformat"):
            return date_value.isoformat()
        
        return None

    def _extract_file_type(self, document: Dict[str, Any]) -> Optional[str]:
        """Extract file type from document"""
        # Check explicit file_type field
        file_type = document.get("file_type")
        if file_type:
            return file_type
        
        # Infer from filename
        filename = document.get("filename", "")
        if "." in filename:
            extension = filename.split(".")[-1].lower()
            return extension
        
        # Infer from content-type if available
        content_type = document.get("content_type", "")
        if content_type:
            return content_type.split("/")[-1]
        
        return None

    def _count_words(self, document: Dict[str, Any]) -> int:
        """Count words in document content"""
        content = document.get("content", "") or document.get("snippet", "")
        if not content:
            return 0
        
        return len(str(content).split())

    def _calculate_quality_score(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate document quality score (0-1).
        
        Based on:
        - Presence of key metadata fields
        - Content length
        - Richness of metadata
        """
        score = 0.0
        
        # Title (20%)
        if metadata.get("title") and len(metadata.get("title", "")) > 5:
            score += 0.2
        
        # Author (10%)
        if metadata.get("author"):
            score += 0.1
        
        # Description (15%)
        if metadata.get("description") and len(metadata.get("description", "")) > 10:
            score += 0.15
        
        # Tags (15%)
        tags = metadata.get("tags", [])
        if tags and len(tags) > 0:
            score += 0.15
        
        # Categories (10%)
        categories = metadata.get("categories", [])
        if categories and len(categories) > 0:
            score += 0.1
        
        # Content (30%)
        word_count = metadata.get("word_count", 0)
        if word_count >= 100:
            score += 0.3
        elif word_count >= 50:
            score += 0.2
        elif word_count > 0:
            score += 0.1
        
        return min(1.0, score)

    def batch_extract(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract metadata from multiple documents.
        
        Args:
            documents: List of documents
            
        Returns:
            List of extracted metadata
        """
        return [self.extract(doc) for doc in documents]

    def get_metadata_summary(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get summary statistics of metadata.
        
        Args:
            metadata_list: List of extracted metadata
            
        Returns:
            Summary statistics
        """
        if not metadata_list:
            return {}
        
        total = len(metadata_list)
        
        # Count fields presence
        has_title = sum(1 for m in metadata_list if m.get("title"))
        has_author = sum(1 for m in metadata_list if m.get("author"))
        has_tags = sum(1 for m in metadata_list if m.get("tags"))
        has_categories = sum(1 for m in metadata_list if m.get("categories"))
        has_embedding = sum(1 for m in metadata_list if m.get("has_embedding"))
        
        # Average quality score
        quality_scores = [m.get("quality_score", 0.0) for m in metadata_list if m.get("quality_score")]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            "total_documents": total,
            "has_title": has_title,
            "has_author": has_author,
            "has_tags": has_tags,
            "has_categories": has_categories,
            "has_embedding": has_embedding,
            "average_quality_score": avg_quality,
            "title_percentage": (has_title / total * 100) if total > 0 else 0,
            "embedding_percentage": (has_embedding / total * 100) if total > 0 else 0,
        }