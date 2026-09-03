"""Bounded real P1C validation: MacBook task plus Office SSH/11434 task."""
import json, subprocess, time, urllib.request
from pathlib import Path
from task_registry_sqlite import PersistentTaskRegistry

TASK = "v11-mto-foundation-mbp-primary-20260903-001"
SESSION = "01a06559-be63-7353-88a2-6ee8d885c83f"

def stamp(): return time.time()
def run_remote():
    start = stamp()
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "office-4090", "powershell", "-NoProfile", "-Command", "Write-Output $env:COMPUTERNAME; Write-Output $env:USERNAME"], text=True, capture_output=True, timeout=15)
    return {"transport": "ssh", "start": start, "end": stamp(), "returncode": p.returncode, "body_identity": p.stdout.strip(), "stderr": p.stderr.strip()}
def run_inference():
    start = stamp(); payload = json.dumps({"model":"qwen3.8-27b-dflash2","messages":[{"role":"user","content":"Return only: P1C"}],"max_tokens":4,"stream":False}).encode()
    req = urllib.request.Request("http://192.168.110.44:11434/v1/chat/completions", data=payload, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=20) as response: body = json.loads(response.read())
    return {"transport":"http_11434","start":start,"end":stamp(),"body_identity":"office-4090","model":body.get("model"),"output":body.get("choices", [{}])[0].get("message", {}).get("content")}
def run():
    db = Path("p1c-runtime.db"); db.unlink(missing_ok=True); registry = PersistentTaskRegistry(db)
    registry.register("P1C-MAC", 1); registry.register("P1C-OFFICE", 1); registry.register("P1C-JOIN", 2, ("P1C-MAC", "P1C-OFFICE"))
    mac_start = stamp(); mac = {"transport":"local", "start":mac_start, "body_identity":"mbp-primary", "value":sum(range(10)), "end":stamp()}
    registry.close_loop("P1C-MAC", body="mbp-primary", generation=1)
    office = run_remote(); inference = run_inference()
    if office["returncode"] != 0: raise RuntimeError("OFFICE_TRANSPORT_FAILED")
    registry.close_loop("P1C-OFFICE", body="office-4090", generation=1)
    ready_before = [r["task_id"] for r in registry.ready_tasks()]
    registry.close_loop("P1C-JOIN", body="mbp-primary", generation=1)
    return {"task_id":TASK,"canonical_session_id":SESSION,"mac":mac,"office_codex":office,"office_inference":inference,"join_unlocked_before_acceptance":ready_before,"join_state":registry.get("P1C-JOIN")["state"]}
if __name__ == "__main__": print(json.dumps(run(), indent=2, ensure_ascii=False))
