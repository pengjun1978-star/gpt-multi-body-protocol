"""Persistent single-execution-owner registry for v1.1.

SQLite gives cross-process serialization so separate Codex UI threads on the same
machine cannot concurrently claim the same business task. This complements the
in-memory execution_control guard with a durable control-plane lease.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from execution_control import ExecutionControlError, ExecutionOwnerRecord, TriggerGate


class SQLiteExecutionOwnerRegistry:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_owners (
                    parent_gpt_thread_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    canonical_session_id TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'IDLE',
                    active_session_id TEXT,
                    generation INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (parent_gpt_thread_id, task_id)
                )
                """
            )

    def register_canonical(self, record: ExecutionOwnerRecord) -> dict:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM execution_owners WHERE parent_gpt_thread_id=? AND task_id=?",
                (record.parent_gpt_thread_id, record.task_id),
            ).fetchone()
            if row and row["canonical_session_id"] != record.canonical_session_id:
                raise ExecutionControlError(
                    "CANONICAL_SESSION_CONFLICT: business task already bound to another session"
                )
            if not row:
                conn.execute(
                    """
                    INSERT INTO execution_owners
                    (parent_gpt_thread_id, task_id, canonical_session_id, state, active_session_id, generation)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.parent_gpt_thread_id,
                        record.task_id,
                        record.canonical_session_id,
                        record.state,
                        record.active_session_id,
                        record.generation,
                    ),
                )
            conn.commit()
            return self.snapshot(record.parent_gpt_thread_id, record.task_id)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

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
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM execution_owners WHERE parent_gpt_thread_id=? AND task_id=?",
                (parent_gpt_thread_id, task_id),
            ).fetchone()
            if not row:
                raise ExecutionControlError("EXECUTION_OWNER_NOT_FOUND")
            if caller_session_id != row["canonical_session_id"]:
                raise ExecutionControlError(
                    "DUPLICATE_EXECUTION_BLOCKED: caller session is not canonical owner"
                )
            if row["state"] == "RUNNING":
                if row["active_session_id"] == caller_session_id:
                    conn.commit()
                    return {
                        "outcome": "ALREADY_RUNNING_NOOP",
                        "task_id": task_id,
                        "canonical_session_id": row["canonical_session_id"],
                        "generation": row["generation"],
                    }
                raise ExecutionControlError(
                    "DUPLICATE_EXECUTION_BLOCKED: another execution owner is RUNNING"
                )
            generation = row["generation"] + 1
            conn.execute(
                """
                UPDATE execution_owners
                SET state='RUNNING', active_session_id=?, generation=?
                WHERE parent_gpt_thread_id=? AND task_id=?
                """,
                (caller_session_id, generation, parent_gpt_thread_id, task_id),
            )
            conn.commit()
            return {
                "outcome": "RESUMED_EXISTING",
                "task_id": task_id,
                "canonical_session_id": row["canonical_session_id"],
                "generation": generation,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def release(self, parent_gpt_thread_id: str, task_id: str, caller_session_id: str) -> dict:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM execution_owners WHERE parent_gpt_thread_id=? AND task_id=?",
                (parent_gpt_thread_id, task_id),
            ).fetchone()
            if not row:
                raise ExecutionControlError("EXECUTION_OWNER_NOT_FOUND")
            if caller_session_id != row["canonical_session_id"]:
                raise ExecutionControlError(
                    "RELEASE_BLOCKED: caller session is not canonical owner"
                )
            if row["state"] != "RUNNING" or row["active_session_id"] != caller_session_id:
                conn.commit()
                return {"outcome": "ALREADY_IDLE_NOOP", "task_id": task_id}
            conn.execute(
                """
                UPDATE execution_owners
                SET state='IDLE', active_session_id=NULL
                WHERE parent_gpt_thread_id=? AND task_id=?
                """,
                (parent_gpt_thread_id, task_id),
            )
            conn.commit()
            return {
                "outcome": "RELEASED",
                "task_id": task_id,
                "generation": row["generation"],
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def snapshot(self, parent_gpt_thread_id: str, task_id: str) -> dict:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM execution_owners WHERE parent_gpt_thread_id=? AND task_id=?",
                (parent_gpt_thread_id, task_id),
            ).fetchone()
            if not row:
                raise ExecutionControlError("EXECUTION_OWNER_NOT_FOUND")
            return dict(row)
