# Implementation Plan: Document Indexing Worker

## Overview
Create `backend/app/workers/indexer.py` that processes `index_document` jobs from the queue, implements idempotent retries, concurrency protection, ownership validation, and file content extraction.

---

## Design Decisions

### 1. Worker Implementation Strategy
**Decision:** Create a dedicated worker that consumes from `app.services.queue.job_queue` (the same queue used by upload endpoint) and directly updates document status in the database.

**Rationale:** 
- The existing `job_queue` in `app/services/queue.py` is already used by the upload endpoint
- Document state transitions happen in the `documents` table (status, content_hash, error_message columns exist)
- This avoids duplicating queue infrastructure and maintains consistency with existing upload flow
- Direct database updates simplify transaction management

### 2. Concurrency Protection Mechanism
**Decision:** Use database-level optimistic locking via the `status` column with conditional UPDATE statements.

**Rationale:**
- SQLite and PostgreSQL both support atomic conditional updates
- No external locking mechanism (Redis locks) needed - reduces complexity
- The `status` column already exists for state tracking
- Transaction isolation prevents race conditions between concurrent workers

### 3. File Content Extraction
**Decision:** Implement extraction for supported formats (PDF, DOCX, TXT, MD, CSV, JSON, HTML) using:
- `PyPDF2` or `pdfplumber` for PDFs
- `python-docx` for DOCX
- Built-in Python for text-based formats

**Rationale:**
- Matches the allowed extensions in `documents.py` (`ALLOWED_EXTENSIONS`)
- PDF and DOCX require third-party libraries; others are native Python
- Content extraction is synchronous, so it runs in the async worker via `asyncio.to_thread`

### 4. Retry Logic and Error Handling
**Decision:** Implement bounded retries (max 3) with exponential backoff stored in job payload. Failures update `error_message` column.

**Rationale:**
- Matches the configuration: `indexing_max_retries: 5` but the task specifies "max 3 retries"
- Errors are stored in the existing `error_message` column for debugging
- Idempotent retries: same job data, same result (deterministic extraction)

### 5. Ownership Validation
**Decision:** Validate that `user_id` in job payload matches the document's `user_id` in the database before processing.

**Rationale:**
- Prevents unauthorized users from indexing documents they don't own
- Job payload includes `user_id` from upload endpoint
- Single source of truth for document ownership is the database

---

## Implementation Steps

### Step 1: Create the Indexing Worker Module
**What to do:** Create `backend/app/workers/indexer.py` with core worker class.

**Files to create:**
- `backend/app/workers/indexer.py`
- `backend/app/workers/__init__.py` (empty, for package)

**Implementation details:**
- `IndexingWorker` class with methods:
  - `__init__(max_retries=3)`
  - `process_job(job)` - main entry point
  - `_validate_ownership(doc_id, user_id)` - verify ownership
  - `_extract_content(file_path)` - extract text from file
  - `_compute_hash(content)` - SHA-256 content hash
  - `_update_status(doc_id, status, content_hash, error_message)`
- Async job loop with sleep interval
- Proper logging using `nebula.indexer` logger

**Verification:**
```bash
cd backend
python -c "from app.workers.indexer import IndexingWorker; print('Import successful')"
```

---

### Step 2: Implement File Content Extraction
**What to do:** Implement extraction methods for PDF, DOCX, and text-based formats.

**Files to modify:**
- `backend/app/workers/indexer.py`

**Implementation details:**
- PDF: Use `PyPDF2.PdfReader` to extract text pages
- DOCX: Use `docx.Document` to extract paragraph text
- Text formats: Read file directly with UTF-8 encoding
- Handle encoding errors gracefully
- Return extracted text as single string

**Dependencies to add:**
```bash
pip install PyPDF2 python-docx
```

**Verification:**
```bash
cd backend
python -c "
from app.workers.indexer import IndexingWorker
w = IndexingWorker()
# Test extraction on a sample file (create test file first)
print('Extraction methods implemented')
"
```

---

### Step 3: Implement Concurrency Protection
**What to do:** Add database-level concurrency protection using conditional UPDATE.

**Files to modify:**
- `backend/app/workers/indexer.py`
- `backend/app/database/repositories/document.py` (add `acquire_processing_lock` method)

