#!/usr/bin/env python3
"""Intent, routing, and retrieval-reply evaluation. No external API is needed."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report, confusion_matrix
from support_agent.agent import SupportAgent
from support_agent.labeling import weak_intent
from support_agent.taxonomy import AUTO_INTENTS, HIGH_RISK_TERMS

def read_gold(path: Path) -> pd.DataFrame:
    return pd.read_json(path, lines=True, dtype={"id": str}).fillna("")

def routing_truth(row):
    return "auto_handle" if row.intent in AUTO_INTENTS and not any(t in row.customer_message.lower() for t in HIGH_RISK_TERMS) else "escalate"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gold", type=Path, default=Path("data/golden_apple_v1.jsonl"))
    p.add_argument("--model", type=Path, default=Path("artifacts/apple_agent.joblib"))
    p.add_argument("--out", type=Path, default=Path("artifacts/evaluation.json"))
    args = p.parse_args()
    gold = read_gold(args.gold)
    agent = SupportAgent(args.model)
    outputs = [agent.respond(x) for x in gold.customer_message]
    y = gold.intent.tolist(); pred = [x["intent"] for x in outputs]
    trivial = ["other_needs_human"] * len(y)
    keyword = [weak_intent(x) for x in gold.customer_message]
    route_true = gold.routing_label.tolist() if "routing_label" in gold else [routing_truth(r) for r in gold.itertuples()]
    route_pred = [x["decision"] for x in outputs]
    result = {
        "dataset": {"name": "golden_apple_v1", "n": len(gold), "labelled_by": "project author", "source": "official TWCS rows"},
        "intent": {
            "majority_baseline_macro_f1": round(f1_score(y, trivial, average="macro", zero_division=0), 3),
            "keyword_baseline_macro_f1": round(f1_score(y, keyword, average="macro", zero_division=0), 3),
            "tfidf_logreg_macro_f1": round(f1_score(y, pred, average="macro", zero_division=0), 3),
            "tfidf_logreg_accuracy": round(accuracy_score(y, pred), 3),
            "per_class": classification_report(y, pred, output_dict=True, zero_division=0),
            "confusion_matrix": {"labels": sorted(set(y)), "values": confusion_matrix(y, pred, labels=sorted(set(y))).tolist()},
        },
        "routing": {"precision": round(precision_score(route_true, route_pred, pos_label="auto_handle", zero_division=0), 3),
                    "recall": round(recall_score(route_true, route_pred, pos_label="auto_handle", zero_division=0), 3),
                    "auto_rate": round(route_pred.count("auto_handle") / len(route_pred), 3)},
        "reply": {"method": "train-only nearest-neighbour historical AppleSupport reply for auto-handled requests; safe escalation template otherwise",
                  "mean_evidence_similarity": round(float(np.mean([x["evidence"]["similarity"] for x in outputs])), 3),
                  "important_note": "Similarity is an audit signal, not a quality metric. Run scripts/judge_replies.py with a model API and the human calibration set before relying on it."},
    }
    args.out.parent.mkdir(exist_ok=True, parents=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame([{**{"id": str(gold.iloc[i].id), "message": gold.iloc[i].customer_message, "gold_intent": y[i]}, **outputs[i]} for i in range(len(gold))]).to_json(args.out.with_name("evaluation_predictions.jsonl"), orient="records", lines=True)
    print(json.dumps({k: result[k] for k in ("intent", "routing")}, indent=2))
if __name__ == "__main__": main()
