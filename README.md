# AppleSupport Twitter triage agent

A small, reproducible AI-support-agent evaluation built from the public
[Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)
dataset. It classifies AppleSupport customer tweets, drafts a reply from a
training-only historical AppleSupport precedent, and makes a conservative
auto-handle/escalate decision with a reason.

This is a research demonstration, not an Apple product and not fit to send live
messages. The full conclusion, including why its headline number is misleading,
is in [docs/report.md](docs/report.md).

## Reproduce in under 15 minutes

Python 3.9+ and about 1 GB free disk are enough. The command downloads the
official 169 MB Kaggle archive into ignored `work/`, converts the Apple rows,
fits the model, evaluates the checked-in 175-row golden set, and prints a demo.
No Kaggle API key was required when last tested for this public dataset.

```bash
make quick
```

Or run the stages explicitly:

```bash
make setup fetch pairs train evaluate demo
```

Headline intent result from the checked-in golden set: **macro F1 0.691;
accuracy 0.766**. Generated detail is saved in `artifacts/evaluation.json` and
`artifacts/evaluation_predictions.jsonl`. See the caveats before interpreting
either number.

To ask the agent about a new message:

```bash
PYTHONPATH=src .venv/bin/python scripts/predict.py \
  ".@AppleSupport how do I stop this absurd autocorrect?"
```

The output contains `intent`, model confidence, `decision`, a
human-readable `decision_reason`, `draft_reply`, and the historical evidence
tweet used to ground it. Evidence is retrieved only from training rows.

## Repository map

- `src/support_agent/` — data conversion, classifier, policy, retrieval, and agent.
- `data/golden_apple_v1.jsonl` — 175 author-labelled real incoming TWCS messages.
- `docs/labeling_protocol.md` — sampling, taxonomy, and annotation rules.
- `scripts/evaluate.py` — intent/routing metrics and leakage-safe predictions.
- `scripts/judge_replies.py` — blinded LLM-as-judge runner and Cohen's-kappa calculation against human reviews.
- `data/judge_human_calibration_v1.jsonl` — 50 stratified IDs reserved for a second human scorer; fields are deliberately blank.
- `docs/report.md` — framing, baselines, failure analysis, limitations, and next work.
- `docs/decision_log.md` — 14 non-obvious decisions and rationales.

## Intent taxonomy and handling policy

| Intent | Default handling |
|---|---|
| `battery_drain`, `update_or_performance`, `app_or_device_functionality` | Escalate: may need diagnostics/context. |
| `account_access_or_purchase`, `security_or_privacy` | Escalate: sensitive identity, payment, or recovery risk. |
| `repair_or_hardware` | Escalate: repair/safety assessment. |
| `how_to_or_compatibility` | Auto only if confidence ≥0.80, close precedent ≥0.34, and no risk term. |
| `other_needs_human` | Escalate: ambiguity or out-of-scope. |

The gate also blocks auto-handling for account, password, payment, fraud,
lost/stolen, emergency, heat/smoke, phone/email/IMEI/serial signals. It is
designed for precision over automation volume.

## LLM judge and agreement evidence

The judge rubric is in `scripts/judge_replies.py`: `grounded`, `helpful`, and
`safe` are each binary, with a short rationale. It is intentionally blinded to
gold intent. After an independent reviewer scores the 50 calibration predictions,
run:

```bash
export OPENAI_API_KEY=...
PYTHONPATH=src .venv/bin/python scripts/judge_replies.py --model gpt-4o-mini
```

The script calls a zero-temperature structured JSON judge and reports per-axis
Cohen's kappa. The submitted calibration fields are blank; **there is no
fabricated judge-agreement claim**. This measurement is a required release gate,
not an optional nice-to-have. Details are in the report and protocol.

## Data, licence, and scope

TWCS is CC BY-NC-SA 4.0; use it only consistently with that licence and its
terms. The raw 493 MB CSV and generated pair file are ignored, so cloning this
repository does not redistribute the corpus. The checked-in golden text is an
annotated research subset with anonymized IDs, retained for reproducibility.
