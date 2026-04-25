import os
import uuid
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from typing import Optional
import json

from models import ClassifyRequest, ClassifyResponse, Ticket
from classifier import TicketClassifierAgent
from mock_data import SAMPLE_TICKETS

load_dotenv()

app = FastAPI(
    title="Smart Ticket Classifier API",
    description="Two-stage agentic pipeline: classify tickets + trigger tool-calling actions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# In-memory ticket store (demo purposes)
ticket_store: dict[str, dict] = {}

def get_agent(api_key: str, model: str = "llama-3.3-70b-versatile") -> TicketClassifierAgent:
    return TicketClassifierAgent(api_key=api_key, model=model)


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Smart Ticket Classifier API", "version": "1.0.0", "docs": "/docs"}


@app.post("/classify", response_model=ClassifyResponse)
async def classify_ticket(
    request: ClassifyRequest,
    x_openai_key: str = Header(..., description="Your Groq API key"),
    model: str = "llama-3.3-70b-versatile"
):
    """
    Main endpoint. Runs the full 2-stage agentic pipeline:
    1. Classify ticket (category, priority, sentiment, etc.)
    2. Action agent (auto-reply draft, escalation, tagging, SLA)
    """
    if len(request.message.strip()) < 10:
        raise HTTPException(status_code=400, detail="Message too short (min 10 chars)")

    try:
        agent = get_agent(x_openai_key, model)
        result = agent.classify(request)
        ticket_store[result.ticket.id] = result.ticket.model_dump()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tickets")
def get_tickets():
    """Return all classified tickets from this session."""
    return {"tickets": list(ticket_store.values()), "total": len(ticket_store)}


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    """Get a single ticket by ID."""
    if ticket_id not in ticket_store:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket_store[ticket_id]


@app.get("/samples")
def get_samples():
    """Return 10 pre-built sample messages for demo."""
    return {"samples": SAMPLE_TICKETS}


@app.get("/stats")
def get_stats():
    """Aggregated stats for the dashboard."""
    tickets = list(ticket_store.values())
    if not tickets:
        return {"total": 0, "by_priority": {}, "by_category": {}, "escalated": 0}

    by_priority = {}
    by_category = {}
    escalated = 0

    for t in tickets:
        clf = t.get("classification", {})
        if clf:
            p = clf.get("priority", "Unknown")
            c = clf.get("category", "Unknown")
            by_priority[p] = by_priority.get(p, 0) + 1
            by_category[c] = by_category.get(c, 0) + 1
            if clf.get("escalate"):
                escalated += 1

    return {
        "total": len(tickets),
        "by_priority": by_priority,
        "by_category": by_category,
        "escalated": escalated,
        "avg_confidence": round(
            sum(t["classification"]["confidence"] for t in tickets if t.get("classification")) / len(tickets), 1
        )
    }


@app.delete("/tickets")
def clear_tickets():
    """Clear all tickets (reset demo)."""
    ticket_store.clear()
    return {"message": "All tickets cleared"}
