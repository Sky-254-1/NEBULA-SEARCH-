"""Phase 2 behavioral coverage expansion.

Targets:
- hybrid/ranking.py (HybridRanker)
- Additional edge cases for existing services
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.hybrid.ranking import HybridRanker
from app.hybrid.config import HybridSearchConfig


# =============================================================
# HybridRanker  (pure logic, sub-components mocked)
# =============================================================
class TestHybridRanker:
    def test_init_default_config(self):
        ranker = HybridRanker()
        assert ranker.config is not None
        assert ranker.bm25_engine is not None
        assert ranker.semantic_engine is not None
        assert ranker.metadata_booster is not None
        assert ranker.normalizer is not None

    def test_init_custom_config(self):
        config = HybridSearchConfig(bm25_weight=0.3, semantic_weight=0.7)
        ranker = HybridRanker(config=config)
        assert ranker.config.bm25_weight == 0.3
        assert ranker.config.semantic_weight == 0.7

    def test_rank_empty_documents(self):
        ranker = HybridRanker()
        result = ranker.rank("test query", documents=[])
        assert result == []

    def test_rank_with_documents(self):
        ranker = HybridRanker()
        docs = [
            {"id": 1, "title": "Python programming", "content": "Python is great"},
            {"id": 2, "title": "Java programming", "content": "Java is also great"},
        ]
        result = ranker.rank("python", documents=docs, top_k=5)
        assert len(result) == 2
        for doc in result:
            assert "score" in doc
            assert "keyword_score" in doc
            assert "semantic_score" in doc
            assert "fused_score" in doc

    def test_rank_top_k(self):
        ranker = HybridRanker()
        docs = [{"id": i, "title": f"Document {i}"} for i in range(10)]
        result = ranker.rank("test", documents=docs, top_k=3)
        assert len(result) == 3

    def test_rank_with_query_vector(self):
        ranker = HybridRanker()
        docs = [
            {"id": 1, "title": "Python", "embedding": [0.1, 0.2, 0.3]},
        ]
        result = ranker.rank("python", query_vector=[0.1, 0.2, 0.3], documents=docs)
        assert len(result) == 1
        assert result[0]["semantic_score"] >= 0

    def test_rank_with_metadata_boost(self):
        config = HybridSearchConfig(enable_metadata_boost=True, title_boost=1.5)
        ranker = HybridRanker(config=config)
        docs = [
            {"id": 1, "title": "Python programming guide"},
            {"id": 2, "title": "Java tutorial"},
        ]
        result = ranker.rank("python", documents=docs)
        python_doc = next(d for d in result if d["id"] == 1)
        assert python_doc.get("boost_multiplier", 1.0) >= 1.0

    def test_rank_with_metadata_boost_disabled(self):
        config = HybridSearchConfig(enable_metadata_boost=False, title_boost=1.5)
        ranker = HybridRanker(config=config)
        docs = [
            {"id": 1, "title": "Python programming guide"},
        ]
        result = ranker.rank("python", documents=docs)
        assert "boost_factors" not in result[0]

    def test_rank_with_tags_boost(self):
        config = HybridSearchConfig(enable_metadata_boost=True, tag_boost=1.3)
        ranker = HybridRanker(config=config)
        docs = [
            {"id": 1, "title": "Article", "tags": ["python", "programming"]},
            {"id": 2, "title": "Article", "tags": ["java"]},
        ]
        result = ranker.rank("python", documents=docs)
        python_doc = next(d for d in result if d["id"] == 1)
        assert python_doc.get("boost_multiplier", 1.0) >= 1.0

    def test_rank_with_headings_boost(self):
        config = HybridSearchConfig(enable_metadata_boost=True, heading_boost=1.2)
        ranker = HybridRanker(config=config)
        docs = [
            {"id": 1, "title": "Article", "headings": ["Python basics", "Advanced"]},
        ]
        result = ranker.rank("python", documents=docs)
        assert result[0].get("boost_multiplier", 1.0) >= 1.0

    def test_explain_ranking(self):
        ranker = HybridRanker()
        doc = {"id": 1, "title": "Python programming"}
        explanation = ranker.explain_ranking("python", doc)
        assert explanation["query"] == "python"
        assert explanation["document_id"] == 1
        assert "scores" in explanation
        assert "factors" in explanation
        assert "final_score" in explanation
        assert "calculation" in explanation

    def test_explain_ranking_with_vector(self):
        ranker = HybridRanker()
        doc = {"id": 1, "title": "Python", "embedding": [0.1, 0.2, 0.3]}
        explanation = ranker.explain_ranking("python", doc, query_vector=[0.1, 0.2, 0.3])
        assert explanation["scores"]["semantic"]["score"] >= 0

    def test_explain_ranking_title_match_factor(self):
        ranker = HybridRanker()
        doc = {"id": 1, "title": "Python programming"}
        explanation = ranker.explain_ranking("python", doc)
        factor_types = [f["type"] for f in explanation["factors"]]
        assert "title_match" in factor_types

    def test_get_statistics(self):
        ranker = HybridRanker()
        stats = ranker.get_statistics()
        assert "bm25" in stats
        assert "semantic" in stats
        assert "config" in stats
        assert stats["config"]["bm25_weight"] == ranker.config.bm25_weight

    def test_score_document_no_embedding(self):
        ranker = HybridRanker()
        doc = {"id": 1, "title": "Python"}
        result = ranker._score_document("python", None, doc, None)
        assert result["semantic_score"] == 0.0
        assert result["keyword_score"] >= 0

    def test_score_document_with_embedding_no_vector(self):
        ranker = HybridRanker()
        doc = {"id": 1, "title": "Python", "embedding": [0.1, 0.2, 0.3]}
        result = ranker._score_document("python", None, doc, None)
        assert result["semantic_score"] == 0.0

    def test_score_document_score_breakdown(self):
        ranker = HybridRanker()
        doc = {"id": 1, "title": "Python"}
        result = ranker._score_document("python", None, doc, None)
        assert "score_breakdown" in result
        breakdown = result["score_breakdown"]
        assert "keyword" in breakdown
        assert "semantic" in breakdown
        assert "final" in breakdown


# =============================================================
# Additional RBAC edge cases
# =============================================================
class TestRBACAdditional:
    def test_can_access_resource_unknown_role(self):
        from app.services.rbac import RBACService
        assert RBACService.can_access_resource("unknown_role", "searches", "read") is False

    def test_get_user_permissions_unknown_role(self):
        from app.services.rbac import RBACService
        perms = RBACService.get_user_permissions("unknown_role", ["custom.perm"])
        assert perms == ["custom.perm"]

    def test_check_permission_with_explicit_perms(self):
        from app.services.rbac import RBACService
        assert RBACService.check_permission("user", "custom.perm", ["custom.perm"]) is True