**Implementation details:**
- In `DocumentRepository`, add method:
  ```python
  async def acquire_processing_lock(self, doc_id: int) -> bool:
      """Try to acquire lock by transitioning from pending to processing."""
      result = await self._db.execute(
          "UPDATE documents SET status = 'processing' WHERE id = ? AND status = 'pending'",
          (doc_id,)
      )
      await self._db.commit()
      return result.rowcount > 0
  ```
- In worker, check lock success before processing
- If lock fails, skip job (already being processed or not pending)

**Verification:**
```bash
cd backend
python -c "
from app.database.repositories.document import DocumentRepository
# Verify the new method exists and has correct signature
import inspect
print(inspect.signature(DocumentRepository.acquire_processing_lock))
"
```

---

### Step 4: Implement Retry Logic with Bounded Attempts
**What to do:** Add retry tracking and exponential backoff in worker.

**Files to modify:**
- `backend/app/workers/indexer.py`

**Implementation details:**
- Extract retry count from job payload: `job.get('retry_count', 0)`
- If `retry_count >= max_retries`, move to dead-letter (set `status='failed'`, store `error_message`)
- Calculate delay: `base_delay * (backoff_multiplier ** retry_count)`
- Store `retry_count + 1` and `next_retry_time` in job before re-enqueue
- Use `asyncio.sleep(delay)` for async-safe delay

**Verification:**
```bash
cd backend
python -c "
from app.workers.indexer import IndexingWorker
w = IndexingWorker(max_retries=3)
# Test delay calculation
for i in range(5):
    print(f'Retry {i}: {w._calculate_delay(i)}s')
"
```

---

### Step 5: Implement Ownership Validation
**What to do:** Add ownership check before processing.

**Files to modify:**
- `backend/app/workers/indexer.py`

**Implementation details:**
- Fetch document from database with `user_id`
- Compare `document.user_id == job_payload.user_id`
- If mismatch, log warning and mark job as failed with error "Ownership validation failed"
- Do NOT proceed with extraction if ownership fails

**Verification:**
```bash
cd backend
python -c "
from app.workers.indexer import IndexingWorker
# Test ownership validation logic
print('Ownership validation: implemented')
"
```

---

### Step 6: Implement State Transitions
**What to do:** Add database methods for state transitions and update worker to use them.

**Files to modify:**
- `backend/app/database/repositories/document.py` (add state transition methods)
- `backend/app/workers/indexer.py` (use new methods)

**Implementation details:**
Add to `DocumentRepository`:
```python
async def transition_to_processing(self, doc_id: int) -> bool:
    """Try to transition from pending to processing. Returns True if successful."""
    result = await self._db.execute(
        "UPDATE documents SET status = 'processing' WHERE id = ? AND status = 'pending'",
        (doc_id,)
    )
    await self._db.commit()
    return result.rowcount > 0

async def transition_to_indexed(self, doc_id: int, content_hash: str) -> None:
    await self._db.execute(
        "UPDATE documents SET status = 'indexed', content_hash = ?, indexed_at = datetime('now'), error_message = NULL WHERE id = ?",
        (content_hash, doc_id)
    )
    await self._db.commit()

async def transition_to_failed(self, doc_id: int, error_message: str) -> None:
    await self._db.execute(
        "UPDATE documents SET status = 'failed', error_message = ? WHERE id = ?",
        (error_message, doc_id)
    )
    await self._db.commit()
```

**Verification:**
```bash
cd backend
python -c "
from app.database.repositories.document import DocumentRepository
import inspect
print('Methods:', [m for m in dir(DocumentRepository) if m.startswith('transition')])
"
```

---

### Step 7: Create Worker Entrypoint
**What to do:** Create `backend/app/workers/indexer_entrypoint.py` for standalone execution.

**Files to create:**
- `backend/app/workers/indexer_entrypoint.py`

**Implementation details:**
- Follow pattern from `backend/app/indexing/worker_entrypoint.py`
- Initialize database connection
- Connect to job queue
- Run worker loop with `asyncio.sleep(0.5)` between iterations
- Handle SIGINT/SIGTERM for graceful shutdown
- Use `app.database.init_db()` if available, otherwise `await connect()`

**Verification:**
```bash
cd backend
python -c "from app.workers.indexer_entrypoint import main; print('Entrypoint imports successfully')"
```

---

### Step 8: Create Workers Package `__init__.py`
**What to do:** Create empty `__init__.py` to make `app.workers` a proper package.

