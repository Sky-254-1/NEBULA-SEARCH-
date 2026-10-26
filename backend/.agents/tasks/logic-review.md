# Indexer Implementation Review

**Date:** 2024-11-25  
**Target:** `backend/app/workers/indexer.py`  
**Workflow:** wf_e202ac64e33082dc  

---

## Executive Summary

The indexer implementation **contains critical correctness and security issues** that prevent safe deployment:

1. **Database connection leak** - `self._db` is never initialized, causing `AttributeError`
2. **Duplicate key violation risk** - `count_all()` method has unreachable code after return statement
3. **Missing validation in job queue processing** - No check for job type before processing
4. **Security vulnerability** - `_sanitize_path` uses relative path resolution that can be bypassed
5. **Race condition** - Database operations inside `_process_job` commit immediately, breaking transactional consistency

**Verdict:** **CHANGES_REQUESTED** - These blockers must be resolved before approval.

---

## Detailed Findings

### 1. Critical: Database Connection Never Initialized

**Location:** `indexer.py:39-42`, `indexer.py:84-88`

**Evidence:**
```python
async def _get_db(self) -> DatabaseConnection:
    """Get or create database connection."""
    if self._db is None:
        self._db = await get_db()
    return self._db

async def connect(self) -> None:
    """Initialize database connection pool."""
    from app.database import init_db
    await init_db()
    logger.info("Indexing worker connected to database")
```

**Problem:**
- `connect()` calls `init_db()` but never assigns a connection to `self._db`
- `_get_db()` attempts to create a connection via `get_db()` but this is inconsistent
- When `_get_db()` is called after `connect()`, it will call `get_db()` instead of reusing a connection

**Impact:**
- Every call to `_get_db()` creates a new database connection
- No connection pooling or reuse occurs
- Resource exhaustion under load

**Correction:**
```python
async def connect(self) -> None:
    """Initialize database connection pool."""
    from app.database import init_db
    await init_db()
    self._db = await get_db()  # <-- MISSING: Assign connection
    logger.info("Indexing worker connected to database")
```

---

### 2. Critical: Unreachable Code in DocumentRepository.count_all()

**Location:** `document.py:110-114`

**Evidence:**
```python
async def count_all(self) -> int:
    """Return total document count across all users."""
    row = await self._db.fetchone("SELECT COUNT(*) as count FROM documents")
async def count_for_user(self, user_id: int) -> int:
    """Return total non-deleted document count for a user."""
    row = await self._db.fetchone(
        "SELECT COUNT(*) as cnt FROM documents WHERE user_id = ? AND is_deleted = FALSE",
        (user_id,),
    )
    return int(row["cnt"]) if row else 0
    return int(row["count"]) if row else 0
```

**Problem:**
- `count_all()` method is missing `return` statement entirely
- `count_for_user()` has **two** return statements - the second one is unreachable
- The method returns the user count result variable but never returns the value

**Impact:**
- `count_all()` returns `None` instead of an integer
- `count_for_user()` may return incorrect values due to unreachable code

**Correction:**
```python
async def count_all(self) -> int:
    """Return total document count across all users."""
    row = await self._db.fetchone("SELECT COUNT(*) as count FROM documents")
    return int(row["count"]) if row else 0

async def count_for_user(self, user_id: int) -> int:
    """Return total non-deleted document count for a user."""
    row = await self._db.fetchone(
        "SELECT COUNT(*) as cnt FROM documents WHERE user_id = ? AND is_deleted = FALSE",
        (user_id,),
    )
    return int(row["cnt"]) if row else 0
```

---

### 3. High: Missing Job Type Validation

**Location:** `indexer.py:259-262`

**Evidence:**
```python
async def run(self, sleep_interval: float = 0.5) -> None:
    """Main worker loop with job acknowledgment pattern."""
    logger.info("Starting indexing worker loop")
    try:
        while True:
            job = await job_queue.dequeue()
            if job:
                try:
                    await self._process_job(job)
```

**Problem:**
- No validation that `job["type"] == "index_document"` before calling `_process_job()`
- A malformed or malicious job with a different type could be processed incorrectly
- `run()` should filter by job type before dispatching

