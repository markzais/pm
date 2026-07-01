import os
import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend import db
from backend.app import app


@pytest.fixture(autouse=True)
def temp_db_path(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "kanban.db")
    monkeypatch.setattr(db, "DB_CONN", None)
    db.initialize_database()
    return tmp_path


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def login(client):
    response = client.post("/api/login", json={"username": "user", "password": "password"})
    assert response.status_code == 200
    return response.json()["token"]


def test_get_board_returns_board(client):
    token = login(client)
    response = client.get("/api/board", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Kanban Studio"
    assert len(data["columns"]) == 5
    assert len(data["cards"]) == 6


def test_create_update_and_delete_card(client):
    token = login(client)
    response = client.get("/api/board", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    board = response.json()
    column_id = board["columns"][0]["id"]

    create_response = client.post(
        "/api/cards",
        json={"columnId": column_id, "title": "New Task", "description": "Details"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 200
    card = create_response.json()
    assert card["title"] == "New Task"

    update_response = client.patch(
        f"/api/cards/{card['id']}",
        json={"title": "Updated Task", "description": "New details", "updatedAt": card["updatedAt"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated Task"

    delete_response = client.delete(
        f"/api/cards/{card['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "ok"


def test_move_card(client):
    token = login(client)
    board_response = client.get("/api/board", headers={"Authorization": f"Bearer {token}"})
    board = board_response.json()
    source_column_id = board["columns"][0]["id"]
    target_column_id = board["columns"][1]["id"]
    card_id = board["cards"][0]["id"]

    move_response = client.post(
        f"/api/cards/{card_id}/move",
        json={"targetColumnId": target_column_id, "position": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert move_response.status_code == 200
    moved_card = move_response.json()
    assert moved_card["columnId"] == target_column_id


def test_rename_column(client):
    token = login(client)
    board_response = client.get("/api/board", headers={"Authorization": f"Bearer {token}"})
    column_id = board_response.json()["columns"][0]["id"]

    rename_response = client.patch(
        f"/api/columns/{column_id}",
        json={"title": "Updated Column"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rename_response.status_code == 200
    assert rename_response.json()["status"] == "ok"


@pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY is not configured in environment",
)
def test_ai_prompt_returns_response(client):
    token = login(client)
    prompt_response = client.post(
        "/api/ai/prompt",
        json={"message": "What is 2+2?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert prompt_response.status_code == 200
    data = prompt_response.json()
    assert "response_text" in data
    assert isinstance(data["response_text"], str)
    assert data["response_text"].strip() != ""
