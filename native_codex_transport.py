"""Exact-session Codex CLI resume transport for v1.1 P0.

Uses the documented non-interactive resume form:
    codex exec --json resume <SESSION_ID> <PROMPT>

The caller must supply the canonical session UUID explicitly.  `--last` and
picker-based resumption are intentionally forbidden because they weaken stable
execution identity.
"""
from __future__ import annotations

import json
import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class NativeCodexTransportError(RuntimeError):
    pass


@dataclass(frozen=True)
class CodexResumeResult:
    session_id: str
    returncode: int
    stdout: str
    stderr: str


def _validate_session_id(session_id: str) -> str:
    try:
        parsed = uuid.UUID(session_id)
    except (ValueError, AttributeError, TypeError) as exc:
        raise NativeCodexTransportError("INVALID_CODEX_SESSION_ID") from exc
    return str(parsed)


def _session_exists(session_id: str, codex_home: str | Path | None = None) -> bool:
    """Best-effort local preflight against Codex's persisted session records."""
    root = Path(codex_home or os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
    sessions = root / "sessions"
    if not sessions.exists():
        return False
    needle = session_id.lower()
    for path in sessions.rglob("*.jsonl"):
        if needle in path.name.lower():
            return True
    return False


def _observed_thread_ids(stdout: str) -> set[str]:
    ids: set[str] = set()
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        for key in ("thread_id", "session_id"):
            value = event.get(key)
            if isinstance(value, str):
                try:
                    ids.add(str(uuid.UUID(value)))
                except ValueError:
                    pass
    return ids


def resume_exact_session(
    session_id: str,
    prompt: str,
    *,
    cwd: str | Path | None = None,
    codex_bin: str = "codex",
    codex_home: str | Path | None = None,
    require_local_session: bool = True,
    timeout_seconds: int = 1800,
    extra_exec_args: Iterable[str] = (),
) -> CodexResumeResult:
    """Resume exactly one persisted Codex session and reject identity drift."""
    sid = _validate_session_id(session_id)
    if require_local_session and not _session_exists(sid, codex_home):
        raise NativeCodexTransportError("CODEX_SESSION_NOT_FOUND_LOCAL")

    command = [
        codex_bin,
        "exec",
        "--json",
        *list(extra_exec_args),
        "resume",
        sid,
        prompt,
    ]
    env = os.environ.copy()
    if codex_home is not None:
        env["CODEX_HOME"] = str(codex_home)

    proc = subprocess.run(
        command,
        cwd=str(cwd) if cwd is not None else None,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if proc.returncode != 0:
        raise NativeCodexTransportError(
            f"CODEX_RESUME_FAILED:{proc.returncode}:{proc.stderr.strip()}"
        )

    observed = _observed_thread_ids(proc.stdout)
    if observed and observed != {sid}:
        raise NativeCodexTransportError(
            f"CODEX_SESSION_IDENTITY_DRIFT: expected={sid} observed={sorted(observed)}"
        )

    return CodexResumeResult(
        session_id=sid,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )
