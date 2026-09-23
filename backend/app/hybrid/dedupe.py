"""
Result Deduplication

Removes duplicate documents from search results using multiple strategies.
"""

import logging
import hashlib
from typing import Any, Dict, List

logger = logging.getLogger("nebula.hybrid.dedupe")


class Deduplicator:
    """
    Remove duplicate search results.
    
    Strategies:
    - Document ID matching
    - URL canonicalization
    - Content fingerprinting
    - Vector ID matching
    """

    def __init__(
        self,
        use_doc_id: bool = True,
        use_url: bool = True,
        use_content_hash: bool = True,
        use_vector_id: bool = True,
        content_hash_length: int = 100,
    ):
        """
        Initialize deduplicator.
        
        Args:
            use_doc_id: Deduplicate by document ID
            use_url: Deduplicate by URL
            use_content_hash: Deduplicate by content hash
            use_vector_id: Deduplicate by vector ID
            content_hash_length: Number of characters to use for content hashing
        """
        self.use_doc_id = use_doc_id
        self.use_url = use_url
        self.use_content_hash = use_content_hash
        self.use_vector_id = use_vector_id
        self.content_hash_length = content_hash_length

    def deduplicate(
        self,
        results: List[Dict[str, Any]],
        score_key: str = "score",
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate results, keeping the highest-scoring version.
        
        Args:
            results: List of search results
            score_key: Key containing the score
            
        Returns:
            Deduplicated results
        """
        if not results:
            return []
        
        # Sort results by score descending (highest first)
        sorted_results = sorted(results, key=lambda x: x.get(score_key, 0.0), reverse=True)
        
        seen_ids = set()
        seen_urls = set()
        seen_content_hashes = set()
        seen_vector_ids = set()
        
        unique_results = []
        
        for result in sorted_results:
            doc_id = result.get("id", "")
            url = self._canonicalize_url(result.get("url", ""))
            content_hash = self._compute_content_hash(result)
            vector_id = result.get("vector_id", result.get("chunk_id", ""))
            
            # Check if this is a duplicate
            is_duplicate = False
            
            if self.use_doc_id and doc_id and doc_id in seen_ids:
                is_duplicate = True
            
            if self.use_url and url and url in seen_urls:
                is_duplicate = True
            
            if self.use_content_hash and content_hash and content_hash in seen_content_hashes:
                is_duplicate = True
            
            if self.use_vector_id and vector_id and vector_id in seen_vector_ids:
                is_duplicate = True
            
            if not is_duplicate:
                unique_results.append(result)
                
                # Add to seen sets
                if doc_id:
                    seen_ids.add(doc_id)
                if url:
                    seen_urls.add(url)
                if content_hash:
                    seen_content_hashes.add(content_hash)
                if vector_id:
                    seen_vector_ids.add(vector_id)
        
        if len(unique_results) < len(results):
            logger.debug(
                f"Deduplicated {len(results)} results to {len(unique_results)} "
                f"(removed {len(results) - len(unique_results)} duplicates)"
            )
        
        return unique_results

    def _canonicalize_url(self, url: str) -> str:
        """Canonicalize URL for comparison"""
        if not url:
            return ""
        
        # Convert to lowercase
        url = url.lower().strip()
        
        # Remove trailing slash
        url = url.rstrip("/")
        
        # Remove common tracking parameters
        # (simplified - in production, use a more comprehensive approach)
        if "?" in url:
            base, params = url.split("?", 1)
            # Keep only essential parameters
            essential_params = []
            for param in params.split("&"):
                if not param.startswith(("utm_", "fbclid", "gclid")):
                    essential_params.append(param)
            
            if essential_params:
                url = base + "?" + "&".join(essential_params)
            else:
                url = base
        
        return url

    def _compute_content_hash(self, result: Dict[str, Any]) -> str:
        """Compute content hash for deduplication"""
        # Use a combination of title and first N characters of content
        title = result.get("title", "")
        content = result.get("content", result.get("snippet", ""))
        
        # Create hash input
        hash_input = f"{title.lower()}{content[:self.content_hash_length].lower()}"
        
        # Compute MD5 hash (fast and sufficient for deduplication)
        return hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest()

    def find_duplicates(
        self,
        results: List[Dict[str, Any]],
    ) -> List[tuple]:
        """
        Find duplicate results without removing them.
        
        Args:
            results: List of search results
            
        Returns:
            List of (result1_index, result2_index, reason) tuples
        """
        duplicates = []
        
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                result1 = results[i]
                result2 = results[j]
                
                # Check for duplicate by ID
                if self.use_doc_id:
                    if result1.get("id") and result1.get("id") == result2.get("id"):
                        duplicates.append((i, j, "document_id"))
                        continue
                
                # Check for duplicate by URL
                if self.use_url:
                    url1 = self._canonicalize_url(result1.get("url", ""))
                    url2 = self._canonicalize_url(result2.get("url", ""))
                    if url1 and url1 == url2:
                        duplicates.append((i, j, "url"))
                        continue
                
                # Check for duplicate by content hash
                if self.use_content_hash:
                    hash1 = self._compute_content_hash(result1)
                    hash2 = self._compute_content_hash(result2)
                    if hash1 and hash1 == hash2:
                        duplicates.append((i, j, "content_hash"))
                        continue
                
                # Check for duplicate by vector ID
                if self.use_vector_id:
                    vid1 = result1.get("vector_id", result1.get("chunk_id", ""))
                    vid2 = result2.get("vector_id", result2.get("chunk_id", ""))
                    if vid1 and vid1 == vid2:
                        duplicates.append((i, j, "vector_id"))
                        continue
        
        return duplicates

    def merge_duplicates(
        self,
        results: List[Dict[str, Any]],
        score_key: str = "score",
    ) -> List[Dict[str, Any]]:
        """
        Merge duplicate results, combining their scores.
        
        Args:
            results: List of search results
            score_key: Key containing the score
            
        Returns:
            Merged results
        """
        if not results:
            return []
        
        # Group results by document ID
        groups = {}
        for i, result in enumerate(results):
            doc_id = result.get("id", f"unknown_{i}")
            if doc_id not in groups:
                groups[doc_id] = []
            groups[doc_id].append(result)
        
        merged = []
        for doc_id, group in groups.items():
            if len(group) == 1:
                # No duplicates
                merged.append(group[0])
            else:
                # Merge duplicates - keep highest score result
                best = max(group, key=lambda x: x.get(score_key, 0.0))
                
                # Combine scores from all duplicates
                combined_score = sum(r.get(score_key, 0.0) for r in group)
                best[score_key] = combined_score
                
                # Add metadata about merging
                best["merged_from"] = len(group)
                best["score_breakdown"] = best.get("score_breakdown", {})
                best["score_breakdown"]["merged"] = True
                
                merged.append(best)
        
        # Sort by score
        merged.sort(key=lambda x: x.get(score_key, 0.0), reverse=True)
        
        return merged

    def get_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get deduplication statistics"""
        if not results:
            return {}
        
        duplicates = self.find_duplicates(results)
        
        return {
            "total_results": len(results),
            "duplicate_pairs": len(duplicates),
            "duplicate_sources": {},
        }