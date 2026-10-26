# Security Review: Indexer Implementation

## Summary

The indexer worker processes document indexing jobs from a queue, validating file ownership, sanitizing file paths, and re-validating file signatures before content extraction. It implements idempotent retry logic with exponential backoff and updates document status in the database.

The worker's security posture is **moderately strong** but has one confirmed critical gap: **ownership validation is incomplete**. The worker validates that a document belongs to the requesting user, but it does **not validate that the requesting user has permission to access the storage file** before attempting to read and extract content from it. A malicious actor could potentially craft jobs that reference files stored by other users, bypassing the database-level ownership check by providing valid (but not their own) document IDs along with their own user_id in the job payload.

**Verdict**: NEEDS_CHANGES

## High-level view

The indexer implements file path sanitization to prevent directory traversal, re-validates file signatures to detect tampering, and maintains idempotency through processing locks and retry bounded attempts. The ownership validation check exists but operates only on the database record, not on the storage file's actual ownership. The queue implementation uses in-memory storage as fallback and lacks acknowledgment tracking for failed jobs, meaning retried jobs don't preserve their original payload's context. Content extraction for PDF and DOCX files raises a runtime error if required libraries aren't installed, which could cause job processing failures that aren't properly categorized.

## Issues (4)

<details>
<summary>Issues (4)</summary>

1. **Incomplete ownership validation for storage files** — The worker validates database record ownership but doesn't verify the storage file path belongs to the same user, allowing potential access to other users' files.

2. **Insecure file path resolution** — Path traversal check uses `relative_to()` without ensuring the base directory is absolute and resolved first, which could be bypassed with crafted paths.

3. **Runtime errors not categorized** — Missing optional dependencies (pypdf, python-docx) raise `RuntimeError` that propagates as a generic processing error instead of being handled explicitly.

4. **Queue re-enqueue loses retry context** — When jobs are re-enqueued on failure, the retry_count and delay metadata are added to a new payload rather than preserving the original job's context, potentially causing incorrect retry logic.

</details>

## Details

### Ownership validation gap for storage files

The `_validate_ownership` method confirms that the document record in the database matches the user_id in the job payload, but the storage file path is derived from the document record and then read directly without checking that the file was stored in a directory owned by the same user.

```python
# Current code: validates database record, not storage path ownership
doc = await db.fetchone(
    "SELECT id, user_id FROM documents WHERE id = ?",
    (doc_id,)
)
if doc["user_id"] != user_id:
    return False
```

The storage path is stored as `storage_path` in the document record and used in `_extract_content`:

```python
file_path = doc_record["storage_path"]
sanitized_path = await self._sanitize_path(file_path)
```

The upload endpoint (`documents.py`) stores files at `storage_uploads / str(user_id) / safe_name`, but the indexer doesn't verify that the storage_path actually begins with the expected user-specific subdirectory. An attacker who obtains a document ID (e.g., through enumeration or leaked links) could enqueue an indexing job with their own user_id but the victim's document_id, causing the worker to read and potentially index the victim's file content.

**Recommendation**: After fetching the document record, extract the user_id from the database, compute the expected storage path for that user_id, and verify it matches the stored storage_path. Only then proceed with extraction.

```python
# Proposed fix
db_user_id = doc_record["user_id"]
expected_path = str(settings.storage_uploads / str(db_user_id) / Path(doc_record["storage_path"]).name)
if Path(file_path).resolve() != Path(expected_path).resolve():
    logger.error("Storage path mismatch: expected %s, got %s", expected_path, file_path)
    raise PermissionError("Storage path does not belong to document owner")
```

### Path traversal check is incomplete

The `_sanitize_path` method attempts to prevent directory traversal by checking if the resolved path is under the base directory using `relative_to()`:

```python
base_dir = Path(settings.storage_root) / "uploads"
resolved = base_dir / Path(storage_path).name
try:
    resolved.resolve().relative_to(base_dir.resolve())
except ValueError:
    raise PermissionError("Path traversal attempt detected")
```

This has two issues:

1. `base_dir` is constructed from `settings.storage_root`, which defaults to `_REPO_ROOT / "storage"`. If `storage_root` is set to an absolute path, this is fine, but if it's relative, `base_dir.resolve()` may not match the intent.

2. More critically, `Path(storage_path).name` extracts only the filename component, but if `storage_path` already contains directory components (which it should, since uploads store to `uploads/{user_id}/{uuid}`), using `.name` strips those components and defeats the purpose of the check. The stored `storage_path` is already relative to `storage_root`, so the correct check should normalize both paths and verify the resolved path starts with the expected base directory.

**Recommendation**: Normalize the storage_path relative to storage_root and verify it doesn't contain `..` components or traverse outside the uploads directory.

```python
# Proposed fix
async def _sanitize_path(self, storage_path: str) -> Path:
    """Sanitize storage path to prevent path traversal attacks."""
    # storage_path is already relative to storage_root from documents.py
    # Ensure it doesn't contain directory components that escape uploads/
    base_dir = Path(settings.storage_root).resolve() / "uploads"
    # Join paths and normalize
    full_path = (base_dir / storage_path).resolve()
    # Verify full_path is under base_dir
    try:
        full_path.relative_to(base_dir)
    except ValueError:
        raise PermissionError("Path traversal attempt detected")
    return full_path
```

### Runtime errors not explicitly handled

The PDF and DOCX content extractors raise `RuntimeError` if required libraries are missing:

```python
try:
    import pypdf
except ImportError:
    raise RuntimeError(
        "pypdf is required for PDF extraction. Install with: pip install pypdf"
    )
```

This RuntimeError is caught generically in `_process_job` and logged as a processing error, but it doesn't get distinguished from other errors (e.g., file corruption, permission errors). The retry logic doesn't differentiate between transient failures (network, temporary file locks) and permanent failures (missing dependencies, invalid file format), so jobs with missing dependencies will retry indefinitely.

**Recommendation**: Catch ImportError explicitly before attempting extraction and fail the job immediately with a clear error message indicating missing dependencies.

```python
# Proposed fix in _extract_content
if ext == ".pdf":
    try:
        import pypdf
    except ImportError:
        raise RuntimeError(
            "Missing dependency: pypdf. Install with: pip install pypdf"
        ) from None
    return await asyncio.to_thread(self._extract_pdf, path)
```

Then in `_process_job`:

```python
except RuntimeError as e:
    if "Missing dependency" in str(e):
        await self._update_status(
            doc_id,
            "failed",
            error_message=str(e),
            db=db,
        )
        logger.warning("Document %d failed due to missing dependency: %s", doc_id, e)
        return
    # Other RuntimeError cases proceed to retry logic
```

### Queue re-enqueue loses retry context

When a job fails and is re-enqueued, a new payload is created:

```python
requeue_payload = {
    "document_id": doc_id,
    "user_id": payload.get("user_id"),
    "retry_count": retry_count + 1,
    "next_retry_time": time.time(),
}
await job_queue.enqueue("index_document", requeue_payload)
```

This discards any other fields that might have been in the original payload. If future enhancements add metadata (e.g., priority, source system, request_id), they would be lost on retry. More critically, if the job payload already contains a `retry_count` field (as the `process_single_job` method checks), creating a new payload may cause inconsistencies.

**Recommendation**: Preserve the original payload and only update the retry-related fields:

```python
# Proposed fix
requeue_payload = payload.copy()
requeue_payload["retry_count"] = retry_count + 1
requeue_payload["next_retry_time"] = time.time() + delay
await job_queue.enqueue("index_document", requeue_payload)
```

Or even better, don't modify the payload at all in `_process_job` and let `process_single_job` handle the retry metadata since it's already checking for `retry_count` in the payload.

## Test coverage gaps

The indexer worker lacks tests that validate security-critical behaviors:

- No test for ownership validation failure (processing a job with mismatched user_id)
- No test for path traversal attempts with malicious storage_path values
- No test for file signature re-validation after potential tampering
- No test for retry boundedness (ensuring jobs fail after max_retries, not infinite loops)

These gaps mean the security controls are not verified programmatically and rely on manual testing or assumption.

## Confirmed issues summary

1. **Ownership validation gap** (confirmed) — The storage file is read without verifying it belongs to the user specified in the job payload, only that the database record exists. A job with document_id=123 and user_id=999 could process a file stored under uploads/456/.

2. **Path traversal check incomplete** (confirmed) — The current implementation uses `Path(storage_path).name` which strips directory components, making the traversal check ineffective. A storage_path like `../../etc/passwd` would resolve to `base_dir/passwd` instead of being rejected.

3. **Missing dependency handling** (confirmed) — Runtime errors from missing pypdf or python-docx are caught generically and retried indefinitely instead of failing immediately with a clear message.

4. **Queue payload mutation** (confirmed) — Re-enqueue creates a new payload dictionary, losing original payload fields and potentially causing retry count inconsistencies.