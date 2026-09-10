# Golden-set protocol

`data/golden_apple_v1.jsonl` has 175 real customer messages from the official
Customer Support on Twitter (TWCS) CSV. It is not a synthetic benchmark. Each
row retains its anonymized source tweet ID but not a customer handle or an
answer, so it is safe to exclude from fitting and to use for offline testing.

Sampling was stratified: the annotation queue selected up to 25 messages from
each of eight initial lexical buckets, with a fixed random seed. Those buckets
were only a queueing aid, not the final truth. The author read every message,
assigned its primary customer need, and recorded 36 corrections in
`scripts/finalize_gold.py`. The source code is deliberately the audit trail for
these decisions.

Primary-need rules:

- Choose `security_or_privacy` for an account compromise, fraudulent charge,
  lost/stolen item, or loss/recovery of irreplaceable personal content. These
  are always human-routed.
- Choose `account_access_or_purchase` for sign-in, identity verification,
  billing, refunds, subscriptions, or entitlement; not merely a named app.
- Choose `repair_or_hardware` for a physical component, physical damage, or
  device that cannot power/boot after ordinary recovery.
- Put OS regressions, slowness, crashes, freezes, update failures, and network
  regressions in `update_or_performance`. Put named feature/app failures in
  `app_or_device_functionality`.
- `how_to_or_compatibility` must be a public, generic question. A how-to that
  involves recovery, account access, a complaint, or urgent data loss is not
  automatically routable.
- When two labels are plausible, select the issue that determines the safe next
  action. If none is clear, use `other_needs_human`.

The routing label is an independent policy annotation, not a prediction: only
public, non-sensitive generic how-to/compatibility requests are `auto_handle`.

## Judge calibration protocol

`data/judge_human_calibration_v1.jsonl` reserves 50 stratified golden IDs.
After generating replies, a second reviewer must score each reply independently
on three binary fields: grounded in supplied precedent, helpful next step, and
safe handling/routing. They should not see the model's intent confidence. Then
run `scripts/judge_replies.py`; it uses the fixed rubric in that script and
reports Cohen's kappa for each field.

The human scores are intentionally blank in this submission. A score or kappa
must never be invented merely to satisfy a benchmark. Consequently this is a
release gate, not completed evidence of human/LLM judge agreement.
