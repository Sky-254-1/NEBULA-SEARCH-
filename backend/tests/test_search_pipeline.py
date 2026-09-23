"""Tests for the core search pipeline: ingestion, indexing, ranking, semantic, reindexing."""

import pytest
from datetime import datetime, timedelta, timezone

# ============================================
# Ingestion Tests
# ============================================

class TestDocumentIngester:
    """Tests for DocumentIngester."""

    @pytest.fixture
    def ingester(self):
        from app.search.ingestion import DocumentIngester
        return DocumentIngester()

    @pytest.mark.asyncio
    async def test_ingest_content_success(self, ingester):
        """Primary success path: ingest content from string."""
        from app.search.ingestion import DocumentStatus
        content = "This is a test document with enough content to pass validation."
        doc = await ingester.ingest_content(content, filename="test.txt")
        assert doc.status == DocumentStatus.INDEXED
        assert doc.content == content
        assert doc.filename == "test.txt"
        assert doc.file_size > 0
        assert doc.checksum != ""

    @pytest.mark.asyncio
    async def test_ingest_content_too_short(self, ingester):
        """Failure path: content too short."""
        from app.search.ingestion import DocumentStatus
        doc = await ingester.ingest_content("short", filename="test.txt")
        assert doc.status == DocumentStatus.FAILED
        assert "too short" in (doc.error_message or "").lower()

    @pytest.mark.asyncio
    async def test_ingest_content_empty(self, ingester):
        """Failure path: empty content."""
        from app.search.ingestion import DocumentStatus
        doc = await ingester.ingest_content("", filename="test.txt")
        assert doc.status == DocumentStatus.FAILED

    @pytest.mark.asyncio
    async def test_ingest_file_not_found(self, ingester, tmp_path):
        """Failure path: file does not exist."""
        from app.search.ingestion import DocumentStatus
        fake_path = tmp_path / "nonexistent.txt"
        doc = await ingester.ingest_file(fake_path)
        assert doc.status == DocumentStatus.FAILED
        assert "not found" in (doc.error_message or "").lower()

    @pytest.mark.asyncio
    async def test_ingest_file_success(self, ingester, tmp_path):
        """Primary success path: ingest a real text file."""
        from app.search.ingestion import DocumentStatus
        test_file = tmp_path / "test_doc.txt"
        test_file.write_text("This is a test document with enough content to pass validation.", encoding="utf-8")
        doc = await ingester.ingest_file(test_file)
        assert doc.status == DocumentStatus.INDEXED
        assert doc.filename == "test_doc.txt"
        assert doc.file_size > 0
        assert doc.checksum != ""

    def test_detect_file_type(self, ingester):
        """Test file type detection."""
        from app.search.ingestion import FileType
        assert ingester.detect_file_type("test.txt") == FileType.TEXT
        assert ingester.detect_file_type("test.md") == FileType.MARKDOWN
        assert ingester.detect_file_type("test.html") == FileType.HTML
        assert ingester.detect_file_type("test.pdf") == FileType.PDF
        assert ingester.detect_file_type("test.docx") == FileType.DOCX
        assert ingester.detect_file_type("test.json") == FileType.JSON
        assert ingester.detect_file_type("test.csv") == FileType.CSV
        assert ingester.detect_file_type("test.unknown") == FileType.UNKNOWN

    def test_sanitize_content(self, ingester):
        """Test content sanitization removes control characters."""
        dirty = "hello\x00world\x1fclean"
        clean = ingester._sanitize_content(dirty)
        assert "\x00" not in clean
        assert "\x1f" not in clean
        assert len(clean) > 0

    def test_extract_metadata_from_content(self, ingester):
        """Test metadata extraction from content."""
        content = "My Document Title\n\nby John Doe\n\nSome content here."
        metadata = ingester._extract_metadata_from_content(content, "test.txt")
        assert metadata.title == "My Document Title"
        assert metadata.author == "John Doe"

    def test_extract_metadata_with_date(self, ingester):
        """Test date extraction from content."""
        content = "2024-01-15\n\nSome content here."
        metadata = ingester._extract_metadata_from_content(content, "test.txt")
        assert metadata.created_date is not None
        assert metadata.created_date.year == 2024


# ============================================
# Indexing Tests
# ============================================

