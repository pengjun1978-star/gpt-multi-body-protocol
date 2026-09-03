"""Mandatory v1.1 execution entrypoint.

Every real dispatch/resume must pass through the persistent single-owner gate.
The owner lease remains RUNNING after dispatch and is released only by explicit
completion with the matching generation token.
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
    """The only supported path for real v1.1 resume/dispatch."""

    def __init__(
        self,
        db_path: str | Path,
        allowed_resume_transports: set[str] | None = None,
        lease_seconds: float = 120.0,
    ):
        self.registry = SQLiteExecutionOwnerRegistry(db_path, lease_seconds=lease_seconds)
        allowed = (
            {"native_codex_resume", "automatic_scheduler_resume"}
            if allowed_resume_transports is None
            else set(allowed_resume_transports)
        )
        self.trigger_gate = TriggerGate(allowed)

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
        now: float | None = None,
    ) -> dict[str, Any]:
        """Claim ownership, schedule, and dispatch without releasing the lease.

        The returned generation is the completion token.  Call complete() only
        after the real execution has produced its terminal Receipt/callback.
        """
        claim = self.registry.claim(
            identity.parent_gpt_thread_id,
            identity.task_id,
            identity.caller_session_id,
            transport=identity.transport,
            trigger_gate=self.trigger_gate,
            now=now,
        )
        if claim["outcome"] == "ALREADY_RUNNING_NOOP":
            return {"claim": claim, "decisions": [], "dispatch_count": 0}

        decisions = scheduler.schedule(completed=completed)
        dispatch_count = 0
        if dispatch is not None:
            for decision in decisions:
                if decision.get("decision") == "DISPATCH":
                    dispatch(decision)
                    dispatch_count += 1
        return {"claim": claim, "decisions": decisions, "dispatch_count": dispatch_count}

    def renew(self, identity: ExecutionIdentity, generation: int, *, now: float | None = None) -> dict[str, Any]:
        return self.registry.renew(
            identity.parent_gpt_thread_id,
            identity.task_id,
            identity.caller_session_id,
            generation,
            now=now,
        )

    def complete(self, identity: ExecutionIdentity, generation: int) -> dict[str, Any]:
        return self.registry.complete(
            identity.parent_gpt_thread_id,
            identity.task_id,
            identity.caller_session_id,
            generation,
        )
