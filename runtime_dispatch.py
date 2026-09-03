"""v1.1.1 runtime affinity and explicit cloud-work dispatch guard."""
from dataclasses import dataclass
DIRECT_CLOUD_WORK="DIRECT_CLOUD_WORK"
LOCAL_BRIDGED_CLOUD_WORK="LOCAL_BRIDGED_CLOUD_WORK"
class RuntimeDispatchError(RuntimeError): pass
@dataclass(frozen=True)
class DispatchRequest:
    task_id: str
    requested_runtime: str | None = None
    cloud_artifact: bool = False
    explicit_fallback: str | None = None
def select_runtime(req, *, cloud_available=True):
    cloud=req.requested_runtime in {"GPT Work Cloud","GPT Work","cloud"} or req.cloud_artifact
    if cloud:
        if cloud_available: return {"runtime":"GPT_WORK_CLOUD","work_type":DIRECT_CLOUD_WORK,"affinity":"STRONG"}
        if req.explicit_fallback=="local_bridge": return {"runtime":"LOCAL_CODEX","work_type":LOCAL_BRIDGED_CLOUD_WORK,"affinity":"EXPLICIT_FALLBACK","lineage":"local_bridge"}
        raise RuntimeDispatchError("DIRECT_CLOUD_WORK_UNAVAILABLE/CLOUD_RUNTIME_UNAVAILABLE")
    if req.requested_runtime is None: raise RuntimeDispatchError("RUNTIME_AFFINITY_REQUIRED")
    return {"runtime":req.requested_runtime,"work_type":"LOCAL_EXECUTION"}
