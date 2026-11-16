"""DB-API adapter with transaction-local tenant binding.

SQLite is for local tests and synthetic previews only. Production requires
PostgreSQL and an authenticated owner UUID on every tenant-scoped transaction.
"""
from __future__ import annotations
import os
from pathlib import Path
from uuid import UUID

DATABASE_URL=os.environ.get("DATABASE_URL","").strip()
APP_ENV=os.environ.get("RAHEB_ENV","development").strip().lower()

def _qmark_to_format(sql: str) -> str:
    out=[]; quote=None; i=0
    while i<len(sql):
        ch=sql[i]
        if quote:
            out.append(ch)
            if ch==quote:
                if i+1<len(sql) and sql[i+1]==quote:
                    out.append(sql[i+1]); i+=1
                else: quote=None
        elif ch in ("'", '"'):
            quote=ch; out.append(ch)
        elif ch=="?": out.append("%s")
        else: out.append(ch)
        i+=1
    return "".join(out)

class Connection:
    def __init__(self,raw,backend):
        self.raw=raw; self.backend=backend
    def execute(self,sql,params=()):
        if self.backend=="postgres":
            from psycopg.rows import dict_row
            cur=self.raw.cursor(row_factory=dict_row)
            cur.execute(_qmark_to_format(sql),params)
            return cur
        return self.raw.execute(sql,params)
    def executescript(self,script):
        if self.backend=="postgres":
            script=script.replace("seq INTEGER PRIMARY KEY AUTOINCREMENT","seq BIGSERIAL PRIMARY KEY")
            for statement in script.split(";"):
                if statement.strip(): self.execute(statement)
        else: self.raw.executescript(script)
    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def close(self): self.raw.close()

def connect(database,timeout=10,isolation_level="DEFERRED",owner_id=None):
    dsn=os.environ.get("DATABASE_URL",DATABASE_URL).strip()
    env=os.environ.get("RAHEB_ENV",APP_ENV).strip().lower()
    if dsn:
        import psycopg
        raw=psycopg.connect(dsn,connect_timeout=10)
        con=Connection(raw,"postgres")
        if owner_id is not None:
            try: UUID(str(owner_id))
            except (ValueError,TypeError,AttributeError):
                raw.close()
                raise ValueError("authenticated owner_id must be a UUID for PostgreSQL tenant scope")
            con.execute("SELECT set_config('raheb.owner_id', %s, true)",(str(owner_id),))
        return con
    if env in {"production","prod"}:
        raise RuntimeError("DATABASE_URL is required in production; refusing SQLite fallback.")
    import sqlite3
    path=Path(database); path.parent.mkdir(parents=True,exist_ok=True)
    raw=sqlite3.connect(path,timeout=timeout,isolation_level=isolation_level)
    raw.row_factory=sqlite3.Row
    raw.execute("PRAGMA foreign_keys=ON"); raw.execute("PRAGMA journal_mode=WAL")
    return Connection(raw,"sqlite")
