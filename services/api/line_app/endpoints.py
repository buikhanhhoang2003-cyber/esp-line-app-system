# line_endpoint.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from line import (
    push_message, 
    broadcast_message, 
    multicast_message,
    build_text_message,
    build_image_message,
    build_sticker_message,
    send_text_to_group,
    send_text_to_user,
    send_text_to_default_group
)
from config import config

app = FastAPI(
    title="LINE Messaging API",
    description="API for sending messages to LINE groups and users",
    version="1.0.0"
)

# ============= Helper Functions =============

def validate_messages(messages):
    """Simple validation for messages"""
    if not messages:
        return False, "No messages provided"
    if len(messages) > 5:
        return False, "Maximum 5 messages per request"
    return True, None

# ============= Simple Text Endpoints =============

@app.post("/api/send/text")
async def send_text(recipient_id: str, text: str, recipient_type: str = "group"):
    """
    Simple endpoint to send text message
    
    Args:
        recipient_id: User ID or Group ID
        text: Message text
        recipient_type: "user" or "group"
    """
    if not config.line_access_token:
        raise HTTPException(status_code=500, detail="LINE token not configured")
    
    if recipient_type == "group":
        success, status, response = send_text_to_group(recipient_id, text)
    elif recipient_type == "user":
        success, status, response = send_text_to_user(recipient_id, text)
    else:
        raise HTTPException(status_code=400, detail="recipient_type must be 'user' or 'group'")
    
    if success:
        return {"success": True, "message": "Text sent successfully", "details": response}
    else:
        raise HTTPException(status_code=status, detail=response.get("message", "Unknown error"))

@app.post("/api/group/default")
async def send_to_default_group(text: str, disable_notification: bool = False):
    """Send text to the default group from config"""
    if not config.group_id:
        raise HTTPException(status_code=400, detail="Default group ID not configured in environment")
    
    success, status, response = send_text_to_default_group(text, disable_notification)
    
    if success:
        return {
            "success": True, 
            "message": "Message sent to default group",
            "group_id": config.group_id,
            "details": response
        }
    else:
        raise HTTPException(status_code=status, detail=response.get("message", "Unknown error"))

@app.post("/api/group/{group_id}")
async def send_to_group(group_id: str, text: str, disable_notification: bool = False):
    """Send text to a specific group"""
    success, status, response = send_text_to_group(group_id, text, disable_notification)
    
    if success:
        return {"success": True, "message": f"Message sent to group {group_id}", "details": response}
    else:
        raise HTTPException(status_code=status, detail=response.get("message", "Unknown error"))

@app.post("/api/user/{user_id}")
async def send_to_user(user_id: str, text: str, disable_notification: bool = False):
    """Send text to a specific user"""
    success, status, response = send_text_to_user(user_id, text, disable_notification)
    
    if success:
        return {"success": True, "message": f"Message sent to user {user_id}", "details": response}
    else:
        raise HTTPException(status_code=status, detail=response.get("message", "Unknown error"))

# ============= Advanced Endpoints (Multiple Messages) =============

@app.post("/api/send/advanced")
async def send_advanced(request: dict):
    """
    Send advanced message with multiple content types
    
    Expected JSON format:
    {
        "recipient_id": "Cxxx or Uxxx",
        "recipient_type": "group",
        "messages": [
            {"type": "text", "text": "Hello"},
            {"type": "image", "originalContentUrl": "https://...", "previewImageUrl": "https://..."},
            {"type": "sticker", "packageId": "446", "stickerId": "1988"}
        ],
        "disable_notification": false
    }
    """
    # Extract parameters
    recipient_id = request.get("recipient_id")
    recipient_type = request.get("recipient_type", "group")
    messages = request.get("messages", [])
    disable_notification = request.get("disable_notification", False)
    
    # Validation
    if not recipient_id:
        raise HTTPException(status_code=400, detail="recipient_id is required")
    
    if recipient_type not in ["user", "group"]:
        raise HTTPException(status_code=400, detail="recipient_type must be 'user' or 'group'")
    
    valid, error = validate_messages(messages)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Send message
    success, status, response = push_message(recipient_id, messages, disable_notification)
    
    if success:
        return {
            "success": True,
            "message": f"Advanced message sent to {recipient_type} {recipient_id}",
            "details": response
        }
    else:
        raise HTTPException(status_code=status, detail=response.get("message", "Unknown error"))

