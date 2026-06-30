from pathlib import Path
from typing import Dict

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

FRONTEND_BUILD_DIR = Path(__file__).resolve().parents[1] / "frontend" / "out"

VALID_TOKENS: Dict[str, str] = {}


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.post("/api/login")
async def login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")

    if username == "user" and password == "password":
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
