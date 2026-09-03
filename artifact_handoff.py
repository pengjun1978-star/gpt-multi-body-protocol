"""Verified GPT Work -> Codex artifact handoff primitives (v1.1.1)."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Manifest:
    artifact_name: str; encoding: str; bytes: int; sha256: str; first_marker: str; last_marker: str; required_markers: tuple[str, ...]
class HandoffError(ValueError): pass
def build_manifest(path: Path, *, first_marker: str, last_marker: str, required_markers: tuple[str, ...] = ()) -> Manifest:
    raw=path.read_bytes(); text=raw.decode('utf-8')
    if not text.startswith(first_marker): raise HandoffError('FIRST_MARKER_MISMATCH')
    if not text.endswith(last_marker): raise HandoffError('LAST_MARKER_MISMATCH')
    missing=[m for m in required_markers if m not in text]
    if missing: raise HandoffError('REQUIRED_MARKER_MISSING:'+','.join(missing))
    return Manifest(path.name,'utf-8',len(raw),hashlib.sha256(raw).hexdigest(),first_marker,last_marker,required_markers)
class TransportProvider:
    name='abstract'
    def stage(self, source: Path, staging: Path) -> Path: raise NotImplementedError
class ManualDownloadProvider(TransportProvider):
    name='manual-download'
    def stage(self, source: Path, staging: Path) -> Path:
        staging.mkdir(parents=True,exist_ok=True); target=staging/source.name; target.write_bytes(source.read_bytes()); return target
def consume(source: Path, target: Path, manifest: Manifest) -> dict:
    raw=source.read_bytes()
    if len(raw)!=manifest.bytes: raise HandoffError('BYTES_MISMATCH')
    if hashlib.sha256(raw).hexdigest()!=manifest.sha256: raise HandoffError('SHA256_MISMATCH')
    raw.decode(manifest.encoding); target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
    if target.read_bytes()!=raw: raise HandoffError('PERSISTENCE_MISMATCH')
    return {'status':'CONSUMED','manifest':asdict(manifest),'target':str(target)}
def write_receipt(path: Path, receipt: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
