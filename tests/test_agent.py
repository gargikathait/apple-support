from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from support_agent.agent import SupportAgent
from support_agent.generation import ResponseGenerator


def artifact(tmp_path: Path) -> Path:
    texts = ["how do I use a cable", "is this adapter compatible", "my battery drains quickly", "my phone is stolen"]
    intents = ["how_to_or_compatibility", "how_to_or_compatibility", "battery_drain", "security_or_privacy"]
    classifier = Pipeline([("tfidf", TfidfVectorizer()), ("clf", LogisticRegression(max_iter=500, random_state=7))]).fit(texts, intents)
    path = tmp_path / "agent.joblib"
    joblib.dump({"classifier": classifier, "train_texts": texts, "train_intents": intents,
                 "train_replies": ["@person You can use a compatible cable.", "@person Check compatibility.", "@person Contact support.", "@person Contact support now."],
                 "train_ids": ["train-1", "train-2", "train-3", "train-4"]}, path)
    return path


def test_sensitive_requests_always_escalate(tmp_path):
    agent = SupportAgent(artifact(tmp_path))
    for message in ["My Apple ID password was stolen", "fraud payment on my account", "my phone was lost", "battery is smoking"]:
        result = agent.respond(message)
        assert result["decision"] == "escalate"
        assert result["risk_level"] == "high"


def test_training_only_evidence_and_structured_result(tmp_path):
    agent = SupportAgent(artifact(tmp_path))
    result = agent.respond("How do I use a cable?")
    assert set(result) >= {"intent", "intent_confidence", "risk_level", "decision", "draft_reply", "evidence"}
    assert result["evidence"]["tweet_id"].startswith("train-")
    assert result["decision"] in {"auto_handle", "escalate"}


def test_low_confidence_and_weak_evidence_escalate(tmp_path):
    agent = SupportAgent(artifact(tmp_path), confidence_threshold=0.999)
    assert agent.respond("is this adapter compatible")["decision"] == "escalate"
    agent = SupportAgent(artifact(tmp_path), evidence_threshold=1.01)
    assert agent.respond("how do I use a cable")["decision"] == "escalate"


def test_openai_failure_fails_closed_to_human(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "not-real")
    agent = SupportAgent(artifact(tmp_path), generator=ResponseGenerator("openai"), evidence_threshold=0)
    result = agent.respond("How do I use a cable?")
    assert result["decision"] == "escalate"
    assert result["llm_used"] is False
    assert result["llm_provider"] == "generation_failed"
    assert result["draft_reply"] == "Unable to safely generate an automated response. Escalating to a human."
