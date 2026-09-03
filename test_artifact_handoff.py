import tempfile, unittest
from pathlib import Path
from artifact_handoff import *
class ArtifactHandoffTests(unittest.TestCase):
 def test_large(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); s=r/'gpt.md'; t=r/'out'/'gpt.md'; s.write_text('# START\n'+('证据\n'*20000)+'# END',encoding='utf-8'); m=build_manifest(s,first_marker='# START',last_marker='# END',required_markers=('证据',)); consume(ManualDownloadProvider().stage(s,r/'staging'),t,m); self.assertEqual(s.read_bytes(),t.read_bytes())
 def test_hash_mismatch(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a'; p.write_text('# START\nx# END'); m=build_manifest(p,first_marker='# START',last_marker='# END'); p.write_text('# START\ny# END')
   with self.assertRaisesRegex(HandoffError,'SHA256_MISMATCH'): consume(p,Path(d)/'o',m)
