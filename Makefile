PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python
export PYTHONPATH := src
export PYTHONPYCACHEPREFIX := work/pycache

.PHONY: setup fetch pairs train evaluate demo serve test quick clean-data

setup:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -r requirements.txt

fetch:
	$(PY) scripts/fetch_data.py

pairs:
	$(PY) scripts/prepare_data.py --twcs work/kaggle-cache/datasets/thoughtvector/customer-support-on-twitter/versions/10/twcs/twcs.csv

train:
	$(PY) scripts/train.py

evaluate:
	$(PY) scripts/evaluate.py

test:
	$(PY) -m pytest -q

serve:
	$(PY) -m uvicorn support_agent.api:app --host 0.0.0.0 --port $${PORT:-8000}

demo:
	$(PY) scripts/predict.py ".@AppleSupport how do I stop this absurd autocorrect?"

quick: setup fetch pairs train evaluate test demo

clean-data:
	rm -f data/apple_pairs.csv artifacts/apple_agent.joblib artifacts/evaluation.json artifacts/evaluation_predictions.jsonl
