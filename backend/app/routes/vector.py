"""Vector document indexing and retrieval routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.database.repositories.document import DocumentRepository
from app.database.repositories.export import ExportRepository
from app.database.repositories.user import UserRepository
from app.models.schemas import (
    DocumentIndexStatusResponse,
    PaginationMeta,
    VectorAskRequest,
    VectorAskResponse,
    VectorCitationListResponse,
    VectorCitationResponse,
    VectorReindexRequest,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)
from app.services.ai import synthesize_snippets
from app.services.auth import get_current_user
from app.services.queue import job_queue
from app.utils.pagination import PaginationParams
from vector.pipeline import (
    ChunkRepository,
    EmbeddingRepository,
    hybrid_search,
    index_document,
)

router = APIRouter(prefix="/api/v1/vector", tags=["Vector"])


async def _user_id(db, email: str) -> int:
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    return user_id


@router.get("/documents/{doc_id}/status", response_model=DocumentIndexStatusResponse)
async def document_index_status(
    doc_id: int,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = await _user_id(db, email)
    docs = DocumentRepository(db)
    row = await docs.get_by_id(doc_id, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentIndexStatusResponse(
        id=row["id"],
        filename=row["filename"],
        status=row.get("status") or "pending",
        indexed_at=str(row.get("indexed_at")) if row.get("indexed_at") else None,
        error_message=row.get("error_message"),
    )


@router.post("/documents/{doc_id}/reindex")
async def reindex_document(
    doc_id: int,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = await _user_id(db, email)
    docs = DocumentRepository(db)
    row = await docs.get_by_id(doc_id, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    await job_queue.enqueue("index_document", {"document_id": doc_id, "user_id": user_id})
    return {"message": "Reindex queued", "document_id": doc_id}


@router.post("/documents/reindex-all")
async def reindex_all(
    body: VectorReindexRequest,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = await _user_id(db, email)
    docs = DocumentRepository(db)
    rows = await docs.list_for_user(user_id, limit=body.limit or 100)
    for row in rows:
        await job_queue.enqueue(
            "index_document",
            {"document_id": row["id"], "user_id": user_id},
        )
    return {"message": "Reindex queued", "count": len(rows)}


@router.post("/ask", response_model=VectorAskResponse)
async def vector_ask(
    body: VectorAskRequest,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """RAG-style answer over indexed documents with citations and sources."""
    user_id = await _user_id(db, email)
    results = await hybrid_search(db, user_id, body.query, top_k=body.top_k)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="No indexed documents match this query. Upload and index documents first.",
        )

    snippets = [r.get("content", "") for r in results if r.get("content")]
    synth = await synthesize_snippets(body.query, snippets)
    answer = synth.synthesis or "No summary could be generated from your documents."

    from vector.citations import CitationRepository

    citations_repo = CitationRepository(db)
    citation_rows = await citations_repo.list_by_query(user_id, body.query, limit=body.top_k)
    sources = sorted({r.get("filename", "") for r in results if r.get("filename")})

    return VectorAskResponse(
        query=body.query,
        answer=answer,
        citations=[
            VectorCitationResponse(
                id=r["id"],
                document_id=r.get("document_id"),
                chunk_id=r.get("chunk_id"),
                query=r["query"],
                snippet=r.get("snippet"),
                score=r.get("score", 0),
                created_at=str(r.get("created_at", "")),
            )
            for r in citation_rows
        ],
        sources=sources,
    )


@router.post("/search", response_model=VectorSearchResponse)
async def vector_search(
    body: VectorSearchRequest,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = await _user_id(db, email)
    results = await hybrid_search(db, user_id, body.query, top_k=body.top_k)
    return VectorSearchResponse(
        query=body.query,
        results=[
            VectorSearchResult(
                document_id=r.get("document_id"),
                chunk_id=r.get("chunk_id"),
                filename=r.get("filename", ""),
                content=r.get("content", ""),
                score=r.get("score", 0),
                vector_score=r.get("vector_score", 0),
                keyword_score=r.get("keyword_score", 0),
            )
            for r in results
        ],
        total=len(results),
    )


@router.get("/citations", response_model=VectorCitationListResponse)
async def list_citations(
    pagination: PaginationParams = Depends(),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """List citations for the current user with pagination."""
    user_id = await _user_id(db, email)
    from vector.citations import CitationRepository

    repo = CitationRepository(db)
    
    # Get all citations (in production, add pagination to repository)
    rows = await repo.list_for_user(user_id)
    total = len(rows)
    
    # Apply pagination
    start_idx = pagination.offset
    end_idx = start_idx + pagination.limit
    paginated_rows = rows[start_idx:end_idx]
    
    # Create pagination metadata
    pagination_meta = PaginationMeta(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
        has_next=pagination.page < (total + pagination.page_size - 1) // pagination.page_size,
        has_previous=pagination.page > 1,
    )
    
    return VectorCitationListResponse(
        citations=[
            VectorCitationResponse(
                id=r["id"],
                document_id=r.get("document_id"),
                chunk_id=r.get("chunk_id"),
                query=r["query"],
                snippet=r.get("snippet"),
                score=r.get("score", 0),
                created_at=str(r.get("created_at", "")),
            )
            for r in paginated_rows
        ],
        pagination=pagination_meta,
    )


@router.post("/documents/{doc_id}/index-now")
async def index_now(
    doc_id: int,
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Synchronous indexing for small documents (bypasses queue)."""
    user_id = await _user_id(db, email)
    ok = await index_document(db, doc_id, user_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Indexing failed")
    return {"message": "Indexed", "document_id": doc_id}


@router.get("/stats")
async def vector_stats(email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _user_id(db, email)
    chunks = ChunkRepository(db)
    EmbeddingRepository(db)
    chunk_rows = await chunks.list_for_user(user_id)
    return {
        "chunks": len(chunk_rows),
        "documents_indexed": len({c["document_id"] for c in chunk_rows}),
    }


@router.post("/export")
async def export_vectors(email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _user_id(db, email)
    from app.config import get_settings
    import json
    import uuid

    settings = get_settings()
    chunks = ChunkRepository(db)
    rows = await chunks.list_for_user(user_id)
    export_dir = settings.storage_exports / str(user_id)
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"vectors_{uuid.uuid4().hex}.json"
    dest = export_dir / filename
    dest.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    exports = ExportRepository(db)
    export_id = await exports.create(user_id, "vectors", str(dest))
    return {"export_id": export_id, "path": str(dest), "chunk_count": len(rows)}
