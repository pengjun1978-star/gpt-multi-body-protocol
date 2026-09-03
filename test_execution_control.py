import unittest

from execution_control import (
    ExecutionControlError,
    ExecutionOwnerRecord,
    ExecutionOwnerRegistry,
    TriggerGate,
)


class ExecutionControlTests(unittest.TestCase):
    def setUp(self):
        self.parent = "parent-gpt"
        self.task = "v11-mto-foundation-mbp-primary-20260903-001"
        self.canonical = "01a06559-be63-7353-88a2-6ee8d885c83f"
        self.duplicate = "01a06561-4cd0-7db3-9da6-e76fc9a25fec"
        self.registry = ExecutionOwnerRegistry()
        self.registry.register_canonical(
            ExecutionOwnerRecord(self.parent, self.task, self.canonical)
        )
        self.gate = TriggerGate({"native_codex_resume"})

    def test_canonical_session_can_claim_once(self):
        result = self.registry.claim(
            self.parent,
            self.task,
            self.canonical,
            transport="native_codex_resume",
            trigger_gate=self.gate,
        )
        self.assertEqual(result["outcome"], "RESUMED_EXISTING")
        self.assertEqual(result["canonical_session_id"], self.canonical)

    def test_duplicate_ui_session_is_blocked_even_with_same_task_id(self):
        with self.assertRaisesRegex(ExecutionControlError, "DUPLICATE_EXECUTION_BLOCKED"):
            self.registry.claim(
                self.parent,
                self.task,
                self.duplicate,
                transport="native_codex_resume",
                trigger_gate=self.gate,
            )

    def test_duplicate_trigger_on_running_canonical_is_noop(self):
        first = self.registry.claim(
            self.parent,
            self.task,
            self.canonical,
            transport="native_codex_resume",
            trigger_gate=self.gate,
        )
        second = self.registry.claim(
            self.parent,
            self.task,
            self.canonical,
            transport="native_codex_resume",
            trigger_gate=self.gate,
        )
        self.assertEqual(first["generation"], second["generation"])
        self.assertEqual(second["outcome"], "ALREADY_RUNNING_NOOP")

    def test_github_comment_cannot_resume_execution(self):
        with self.assertRaisesRegex(ExecutionControlError, "RESUME_TRANSPORT_BLOCKED"):
            self.registry.claim(
                self.parent,
                self.task,
                self.canonical,
                transport="github_issue_comment",
                trigger_gate=self.gate,
            )

    def test_handoff_create_transport_cannot_resume_execution(self):
        with self.assertRaisesRegex(ExecutionControlError, "RESUME_TRANSPORT_BLOCKED"):
            self.registry.claim(
                self.parent,
                self.task,
                self.canonical,
                transport="local_handoff_create",
                trigger_gate=self.gate,
            )

    def test_release_allows_next_serial_resume_generation(self):
        first = self.registry.claim(
            self.parent,
            self.task,
            self.canonical,
            transport="native_codex_resume",
            trigger_gate=self.gate,
        )
        released = self.registry.release(self.parent, self.task, self.canonical)
        second = self.registry.claim(
            self.parent,
            self.task,
            self.canonical,
            transport="native_codex_resume",
            trigger_gate=self.gate,
        )
        self.assertEqual(released["outcome"], "RELEASED")
        self.assertEqual(second["generation"], first["generation"] + 1)

    def test_canonical_mapping_conflict_is_blocked(self):
        with self.assertRaisesRegex(ExecutionControlError, "CANONICAL_SESSION_CONFLICT"):
            self.registry.register_canonical(
                ExecutionOwnerRecord(self.parent, self.task, self.duplicate)
            )


if __name__ == "__main__":
    unittest.main()
