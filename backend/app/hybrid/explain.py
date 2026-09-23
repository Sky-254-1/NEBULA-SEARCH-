"""
Ranking Explanation Generator

Generates detailed explanations for search result rankings.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nebula.hybrid.explain")


class ExplanationGenerator:
    """
    Generate explanations for search result rankings.
    
    Provides transparency into:
    - Score components
    - Ranking factors
    - Boost applications
    - Match details
    """

    def __init__(self):
        """Initialize explanation generator"""
        pass

    def explain_result(
        self,
        result: Dict[str, Any],
        query: str,
        all_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate explanation for a single result.
        
        Args:
            result: Search result to explain
            query: Original search query
            all_results: All results for context (optional)
            
        Returns:
            Explanation dictionary
        """
        explanation = {
            "query": query,
            "document_id": result.get("id", "unknown"),
            "document_title": result.get("title", "unknown"),
            "final_score": result.get("score", 0.0),
            "rank": None,
            "score_breakdown": {},
            "matched_terms": [],
            "boosts": [],
            "reasons": [],
            "debug_info": {},
        }
        
        # Get rank if all results provided
        if all_results:
            sorted_results = sorted(
                all_results,
                key=lambda x: x.get("score", 0.0),
                reverse=True,
            )
            for i, r in enumerate(sorted_results, 1):
                if r.get("id") == result.get("id"):
                    explanation["rank"] = i
                    break
        
        # Extract score breakdown
        if "score_breakdown" in result:
            explanation["score_breakdown"] = self._format_score_breakdown(
                result["score_breakdown"]
            )
        
        # Extract keyword scores
        if "keyword_score" in result or "lexical_score" in result:
            keyword_score = result.get("keyword_score", result.get("lexical_score", 0.0))
            explanation["score_breakdown"]["keyword"] = {
                "score": keyword_score,
                "description": "BM25 keyword relevance",
            }
        
        # Extract semantic scores
        if "semantic_score" in result:
            explanation["score_breakdown"]["semantic"] = {
                "score": result.get("semantic_score", 0.0),
                "description": "Semantic vector similarity",
            }
        
        # Extract boost information
        if "boost_factors" in result:
            explanation["boosts"] = [
                {"type": boost_type, "factor": factor}
                for boost_type, factor in result.get("boost_factors", [])
            ]
        
        # Extract boost multiplier
        if "boost_multiplier" in result:
            explanation["boost_multiplier"] = result.get("boost_multiplier", 1.0)
        
        # Find matched terms
        explanation["matched_terms"] = self._find_matched_terms(query, result)
        
        # Generate human-readable reasons
        explanation["reasons"] = self._generate_reasons(explanation, result)
        
        # Add debug info
        explanation["debug_info"] = {
            "result_keys": list(result.keys()),
            "has_embedding": "embedding" in result or "vector" in result,
            "content_preview": str(result.get("content", ""))[:100],
        }
        
        return explanation

    def _format_score_breakdown(self, breakdown: Dict[str, Any]) -> Dict[str, Any]:
        """Format score breakdown for display"""
        formatted = {}
        
        for key, value in breakdown.items():
            if isinstance(value, dict):
                formatted[key] = value
            else:
                formatted[key] = {"value": value}
        
        return formatted

    def _find_matched_terms(self, query: str, result: Dict[str, Any]) -> List[str]:
        """Find which query terms matched in the result"""
        matched = []
        query_terms = query.lower().split()
        
        # Check title
        title = str(result.get("title", "")).lower()
        for term in query_terms:
            if term in title and term not in matched:
                matched.append(term)
        
        # Check content
        content = str(result.get("content", "")).lower()
        str(result.get("snippet", "")).lower()
        for term in query_terms:
            if term in content and term not in matched:
                matched.append(term)
        
        # Check tags
        tags = result.get("tags", [])
        for tag in tags:
            tag_lower = str(tag).lower()
            for term in query_terms:
                if term in tag_lower and term not in matched:
                    matched.append(term)
        
        return matched

    def _generate_reasons(self, explanation: Dict[str, Any], result: Dict[str, Any]) -> List[str]:
        """Generate human-readable ranking reasons"""
        reasons = []
        
        # Score-based reasons
        score = result.get("score", 0.0)
        if score > 0.8:
            reasons.append("Very high relevance score")
        elif score > 0.5:
            reasons.append("High relevance score")
        elif score > 0.3:
            reasons.append("Moderate relevance")
        else:
            reasons.append("Low relevance")
        
        # Keyword match reasons
        keyword_score = result.get("keyword_score", result.get("lexical_score", 0.0))
        if keyword_score > 0.5:
            reasons.append("Strong keyword match")
        
        # Semantic match reasons
        semantic_score = result.get("semantic_score", 0.0)
        if semantic_score > 0.7:
            reasons.append("Strong semantic similarity")
        elif semantic_score > 0.4:
            reasons.append("Moderate semantic similarity")
        
        # Boost reasons
        boost_factors = result.get("boost_factors", [])
        for boost_type, boost_value in boost_factors:
            if boost_type == "title":
                reasons.append("Query terms found in title")
            elif boost_type == "heading":
                reasons.append("Query terms found in headings")
            elif boost_type == "tag":
                reasons.append("Document tagged with relevant terms")
            elif boost_type == "category":
                reasons.append("Document in relevant category")
            elif boost_type == "recency":
                reasons.append("Recent document")
            elif boost_type == "popularity":
                reasons.append("Popular document")
        
        # Matched terms
        matched_terms = explanation.get("matched_terms", [])
        if len(matched_terms) > 2:
            reasons.append(f"Multiple query terms matched ({len(matched_terms)} terms)")
        
        return reasons

    def explain_search(
        self,
        query: str,
        results: List[Dict[str, Any]],
        intent: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate overall search explanation.
        
        Args:
            query: Search query
            results: Search results
            intent: Query intent analysis (optional)
            config: Search configuration used (optional)
            
        Returns:
            Search explanation
        """
        explanation = {
            "query": query,
            "result_count": len(results),
            "intent": intent,
            "configuration": config,
            "results": [],
            "summary": {},
        }
        
        # Generate explanation for each result
        for result in results:
            result_explanation = self.explain_result(result, query, results)
            explanation["results"].append(result_explanation)
        
        # Generate summary
        explanation["summary"] = self._generate_summary(results, explanation["results"])
        
        return explanation

    def _generate_summary(
        self,
        results: List[Dict[str, Any]],
        explanations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate search summary statistics"""
        if not results or not explanations:
            return {}
        
        # Score statistics
        scores = [r.get("score", 0.0) for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Count boost applications
        boost_counts = {}
        for expl in explanations:
            for boost in expl.get("boosts", []):
                boost_type = boost.get("type", "unknown")
                boost_counts[boost_type] = boost_counts.get(boost_type, 0) + 1
        
        # Count matched term occurrences
        term_matches = {}
        for expl in explanations:
            for term in expl.get("matched_terms", []):
                term_matches[term] = term_matches.get(term, 0) + 1
        
        return {
            "total_results": len(results),
            "average_score": avg_score,
            "score_range": {
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
            },
            "boost_distribution": boost_counts,
            "term_match_distribution": term_matches,
            "top_boosts": sorted(boost_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_matched_terms": sorted(term_matches.items(), key=lambda x: x[1], reverse=True)[:10],
        }

    def format_explanation_text(self, explanation: Dict[str, Any]) -> str:
        """
        Format explanation as human-readable text.
        
        Args:
            explanation: Explanation dictionary
            
        Returns:
            Formatted text
        """
        lines = []
        lines.append(f"Query: {explanation.get('query', 'N/A')}")
        lines.append(f"Document: {explanation.get('document_title', 'N/A')}")
        lines.append(f"Final Score: {explanation.get('final_score', 0.0):.3f}")
        
        if explanation.get("score_breakdown"):
            lines.append("\nScore Breakdown:")
            for key, value in explanation["score_breakdown"].items():
                if isinstance(value, dict):
                    score = value.get("score", value.get("weighted_score", value.get("value", 0)))
                    if score:
                        lines.append(f"  {key}: {score:.3f}")
        
        if explanation.get("boosts"):
            lines.append("\nBoosts Applied:")
            for boost in explanation["boosts"]:
                lines.append(f"  {boost['type']}: ×{boost['factor']:.1f}")
        
        if explanation.get("matched_terms"):
            lines.append(f"\nMatched Terms: {', '.join(explanation['matched_terms'])}")
        
        if explanation.get("reasons"):
            lines.append("\nRanking Reasons:")
            for reason in explanation["reasons"]:
                lines.append(f"  • {reason}")
        
        return "\n".join(lines)

    def get_component_importance(
        self,
        explanation: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Calculate importance of each ranking component.
        
        Args:
            explanation: Explanation dictionary
            
        Returns:
            Dictionary mapping component to importance (0-1)
        """
        importance = {}
        
        breakdown = explanation.get("score_breakdown", {})
        total = 0.0
        
        # Calculate raw contribution
        for key, value in breakdown.items():
            if isinstance(value, dict):
                score = value.get("weighted_score", value.get("score", 0.0))
                importance[key] = score
                total += score
        
        # Normalize to 0-1
        if total > 0:
            importance = {k: v / total for k, v in importance.items()}
        
        return importance