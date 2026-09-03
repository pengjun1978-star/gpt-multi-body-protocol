# GPT Multi-Body Protocol v1.0.2 — Business Routing Foundation

This isolated development line extends the frozen v1.0/v1.0.1 protocol with a capability registry, backward-compatible task requirements, deterministic routing, and sanitized business receipts.

## Safety boundary

Registry discovery reads local identity, Office-4090 GPU/runtime metadata, and the existing llama.cpp `/v1/models` endpoint. It does not install, upgrade, delete, switch, or restart software. `runtime_health` is an input fact; `ACTIVE` alone is not readiness.

## Components

- `discover.py`: builds a live registry for `mbp-primary`, `office-4090`, and reserved `mac-studio`.
- `router.py`: rejects `RESERVED`, `OFFLINE`, `STALE`, and `ORPHANED`, then matches requirements deterministically.
- `business_receipt.py`: runs Office capability discovery through the router and writes a Business Receipt.
- `schemas/task-requirement-v1.json`: compatible requirement fields.

The employee-review integration is represented only by a future task template boundary; this line does not access mailbox credentials or fabricate email data.
