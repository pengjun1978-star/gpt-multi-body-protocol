import unittest
from task_orchestrator import Body, DeterministicScheduler, Priority, Task, TaskRegistry


class OrchestratorTests(unittest.TestCase):
    def test_priority_dependency_and_dry_run_are_deterministic(self):
        r = TaskRegistry()
        for t in (Task("t2", Priority.P1, ("t1",)), Task("t1", Priority.P2), Task("t5", Priority.P0)):
            r.register(t)
        bodies = [Body("mbp-primary"), Body("mac-studio", state="UNAVAILABLE")]
        result = DeterministicScheduler(r, bodies).schedule()
        self.assertEqual([x["task_id"] for x in result], ["t5", "t2", "t1"])
        self.assertEqual(result[1]["decision"], "WAIT")
        self.assertEqual(result[2]["decision"], "DRY_RUN")

    def test_capability_and_reserved_body_rejection(self):
        r = TaskRegistry(); r.register(Task("gpu", required_capabilities=frozenset({"gpu"})))
        result = DeterministicScheduler(r, [Body("mac-studio", state="UNAVAILABLE")]).schedule()
        self.assertEqual(result[0]["decision"], "REJECT")

    def test_stable_identity_conflict(self):
        r = TaskRegistry(); r.register(Task("same"))
        with self.assertRaises(ValueError): r.register(Task("same", Priority.P0))

    def test_concurrency_and_deterministic_reroute(self):
        r = TaskRegistry(); r.register(Task("t"))
        bodies = [Body("busy", active_task_count=1, max_concurrency=1), Body("backup", max_concurrency=2)]
        scheduler = DeterministicScheduler(r, bodies, dry_run=False)
        self.assertEqual(scheduler.schedule()[0]["body_id"], "backup")
        self.assertEqual(scheduler.retry_or_reroute("t", "busy")["body_id"], "backup")


if __name__ == "__main__": unittest.main()
