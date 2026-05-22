"""
LINE Messaging API - Push, Group & Broadcast Message Sender
=============================================================
Supports:
  - Push message  : Send to a specific user by user ID
  - Group message : Send to a group chat by group ID
  - Broadcast     : Send to all followers of your LINE Official Account

Setup:
  1. Go to https://developers.line.biz/console/
  2. Select your Messaging API channel
  3. Copy your "Channel Access Token" (long-lived)
  4. For push messages, you need the target user's User ID (starts with "U")
  5. For group messages, you need the Group ID (starts with "C")
     - Get it via webhook.py or from LINE webhook events

Usage:
  # Push message to a specific user
  python line_messenger.py --user U4af498... -m "Hello!"

  # Send to a group (using group ID)
  python line_messenger.py --group Cd56e245... -m "Hello group!"

  # Send to default group (from .env LINE_GROUP_ID)
  python line_messenger.py --group -m "Hello group!"

  # Broadcast to all followers
  python line_messenger.py --broadcast -m "Announcement!"

  # Override token via CLI
  python line_messenger.py --group Cd56e245... -m "Hello!" --token YOUR_TOKEN

  # Use environment variable for token
  export LINE_CHANNEL_ACCESS_TOKEN="your_token_here"
  export LINE_GROUP_ID="your_group_id_here"
  python line_messenger.py --broadcast -m "Hi everyone!"
"""

import argparse
import json
import os
import sys
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


