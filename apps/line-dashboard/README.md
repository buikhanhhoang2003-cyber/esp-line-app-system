Line Dashboard
===============

Quick start:

1. Copy the environment template:

```bash
cp .env.example .env
# Edit .env and set LINE_NOTIFY_TOKEN
```

2. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Run the app:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Open the dashboard at `http://localhost:8000/`

Notes:
- The UI calls `/api/notify` which requires a valid `LINE_NOTIFY_TOKEN` in `.env`.
- Use `curl` or Postman to test the API endpoint directly:

```bash
curl -X POST http://localhost:8000/api/notify -H 'Content-Type: application/json' -d '{"message":"hello"}'
```

Additional LINE Messaging API endpoints (server-side)

- `POST /api/line/push` — Send a push message to a specific user.
	- Body JSON: `{"user_id":"Uxxxx","message":"Hello","image":"https://...","sticker":["1","1"],"token":"OPTIONAL_OVERRIDE"}`

- `POST /api/line/broadcast` — Broadcast a message to all followers.
	- Body JSON: `{"message":"Announcement","image":"https://...","sticker":["1","1"],"token":"OPTIONAL_OVERRIDE"}`

Note: These endpoints use the LINE Messaging API and require a `LINE_CHANNEL_ACCESS_TOKEN` to be set (in `.env` or provided in the request body as `token`).
