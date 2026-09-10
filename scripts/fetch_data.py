#!/usr/bin/env python3
"""Fetch the official public Kaggle release without committing it to the repo."""
import os
from pathlib import Path

os.environ.setdefault("KAGGLEHUB_CACHE", str(Path("work/kaggle-cache").resolve()))
import kagglehub

path = Path(kagglehub.dataset_download("thoughtvector/customer-support-on-twitter"))
matches = list(path.rglob("twcs.csv"))
if not matches:
    raise SystemExit(f"TWCS CSV not found under {path}")
print(matches[0])
