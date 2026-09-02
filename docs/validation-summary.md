# Protocol v1.0 Public Validation Summary

- Baseline status: frozen architecture reference, accepted at the protocol level.
- Verified surfaces: registry and interface concepts, Task Envelope V2, Execution Receipt V2, GPT Acceptance boundary, Heartbeat/Lease states, Recovery/Retry rules, callback evidence semantics, continuous context inheritance, and bootstrap structure.
- Failure drill: heartbeat interruption can progress through `STALE` and `ORPHANED`; safe retry requires `side_effect_state=NONE` and idempotency protection.
- Deliberate limits: production daemon deployment, scheduler/concurrency, failover, and hardware-specific service installation remain future work.
- Public release rule: examples and schemas contain no personal identifiers, hostnames, network addresses, credentials, absolute paths, conversation IDs, or internal business settings.
