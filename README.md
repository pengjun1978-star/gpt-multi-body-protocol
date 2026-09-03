# GPT Multi-Body Protocol v1.1.1 — Reliability & Integration

This release candidate hardens runtime affinity, cloud artifact transport,
exact continuation, Return-to-Origin callbacks, parent progress reporting,
runtime liveness, and explicit resource contracts. GPT Work is the Cloud
Artifact Production Runtime; it is not a Body.

## Release boundaries

- `DIRECT_CLOUD_WORK` requires strong Cloud Runtime affinity.
- `LOCAL_BRIDGED_CLOUD_WORK` is an explicit fallback and cannot satisfy Direct
  Cloud Work acceptance.
- Runtime fallback is never silent; unavailable Cloud Runtime returns an
  explicit failure.
- The 200KB Human-in-the-Loop Cloud-to-Local artifact path is
  `PASS/GPT_ACCEPTED`. Fully Automatic Cloud-to-Local remains a platform
  boundary.
- Enterprise Mail Skill employee rollout is `MANUAL/OFFLINE ROLLOUT` and does
  not block this release.
- This package must be accepted by Parent GPT before GA publication.

See [v1.1.1 acceptance matrix](docs/v1.1.1-acceptance-matrix.md) and
[200KB E2E evidence](docs/GPT-Work-Cloud-200KB-E2E.md).

This release extends the frozen v1.0/v1.0.1 protocol with a capability registry, backward-compatible task requirements, deterministic routing, sanitized business receipts, resumable execution, evidence delivery, and automatic GPT callback acknowledgement tracking.

## Safety boundary

Registry discovery reads local identity, Office-4090 GPU/runtime metadata, and the existing llama.cpp `/v1/models` endpoint. It does not install, upgrade, delete, switch, or restart software. `runtime_health` is an input fact; `ACTIVE` alone is not readiness.

## Components

- `discover.py`: builds a live registry for `mbp-primary`, `office-4090`, and reserved `mac-studio`.
- `router.py`: rejects `RESERVED`, `OFFLINE`, `STALE`, and `ORPHANED`, then matches requirements deterministically.
- `business_receipt.py`: runs Office capability discovery through the router and writes a Business Receipt.
- `resume_contract.py`: resolves and resumes an existing mapping; it rejects silent create and duplicate active mappings.
- `business_evidence_delivery.py`: packages substantive evidence into hashed, bounded chunks and tracks delivery separately from parent visibility.
- `automatic_callback.py`: persists callbacks, retries busy parents, deduplicates sends, escalates failures, and records explicit GPT ACKs.
- `mandatory_return.py`: requires every terminal local result to actively return a canonical callback to its original Parent GPT; Office inbox/outbox is fallback only.
- `schemas/task-requirement-v1.json`: compatible requirement fields.

The employee-review integration is represented only by a future task template boundary; this line does not access mailbox credentials or fabricate email data.

## Resume Contract (P0)

Every task mapping carries `parent_gpt_thread_id`, `codex_task_id`, `codex_thread_session_id`, `body_node_id`, `project_worktree`, `created_at`, and `last_resume_at`. A continuation first resolves the existing `(parent_gpt_thread_id, codex_task_id)` record, verifies body identity, then resumes it. Missing or mismatched records return `RESUME_FAILED/BLOCKED`; they never create a replacement. Creation requires explicit new-task intent and returns `CREATED_NEW`. Existing `ACTIVE` or `RESUMABLE` mappings reject creation.

## Mandatory Return-to-Origin Rule (v1.1.1)

Every Parent GPT delegation must actively return a canonical callback to the
original Parent GPT for `COMPLETED`, `PARTIAL`, `BLOCKED`, `FAILED`, or
`CANCELLED`. Office inbox/outbox is a fallback path and cannot replace the
Parent GPT return. Continuation of the same task must exact-resume the canonical
Codex session; unavailable canonical sessions result in `BLOCKED` and never
create a new task, thread, or session.
