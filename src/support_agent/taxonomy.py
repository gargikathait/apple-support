"""Closed taxonomy and conservative policy used by the demo."""
from __future__ import annotations

INTENTS = [
    "battery_drain",
    "update_or_performance",
    "app_or_device_functionality",
    "account_access_or_purchase",
    "security_or_privacy",
    "repair_or_hardware",
    "how_to_or_compatibility",
    "other_needs_human",
]

DESCRIPTIONS = {
    "battery_drain": "Unexpected battery loss, charging, or battery health.",
    "update_or_performance": "An OS update, slow device, freezing, crashing, or connectivity regression.",
    "app_or_device_functionality": "A named app, audio, notification, sync, or other feature does not work.",
    "account_access_or_purchase": "Apple ID, verification code, billing, refund, subscription, or purchase issue.",
    "security_or_privacy": "Lost/stolen device, unauthorized access/charge, phishing, or personal-data concern.",
    "repair_or_hardware": "Physical damage, display, camera, speaker, port, or repair/service request.",
    "how_to_or_compatibility": "A non-sensitive how-to question or compatibility question.",
    "other_needs_human": "Ambiguous, abusive, or out-of-scope request.",
}

# Only public, generic questions can be sent automatically. This deliberately
# trades coverage for avoiding account, safety, and diagnosis mistakes.
AUTO_INTENTS = {"how_to_or_compatibility"}
HIGH_RISK_TERMS = {
    "lost", "stolen", "fraud", "hacked", "hack", "unauthorized", "charged",
    "chargeback", "password", "passcode", "apple id", "account", "refund",
    "billing", "receipt", "serial", "imei", "phone number", "email",
    "emergency", "fire", "swollen", "overheat", "overheating", "smoke",
}

HIGH_RISK_INTENTS = {"account_access_or_purchase", "security_or_privacy", "repair_or_hardware"}
