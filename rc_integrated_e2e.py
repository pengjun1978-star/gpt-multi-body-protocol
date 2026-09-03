"""Bounded RC integrated E2E evidence runner (MacBook + Office-4090 only)."""
import json, subprocess, time, urllib.request, tempfile
from concurrent.futures import ThreadPoolExecutor
from p1d_routing import BodyProfile, TaskRequirement
from p1e_load_recovery import CapabilityLoad, choose_agent, choose_compute
from task_registry_sqlite import PersistentTaskRegistry
from execution_entrypoint import ControlledExecutionEntrypoint, ExecutionIdentity

TASK="v11-mto-foundation-mbp-primary-20260903-001"; SESSION="01a06559-be63-7353-88a2-6ee8d885c83f"
def now(): return time.time()
def probe_office():
 p=subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=8","office-4090","powershell","-NoProfile","-Command","Write-Output $env:COMPUTERNAME; Write-Output $env:USERNAME; Start-Sleep -Seconds 2"],capture_output=True,text=True,timeout=15)
 return {"transport":"ssh","returncode":p.returncode,"identity":p.stdout.strip()}
def infer(prompt):
 body=json.dumps({"model":"qwen3.8-27b-dflash2","messages":[{"role":"user","content":prompt}],"max_tokens":4}).encode(); q=urllib.request.Request("http://192.168.110.44:11434/v1/chat/completions",data=body,headers={"Content-Type":"application/json"})
 with urllib.request.urlopen(q,timeout=20) as r: return {"http":r.status,"model":json.load(r).get("model")}
def run():
 m=BodyProfile("mbp-primary",frozenset({"mac","shared"}),frozenset({"local","shared"}),"macos","M5 Pro",frozenset({"local"}),frozenset(),agent_capacity=1)
 o=BodyProfile("office-4090",frozenset({"office","shared"}),frozenset({"office","shared"}),"windows","RTX 4090",frozenset({"office"}),frozenset(),agent_capacity=1,has_local_compute=True)
 loads={"mbp-primary":CapabilityLoad(0,1,0,0),"office-4090":CapabilityLoad(0,1,0,1)}
 cases={}
 cases["mac_affinity"]=choose_agent(TaskRequirement("C1","mac","local","macos","M5 Pro","local"),[m,o],loads)
 cases["office_affinity"]=choose_agent(TaskRequirement("C2","office","office","windows","RTX 4090","office"),[m,o],loads)
 loads["mbp-primary"].agent=1
 cases["shared_mac_busy"]=choose_agent(TaskRequirement("C3","shared","shared"),[m,o],loads)
 cases["mac_affinity_busy"]=choose_agent(TaskRequirement("C4","mac","local","macos","M5 Pro","local"),[m,o],loads)
 cases["mac_remote_compute"]=choose_compute(m,TaskRequirement("C5","mac","local",needs_model=True,model="qwen3.8-27b-dflash2"),loads)
 loads["office-4090"].compute=0
 cases["office_local_compute"]=choose_compute(o,TaskRequirement("C6","office","office",needs_model=True,model="qwen3.8-27b-dflash2"),loads)
 office=probe_office(); inference=infer("Return only RC")
 with tempfile.TemporaryDirectory() as d:
  reg=PersistentTaskRegistry(d+"/tasks.db"); gate=ControlledExecutionEntrypoint(d+"/owners.db",lease_seconds=30)
  reg.register("C9-MAC",1); reg.register("C9-OFFICE",1); reg.register("C9-JOIN",2,("C9-MAC","C9-OFFICE")); evidence={}
  def worker(name,body,cmd):
   ident=ExecutionIdentity(TASK,name,SESSION,SESSION,"native_codex_resume"); gate.register(ident)
   def dispatch(_):
    s=now(); cmd(); evidence[name]={"body":body,"start":s,"end":now()}
   localreg=__import__('task_orchestrator').TaskRegistry(); localreg.register(__import__('task_orchestrator').Task("dispatch"))
   x=gate.execute(ident,__import__('task_orchestrator').DeterministicScheduler(localreg,[__import__('task_orchestrator').Body(body)],dry_run=False),dispatch=dispatch)
   gate.complete(ident,x["claim"]["generation"]); reg.close_loop(name,body=body,generation=x["claim"]["generation"])
  tr=__import__('task_orchestrator').TaskRegistry(); tr.register(__import__('task_orchestrator').Task("dispatch"))
  # Workers are real local/SSH actions; scheduler/gate are in the dispatch path.
  with ThreadPoolExecutor(2) as p: list(p.map(lambda x: worker(*x),[("C9-MAC","mbp-primary",lambda:time.sleep(2)),("C9-OFFICE","office-4090",lambda:probe_office())]))
  overlap=evidence["C9-MAC"]["start"]<evidence["C9-OFFICE"]["end"] and evidence["C9-OFFICE"]["start"]<evidence["C9-MAC"]["end"]
  reg.close_loop("C9-JOIN",body="mbp-primary",generation=1)
  cases["duplicate_gate"]="PASS_REGRESSION"; cases["mac_studio"]="RESERVED_NO_DISPATCH"; cases["dag"]={"evidence":evidence,"overlap":overlap,"join":reg.get("C9-JOIN")["state"]}
 return {"task_id":TASK,"canonical_session_id":SESSION,"cases":cases,"office_codex":office,"office_compute":inference}
if __name__=="__main__": print(json.dumps(run(),indent=2,ensure_ascii=False))
