import tempfile
import unittest
from pathlib import Path

from execution_control import ExecutionControlError, ExecutionOwnerRecord, TriggerGate
from execution_control_sqlite import SQLiteExecutionOwnerRegistry


class SQLiteExecutionOwnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "execution-control.db"
        self.parent = "parent-gpt"
        self.task = "v11-mto-foundation-mbp-primary-20260903-001"
        self.canonical = "01a06559-be63-7353-88a2-6ee8d885c83f"
        self.duplicate = "01a06561-4cd0-7db3-9da6-e76fc9a25fec"
        self.gate = TriggerGate({"native_codex_resume"})
        self.a = SQLiteExecutionOwnerRegistry(self.db, lease_seconds=10)
        self.b = SQLiteExecutionOwnerRegistry(self.db, lease_seconds=10)
        self.a.register_canonical(ExecutionOwnerRecord(self.parent, self.task, self.canonical))

    def tearDown(self):
        self.tmp.cleanup()

    def claim(self, registry, session=None, now=100):
        return registry.claim(
            self.parent, self.task, session or self.canonical,
            transport="native_codex_resume", trigger_gate=self.gate, now=now,
        )

    def test_two_process_views_share_single_running_owner(self):
        first = self.claim(self.a)
        self.assertEqual(first["outcome"], "RESUMED_EXISTING")
        with self.assertRaisesRegex(ExecutionControlError, "DUPLICATE_EXECUTION_BLOCKED"):
            self.claim(self.b, self.duplicate, now=101)
        snap = self.b.snapshot(self.parent, self.task)
        self.assertEqual(snap["active_session_id"], self.canonical)
        self.assertEqual(snap["state"], "RUNNING")

    def test_same_canonical_duplicate_trigger_is_noop_across_instances(self):
        first = self.claim(self.a)
        second = self.claim(self.b, now=101)
        self.assertEqual(second["outcome"], "ALREADY_RUNNING_NOOP")
        self.assertEqual(second["generation"], first["generation"])

    def test_complete_then_resume_increments_generation(self):
        first = self.claim(self.a)
        self.b.complete(self.parent, self.task, self.canonical, first["generation"])
        second = self.claim(self.a, now=101)
        self.assertEqual(second["generation"], first["generation"] + 1)

    def test_expired_lease_reclaims_and_stale_completion_cannot_release_new_owner(self):
        first = self.claim(self.a, now=100)
        second = self.claim(self.b, now=111)
        self.assertEqual(second["generation"], first["generation"] + 1)
        with self.assertRaisesRegex(ExecutionControlError, "STALE_GENERATION_BLOCKED"):
            self.a.complete(self.parent, self.task, self.canonical, first["generation"])
        self.assertEqual(self.a.snapshot(self.parent, self.task)["state"], "RUNNING")

    def test_renew_keeps_generation_live(self):
        first = self.claim(self.a, now=100)
        renewed = self.b.renew(self.parent, self.task, self.canonical, first["generation"], now=105)
        self.assertEqual(renewed["outcome"], "LEASE_RENEWED")
        second = self.claim(self.a, now=111)
        self.assertEqual(second["outcome"], "ALREADY_RUNNING_NOOP")

    def test_create_only_and_github_transports_stay_blocked(self):
        for transport in ("local_handoff_create", "github_issue_comment"):
            with self.subTest(transport=transport):
                with self.assertRaisesRegex(ExecutionControlError, "RESUME_TRANSPORT_BLOCKED"):
                    self.a.claim(
                        self.parent, self.task, self.canonical,
                        transport=transport, trigger_gate=self.gate, now=100,
                    )


if __name__ == "__main__":
    unittest.main()