@app.post("/api/send/with-image")
async def send_with_image(group_id: str, text: str, image_url: str, preview_url: str = None):
    """Send text + image to a group"""
    messages = [
        build_text_message(text),
        build_image_message(image_url, preview_url)
    ]
    
    success, status, response = push_message(group_id, messages)
    
    if success:
        return {"success": True, "message": "Text and image sent", "details": response}
    else:
        raise HTTPException(status_code=status, detail=response.get("message", "Unknown error"))

@app.post("/api/send/with-sticker")
async def send_with_sticker(group_id: str, text: str, package_id: str, sticker_id: str):
    """Send text + sticker to a group"""
    messages = [
        build_text_message(text),
        build_sticker_message(package_id, sticker_id)
    ]
    
    success, status, response = push_message(group_id, messages)
    
    if success:
        return {"success": True, "message": "Text and sticker sent", "details": response}
    else:
        raise HTTPException(status_code=status, detail=response.get("message", "Unknown error"))

# ============= Broadcast Endpoints =============

@app.post("/api/broadcast")
async def send_broadcast(text: str, confirm: bool = False, disable_notification: bool = False):
    """Broadcast text to all followers"""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Please set confirm=true to confirm broadcast to all followers"
        )
    
    messages = [build_text_message(text)]
    success, status, response = broadcast_message(messages, disable_notification)
    
    if success:
        return {"success": True, "message": "Broadcast sent to all followers", "details": response}
    else:
        raise HTTPException(status_code=status, detail=response.get("message", "Unknown error"))

@app.post("/api/broadcast/advanced")
async def send_broadcast_advanced(request: dict):
    """
    Advanced broadcast with multiple message types
    
    Expected JSON format:
    {
        "messages": [
            {"type": "text", "text": "Hello everyone!"},
            {"type": "image", "originalContentUrl": "https://..."}
        ],
        "confirm": true,
        "disable_notification": false
    }
    """
    messages = request.get("messages", [])
    confirm = request.get("confirm", False)
    disable_notification = request.get("disable_notification", False)
    
    if not confirm:
        raise HTTPException(status_code=400, detail="Please set confirm=true to confirm broadcast")
    
    valid, error = validate_messages(messages)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    success, status, response = broadcast_message(messages, disable_notification)
    
    if success:
        return {"success": True, "message": "Advanced broadcast sent", "details": response}
    else:
        raise HTTPException(status_code=status, detail=response.get("message", "Unknown error"))

# ============= Multicast Endpoint =============

@app.post("/api/multicast")
async def send_multicast(user_ids: list, text: str):
    """
    Send same message to multiple users
    
    Args:
        user_ids: List of user IDs (max 500)
        text: Message text
    """
    if len(user_ids) > 500:
        raise HTTPException(status_code=400, detail="Maximum 500 recipients per multicast request")
    
    messages = [build_text_message(text)]
    success, status, response = multicast_message(user_ids, messages)
    
    if success:
        return {
            "success": True, 
            "message": f"Message sent to {len(user_ids)} users",
            "details": response
        }
    else:
        raise HTTPException(status_code=status, detail=response.get("message", "Unknown error"))

# ============= Async/Background Endpoint =============

async def send_async_message(recipient_id, text):
    """Background task helper"""
    from line import send_text_to_group
    return send_text_to_group(recipient_id, text)

@app.post("/api/send/async/{group_id}")
async def send_async(group_id: str, text: str, background_tasks: BackgroundTasks):
    """Send message asynchronously (non-blocking)"""
    background_tasks.add_task(send_async_message, group_id, text)
    return {
        "status": "accepted",
        "message": "Message queued for sending",
        "group_id": group_id
    }

# ============= Error Handler =============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )