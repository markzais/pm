import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.db import (
    create_card,
    delete_card,
    get_board_for_user,
    get_card,
    get_column,
    get_user_id,
    initialize_database,
    move_card,
    rename_column,
    update_card,
    verify_user,
    get_db,
)

app = FastAPI()
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

FRONTEND_BUILD_DIR = Path(__file__).resolve().parents[1] / "frontend" / "out"

VALID_TOKENS: Dict[str, str] = {}


@app.on_event("startup")
async def startup_event():
    initialize_database()


class CreateCardRequest(BaseModel):
    columnId: int
    title: str
    description: Optional[str] = ""


class UpdateCardRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    updatedAt: Optional[str] = None


class MoveCardRequest(BaseModel):
    targetColumnId: int
    position: int


class RenameColumnRequest(BaseModel):
    title: str


class AIPromptRequest(BaseModel):
    message: str


class AIAction(BaseModel):
    action_type: str
    card: Optional[dict] = None
    target_column_id: Optional[int] = None
    position: Optional[int] = None


def parse_ai_response(raw_text: str) -> dict:
    candidate = raw_text.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return {"response_text": raw_text.strip(), "actions": []}

    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object")

    response_text = data.get("response_text")
    if not isinstance(response_text, str) or not response_text.strip():
        raise ValueError("response_text is required")

    actions = data.get("actions", [])
    if actions is None:
        actions = []
    if not isinstance(actions, list):
        raise ValueError("actions must be a list")

    normalized_actions = []
    for action in actions:
        if not isinstance(action, dict):
            raise ValueError("each action must be an object")
        action_type = action.get("action_type")
        if action_type not in {"create", "update", "move", "delete"}:
            raise ValueError("unsupported action_type")
        normalized_actions.append(
            {
                "action_type": action_type,
                "card": action.get("card") if isinstance(action.get("card"), dict) else {},
                "target_column_id": action.get("target_column_id"),
                "position": action.get("position"),
            }
        )

    return {"response_text": response_text, "actions": normalized_actions}


def _ensure_board_access(user_id: int, card_id: Optional[int] = None, column_id: Optional[int] = None) -> dict:
    board = get_board_for_user(user_id)
    if board is None:
        raise ValueError("board not found")

    allowed_columns = {column["id"] for column in board["columns"]}
    if column_id is not None and column_id not in allowed_columns:
        raise ValueError("column not found")

    if card_id is not None:
        card = get_card(card_id)
        if card is None or card["columnId"] not in allowed_columns:
            raise ValueError("card not found")
        return board
    return board


