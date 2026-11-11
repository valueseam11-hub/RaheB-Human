import os
import tempfile
import unittest
from pathlib import Path
from raheb_human.core import database

class DatabaseAdapterTests(unittest.TestCase):
    def test_sqlite_development_fallback_supports_dbapi_and_transactions(self):
        previous = database.DATABASE_URL
        database.DATABASE_URL = ""
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "test.sqlite3"
                with database.connect(path) as con:
                    con.execute("CREATE TABLE sample (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
                    con.execute("INSERT INTO sample(id, value) VALUES(?, ?)", ("one", "persisted"))
                with database.connect(path) as con:
                    row = con.execute("SELECT value FROM sample WHERE id=?", ("one",)).fetchone()
                    self.assertEqual(row["value"], "persisted")
        finally:
            database.DATABASE_URL = previous

    def test_postgres_mode_requires_psycopg_connection_not_silent_sqlite_fallback(self):
        previous = database.DATABASE_URL
        database.DATABASE_URL = "postgresql://invalid:invalid@127.0.0.1:1/invalid"
        try:
            with self.assertRaises(Exception):
                database.connect("unused.sqlite3")
        finally:
            database.DATABASE_URL = previous

if __name__ == "__main__":
    unittest.main()