**Impact:**
- Worker processes any job type with indexing logic, potentially corrupting data
- No job type safety

**Correction:**
```python
if job and job.get("type") == "index_document":
    try:
        await self._process_job(job)
```

---

### 4. High: Path Traversal Vulnerability in _sanitize_path

**Location:** `indexer.py:94-105`

**Evidence:**
```python
async def _sanitize_path(self, storage_path: str) -> Path:
    """Sanitize storage path to prevent path traversal attacks."""
    base_dir = Path(settings.storage_root) / "uploads"
    resolved = base_dir / Path(storage_path).name  # <-- VULNERABLE: Only uses .name
    
    # Ensure the resolved path is under base_dir
    try:
        resolved.resolve().relative_to(base_dir.resolve())
    except ValueError:
        raise PermissionError("Path traversal attempt detected")
    
    return resolved
```

**Problem:**
- `Path(storage_path).name` only extracts the filename, **discarding the rest of the path**
- Storage paths are stored like `"storage/uploads/123/somefile.pdf"` but only `"somefile.pdf"` is used
- The original user-specific subdirectory (`123/`) is **stripped**, causing all documents to be read from the wrong location
- The `relative_to` check passes because `resolved` becomes `base_dir / "somefile.pdf"` which is always under `base_dir`

**Example Attack:**
1. User uploads file → stored as `uploads/42/report.pdf`
2. `storage_path = "uploads/42/report.pdf"` is saved to database
3. `_sanitize_path("uploads/42/report.pdf")` → `Path("report.pdf").name` = `"report.pdf"`
4. Resolved = `base_dir / "report.pdf"` = `storage/uploads/report.pdf` (different file!)
5. Worker reads wrong file or raises FileNotFoundError

**Impact:**
- Workers read incorrect files or fail completely
- Document indexing is broken
- Security check gives false sense of safety while actually corrupting functionality

**Correction:**
```python
async def _sanitize_path(self, storage_path: str) -> Path:
    """Sanitize storage path to prevent path traversal attacks."""
    base_dir = Path(settings.storage_root) / "uploads"
    
    # Normalize the path and resolve it
    resolved = (base_dir / storage_path).resolve()
    
    # Ensure the resolved path is under base_dir
    try:
        resolved.relative_to(base_dir.resolve())
    except ValueError:
        raise PermissionError("Path traversal attempt detected")
    
    return resolved
```

---

### 5. Medium: Missing is_deleted Column Handling

**Location:** `document.py:110-114`

**Evidence:**
```python
async def count_for_user(self, user_id: int) -> int:
    """Return total non-deleted document count for a user."""
    row = await self._db.fetchone(
        "SELECT COUNT(*) as cnt FROM documents WHERE user_id = ? AND is_deleted = FALSE",
        (user_id,),
    )
    return int(row["cnt"]) if row else 0
```

**Problem:**
- Query references `is_deleted` column that may not exist in the database schema
- The schema in `documents.py` shows: `id, user_id, filename, content_type, storage_path, indexed_at, created_at, status, content_hash, error_message`
- No `is_deleted` column is added by the migration shown in the task description

**Impact:**
- Database query fails with `no such column: documents.is_deleted` if migration not applied
- Soft-delete functionality not implemented

**Correction:**
Either add `is_deleted` column to schema:
```sql
ALTER TABLE documents ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;
```

Or update the query to not filter by deleted status if not implemented.

---

### 6. Medium: Inconsistent Database Commit Patterns

**Location:** `indexer.py:223-240`, `document.py`

**Evidence:**
```python
async def _update_status(self, doc_id: int, status: str, ...) -> None:
    if db is None:
        db = await self._get_db()
    await db.execute(...)
    await db.commit()  # <-- Commits inside method
```

**Problem:**
- `_update_status()` commits immediately, breaking transactional consistency
- `_process_job()` calls `_update_status()` multiple times in sequence
- If a later operation fails, previous updates are already committed (not atomic)

**Example Race Condition:**
1. Update status to `processing` (committed)
2. Validate ownership (passes)
3. Extract content (fails)
4. Update status to `failed` (committed)
5. But the document is left in `processing` state if step 4 fails before commit

