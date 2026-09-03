"""Bounded real P1C validation: MacBook task plus Office SSH/11434 task."""
import json, subprocess, time, urllib.request, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from execution_entrypoint import ControlledExecutionEntrypoint, ExecutionIdentity
from task_orchestrator import Body, DeterministicScheduler, Task, TaskRegistry
from task_registry_sqlite import PersistentTaskRegistry

TASK = "v11-mto-foundation-mbp-primary-20260903-001"
SESSION = "01a06559-be63-7353-88a2-6ee8d885c83f"

def stamp(): return time.time()
def run_remote():
    start = stamp()
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "office-4090", "powershell", "-NoProfile", "-Command", "Write-Output $env:COMPUTERNAME; Write-Output $env:USERNAME; Start-Sleep -Seconds 2"], text=True, capture_output=True, timeout=15)
    return {"transport": "ssh", "start": start, "end": stamp(), "returncode": p.returncode, "body_identity": p.stdout.strip(), "stderr": p.stderr.strip()}
def run_inference():
    start = stamp(); payload = json.dumps({"model":"qwen3.8-27b-dflash2","messages":[{"role":"user","content":"Return only: P1C"}],"max_tokens":4,"stream":False}).encode()
    req = urllib.request.Request("http://192.168.110.44:11434/v1/chat/completions", data=payload, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=20) as response: body = json.loads(response.read())
    return {"transport":"http_11434","start":start,"end":stamp(),"body_identity":"office-4090","model":body.get("model"),"output":body.get("choices", [{}])[0].get("message", {}).get("content")}
def run():
    with tempfile.TemporaryDirectory() as d:
        registry = PersistentTaskRegistry(Path(d) / "tasks.db")
        registry.register("P1C-MAC", 1); registry.register("P1C-OFFICE", 1); registry.register("P1C-JOIN", 2, ("P1C-MAC", "P1C-OFFICE"))
        taskreg = TaskRegistry(); taskreg.register(Task("dispatch", required_capabilities=frozenset()))
        gate = ControlledExecutionEntrypoint(Path(d) / "owners.db", lease_seconds=30)
        evidence = {}
        def local():
            identity = ExecutionIdentity(TASK, "P1C-MAC", SESSION, SESSION, "native_codex_resume"); gate.register(identity)
            def work(_):
                start = stamp(); time.sleep(2); evidence["mac"]={"transport":"local", "start":start,"end":stamp(),"body_identity":"mbp-primary","value":sum(range(10))}
            result = gate.execute(identity, DeterministicScheduler(taskreg, [Body("mbp-primary")], dry_run=False), dispatch=work); registry.close_loop("P1C-MAC", body="mbp-primary", generation=result["claim"]["generation"]); gate.complete(identity, result["claim"]["generation"]); return result
        def office_work():
            identity = ExecutionIdentity(TASK, "P1C-OFFICE", SESSION, SESSION, "native_codex_resume"); gate.register(identity)
            def work(_): evidence["office"]={"codex":run_remote(), "inference":run_inference()}
            result = gate.execute(identity, DeterministicScheduler(taskreg, [Body("office-4090")], dry_run=False), dispatch=work); registry.close_loop("P1C-OFFICE", body="office-4090", generation=result["claim"]["generation"]); gate.complete(identity, result["claim"]["generation"]); return result
        with ThreadPoolExecutor(max_workers=2) as pool:
            mac_result, office_result = pool.map(lambda fn: fn(), (local, office_work))
        registry.close_loop("P1C-JOIN", body="mbp-primary", generation=1)
        mac, office = evidence["mac"], evidence["office"]
        overlap = mac["start"] < office["codex"]["end"] and office["codex"]["start"] < mac["end"]
        if not overlap or office["codex"]["returncode"] != 0: raise RuntimeError("REAL_OVERLAP_OR_OFFICE_FAILED")
        return {"task_id":TASK,"canonical_session_id":SESSION,"dispatch_mode":"REAL_PARALLEL","mac":mac,"office":office,"overlap":overlap,"join_state":registry.get("P1C-JOIN")["state"]}
if __name__ == "__main__": print(json.dumps(run(), indent=2, ensure_ascii=False))
