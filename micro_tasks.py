"""Six bounded regression micro tasks for the v1.1 foundation."""
import hashlib
import json


def run() -> dict:
    t1 = {"task_id": "v11-mto-foundation-mbp-primary-20260903-001:T1", "body_id": "mbp-primary", "status": "completed"}
    raw = json.dumps(t1, sort_keys=True, separators=(",", ":")).encode()
    t2 = {"task_id": "T2", "depends_on": "T1", "sha256": hashlib.sha256(raw).hexdigest()}
    t3 = {"task_id": "T3", "body_id": "office-4090", "probe": "capability_only", "inference": False}
    t4 = {"task_id": "T4", "body_id": "mbp-primary", "value": sum(range(10))}
    t5 = {"task_id": "T5", "body_id": "mac-studio", "state": "RESERVED", "decision": "REJECT"}
    t6 = {"task_id": "T6", "depends_on": ["T2", "T4"], "sha256": t2["sha256"], "value": t4["value"]}
    return {"T1": t1, "T2": t2, "T3": t3, "T4": t4, "T5": t5, "T6": t6}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
