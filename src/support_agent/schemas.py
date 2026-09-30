"""Typed public contracts for the support-agent workflow."""
from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    tweet_id: str
    similarity: float
    historical_customer_message: str
    historical_apple_reply: str


class AgentResult(BaseModel):
    intent: str
    intent_confidence: float
    risk_level: Literal["low", "medium", "high"]
    risk_signals: List[str]
    decision: Literal["auto_handle", "escalate"]
    decision_reason: str
    draft_reply: str
    evidence: Optional[Evidence]
    llm_used: bool = False
    llm_provider: str = "historical"
    latency_ms: float = 0


class AnalyzeRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
