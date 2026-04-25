import json
import re
import time
import uuid
from openai import OpenAI
from models import (
    Ticket, ClassificationResult, AgentAction,
    ClassifyRequest, ClassifyResponse,
    Priority, Category, Sentiment
)
from tools import AGENT_TOOLS

# ─── SYSTEM PROMPTS ──────────────────────────────────────────────────────────

CLASSIFIER_SYSTEM_PROMPT = """You are an expert customer support ticket classifier.
Analyze the given support message and respond ONLY with a valid JSON object (no markdown, no extra text).

Return this exact JSON structure:
{
  "category": "<Billing|Technical|Account|Shipping|Refund|Feature Request|General>",
  "priority": "<Critical|High|Medium|Low>",
  "sentiment": "<Angry|Frustrated|Neutral|Satisfied|Positive>",
  "confidence": <integer 0-100>,
  "summary": "<1-2 sentence neutral summary of the issue>",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "escalate": <true|false>,
  "estimated_resolution_hours": <integer: 1 for Critical, 4 for High, 24 for Medium, 72 for Low>
}

Priority rules:
- Critical: service outage, data loss, financial fraud, legal threat, repeated billing errors
- High: cannot access account, urgent business impact, major bug affecting workflow
- Medium: billing question, slow performance, missing feature, moderate issue
- Low: general inquiry, feature request, compliment, non-urgent question"""

ACTION_AGENT_SYSTEM_PROMPT = """You are a senior customer support operations agent.
You have just received a classified support ticket. Your job is to call the available tools
to take the right actions. You MUST call all relevant tools:

1. ALWAYS call auto_respond — draft a helpful, empathetic customer reply.
2. Call escalate_ticket if priority is Critical or High, OR if escalate=true.
3. ALWAYS call tag_ticket with 2-4 relevant CRM tags.
4. ALWAYS call set_sla_deadline based on priority (Critical=1h, High=4h, Medium=24h, Low=72h).

Be decisive. Call all tools in one response using parallel tool calls."""

# ─── CLASSIFIER AGENT ────────────────────────────────────────────────────────

class TicketClassifierAgent:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = model

    def classify(self, request: ClassifyRequest) -> ClassifyResponse:
        start = time.time()
        ticket_id = request.ticket_id or str(uuid.uuid4())[:8]
        total_tokens = 0

        # ── STAGE 1: Classification ──────────────────────────────────────────
        stage1 = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Classify this support ticket:\n\n\"{request.message}\""}
            ],
            temperature=0.1,
            max_tokens=400
        )
        total_tokens += stage1.usage.total_tokens if stage1.usage else 0

        # Robustly extract JSON from response (may contain markdown fences)
        raw_text = stage1.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            raw_classification = json.loads(json_match.group())
        else:
            raw_classification = json.loads(raw_text)

        classification = ClassificationResult(
            category=raw_classification["category"],
            priority=raw_classification["priority"],
            sentiment=raw_classification["sentiment"],
            confidence=raw_classification["confidence"],
            summary=raw_classification["summary"],
            keywords=raw_classification["keywords"],
            escalate=raw_classification["escalate"],
            estimated_resolution_hours=raw_classification["estimated_resolution_hours"]
        )

        # ── STAGE 2: Action Agent (Tool Calling) ─────────────────────────────
        action_context = f"""Ticket classified:
- Message: "{request.message}"
- Category: {classification.category}
- Priority: {classification.priority}
- Sentiment: {classification.sentiment}
- Summary: {classification.summary}
- Should escalate: {classification.escalate}
- Keywords: {', '.join(classification.keywords)}

Now take all required actions using the available tools."""

        stage2 = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": ACTION_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": action_context}
            ],
            tools=AGENT_TOOLS,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=800
        )
        total_tokens += stage2.usage.total_tokens if stage2.usage else 0

        # ── Parse Tool Call Results ───────────────────────────────────────────
        agent_actions = []
        draft_reply = None
        assigned_team = None
        tags = []
        sla_hours = None

        tool_calls = stage2.choices[0].message.tool_calls or []
        for call in tool_calls:
            args = json.loads(call.function.arguments)
            fn = call.function.name

            if fn == "auto_respond":
                draft_reply = args.get("draft_reply")
                agent_actions.append(AgentAction(
                    action_type="auto_respond",
                    payload=args,
                    reasoning=f"Drafted {args.get('tone')} reply for {classification.sentiment.lower()} customer"
                ))

            elif fn == "escalate_ticket":
                assigned_team = args.get("team")
                agent_actions.append(AgentAction(
                    action_type="escalate",
                    payload=args,
                    reasoning=args.get("reason", "")
                ))

            elif fn == "tag_ticket":
                tags = args.get("tags", [])
                agent_actions.append(AgentAction(
                    action_type="tag",
                    payload=args,
                    reasoning=f"Tagged with {len(tags)} CRM labels"
                ))

            elif fn == "set_sla_deadline":
                sla_hours = args.get("hours")
                agent_actions.append(AgentAction(
                    action_type="set_sla",
                    payload=args,
                    reasoning=args.get("justification", "")
                ))

        # ── Build Final Ticket Object ─────────────────────────────────────────
        ticket = Ticket(
            id=ticket_id,
            message=request.message,
            classification=classification,
            agent_actions=agent_actions,
            draft_reply=draft_reply,
            assigned_team=assigned_team,
            tags=tags,
            sla_deadline_hours=sla_hours,
            status="classified"
        )

        elapsed_ms = int((time.time() - start) * 1000)

        return ClassifyResponse(
            ticket=ticket,
            tokens_used=total_tokens,
            model=self.model,
            processing_time_ms=elapsed_ms
        )
