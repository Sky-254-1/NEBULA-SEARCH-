"""Feature routes: saved searches, collections, bookmarks, notifications."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.database.repositories.bookmark import BookmarkRepository
from app.database.repositories.collection import CollectionRepository
from app.database.repositories.notification import NotificationRepository
from app.database.repositories.saved_search import SavedSearchRepository
from app.database.repositories.user import UserRepository
from app.models.schemas import (
    BookmarkCreate,
    BookmarkListResponse,
    BookmarkResponse,
    BookmarkUpdate,
    CollectionCreate,
    CollectionItemCreate,
    CollectionItemResponse,
    CollectionListResponse,
    CollectionResponse,
    CollectionUpdate,
    NotificationListResponse,
    NotificationResponse,
    SavedSearchCreate,
    SavedSearchListResponse,
    SavedSearchResponse,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Features"])


async def _get_user_id(email: str, db) -> int:
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    return user_id


# ---------------------------------------------------------------------------
# Saved Searches
# ---------------------------------------------------------------------------


@router.get("/saved-searches", response_model=SavedSearchListResponse)
async def list_saved_searches(email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = SavedSearchRepository(db)
    rows = await repo.list_for_user(user_id)
    return SavedSearchListResponse(saved_searches=[SavedSearchResponse(**r) for r in rows])


@router.post("/saved-searches", response_model=SavedSearchResponse, status_code=201)
async def create_saved_search(body: SavedSearchCreate, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = SavedSearchRepository(db)
    search_id = await repo.create(user_id, body.query, body.filters, body.label)
    row = await repo.get_by_id(search_id, user_id)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create saved search")
    return SavedSearchResponse(**row)


@router.delete("/saved-searches/{search_id}", status_code=204)
async def delete_saved_search(search_id: int, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = SavedSearchRepository(db)
    existing = await repo.get_by_id(search_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Saved search not found")
    await repo.delete(search_id, user_id)


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


@router.get("/collections", response_model=CollectionListResponse)
async def list_collections(email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = CollectionRepository(db)
    rows = await repo.list_for_user(user_id)
    return CollectionListResponse(collections=[CollectionResponse(**r) for r in rows])


@router.post("/collections", response_model=CollectionResponse, status_code=201)
async def create_collection(body: CollectionCreate, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = CollectionRepository(db)
    coll_id = await repo.create(user_id, body.name, body.description, body.is_public)
    row = await repo.get_by_id(coll_id, user_id)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create collection")
    return CollectionResponse(**row)


@router.get("/collections/{collection_id}", response_model=CollectionResponse)
async def get_collection(collection_id: int, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = CollectionRepository(db)
    row = await repo.get_by_id(collection_id, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Collection not found")
    return CollectionResponse(**row)


@router.put("/collections/{collection_id}", response_model=CollectionResponse)
async def update_collection(collection_id: int, body: CollectionUpdate, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = CollectionRepository(db)
    existing = await repo.get_by_id(collection_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")
    await repo.update(
        collection_id, user_id,
        name=body.name,
        description=body.description,
        is_public=body.is_public,
    )
    row = await repo.get_by_id(collection_id, user_id)
    return CollectionResponse(**row)


@router.delete("/collections/{collection_id}", status_code=204)
async def delete_collection(collection_id: int, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = CollectionRepository(db)
    existing = await repo.get_by_id(collection_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")
    await repo.delete(collection_id, user_id)


@router.post("/collections/{collection_id}/items", response_model=CollectionItemResponse, status_code=201)
async def add_collection_item(collection_id: int, body: CollectionItemCreate, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = CollectionRepository(db)
    existing = await repo.get_by_id(collection_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")
    item_id = await repo.add_item(collection_id, body.document_id, body.search_result_id, body.note)
    if not item_id:
        raise HTTPException(status_code=500, detail="Failed to add item")
    items = await repo.list_items(collection_id)
    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=500, detail="Item not found after creation")
    return CollectionItemResponse(**item)


@router.delete("/collections/{collection_id}/items/{item_id}", status_code=204)
async def remove_collection_item(collection_id: int, item_id: int, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = CollectionRepository(db)
    existing = await repo.get_by_id(collection_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")
    await repo.remove_item(item_id)


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------


@router.get("/bookmarks", response_model=BookmarkListResponse)
async def list_bookmarks(limit: int = Query(50, ge=1, le=200), email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = BookmarkRepository(db)
    rows = await repo.list_for_user(user_id, limit)
    return BookmarkListResponse(bookmarks=[BookmarkResponse(**r) for r in rows])


@router.get("/bookmarks/search", response_model=BookmarkListResponse)
async def search_bookmarks(q: str = Query(..., min_length=1, max_length=500), email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = BookmarkRepository(db)
    rows = await repo.search(user_id, q)
    return BookmarkListResponse(bookmarks=[BookmarkResponse(**r) for r in rows])


@router.post("/bookmarks", response_model=BookmarkResponse, status_code=201)
async def create_bookmark(body: BookmarkCreate, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = BookmarkRepository(db)
    bm_id = await repo.create(user_id, body.title, body.url, body.snippet, body.tags)
    row = await repo.get_by_id(bm_id, user_id)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create bookmark")
    return BookmarkResponse(**row)


@router.put("/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(bookmark_id: int, body: BookmarkUpdate, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = BookmarkRepository(db)
    existing = await repo.get_by_id(bookmark_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    await repo.update(bookmark_id, user_id, title=body.title, snippet=body.snippet, tags=body.tags)
    row = await repo.get_by_id(bookmark_id, user_id)
    return BookmarkResponse(**row)


@router.delete("/bookmarks/{bookmark_id}", status_code=204)
async def delete_bookmark(bookmark_id: int, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = BookmarkRepository(db)
    existing = await repo.get_by_id(bookmark_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    await repo.delete(bookmark_id, user_id)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(limit: int = Query(50, ge=1, le=200), email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = NotificationRepository(db)
    rows = await repo.list_for_user(user_id, limit)
    unread = await repo.unread_count(user_id)
    return NotificationListResponse(notifications=[NotificationResponse(**r) for r in rows], unread_count=unread)


@router.post("/notifications/{notification_id}/read", status_code=204)
async def mark_notification_read(notification_id: int, email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = NotificationRepository(db)
    await repo.mark_read(notification_id, user_id)


@router.post("/notifications/read-all", status_code=204)
async def mark_all_notifications_read(email: str = Depends(get_current_user), db=Depends(get_db)):
    user_id = await _get_user_id(email, db)
    repo = NotificationRepository(db)
    await repo.mark_all_read(user_id)
