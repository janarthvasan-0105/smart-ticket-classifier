# 🎫 Smart Support Ticket Classifier

An **AI-powered, multi-stage agentic pipeline** that classifies customer support tickets and automatically takes intelligent actions using OpenAI's function calling capabilities.

## What Makes This Different

Most ticket classifiers are simple OpenAI wrappers. This project implements a **two-stage agentic pipeline**:

```
Ticket Input
    ↓
[Stage 1] Classifier Agent
    → category, priority, sentiment, confidence, keywords
    ↓
[Stage 2] Action Agent (OpenAI function calling)
    → Tool: auto_respond(draft_reply)        ← drafts customer reply
    → Tool: escalate_ticket(team, reason)    ← routes to human if needed
    → Tool: tag_ticket(tags[])               ← adds CRM tags
    → Tool: set_sla_deadline(hours)          ← sets resolution deadline
    ↓
[Stage 3] Result
    → Full structured ticket object
    → Displayed on React dashboard
```

## 🚀 Quick Start

### Option 1: Local Development

```bash
# 1. Install Python dependencies
cd backend
pip install -r requirements.txt

# 2. Set up environment variables
cp ../.env.example ../.env
# Edit .env and add your OpenAI API key

# 3. Start the backend server
uvicorn main:app --reload --port 8000

# 4. Open the frontend
# Open frontend/index.html in your browser
# Or serve it: npx serve ../frontend -p 3000
```

### Option 2: Docker (One Command)

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-your-key-here

# Start everything
docker-compose up --build
```

- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:3000 (Docker) or open `frontend/index.html` directly
- **API Docs:** http://localhost:8000/docs

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/classify` | Classify a ticket (full agentic pipeline) |
| `GET` | `/tickets` | List all classified tickets |
| `GET` | `/tickets/{id}` | Get a single ticket |
| `GET` | `/samples` | Get 10 sample tickets for demo |
| `GET` | `/stats` | Dashboard statistics |
| `DELETE` | `/tickets` | Clear all tickets |

### Example Request

```bash
curl -X POST http://localhost:8000/classify?model=gpt-4o-mini \
  -H "Content-Type: application/json" \
  -H "X-Openai-Key: sk-your-key" \
  -d '{"message": "I have been charged twice this month!", "ticket_id": "TKT-042"}'
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                         │
│         React SPA (CDN, no build step)              │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐      │
│  │  Stats   │  │ Classify  │  │   Result     │      │
│  │  Panel   │  │  Panel    │  │   Panel      │      │
│  └──────────┘  └───────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────┘
                     │ REST API (JSON)
┌────────────────────▼────────────────────────────────┐
│                   BACKEND (FastAPI)                 │
│  ┌────────────────────────────────────────────┐     │
│  │          TicketClassifierAgent             │     │
│  │  ┌─────────────┐    ┌──────────────────┐   │     │
│  │  │  Stage 1:   │    │   Stage 2:       │   │     │
│  │  │  Classify   │──▶│   Action Agent   │   │     │
│  │  │  (JSON)     │    │   (Tool Calling) │   │     │
│  │  └─────────────┘    └──────────────────┘   │     │
│  └────────────────────────────────────────────┘     │
│            │                    │                   │
│     ┌──────▼──────┐    ┌───────▼───────┐            │
│     │   Models    │    │    Tools      │            │
│     │  (Pydantic) │    │  (4 functions)│            │
│     └─────────────┘    └──────────────┘             │
└─────────────────────────────────────────────────────┘
                     │
              ┌──────▼──────┐
              │   OpenAI    │
              │  GPT-4o-mini│
              └─────────────┘
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| AI/ML | OpenAI GPT-4o-mini, Function Calling |
| Frontend | React 18 (CDN), Vanilla CSS |
| Deployment | Docker, Docker Compose, Nginx |

## 📋 Features

- **Two-stage AI pipeline** — classification + autonomous action execution
- **4 parallel tool calls** — auto-respond, escalate, tag, set SLA
- **10 sample tickets** — instant demo without typing
- **Real-time stats** — priority/category breakdown, escalation count
- **5-tab result view** — Overview, Agent Actions, Draft Reply, Raw JSON, Code
- **Dark mode** — toggle between light and dark themes
- **Copy buttons** — one-click copy for draft replies and code snippets
- **Priority color coding** — visual urgency indicators
- **Escalation alerts** — prominent banner for escalated tickets
- **Responsive design** — works on desktop and tablet

---

*Built as an AI agent interview task demonstration — showcasing OpenAI function calling, agentic pipelines, and full-stack development.*
