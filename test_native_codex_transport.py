import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from native_codex_transport import (
    NativeCodexTransportError,
    _session_exists,
    resume_exact_session,
)


CANON = "01a06559-be63-7353-88a2-6ee8d885c83f"
OTHER = "01a06561-4cd0-7db3-9da6-e76fc9a25fec"


class Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class NativeCodexTransportTests(unittest.TestCase):
    def test_session_preflight_finds_exact_rollout(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sessions" / "2026" / "09" / "03"
            p.mkdir(parents=True)
            (p / f"rollout-2026-09-03T00-00-00-{CANON}.jsonl").write_text("{}")
            self.assertTrue(_session_exists(CANON, td))
            self.assertFalse(_session_exists(OTHER, td))

    @patch("native_codex_transport.subprocess.run")
    def test_exact_noninteractive_resume_command(self, run):
        run.return_value = Proc(stdout='{"thread_id":"%s"}\n' % CANON)
        result = resume_exact_session(CANON, "continue P0", require_local_session=False)
        self.assertEqual(CANON, result.session_id)
        command = run.call_args.args[0]
        self.assertEqual(
            ["codex", "exec", "--json", "resume", CANON, "continue P0"],
            command,
        )
        self.assertNotIn("--last", command)

    @patch("native_codex_transport.subprocess.run")
    def test_identity_drift_is_blocked(self, run):
        run.return_value = Proc(stdout='{"thread_id":"%s"}\n' % OTHER)
        with self.assertRaisesRegex(NativeCodexTransportError, "CODEX_SESSION_IDENTITY_DRIFT"):
            resume_exact_session(CANON, "continue", require_local_session=False)

    @patch("native_codex_transport.subprocess.run")
    def test_failed_resume_is_not_treated_as_success(self, run):
        run.return_value = Proc(returncode=1, stderr="thread not found")
        with self.assertRaisesRegex(NativeCodexTransportError, "CODEX_RESUME_FAILED"):
            resume_exact_session(CANON, "continue", require_local_session=False)

    def test_invalid_session_id_rejected_before_execution(self):
        with self.assertRaisesRegex(NativeCodexTransportError, "INVALID_CODEX_SESSION_ID"):
            resume_exact_session("last", "continue", require_local_session=False)


if __name__ == "__main__":
    unittest.main()
