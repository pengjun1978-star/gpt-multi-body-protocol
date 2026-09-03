import tempfile,unittest
from successor_lineage import SuccessorLineage
class LineageTests(unittest.TestCase):
 def test_single_successor_generation(self):
  with tempfile.TemporaryDirectory() as d:
   r=SuccessorLineage(d+'/x.db'); r.add('t',2,'01a0655a-3c5e-7270-9083-0470e5616632','01a06559-be63-7353-88a2-6ee8d885c83f','RUNTIME_COMPATIBILITY_FAILED'); self.assertEqual(r.get('01a0655a-3c5e-7270-9083-0470e5616632')['execution_generation'],2)
   with self.assertRaisesRegex(ValueError,'GENERATION_ALREADY_EXISTS'): r.add('t',2,'01a0655b-3c5e-7270-9083-0470e5616632','01a06559-be63-7353-88a2-6ee8d885c83f','x')