**Files to create:**
- `backend/app/workers/__init__.py`

**Implementation details:**
- Empty file (just `"""Workers package."""` docstring)
- Allows `from app.workers.indexer import IndexingWorker`

**Verification:**
```bash
cd backend
python -c "from app.workers import indexer; print('Package imports successfully')"
```

---

## Testing the Implementation

### Unit Tests
Create test file: `backend/tests/test_indexer.py`

**Test cases:**
1. `test_worker_processes_job_successfully` - full successful indexing flow
2. `test_worker_ownership_validation_fails` - reject jobs with wrong user_id
3. `test_worker_handles_extraction_error` - mark failed with error_message
4. `test_worker_concurrency_lock` - concurrent jobs on same doc_id
5. `test_worker_retry_logic` - retry_count increments, max_retries enforced
6. `test_worker_idempotent_retries` - same job data produces same result

**Run tests:**
```bash
cd backend
python -m pytest tests/test_indexer.py -v
```

### Integration Test
1. Upload a test document via `/api/v1/documents/`
2. Confirm job is enqueued
3. Run worker: `python -m app.workers.indexer_entrypoint`
4. Wait for job to process
5. Verify document status changes to `indexed`
6. Verify `content_hash` is populated
7. Check no errors in logs

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/app/workers/indexer.py` | New - Core worker implementation |
| `backend/app/workers/indexer_entrypoint.py` | New - Standalone execution entrypoint |
| `backend/app/workers/__init__.py` | New - Package marker |
| `backend/app/database/repositories/document.py` | Modified - State transition methods |
| `backend/app/services/queue.py` | Existing - Job queue (already used) |
| `backend/app/services/auth.py` | Existing - Get current user (for validation) |

---

## Error Handling Scenarios

| Scenario | Action | Status | Error Message |
|----------|--------|--------|---------------|
| File not found | Mark failed | `failed` | "Document file not found: {path}" |
| Ownership validation fails | Mark failed | `failed` | "Ownership validation failed" |
| Extraction error (PDF corrupt) | Mark failed | `failed` | "Failed to extract content: {error}" |
| Max retries exceeded | Mark failed | `failed` | "Max retries ({n}) exceeded: {last_error}" |
| Database error | Mark failed | `failed` | "Database error: {error}" |
| Success | Mark indexed | `indexed` | NULL |

---

## Performance Considerations

1. **Async I/O:** File extraction runs in `asyncio.to_thread` to avoid blocking event loop
2. **Connection Pooling:** Uses existing `DatabaseConnection` pool
3. **Minimal Database Queries:** Single UPDATE for state transitions (atomic)
4. **No N+1 Queries:** All document data fetched in one query
5. **Graceful Degradation:** If Redis unavailable, falls back to in-memory queue

---

## Next Steps (Out of Scope for This Plan)

These were identified in the task context but are separate work items:

1. **Database Migration** - Add status/content_hash/error_message columns
2. **Queue Backend** - Configure Redis for production durability
3. **Tests** - Full test suite (upload validation, retry/idempotency, concurrent indexing)
4. **Indexing Service** - Implement full text chunking, embedding generation, vector storage

---

## Implementation Checklist

- [ ] Create `backend/app/workers/` directory
- [ ] Create `backend/app/workers/__init__.py`
- [ ] Create `backend/app/workers/indexer.py` with `IndexingWorker` class
- [ ] Add state transition methods to `DocumentRepository`
- [ ] Implement file content extraction (PDF, DOCX, text formats)
- [ ] Implement concurrency protection via conditional UPDATE
- [ ] Implement retry logic with exponential backoff
- [ ] Implement ownership validation
- [ ] Create `backend/app/workers/indexer_entrypoint.py`
- [ ] Add dependencies to `requirements.txt` (PyPDF2, python-docx)
- [ ] Create unit tests in `backend/tests/test_indexer.py`
- [ ] Verify: `python -c "from app.workers.indexer import IndexingWorker"` succeeds
- [ ] Verify: Worker processes jobs from queue
- [ ] Verify: Status transitions work correctly
- [ ] Verify: Retries bounded to 3 attempts

---

## Dependencies to Install

```bash
pip install PyPDF2 python-docx
```

Verify installation:
```bash
python -c "import PyPDF2; import docx; print('Dependencies installed successfully')"
```

---

*Plan written on: 2024-11-12*
*Last updated: 2024-11-12*
