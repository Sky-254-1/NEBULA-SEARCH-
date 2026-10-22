"""Unified search service composing query processing, web search, vector search, ranking, and analytics."""

import logging
import time
from typing import Any

from app.config import get_settings
from app.database.engine import DatabaseConnection
from app.search.intelligence import (
    personalization_engine,
    query_suggestion_engine,
    spell_corrector,
)
from app.search.query_understanding.query_processor import query_processor
from app.search.ranking import hybrid_ranker
from app.services.search import run_web_search
from vector.pipeline import hybrid_search as vector_hybrid_search
from app.services.ai import get_ai_answer, synthesize_snippets

logger = logging.getLogger("nebula.search.service")
settings = get_settings()


class SearchService:
    """Single entrypoint for all search modes."""

    async def search(
        self,
        db: DatabaseConnection,
        user_id: int,
        query: str,
        mode: str = "hybrid",
        page: int = 1,
        page_size: int = 20,
        enable_spell_check: bool = True,
        enable_personalization: bool = True,
        enable_diversity: bool = True,
        filters: dict | None = None,
        include_ai_answer: bool = True,
        include_suggestions: bool = True,
    ) -> dict[str, Any]:
        start = time.time()
        original_query = query

        processed = await query_processor.process_for_search(query)
        processed_query = processed.get("processed") or processed.get("normalized") or query

        if enable_spell_check:
            corrected, was_corrected = await spell_corrector.correct_query(processed_query)
            if was_corrected:
                logger.info("Spell corrected '%s' -> '%s'", processed_query, corrected)
                processed_query = corrected

        results: list[dict] = []
        ai_answer = None
        suggestions = None
        facets = None

        try:
            if mode == "web":
                web_results = await run_web_search(processed_query, backend="wikipedia", page=page, page_size=page_size)
                results = [
                    {
                        "id": i,
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                        "url": r.get("url", ""),
                        "source": "web",
                        "score": r.get("score", 0.0),
                    }
                    for i, r in enumerate(web_results, 1)
                ]
            elif mode == "vector":
                results = await vector_hybrid_search(db, user_id, processed_query, top_k=page_size)
                for i, r in enumerate(results, 1):
                    r.setdefault("source", "vector")
                    r.setdefault("id", r.get("chunk_id", i))
            elif mode == "hybrid":
                web_results, vector_results = await _gather(
                    processed_query, db, user_id, page_size
                )
                results = web_results + vector_results
                results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            elif mode == "ai":
                answer, provider = await get_ai_answer(processed_query)
                ai_answer = {"answer": answer, "provider": provider, "citations": []}

            if results:
                ranked = await hybrid_ranker.rank(
                    query=processed_query,
                    results=results,
                    user_profile=None,
                    enable_diversity=enable_diversity,
                )
                if enable_personalization:
                    try:
                        ranked = await personalization_engine.personalize_results(user_id, processed_query, ranked)
                    except Exception as exc:
                        logger.debug("Personalization failed: %s", exc)
                start_idx = (page - 1) * page_size
                results = ranked[start_idx : start_idx + page_size]

            if include_ai_answer and mode != "ai" and results:
                try:
                    synth = await synthesize_snippets(processed_query, [r.get("snippet") or r.get("content", "") for r in results[:5]])
                    if synth and synth.synthesis:
                        ai_answer = {"answer": synth.synthesis, "provider": "openai", "citations": []}
                except Exception as exc:
                    logger.debug("AI answer synthesis failed: %s", exc)

            if include_suggestions:
                try:
                    suggestions = [
                        s.suggestion for s in await query_suggestion_engine.get_suggestions(processed_query, user_id, limit=5)
                    ]
                except Exception:
                    suggestions = []

            if filters:
                results = _apply_filters(results, filters)

        except Exception as exc:
            logger.exception("Search failed: %s", exc)
            raise

        elapsed = (time.time() - start) * 1000

        try:
            from app.database.repositories.search import SearchRepository
            repo = SearchRepository(db)
            await repo.log_search(user_id, original_query, mode, len(results))
        except Exception as exc:
            logger.debug("Search logging failed: %s", exc)

        return {
            "query": processed_query,
            "original_query": original_query,
            "results": results,
            "ai_answer": ai_answer,
            "suggestions": suggestions,
            "facets": facets,
            "total": len(results),
            "response_time_ms": round(elapsed, 2),
        }


async def _gather(query: str, db, user_id: int, page_size: int) -> tuple[list[dict], list[dict]]:
    half = max(page_size // 2, 1)
    web_task = run_web_search(query, backend="wikipedia", page=1, page_size=half)
    vector_task = vector_hybrid_search(db, user_id, query, top_k=half)
    web_results, vector_results = await __import__("asyncio").gather(web_task, vector_task, return_exceptions=True)

    web: list[dict] = []
    if isinstance(web_results, Exception):
        logger.debug("Web search failed: %s", web_results)
    else:
        web = [
            {
                "id": i,
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "url": r.get("url", ""),
                "source": "web",
                "score": r.get("score", 0.0),
            }
            for i, r in enumerate(web_results, 1)
        ]

    vec: list[dict] = []
    if isinstance(vector_results, Exception):
        logger.debug("Vector search failed: %s", vector_results)
    else:
        for i, r in enumerate(vector_results, 1):
            r.setdefault("source", "vector")
            r.setdefault("id", r.get("chunk_id", i))
            vec.append(r)

    return web, vec


def _apply_filters(results: list[dict], filters: dict) -> list[dict]:
    if not filters:
        return results
    out = []
    for item in results:
        match = True
        if filters.get("source") and item.get("source") not in filters["source"]:
            match = False
        if filters.get("document_type"):
            url = item.get("url", "")
            ext = url.split(".")[-1].lower() if url else ""
            if ext not in filters["document_type"]:
                match = False
        if match:
            out.append(item)
    return out


search_service = SearchService()
