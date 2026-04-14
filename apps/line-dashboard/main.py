import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional

# LINE Messaging API helper
# Use absolute import so `main.py` can be executed from the app folder
from script.line_messenger import (
    push_message,
    broadcast_message,
    build_text_message,
    build_image_message,
    build_sticker_message,
)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN", "")

app = FastAPI(title="Line Dashboard")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/status")
def status():
    return {"tokenConfigured": bool(LINE_NOTIFY_TOKEN)}


@app.post("/api/notify")
async def notify(request: Request):
    data = await request.json()
    # Accept either explicit type or default to push to a provided target
    target_type = data.get("type")  # 'user', 'group', 'broadcast'
    target = data.get("target")
    message = data.get("message", "")
    image = data.get("image")
    sticker = data.get("sticker")
    token = data.get("token")

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    # Build message payloads using script helpers
    messages = [build_text_message(message)]
    if image:
        messages.append(build_image_message(image))
    if sticker and isinstance(sticker, list) and len(sticker) >= 2:
        messages.append(build_sticker_message(sticker[0], sticker[1]))

    # Determine action
    if target_type == "broadcast" or data.get("broadcast"):
        result = broadcast_message(messages, token=token)
    else:
        # For both user and group, the underlying API uses push to the id
        if not target:
            raise HTTPException(status_code=400, detail="target (user_id or group_id) is required")
        result = push_message(target, messages, token=token)

    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result)

    return JSONResponse(result)


@app.post("/api/line/push")
async def line_push(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    message = data.get("message")
    image = data.get("image")
    sticker = data.get("sticker")
    token = data.get("token")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    messages = [build_text_message(message)]
    if image:
        messages.append(build_image_message(image))
    if sticker and isinstance(sticker, list) and len(sticker) >= 2:
        messages.append(build_sticker_message(sticker[0], sticker[1]))

    result = push_message(user_id, messages, token=token)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result)
    return JSONResponse(result)


@app.post("/api/line/broadcast")
async def line_broadcast(request: Request):
    data = await request.json()
    message = data.get("message")
    image = data.get("image")
    sticker = data.get("sticker")
    token = data.get("token")

    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    messages = [build_text_message(message)]
    if image:
        messages.append(build_image_message(image))
    if sticker and isinstance(sticker, list) and len(sticker) >= 2:
        messages.append(build_sticker_message(sticker[0], sticker[1]))

    result = broadcast_message(messages, token=token)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result)
    return JSONResponse(result)
