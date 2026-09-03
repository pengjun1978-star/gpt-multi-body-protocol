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
        self.entry = ControlledExecutionEntrypoint(Path(self.tmp.name) / "owners.db")
        self.canonical = ExecutionIdentity(PARENT, TASK, CANON, CANON, "native_codex_resume")
        self.entry.register(self.canonical)
        reg = TaskRegistry()
        reg.register(Task("micro", Priority.P1))
        self.scheduler = DeterministicScheduler(reg, [Body("mbp-primary")], dry_run=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_canonical_can_dispatch_once(self):
        seen = []
        result = self.entry.execute(self.canonical, self.scheduler, dispatch=seen.append)
        self.assertEqual("RESUMED_EXISTING", result["claim"]["outcome"])
        self.assertEqual(1, result["dispatch_count"])
        self.assertEqual(1, len(seen))

    def test_duplicate_ui_thread_blocked_before_scheduler(self):
        duplicate = ExecutionIdentity(PARENT, TASK, CANON, DUP, "native_codex_resume")
        with self.assertRaisesRegex(ExecutionControlError, "DUPLICATE_EXECUTION_BLOCKED"):
            self.entry.execute(duplicate, self.scheduler)
        self.assertEqual(0, self.scheduler.bodies[0].active_task_count)

    def test_github_comment_cannot_resume(self):
        bad = ExecutionIdentity(PARENT, TASK, CANON, CANON, "github_issue_comment")
        with self.assertRaises(ExecutionControlError):
            self.entry.execute(bad, self.scheduler)
        self.assertEqual(0, self.scheduler.bodies[0].active_task_count)

    def test_create_handoff_cannot_resume(self):
        bad = ExecutionIdentity(PARENT, TASK, CANON, CANON, "local_handoff_create")
        with self.assertRaises(ExecutionControlError):
            self.entry.execute(bad, self.scheduler)
        self.assertEqual(0, self.scheduler.bodies[0].active_task_count)


if __name__ == "__main__":
    unittest.main()
