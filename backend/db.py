import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent / "kanban.db"

DB_CONN: Optional[sqlite3.Connection] = None


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_db() -> sqlite3.Connection:
    global DB_CONN
    if DB_CONN is None:
        DB_CONN = sqlite3.connect(DB_PATH, check_same_thread=False)
        DB_CONN.row_factory = sqlite3.Row
    return DB_CONN


def initialize_database() -> None:
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            position INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(board_id, position)
        );

        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_id INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            position INTEGER NOT NULL,
            metadata TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS card_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
            action TEXT NOT NULL,
            payload TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    conn.commit()
    _seed_default_data(conn)


def _seed_default_data(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", ("user",))
    if cursor.fetchone():
        return

    password_hash = _hash_password("password")
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("user", password_hash),
    )
    user_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO boards (user_id, title) VALUES (?, ?)",
        (user_id, "Kanban Studio"),
    )
    board_id = cursor.lastrowid

    columns = [
        "Backlog",
        "Discovery",
        "In Progress",
        "Review",
        "Done",
    ]
    column_ids = []
    for position, title in enumerate(columns):
        cursor.execute(
            "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
            (board_id, title, position),
        )
        column_ids.append(cursor.lastrowid)

    cards = [
        (column_ids[0], "Align roadmap themes", "Draft quarterly themes with impact statements and metrics.", 0),
        (column_ids[0], "Gather customer signals", "Review support tags, sales notes, and churn feedback.", 1),
        (column_ids[1], "Prototype analytics view", "Sketch initial dashboard layout and key drill-downs.", 0),
        (column_ids[2], "Build team sync ritual", "Create a weekly check-in for progress and blockers.", 0),
        (column_ids[3], "Review user onboarding flow", "Validate the first three steps of onboarding for friction.", 0),
        (column_ids[4], "Publish launch plan", "Share the rollout plan with the team and stakeholders.", 0),
    ]

    for column_id, title, description, position in cards:
        cursor.execute(
            "INSERT INTO cards (column_id, title, description, position, metadata) VALUES (?, ?, ?, ?, ?)",
            (column_id, title, description, position, json.dumps({})),
        )

    conn.commit()


def verify_user(username: str, password: str) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        return False
    return row["password_hash"] == _hash_password(password)


def get_user_id(username: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    return row["id"] if row else None


def get_board_for_user(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM boards WHERE user_id = ?", (user_id,))
    board = cursor.fetchone()
    if not board:
        return None

    cursor.execute(
        "SELECT id, title, position FROM columns WHERE board_id = ? ORDER BY position",
        (board["id"],),
    )
    columns = cursor.fetchall()
    column_ids = [column["id"] for column in columns]

    cards = []
    if column_ids:
        placeholders = ",".join("?" for _ in column_ids)
        cursor.execute(
            f"SELECT id, column_id, title, description, position, metadata, updated_at FROM cards WHERE column_id IN ({placeholders}) ORDER BY position",
            tuple(column_ids),
        )
        cards = cursor.fetchall()

    board_columns = [
        {
            "id": column["id"],
            "title": column["title"],
            "position": column["position"],
            "cardIds": [card["id"] for card in cards if card["column_id"] == column["id"]],
        }
        for column in columns
    ]

    board_cards = [
        {
            "id": card["id"],
            "columnId": card["column_id"],
            "title": card["title"],
            "description": card["description"],
            "position": card["position"],
            "metadata": json.loads(card["metadata"]) if card["metadata"] else {},
            "updatedAt": card["updated_at"],
        }
        for card in cards
    ]

    return {
        "id": board["id"],
        "title": board["title"],
        "columns": board_columns,
        "cards": board_cards,
    }


def get_card(card_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, column_id, title, description, position, metadata, updated_at FROM cards WHERE id = ?",
        (card_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "columnId": row["column_id"],
        "title": row["title"],
        "description": row["description"],
        "position": row["position"],
        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
        "updatedAt": row["updated_at"],
    }


def get_column(column_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, board_id, title, position FROM columns WHERE id = ?", (column_id,))
    return cursor.fetchone()


def create_card(column_id: int, title: str, description: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(position) FROM cards WHERE column_id = ?", (column_id,))
    row = cursor.fetchone()
    next_position = (row[0] or -1) + 1
    metadata = json.dumps({})
    cursor.execute(
        "INSERT INTO cards (column_id, title, description, position, metadata) VALUES (?, ?, ?, ?, ?)",
        (column_id, title, description, next_position, metadata),
    )
    conn.commit()
    return get_card(cursor.lastrowid)


def delete_card(card_id: int):
    conn = get_db()
    cursor = conn.cursor()
    card = get_card(card_id)
    if card is None:
        return False

    cursor.execute(
        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
        (card["columnId"], card["position"]),
    )
    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()
    return True


def update_card(card_id: int, title: Optional[str], description: Optional[str], updated_at: Optional[str]):
    card = get_card(card_id)
    if card is None:
        return None
    if updated_at and updated_at != card["updatedAt"]:
        raise ValueError("conflict")

    conn = get_db()
    cursor = conn.cursor()
    new_title = title if title is not None else card["title"]
    new_description = description if description is not None else card["description"]
    cursor.execute(
        "UPDATE cards SET title = ?, description = ?, updated_at = datetime('now') WHERE id = ?",
        (new_title, new_description, card_id),
    )
    conn.commit()
    return get_card(card_id)


def move_card(card_id: int, target_column_id: int, position: int):
    card = get_card(card_id)
    if card is None:
        return None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(position) FROM cards WHERE column_id = ?", (target_column_id,))
    row = cursor.fetchone()
    max_position = row[0] if row[0] is not None else -1
    destination = max(0, min(position, max_position + 1))

    if card["columnId"] == target_column_id:
        if destination == card["position"]:
            return card

        if destination > card["position"]:
            cursor.execute(
                "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ? AND position <= ?",
                (target_column_id, card["position"], destination),
            )
        else:
            cursor.execute(
                "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ? AND position < ?",
                (target_column_id, destination, card["position"]),
            )
        cursor.execute(
            "UPDATE cards SET position = ? WHERE id = ?",
            (destination, card_id),
        )
    else:
        cursor.execute(
            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
            (card["columnId"], card["position"]),
        )
        cursor.execute(
            "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
            (target_column_id, destination),
        )
        cursor.execute(
            "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
            (target_column_id, destination, card_id),
        )

    conn.commit()
    return get_card(card_id)


def rename_column(column_id: int, title: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE columns SET title = ? WHERE id = ?", (title, column_id))
    conn.commit()
    return cursor.rowcount > 0
