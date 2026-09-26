from __future__ import annotations

import time
from collections import defaultdict, deque
from datetime import date, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()  # local dev only; on Vercel these come from project env vars

from .agent import run_agent  # noqa: E402  (after load_dotenv on purpose)
from .flights import search_flights  # noqa: E402
from .guardrails import MAX_MESSAGE_LEN  # noqa: E402

# Only this API surface exists. No routes for code execution, web search, file
# access, or anything else are defined anywhere in this app.
app = FastAPI(
    title="AMS Flex-Date Flight Agent",
    docs_url=None,      # no Swagger UI in production
    redoc_url=None,      # no ReDoc
    openapi_url=None,    # no schema introspection endpoint
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Best-effort per-instance rate limit (serverless instances don't share
# memory, so this bounds abuse per warm instance, not globally).
_RATE_LIMIT = 20  # requests
_RATE_WINDOW_S = 300  # per 5 minutes
_hits: dict[str, deque] = defaultdict(deque)


def _rate_limited(client_id: str) -> bool:
    now = time.time()
    window = _hits[client_id]
    while window and now - window[0] > _RATE_WINDOW_S:
        window.popleft()
    if len(window) >= _RATE_LIMIT:
        return True
    window.append(now)
    return False


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/chat")
def chat(req: ChatRequest, request: Request):
    client_id = request.client.host if request.client else "unknown"
    if _rate_limited(client_id):
        raise HTTPException(status_code=429, detail="Too many requests, slow down.")

    # Sanitize client-supplied history: only user/assistant roles, capped
    # length and turn count, so a crafted payload can't smuggle a fake
    # system role or an oversized prompt into the model call.
    safe_history = [
        {"role": m.role, "content": m.content[:MAX_MESSAGE_LEN]}
        for m in req.history
        if m.role in ("user", "assistant")
    ][-6:]

    try:
        result = run_agent(req.message, safe_history)
        return result
    except KeyError as exc:
        raise HTTPException(status_code=500, detail=f"Missing env var: {exc}") from exc


@app.get("/api/heatmap")
def heatmap(destination: str, start_date: str | None = None, end_date: str | None = None):
    """Direct, non-LLM path: used when the UI just wants prices for a picked destination."""
    if not start_date:
        start_date = (date.today() + timedelta(days=14)).isoformat()
    if not end_date:
        end_date = (date.fromisoformat(start_date) + timedelta(days=21)).isoformat()
    return search_flights(destination=destination, start_date=start_date, end_date=end_date)
