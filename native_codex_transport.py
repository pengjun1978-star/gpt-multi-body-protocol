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
import hashlib
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
    before: dict | None = None
    after: dict | None = None

def discover_runtime(codex_home=None, rollout_path=None) -> tuple[str, str]:
    candidates = [Path('/Applications/ChatGPT.app/Contents/Resources/codex'), Path('/opt/homebrew/bin/codex')]
    writer = None
    if rollout_path and Path(rollout_path).exists():
        with Path(rollout_path).open() as f: writer = json.loads(f.readline()).get('payload',{}).get('cli_version')
    for path in candidates:
        if not path.exists(): continue
        version = subprocess.run([str(path), '--version'], capture_output=True, text=True, check=False).stdout.strip().split()[-1]
        if writer and tuple(map(int, version.split('.'))) < tuple(map(int, writer.split('.'))): continue
        return str(path), version
    raise NativeCodexTransportError('CODEX_RUNTIME_TOO_OLD')

def rollout_snapshot(path):
    p=Path(path); data=p.read_bytes(); lines=data.splitlines(keepends=True)
    return {'path':str(p),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'record_count':len(lines),'prefix':data}

def validate_append_only(before, after, session_id):
    if before['path'] != after['path'] or after['bytes'] < before['bytes'] or not after['prefix'].startswith(before['prefix']):
        raise NativeCodexTransportError('CODEX_ROLLOUT_APPEND_ONLY_VIOLATION')
    if session_id not in after['prefix'].decode('utf-8','ignore'):
        raise NativeCodexTransportError('CODEX_SESSION_IDENTITY_DRIFT')


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
    codex_bin: str | None = None,
    codex_home: str | Path | None = None,
    require_local_session: bool = True,
    timeout_seconds: int = 1800,
    extra_exec_args: Iterable[str] = (),
    rollout_path: str | Path | None = None,
) -> CodexResumeResult:
    """Resume exactly one persisted Codex session and reject identity drift."""
    sid = _validate_session_id(session_id)
    if require_local_session and not _session_exists(sid, codex_home):
        raise NativeCodexTransportError("CODEX_SESSION_NOT_FOUND_LOCAL")

    if codex_bin is None:
        codex_bin, _ = discover_runtime(codex_home, rollout_path)
    before = rollout_snapshot(rollout_path) if rollout_path else None
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

    after = rollout_snapshot(rollout_path) if rollout_path else None
    if before and after: validate_append_only(before, after, sid)
    return CodexResumeResult(
        session_id=sid,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        before={k:v for k,v in before.items() if k!='prefix'} if before else None,
        after={k:v for k,v in after.items() if k!='prefix'} if after else None,
    )
