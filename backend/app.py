from pathlib import Path
from typing import Dict, Optional

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
)

app = FastAPI()

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
