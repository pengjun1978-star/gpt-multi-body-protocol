import unittest
from runtime_dispatch import *
from resource_contract import ResourceContract
from liveness import Liveness
class V111Guards(unittest.TestCase):
    def test_cloud_is_strong_affinity_and_bridged_is_distinct(self):
        r=select_runtime(DispatchRequest("t",requested_runtime="GPT Work Cloud")); self.assertEqual((r["work_type"],r["affinity"]),(DIRECT_CLOUD_WORK,"STRONG"))
        b=select_runtime(DispatchRequest("t",requested_runtime="GPT Work Cloud",explicit_fallback="local_bridge"),cloud_available=False); self.assertEqual(b["work_type"],LOCAL_BRIDGED_CLOUD_WORK)
    def test_cloud_unavailable_fails_closed(self):
        with self.assertRaisesRegex(RuntimeDispatchError,"CLOUD_RUNTIME_UNAVAILABLE"): select_runtime(DispatchRequest("t",cloud_artifact=True),cloud_available=False)
    def test_resource_contract_and_liveness(self):
        self.assertTrue(ResourceContract("codex","none","local","none","parent","exact_resume").validate()); l=Liveness(); l.transition("ACCEPTED"); self.assertEqual(l.check_timeout(11,10),"STALLED")
if __name__=="__main__": unittest.main()