def apply_ai_actions(user_id: int, actions: List[dict]) -> List[dict]:
    board = get_board_for_user(user_id)
    if board is None:
        raise ValueError("board not found")

    allowed_columns = {column["id"] for column in board["columns"]}
    applied_changes: List[dict] = []
    conn = get_db()

    try:
        conn.execute("BEGIN")
        for action in actions:
            action_type = action.get("action_type")
            card_payload = action.get("card") or {}
            target_column_id = action.get("target_column_id")
            position = action.get("position")

            if action_type == "create":
                if target_column_id is None or target_column_id not in allowed_columns:
                    raise ValueError("invalid target column")
                title = card_payload.get("title")
                description = card_payload.get("description") or ""
                if not isinstance(title, str) or not title.strip():
                    raise ValueError("card title is required")

                cursor = conn.cursor()
                cursor.execute("SELECT MAX(position) FROM cards WHERE column_id = ?", (target_column_id,))
                row = cursor.fetchone()
                max_position = row[0] if row and row[0] is not None else -1
                target_position = max(0, min(int(position), max_position + 1)) if position is not None else max_position + 1
                cursor.execute(
                    "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
                    (target_column_id, target_position),
                )
                cursor.execute(
                    "INSERT INTO cards (column_id, title, description, position, metadata) VALUES (?, ?, ?, ?, ?)",
                    (target_column_id, title, description, target_position, json.dumps({})),
                )
                created_id = cursor.lastrowid
                applied_changes.append({"action_type": "create", "card_id": created_id})
            elif action_type == "update":
                card_id = card_payload.get("id")
                if not isinstance(card_id, int):
                    raise ValueError("card id is required")
                _ensure_board_access(user_id, card_id=card_id)
                title = card_payload.get("title")
                description = card_payload.get("description")
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE cards SET title = ?, description = ?, updated_at = datetime('now') WHERE id = ?",
                    (title if title is not None else None, description, card_id),
                )
                applied_changes.append({"action_type": "update", "card_id": card_id})
            elif action_type == "move":
                card_id = card_payload.get("id")
                if not isinstance(card_id, int):
                    raise ValueError("card id is required")
                if target_column_id is None or target_column_id not in allowed_columns:
                    raise ValueError("invalid target column")
                _ensure_board_access(user_id, card_id=card_id)
                cursor = conn.cursor()
                cursor.execute("SELECT column_id, position FROM cards WHERE id = ?", (card_id,))
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("card not found")
                current_column_id, current_position = row[0], row[1]
                destination = max(0, min(int(position if position is not None else 0), 999999))
                cursor.execute("SELECT MAX(position) FROM cards WHERE column_id = ?", (target_column_id,))
                target_row = cursor.fetchone()
                max_target_position = target_row[0] if target_row and target_row[0] is not None else -1
                destination = max(0, min(destination, max_target_position + 1))

                if current_column_id == target_column_id:
                    if destination == current_position:
                        continue
                    if destination > current_position:
                        cursor.execute(
                            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ? AND position <= ?",
                            (target_column_id, current_position, destination),
                        )
                    else:
                        cursor.execute(
                            "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ? AND position < ?",
                            (target_column_id, destination, current_position),
                        )
                    cursor.execute("UPDATE cards SET position = ? WHERE id = ?", (destination, card_id))
                else:
                    cursor.execute(
                        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
                        (current_column_id, current_position),
                    )
                    cursor.execute(
                        "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
                        (target_column_id, destination),
                    )
                    cursor.execute(
                        "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
                        (target_column_id, destination, card_id),
                    )
                applied_changes.append({"action_type": "move", "card_id": card_id})
            elif action_type == "delete":
                card_id = card_payload.get("id")
                if not isinstance(card_id, int):
                    raise ValueError("card id is required")
                _ensure_board_access(user_id, card_id=card_id)
                cursor = conn.cursor()
                cursor.execute("SELECT column_id, position FROM cards WHERE id = ?", (card_id,))
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("card not found")
                column_id, position = row[0], row[1]
                cursor.execute(
                    "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
                    (column_id, position),
                )
                cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
                applied_changes.append({"action_type": "delete", "card_id": card_id})
            else:
                raise ValueError("unsupported action_type")

        conn.commit()
        return applied_changes
    except Exception:
        conn.rollback()
        raise


def _format_board_context(board: dict) -> str:
    lines = [f"Board: {board['title']}"]
    for column in board["columns"]:
        lines.append(f"Column: {column['title']} ({len(column['cardIds'])} cards)")
        for card in board["cards"]:
            if card["columnId"] == column["id"]:
                lines.append(f"- {card['title']}: {card['description']}")
    return "\n".join(lines)


async def call_openrouter(message: str, board: dict) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": "You are an AI assistant that helps manage a kanban board."},
            {"role": "system", "content": _format_board_context(board)},
            {"role": "user", "content": message},
        ],
        "temperature": 0.2,
        "max_tokens": 512,
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(endpoint, json=payload, headers=headers)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter returned {exc.response.status_code}: {exc.response.text}",
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Invalid JSON from OpenRouter") from exc

    choices = data.get("choices")
    if not choices or not isinstance(choices, list):
        raise HTTPException(status_code=502, detail="Unexpected OpenRouter response format")

    first_choice = choices[0]
    message_obj = first_choice.get("message") if isinstance(first_choice, dict) else None
    if not isinstance(message_obj, dict):
        raise HTTPException(status_code=502, detail="OpenRouter response missing message")

    content = message_obj.get("content")
    if not isinstance(content, str):
        raise HTTPException(status_code=502, detail="OpenRouter response missing content")

    return content.strip()


def get_current_user_id(authorization: str = Header(default=None)) -> int:
    token = authorization.replace("Bearer ", "") if authorization else None
    if not token or token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="not authenticated")

    username = VALID_TOKENS[token]
    user_id = get_user_id(username)
    if user_id is None:
        raise HTTPException(status_code=401, detail="invalid token")
    return user_id


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.post("/api/login")
async def login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")

    if username and password and verify_user(username, password):
        token = f"demo-token-{username}"
        VALID_TOKENS[token] = username
        return JSONResponse({"user": username, "token": token})

    raise HTTPException(status_code=401, detail="invalid credentials")


