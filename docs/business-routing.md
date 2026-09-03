# Business Routing Foundation

The control body creates a registry from self-identification and live probes. A requirement is evaluated against capability names, GPU/VRAM, OS, routing flag, and runtime health. Every rejected body receives explicit reasons. Fallback is permitted only when the requirement says so.

Business Case 001 is `office_4090_ai_compute_capability_discovery`. The expected route is `mbp-primary` control/orchestration to `office-4090` execution, followed by a receipt. The receipt remains `PASS_PENDING_GPT_ACCEPTANCE` until GPT accepts it.
