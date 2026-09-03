"""Mandatory v1.1 execution entrypoint.

Every real dispatch/resume must pass through the persistent single-owner gate
before the scheduler can mutate workload or dispatch a task.  This is the
control-plane choke point created from the 2026-09-03 duplicate-thread incident.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from execution_control import ExecutionOwnerRecord, TriggerGate
from execution_control_sqlite import SQLiteExecutionOwnerRegistry
from task_orchestrator import DeterministicScheduler


@dataclass(frozen=True)
class ExecutionIdentity:
    parent_gpt_thread_id: str
    task_id: str
    canonical_session_id: str
    caller_session_id: str
    transport: str


class ControlledExecutionEntrypoint:
    """The only supported path for a real v1.1 resume/dispatch."""

    def __init__(self, db_path: str | Path, allowed_resume_transports: set[str] | None = None):
        self.registry = SQLiteExecutionOwnerRegistry(db_path)
        self.trigger_gate = TriggerGate(
            allowed_resume_transports or {"native_codex_resume", "automatic_scheduler_resume"}
        )

    def register(self, identity: ExecutionIdentity) -> dict[str, Any]:
        return self.registry.register_canonical(
            ExecutionOwnerRecord(
                parent_gpt_thread_id=identity.parent_gpt_thread_id,
                task_id=identity.task_id,
                canonical_session_id=identity.canonical_session_id,
            )
        )

    def execute(
        self,
        identity: ExecutionIdentity,
        scheduler: DeterministicScheduler,
        *,
        completed: set[str] | None = None,
        dispatch: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Claim ownership first; only then allow scheduling/dispatch.

        A duplicate/non-canonical session or an unauthorized transport fails
        before scheduler.schedule() is called.  ALREADY_RUNNING_NOOP also exits
        before scheduling, giving true single-flight behavior.
        """
        claim = self.registry.claim(
            identity.parent_gpt_thread_id,
            identity.task_id,
            identity.caller_session_id,
            transport=identity.transport,
            trigger_gate=self.trigger_gate,
        )
        if claim["outcome"] == "ALREADY_RUNNING_NOOP":
            return {"claim": claim, "decisions": [], "dispatch_count": 0}

        try:
            decisions = scheduler.schedule(completed=completed)
            dispatch_count = 0
            if dispatch is not None:
                for decision in decisions:
                    if decision.get("decision") == "DISPATCH":
                        dispatch(decision)
                        dispatch_count += 1
            return {"claim": claim, "decisions": decisions, "dispatch_count": dispatch_count}
        finally:
            self.registry.release(
                identity.parent_gpt_thread_id,
                identity.task_id,
                identity.caller_session_id,
            )
