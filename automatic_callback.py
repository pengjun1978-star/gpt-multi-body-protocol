"""Persistent, idempotent callback queue for GPT Brain acceptance callbacks."""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path

PENDING = "PENDING_CALLBACK"
SENT = "SENT_PENDING_ACK"
VERIFIED = "VERIFIED"
ESCALATED = "FAILED_ESCALATED"

class CallbackQueue:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.items = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    item = json.loads(line); self.items[item["idempotency_key"]] = item

    def _save(self):
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in self.items.values()), encoding="utf-8")
        tmp.replace(self.path)

    @staticmethod
    def key(task_id, parent_gpt_thread_id, event_id, payload):
        digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        return f"{task_id}:{parent_gpt_thread_id}:{event_id}:{digest}"

    def enqueue(self, *, task_id, parent_gpt_thread_id, event_id, payload, max_attempts=5):
        key = self.key(task_id, parent_gpt_thread_id, event_id, payload)
        item = self.items.get(key)
        if item: return item
        item = {"idempotency_key": key, "task_id": task_id,
                "parent_gpt_thread_id": parent_gpt_thread_id, "event_id": event_id,
                "payload": payload, "status": PENDING, "attempts": 0,
                "max_attempts": max_attempts, "next_retry_at": 0, "ack": None,
                "errors": []}
        self.items[key] = item; self._save(); return item

    def retry(self, sender, *, now=None):
        now = time.time() if now is None else now
        results = []
        for item in list(self.items.values()):
            if item["status"] not in (PENDING,): continue
            if item["next_retry_at"] > now: continue
            item["attempts"] += 1
            try:
                sender(item["parent_gpt_thread_id"], item["payload"])
                item["status"] = SENT; item["sent_at"] = now
            except Exception as exc:
                item["errors"].append(str(exc))
                if item["attempts"] >= item["max_attempts"]:
                    item["status"] = ESCALATED
                else:
                    item["next_retry_at"] = now + min(60, 2 ** (item["attempts"] - 1))
            results.append(item)
        self._save(); return results

    def acknowledge(self, idempotency_key, *, ack_id, consumer="GPT Brain"):
        item = self.items[idempotency_key]
        if item["status"] != SENT: raise ValueError("ACK_REJECTED: callback not sent")
        item.update({"status": VERIFIED, "ack": {"ack_id": ack_id, "consumer": consumer}})
        self._save(); return item
