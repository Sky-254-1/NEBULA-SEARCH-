"""Tests for app/search/semantic/engine.py - SemanticEngine."""

import pytest
from unittest.mock import AsyncMock


class TestSemanticEngine:
    """Tests for SemanticEngine."""

    @pytest.fixture
    def engine(self):
        from app.search.semantic import SemanticEngine
        return SemanticEngine()

    def test_cosine_similarity_identical(self, engine):
        """Primary success path: identical vectors."""
        sim = engine._cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        assert sim == pytest.approx(1.0)

    def test_cosine_similarity_opposite(self, engine):
        """Primary success path: opposite vectors (normalized to 0)."""
        sim = engine._cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        # (cosine(-1) + 1) / 2 = 0
        assert sim == pytest.approx(0.0, abs=1e-10)

    def test_cosine_similarity_orthogonal(self, engine):
        """Orthogonal vectors give 0.5 (midpoint in 0-1 normalization)."""
        sim = engine._cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert sim == pytest.approx(0.5)

    def test_cosine_similarity_zero_vector(self, engine):
        """Failure path: zero vector."""
        assert engine._cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
        assert engine._cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0

    def test_cosine_similarity_empty_input(self, engine):
        """Failure path: empty vectors."""
        assert engine._cosine_similarity([], [1.0, 0.0]) == 0.0
        assert engine._cosine_similarity([1.0], [1.0, 0.0]) == 0.0

    @pytest.mark.asyncio
    async def test_rerank_empty(self, engine):
        """Failure path: rerank empty list."""
        result = await engine.rerank("query", [])
        assert result == []

    @pytest.mark.asyncio
    async def test_rerank_no_embeddings(self, engine):
        """Failure path: rerank without embedding provider returns originals."""
        docs = [{"id": "1", "score": 0.8}]
        result = await engine.rerank("query", docs)
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_get_embedding_no_provider(self, engine):
        """Failure path: get_embedding without provider."""
        import pytest
        with pytest.raises(ValueError, match="not initialized"):
            import asyncio
            asyncio.run(engine.get_embedding("test"))

    def test_get_embedding_with_provider(self, engine):
        """Primary success path: get_embedding."""
        mock_provider = AsyncMock()
        mock_provider.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        engine._embedding_provider = mock_provider

        import asyncio
        result = asyncio.run(engine.get_embedding("test"))
        assert result == [0.1, 0.2, 0.3]

    def test_clear_cache(self, engine):
        """Test clear_cache method."""
        engine._cache = {"key": "value"}
        engine.clear_cache()
        assert engine._cache == {}

    def test_health_check_no_providers(self, engine):
        """Health check with no providers initialized."""
        import asyncio
        result = asyncio.run(engine.health_check())
        assert result["embedding_provider"] is False
        assert result["vector_store"] is False

    def test_health_check_with_providers(self, engine):
        """Primary success path: health check."""
        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_vs = AsyncMock()
        mock_vs.health_check = AsyncMock(return_value=True)
        engine._embedding_provider = mock_provider
        engine._vector_store = mock_vs

        import asyncio
        result = asyncio.run(engine.health_check())
        assert result["embedding_provider"] is True
        assert result["vector_store"] is True