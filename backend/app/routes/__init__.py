"""API route modules."""

from app.routes import admin
from app.routes import ai
from app.routes import audio
from app.routes import auth
from app.routes import crawler
from app.routes import features
from app.routes import health
from app.routes import oauth
from app.routes import search
from app.routes import storage
from app.routes import vector

__all__ = [
    "admin",
    "ai",
    "audio",
    "auth",
    "crawler",
    "features",
    "health",
    "oauth",
    "search",
    "storage",
    "vector",
]
