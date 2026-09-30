"""Modular, conservative support-agent orchestration."""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .generation import ResponseGenerator
from .model import load
from .observability import DecisionLogger
from .schemas import AgentResult, Evidence
from .taxonomy import AUTO_INTENTS, HIGH_RISK_INTENTS, HIGH_RISK_TERMS

ESCALATION_REPLY = "Thanks for letting us know. A support specialist should review the details and help with the next best step. Please don’t post personal information publicly."
SENSITIVE_REPLY = "Thanks for reaching out. For your security and privacy, a support specialist should help with this directly. Please use Apple Support rather than sharing personal or account details here."


def redact_customer_handle(reply: str) -> str:
    return re.sub(r"^@\S+\s*", "", reply).strip()


class IntentClassifier:
    def __init__(self, classifier) -> None:
        self.classifier = classifier

    def predict(self, text: str) -> Tuple[str, float]:
        probabilities = self.classifier.predict_proba([text])[0]
        index = int(np.argmax(probabilities))
        return str(self.classifier.classes_[index]), float(probabilities[index])


class RiskDetector:
    def detect(self, text: str, intent: str) -> Tuple[str, List[str]]:
        signals = sorted(term for term in HIGH_RISK_TERMS if term in text.lower())
        if signals or intent in HIGH_RISK_INTENTS:
            return "high", signals
        if intent in {"battery_drain", "update_or_performance", "app_or_device_functionality"}:
            return "medium", signals
        return "low", signals


class EvidenceRetriever:
    def __init__(self, vectorizer, train_texts: List[str], train_intents: List[str], train_replies: List[str], train_ids: List[str]) -> None:
        self.vectorizer, self.train_texts, self.train_intents = vectorizer, train_texts, train_intents
        self.train_replies, self.train_ids = train_replies, train_ids
        self.train_matrix = vectorizer.transform(train_texts)

    def retrieve(self, text: str, intent: str) -> Optional[Evidence]:
        if not self.train_texts:
            return None
        scores = cosine_similarity(self.vectorizer.transform([text]), self.train_matrix).ravel()
        candidates = [i for i, label in enumerate(self.train_intents) if label == intent]
        idx = max(candidates, key=lambda i: scores[i]) if candidates else int(np.argmax(scores))
        return Evidence(tweet_id=str(self.train_ids[idx]), similarity=round(float(scores[idx]), 3),
                        historical_customer_message=self.train_texts[idx], historical_apple_reply=self.train_replies[idx])


class PolicyEngine:
    def __init__(self, confidence_threshold: float = 0.80, evidence_threshold: float = 0.34) -> None:
        self.confidence_threshold, self.evidence_threshold = confidence_threshold, evidence_threshold

    def decide(self, intent: str, confidence: float, risk_signals: List[str], evidence: Optional[Evidence]) -> Tuple[str, str, str]:
        if risk_signals:
            return "escalate", "Contains a sensitive account, security, payment, or safety signal: " + ", ".join(risk_signals) + ".", SENSITIVE_REPLY
        if intent in HIGH_RISK_INTENTS:
            return "escalate", "This intent requires identity, security, repair, or device-specific human review.", SENSITIVE_REPLY if intent != "repair_or_hardware" else ESCALATION_REPLY
        if intent not in AUTO_INTENTS:
            return "escalate", "Not eligible for automatic handling: diagnosis or account-specific follow-up may be needed.", ESCALATION_REPLY
        if confidence < self.confidence_threshold:
            return "escalate", f"Classification confidence {confidence:.2f} is below the configured safety threshold.", ESCALATION_REPLY
        if evidence is None or evidence.similarity < self.evidence_threshold:
            return "escalate", "No sufficiently close training-only historical precedent was found.", ESCALATION_REPLY
        return "auto_handle", "Public how-to/compatibility question with high model confidence and a close historical AppleSupport precedent.", redact_customer_handle(evidence.historical_apple_reply)


class SupportAgent:
    def __init__(self, artifact_path: Union[str, Path], *, generator: Optional[ResponseGenerator] = None,
                 logger: Optional[DecisionLogger] = None, confidence_threshold: float = 0.80, evidence_threshold: float = 0.34):
        artifact = load(Path(artifact_path))
        vectorizer = artifact["classifier"].named_steps["tfidf"]
        self.classifier = IntentClassifier(artifact["classifier"])
        self.risk_detector = RiskDetector()
        self.retriever = EvidenceRetriever(vectorizer, artifact["train_texts"], artifact["train_intents"], artifact["train_replies"], artifact["train_ids"])
        self.policy = PolicyEngine(confidence_threshold, evidence_threshold)
        self.generator, self.logger = generator or ResponseGenerator(), logger

    def respond(self, text: str) -> dict:
        started = time.perf_counter()
        if not text or not text.strip():
            raise ValueError("message must not be blank")
        intent, confidence = self.classifier.predict(text)
        risk_level, risk_signals = self.risk_detector.detect(text, intent)
        try:
            evidence = self.retriever.retrieve(text, intent)
        except Exception:
            evidence = None
        decision, reason, base_reply = self.policy.decide(intent, confidence, risk_signals, evidence)
        reply, llm_used, provider = self.generator.generate(message=text, intent=intent, confidence=confidence,
            evidence=evidence.model_dump() if evidence else None, decision=decision, safety_reason=reason, historical_reply=base_reply)
        if provider == "generation_failed":
            decision = "escalate"
            reason = "LLM generation was unavailable; escalating rather than sending an unverified automated draft."
        result = AgentResult(intent=intent, intent_confidence=round(confidence, 3), risk_level=risk_level, risk_signals=risk_signals,
            decision=decision, decision_reason=reason, draft_reply=reply, evidence=evidence, llm_used=llm_used,
            llm_provider=provider, latency_ms=round((time.perf_counter() - started) * 1000, 1)).model_dump()
        if self.logger:
            self.logger.record(result)
        return result
