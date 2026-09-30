# AppleSupport AI Triage Agent

An AI support triage agent that combines classification, retrieval, generation, and deterministic safety policies to decide which customer requests can be safely handled automatically and which require human intervention.

> **Scope:** This is a portfolio/research demonstration built from historical, public AppleSupport conversations in the [Customer Support on Twitter dataset](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter). It is not affiliated with Apple, is not a live-support system, and must not be used to send customer messages without review.

## Problem

Public support queues contain a mix of simple, answerable questions and requests involving account access, payments, device safety, repair, and unclear context. Treating every message as a chatbot prompt is unsafe; sending all messages to people loses the benefit of fast triage. This project makes the routing decision explicit and inspectable.

## What I built

A small full-stack support workflow: a reproducible TF-IDF + logistic-regression baseline classifies intent, a training-only retriever supplies historical precedent, an optional LLM can draft an allowed reply, and a deterministic policy gate independently determines whether to auto-handle or escalate. The web UI, API, structured metrics, health check, tests, and Render configuration make that workflow easy to run and demo.

## How it works

```text
Customer message
       ↓
Intent classification (TF-IDF + logistic regression)
       ↓
Risk detection → training-only evidence retrieval
       ↓
Optional LLM response generation (drafting only)
       ↓
Deterministic safety policy
       ↓
Auto-handle or human escalation
```

The LLM never decides routing. Account access, payments, fraud, lost/stolen devices, privacy/security, emergencies, heat/smoke, repair/hardware, ambiguous requests, weak evidence, and low confidence remain conservatively routed to a human.

## Demo

Run the browser demo locally at `http://localhost:8000` after the setup below. It displays the message, predicted intent/confidence/risk, retrieved precedent and similarity, draft response, decision, and plain-language reason. A deployment URL is intentionally not claimed here: deploy `render.yaml` to Render first, then add your actual URL to this section.

**Example input**

```text
How do I check whether this adapter is compatible with my iPhone?
```

**Representative output shape**

```json
{
  "intent": "how_to_or_compatibility",
  "intent_confidence": 0.91,
  "risk_level": "low",
  "decision": "auto_handle",
  "decision_reason": "Public how-to/compatibility question with high model confidence and a close historical AppleSupport precedent.",
  "evidence": {"tweet_id": "…", "similarity": 0.42}
}
```

For a sensitive demo, enter: `My Apple ID was hacked and there is an unauthorized charge.` The policy should visibly escalate it even if a classifier is confident.

## Tech stack

- Python, pandas, scikit-learn, NumPy, joblib
- FastAPI + Uvicorn and a dependency-free HTML/CSS/JavaScript interface
- Optional OpenAI Chat Completions API for reply drafting only
- pytest, JSON evaluation artifacts, and standard structured application logs

## Evaluation

The checked-in result was produced on the fixed 175-row author-labelled golden set, whose IDs are excluded from both fitting and retrieval.

| System / metric | Result |
|---|---:|
| TF-IDF + logistic regression macro F1 | 0.691 |
| TF-IDF + logistic regression accuracy | 0.766 |
| Keyword baseline macro F1 | 0.691 |
| Auto-handle precision | 0.500 |
| Auto-handle rate | 3.4% |

These are not deployment claims: the learned model does **not** beat the related keyword baseline, the data uses bootstrap labels, the golden set is small, and LLM/human-judge agreement is deliberately not reported until an independent reviewer completes the calibration set. `make evaluate` writes current machine-readable results to `artifacts/evaluation.json`, including routing, safety-term, retrieval-similarity, and latency audit fields. The full analysis is in [docs/report.md](docs/report.md).

## Engineering decisions

- **Retain the simple classifier:** TF-IDF + logistic regression is fast, reproducible, inspectable, and provides a useful baseline rather than opaque routing.
- **Use retrieval, not invented device advice:** evidence is the closest same-intent conversation from training data only, with its similarity exposed in every result.
- **Keep routing deterministic:** the policy gate owns the decision; a configurable LLM can only refine an already permitted draft.
- **Prefer false escalations to risky automation:** generic public how-to/compatibility requests are the sole auto-handle class, gated by confidence and evidence thresholds.
- **Observe without retaining customer content:** logs omit message text and the developer metrics endpoint exposes aggregate decision, confidence, latency, intent, and escalation-reason signals.

