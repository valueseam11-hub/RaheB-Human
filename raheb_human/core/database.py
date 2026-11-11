"""DB-API adapter: PostgreSQL in production, SQLite for local development."""
from pathlib import Path
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

class Connection:
    def __init__(self, raw, backend):
        self.raw, self.backend = raw, backend
    def execute(self, sql, params=()):
        if self.backend == "postgres":
            from psycopg.rows import dict_row
            cur = self.raw.cursor(row_factory=dict_row)
            cur.execute(sql.replace("?", "%s"), params)
            return cur
        return self.raw.execute(sql, params)
    def executescript(self, script):
        if self.backend == "postgres":
            script = script.replace("seq INTEGER PRIMARY KEY AUTOINCREMENT", "seq BIGSERIAL PRIMARY KEY")
            for statement in script.split(";"):
                if statement.strip():
                    self.execute(statement)
        else:
            self.raw.executescript(script)
    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def close(self): self.raw.close()

def connect(database, timeout=10, isolation_level="DEFERRED"):
    if DATABASE_URL:
        import psycopg
        raw = psycopg.connect(DATABASE_URL, connect_timeout=10)
        return Connection(raw, "postgres")
    import sqlite3
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = sqlite3.connect(path, timeout=timeout, isolation_level=isolation_level)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA foreign_keys=ON")
    raw.execute("PRAGMA journal_mode=WAL")
    return Connection(raw, "sqlite")
