import tempfile, unittest
from pathlib import Path
from automatic_callback import CallbackQueue, SENT, VERIFIED, ESCALATED

class AutomaticCallbackTests(unittest.TestCase):
    def test_busy_retry_then_ack_without_user_trigger(self):
        with tempfile.TemporaryDirectory() as d:
            q=CallbackQueue(Path(d)/"queue.jsonl"); calls=[]
            item=q.enqueue(task_id="t", parent_gpt_thread_id="p", event_id="e", payload={"evidence":"substantive"})
            def sender(parent, payload):
                calls.append((parent,payload))
                if len(calls)==1: raise RuntimeError("parent responding")
            q.retry(sender, now=0); q.retry(sender, now=0.9); q.retry(sender, now=1.1)
            self.assertEqual(item["status"], SENT); self.assertEqual(len(calls), 2)
            self.assertEqual(q.acknowledge(item["idempotency_key"], ack_id="ack-1")["status"], VERIFIED)
            self.assertEqual(CallbackQueue(Path(d)/"queue.jsonl").items[item["idempotency_key"]]["status"], VERIFIED)
    def test_duplicate_enqueue_and_escalation(self):
        with tempfile.TemporaryDirectory() as d:
            q=CallbackQueue(Path(d)/"q.jsonl")
            a=q.enqueue(task_id="t", parent_gpt_thread_id="p", event_id="e", payload={"x":1}, max_attempts=2)
            b=q.enqueue(task_id="t", parent_gpt_thread_id="p", event_id="e", payload={"x":1}, max_attempts=2)
            self.assertIs(a,b)
            def busy(*_): raise RuntimeError("busy")
            q.retry(busy, now=0); q.retry(busy, now=1)
            self.assertEqual(a["status"], ESCALATED)

if __name__ == "__main__": unittest.main()
