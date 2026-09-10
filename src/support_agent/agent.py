"""Conservative retrieve-and-adapt Apple support agent."""
from __future__ import annotations
import re
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .model import load
from .taxonomy import AUTO_INTENTS, HIGH_RISK_TERMS

def redact_customer_handle(reply: str) -> str:
    return re.sub(r"^@\S+\s*", "", reply).strip()

class SupportAgent:
    def __init__(self, artifact_path: str | Path):
        self.a = load(Path(artifact_path))
        self.vectorizer = self.a["classifier"].named_steps["tfidf"]
        self.train_matrix = self.vectorizer.transform(self.a["train_texts"])

    def respond(self, text: str) -> dict:
        probabilities = self.a["classifier"].predict_proba([text])[0]
        labels = self.a["classifier"].classes_
        best = int(np.argmax(probabilities)); intent = str(labels[best]); confidence = float(probabilities[best])
        similarity = cosine_similarity(self.vectorizer.transform([text]), self.train_matrix).ravel()
        # Evidence must agree with the predicted class, avoiding a topical but incompatible reply.
        candidates = [i for i, label in enumerate(self.a["train_intents"]) if label == intent]
        evidence_idx = max(candidates, key=lambda i: similarity[i]) if candidates else int(np.argmax(similarity))
        evidence = float(similarity[evidence_idx])
        lower = text.lower()
        risks = sorted(term for term in HIGH_RISK_TERMS if term in lower)
        auto = intent in AUTO_INTENTS and confidence >= 0.80 and evidence >= 0.34 and not risks
        if auto:
            reply = redact_customer_handle(self.a["train_replies"][evidence_idx])
            reason = "Public how-to/compatibility question with high model confidence and a close historical AppleSupport precedent."
        elif risks:
            reply = "Thanks for reaching out. For your security and privacy, a support specialist should help with this directly. Please use Apple Support rather than sharing personal or account details here."
            reason = "Contains a sensitive-account, security, payment, or safety signal: " + ", ".join(risks) + "."
        else:
            reply = "Thanks for letting us know. A support specialist should review the details and help with the next best step. Please don’t post personal information publicly."
            reason = "Not eligible for automatic handling: diagnosis or account-specific follow-up may be needed."
        return {"intent": intent, "intent_confidence": round(confidence, 3), "decision": "auto_handle" if auto else "escalate",
                "decision_reason": reason, "draft_reply": reply,
                "evidence": {"tweet_id": self.a["train_ids"][evidence_idx], "similarity": round(evidence, 3),
                             "historical_customer_message": self.a["train_texts"][evidence_idx],
                             "historical_apple_reply": self.a["train_replies"][evidence_idx]}}
