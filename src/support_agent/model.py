from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Set
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .labeling import weak_intent
from .taxonomy import INTENTS

def train(pair_csv: Path, model_path: Path, exclude_ids: Optional[Set[str]] = None) -> dict:
    frame = pd.read_csv(pair_csv).fillna("")
    frame["intent"] = frame.customer_text.map(weak_intent)
    if exclude_ids:
        frame = frame[~frame.tweet_id.astype(str).isin(exclude_ids)].copy()
    train_frame = frame[frame.split == "train"].copy()
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, strip_accents="unicode")),
        ("clf", LogisticRegression(max_iter=600, class_weight="balanced", C=2.0, random_state=7)),
    ])
    pipe.fit(train_frame.customer_text, train_frame.intent)
    # Retrieval evidence is strictly train-only; never retrieve a held-out answer.
    artifact = {"classifier": pipe, "train_texts": train_frame.customer_text.tolist(),
                "train_replies": train_frame.historical_reply.tolist(), "train_ids": train_frame.tweet_id.astype(str).tolist(),
                "train_intents": train_frame.intent.tolist(), "taxonomy": INTENTS}
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_path)
    return {"n_pairs": len(frame), "n_train": len(train_frame), "intent_counts": frame.intent.value_counts().to_dict()}

def load(path: Path):
    return joblib.load(path)
