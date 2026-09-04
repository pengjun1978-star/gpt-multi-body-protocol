"""v1.1.1 hotfix: stable business identity, single ownership and mail gates."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import hashlib, re

ACTIVE = {"ACCEPTED", "STARTED", "RUNNING", "BLOCKED", "RECOVERY"}
STAGES = ("PREPARE", "MATERIALIZE_MD", "USER_REVIEW", "VERIFY_RECIPIENTS", "VERIFY_ARTIFACT", "SEND", "DELIVERY_CONFIRMATION")
CORRECTION_WORDS = ("继续", "改一下", "不是这个", "附件错了", "地址对了", "再核验", "重新发", "补一个人", "抄送改")

@dataclass
class Artifact:
    artifact_id: str; path: str; bytes: int; sha256: str; version: str
    business_task_id: str; stage: str; current: bool = True; approved: bool = False

@dataclass
class BusinessTask:
    business_task_id: str; intent: str; canonical_thread: str; canonical_session: str
    stage: str = "PREPARE"; state: str = "STARTED"
    recipients: dict = field(default_factory=lambda: {"to": [], "cc": []})
    artifact: Artifact | None = None

class BusinessTaskError(RuntimeError): pass

class BusinessTaskRuntime:
    def __init__(self): self.tasks: dict[str, BusinessTask] = {}

    def create(self, business_task_id, intent, thread, session):
        if business_task_id in self.tasks: raise BusinessTaskError("DUPLICATE_EXECUTION_BLOCKED")
        t=BusinessTask(business_task_id, intent, thread, session); self.tasks[business_task_id]=t; return t

    def resolve(self, text, current_task_id=None):
        correction=any(w in text for w in CORRECTION_WORDS)
        if correction:
            if not current_task_id or current_task_id not in self.tasks: raise BusinessTaskError("CONTINUATION_DISPATCH_BLOCKED")
            return {"business_task_id": current_task_id, "continuation_or_new": "CONTINUATION", "owner": self.tasks[current_task_id].canonical_thread}
        return {"business_task_id": current_task_id, "continuation_or_new": "NEW"}

    def transition(self, task_id, stage, *, state=None):
        if stage not in STAGES: raise ValueError("UNKNOWN_STAGE")
        t=self.tasks[task_id]; t.stage=stage
        if state: t.state=state
        return t

    def materialize(self, task_id, path, version):
        p=Path(path); raw=p.read_bytes(); old=self.tasks[task_id].artifact
        if old: old.current=False
        a=Artifact(f"{task_id}:artifact:{version}",str(p),len(raw),hashlib.sha256(raw).hexdigest(),version,task_id,"MATERIALIZE_MD")
        self.tasks[task_id].artifact=a; return a

    def invalidate_artifact(self, task_id):
        t=self.tasks[task_id]
        if t.artifact: t.artifact.current=False
        t.state="BLOCKED"; t.stage="SEND"; raise BusinessTaskError("BLOCKED_BY_ARTIFACT")

    def set_recipients(self, task_id, to, cc=()): self.tasks[task_id].recipients={"to":list(to),"cc":list(cc)}

    def attachment_gate(self, task_id, *, to, cc=()):
        t=self.tasks[task_id]; a=t.artifact
        if not a or not a.current or not a.approved or a.business_task_id != task_id: raise BusinessTaskError("BLOCKED_BY_ARTIFACT")
        p=Path(a.path)
        if not p.exists() or p.stat().st_size != a.bytes or hashlib.sha256(p.read_bytes()).hexdigest()!=a.sha256: raise BusinessTaskError("ARTIFACT_VERIFY_FAILED")
        if t.recipients != {"to":list(to),"cc":list(cc)}: raise BusinessTaskError("RECIPIENT_SET_STALE")
        return {"status":"ATTACHMENT_GATE_PASS","artifact_id":a.artifact_id,"business_task_id":task_id}

    def dispatch(self, task_id, action, *, thread):
        t=self.tasks[task_id]
        if t.canonical_thread != thread: raise BusinessTaskError("DUPLICATE_EXECUTION_BLOCKED")
        return {"business_task_id":task_id,"execution_owner":t.canonical_thread,"stage":t.stage,"action":action}
