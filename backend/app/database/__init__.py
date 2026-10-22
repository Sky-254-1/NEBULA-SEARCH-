"""Database connection, migrations, and repositories."""

from collections.abc import AsyncGenerator

from app.database.engine import DatabaseConnection, connect
from app.database.migrate import run_migrations

__all__ = ["DatabaseConnection", "connect", "get_db", "init_db"]


async def get_db() -> AsyncGenerator[DatabaseConnection, None]:
    db = await connect()
    try:
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    await run_migrations()
