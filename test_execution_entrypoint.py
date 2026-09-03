import tempfile
import unittest
from pathlib import Path

from execution_control import ExecutionControlError
from execution_entrypoint import ControlledExecutionEntrypoint, ExecutionIdentity
from task_orchestrator import Body, DeterministicScheduler, Priority, Task, TaskRegistry


PARENT = "6a96e7a6-4d34-83e8-810c-e7195f3dc427"
TASK = "v11-mto-foundation-mbp-primary-20260903-001"
CANON = "01a06559-be63-7353-88a2-6ee8d885c83f"
DUP = "01a06561-4cd0-7db3-9da6-e76fc9a25fec"


class EntrypointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.entry = ControlledExecutionEntrypoint(Path(self.tmp.name) / "owners.db", lease_seconds=10)
        self.canonical = ExecutionIdentity(PARENT, TASK, CANON, CANON, "native_codex_resume")
        self.entry.register(self.canonical)
        reg = TaskRegistry()
        reg.register(Task("micro", Priority.P1))
        self.scheduler = DeterministicScheduler(reg, [Body("mbp-primary")], dry_run=False)

    def tearDown(self):
        self.tmp.cleanup()

    def fresh_scheduler(self):
        reg = TaskRegistry(); reg.register(Task("micro", Priority.P1))
        return DeterministicScheduler(reg, [Body("mbp-primary")], dry_run=False)

    def test_lease_stays_running_until_explicit_completion(self):
        seen = []
        result = self.entry.execute(self.canonical, self.scheduler, dispatch=seen.append, now=100)
        self.assertEqual("RESUMED_EXISTING", result["claim"]["outcome"])
        generation = result["claim"]["generation"]
        snap = self.entry.registry.snapshot(PARENT, TASK)
        self.assertEqual("RUNNING", snap["state"])
        self.assertEqual(CANON, snap["active_session_id"])
        second = self.entry.execute(self.canonical, self.fresh_scheduler(), now=101)
        self.assertEqual("ALREADY_RUNNING_NOOP", second["claim"]["outcome"])
        self.assertEqual(0, second["dispatch_count"])
        done = self.entry.complete(self.canonical, generation)
        self.assertEqual("RELEASED", done["outcome"])
        self.assertEqual("IDLE", self.entry.registry.snapshot(PARENT, TASK)["state"])

    def test_duplicate_ui_thread_blocked_before_scheduler(self):
        duplicate = ExecutionIdentity(PARENT, TASK, CANON, DUP, "native_codex_resume")
        with self.assertRaisesRegex(ExecutionControlError, "DUPLICATE_EXECUTION_BLOCKED"):
            self.entry.execute(duplicate, self.scheduler, now=100)
        self.assertEqual(0, self.scheduler.bodies[0].active_task_count)

    def test_github_and_create_handoff_cannot_resume(self):
        for transport in ("github_issue_comment", "local_handoff_create"):
            bad = ExecutionIdentity(PARENT, TASK, CANON, CANON, transport)
            with self.subTest(transport=transport):
                with self.assertRaisesRegex(ExecutionControlError, "RESUME_TRANSPORT_BLOCKED"):
                    self.entry.execute(bad, self.fresh_scheduler(), now=100)

    def test_expired_lease_allows_new_generation_but_stale_completion_is_blocked(self):
        first = self.entry.execute(self.canonical, self.scheduler, now=100)
        g1 = first["claim"]["generation"]
        second = self.entry.execute(self.canonical, self.fresh_scheduler(), now=111)
        g2 = second["claim"]["generation"]
        self.assertEqual(g1 + 1, g2)
        with self.assertRaisesRegex(ExecutionControlError, "STALE_GENERATION_BLOCKED"):
            self.entry.complete(self.canonical, g1)
        self.assertEqual("RUNNING", self.entry.registry.snapshot(PARENT, TASK)["state"])
        self.entry.complete(self.canonical, g2)

    def test_renew_extends_active_generation(self):
        first = self.entry.execute(self.canonical, self.scheduler, now=100)
        generation = first["claim"]["generation"]
        renewed = self.entry.renew(self.canonical, generation, now=105)
        self.assertEqual("LEASE_RENEWED", renewed["outcome"])
        second = self.entry.execute(self.canonical, self.fresh_scheduler(), now=111)
        self.assertEqual("ALREADY_RUNNING_NOOP", second["claim"]["outcome"])


if __name__ == "__main__":
    unittest.main()
