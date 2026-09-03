import json, os, platform, socket, subprocess, urllib.request, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
def sh(cmd):
    try: return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=12).strip()
    except Exception as e: return f"unavailable: {e}"
def office_probe():
    host = "100.92.26.11"
    def get(path):
        try:
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(f"http://{host}:11434{path}", timeout=8) as r: return json.load(r)
        except Exception as e: return {"error": str(e)}
    remote = sh(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "office-4090", "nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"])
    models = get("/v1/models")
    gpu_line=next((x for x in remote.splitlines() if "MiB" in x), "")
    vram=re.search(r"(\d+) MiB", gpu_line)
    model_ok="error" not in models and bool(models.get("data") or models.get("models"))
    caps=["gpu","cuda"] + (["local_inference","batch_inference","document_analysis","data_processing"] if model_ok else [])
    return {"hostname":"CHINAMI-UB37H72", "os":"windows", "runtime_health":"ONLINE", "gpu":{"name":gpu_line.split(",")[0].strip(),"vram_gb":round(int(vram.group(1))/1024,2) if vram else None} ,"ssh_probe":remote, "inference_models":models, "capabilities":caps}
def main():
    now=datetime.now(timezone.utc).isoformat()
    reg={"schema":"capability-registry-v1","generated_at":now,"bodies":[
      {"node_id":"mbp-primary","role":"CONTROL","runtime_health":"ONLINE","routing":True,"os":"macos","architecture":platform.machine(),"hostname":socket.gethostname(),"capabilities":["orchestration","lightweight_execution","file_operations"]},
      {"node_id":"office-4090","role":"EXECUTION","routing":True,**office_probe()},
      {"node_id":"mac-studio","role":"RESERVED","runtime_health":"RESERVED","routing":False,"capabilities":[]}]}
    (ROOT/"registry/capability_registry.json").write_text(json.dumps(reg,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(reg,ensure_ascii=False,indent=2))
if __name__ == '__main__': main()
