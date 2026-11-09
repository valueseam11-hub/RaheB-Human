"""Apply the checked-in PostgreSQL schema as a migration administrator.

Use RAHEB_MIGRATION_DATABASE_URL, never the runtime application role.
"""
import os
from pathlib import Path
import psycopg

dsn=os.environ.get("RAHEB_MIGRATION_DATABASE_URL")
if not dsn:
    raise SystemExit("RAHEB_MIGRATION_DATABASE_URL is required")
sql_path=Path(__file__).resolve().parents[1]/"migrations"/"postgresql"/"0001_trust_foundation.sql"
with psycopg.connect(dsn) as connection:
    connection.execute(sql_path.read_text(encoding="utf-8"))
print("Applied PostgreSQL trust foundation migration.")
