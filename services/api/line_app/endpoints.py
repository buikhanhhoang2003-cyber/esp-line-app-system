# line_endpoint.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from line import push, broadcast
from config import config

app = FastAPI(title="LINE Messaging API")

# ============= Request Models =============

class TextMessage(BaseModel):
    type: str = "text"
    text: str

class ImageMessage(BaseModel):
    type: str = "image"
    originalContentUrl: str
    previewImageUrl: Optional[str] = None

class StickerMessage(BaseModel):
    type: str = "sticker"
    packageId: str
    stickerId: str

class PushRequest(BaseModel):
    to: str
    messages: List[dict]
    disable_notification: bool = False

class BroadcastRequest(BaseModel):
    messages: List[dict]
    disable_notification: bool = False
    confirm: bool = False

# ============= API Endpoints =============

@app.get("/")
async def root():
    return {
        "service": "LINE Messaging API",
        "endpoints": {
            "push": "POST /push",
            "push_user": "POST /push/user",
            "push_group": "POST /push/group",
            "push_default_group": "POST /push/default-group",
            "broadcast": "POST /broadcast"
        }
    }

@app.post("/push")
async def push_message(req: PushRequest):
    """Push message to user or group"""
    success, code, res = push(req.to, req.messages, req.disable_notification)
    if not success:
        raise HTTPException(code, res.get("error", "Failed"))
    return {"success": True, "status": code, "response": res}

@app.post("/push/user")
async def push_to_user(
    user_id: str = Query(..., regex="^U"),
    message: str = Query(..., min_length=1),
    image: Optional[str] = Query(None),
    sticker_package: Optional[str] = Query(None),
    sticker_id: Optional[str] = Query(None),
    silent: bool = False
):
    """Push message to specific user (starts with U)"""
    messages = [{"type": "text", "text": message}]
    if image:
        messages.append({"type": "image", "originalContentUrl": image, "previewImageUrl": image})
    if sticker_package and sticker_id:
        messages.append({"type": "sticker", "packageId": sticker_package, "stickerId": sticker_id})
    
    success, code, res = push(user_id, messages, silent)
    if not success:
        raise HTTPException(code, res.get("error", "Failed"))
    return {"success": True, "to": user_id, "response": res}

@app.post("/push/group")
async def push_to_group(
    group_id: str = Query(..., regex="^C"),
    message: str = Query(..., min_length=1),
    image: Optional[str] = Query(None),
    sticker_package: Optional[str] = Query(None),
    sticker_id: Optional[str] = Query(None),
    silent: bool = False
):
    """Push message to specific group (starts with C)"""
    messages = [{"type": "text", "text": message}]
    if image:
        messages.append({"type": "image", "originalContentUrl": image, "previewImageUrl": image})
    if sticker_package and sticker_id:
        messages.append({"type": "sticker", "packageId": sticker_package, "stickerId": sticker_id})
    
    success, code, res = push(group_id, messages, silent)
    if not success:
        raise HTTPException(code, res.get("error", "Failed"))
    return {"success": True, "to": group_id, "response": res}

@app.post("/push/default-group")
async def push_to_default_group(
    message: str = Query(..., min_length=1),
    image: Optional[str] = Query(None),
    sticker_package: Optional[str] = Query(None),
    sticker_id: Optional[str] = Query(None),
    silent: bool = False
):
    """Push message to default group from .env"""
    if not config.group_id:
        raise HTTPException(400, "Default group ID not configured")
    
    messages = [{"type": "text", "text": message}]
    if image:
        messages.append({"type": "image", "originalContentUrl": image, "previewImageUrl": image})
    if sticker_package and sticker_id:
        messages.append({"type": "sticker", "packageId": sticker_package, "stickerId": sticker_id})
    
    success, code, res = push(config.group_id, messages, silent)
    if not success:
        raise HTTPException(code, res.get("error", "Failed"))
    return {"success": True, "to": config.group_id, "response": res}

@app.post("/broadcast")
async def broadcast_message(
    message: str = Query(..., min_length=1),
    image: Optional[str] = Query(None),
    sticker_package: Optional[str] = Query(None),
    sticker_id: Optional[str] = Query(None),
    silent: bool = False,
    confirm: bool = False
):
    """Broadcast to all followers (requires confirm=true)"""
    if not confirm:
        raise HTTPException(400, "Set confirm=true to confirm broadcast")
    
    messages = [{"type": "text", "text": message}]
    if image:
        messages.append({"type": "image", "originalContentUrl": image, "previewImageUrl": image})
    if sticker_package and sticker_id:
        messages.append({"type": "sticker", "packageId": sticker_package, "stickerId": sticker_id})
    
    success, code, res = broadcast(messages, silent)
    if not success:
        raise HTTPException(code, res.get("error", "Failed"))
    return {"success": True, "response": res}

@app.post("/broadcast/advanced")
async def broadcast_advanced(req: BroadcastRequest):
    """Advanced broadcast with multiple messages"""
    if not req.confirm:
        raise HTTPException(400, "Set confirm=true to confirm broadcast")
    
    success, code, res = broadcast(req.messages, req.disable_notification)
    if not success:
        raise HTTPException(code, res.get("error", "Failed"))
    return {"success": True, "response": res}

@app.get("/config")
async def get_config():
    """Show config info (debug)"""
    return {
        "token_configured": bool(config.line_access_token),
        "token_preview": f"{config.line_access_token[:10]}..." if config.line_access_token else None,
        "default_group_id": config.group_id,
        "default_group_configured": bool(config.group_id)
    }