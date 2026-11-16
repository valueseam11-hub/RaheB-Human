import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from raheb_human.core import database


class DatabaseAdapterTests(unittest.TestCase):
    def test_qmark_translation_preserves_question_marks_in_quoted_text(self):
        sql = "SELECT '?' AS literal, value FROM sample WHERE id=? AND note='it''s ?'"
        self.assertEqual(
            database._qmark_to_format(sql),
            "SELECT '?' AS literal, value FROM sample WHERE id=%s AND note='it''s ?'",
        )

    def test_sqlite_development_fallback_supports_dbapi_and_transactions(self):
        with patch.dict(os.environ, {"DATABASE_URL": "", "RAHEB_ENV": "development"}):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "test.sqlite3"
                with database.connect(path) as con:
                    con.execute("CREATE TABLE sample (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
                    con.execute(
                        "INSERT INTO sample(id, value) VALUES(?, ?)",
                        ("one", "persisted"),
                    )
                with database.connect(path) as con:
                    row = con.execute(
                        "SELECT value FROM sample WHERE id=?", ("one",)
                    ).fetchone()
                    self.assertEqual(row["value"], "persisted")

    def test_sqlite_transaction_rolls_back_on_exception(self):
        with patch.dict(os.environ, {"DATABASE_URL": "", "RAHEB_ENV": "development"}):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "rollback.sqlite3"
                with database.connect(path) as con:
                    con.execute("CREATE TABLE sample (id TEXT PRIMARY KEY)")
                with self.assertRaisesRegex(RuntimeError, "rollback"):
                    with database.connect(path) as con:
                        con.execute("INSERT INTO sample(id) VALUES(?)", ("x",))
                        raise RuntimeError("rollback")
                with database.connect(path) as con:
                    self.assertIsNone(
                        con.execute("SELECT id FROM sample WHERE id=?", ("x",)).fetchone()
                    )

    def test_production_refuses_silent_sqlite_fallback_without_database_url(self):
        with patch.dict(os.environ, {"DATABASE_URL": "", "RAHEB_ENV": "production"}):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(RuntimeError, "DATABASE_URL is required"):
                    database.connect(Path(tmp) / "must-not-create.sqlite3")

    def test_postgres_mode_requires_real_connection_not_silent_sqlite_fallback(self):
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://invalid:invalid@127.0.0.1:1/invalid",
                "RAHEB_ENV": "production",
            },
        ):
            with self.assertRaises(Exception):
                database.connect("unused.sqlite3")


if __name__ == "__main__":
    unittest.main()
