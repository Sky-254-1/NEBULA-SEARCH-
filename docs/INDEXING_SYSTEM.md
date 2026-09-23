# Background Document Indexing System

## Overview

Production-grade background document indexing system for Nebula Search Engine, similar to systems used by Google Search, Elasticsearch, Meilisearch, and OpenSearch.

## Architecture

### Core Components

1. **Priority Queue** (`indexing/queue.py`)
   - Redis-backed priority queue with in-memory fallback
   - Supports priorities: SYSTEM > HIGH > NORMAL > LOW
   - Queue persistence across restarts
   - Pause/resume capability

2. **Worker Pool** (`indexing/worker.py`)
   - Multiple concurrent workers
   - Worker health monitoring
   - Automatic retry with exponential backoff
   - Graceful shutdown

3. **Progress Tracking** (`indexing/progress.py`)
   - Real-time progress updates
   - ETA calculation
   - Speed metrics
   - Step-by-step tracking

4. **Retry Logic** (`indexing/retry.py`)
   - Exponential backoff: 5s → 15s → 45s → 120s → 300s
   - Jitter to prevent thundering herd
   - Non-retryable error detection
   - Configurable max retries

5. **Dead Letter Queue** (`indexing/deadletter.py`)
   - Failed job quarantine
   - Manual retry capability
   - Failure reason logging
   - Stack trace preservation

6. **Metrics Collection** (`indexing/metrics.py`)
   - Indexed documents count
   - Average indexing time
   - Worker utilization
   - Failure/retry metrics
   - Storage throughput

7. **Health Monitoring** (`indexing/health.py`)
   - Worker heartbeat tracking
   - Dead worker detection
   - Automatic restart capability

8. **Scheduler** (`indexing/scheduler.py`)
   - Cron-based scheduling
   - Interval-based tasks
   - Manual triggers
   - Nightly reindex support

## API Endpoints

### POST /api/v1/indexing/start
Start indexing a document.

**Request:**
```json
{
  "document_id": 123,
  "priority": "NORMAL"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "job_id": "uuid-here"
  }
}
```

### POST /api/v1/indexing/reindex
Reindex documents.

**Request:**
```json
{
  "document_ids": [123, 456],
  "priority": "HIGH",
  "incremental": true
}
```

### POST /api/v1/indexing/cancel/{job_id}
Cancel a queued or running job.

### POST /api/v1/indexing/retry/{job_id}
Retry a failed job from dead-letter queue.

### GET /api/v1/indexing/jobs
Get all queued jobs.

### GET /api/v1/indexing/job/{job_id}
Get specific job details.

### GET /api/v1/indexing/progress/{job_id}
Get job progress with ETA and speed.

### GET /api/v1/indexing/workers
Get worker health status.

### GET /api/v1/indexing/metrics
Get indexing metrics.

### GET /api/v1/indexing/deadletter
Get dead-letter queue contents.

### DELETE /api/v1/indexing/deadletter/{job_id}
Remove job from dead-letter queue.

### GET /api/v1/indexing/scheduler
Get scheduler status.

## Configuration

Environment variables:

- `INDEXING_MAX_QUEUE_SIZE` (default: 10000)
- `INDEXING_WORKER_COUNT` (default: 2)
- `INDEXING_MAX_RETRIES` (default: 5)
- `INDEXING_RETRY_BASE_DELAY` (default: 5.0)
- `INDEXING_RETRY_BACKOFF_MULTIPLIER` (default: 3.0)
- `INDEXING_CHUNK_SIZE` (default: 1000)
- `INDEXING_CHUNK_OVERLAP` (default: 200)

## Database Schema

See `backend/app/database/migrations/004_sqlite_indexing.sql` for:
- `index_jobs` - Job tracking
- `dead_letter_queue` - Failed jobs
- `worker_health` - Worker monitoring
- `indexing_metrics` - Performance metrics
- `scheduler_configs` - Scheduled tasks
- `document_chunks` - Incremental indexing

## Indexing Flow

1. Document Upload → Create Job
2. Queue Job with Priority
3. Worker Picks Job
4. Extract Text
5. Chunk Document
6. Generate Embeddings
7. Build Metadata
8. Store Vectors
9. Update Search Index
10. Mark Complete

## Job States

- `QUEUED` - Waiting for worker
- `WAITING` - In queue
- `RUNNING` - Processing
- `PAUSED` - Temporarily paused
- `RETRYING` - Retry in progress
- `COMPLETED` - Success
- `FAILED` - Failed permanently
- `CANCELLED` - User cancelled

## Performance Goals

- Multiple documents indexed concurrently
- Large files processed without blocking API
- Background indexing never blocks searches
- Support thousands of queued jobs
- Resume safely after restart
- Prevent duplicate indexing
- Efficient memory usage

## Testing

Run indexing tests:
```bash
cd backend
python -m pytest tests/test_indexing.py -v
```

## Integration

The indexing system integrates with:
- Document upload endpoints
- Existing database (documents table)
- Configuration system
- Health monitoring
- Main FastAPI application

## Next Steps

1. Connect to actual embedding service
2. Implement vector storage backend
3. Add file type parsers (PDF, DOCX, etc.)
4. Implement incremental indexing logic
5. Add reindex scheduling