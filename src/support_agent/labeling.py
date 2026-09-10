"""A transparent rule labeler used only to bootstrap training labels.

It is intentionally not used as a production decision rule. Golden labels are
stored separately and are reviewed using docs/labeling_protocol.md.
"""
from __future__ import annotations
import re

from .taxonomy import INTENTS

RULES = [
    ("security_or_privacy", r"\b(lost|stolen|fraud|hacked?|unauthori[sz]ed|phish|privacy|data breach)\b"),
    ("account_access_or_purchase", r"\b(apple id|icloud|i-store|app store|verification|code|password|billing|refund|purchase|subscription|payment|charged)\b"),
    ("repair_or_hardware", r"\b(repair|crack(?:ed)?|screen|camera|speaker|headphone jack|port|button|water damage|hardware)\b"),
    ("battery_drain", r"\b(battery|charge|charging|drain(?:ing|ed)?|percent|%)\b"),
    ("update_or_performance", r"\b(ios\s?\d|update|updat(?:ed|ing)|slow|freeze|freez(?:ing|es)|lag(?:gy)?|crash(?:ing|es|ed)?|wifi|wi-fi)\b"),
    ("app_or_device_functionality", r"\b(app|music|whatsapp|notification|keyboard|bluetooth|sync|siri|facetime|imessage|airdrop|listen|playback)\b"),
    ("how_to_or_compatibility", r"\b(how (do|can|to)|can i|does .* work|compatible|support(?:ed)?|where (is|can))\b"),
]

def weak_intent(text: str) -> str:
    clean = (text or "").lower()
    for label, pattern in RULES:
        if re.search(pattern, clean):
            return label
    return "other_needs_human"

def is_unambiguous_for_gold(text: str) -> bool:
    """Keep only one-rule matches for the automatically proposed annotation queue."""
    clean = (text or "").lower()
    matches = [label for label, p in RULES if re.search(p, clean)]
    return len(set(matches)) == 1 and len(clean.split()) >= 4
