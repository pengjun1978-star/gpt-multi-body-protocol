# GPT Multi-Body Protocol v1.0.1

An open architecture reference for a single GPT Brain coordinating multiple Codex execution Bodies across heterogeneous hardware.

## Architecture

- **Single GPT Brain**: routing, decisions, acceptance, and memory authority.
- **Codex Bodies**: execution workers with explicit roles and capabilities.
- **PRIMARY / EXTENSION / RESERVED**: lifecycle and routing roles for active and future Bodies.

## Protocol surface

This baseline defines interoperable concepts and machine-readable schemas for:

- Task Envelope V2 and Execution Receipt V2
- GPT Verdict / Acceptance gate
- Heartbeat / Lease and finite health states
- Recovery / Retry / Reroute with idempotency protection
- Callback Contract and delivery evidence boundaries
- Continuous Task Context Inheritance
- Bootstrap for provisioning a compatible Body

Execution completion does not grant GPT acceptance, memory commit, or global completion. Irreversible or ambiguous work must stop and await a decision. Retry requires a satisfied idempotency check and no confirmed side effect.

## Repository layout

`schemas/` contains JSON protocol definitions. `bootstrap/` contains portable low-risk bootstrap and validation examples. `docs/` contains public implementation notes. `examples/` is reserved for sanitized fixtures.

## v1.0.1 Production Hardening

This release adds resident heartbeat/lease adapters, health evaluation, reversible install templates, Body self-identification, canonical timestamp handling, and validation evidence. The v1.0 architecture and schemas remain compatible and frozen.

See [the v1.0.1 phase review](docs/phase-review-v1.0.1.md), [body and time contract](docs/body-and-time-contract.md), and [compatibility and rollback notes](docs/compatibility-and-rollback.md).

## Status

`Protocol v1.0.1 / production hardening.` The v1.0 baseline remains available as the frozen architecture reference.

## Public-safety boundary

This repository contains generalized protocol material and sanitized examples. It excludes private registries, receipts with environment details, credentials, network identifiers, absolute local paths, conversation identifiers, business configuration, and third-party proprietary files.

## License

MIT. See [LICENSE](LICENSE).
