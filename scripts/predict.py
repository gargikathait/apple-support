#!/usr/bin/env python3
import argparse, json
from support_agent.agent import SupportAgent

p = argparse.ArgumentParser()
p.add_argument("message")
p.add_argument("--model", default="artifacts/apple_agent.joblib")
args = p.parse_args()
print(json.dumps(SupportAgent(args.model).respond(args.message), indent=2, ensure_ascii=False))
