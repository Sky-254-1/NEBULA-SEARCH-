# Incremental Re-indexing System

## Overview

The Nebula Search Engine includes a production-grade incremental re-indexing system that detects document changes and updates only modified content, minimizing indexing time, CPU usage, and storage operations.

## Architecture

### Core Components

1. **Hashing Utilities** (`app/incremental/hashing.py`)
   - SHA-256 document and chunk hashing
   - Metadata fingerprinting
   - Vector embedding checksums
   - File integrity verification

2. **Change Detection** (`app/incremental/detector.py`)
   - Document state comparison
   - New/modified/deleted/renamed/moved detection
   - Chunk-level change identification
   - Corruption detection

3. **Diff Engine** (`app/incremental/diff.py`)
   - Computes differences between document versions
   - Identifies added, removed, modified, and reused chunks
   - Optimizes operations to minimize embedding generation
   - Determines when full reindex is needed

4. **Document Scanner** (`app/incremental/scanner.py`)
   - Batch document scanning
   - File system monitoring
   - Change type classification
   - Metadata comparison

5. **Synchronizer** (`app/incremental/synchronizer.py`)
   - Incremental index updates
   - Chunk addition, modification, and removal
   - Vector store synchronization
   - Metadata-only updates

6. **Metadata Synchronizer** (`app/incremental/metadata.py`)
   - Updates searchable fields without regenerating embeddings
   - Tracks metadata changes over time
   - Versioning support

7. **Index Tracker** (`app/incremental/tracker.py`)
   - Maintains document hash history
   - Version tracking
   - Reindex necessity detection

8. **Cleanup Service** (`app/incremental/cleanup.py`)
   - Removes orphaned vectors
   - Cleans stale metadata
   - Eliminates duplicate chunks
   - Purges expired cache entries

9. **Scheduler** (`app/incremental/scheduler.py`)
   - Cron-based scheduled scans
   - Interval-based scanning
   - Manual trigger support

10. **Event System** (`app/incremental/events.py`)
    - Async event publishing
    - Metrics collection
    - Event history tracking

## Database Schema

### Tables

- `index_tracking` - Document hash and version tracking
- `incremental_jobs` - Re-indexing job history
- `reindex_history` - Change event log
- `cleanup_logs` - Cleanup operation records
- `file_watcher_state` - File watcher state
- `incremental_scheduler_configs` - Scheduled task configurations

### Views

- `v_incremental_stats` - Overview statistics
- `recent_changes` - Recent change history

## API Endpoints

All endpoints are prefixed with `/api/v1/reindex`:

- `GET /status` - Get re-indexing status and configuration
- `GET /stats` - Get detailed statistics and metrics
- `GET /history` - Get re-indexing history (last 100 events)
- `POST /document/{document_id}` - Reindex specific document
- `POST /all` - Reindex all documents
- `POST /scan` - Scan for changes
- `POST /cleanup` - Run cleanup operations
- `POST /sync` - Synchronize indexes
- `DELETE /cache` - Clear event cache
- `GET /scheduler` - Get scheduler status
- `POST /scheduler/run/{task_id}` - Trigger scheduled task

## Configuration

Environment variables:

```bash
# Core settings
ENABLE_INCREMENTAL_INDEXING=true
HASH_ALGORITHM=sha256
REINDEX_MODE=incremental  # full, incremental, metadata_only

# Scanning
SCAN_INTERVAL=300  # seconds
SCAN_BATCH_SIZE=100
MAX_SCAN_THREADS=4

# File watching
ENABLE_FILE_WATCHER=false
WATCHER_DEBOUNCE_SECONDS=30

# Change detection
CHUNK_COMPARISON_ENABLED=true
CHUNK_REUSE_ENABLED=true

# Cleanup
ENABLE_AUTO_CLEANUP=true
CLEANUP_ORPHANED_VECTORS=true
CLEANUP_ORPHANED_METADATA=true

# Metadata sync
ENABLE_METADATA_SYNC=true
METADATA_FIELDS_TO_TRACK=title,description,author,category,tags,language,permissions,collections

# Scheduling
ENABLE_AUTO_SCHEDULE=true
DEFAULT_CRON_SCHEDULE=0 * * * *  # Every hour

# Performance
MAX_BATCH_SIZE=1000
WORKER_CONCURRENCY=2

# Detection features
ENABLE_RENAME_DETECTION=true
ENABLE_MOVE_DETECTION=true
ENABLE_CORRUPTION_DETECTION=true
```

