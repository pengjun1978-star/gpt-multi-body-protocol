import json
from datetime import datetime, timezone
from pathlib import Path
from discover import main
from router import route

ROOT=Path(__file__).parent
main()
registry=json.loads((ROOT/'registry/capability_registry.json').read_text())
req={"task_type":"office_4090_ai_compute_capability_discovery","requires_gpu":True,"min_vram_gb":23.9,"os":"windows","capabilities":["gpu","cuda"],"data_locality":"office-4090","preferred_body":"office-4090","fallback_allowed":False}
d=route(registry,req)
receipt={"receipt_schema":"business-receipt-v1","status":"completed" if d.selected_body=="office-4090" else "failed","acceptance_status":"PASS_PENDING_GPT_ACCEPTANCE","created_at":datetime.now(timezone.utc).isoformat(),"task_requirement":req,"routing":{"selected_body":d.selected_body,"candidates":d.candidates,"rejection_reasons":d.rejections,"fallback":d.fallback},"discovery":next((b for b in registry['bodies'] if b['node_id']=='office-4090'),None),"side_effects":"NONE","notes":"Read-only discovery; no installation, upgrade, deletion, switching, or service mutation."}
(ROOT/'receipts/office-4090-capability-discovery.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(receipt,ensure_ascii=False,indent=2))
