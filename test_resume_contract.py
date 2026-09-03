import unittest
from resume_contract import ResumeError, ResumeRecord, ResumeRegistry

class ResumeContractTests(unittest.TestCase):
    def setUp(self):
        self.r = ResumeRegistry()
        self.kw = dict(codex_thread_session_id="thread-1", body_node_id="mbp-primary",
                       project_worktree="/work/case", created_at="2026-09-03T00:00:00Z")
        self.r.register(ResumeRecord("parent-1", "task-1", **self.kw))

    def test_two_resumes_keep_identifier(self):
        a = self.r.resume("parent-1", "task-1", "mbp-primary")
        b = self.r.resume("parent-1", "task-1", "mbp-primary")
        self.assertEqual(a["outcome"], "RESUMED_EXISTING")
        self.assertEqual(a["record"]["codex_thread_session_id"], b["record"]["codex_thread_session_id"])
        self.assertEqual(a["record"]["codex_task_id"], b["record"]["codex_task_id"])

    def test_create_requires_explicit_new_and_guard_rejects_duplicate(self):
        with self.assertRaises(ResumeError):
            self.r.create("parent-1", "task-1", explicit_new=False, **self.kw)
        with self.assertRaises(ResumeError):
            self.r.create("parent-1", "task-1", explicit_new=True, **self.kw)

    def test_explicit_new_generates_new_identifier(self):
        result = self.r.create("parent-2", "task-2", explicit_new=True,
            codex_thread_session_id="thread-2", body_node_id="mbp-primary",
            project_worktree="/work/new", created_at="2026-09-03T00:00:00Z")
        self.assertEqual(result["outcome"], "CREATED_NEW")
        self.assertNotEqual(result["record"]["codex_thread_session_id"], "thread-1")

    def test_missing_mapping_blocks_without_create(self):
        with self.assertRaisesRegex(ResumeError, "RESUME_FAILED/BLOCKED"):
            self.r.resume("parent-missing", "task-missing", "mbp-primary")

if __name__ == "__main__": unittest.main()