def _send_request(url: str, payload: dict) -> dict:
    """Send an HTTP POST request to the LINE API."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")

    try:
        with urlopen(req) as response:
            status = response.status
            body = response.read().decode("utf-8")
            return {
                "success": True,
                "status": status,
                "body": json.loads(body) if body.strip() else {},
            }
    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        return {
            "success": False,
            "status": e.code,
            "body": json.loads(error_body) if error_body.strip() else {},
        }


def build_text_message(text: str) -> dict:
    """Build a simple text message object."""
    return {"type": "text", "text": text}


def build_image_message(original_url: str, preview_url: str = None) -> dict:
    """Build an image message object."""
    return {
        "type": "image",
        "originalContentUrl": original_url,
        "previewImageUrl": preview_url or original_url,
    }


def build_sticker_message(package_id: str, sticker_id: str) -> dict:
    """Build a sticker message object."""
    return {
        "type": "sticker",
        "packageId": package_id,
        "stickerId": sticker_id,
    }


def build_flex_message(alt_text: str, contents: dict) -> dict:
    """Build a Flex Message object (advanced layout)."""
    return {
        "type": "flex",
        "altText": alt_text,
        "contents": contents,
    }


# ──────────────────────────────────────────────
# PUSH MESSAGE - Send to a specific user
# ──────────────────────────────────────────────
def push_message(user_id: str, messages: list) -> dict:
    """
    Send a push message to a specific user.

    Args:
        user_id:  The target user's LINE user ID (starts with 'U')
        messages: A list of message objects (max 5 per request)

    Returns:
        API response dict with 'success', 'status', and 'body' keys
    """
    if len(messages) > 5:
        return {"success": False, "status": 0, "body": {"error": "Max 5 messages per request"}}

    payload = {
        "to": user_id,
        "messages": messages,
    }
    return _send_request(PUSH_URL, payload)


# ──────────────────────────────────────────────
# BROADCAST MESSAGE - Send to all followers
# ──────────────────────────────────────────────
def broadcast_message(messages: list) -> dict:
    """
    Send a broadcast message to ALL followers of your LINE Official Account.

    Args:
        messages: A list of message objects (max 5 per request)

    Returns:
        API response dict with 'success', 'status', and 'body' keys
    """
    if len(messages) > 5:
        return {"success": False, "status": 0, "body": {"error": "Max 5 messages per request"}}

    payload = {
        "messages": messages,
    }
    return _send_request(BROADCAST_URL, payload)


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Send messages via LINE Messaging API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user U4af498062... -m "Hello!"
  %(prog)s --group Cd56e2456f... -m "Hello group!"
  %(prog)s --group -m "Hello!"                        (uses LINE_GROUP_ID from .env)
  %(prog)s --broadcast -m "News for everyone!"
  %(prog)s --user U4af498062... -m "With image" --image https://example.com/photo.jpg
  %(prog)s --broadcast -m "Hi!" --token YOUR_TOKEN
        """,
    )

    # Mode: --user, --group, or --broadcast (mutually exclusive, required)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--user",
        metavar="USER_ID",
        help="Send a push message to a specific user ID (starts with 'U')",
    )
    mode.add_argument(
        "--group",
        nargs="?",
        const="__DEFAULT__",
        metavar="GROUP_ID",
        help="Send a message to a group chat (starts with 'C'). "
             "If no ID given, uses LINE_GROUP_ID from .env",
    )
    mode.add_argument(
        "--broadcast",
        action="store_true",
        help="Broadcast message to all followers",
    )

    # Message content
    parser.add_argument(
        "-m", "--message",
        required=True,
        help="Text message to send",
    )
    parser.add_argument(
        "--image",
        metavar="URL",
        help="Attach an image by URL (sent as a separate message)",
    )
    parser.add_argument(
        "--sticker",
        nargs=2,
        metavar=("PACKAGE_ID", "STICKER_ID"),
        help="Attach a sticker (sent as a separate message)",
    )

    # Auth
    parser.add_argument(
        "--token",
        help="Channel access token (overrides env var and script default)",
    )

    # Flags
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Disable push notification sound on the user's device",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt for broadcast",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug info (token preview, request details)",
    )

    args = parser.parse_args()

    # Resolve token
    global CHANNEL_ACCESS_TOKEN
    if args.token:
        CHANNEL_ACCESS_TOKEN = args.token

    if CHANNEL_ACCESS_TOKEN == "YOUR_CHANNEL_ACCESS_TOKEN_HERE":
        print("❌ No channel access token provided.", file=sys.stderr)
        print("   Use --token, set LINE_CHANNEL_ACCESS_TOKEN env var,", file=sys.stderr)
        print("   or create a .env file with LINE_CHANNEL_ACCESS_TOKEN=your_token", file=sys.stderr)
        sys.exit(1)

    if args.debug:
        token = CHANNEL_ACCESS_TOKEN
        print(f"🔍 Token length : {len(token)}")
        print(f"🔍 Token start  : {token[:20]}...")
        print(f"🔍 Token end    : ...{token[-20:]}")
        print(f"🔍 Token source : {'--token flag' if args.token else '.env / env var'}")
        print()

    # Build messages list (max 5)
    messages = [build_text_message(args.message)]

    if args.image:
        messages.append(build_image_message(args.image))

    if args.sticker:
        messages.append(build_sticker_message(args.sticker[0], args.sticker[1]))

    # Send
    if args.user:
        print(f"📤 Sending push message to {args.user[:10]}...")
        result = push_message(args.user, messages)
    elif args.group is not None:
        # Resolve group ID
        group_id = args.group
        if group_id == "__DEFAULT__":
            group_id = DEFAULT_GROUP_ID
        if not group_id:
            print("❌ No group ID provided.", file=sys.stderr)
            print("   Use --group GROUP_ID or set LINE_GROUP_ID in .env", file=sys.stderr)
            sys.exit(1)
        print(f"📤 Sending message to group {group_id[:10]}...")
        result = push_message(group_id, messages)
    else:
        if not args.yes:
            confirm = input("⚠️  This will send to ALL followers. Continue? [y/N]: ").strip().lower()
            if confirm != "y":
                print("Cancelled.")
                sys.exit(0)
        print("📤 Broadcasting message to all followers...")
        result = broadcast_message(messages)

    # Output
    if result["success"]:
        print(f"✅ Message sent successfully! (HTTP {result['status']})")
    else:
        print(f"❌ Failed to send message (HTTP {result['status']})", file=sys.stderr)
        print(f"   Error: {json.dumps(result['body'], indent=2)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()