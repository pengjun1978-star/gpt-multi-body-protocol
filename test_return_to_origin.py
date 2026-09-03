import tempfile, unittest
from return_to_origin import ReturnToOrigin, RecordingTransport

class GateCTest(unittest.TestCase):
    def test_new_thread_and_successor_keep_parent_and_ack_once(self):
        with tempfile.NamedTemporaryFile() as f:
            r=ReturnToOrigin(f.name); r.bind(task_id="t1",parent_gpt_conversation_id="parent-1",origin_route={"kind":"thread","id":"parent-1"},codex_thread_id="new-1",generation=1)
            r.bind(task_id="t2",codex_thread_id="successor-2",generation=2,inherit_task_id="t1")
            e=r.envelope(task_id="t2",status="completed",body="ok",evidence=["test"]); a=RecordingTransport()
            self.assertEqual(r.deliver(e["callback_event_id"],a),"ACCEPTED"); self.assertEqual(a.sent[0]["origin"]["parent_gpt_conversation_id"],"parent-1")
            self.assertEqual(r.deliver(e["callback_event_id"],a),"ACCEPTED"); self.assertEqual(len(a.sent),1); self.assertEqual(r.acknowledge(e["callback_event_id"],"ack-1"),"ACKED")
    def test_unavailable_goes_outbox_then_retries_without_duplicate(self):
        with tempfile.NamedTemporaryFile() as f:
            r=ReturnToOrigin(f.name); r.bind(task_id="t",parent_gpt_conversation_id="p",origin_route={"kind":"thread","id":"p"},codex_thread_id="n")
            e=r.envelope(task_id="t",status="BLOCKED",body="wait"); self.assertEqual(r.deliver(e["callback_event_id"],RecordingTransport(True)),"OUTBOX")
            a=RecordingTransport(); self.assertEqual(r.deliver(e["callback_event_id"],a),"ACCEPTED"); self.assertEqual(len(a.sent),1)
if __name__ == "__main__": unittest.main()
