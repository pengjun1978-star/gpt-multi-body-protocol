import unittest
from mandatory_return import require_parent_return, MandatoryReturnError
from resume_contract import ResumeRegistry, ResumeRecord, ResumeError

class RuleTests(unittest.TestCase):
    def test_all_terminal_states_require_parent_callback(self):
        for state in ("COMPLETED", "PARTIAL", "BLOCKED", "FAILED", "CANCELLED"):
            self.assertEqual(require_parent_return(status=state,parent_route={"id":"p"},callback_event_id="cb",sender=lambda *x:"HOST_ACCEPTED"),"HOST_ACCEPTED")
        with self.assertRaises(MandatoryReturnError): require_parent_return(status="FAILED",parent_route={},callback_event_id="cb",sender=lambda *x:"SENT")

    def test_continuation_exact_session_and_no_create(self):
        r=ResumeRegistry(); rec=ResumeRecord("p","t","session-1","mbp","/w","now") ; r.register(rec)
        self.assertEqual(r.continue_task("p","t",canonical_session_id="session-1",body_node_id="mbp")["outcome"],"RESUMED_EXISTING")
        with self.assertRaisesRegex(ResumeError,"canonical session unavailable"): r.continue_task("p","t",canonical_session_id="session-2",body_node_id="mbp")
