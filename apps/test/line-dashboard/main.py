"""
LINE MSG CTRL - FastAPI Backend
================================
Usage:
  pip install fastapi uvicorn httpx python-dotenv
  uvicorn main:app --reload --port 5000

Then open: http://localhost:5000
"""

import os
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ─── Load .env ────────────────────────────────────────────────
load_dotenv()

SAVED_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_API_BASE = "https://api.line.me/v2/bot"

# ─── FastAPI App ──────────────────────────────────────────────
app = FastAPI(title="LINE MSG CTRL", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Models ───────────────────────────────────────────────────
class ConnectRequest(BaseModel):
    token: str


class SendRequest(BaseModel):
    token: str
    mode: str  # "push" | "broadcast"
    userId: str = ""
    message: str
    imageUrl: str = ""


# ─── Helpers ──────────────────────────────────────────────────
def _headers(token: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


# ─── Routes ───────────────────────────────────────────────────

@app.get("/")
async def index():
    """Serve the dashboard HTML."""
    return FileResponse("static/index.html")


@app.get("/api/default-token")
async def default_token():
    """Return token from .env if available."""
    return {"token": SAVED_TOKEN}


@app.post("/api/connect")
async def connect(req: ConnectRequest):
    """Verify token and return bot info + quota."""
    if not req.token:
        raise HTTPException(status_code=400, detail="No token provided")

    async with httpx.AsyncClient() as client:
        # Get bot info
        r = await client.get(f"{LINE_API_BASE}/info", headers=_headers(req.token))
        if r.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")

        bot_info = r.json()

        # Get quota
        q = await client.get(
            f"{LINE_API_BASE}/message/quota/consumption",
            headers=_headers(req.token),
        )
        quota = q.json() if q.status_code == 200 else None

    return {"bot": bot_info, "quota": quota}


@app.post("/api/send")
async def send(req: SendRequest):
    """Send push or broadcast message."""
    if not req.token or not req.message:
        raise HTTPException(status_code=400, detail="Token and message required")

    if req.mode == "push" and not req.userId:
        raise HTTPException(status_code=400, detail="User ID required for push")

    # Build messages
    messages = [{"type": "text", "text": req.message}]
    if req.imageUrl:
        messages.append({
            "type": "image",
            "originalContentUrl": req.imageUrl,
            "previewImageUrl": req.imageUrl,
        })

    # Build request
    if req.mode == "push":
        url = f"{LINE_API_BASE}/message/push"
        payload = {"to": req.userId, "messages": messages}
    else:
        url = f"{LINE_API_BASE}/message/broadcast"
        payload = {"messages": messages}

    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=_headers(req.token), json=payload)

    body = r.json() if r.text.strip() else {}

    return {
        "ok": r.status_code == 200,
        "status": r.status_code,
        "body": body,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ─── Run directly ────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║   LINE MSG CTRL - Dashboard v1.0     ║")
    print("  ╠══════════════════════════════════════╣")
    print("  ║   http://localhost:5000              ║")
    print("  ╚══════════════════════════════════════╝")
    print()
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