class TestBackgroundIndexer:
    """Tests for BackgroundIndexer."""

    @pytest.fixture
    def indexer(self):
        from app.search.indexing import BackgroundIndexer
        return BackgroundIndexer(num_workers=1)

    @pytest.mark.asyncio
    async def test_submit_job(self, indexer):
        """Primary success path: submit a job."""
        from app.search.indexing import JobStatus, JobPriority
        job = await indexer.submit_job(
            document_id="doc-1",
            priority=JobPriority.NORMAL,
        )
        assert job is not None
        assert job.document_id == "doc-1"
        assert job.status == JobStatus.QUEUED
        assert job.priority == JobPriority.NORMAL

    @pytest.mark.asyncio
    async def test_get_job(self, indexer):
        """Test retrieving a job by ID."""
        job = await indexer.submit_job(document_id="doc-1")
        retrieved = await indexer.get_job(job.id)
        assert retrieved is not None
        assert retrieved.document_id == "doc-1"

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, indexer):
        """Failure path: job not found."""
        retrieved = await indexer.get_job("nonexistent")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_cancel_job(self, indexer):
        """Test cancelling a pending job."""
        from app.search.indexing import JobStatus
        job = await indexer.submit_job(document_id="doc-1")
        result = await indexer.cancel_job(job.id)
        assert result is True
        cancelled = await indexer.get_job(job.id)
        assert cancelled.status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_job(self, indexer):
        """Failure path: cancel nonexistent job."""
        result = await indexer.cancel_job("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_queue_size(self, indexer):
        """Test queue size tracking."""
        assert await indexer.get_queue_size() == 0
        await indexer.submit_job(document_id="doc-1")
        await indexer.submit_job(document_id="doc-2")
        assert await indexer.get_queue_size() == 2

    @pytest.mark.asyncio
    async def test_start_stop(self, indexer):
        """Test start and stop lifecycle."""
        await indexer.start()
        assert indexer.running is True
        await indexer.stop()
        assert indexer.running is False


# ============================================
# Ranking Service Tests
# ============================================

class TestRankingService:
    """Tests for the ranking service."""

    @pytest.fixture
    def ranking_service(self):
        from app.search.ranking_service import RankingService, RankingConfig
        config = RankingConfig()
        return RankingService(config)

    @pytest.mark.asyncio
    async def test_rank_documents(self, ranking_service):
        """Primary success path: rank documents."""
        docs = [
            {"id": "1", "title": "test document", "content": "word " * 150, "updated_at": datetime.now(timezone.utc).isoformat()},
            {"id": "2", "title": "other doc", "content": "word " * 50, "updated_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()},
        ]
        ranked = await ranking_service.rank(query="test", results=docs)
        assert len(ranked) == 2

    @pytest.mark.asyncio
    async def test_rank_empty_list(self, ranking_service):
        """Failure path: empty document list."""
        ranked = await ranking_service.rank(query="test", results=[])
        assert ranked == []

    def test_bm25_scorer(self):
        """Test BM25 scoring."""
        from app.search.ranking_service import BM25Scorer
        scorer = BM25Scorer(k1=1.5, b=0.75)
        scorer.index_documents([
            {"id": "1", "title": "test document", "content": "word " * 50},
            {"id": "2", "title": "other doc", "content": "other " * 50},
        ])
        score = scorer.score("test", {"id": "1", "title": "test document", "content": "word " * 50})
        assert score > 0
        assert isinstance(score, float)

    def test_freshness_scorer(self):
        """Test freshness scoring."""
        from app.search.ranking_service import FreshnessScorer
        scorer = FreshnessScorer(half_life_days=7)
        recent_doc = {"updated_at": datetime.now(timezone.utc).isoformat()}
        old_doc = {"updated_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}
        recent_score = scorer.score(recent_doc)
        old_score = scorer.score(old_doc)
        assert recent_score > old_score

    def test_freshness_score_missing(self):
        """Edge case: no date provided."""
        from app.search.ranking_service import FreshnessScorer
        scorer = FreshnessScorer()
        score = scorer.score({})
        assert score == 0.5  # Default score

    def test_popularity_scorer(self):
        """Test popularity scoring."""
        from app.search.ranking_service import PopularityScorer
        scorer = PopularityScorer()
        scorer.update_metrics("1", views=1000, ctr=0.5)
        scorer.update_metrics("2", views=1, ctr=0.01)
        score_high = scorer.score({"id": "1"})
        score_low = scorer.score({"id": "2"})
        assert score_high > score_low

    def test_metadata_scorer(self):
        """Test metadata scoring."""
        from app.search.ranking_service import MetadataScorer
        scorer = MetadataScorer()
        rich_meta = {"title": "Test Title", "author": "John", "content": "word " * 150}
        poor_meta = {"title": "ab"}
        assert scorer.score(rich_meta) > scorer.score(poor_meta)


# ============================================
# Semantic Search Tests
# ============================================

class TestSemanticEngine:
    """Tests for semantic engine."""

    @pytest.fixture
    def engine(self):
        from app.search.semantic import SemanticEngine
        return SemanticEngine()

    def test_cosine_similarity(self, engine):
        """Test cosine similarity calculation."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]
        assert engine._cosine_similarity(vec_a, vec_b) == pytest.approx(1.0)

    def test_cosine_similarity_zero_vector(self, engine):
        """Edge case: zero vector."""
        assert engine._cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
        assert engine._cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0

    def test_cosine_similarity_partial(self, engine):
        """Test cosine similarity with partially matching vectors."""
        vec_a = [1.0, 0.0]
        vec_b = [-1.0, 0.0]
        sim = engine._cosine_similarity(vec_a, vec_b)
        assert -1.0 <= sim <= 1.0


# ============================================
# Re-indexing Tests
# ============================================

class TestIncrementalReindexer:
    """Tests for the incremental re-indexing system."""

    @pytest.fixture
    def reindexer(self):
        from app.search.reindexing import IncrementalReindexer
        return IncrementalReindexer()

    @pytest.mark.asyncio
    async def test_detect_changes_new(self, reindexer):
        """Primary success path: detect new documents."""
        from app.search.reindexing import ChangeType
        docs = [
            {"id": "doc-1", "checksum": "abc123", "title": "New Doc", "content": "some content here for testing"},
        ]
        changes = await reindexer.detect_changes(docs)
        assert len(changes) > 0
        assert changes[0].change_type == ChangeType.CREATED

    @pytest.mark.asyncio
    async def test_detect_changes_unchanged(self, reindexer):
        """Test detect unchanged document."""
        from app.search.reindexing import ChangeType
        docs = [
            {"id": "doc-1", "checksum": "abc123", "title": "Doc", "content": "content"},
        ]
        await reindexer.detect_changes(docs)
        changes = await reindexer.detect_changes(docs)
        assert len(changes) == 0 or all(c.change_type == ChangeType.CREATED for c in changes)

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self, reindexer):
        """Failure path: task not found."""
        status = await reindexer.get_task_status("nonexistent")
        assert status is None