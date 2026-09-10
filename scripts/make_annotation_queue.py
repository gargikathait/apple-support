#!/usr/bin/env python3
"""Create a stratified queue. Labels are proposed only; a human must review them."""
import argparse, json
from pathlib import Path
import pandas as pd
from support_agent.labeling import is_unambiguous_for_gold, weak_intent
from support_agent.taxonomy import INTENTS

p = argparse.ArgumentParser()
p.add_argument("--pairs", type=Path, default=Path("data/apple_pairs.csv"))
p.add_argument("--output", type=Path, default=Path("data/annotation_queue.jsonl"))
p.add_argument("--per-intent", type=int, default=35)
args = p.parse_args()
df = pd.read_csv(args.pairs).fillna("")
df["proposed_intent"] = df.customer_text.map(weak_intent)
df = df[df.customer_text.map(is_unambiguous_for_gold)]
with args.output.open("w", encoding="utf-8") as out:
    for intent in INTENTS:
        sample = df[df.proposed_intent == intent].sample(min(args.per_intent, (df.proposed_intent == intent).sum()), random_state=11)
        for row in sample.itertuples():
            out.write(json.dumps({"id": str(row.tweet_id), "customer_message": row.customer_text,
                                  "proposed_intent": intent, "intent": "", "auto_handle": "",
                                  "escalation_reason": "", "annotator": "", "reviewed_at": ""}, ensure_ascii=False) + "\n")
print(args.output)
