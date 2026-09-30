"""FastAPI surface for the support-agent demo and developer metrics."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .agent import SupportAgent
from .observability import DecisionLogger
from .schemas import AnalyzeRequest, AgentResult

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s")
ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(os.getenv("MODEL_PATH", ROOT / "artifacts/apple_agent.joblib"))
logger = DecisionLogger()
agent: Optional[SupportAgent] = None

app = FastAPI(title="AppleSupport AI Triage Agent", version="1.0.0")
allowed_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


def get_agent() -> SupportAgent:
    global agent
    if agent is None:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"Model artifact is missing at {MODEL_PATH}. Run make train first.")
        agent = SupportAgent(MODEL_PATH, logger=logger,
            confidence_threshold=float(os.getenv("AUTO_HANDLE_CONFIDENCE", "0.80")),
            evidence_threshold=float(os.getenv("AUTO_HANDLE_EVIDENCE", "0.34")))
    return agent


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_ready": MODEL_PATH.exists()}


@app.post("/api/analyze", response_model=AgentResult)
def analyze(request: AnalyzeRequest) -> dict:
    try:
        return get_agent().respond(request.message)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Agent is unavailable; please escalate to a human.") from exc


@app.get("/api/metrics")
def metrics() -> dict:
    return logger.summary()


@app.get("/")
def home():
    return FileResponse(Path(__file__).with_name("web") / "index.html")
