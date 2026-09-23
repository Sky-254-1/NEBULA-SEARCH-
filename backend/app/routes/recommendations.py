"""Recommendation endpoints for related content and personalized suggestions."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.database.repositories.document import DocumentRepository
from app.database.repositories.search import SearchRepository
from app.database.repositories.user import UserRepository
from app.database.repositories.saved_search import SavedSearchRepository
from app.services.auth import get_current_user

logger = logging.getLogger("nebula.recommendations")

router = APIRouter(prefix="/api/v1/recommendations", tags=["Recommendations"])


async def _user_id(db, email: str) -> int:
    users = UserRepository(db)
    user = await users.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user["id"]


@router.get("/related")
async def get_related_content(
    document_id: int = Query(..., description="Document ID to find related content for"),
    limit: int = Query(10, ge=1, le=50),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get content related to a specific document based on filename similarity and recency."""
    user_id = await _user_id(db, email)
    docs = DocumentRepository(db)
    document = await docs.get_by_id(document_id, user_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_name = (document.get("filename") or "").lower()
    doc_words = set(doc_name.replace("_", " ").replace("-", " ").split())

    rows = await docs.list_for_user(user_id, limit=100)
    related = []
    for row in rows:
        if row["id"] == document_id:
            continue
        other_name = (row.get("filename") or "").lower()
        other_words = set(other_name.replace("_", " ").replace("-", " ").split())
        overlap = len(doc_words & other_words)
        if overlap > 0:
            related.append({
                "document_id": row["id"],
                "filename": row["filename"],
                "content_type": row.get("content_type"),
                "relevance_score": round(overlap / max(len(doc_words | other_words), 1), 4),
                "reason": f"Shares {overlap} term(s) in filename",
            })

    related.sort(key=lambda x: x["relevance_score"], reverse=True)
    related = related[:limit]

    return {"recommendations": related, "total": len(related)}


@router.get("/personalized")
async def get_personalized_recommendations(
    limit: int = Query(10, ge=1, le=50),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get personalized recommendations based on user behavior (search history, interests)."""
    user_id = await _user_id(db, email)
    search_repo = SearchRepository(db)
    recent = await search_repo.recent_for_user(user_id, limit=50)

    if not recent:
        # Fall back: recommend first few user documents
        docs = DocumentRepository(db)
        rows = await docs.list_for_user(user_id, limit=limit)
        recommendations = [
            {
                "document_id": r["id"],
                "filename": r["filename"],
                "content_type": r.get("content_type"),
                "score": 0.5,
                "reason": "Recently indexed",
            }
            for r in rows
        ]
        return {"recommendations": recommendations, "total": len(recommendations)}

    # Build interest profile from search history
    word_counts: dict = {}
    for item in recent:
        for word in item.get("query", "").lower().split():
            if len(word) > 3:
                word_counts[word] = word_counts.get(word, 0) + 1

    top_interests = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    interests = [w for w, _ in top_interests]

    # Recommend saved searches first
    saved_repo = SavedSearchRepository(db)
    saved = await saved_repo.list_for_user(user_id, limit=limit // 2)

    recommendations = [
        {
            "document_id": None,
            "query": s["query"],
            "content_type": "saved_search",
            "score": 0.9,
            "reason": "Your saved search",
        }
        for s in saved
    ]

    # Then recommend document similarity based on interests
    if interests:
        docs = DocumentRepository(db)
        rows = await docs.list_for_user(user_id, limit=limit - len(recommendations))
        for row in rows:
            doc_text = f"{row.get('filename', '')} {row.get('content_type', '')}".lower()
            score = sum(1 for interest in interests if interest in doc_text)
            if score > 0:
                recommendations.append({
                    "document_id": row["id"],
                    "filename": row["filename"],
                    "content_type": row.get("content_type"),
                    "score": round(score / len(interests), 4),
                    "reason": f"Matches your interests: {', '.join(interests[:3])}",
                })

    recommendations.sort(key=lambda x: x.get("score", 0), reverse=True)
    recommendations = recommendations[:limit]

    return {"recommendations": recommendations, "total": len(recommendations)}


@router.get("/similar-searches")
async def get_similar_searches(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    email: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get similar searches based on query and search history."""
    user_id = await _user_id(db, email)

    # Find similar queries from user's history
    search_repo = SearchRepository(db)
    history = await search_repo.recent_for_user(user_id, limit=100)

    q_lower = q.lower()
    q_words = set(q_lower.split())

    similar = []
    for item in history:
        hist_query = item.get("query", "")
        hist_words = set(hist_query.lower().split())
        if not hist_words:
            continue
        overlap = len(q_words & hist_words)
        if overlap > 0:
            jaccard = overlap / len(q_words | hist_words)
            similar.append({
                "query": hist_query,
                "frequency": item.get("results_count", 0) + 1,
                "category": "history" if item.get("user_id") == user_id else "popular",
                "similarity": round(jaccard, 4),
            })

    similar.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    seen = set()
    unique = []
    for s in similar:
        if s["query"].lower() not in seen and s["query"].lower() != q_lower:
            seen.add(s["query"].lower())
            unique.append(s)

    return {"recommendations": unique[:limit], "total": len(unique[:limit])}
