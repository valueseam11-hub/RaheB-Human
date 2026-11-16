"""Small DB-API adapter for PostgreSQL production and SQLite local tests.

The application deliberately uses a narrow common SQL subset. PostgreSQL is
selected only by DATABASE_URL; production mode fails closed when it is absent.
"""
from __future__ import annotations

import os
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
APP_ENV = os.environ.get("RAHEB_ENV", "development").strip().lower()


def _qmark_to_format(sql: str) -> str:
    """Translate DB-API qmark placeholders without touching quoted literals.

    Handles SQL single/double quoted strings and doubled quote escaping. The
    application's SQL does not use PostgreSQL dollar-quoted bodies.
    """
    out = []
    quote = None
    i = 0
    while i < len(sql):
        char = sql[i]
        if quote:
            out.append(char)
            if char == quote:
                if i + 1 < len(sql) and sql[i + 1] == quote:
                    out.append(sql[i + 1])
                    i += 1
                else:
                    quote = None
        elif char in ("'", '"'):
            quote = char
            out.append(char)
        elif char == "?":
            out.append("%s")
        else:
            out.append(char)
        i += 1
    return "".join(out)


class Connection:
    def __init__(self, raw, backend: str):
        self.raw = raw
        self.backend = backend

    def execute(self, sql: str, params=()):
        if self.backend == "postgres":
            from psycopg.rows import dict_row
            cursor = self.raw.cursor(row_factory=dict_row)
            cursor.execute(_qmark_to_format(sql), params)
            return cursor
        return self.raw.execute(sql, params)

    def executescript(self, script: str):
        if self.backend == "postgres":
            # The application's startup schema consists of ordinary DDL
            # statements separated by semicolons (no procedural SQL blocks).
            script = script.replace(
                "seq INTEGER PRIMARY KEY AUTOINCREMENT",
                "seq BIGSERIAL PRIMARY KEY",
            )
            for statement in script.split(";"):
                if statement.strip():
                    self.execute(statement)
        else:
            self.raw.executescript(script)

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        self.raw.close()

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        try:
            if typ is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()


def connect(database, timeout=10, isolation_level="DEFERRED"):
    database_url = os.environ.get("DATABASE_URL", DATABASE_URL).strip()
    app_env = os.environ.get("RAHEB_ENV", APP_ENV).strip().lower()
    if database_url:
        import psycopg
        raw = psycopg.connect(database_url, connect_timeout=10)
        return Connection(raw, "postgres")
    if app_env in {"production", "prod"}:
        raise RuntimeError(
            "DATABASE_URL is required in production; refusing SQLite fallback."
        )
    import sqlite3
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = sqlite3.connect(path, timeout=timeout, isolation_level=isolation_level)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA foreign_keys=ON")
    raw.execute("PRAGMA journal_mode=WAL")
    return Connection(raw, "sqlite")