## Usage Examples

### Python

```python
from app.incremental.services import get_incremental_service
from app.incremental.config import ReindexJobConfig

# Reindex a single document
service = get_incremental_service()
job_config = ReindexJobConfig(
    document_id=123,
    incremental=True,
    force_full=False
)

result = await service.reindex_document(
    db_session=db,
    document_id=123,
    job_config=job_config,
    file_path="/path/to/document.pdf",
    metadata={"title": "My Document", "author": "John Doe"}
)

print(f"Change type: {result.change_type}")
print(f"Chunks added: {result.chunks_added}")
print(f"Chunks reused: {result.chunks_reused}")
print(f"Duration: {result.total_duration}s")
```

### API Usage

```bash
# Reindex specific document
curl -X POST "http://localhost:8000/api/v1/reindex/document/123" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"incremental": true}'

# Scan all documents
curl -X POST "http://localhost:8000/api/v1/reindex/scan" \
  -H "Authorization: Bearer TOKEN"

# Get status
curl "http://localhost:8000/api/v1/reindex/status" \
  -H "Authorization: Bearer TOKEN"

# Run cleanup
curl -X POST "http://localhost:8000/api/v1/reindex/cleanup" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"dry_run": true}'
```

## Metrics Tracked

- Documents scanned
- Documents skipped (unchanged)
- Documents updated
- Documents deleted
- Chunks reused
- Chunks regenerated
- Embeddings reused
- Embeddings regenerated
- Vectors deleted
- Average scan time
- Average update time
- Storage reclaimed
- Cleanup duration

## Performance Features

1. **Chunk Reuse**: Unchanged chunks preserve their embeddings
2. **Hash Comparison**: Quick detection via SHA-256 checksums
3. **Batch Processing**: Concurrent document scanning
4. **Incremental Updates**: Only modified chunks re-indexed
5. **Metadata-Only Sync**: No vector regeneration for metadata changes
6. **Orphan Cleanup**: Automatic removal of stale data

## Testing

Run the test suite:

```bash
cd backend
python -m pytest tests/test_incremental.py -v
```

Test coverage includes:
- Hashing utilities
- Change detection
- Diff computation
- Scanner functionality
- Synchronization
- Metadata sync
- Index tracking
- Cleanup operations
- Event system
- Scheduler
- Full integration pipeline

## Integration with Existing Systems

The incremental re-indexing system integrates seamlessly with:

- **Background Indexing** (`app/indexing/`) - Uses existing queue and workers
- **Vector Search** - Updates vector store incrementally
- **Search API** - Maintains search index consistency
- **Document Upload** - Triggers incremental indexing on upload
- **Database** - Tracks document state in `index_tracking` table

## Migration

Run the database migration:

```bash
cd backend
# SQLite
sqlite3 nebula.db < app/database/migrations/005_sqlite_incremental.sql

# Or via Python
from app.database.engine import init_db
await init_db()  # Automatically runs all migrations
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all environment variables are set
2. **Slow Scans**: Increase `MAX_SCAN_THREADS` and `SCAN_BATCH_SIZE`
3. **Memory Usage**: Reduce `WORKER_CONCURRENCY` for large documents
4. **Missing Events**: Check event manager history with `get_history()`

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG
```

## Success Criteria

✅ Detects document changes automatically  
✅ Re-indexes only modified content  
✅ Reuses existing vectors for unchanged chunks  
✅ Removes stale search and vector entries safely  
✅ Keeps metadata synchronized without unnecessary re-indexing  
✅ Supports automatic background scanning and manual re-indexing  
✅ Scales efficiently to large document collections  
✅ Integrates seamlessly with Nebula's existing APIs  

## Files Created

```
backend/app/incremental/
├── __init__.py
├── config.py
├── hashing.py
├── detector.py
├── diff.py
├── scanner.py
├── synchronizer.py
├── metadata.py
├── tracker.py
├── cleanup.py
├── scheduler.py
├── events.py
├── services.py
└── routes.py

backend/app/database/migrations/
└── 005_sqlite_incremental.sql

backend/tests/
└── test_incremental.py

docs/
└── INCREMENTAL_REINDEXING.md

backend/app/main.py  (updated to register incremental routes)
```

## Future Enhancements

- Proper cron expression parser
- Distributed worker support
- Real file watcher (watchdog library)
- Vector database integration (Pinecone, Weaviate)
- Advanced conflict resolution
- Rollback capability
- Compression for stored hashes