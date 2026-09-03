"""Persistent single-execution-owner registry for v1.1.

SQLite provides cross-process serialization and a durable execution lease.  A
business task stays RUNNING until explicit completion; a stale generation can
never release a newer owner lease.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from execution_control import ExecutionControlError, ExecutionOwnerRecord, TriggerGate


class SQLiteExecutionOwnerRegistry:
    def __init__(self, db_path: str | Path, lease_seconds: float = 120.0):
        self.db_path = str(db_path)
        self.lease_seconds = float(lease_seconds)
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
                    lease_expires_at REAL,
                    PRIMARY KEY (parent_gpt_thread_id, task_id)
                )
                """
            )
            cols = {row[1] for row in conn.execute("PRAGMA table_info(execution_owners)")}
            if "lease_expires_at" not in cols:
                conn.execute("ALTER TABLE execution_owners ADD COLUMN lease_expires_at REAL")

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
                    (parent_gpt_thread_id, task_id, canonical_session_id, state,
                     active_session_id, generation, lease_expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, NULL)
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
        now: float | None = None,
    ) -> dict:
        trigger_gate.authorize_resume(transport)
        now = time.time() if now is None else float(now)
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

            lease_live = (
                row["state"] == "RUNNING"
                and row["lease_expires_at"] is not None
                and float(row["lease_expires_at"]) > now
            )
            if lease_live:
                conn.commit()
                return {
                    "outcome": "ALREADY_RUNNING_NOOP",
                    "task_id": task_id,
                    "canonical_session_id": row["canonical_session_id"],
                    "generation": row["generation"],
                    "lease_expires_at": row["lease_expires_at"],
                }

            generation = row["generation"] + 1
            lease_expires_at = now + self.lease_seconds
            conn.execute(
                """
                UPDATE execution_owners
                SET state='RUNNING', active_session_id=?, generation=?, lease_expires_at=?
                WHERE parent_gpt_thread_id=? AND task_id=?
                """,
                (
                    caller_session_id,
                    generation,
                    lease_expires_at,
                    parent_gpt_thread_id,
                    task_id,
                ),
            )
            conn.commit()
            return {
                "outcome": "RESUMED_EXISTING",
                "task_id": task_id,
                "canonical_session_id": row["canonical_session_id"],
                "generation": generation,
                "lease_expires_at": lease_expires_at,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def renew(
        self,
        parent_gpt_thread_id: str,
        task_id: str,
        caller_session_id: str,
        generation: int,
        *,
        now: float | None = None,
    ) -> dict:
        now = time.time() if now is None else float(now)
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
                raise ExecutionControlError("RENEW_BLOCKED: caller session is not canonical owner")
            if row["state"] != "RUNNING" or row["active_session_id"] != caller_session_id:
                raise ExecutionControlError("RENEW_BLOCKED: execution is not RUNNING")
            if int(row["generation"]) != int(generation):
                raise ExecutionControlError("STALE_GENERATION_BLOCKED: cannot renew newer execution")
            lease_expires_at = now + self.lease_seconds
            conn.execute(
                "UPDATE execution_owners SET lease_expires_at=? WHERE parent_gpt_thread_id=? AND task_id=?",
                (lease_expires_at, parent_gpt_thread_id, task_id),
            )
            conn.commit()
            return {
                "outcome": "LEASE_RENEWED",
                "task_id": task_id,
                "generation": generation,
                "lease_expires_at": lease_expires_at,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def complete(
        self,
        parent_gpt_thread_id: str,
        task_id: str,
        caller_session_id: str,
        generation: int,
    ) -> dict:
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
                raise ExecutionControlError("RELEASE_BLOCKED: caller session is not canonical owner")
            if int(row["generation"]) != int(generation):
                raise ExecutionControlError("STALE_GENERATION_BLOCKED: cannot release newer execution")
            if row["state"] != "RUNNING" or row["active_session_id"] != caller_session_id:
                conn.commit()
                return {"outcome": "ALREADY_IDLE_NOOP", "task_id": task_id}
            conn.execute(
                """
                UPDATE execution_owners
                SET state='IDLE', active_session_id=NULL, lease_expires_at=NULL
                WHERE parent_gpt_thread_id=? AND task_id=?
                """,
                (parent_gpt_thread_id, task_id),
            )
            conn.commit()
            return {"outcome": "RELEASED", "task_id": task_id, "generation": generation}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def release(self, parent_gpt_thread_id: str, task_id: str, caller_session_id: str) -> dict:
        """Backward-compatible release for older callers; generation-safe callers use complete()."""
        snap = self.snapshot(parent_gpt_thread_id, task_id)
        return self.complete(parent_gpt_thread_id, task_id, caller_session_id, snap["generation"])

    def snapshot(self, parent_gpt_thread_id: str, task_id: str) -> dict:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM execution_owners WHERE parent_gpt_thread_id=? AND task_id=?",
                (parent_gpt_thread_id, task_id),
            ).fetchone()
            if not row:
                raise ExecutionControlError("EXECUTION_OWNER_NOT_FOUND")
            return dict(row)
