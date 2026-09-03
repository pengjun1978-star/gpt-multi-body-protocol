# Changelog

## v1.1.1 - 2026-09-03

- Added Runtime Dispatch Guard with strong Cloud Runtime affinity and explicit
  Direct-versus-bridged cloud work types.
- Added Gate D liveness states and heartbeat timeout handling to `STALLED`.
- Added explicit execution, compute, data, artifact, callback, and recovery
  resource contract validation.
- Formalized 200KB GPT Work artifact evidence and Human-in-the-Loop transport
  boundary.
- Moved Enterprise Mail Skill employee clean-install and production rollout to
  manual/offline rollout scope.
- Release verification: 67/67 automated tests pass; v1.1 frozen baseline is
  preserved at `269d7d47892427454255c051b5582c02f812331a`.

## v1.0.2 - 2026-09-03

- Added resumable canonical-session guard with stable execution identifiers.
- Added Business Evidence Delivery Contract with bounded chunks, manifest, and SHA-256 integrity.
- Added persistent Automatic Callback queue with busy retry, idempotency, ACK tracking, and failure escalation.
- Added Release Candidate regression coverage for Router, Resume, evidence delivery, callbacks, ACK, and failure paths.
- Preserved v1.0/v1.0.1 frozen baselines.

## v1.0.2-dev - 2026-09-03

- Added live Capability Registry v1 and deterministic Router v0.
- Added backward-compatible Task Requirement v1 fields.
- Added read-only Office-4090 AI Compute Capability Discovery and Business Receipt.
- Preserved v1.0/v1.0.1 frozen protocol material.

## v1.0.1 - 2026-09-02

- Added resident heartbeat daemon with atomic state writes and signal-safe shutdown.
- Added macOS LaunchAgent and Windows Scheduled Task templates with reversible paths.
- Added control-plane health evaluation and validation documentation.
- Added mandatory Body self-identification and registry matching.
- Added canonical `Asia/Shanghai` serialization and explicit clock-skew evidence requirements.
- Preserved the v1.0 frozen architecture, schemas, and compatibility boundary.
