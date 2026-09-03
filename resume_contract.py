"""P0 continuation guard for v1.0.2.

Continuation is an explicit lookup operation. It never falls back to create.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

RESUMABLE = {"ACTIVE", "RESUMABLE"}

class ResumeError(RuntimeError):
    code = "RESUME_FAILED/BLOCKED"

@dataclass
class ResumeRecord:
    parent_gpt_thread_id: str
    codex_task_id: str
    codex_thread_session_id: str
    body_node_id: str
    project_worktree: str
    created_at: str
    last_resume_at: str | None = None
    status: str = "RESUMABLE"

class ResumeRegistry:
    def __init__(self):
        self.records = {}

    def _key(self, parent, task):
        return (parent, task)

    def register(self, record: ResumeRecord):
        key = self._key(record.parent_gpt_thread_id, record.codex_task_id)
        existing = self.records.get(key)
        if existing and existing.status in RESUMABLE:
            raise ResumeError("CREATE_REJECTED: existing ACTIVE/RESUMABLE mapping")
        self.records[key] = record
        return record

    def resolve_existing(self, parent, task):
        record = self.records.get(self._key(parent, task))
        if not record or record.status not in RESUMABLE:
            raise ResumeError("RESUME_FAILED/BLOCKED: no ACTIVE/RESUMABLE task mapping")
        return record

    def resume(self, parent, task, body_node_id):
        record = self.resolve_existing(parent, task)
        if record.body_node_id != body_node_id:
            raise ResumeError("RESUME_FAILED/BLOCKED: body identity mismatch")
        record.last_resume_at = datetime.now(timezone.utc).isoformat()
        return {"outcome": "RESUMED_EXISTING", "record": asdict(record)}

    def create(self, parent, task, *, explicit_new, **fields):
        if not explicit_new:
            raise ResumeError("CREATE_REJECTED: create requires explicit new-task intent")
        key = self._key(parent, task)
        existing = self.records.get(key)
        if existing and existing.status in RESUMABLE:
            raise ResumeError("CREATE_REJECTED: existing ACTIVE/RESUMABLE mapping")
        record = ResumeRecord(parent, task, **fields)
        self.records[key] = record
        return {"outcome": "CREATED_NEW", "record": asdict(record)}
