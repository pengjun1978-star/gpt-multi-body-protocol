"""Business evidence delivery contract for direct-parent text callbacks."""
from __future__ import annotations
import hashlib, json, uuid
from datetime import datetime, timezone

CONTRACT = "business-evidence-delivery-v1"
MAX_CHUNK_CHARS = 12000

def _now(): return datetime.now(timezone.utc).isoformat()

def build_manifest(evidence, *, artifact_name="business-evidence.md"):
    raw = evidence.encode("utf-8")
    return {"artifact_name": artifact_name, "encoding": "utf-8", "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "chunks": (len(evidence) + MAX_CHUNK_CHARS - 1) // MAX_CHUNK_CHARS}

def build_delivery(task_id, evidence, *, artifact_name="business-evidence.md", event_id=None):
    manifest = build_manifest(evidence, artifact_name=artifact_name)
    delivery_id = event_id or str(uuid.uuid4())
    chunks = []
    for index in range(manifest["chunks"]):
        text = evidence[index * MAX_CHUNK_CHARS:(index + 1) * MAX_CHUNK_CHARS]
        chunks.append({"contract": CONTRACT, "task_id": task_id, "delivery_id": delivery_id,
                       "chunk_index": index, "chunk_count": manifest["chunks"], "text": text,
                       "chunk_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                       "manifest_sha256": manifest["sha256"]})
    receipt = {"contract": CONTRACT, "task_id": task_id, "delivery_id": delivery_id,
               "created_at": _now(), "manifest": manifest,
               "delivery": {"transport": "PENDING", "chunks_sent": 0,
                            "sender_confirmed": False, "office_inbox": "UNVERIFIED",
                            "parent_visibility": "UNVERIFIED", "parent_ack": None},
               "status": "PENDING", "errors": [],
               "needs_gpt_decision": ["Parent GPT must acknowledge evidence consumption"]}
    return receipt, chunks

def confirm_delivery(receipt, *, chunks_sent, sender_confirmed,
                     office_inbox="UNVERIFIED", parent_ack=None, error=None):
    expected = receipt["manifest"]["chunks"]
    receipt["delivery"].update({"chunks_sent": chunks_sent, "sender_confirmed": sender_confirmed,
                                 "office_inbox": office_inbox, "parent_ack": parent_ack})
    if error or chunks_sent != expected or not sender_confirmed:
        receipt["status"] = "BLOCKED"
        receipt["delivery"]["transport"] = "FAIL"
        receipt["errors"].append(error or "Incomplete chunk delivery or sender confirmation")
    else:
        receipt["status"] = "PASS_PENDING_GPT_ACCEPTANCE"
        receipt["delivery"]["transport"] = "PASS"
    return receipt

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
