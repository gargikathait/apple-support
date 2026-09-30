"""Optional response generation. Routing always remains outside this module."""
from __future__ import annotations

import os
import json
import urllib.request
from typing import Dict, Optional, Tuple

FALLBACK_REPLY = "Unable to safely generate an automated response. Escalating to a human."


class ResponseGenerator:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None) -> None:
        self.provider = (provider or os.getenv("LLM_PROVIDER", "historical")).lower()
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")

    def generate(
        self,
        *,
        message: str,
        intent: str,
        confidence: float,
        evidence: Optional[Dict],
        decision: str,
        safety_reason: str,
        historical_reply: str,
    ) -> Tuple[str, bool, str]:
        if decision != "auto_handle":
            if self.provider == "openai":
                return FALLBACK_REPLY, False, "generation_failed"
            return historical_reply, False, "policy_template"

        if self.provider in {"historical", "mock"}:
            return historical_reply, self.provider == "mock", self.provider

        if self.provider != "openai" or not os.getenv("OPENAI_API_KEY"):
            return FALLBACK_REPLY, False, "generation_failed"

        prompt = {
            "customer_message": message,
            "predicted_intent": intent,
            "confidence": confidence,
            "historical_evidence": evidence,
            "decision": decision,
            "constraint": (
                "Write one concise public reply. Do not request secrets, "
                "promise outcomes, or override the decision."
            ),
            "safety_reason": safety_reason,
        }

        try:
            body = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Draft only a safe, concise support response "
                            "grounded in the provided precedent."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(prompt),
                    },
                ],
                "temperature": 0.2,
            }

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(body).encode(),
                headers={
                    "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                    "Content-Type": "application/json",
                },
            )

            with urllib.request.urlopen(req, timeout=20) as response:
                reply = json.loads(response.read())["choices"][0]["message"]["content"].strip()

            return reply, True, "openai"

        except Exception:
            # A generation outage must never make an unsafe response more likely.
            return FALLBACK_REPLY, False, "generation_failed"