import tempfile, unittest
from pathlib import Path
from business_task_runtime import *

class HotfixTests(unittest.TestCase):
    def setUp(self): self.r=BusinessTaskRuntime(); self.t=self.r.create("bt-1","研发会议安排并邮件发送","th-1","sess-1")
    def test_multistage_one_lineage(self):
        for s in STAGES: self.r.transition("bt-1",s)
        self.assertEqual(len(self.r.tasks),1); self.assertEqual(self.t.canonical_thread,"th-1")
    def test_correction_inherits_identity(self): self.assertEqual(self.r.resolve("附件错了", "bt-1")["business_task_id"],"bt-1")
    def test_resume_unavailable_blocks(self):
        with self.assertRaisesRegex(BusinessTaskError,"CONTINUATION_DISPATCH_BLOCKED"): self.r.resolve("继续发", "missing")
    def test_duplicate_handoff_blocked(self):
        with self.assertRaisesRegex(BusinessTaskError,"DUPLICATE_EXECUTION_BLOCKED"): self.r.dispatch("bt-1","send",thread="th-2")
    def test_artifact_invalidation_blocks_send(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"wrong.md"; p.write_text("wrong"); self.r.materialize("bt-1",p,"1")
            with self.assertRaisesRegex(BusinessTaskError,"BLOCKED_BY_ARTIFACT"): self.r.invalidate_artifact("bt-1")
    def test_replacement_requires_verify_then_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ok.md"; p.write_text("correct"); a=self.r.materialize("bt-1",p,"2"); self.r.set_recipients("bt-1",["a@x"],["b@x"])
            with self.assertRaisesRegex(BusinessTaskError,"BLOCKED_BY_ARTIFACT"): self.r.attachment_gate("bt-1",to=["a@x"],cc=["b@x"])
            a.approved=True; self.assertEqual(self.r.attachment_gate("bt-1",to=["a@x"],cc=["b@x"])["status"],"ATTACHMENT_GATE_PASS")
    def test_recipient_correction_same_task(self): self.r.set_recipients("bt-1",["new@x"]); self.assertEqual(self.r.resolve("抄送改成 new", "bt-1")["business_task_id"],"bt-1")
    def test_new_intent_and_explicit_successor(self): self.assertEqual(self.r.resolve("安排另一场会议")["continuation_or_new"],"NEW")
    def test_real_case_one_task(self):
        for s in ("PREPARE","MATERIALIZE_MD","USER_REVIEW","VERIFY_RECIPIENTS"): self.r.transition("bt-1",s)
        self.assertEqual(self.r.resolve("地址对了，但是 md 文件不是这个", "bt-1")["business_task_id"],"bt-1")
        self.assertEqual(len(self.r.tasks),1)

if __name__ == "__main__": unittest.main()