**Impact:**
- Document states can become inconsistent
- No rollback capability on partial failures
- Retry logic may reprocess documents stuck in `processing` state

**Correction:**
Remove `await db.commit()` from `_update_status()` and let `_process_job()` control transaction boundaries.

---

### 7. Medium: No Exponential Backoff Guard in process_single_job

**Location:** `indexer.py:286-287`

**Evidence:**
```python
delay = await self._calculate_delay(retry_count)
next_retry_time": time.time() + delay,
```

**Problem:**
- `retry_count` is passed from job payload but not validated
- If `retry_count` is negative or extremely large (e.g., from malicious job), delay calculation can overflow or produce unexpected values

**Impact:**
- Malicious or malformed jobs could cause denial of service via resource exhaustion

**Correction:**
Validate retry_count before use:
```python
retry_count = max(0, job.get("retry_count", 0))
```

---

### 8. Low: Incomplete Error Recovery in _extract_content

**Location:** `indexer.py:177-185`

**Evidence:**
```python
async def _extract_content(self, file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document file not found: {file_path}")
    ext = path.suffix.lower()
    if ext == ".pdf":
        return await asyncio.to_thread(self._extract_pdf, path)
    elif ext == ".docx":
        return await asyncio.to_thread(self._extract_docx, path)
    else:
        return await asyncio.to_thread(self._extract_text, path)
```

**Problem:**
- `_extract_text` catches `UnicodeDecodeError` and tries `latin-1` encoding
- If both fail, the exception propagates but the caller's error handling may not account for it

**Impact:**
- Some text files may fail to index with unclear error messages

**Correction:**
Add explicit exception handling:
```python
def _extract_text(self, path: Path) -> str:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode file with any known encoding: {path}")
```

---

### 9. Operational: In-Memory Queue Lacks Persistence

**Location:** `queue.py:1-41`

**Evidence:**
```python
class JobQueue:
    def __init__(self) -> None:
        self._queue: deque[dict] = deque()
        self._redis = None
        self._paused = False
```

**Problem:**
- In-memory queue (`deque`) is not durable
- Worker restart loses all pending jobs
- No visibility into queue depth or job age

**Impact:**
- Job loss on worker crash or restart
- No operational visibility into queue backlog

**Note:** This is documented in the task as a known limitation (🟡 Queue Backend). Not a blocker if user accepts trade-off, but must be addressed for production.

---

## Unchanged Code Review

### Documents Route (documents.py:1-335)

The upload endpoint correctly:
- Validates file extension and MIME type
- Streams file content in chunks with size limit
- Validates file signatures (PDF/DOCX magic bytes)
- Stores files with sanitized names and user-specific directories
- Creates database record AFTER successful file write
- Enqueues indexing job with `document_id` and `user_id`

The delete endpoint correctly:
- Validates ownership before deletion
- Removes file from storage and database record

### Document Repository (document.py:1-134)

The repository correctly:
- Implements ownership validation (`get_by_id` includes `user_id` filter)
- Updates status with content hash for deduplication
- Provides `find_by_hash` for duplicate detection
- Missing `is_deleted` handling (see Finding #5)

---

## Required Verification Steps

1. **Fix database connection initialization** - `connect()` must assign `self._db`
2. **Fix unreachable code** in `count_all()` and `count_for_user()`
3. **Add job type validation** before processing
4. **Fix path traversal logic** to use full path, not just filename
5. **Add `is_deleted` column** to schema or remove reference from query
6. **Remove automatic commits** from `_update_status()` to enable transaction control
7. **Validate retry_count** before exponential backoff calculation

---

## Conclusion

**No blocker is speculative.** All findings are reachable with standard workloads:

- **Blocker #1** (connection leak) occurs on every worker invocation
- **Blocker #2** (unreachable code) causes `count_all()` to return `None`
- **Blocker #3** (no job type check) allows arbitrary jobs to be processed
- **Blocker #4** (path traversal bypass) causes file processing to fail or read wrong files

All blockers must be fixed before the indexer can be deployed safely.