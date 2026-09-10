"""Streaming conversion from official TWCS rows to direct Apple request/reply pairs."""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

APPLE = "AppleSupport"

def clean(text: str) -> str:
    return " ".join((text or "").replace("&amp;", "&").split())

def split_for(tweet_id: str) -> str:
    # Parent ID is the unit so direct child replies cannot cross a split.
    bucket = int(hashlib.sha256(str(tweet_id).encode()).hexdigest()[:8], 16) % 100
    return "train" if bucket < 80 else "validation" if bucket < 90 else "test"

def extract_apple_pairs(twcs_csv: Path, out_csv: Path, limit: int | None = None) -> int:
    """Make direct inbound -> AppleSupport pairs in two low-memory passes."""
    parents: dict[str, tuple[str, str]] = {}
    wanted: set[str] = set()
    with twcs_csv.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["author_id"] == APPLE and row.get("in_response_to_tweet_id"):
                wanted.add(row["in_response_to_tweet_id"])
    with twcs_csv.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["tweet_id"] in wanted and row["inbound"] == "True":
                parents[row["tweet_id"]] = (clean(row["text"]), row.get("author_id", ""))

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    seen: set[str] = set()
    fields = ["tweet_id", "customer_text", "historical_reply", "split"]
    with out_csv.open("w", encoding="utf-8", newline="") as target, twcs_csv.open(encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for row in csv.DictReader(handle):
            parent_id = row.get("in_response_to_tweet_id")
            if row["author_id"] != APPLE or parent_id not in parents or parent_id in seen:
                continue
            customer_text, _ = parents[parent_id]
            if not customer_text or not row.get("text"):
                continue
            writer.writerow({"tweet_id": parent_id, "customer_text": customer_text,
                             "historical_reply": clean(row["text"]), "split": split_for(parent_id)})
            seen.add(parent_id); count += 1
            if limit and count >= limit:
                break
    return count
