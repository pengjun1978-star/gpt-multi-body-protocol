import unittest
from p1d_routing import BodyProfile, TaskRequirement
from p1e_load_recovery import CapabilityLoad, choose_agent, choose_compute

class P1ELoadTests(unittest.TestCase):
    def setUp(self):
        self.m=BodyProfile("mbp-primary",frozenset({"shared","mac"}),frozenset({"local"}),"macos","M5 Pro",frozenset({"local"}),frozenset(),agent_capacity=1)
        self.o=BodyProfile("office-4090",frozenset({"shared","office"}),frozenset({"local","office"}),"windows","RTX 4090",frozenset({"office"}),frozenset(),agent_capacity=1,has_local_compute=True)
        self.loads={"mbp-primary":CapabilityLoad(1,1,0,0),"office-4090":CapabilityLoad(0,1,0,1)}
    def test_mac_busy_shared_task_reroutes_office(self):
        req=TaskRequirement("t","shared","local")
        self.assertEqual(choose_agent(req,[self.m,self.o],self.loads)["body_id"],"office-4090")
    def test_mac_affinity_waits_when_mac_busy(self):
        req=TaskRequirement("t","mac","local","macos",hardware="M5 Pro",environment="local")
        self.assertEqual(choose_agent(req,[self.m,self.o],self.loads)["decision"],"WAITING_RETRY")
    def test_agent_and_compute_failures_are_independent(self):
        self.loads["office-4090"].agent_available=False
        req=TaskRequirement("t","office","office",needs_model=True,model="qwen")
        self.assertEqual(choose_compute(self.o,req,self.loads)["decision"],"LOCAL_COMPUTE")
        self.loads["office-4090"].compute_available=False
        self.assertEqual(choose_compute(self.o,req,self.loads)["decision"],"COMPUTE_UNAVAILABLE")
        self.loads["office-4090"].compute_available=True; self.loads["office-4090"].agent_available=True
        self.loads["office-4090"].compute=1
        self.assertEqual(choose_compute(self.m,req,self.loads)["decision"],"COMPUTE_UNAVAILABLE")
