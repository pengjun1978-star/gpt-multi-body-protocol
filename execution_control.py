"""v1.1 P0 single-execution-owner and trigger-deduplication guard.

This module protects business task identity from being executed concurrently by
multiple Codex UI/session threads. Transport authorization is explicit: a
GitHub comment is not a resume transport, and create-only handoff transports
must never be used to resume an existing task.
"""
from dataclasses import dataclass


class ExecutionControlError(RuntimeError):
    """Raised when an execution trigger is not authorized."""

    code = "DUPLICATE_EXECUTION_BLOCKED"


@dataclass
class ExecutionOwnerRecord:
    parent_gpt_thread_id: str
    task_id: str
    canonical_session_id: str
    state: str = "IDLE"
    active_session_id: str | None = None
    generation: int = 0


class TriggerGate:
    """Explicit allow-list for transports that may resume an existing task."""

    def __init__(self, allowed_resume_transports: set[str] | None = None):
        self.allowed_resume_transports = allowed_resume_transports or {"native_codex_resume"}

    def authorize_resume(self, transport: str) -> None:
        if transport not in self.allowed_resume_transports:
            raise ExecutionControlError(
                f"RESUME_TRANSPORT_BLOCKED: {transport} is not an authorized resume transport"
            )


class ExecutionOwnerRegistry:
    """One business task -> one canonical session -> at most one RUNNING owner."""

    def __init__(self):
        self.records: dict[tuple[str, str], ExecutionOwnerRecord] = {}

    @staticmethod
    def _key(parent_gpt_thread_id: str, task_id: str) -> tuple[str, str]:
        return parent_gpt_thread_id, task_id

    def register_canonical(self, record: ExecutionOwnerRecord) -> ExecutionOwnerRecord:
        key = self._key(record.parent_gpt_thread_id, record.task_id)
        existing = self.records.get(key)
        if existing:
            if existing.canonical_session_id != record.canonical_session_id:
                raise ExecutionControlError(
                    "CANONICAL_SESSION_CONFLICT: business task already bound to another session"
                )
            return existing
        self.records[key] = record
        return record

    def resolve(self, parent_gpt_thread_id: str, task_id: str) -> ExecutionOwnerRecord:
        record = self.records.get(self._key(parent_gpt_thread_id, task_id))
        if not record:
            raise ExecutionControlError("EXECUTION_OWNER_NOT_FOUND")
        return record

    def claim(
        self,
        parent_gpt_thread_id: str,
        task_id: str,
        caller_session_id: str,
        *,
        transport: str,
        trigger_gate: TriggerGate,
    ) -> dict:
        trigger_gate.authorize_resume(transport)
        record = self.resolve(parent_gpt_thread_id, task_id)

        if caller_session_id != record.canonical_session_id:
            raise ExecutionControlError(
                "DUPLICATE_EXECUTION_BLOCKED: caller session is not canonical owner"
            )

        if record.state == "RUNNING":
            if record.active_session_id == caller_session_id:
                return {
                    "outcome": "ALREADY_RUNNING_NOOP",
                    "task_id": task_id,
                    "canonical_session_id": record.canonical_session_id,
                    "generation": record.generation,
                }
            raise ExecutionControlError(
                "DUPLICATE_EXECUTION_BLOCKED: another execution owner is RUNNING"
            )

        record.state = "RUNNING"
        record.active_session_id = caller_session_id
        record.generation += 1
        return {
            "outcome": "RESUMED_EXISTING",
            "task_id": task_id,
            "canonical_session_id": record.canonical_session_id,
            "generation": record.generation,
        }

    def release(
        self,
        parent_gpt_thread_id: str,
        task_id: str,
        caller_session_id: str,
    ) -> dict:
        record = self.resolve(parent_gpt_thread_id, task_id)
        if caller_session_id != record.canonical_session_id:
            raise ExecutionControlError(
                "RELEASE_BLOCKED: caller session is not canonical owner"
            )
        if record.state != "RUNNING" or record.active_session_id != caller_session_id:
            return {"outcome": "ALREADY_IDLE_NOOP", "task_id": task_id}
        record.state = "IDLE"
        record.active_session_id = None
        return {
            "outcome": "RELEASED",
            "task_id": task_id,
            "generation": record.generation,
        }
