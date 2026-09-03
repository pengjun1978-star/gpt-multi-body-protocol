import tempfile
import unittest
from pathlib import Path
from task_registry_sqlite import PersistentTaskRegistry


class PersistentRegistryTests(unittest.TestCase):
    def test_lifecycle_survives_reopen_and_preserves_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "tasks.db"
            r = PersistentTaskRegistry(p); r.register("t1", 1, ("t0",))
            r.transition("t1", "READY"); r.transition("t1", "RUNNING", body="mbp-primary", generation=3)
            r2 = PersistentTaskRegistry(p)
            row = r2.get("t1")
            self.assertEqual((row["state"], row["assigned_body"], row["generation"]), ("RUNNING", "mbp-primary", 3))
            self.assertEqual([x["task_id"] for x in r2.recoverable()], ["t1"])

    def test_invalid_transition_and_identity_conflict_are_blocked(self):
        r = PersistentTaskRegistry(":memory:"); r.register("t1")
        with self.assertRaisesRegex(ValueError, "INVALID_TRANSITION"): r.transition("t1", "ACCEPTED")
        with self.assertRaisesRegex(ValueError, "TASK_ID_CONFLICT"): r.register("t1", 0)

    def test_receipt_callback_ack_fields_are_persisted(self):
        r = PersistentTaskRegistry(":memory:"); r.register("t1")
        r.transition("t1", "READY"); r.transition("t1", "RUNNING")
        r.transition("t1", "RESULT_READY", receipt_status="READY")
        r.transition("t1", "WAITING_GPT_ACCEPTANCE", callback_status="DELIVERED")
        row = r.transition("t1", "ACCEPTED", ack_status="ACKED")
        self.assertEqual((row["receipt_status"], row["callback_status"], row["ack_status"]), ("READY", "DELIVERED", "ACKED"))
