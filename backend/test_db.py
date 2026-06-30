import sqlite3
import tempfile
from pathlib import Path

import pytest

from backend import db


@pytest.fixture(autouse=True)
def temp_db_path(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "kanban.db")
    monkeypatch.setattr(db, "DB_CONN", None)
    return tmp_path


def test_initialize_database_creates_tables_and_seed_data(temp_db_path):
    db.initialize_database()
    assert db.DB_PATH.exists()

    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert tables >= {"users", "boards", "columns", "cards", "card_history"}

    cursor.execute("SELECT username FROM users")
    users = [row[0] for row in cursor.fetchall()]
    assert users == ["user"]

    cursor.execute("SELECT title FROM boards")
    boards = [row[0] for row in cursor.fetchall()]
    assert boards == ["Kanban Studio"]

    cursor.execute("SELECT COUNT(*) FROM columns")
    assert cursor.fetchone()[0] == 5

    cursor.execute("SELECT COUNT(*) FROM cards")
    assert cursor.fetchone()[0] == 6


def test_verify_user_accepts_seeded_user(temp_db_path):
    db.initialize_database()
    assert db.verify_user("user", "password") is True
    assert db.verify_user("user", "wrong") is False
    assert db.verify_user("missing", "password") is False
