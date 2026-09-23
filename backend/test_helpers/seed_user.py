"""Seed test users and data for E2E runs."""

import hashlib
import secrets

from app.services.auth import hash_password

DEFAULT_E2E_EMAIL = "e2e@nebula.test"
DEFAULT_E2E_PASSWORD = "e2e_secret123"


def unique_email(prefix: str = "e2e") -> str:
    token = secrets.token_hex(4)
    return f"{prefix}_{token}@nebula.test"


async def seed_user(db, email: str = DEFAULT_E2E_EMAIL, password: str = DEFAULT_E2E_PASSWORD) -> int:
    from app.database.repositories.user import UserRepository

    users = UserRepository(db)
    existing = await users.get_by_email(email)
    if existing:
        return existing["id"]
    await users.create(email, hash_password(password))
    return await users.get_id_by_email(email)


def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
