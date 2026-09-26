from __future__ import annotations

from datetime import date, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()  # local dev only; on Vercel these come from project env vars

from .agent import run_agent  # noqa: E402  (after load_dotenv on purpose)
from .flights import search_flights  # noqa: E402

app = FastAPI(title="AMS Flex-Date Flight Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
def chat(req: ChatRequest):
    try:
        result = run_agent(req.message, [m.model_dump() for m in req.history])
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
