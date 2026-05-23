# line.py
import json
from urllib.request import Request, urlopen
from config import config

BASE_URL = "https://api.line.me/v2/bot/message"

def send_request(url, payload):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.line_access_token}"
    }
    req = Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urlopen(req) as res:
            return True, res.status, json.loads(res.read().decode())
    except Exception as e:
        return False, 500, {"error": str(e)}

def push(recipient_id, messages, disable_notification=False):
    payload = {"to": recipient_id, "messages": messages}
    if disable_notification:
        payload["notificationDisabled"] = True
    return send_request(f"{BASE_URL}/push", payload)

def broadcast(messages, disable_notification=False):
    payload = {"messages": messages}
    if disable_notification:
        payload["notificationDisabled"] = True
    return send_request(f"{BASE_URL}/broadcast", payload)
