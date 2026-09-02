#!/usr/bin/env python3
import json, platform, socket, subprocess

def identify(registry_path):
    hostname = socket.gethostname()
    info = {"hostname": hostname, "os": platform.system(), "platform": platform.platform(),
            "cpu_architecture": platform.machine(), "cpu": platform.processor(),
            "gpu": "unknown (read-only probe unavailable)"}
    try:
        info["gpu"] = subprocess.check_output(["system_profiler", "SPDisplaysDataType"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception: pass
    registry = json.load(open(registry_path, encoding="utf-8"))
    matches = [n for n in registry.get("nodes", []) if n.get("hostname") == hostname]
    if len(matches) != 1:
        raise SystemExit(json.dumps({"status":"BODY_MISMATCH","identity":info,"matches":matches}, ensure_ascii=False))
    info.update({"node_id": matches[0]["id"], "registry_identity": matches[0], "source_hardware": matches[0]["name"]})
    return info

if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("registry"); print(json.dumps(identify(p.parse_args().registry), ensure_ascii=False, indent=2))
