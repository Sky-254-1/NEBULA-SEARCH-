# Queue/Job Implementation Investigation Report

## Summary

The backend has a **dual-queue architecture** with two separate systems:

1. **Indexing Queue** (`app/indexing/queue.py`) - A priority queue for document indexing jobs with optional Redis persistence
2. **Job Queue** (`app/services/queue.py`) - A simple FIFO queue for background tasks

**The `index_document` job type is implemented in `app/services/queue.py` and processed by `vector/worker.py`, which calls `vector/pipeline.index_document()`.**

---

## Evidence

### 1. Queue Implementations

#### Indexing Queue (`app/indexing/queue.py`)
- **Class:** `IndexingQueue` - Thread-safe priority queue
- **Features:**
  - Priority-based ordering (SYSTEM > HIGH > NORMAL > LOW)
  - Redis persistence (optional) using sorted sets
  - Fallback to in-memory `deque` when Redis unavailable
  - Methods: `enqueue()`, `dequeue()`, `peek()`, `remove()`, `clear()`, `pause()`/`resume()`
  - Global instance: `indexing_queue`

#### Job Queue (`app/services/queue.py`)
- **Class:** `JobQueue`
- **Features:**
  - Simple FIFO queue using `deque`
  - Redis support via `queue:jobs` list
  - Methods: `enqueue(job_type, payload)`, `dequeue()`
  - Global instance: `job_queue`
- **Job structure:**
  ```python
  {
    "type": "index_document",
    "payload": {"document_id": int, "user_id": int, ...}
  }
  ```

### 2. Job Object Structure

#### In `app/services/queue.py`
```python
job = {
    "type": job_type,  # e.g., "index_document"
    "payload": payload  # dict with job-specific data
}
```

#### In `app/indexing/tasks.py` (Indexing-specific)
```python
job = {
    "job_id": str(uuid.uuid4()),
    "type": "index_document",  # or "reindex_document", "delete_document"
    "document_id": int,
    "user_id": Optional[int],
    "filename": str,
    "priority": JobPriority.NORMAL,
    "payload": {...},
    "created_at": float,
    "retry_count": int,
    "enqueue_time": float
}
```

### 3. Worker Pattern

#### Document Indexing Worker (`vector/worker.py`)
- **Process:** Polls `job_queue` (not `indexing_queue`)
- **Job Type:** `index_document`
- **Processing:**
  ```python
  async def process_job(job: dict) -> None:
      job_type = job.get("type")  # "index_document"
      payload = job.get("payload", {})
      document_id = payload.get("document_id")
      user_id = payload.get("user_id")
      attempts = payload.get("attempts", 0)
      
      db = await connect()
      try:
          success = await index_document(db, document_id, user_id)
          # Retry on failure (max 3 attempts)
          if not success and attempts + 1 < MAX_INDEX_ATTEMPTS:
              await job_queue.enqueue("index_document", {..., "attempts": attempts + 1})
      finally:
          await db.close()
  ```

#### Standalone Indexing Worker (`app/indexing/worker_entrypoint.py`)
- **Process:** Uses `app/indexing/worker.py` with `WorkerPool`
- **Queue:** `indexing_queue` (priority queue)
- **Features:**
  - Worker pool with configurable workers (default: 2)
  - Health monitoring via `app/indexing/health.py`
  - Progress tracking via `app/indexing/progress.py`
  - Retry logic via `app/indexing/retry.py`
  - Metrics via `app/indexing/metrics.py`
  - Dead-letter queue via `app/indexing/deadletter.py`

### 4. Document State Transitions

From `app/routes/documents.py` (upload):
```python
# Enqueue indexing job
await job_queue.enqueue("index_document", {
    "document_id": doc_id,
    "user_id": user_id
})
```

From `app/indexing/queue.py` and `app/indexing/tasks.py`:
- **Job priorities:** SYSTEM, HIGH, NORMAL, LOW
- **Document status field:** `documents.status` (pending → processing → indexed/failed)
- **Missing field mappings in database:**
  - `status TEXT DEFAULT 'pending'`
  - `content_hash TEXT`
  - `error_message TEXT`

