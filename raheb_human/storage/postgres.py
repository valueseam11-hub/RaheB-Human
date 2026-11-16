"""PostgreSQL transaction boundary for authenticated owner tenants."""
from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Iterator
from uuid import UUID

try:
    import psycopg
except ImportError:
    psycopg=None

class PostgresNotConfigured(RuntimeError):
    pass

class PostgresTenantStore:
    def __init__(self,dsn: str|None=None):
        self.dsn=dsn or os.environ.get("DATABASE_URL","")
        if not self.dsn:
            raise PostgresNotConfigured("DATABASE_URL is required")
        if psycopg is None:
            raise PostgresNotConfigured("Install psycopg[binary]")

    @contextmanager
    def tenant_transaction(self,authenticated_owner_id: str)->Iterator["psycopg.Connection"]:
        try:
            owner=str(UUID(authenticated_owner_id))
        except (ValueError,TypeError,AttributeError) as exc:
            raise ValueError("authenticated owner identity must be a UUID") from exc
        with psycopg.connect(self.dsn) as connection:
            with connection.transaction():
                connection.execute("SELECT set_config('raheb.owner_id', %s, true)",(owner,))
                yield connection
