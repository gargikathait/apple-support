"""Privacy-minimising in-memory request metrics and structured logs."""
from __future__ import annotations

from collections import Counter
import json
import logging
from threading import Lock


logger = logging.getLogger("support_agent")


class DecisionLogger:
    """Store aggregates only; customer message text is deliberately never logged."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._total = 0
        self._auto = 0
        self._confidence_total = 0.0
        self._latency_total = 0.0
        self._intents: Counter[str] = Counter()
        self._reasons: Counter[str] = Counter()

    def record(self, result: dict) -> None:
        event = {
            "event": "support_decision",
            "intent": result["intent"],
            "confidence": result["intent_confidence"],
            "risk_level": result["risk_level"],
            "retrieval_similarity": (result.get("evidence") or {}).get("similarity"),
            "decision": result["decision"],
            "latency_ms": result["latency_ms"],
            "llm_used": result["llm_used"],
            "llm_provider": result["llm_provider"],
            "escalation_reason": result["decision_reason"] if result["decision"] == "escalate" else None,
        }
        logger.info(json.dumps(event, sort_keys=True))
        with self._lock:
            self._total += 1
            self._auto += int(result["decision"] == "auto_handle")
            self._confidence_total += result["intent_confidence"]
            self._latency_total += result["latency_ms"]
            self._intents[result["intent"]] += 1
            if result["decision"] == "escalate":
                self._reasons[result["decision_reason"]] += 1

    def summary(self) -> dict:
        with self._lock:
            total = self._total
            return {
                "total_requests": total,
                "auto_handle_rate": round(self._auto / total, 3) if total else 0.0,
                "escalation_rate": round((total - self._auto) / total, 3) if total else 0.0,
                "average_confidence": round(self._confidence_total / total, 3) if total else 0.0,
                "average_latency_ms": round(self._latency_total / total, 1) if total else 0.0,
                "common_intents": self._intents.most_common(5),
                "common_escalation_reasons": self._reasons.most_common(5),
            }
