import tempfile, unittest
from ack_return_channel import AckReturnChannel, GPT_ACKED, OUTBOX
from task_registry_sqlite import PersistentTaskRegistry

class AckReturnTests(unittest.TestCase):
    def test_e2e_identity_idempotency_and_outbox(self):
        with tempfile.TemporaryDirectory() as d:
            reg=PersistentTaskRegistry(d+"/tasks.db"); reg.register("t1"); reg.transition("t1","READY"); reg.transition("t1","RUNNING",body="mbp",generation=3); reg.transition("t1","RESULT_READY"); reg.transition("t1","WAITING_GPT_ACCEPTANCE")
            ch=AckReturnChannel(d+"/acks.db"); route={"kind":"parent_gpt","id":"p1"}
            ch.create(callback_event_id="cb-1",task_id="t1",execution_generation=3,parent_route=route,ack_id="gpt-ack-1")
            self.assertEqual(ch.deliver("cb-1",reg,task_id="t1",execution_generation=3,parent_route=route),GPT_ACKED)
            self.assertEqual(ch.deliver("cb-1",reg,task_id="t1",execution_generation=3,parent_route=route),GPT_ACKED)
            self.assertEqual(reg.get("t1")["ack_status"],GPT_ACKED)
            with self.assertRaises(ValueError): ch.deliver("cb-1",reg,task_id="wrong",execution_generation=3,parent_route=route)

    def test_successor_generation_and_route_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            reg=PersistentTaskRegistry(d+"/tasks.db"); reg.register("t2"); reg.transition("t2","READY"); reg.transition("t2","RUNNING",body="resume",generation=7); reg.transition("t2","RESULT_READY"); reg.transition("t2","WAITING_GPT_ACCEPTANCE")
            ch=AckReturnChannel(d+"/acks.db"); route={"kind":"parent_gpt","id":"p2"}; ch.create(callback_event_id="cb-2",task_id="t2",execution_generation=7,parent_route=route,ack_id="a2")
            self.assertEqual(ch.deliver("cb-2",reg,task_id="t2",execution_generation=7,parent_route=route),GPT_ACKED)
            self.assertEqual(reg.get("t2")["ack_generation"],7)
            with self.assertRaises(ValueError): ch.deliver("cb-2",reg,task_id="t2",execution_generation=8,parent_route=route)