### 5. Task Submission

From `app/indexing/tasks.py`:
```python
async def submit_index_task(...) -> str:
    task = TaskBuilder.create_index_task(...)
    job = {
        "job_id": task.task_id,
        "type": task.task_type,  # "index_document"
        "document_id": task.document_id,
        "user_id": task.user_id,
        "filename": task.filename,
        "priority": task.priority,
        "payload": task.payload,
        "created_at": task.created_at,
        "retry_count": 0,
    }
    return await indexing_queue.enqueue(job)  # Uses priority queue
```

---

## Conclusions

### Current State

1. **Dual Queue Architecture:**
   - `app/services/queue.py` - Simple FIFO for `index_document` jobs
   - `app/indexing/queue.py` - Priority queue for advanced indexing features

2. **Worker Implementation:**
   - **Production worker** (`vector/worker.py`) reads from `job_queue`
   - **Standalone worker** (`app/indexing/worker_entrypoint.py`) uses priority queue
   - The production worker calls `vector/pipeline.index_document(db, doc_id, user_id)`

3. **Missing Implementation:**
   - **No document state transitions** (pending → processing → indexed/failed)
   - **No concurrency protection** (lock/reindex checks)
   - **No ownership validation before indexing**
   - Database columns missing: `status`, `content_hash`, `error_message`

4. **Retry Logic:**
   - Basic retry in `vector/worker.py` (3 attempts, no backoff)
   - Sophisticated retry in `app/indexing/retry.py` (exponential backoff)

### Recommendations

1. **Implement Document State Transitions:**
   - Add `status`, `content_hash`, `error_message` columns
   - Update `document.status` in worker before/after indexing
   - Mark as `processing` when job starts, `indexed` on success, `failed` on failure

2. **Add Ownership Validation:**
   - Verify `user_id` matches document ownership before processing
   - Check in `vector/pipeline.index_document()` or worker wrapper

3. **Implement Concurrency Protection:**
   - Add database lock or status check to prevent concurrent reindexing
   - Skip jobs if document already `processing` or `indexed`

4. **Choose Single Queue Strategy:**
   - **Option A:** Migrate to priority queue (`app/indexing/queue.py`) for better control
   - **Option B:** Add Redis persistence to `job_queue` for production durability

5. **Standardize Retry Logic:**
   - Use `app/indexing/retry.py` for consistent exponential backoff
   - Implement bounded retry attempts with dead-letter queue

---

## Files Referenced

| File | Purpose |
|------|---------|
| `backend/app/services/queue.py` | FIFO job queue with Redis support |
| `backend/app/indexing/queue.py` | Priority queue with Redis persistence |
| `backend/app/indexing/tasks.py` | Task definitions and builders |
| `backend/app/indexing/worker.py` | Worker class with health/metrics |
| `backend/app/indexing/worker_entrypoint.py` | Worker process entrypoint |
| `backend/vector/worker.py` | Production indexing worker |
| `backend/app/indexing/retry.py` | Exponential backoff retry logic |
| `backend/app/indexing/progress.py` | Job progress tracking |
| `backend/app/indexing/health.py` | Worker health monitoring |
| `backend/app/indexing/metrics.py` | Metrics collection |
| `backend/app/indexing/deadletter.py` | Dead-letter queue management |
| `backend/app/indexing/scheduler.py` | Scheduled task execution |
| `backend/tests/test_indexing.py` | Comprehensive test suite |
| `backend/app/routes/documents.py` | Document upload endpoint |
| `backend/app/database/repositories/document.py` | Document repository |
| `backend/app/database/migrations/004_sqlite_indexing.sql` | Indexing schema |

---

## Next Steps

1. Apply database migration to add missing columns to `documents` table
2. Implement document state transitions in worker
3. Add ownership validation before processing
4. Add concurrency protection to prevent duplicate processing
5. Decide on single queue strategy (priority vs. simple FIFO)
6. Add comprehensive tests for worker behavior