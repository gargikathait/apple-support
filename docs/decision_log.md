# Decision log

- Selected **AppleSupport** because it has 106k direct request/reply pairs in TWCS, enough to retrieve brand-specific precedent without cross-brand contamination.
- Used only a direct inbound parent and AppleSupport child as training pairs; thread context is useful later, but ambiguous reply chains make a first pass less auditable.
- Chose eight operational intents rather than an exhaustive product ontology; a support router needs safe action categories, not fine-grained device taxonomy.
- Made data/content loss a security/privacy-class routing trigger even when it is not a breach; recovery promises are high-risk.
- Excluded the golden tweet IDs from both classifier fitting and nearest-neighbour evidence retrieval.
- Split ordinary pairs deterministically by inbound tweet ID, so a direct message and its answer do not land in different splits.
- Used TF-IDF + logistic regression as the simple learned model: fast, inspectable, and reproducible under 15 minutes.
- Kept the lexical labeler only as a transparent weak-supervision bootstrap, never as the production routing policy.
- Retrieved precedent only from the predicted intent class, avoiding a superficially similar answer for a different issue.
- Returned historical AppleSupport wording for auto replies instead of inventing device-specific repair instructions.
- Auto-handling is limited to high-confidence, close-match, public how-to/compatibility questions; all other cases escalate by design.
- Hard-blocked account, security, payment, safety, hardware identifiers, and potential personal identifiers from automatic handling.
- Treated reply similarity as an audit clue, not reply-quality evidence.
- Built an LLM judge that is blinded to gold labels and requires independent human calibration; deliberately did not fabricate its agreement result without an API/reviewer.
- Kept response generation optional and downstream of policy: an LLM may draft an already permitted reply but cannot decide routing or override hard safety blocks.
- Added a single FastAPI service that serves both the demo interface and JSON API; this is easier to deploy and explain than a separate frontend/backend for a small portfolio project.
- Logged aggregate operational signals and structured, message-free decisions rather than retaining customer text in application logs.
- Exposed confidence and evidence thresholds as environment variables, so routing trade-offs can be tested without modifying source code.
