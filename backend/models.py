from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class Priority(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class Category(str, Enum):
    BILLING = "Billing"
    TECHNICAL = "Technical"
    ACCOUNT = "Account"
    SHIPPING = "Shipping"
    REFUND = "Refund"
    FEATURE_REQUEST = "Feature Request"
    GENERAL = "General"

class Sentiment(str, Enum):
    ANGRY = "Angry"
    FRUSTRATED = "Frustrated"
    NEUTRAL = "Neutral"
    SATISFIED = "Satisfied"
    POSITIVE = "Positive"

class ClassificationResult(BaseModel):
    category: Category
    priority: Priority
    sentiment: Sentiment
    confidence: int = Field(ge=0, le=100)
    summary: str
    keywords: list[str]
    escalate: bool
    estimated_resolution_hours: int

class AgentAction(BaseModel):
    action_type: str           # "auto_respond" | "escalate" | "tag" | "set_sla"
    payload: dict
    reasoning: str

class Ticket(BaseModel):
    id: str
    message: str
    classification: Optional[ClassificationResult] = None
    agent_actions: list[AgentAction] = []
    draft_reply: Optional[str] = None
    assigned_team: Optional[str] = None
    tags: list[str] = []
    sla_deadline_hours: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"    # pending | classified | resolved

class ClassifyRequest(BaseModel):
    message: str
    ticket_id: Optional[str] = None

class ClassifyResponse(BaseModel):
    ticket: Ticket
    tokens_used: int
    model: str
    processing_time_ms: int
