#!/usr/bin/env python3
"""Create the small Apple pair file used by the runnable pipeline."""
import argparse
from pathlib import Path
from support_agent.data import extract_apple_pairs

p = argparse.ArgumentParser()
p.add_argument("--twcs", type=Path, required=True, help="Path to official twcs.csv")
p.add_argument("--output", type=Path, default=Path("data/apple_pairs.csv"))
p.add_argument("--limit", type=int, default=None, help="Optional cap for a faster experiment")
args = p.parse_args()
print(f"wrote {extract_apple_pairs(args.twcs, args.output, args.limit)} direct AppleSupport pairs to {args.output}")
