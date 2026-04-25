AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "auto_respond",
            "description": "Draft a professional, empathetic reply to the customer. Call this for all tickets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "draft_reply": {
                        "type": "string",
                        "description": "The full drafted reply to send to the customer. Be empathetic, specific, and solution-focused."
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["apologetic", "informative", "empathetic", "positive"],
                        "description": "The tone of the reply based on customer sentiment."
                    }
                },
                "required": ["draft_reply", "tone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_ticket",
            "description": "Escalate the ticket to a human support team. Call this when escalate=true or priority is Critical/High.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team": {
                        "type": "string",
                        "enum": ["billing", "technical", "logistics", "account_security", "management"],
                        "description": "The team to escalate to based on the ticket category."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for escalation."
                    },
                    "urgency_note": {
                        "type": "string",
                        "description": "Special notes for the receiving agent."
                    }
                },
                "required": ["team", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tag_ticket",
            "description": "Add CRM/helpdesk tags to the ticket for filtering and reporting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tags. Examples: ['payment-failed', 'vip-customer', 'repeat-complaint', 'first-contact']"
                    }
                },
                "required": ["tags"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_sla_deadline",
            "description": "Set the SLA resolution deadline in hours based on priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "integer",
                        "description": "Hours to resolve. Critical=1, High=4, Medium=24, Low=72"
                    },
                    "justification": {
                        "type": "string",
                        "description": "Why this SLA was chosen."
                    }
                },
                "required": ["hours"]
            }
        }
    }
]
