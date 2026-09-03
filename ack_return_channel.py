"""Parent GPT -> canonical Codex registry ACK return channel."""
from __future__ import annotations
import hashlib, json, sqlite3, time
from pathlib import Path

ACK_CREATED, ACK_DELIVERED, GPT_ACKED, OUTBOX = "ACK_CREATED", "ACK_DELIVERED_TO_CODEX", "GPT_ACKED", "OUTBOX"

class AckReturnChannel:
    def __init__(self, path: str | Path):
        self.db = sqlite3.connect(path, check_same_thread=False); self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS acks(
          ack_event_id TEXT PRIMARY KEY, callback_event_id TEXT UNIQUE NOT NULL,
          task_id TEXT NOT NULL, execution_generation INTEGER NOT NULL,
          parent_route TEXT NOT NULL, ack_id TEXT NOT NULL, payload TEXT NOT NULL,
          status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
          last_error TEXT, created_at REAL NOT NULL, delivered_at REAL);
        """); self.db.commit()

    @staticmethod
    def ack_event_id(callback_event_id, task_id, generation, parent_route):
        raw = json.dumps([callback_event_id, task_id, generation, parent_route], sort_keys=True, ensure_ascii=False)
        return "ack-" + hashlib.sha256(raw.encode()).hexdigest()[:32]

    def create(self, *, callback_event_id, task_id, execution_generation, parent_route, ack_id, payload=None):
        aid = self.ack_event_id(callback_event_id, task_id, execution_generation, parent_route)
        item = {"ack_event_id": aid, "callback_event_id": callback_event_id, "task_id": task_id,
                "execution_generation": execution_generation, "parent_route": parent_route,
                "ack_id": ack_id, "payload": payload or {}, "status": ACK_CREATED,
                "attempts": 0, "created_at": time.time()}
        self.db.execute("""INSERT INTO acks VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
          ON CONFLICT(callback_event_id) DO NOTHING""", (aid, callback_event_id, task_id, execution_generation,
          json.dumps(parent_route, sort_keys=True, ensure_ascii=False), ack_id,
          json.dumps(item["payload"], ensure_ascii=False), ACK_CREATED, 0, None, item["created_at"], None))
        self.db.commit(); return self.get(callback_event_id)

    def get(self, callback_event_id):
        row = self.db.execute("SELECT * FROM acks WHERE callback_event_id=?", (callback_event_id,)).fetchone()
        if not row: raise KeyError(callback_event_id)
        return dict(row)

    def deliver(self, callback_event_id, registry, *, task_id, execution_generation, parent_route):
        item = self.get(callback_event_id)
        if (item["task_id"], item["execution_generation"], json.loads(item["parent_route"])) != (task_id, execution_generation, parent_route):
            raise ValueError("ACK_ROUTE_OR_IDENTITY_MISMATCH")
        if item["status"] == GPT_ACKED: return GPT_ACKED
        try:
            self.db.execute("UPDATE acks SET attempts=attempts+1 WHERE callback_event_id=?", (callback_event_id,))
            registry.receive_gpt_ack(callback_event_id=callback_event_id, task_id=task_id,
                                     generation=execution_generation, parent_route=parent_route, ack_id=item["ack_id"])
            self.db.execute("UPDATE acks SET status=?, delivered_at=? WHERE callback_event_id=?", (GPT_ACKED, time.time(), callback_event_id)); self.db.commit()
            return GPT_ACKED
        except Exception as exc:
            self.db.execute("UPDATE acks SET status=?, last_error=? WHERE callback_event_id=?", (OUTBOX, str(exc), callback_event_id)); self.db.commit(); return OUTBOX
