# line.py
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from config import config

BASE_URL = "https://api.line.me/v2/bot/message"

def send_line_request(url, payload):
    """Send HTTP request to LINE API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.line_access_token}",
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urlopen(req) as response:
            status = response.status
            body = response.read().decode("utf-8")
            return True, status, json.loads(body) if body.strip() else {}
    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        return False, e.code, json.loads(error_body) if error_body.strip() else {}

def push_message(recipient_id, messages, disable_notification=False):
    """
    Send push message to specific user or group
    
    Args:
        recipient_id: User ID (starts with U) or Group ID (starts with C)
        messages: List of message objects
        disable_notification: Whether to disable push notifications
    
    Returns:
        tuple: (success, status_code, response_body)
    """
    url = f"{BASE_URL}/push"
    payload = {
        "to": recipient_id,
        "messages": messages,
    }
    if disable_notification:
        payload["notificationDisabled"] = True
    
    return send_line_request(url, payload)

def broadcast_message(messages, disable_notification=False):
    """
    Send broadcast message to all followers
    
    Args:
        messages: List of message objects
        disable_notification: Whether to disable push notifications
    
    Returns:
        tuple: (success, status_code, response_body)
    """
    url = f"{BASE_URL}/broadcast"
    payload = {"messages": messages}
    if disable_notification:
        payload["notificationDisabled"] = True
    
    return send_line_request(url, payload)

def multicast_message(recipient_ids, messages):
    """
    Send message to multiple users (max 500 per request)
    
    Args:
        recipient_ids: List of user IDs (max 500)
        messages: List of message objects
    
    Returns:
        tuple: (success, status_code, response_body)
    """
    url = f"{BASE_URL}/multicast"
    payload = {
        "to": recipient_ids[:500],  # LINE API limit: 500 recipients
        "messages": messages
    }
    return send_line_request(url, payload)

def build_text_message(text):
    """Build a text message object"""
    return {"type": "text", "text": text}

def build_image_message(original_url, preview_url=None):
    """Build an image message object"""
    return {
        "type": "image",
        "originalContentUrl": original_url,
        "previewImageUrl": preview_url or original_url,
    }

def build_sticker_message(package_id, sticker_id):
    """Build a sticker message object"""
    return {
        "type": "sticker",
        "packageId": package_id,
        "stickerId": sticker_id,
    }

# Quick send functions
def send_text_to_group(group_id, text, disable_notification=False):
    """Quick helper to send text to a group"""
    messages = [build_text_message(text)]
    return push_message(group_id, messages, disable_notification)

def send_text_to_user(user_id, text, disable_notification=False):
    """Quick helper to send text to a user"""
    messages = [build_text_message(text)]
    return push_message(user_id, messages, disable_notification)

def send_text_to_default_group(text, disable_notification=False):
    """Send text to the default group from config"""
    if not config.group_id:
        return False, 400, {"message": "Default group ID not configured"}
    return send_text_to_group(config.group_id, text, disable_notification)