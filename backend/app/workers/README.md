# Document Indexing Worker

The indexer worker processes document indexing jobs from the queue. It extracts content from uploaded files, computes content hashes for deduplication, and updates document status in the database.

## Features

- **Async job processing**: Consumes `index_document` jobs from the queue
- **State transitions**: Handles pending → processing → indexed/failed transitions
- **Idempotent retries**: Bounded retry logic with exponential backoff (max 3 retries)
- **Concurrency protection**: Uses database locks to prevent duplicate processing
- **Ownership validation**: Verifies document belongs to requesting user
- **Content extraction**: Supports PDF, DOCX, TXT, MD, CSV, JSON, HTML
- **Content hashing**: SHA-256 hash for deduplication

## Usage

### Start the worker

```bash
python -m app.workers.indexer_entrypoint
```

### Run tests

```bash
pytest tests/test_indexer.py -v
```

## File Format Support

| Format | Library | Extension |
|--------|---------|-----------|
| PDF | pypdf | .pdf |
| DOCX | python-docx | .docx |
| Text | Built-in | .txt, .md, .csv, .json, .html |

## Configuration

The worker uses settings from `app/config.py`:

- `indexing_retry_base_delay`: Base delay for retries (default: 5.0)
- `indexing_retry_backoff_multiplier`: Exponential backoff multiplier (default: 3.0)
- `indexing_max_retries`: Maximum retry attempts (config value, actual: 3)

## Job Payload

Jobs enqueued with type `index_document` should include:

```python
{
    "type": "index_document",
    "payload": {
        "document_id": 123,
        "user_id": 456
    }
}
```

## State Transitions

1. **pending**: Initial state after upload
2. **processing**: Worker acquires lock and begins extraction
3. **indexed**: Content extracted and hash computed successfully
4. **failed**: Extraction failed or ownership validation failed

## Error Handling

Errors are logged and stored in the `error_message` column of the documents table:

| Error | Status | Error Message |
|-------|--------|---------------|
| File not found | failed | "Document file not found: {path}" |
| Ownership validation fails | failed | "Ownership validation failed" |
| Extraction error | failed | "Failed to extract content: {error}" |
| Max retries exceeded | failed | "Max retries (3) exceeded: {last_error}" |
| Database error | failed | "Database error: {error}" |

## Concurrency

The worker uses database-level optimistic locking via conditional UPDATE statements to prevent duplicate processing:

```sql
UPDATE documents 
SET status = 'processing' 
WHERE id = ? AND status = 'pending'
```

Only one worker can successfully transition a document to processing at a time.
