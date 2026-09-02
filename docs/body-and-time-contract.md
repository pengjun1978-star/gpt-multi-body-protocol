# Body identity and Beijing time contract

This v1.0.1 compatibility-layer contract applies to every current and future Body bootstrap. Before execution, the Body records hostname, OS/platform, CPU/architecture, GPU when applicable, registry/node identity, and safely readable network identity. It must match one registry entry. A mismatch stops routing and returns `BODY_MISMATCH`.

Protocol-facing timestamps are serialized as ISO-8601 with `Asia/Shanghai` and `+08:00`. Epoch/UTC instants remain authoritative for age, lease TTL, timeout, and skew calculations. Existing v1.0 UTC `Z` inputs remain parseable. New receipts and callbacks include `source_hardware`, canonical timezone, and `clock_skew_ms` for cross-Body comparisons. System clock and NTP settings are checked by the local Body; changing system time or timezone requires that Body's explicit execution and receipt.
