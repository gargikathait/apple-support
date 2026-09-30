from fastapi.testclient import TestClient
from support_agent import api


class FakeAgent:
    def respond(self, message):
        return {"intent": "how_to_or_compatibility", "intent_confidence": .91, "risk_level": "low", "risk_signals": [], "decision": "auto_handle", "decision_reason": "safe", "draft_reply": "Try this.", "evidence": None, "llm_used": False, "llm_provider": "historical", "latency_ms": 1.0}


def test_health_and_valid_request(monkeypatch):
    monkeypatch.setattr(api, "get_agent", lambda: FakeAgent())
    client = TestClient(api.app)
    assert client.get("/health").status_code == 200
    response = client.post("/api/analyze", json={"message": "How do I connect this?"})
    assert response.status_code == 200
    assert response.json()["decision"] == "auto_handle"


def test_api_rejects_missing_or_blank_message():
    client = TestClient(api.app)
    assert client.post("/api/analyze", json={}).status_code == 422
    assert client.post("/api/analyze", json={"message": "   "}).status_code == 422
