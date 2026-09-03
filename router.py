"""Deterministic v1.0.2 router; consumes v1.0/v1.0.1-compatible health facts."""
from dataclasses import dataclass

BLOCKED = {"RESERVED", "OFFLINE", "STALE", "ORPHANED"}

@dataclass
class Decision:
    selected_body: str | None
    candidates: list
    rejections: dict
    fallback: dict

def route(registry: dict, requirement: dict) -> Decision:
    candidates, rejections = [], {}
    for body in registry.get("bodies", []):
        ident = body["node_id"]
        reasons = []
        if body.get("role") in BLOCKED or body.get("routing") is False:
            reasons.append(f"role_or_routing={body.get('role')}")
        if body.get("runtime_health") in BLOCKED:
            reasons.append(f"runtime_health={body.get('runtime_health')}")
        caps = set(body.get("capabilities", []))
        for cap in requirement.get("capabilities", []):
            if cap not in caps: reasons.append(f"missing_capability={cap}")
        if requirement.get("requires_gpu") and not body.get("gpu"): reasons.append("gpu_required")
        vram = body.get("gpu", {}).get("vram_gb") or 0
        if vram < requirement.get("min_vram_gb", 0): reasons.append("insufficient_vram")
        if requirement.get("os") and body.get("os") != requirement["os"]: reasons.append("os_mismatch")
        if reasons: rejections[ident] = reasons
        else: candidates.append(ident)
    preferred = requirement.get("preferred_body")
    selected = preferred if preferred in candidates else (candidates[0] if candidates else None)
    return Decision(selected, candidates, rejections, {"allowed": bool(requirement.get("fallback_allowed")), "used": bool(preferred and selected != preferred and selected is not None)})
