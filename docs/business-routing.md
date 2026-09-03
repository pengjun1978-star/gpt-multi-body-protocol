# Business Routing Foundation

The control body creates a registry from self-identification and live probes. A requirement is evaluated against capability names, GPU/VRAM, OS, routing flag, and runtime health. Every rejected body receives explicit reasons. Fallback is permitted only when the requirement says so.

Business Case 001 is `office_4090_ai_compute_capability_discovery`. The expected route is `mbp-primary` control/orchestration to `office-4090` execution, followed by a receipt. The receipt remains `PASS_PENDING_GPT_ACCEPTANCE` until GPT accepts it.

## Business Evidence Delivery / Receipt Contract

`business_evidence_delivery.py` packages substantive evidence as UTF-8 text chunks (12,000 characters maximum), with a delivery manifest and SHA-256 hashes. The direct-parent text callback is the preferred transport. Sender confirmation proves transmission only; `office_inbox` and `parent_visibility` remain separate fields. Missing chunks, missing sender confirmation, or an explicit transport error yields `BLOCKED`. Successful transport yields `PASS_PENDING_GPT_ACCEPTANCE` and does not claim parent visibility without explicit parent acknowledgement.

## Automatic Callback Queue / ACK

`automatic_callback.py` persists callbacks as JSONL records keyed by `task_id`, `parent_gpt_thread_id`, `event_id`, and payload hash. A busy parent causes exponential retry with bounded delay; duplicate enqueue is idempotent. After the final retry, the record becomes `FAILED_ESCALATED`. A successful send remains `SENT_PENDING_ACK`; only an explicit GPT Brain acknowledgement with `ack_id` changes it to `VERIFIED`.
