"""Apply database migrations with idempotency tracking."""

import re
from pathlib import Path

from app.config import get_settings
from app.database.engine import connect

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

TRACKING_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    filename TEXT UNIQUE NOT NULL,
    version TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

TRACKING_TABLE_SQL_SQLITE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,
    version TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


async def run_migrations() -> None:
    settings = get_settings()
    suffix = "postgres" if settings.uses_postgres else "sqlite"
    suffixed = sorted(MIGRATIONS_DIR.glob(f"*_{suffix}.sql"))
    generic = sorted(MIGRATIONS_DIR.glob("0[0-9][0-9]_*.sql"))
    suffixed_bases = {p.stem.split("_")[0] for p in suffixed}
    files = list(suffixed)
    for p in generic:
        base = p.stem.split("_")[0]
        if base in suffixed_bases:
            continue
        # On SQLite, skip PostgreSQL-only migrations (files suffixed with _postgres)
        if not settings.uses_postgres and p.name.endswith("_postgres.sql"):
            continue
        # On PostgreSQL, skip SQLite-only migrations (files suffixed with _sqlite)
        if settings.uses_postgres and p.name.endswith("_sqlite.sql"):
            continue
        files.append(p)
    files.sort()

    db = await connect()
    try:
        # Disable foreign key constraints for SQLite during migrations
        if not settings.uses_postgres:
            await db.execute("PRAGMA foreign_keys = OFF")
        
        # Create/ensure schema_migrations tracking table
        tracking_sql = TRACKING_TABLE_SQL if settings.uses_postgres else TRACKING_TABLE_SQL_SQLITE
        await db.execute(tracking_sql)
        
        # Get already-applied migrations
        applied = set()
        try:
            cursor = await db.execute(
                "SELECT filename FROM schema_migrations ORDER BY applied_at"
            )
            rows = await cursor.fetchall()
            applied = {row[0] for row in rows}
        except Exception:
            # Table might not exist on first run (shouldn't happen, but be safe)
            pass
        
        for path in files:
            filename = path.name
            
            # Skip already-applied migrations (idempotency via tracking table)
            if filename in applied:
                continue
            
            sql = path.read_text(encoding="utf-8")
            for statement in _split_statements(sql):
                # Skip PostgreSQL-specific EXTENSION statements on SQLite
                if not settings.uses_postgres and _is_extension_statement(statement):
                    continue
                # For SQLite, handle ALTER TABLE ADD COLUMN with idempotency check
                if not settings.uses_postgres and _is_add_column_statement(statement):
                    statement = await _make_add_column_idempotent(db, statement)
                    if statement is None:
                        # Column already exists, skip
                        continue
                try:
                    await db.execute(statement)
                except Exception as exc:
                    # Fallback: SQLite ALTER may fail if column already exists on re-run
                    error_msg = str(exc).lower()
                    if not settings.uses_postgres and ("duplicate column" in error_msg or "duplicate column name" in error_msg):
                        continue
                    # For Postgres: check for "already exists" errors (defense in depth)
                    if settings.uses_postgres and any(
                        phrase in error_msg
                        for phrase in ["already exists", "duplicate column", "duplicate key"]
                    ):
                        continue
                    raise
            
            # Record migration as applied
            version = path.stem.split("_")[0]
            await db.execute(
                "INSERT INTO schema_migrations (filename, version) VALUES ($1, $2)"
                if settings.uses_postgres
                else "INSERT INTO schema_migrations (filename, version) VALUES (?, ?)",
                [filename, version],
            )
        
        # Re-enable foreign key constraints for SQLite after migrations
        if not settings.uses_postgres:
            await db.execute("PRAGMA foreign_keys = ON")
        
        await db.commit()
    finally:
        await db.close()


def _is_extension_statement(statement: str) -> bool:
    """Check if statement is a PostgreSQL CREATE EXTENSION statement."""
    return bool(re.match(r"^\s*CREATE\s+EXTENSION\s+", statement, re.IGNORECASE))


def _is_add_column_statement(statement: str) -> bool:
    """Check if statement is an ALTER TABLE ADD COLUMN statement."""
    return bool(re.match(r"^\s*ALTER\s+TABLE\s+\w+\s+ADD\s+COLUMN\s+", statement, re.IGNORECASE))


async def _make_add_column_idempotent(db, statement: str) -> str | None:
    """
    For SQLite: Check if column exists before adding it.
    Returns the statement if it should be executed, or None if column already exists.
    Also strips PostgreSQL-specific syntax (IF NOT EXISTS, vector type) for SQLite.
    """
    # Strict SQL identifier pattern: alphanumeric + underscore, first char not a digit.
    # This is the only shape we accept into the PRAGMA call below because PRAGMA
    # does not support parameterised queries (bound arguments).
    _SAFE_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def _validate_identifier(value: str, kind: str) -> str:
        if not _SAFE_IDENT_RE.match(value):
            raise ValueError(
                f"Refusing unsafe SQL {kind} identifier: {value!r}"
            )
        return value

    # Strip PostgreSQL-only "IF NOT EXISTS" clause since SQLite doesn't support it in ADD COLUMN
    # and we do our own existence check via PRAGMA
    normalized = re.sub(
        r"^\s*(ALTER\s+TABLE\s+\w+\s+ADD\s+COLUMN\s+)IF\s+NOT\s+EXISTS\s+",
        r"\1",
        statement,
        flags=re.IGNORECASE,
    )

    # Parse table name and column name from ALTER TABLE statement
    match = re.match(r"^\s*ALTER\s+TABLE\s+(\w+)\s+ADD\s+COLUMN\s+(\w+)", normalized, re.IGNORECASE)
    if not match:
        return normalized

    table_name = _validate_identifier(match.group(1), "table")
    column_name = _validate_identifier(match.group(2), "column")

    # Check if column already exists using PRAGMA table_info.
    # PRAGMA does NOT support bound parameters (? / $1) so we rely on the strict
    # identifier validation above combined with the original \w+ regex capture.
    cursor = await db.execute(f"PRAGMA table_info({table_name})")
    columns = await cursor.fetchall()

    # PRAGMA table_info returns rows with: cid, name, type, notnull, dflt_value, pk
    column_exists = any(col[1] == column_name for col in columns)
    
    if column_exists:
        return None  # Skip this statement
    
    # Replace PostgreSQL vector(n) type with BLOB for SQLite (vector unsupported)
    normalized = re.sub(
        r"\bvector\(\s*\d+\s*\)",
        "BLOB",
        normalized,
        flags=re.IGNORECASE,
    )
    
    return normalized


def _split_statements(sql: str) -> list[str]:
    statements = []
    buffer: list[str] = []
    in_dollar_quote = False
    in_begin_block = False
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buffer.append(line)
        if in_dollar_quote:
            if "$$" in line:
                in_dollar_quote = False
                if stripped.endswith(";"):
                    statements.append("\n".join(buffer))
                    buffer = []
        elif in_begin_block:
            upper = stripped.upper()
            if upper == "END;" or upper.endswith("END$$;"):
                in_begin_block = False
                statements.append("\n".join(buffer))
                buffer = []
        else:
            if "$$" in stripped:
                in_dollar_quote = True
            elif stripped.upper().startswith("BEGIN"):
                in_begin_block = True
            elif stripped.endswith(";"):
                statements.append("\n".join(buffer))
                buffer = []
    if buffer:
        statements.append("\n".join(buffer))
    return statements