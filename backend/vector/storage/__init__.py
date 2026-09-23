"""Vector file storage helpers."""

from pathlib import Path

from app.config import get_settings


def vector_path(user_id: int, document_id: int, chunk_id: int) -> Path:
    settings = get_settings()
    return settings.storage_vector / str(user_id) / str(document_id) / f"{chunk_id}.json"


def index_path(user_id: int) -> Path:
    settings = get_settings()
    return settings.storage_indexes / str(user_id) / "manifest.json"
