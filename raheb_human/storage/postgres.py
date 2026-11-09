"""PostgreSQL tenant transaction boundary; caller must authenticate owner identity."""
from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Iterator
from uuid import UUID
try:
    import psycopg
except ImportError:
    psycopg = None

class PostgresNotConfigured(RuntimeError):
    pass

class PostgresTenantStore:
    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.environ.get("RAHEB_DATABASE_URL", "")
        if not self.dsn:
            raise PostgresNotConfigured("RAHEB_DATABASE_URL is required")
        if psycopg is None:
            raise PostgresNotConfigured("Install psycopg[binary] to enable PostgreSQL storage")

    @contextmanager
    def tenant_transaction(self, owner_id: str) -> Iterator["psycopg.Connection"]:
        """Bind authenticated owner UUID transaction-locally; never accept it from JSON."""
        try:
            tenant = str(UUID(owner_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("owner_id must be a UUID") from exc
        with psycopg.connect(self.dsn) as connection:
            with connection.transaction():
                connection.execute("SELECT set_config('raheb.owner_id', %s, true)", (tenant,))
                yield connection
