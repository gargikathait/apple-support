#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from support_agent.model import train

p = argparse.ArgumentParser()
p.add_argument("--pairs", type=Path, default=Path("data/apple_pairs.csv"))
p.add_argument("--output", type=Path, default=Path("artifacts/apple_agent.joblib"))
p.add_argument("--exclude-gold", type=Path, default=Path("data/golden_apple_v1.jsonl"),
               help="Gold IDs excluded from fitting and retrieval; ignored if absent.")
args = p.parse_args()
exclude = set()
if args.exclude_gold.exists():
    import pandas as pd
    exclude = set(pd.read_json(args.exclude_gold, lines=True, dtype={"id": str}).id.astype(str))
print(json.dumps(train(args.pairs, args.output, exclude), indent=2))