@app.post("/api/logout")
async def logout(authorization: str = Header(default=None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    if token and token in VALID_TOKENS:
        VALID_TOKENS.pop(token, None)
    return JSONResponse({"status": "ok"})


@app.get("/api/me")
async def me(authorization: str = Header(default=None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    if not token or token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="not authenticated")

    return JSONResponse({"user": VALID_TOKENS[token]})


@app.get("/api/board")
async def get_board(user_id: int = Depends(get_current_user_id)):
    board = get_board_for_user(user_id)
    if board is None:
        raise HTTPException(status_code=404, detail="board not found")
    return board


@app.post("/api/ai/prompt")
async def ai_prompt(request: AIPromptRequest, user_id: int = Depends(get_current_user_id)):
    board = get_board_for_user(user_id)
    if board is None:
        raise HTTPException(status_code=404, detail="board not found")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    try:
        response_text = await call_openrouter(request.message, board)
        parsed = parse_ai_response(response_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    applied_changes = []
    if parsed.get("actions"):
        applied_changes = apply_ai_actions(user_id, parsed["actions"])

    return {"response_text": parsed["response_text"], "actions": applied_changes}


@app.post("/api/cards")
async def create_card_route(request: CreateCardRequest, user_id: int = Depends(get_current_user_id)):
    board = get_board_for_user(user_id)
    if board is None:
        raise HTTPException(status_code=404, detail="board not found")

    allowed_columns = {column["id"] for column in board["columns"]}
    if request.columnId not in allowed_columns:
        raise HTTPException(status_code=404, detail="column not found")

    card = create_card(request.columnId, request.title, request.description or "")
    return card


@app.patch("/api/cards/{card_id}")
async def update_card_route(card_id: int, request: UpdateCardRequest, user_id: int = Depends(get_current_user_id)):
    board = get_board_for_user(user_id)
    if board is None:
        raise HTTPException(status_code=404, detail="board not found")

    card = get_card(card_id)
    if card is None or card["columnId"] not in {column["id"] for column in board["columns"]}:
        raise HTTPException(status_code=404, detail="card not found")

    try:
        updated = update_card(card_id, request.title, request.description, request.updatedAt)
    except ValueError:
        raise HTTPException(status_code=409, detail="conflict")
    if updated is None:
        raise HTTPException(status_code=404, detail="card not found")
    return updated


@app.delete("/api/cards/{card_id}")
async def delete_card_route(card_id: int, user_id: int = Depends(get_current_user_id)):
    board = get_board_for_user(user_id)
    if board is None:
        raise HTTPException(status_code=404, detail="board not found")

    card = get_card(card_id)
    if card is None or card["columnId"] not in {column["id"] for column in board["columns"]}:
        raise HTTPException(status_code=404, detail="card not found")

    delete_card(card_id)
    return JSONResponse({"status": "ok"})


@app.post("/api/cards/{card_id}/move")
async def move_card_route(card_id: int, request: MoveCardRequest, user_id: int = Depends(get_current_user_id)):
    board = get_board_for_user(user_id)
    if board is None:
        raise HTTPException(status_code=404, detail="board not found")

    allowed_columns = {column["id"] for column in board["columns"]}
    if request.targetColumnId not in allowed_columns:
        raise HTTPException(status_code=404, detail="column not found")

    card = get_card(card_id)
    if card is None or card["columnId"] not in allowed_columns:
        raise HTTPException(status_code=404, detail="card not found")

    moved = move_card(card_id, request.targetColumnId, request.position)
    if moved is None:
        raise HTTPException(status_code=404, detail="card not found")
    return moved


@app.patch("/api/columns/{column_id}")
async def rename_column_route(column_id: int, request: RenameColumnRequest, user_id: int = Depends(get_current_user_id)):
    board = get_board_for_user(user_id)
    if board is None:
        raise HTTPException(status_code=404, detail="board not found")

    allowed_columns = {column["id"] for column in board["columns"]}
    if column_id not in allowed_columns:
        raise HTTPException(status_code=404, detail="column not found")

    success = rename_column(column_id, request.title)
    if not success:
        raise HTTPException(status_code=404, detail="column not found")
    return JSONResponse({"status": "ok"})


if FRONTEND_BUILD_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_BUILD_DIR), html=True), name="frontend")
else:
    @app.get("/", response_class=HTMLResponse)
    async def root():
        html = """
        <html>
          <head><title>PM MVP - Backend</title></head>
          <body>
            <h1>Project Management MVP - Backend</h1>
            <p>This is a placeholder page from the backend service.</p>
          </body>
        </html>
        """
        return HTMLResponse(content=html)
