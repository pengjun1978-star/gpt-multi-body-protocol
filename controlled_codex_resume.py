"""Production bridge: persistent owner gate -> exact Codex CLI resume.

This module turns the product-level gap (no exposed ChatGPT native resume tool)
into a local transport that can target one existing Codex session by UUID
without creating a new thread.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from execution_control import ExecutionOwnerRecord, TriggerGate
from execution_control_sqlite import SQLiteExecutionOwnerRegistry
from native_codex_transport import CodexResumeResult, resume_exact_session


TRANSPORT = "codex_cli_exec_resume"


@dataclass(frozen=True)
class ControlledResumeIdentity:
    parent_gpt_thread_id: str
    task_id: str
    canonical_session_id: str
    caller_session_id: str


class ControlledCodexResume:
    def __init__(self, db_path: str | Path, *, lease_seconds: float = 1800.0):
        self.registry = SQLiteExecutionOwnerRegistry(db_path, lease_seconds=lease_seconds)
        self.trigger_gate = TriggerGate({TRANSPORT})

    def register(self, identity: ControlledResumeIdentity) -> dict:
        return self.registry.register_canonical(
            ExecutionOwnerRecord(
                parent_gpt_thread_id=identity.parent_gpt_thread_id,
                task_id=identity.task_id,
                canonical_session_id=identity.canonical_session_id,
            )
        )

    def resume(
        self,
        identity: ControlledResumeIdentity,
        prompt: str,
        *,
        cwd: str | Path | None = None,
        codex_bin: str = "codex",
        codex_home: str | Path | None = None,
        require_local_session: bool = True,
        timeout_seconds: int = 1800,
    ) -> dict:
        claim = self.registry.claim(
            identity.parent_gpt_thread_id,
            identity.task_id,
            identity.caller_session_id,
            transport=TRANSPORT,
            trigger_gate=self.trigger_gate,
        )
        if claim["outcome"] == "ALREADY_RUNNING_NOOP":
            return {"claim": claim, "resume": None}

        generation = claim["generation"]
        try:
            result: CodexResumeResult = resume_exact_session(
                identity.canonical_session_id,
                prompt,
                cwd=cwd,
                codex_bin=codex_bin,
                codex_home=codex_home,
                require_local_session=require_local_session,
                timeout_seconds=timeout_seconds,
            )
            return {"claim": claim, "resume": result}
        finally:
            self.registry.complete(
                identity.parent_gpt_thread_id,
                identity.task_id,
                identity.caller_session_id,
                generation,
            )
