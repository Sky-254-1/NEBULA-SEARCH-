"""Background task helpers for async operations."""

import logging

logger = logging.getLogger("nebula.background")


async def track_autocomplete_events(
    user_id: int | None,
    query: str,
) -> None:
    """Track autocomplete events (recent searches and popularity)."""
    if not query:
        return
    try:
        from app.database import get_db
        from app.services.autocomplete_service import AutocompleteService
        
        db = await get_db()
        try:
            service = AutocompleteService(db)
            if user_id:
                await service.save_recent(user_id, query)
            await service.update_popularity(query)
        finally:
            await db.close()
    except Exception as exc:
        logger.debug("Background autocomplete tracking failed: %s", exc)