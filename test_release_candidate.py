import json, unittest
from pathlib import Path
from router import route
from business_evidence_delivery import build_delivery, confirm_delivery

class ReleaseCandidateRegression(unittest.TestCase):
    def test_router_selects_preferred_and_rejects_mismatch(self):
        registry={"bodies":[
            {"node_id":"mbp-primary","role":"CONTROL","runtime_health":"ONLINE","routing":True,"os":"macos","capabilities":["orchestration"]},
            {"node_id":"office-4090","role":"EXECUTION","runtime_health":"ONLINE","routing":True,"os":"windows","gpu":{"vram_gb":24},"capabilities":["gpu","cuda"]}]}
        d=route(registry,{"requires_gpu":True,"min_vram_gb":23.9,"os":"windows","capabilities":["gpu","cuda"],"preferred_body":"office-4090","fallback_allowed":False})
        self.assertEqual(d.selected_body,"office-4090"); self.assertIn("mbp-primary",d.rejections)
    def test_receipt_and_schema_use_same_contract_states(self):
        root=Path(__file__).parent
        schema=json.loads((root/"schemas/execution-receipt-v2.json").read_text())
        receipt,chunks=build_delivery("rc-task","substantive evidence")
        confirm_delivery(receipt,chunks_sent=len(chunks),sender_confirmed=True)
        self.assertEqual(receipt["status"],"PASS_PENDING_GPT_ACCEPTANCE")
        self.assertIn(receipt["delivery"]["parent_visibility"],("UNVERIFIED","VERIFIED"))
        self.assertIn("business-evidence-delivery-v1",json.dumps(schema))
    def test_failure_paths_are_terminal_and_non_success(self):
        receipt,chunks=build_delivery("rc-fail","evidence")
        confirm_delivery(receipt,chunks_sent=0,sender_confirmed=False,error="parent busy")
        self.assertEqual(receipt["status"],"BLOCKED")

if __name__ == "__main__": unittest.main()
