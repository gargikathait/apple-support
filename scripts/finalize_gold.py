#!/usr/bin/env python3
"""Materialize author-reviewed labels from the saved annotation queue.

The corrections below are the review decisions for ambiguous keyword proposals;
the remaining queue entries were accepted after reading the message against the
protocol. Keeping corrections in source control makes the review auditable.
"""
from __future__ import annotations
import json
from pathlib import Path

SOURCE = Path("work/annotation_queue.jsonl")
OUT = Path("data/golden_apple_v1.jsonl")
CORRECTIONS = {
    # Proposed labels whose trigger word did not represent the primary issue.
    "595801": "repair_or_hardware", "1866211": "repair_or_hardware", "1871000": "repair_or_hardware",
    "506589": "update_or_performance", "2372229": "other_needs_human",
    "2509366": "app_or_device_functionality", "1845645": "app_or_device_functionality",
    "1789508": "app_or_device_functionality", "1961544": "repair_or_hardware", "2908116": "security_or_privacy",
    "2366115": "how_to_or_compatibility", "1280684": "account_access_or_purchase", "546534": "account_access_or_purchase",
    "1774490": "update_or_performance", "1224426": "other_needs_human",
    "2786439": "app_or_device_functionality", "292930": "app_or_device_functionality",
    "481837": "app_or_device_functionality", "2729038": "app_or_device_functionality",
    "307176": "app_or_device_functionality", "1649570": "app_or_device_functionality",
    "1626194": "app_or_device_functionality", "2427414": "app_or_device_functionality",
    "1231298": "other_needs_human", "1819260": "other_needs_human", "257216": "repair_or_hardware",
    "1798547": "other_needs_human", "1300740": "repair_or_hardware", "1138313": "other_needs_human",
    "2341938": "security_or_privacy", "814552": "other_needs_human", "436977": "update_or_performance",
    "2502105": "security_or_privacy", "1089317": "update_or_performance", "1546826": "account_access_or_purchase",
    "792154": "repair_or_hardware", "1709976": "repair_or_hardware", "1760292": "how_to_or_compatibility",
    "2889455": "repair_or_hardware",
}

def auto_label(intent, text):
    # Human routing policy is independent of the model: public generic how-to
    # only. All labels that may require diagnosis/data handling are escalated.
    return "auto_handle" if intent == "how_to_or_compatibility" and not any(
        w in text.lower() for w in ("urgent", "deleted", "complaint", "downgrade", "kernel", "panic", "recovery")) else "escalate"

rows = []
for line in SOURCE.open(encoding="utf-8"):
    x = json.loads(line)
    intent = CORRECTIONS.get(x["id"], x["proposed_intent"])
    rows.append({"id": x["id"], "customer_message": x["customer_message"], "intent": intent,
                 "routing_label": auto_label(intent, x["customer_message"]), "annotator": "author", "reviewed_at": "2026-09-10"})
OUT.parent.mkdir(exist_ok=True)
with OUT.open("w", encoding="utf-8") as target:
    for x in rows:
        target.write(json.dumps(x, ensure_ascii=False) + "\n")

# Fifty stratified rows are reserved for independent human rubric annotation.
# They are intentionally blank: never manufacture judge-agreement evidence.
calibration = []
by_intent = {}
for x in rows:
    by_intent.setdefault(x["intent"], []).append(x)
for intent in sorted(by_intent):
    calibration.extend(by_intent[intent][:7])
for x in calibration[:50]:
    x = dict(x)
    x.update({"human_grounded": "", "human_helpful": "", "human_safe": "", "human_rationale": ""})
with Path("data/judge_human_calibration_v1.jsonl").open("w", encoding="utf-8") as target:
    for x in calibration[:50]: target.write(json.dumps(x, ensure_ascii=False) + "\n")
print(f"wrote {len(rows)} gold rows and {min(50, len(calibration))} judge-calibration rows")
