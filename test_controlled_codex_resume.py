import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from controlled_codex_resume import ControlledCodexResume, ControlledResumeIdentity
from execution_control import ExecutionControlError
from native_codex_transport import CodexResumeResult


PARENT = "6a96e7a6-4d34-83e8-810c-e7195f3dc427"
TASK = "v11-mto-foundation-mbp-primary-20260903-001"
CANON = "01a06559-be63-7353-88a2-6ee8d885c83f"
DUP = "01a06561-4cd0-7db3-9da6-e76fc9a25fec"


class ControlledCodexResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bridge = ControlledCodexResume(Path(self.tmp.name) / "owners.db")
        self.canon = ControlledResumeIdentity(PARENT, TASK, CANON, CANON)
        self.bridge.register(self.canon)

    def tearDown(self):
        self.tmp.cleanup()

    @patch("controlled_codex_resume.resume_exact_session")
    def test_canonical_resumes_exact_existing_session(self, resume):
        resume.return_value = CodexResumeResult(CANON, 0, "ok", "")
        result = self.bridge.resume(self.canon, "continue P0", require_local_session=False)
        self.assertEqual("RESUMED_EXISTING", result["claim"]["outcome"])
        self.assertEqual(CANON, result["resume"].session_id)
        resume.assert_called_once()
        self.assertEqual(CANON, resume.call_args.args[0])

    @patch("controlled_codex_resume.resume_exact_session")
    def test_duplicate_session_never_reaches_codex_cli(self, resume):
        duplicate = ControlledResumeIdentity(PARENT, TASK, CANON, DUP)
        with self.assertRaisesRegex(ExecutionControlError, "DUPLICATE_EXECUTION_BLOCKED"):
            self.bridge.resume(duplicate, "continue P0", require_local_session=False)
        resume.assert_not_called()

    @patch("controlled_codex_resume.resume_exact_session")
    def test_failed_resume_releases_owner_for_retry(self, resume):
        resume.side_effect = RuntimeError("resume failed")
        with self.assertRaises(RuntimeError):
            self.bridge.resume(self.canon, "continue P0", require_local_session=False)
        snap = self.bridge.registry.snapshot(PARENT, TASK)
        self.assertEqual("IDLE", snap["state"])


if __name__ == "__main__":
    unittest.main()
