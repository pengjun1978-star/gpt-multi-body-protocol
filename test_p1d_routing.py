import unittest
from p1d_routing import *

class P1DRoutingTests(unittest.TestCase):
    def setUp(self):
        self.m=BodyProfile("mbp-primary",frozenset({"control"}),frozenset({"local"}),"macos","M5 Pro",frozenset({"local"}),frozenset({"read"}),agent_load=0,agent_capacity=2)
        self.o=BodyProfile("office-4090",frozenset({"execution"}),frozenset({"office"}),"windows","RTX 4090",frozenset({"office"}),frozenset({"execute"}),agent_load=1,agent_capacity=2,compute_capacity=1,has_local_compute=True)
    def test_affinity_before_load_and_compute_separation(self):
        req=TaskRequirement("t","execution","office","windows","RTX 4090","office",frozenset({"execute"}),True,"qwen")
        a=AgentScheduler().schedule(req,[self.m,self.o]); self.assertEqual(a["body_id"],"office-4090"); self.assertEqual(self.o.agent_load,2); self.assertEqual(self.o.compute_load,0)
        self.assertEqual(ComputeRouter().route(req,self.o,{"qwen"})["decision"],"LOCAL_COMPUTE")
    def test_mac_routes_model_to_office_and_reserved_rejected(self):
        req=TaskRequirement("t","control","local","macos",environment="local",permissions=frozenset(),needs_model=True,model="qwen")
        self.assertEqual(ComputeRouter().route(req,self.m,{"qwen"})["port"],11434)
        reserved=BodyProfile("mac-studio",frozenset({"execution"}),frozenset({"office"}),"macos","M2",frozenset({"office"}),frozenset(),state="RESERVED")
        self.assertEqual(AgentScheduler().schedule(req,[reserved])["decision"],"REJECT")
