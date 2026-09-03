"""Persistent P1A task registry with explicit lifecycle transitions."""
import json
import sqlite3
from pathlib import Path

STATES = {"REGISTERED", "READY", "RUNNING", "RESULT_READY", "WAITING_GPT_ACCEPTANCE", "ACCEPTED", "BLOCKED", "FAILED"}
ALLOWED = {
    "REGISTERED": {"READY", "BLOCKED"}, "READY": {"RUNNING", "BLOCKED"},
    "RUNNING": {"RESULT_READY", "FAILED", "BLOCKED"},
    "RESULT_READY": {"WAITING_GPT_ACCEPTANCE", "FAILED"},
    "WAITING_GPT_ACCEPTANCE": {"ACCEPTED", "BLOCKED"},
    "ACCEPTED": set(), "BLOCKED": set(), "FAILED": set(),
}


class PersistentTaskRegistry:
    def __init__(self, path: str | Path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS tasks (
          task_id TEXT PRIMARY KEY, priority INTEGER NOT NULL, dependencies TEXT NOT NULL,
          state TEXT NOT NULL, assigned_body TEXT, generation INTEGER NOT NULL DEFAULT 0,
          receipt_status TEXT, callback_status TEXT, ack_status TEXT)""")
        self.db.commit()

    def register(self, task_id, priority=2, dependencies=()):
        deps = tuple(dependencies)
        row = self.db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row:
            if (row["priority"], tuple(json.loads(row["dependencies"]))) != (priority, deps):
                raise ValueError("TASK_ID_CONFLICT")
            return dict(row)
        self.db.execute("INSERT INTO tasks(task_id,priority,dependencies,state) VALUES(?,?,?,?)", (task_id, priority, json.dumps(deps), "REGISTERED"))
        self.db.commit()
        return self.get(task_id)

    def get(self, task_id):
        row = self.db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row: raise KeyError(task_id)
        return dict(row)

    def transition(self, task_id, state, *, body=None, generation=None, receipt_status=None, callback_status=None, ack_status=None):
        current = self.get(task_id)
        if state not in STATES or state not in ALLOWED[current["state"]]:
            raise ValueError(f"INVALID_TRANSITION:{current['state']}->{state}")
        self.db.execute("""UPDATE tasks SET state=?, assigned_body=COALESCE(?,assigned_body),
          generation=COALESCE(?,generation), receipt_status=COALESCE(?,receipt_status),
          callback_status=COALESCE(?,callback_status), ack_status=COALESCE(?,ack_status) WHERE task_id=?""",
          (state, body, generation, receipt_status, callback_status, ack_status, task_id))
        self.db.commit()
        return self.get(task_id)

    def recoverable(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM tasks WHERE state IN ('REGISTERED','READY','RUNNING','RESULT_READY','WAITING_GPT_ACCEPTANCE') ORDER BY priority, task_id")]

    def ready_tasks(self):
        rows = self.db.execute("SELECT * FROM tasks ORDER BY priority, task_id").fetchall()
        accepted = {r["task_id"] for r in rows if r["state"] == "ACCEPTED"}
        return [dict(r) for r in rows if r["state"] in ("REGISTERED", "READY") and set(json.loads(r["dependencies"])) <= accepted]

    def close_loop(self, task_id, *, body, generation, receipt_status="READY", callback_status="DELIVERED", ack_status="ACKED"):
        """Persist one bounded execution -> receipt -> callback -> ACK loop."""
        row = self.get(task_id)
        if row["state"] == "REGISTERED": self.transition(task_id, "READY")
        self.transition(task_id, "RUNNING", body=body, generation=generation)
        self.transition(task_id, "RESULT_READY", receipt_status=receipt_status)
        self.transition(task_id, "WAITING_GPT_ACCEPTANCE", callback_status=callback_status)
        return self.transition(task_id, "ACCEPTED", ack_status=ack_status)