## Run locally

Python 3.9+ and around 1 GB disk are required for the source dataset.

```bash
make setup
make fetch pairs train
make test
make evaluate
make serve
```

Then open `http://localhost:8000`. `make quick` executes the complete reproducible workflow. To use the original CLI:

```bash
PYTHONPATH=src .venv/bin/python scripts/predict.py ".@AppleSupport how do I stop this absurd autocorrect?"
```

### Configuration

Copy `.env.example` values into your deployment platform or shell; never commit a secret.

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `historical` | `historical` uses precedent directly; `mock` is local demo mode; `openai` enables optional drafting. |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model for the optional draft generator. |
| `OPENAI_API_KEY` | unset | Required only with `LLM_PROVIDER=openai`. |
| `AUTO_HANDLE_CONFIDENCE` | `0.80` | Minimum classifier confidence for the only auto-routable class. |
| `AUTO_HANDLE_EVIDENCE` | `0.34` | Minimum train-only cosine similarity. |
| `CORS_ORIGINS` | localhost | Comma-separated allowed browser origins. |
| `MODEL_PATH` | `artifacts/apple_agent.joblib` | Artifact location in a deployed service. |

If an explicitly configured LLM is unavailable, the agent fails closed with `Unable to safely generate an automated response. Escalating to a human.` Historical mode itself needs no API key. If the model artifact is missing, `/api/analyze` returns a safe `503`; `/health` remains available.

## Deploy

The included `render.yaml` is the intentionally small deployment path:

1. Create a Render Blueprint from this repository. Its build command downloads the public source dataset, converts pairs, and trains the ignored model artifact; allow enough build disk and time for the roughly 169 MB archive.
2. It runs Uvicorn and checks `GET /health`. If the Kaggle dataset layout/version changes, adapt the `--twcs` path in `render.yaml` or build the artifact in your platform’s build step and set `MODEL_PATH`.
3. Set `CORS_ORIGINS` to the final frontend origin. Leave `LLM_PROVIDER=historical` for a no-secret demo, or set `LLM_PROVIDER=openai`, `OPENAI_API_KEY`, and `LLM_MODEL` in Render’s secret environment.
4. Verify `/health`, submit a safe how-to and a sensitive message, and inspect `/api/metrics` (aggregate-only developer view).

The single FastAPI service ships the UI and API together to avoid unnecessary infrastructure. A separate Vercel frontend can call the same API by setting `CORS_ORIGINS`, but is not required.

## 30–60 second recording flow

1. Open the demo and read the one-sentence framing.
2. Submit the prefilled battery-drain message; point out its intent, medium risk, training-only precedent, and escalation for diagnostics.
3. Replace it with the adapter compatibility example; show confidence/evidence and the narrow auto-handle decision.
4. Submit the hacked-account/unauthorized-charge example; show the high-risk signals and deterministic escalation.
5. Open `/api/metrics` and `/health` to show observability and deployability, then mention `make evaluate` and the honest limits below.

## Failure analysis and limitations

The original failure analysis is retained in [docs/report.md](docs/report.md): hardware/software overlap, account terms in functional issues, recovery/data-loss ambiguity, contextless follow-ups, and over-generalising product-specific replies remain real limitations. Historical Twitter replies are not current policy. There is no authentication, account lookup, diagnostic integration, multilingual evaluation, live outcome measurement, or completed LLM/human calibration. The latter is a release gate—not a metric to invent. See [docs/labeling_protocol.md](docs/labeling_protocol.md) and [docs/decision_log.md](docs/decision_log.md) for the dataset and methodological audit trail.

## AI-assisted development

Codex was used as an implementation partner for refactoring the workflow, adding tests and the web/API surface, debugging, and iterating on documentation. The project’s data choices, safety posture, evaluation claims, and final review remain deliberate engineering decisions; Codex did not autonomously build or validate the system.
