import argparse
import json
import os
import sys
from typing import Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError


# ──────────────────────────────────────────────
# Load .env file (no dependencies needed)
# ──────────────────────────────────────────────
def load_env(filepath=".env"):
    """Load key=value pairs from a .env file into os.environ."""
    if not os.path.exists(filepath):
        return
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            # Remove surrounding quotes if present
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            os.environ.setdefault(key, value)


load_env()

# ──────────────────────────────────────────────
# CONFIGURATION
#   Priority: --token flag > .env file > env var > script default
# ──────────────────────────────────────────────
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_CHANNEL_ACCESS_TOKEN_HERE")
DEFAULT_GROUP_ID = os.environ.get("LINE_GROUP_ID", "")

# ──────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────
BASE_URL = "https://api.line.me/v2/bot/message"
PUSH_URL = f"{BASE_URL}/push"
BROADCAST_URL = f"{BASE_URL}/broadcast"


def _send_request(url: str, payload: Dict, token: str) -> Dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=15) as response:
            status = response.status
            body = response.read().decode("utf-8")
            return {
                "success": True,
                "status": status,
                "body": json.loads(body) if body.strip() else {},
            }
    except HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
            parsed = json.loads(error_body) if error_body.strip() else {}
        except Exception:
            parsed = {"error": "Invalid error response"}
        return {
            "success": False,
            "status": e.code,
            "body": parsed,
        }


def build_text_message(text: str) -> Dict:
    return {"type": "text", "text": text}


def build_image_message(original_url: str, preview_url: Optional[str] = None) -> Dict:
    return {
        "type": "image",
        "originalContentUrl": original_url,
        "previewImageUrl": preview_url or original_url,
    }


def build_sticker_message(package_id: str, sticker_id: str) -> Dict:
    return {"type": "sticker", "packageId": package_id, "stickerId": sticker_id}


def push_message(user_id: str, messages: List[Dict], token: Optional[str] = None) -> Dict:
    token = token or os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        return {"success": False, "status": 0, "body": {"error": "No channel access token provided"}}
    if not isinstance(messages, list) or len(messages) == 0:
        return {"success": False, "status": 0, "body": {"error": "No messages to send"}}
    if len(messages) > 5:
        return {"success": False, "status": 0, "body": {"error": "Max 5 messages per request"}}

    payload = {"to": user_id, "messages": messages}
    return _send_request(PUSH_URL, payload, token)


def broadcast_message(messages: List[Dict], token: Optional[str] = None) -> Dict:
    token = token or os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        return {"success": False, "status": 0, "body": {"error": "No channel access token provided"}}
    if not isinstance(messages, list) or len(messages) == 0:
        return {"success": False, "status": 0, "body": {"error": "No messages to send"}}
    if len(messages) > 5:
        return {"success": False, "status": 0, "body": {"error": "Max 5 messages per request"}}

    payload = {"messages": messages}
    return _send_request(BROADCAST_URL, payload, token)
