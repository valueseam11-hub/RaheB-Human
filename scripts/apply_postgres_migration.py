"""Apply a checked-in PostgreSQL migration using a dedicated migration DSN.

Never point RAHEB_MIGRATION_DATABASE_URL at the restricted runtime role.
"""
import argparse
import os
from pathlib import Path
import psycopg

ROOT=Path(__file__).resolve().parents[1]
MIGRATIONS=(ROOT/"migrations"/"postgresql").resolve()
parser=argparse.ArgumentParser()
parser.add_argument("--file",default="0001_tenant_runtime.sql")
args=parser.parse_args()
target=(MIGRATIONS/args.file).resolve()
if target.parent!=MIGRATIONS or not target.is_file():
    raise SystemExit("Migration must be an existing direct child of migrations/postgresql")
dsn=os.environ.get("RAHEB_MIGRATION_DATABASE_URL") or os.environ.get("RAHEB_TEST_DATABASE_URL")
if not dsn:
    raise SystemExit("RAHEB_MIGRATION_DATABASE_URL (or test-only RAHEB_TEST_DATABASE_URL) is required")
sql=target.read_text(encoding="utf-8")
with psycopg.connect(dsn) as connection:
    connection.execute(sql)
print(f"Applied {target.name}")
