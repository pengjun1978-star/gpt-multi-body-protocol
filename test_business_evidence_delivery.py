import unittest
from business_evidence_delivery import MAX_CHUNK_CHARS, build_delivery, confirm_delivery

class DeliveryContractTests(unittest.TestCase):
    def test_manifest_chunks_and_hashes(self):
        receipt, chunks = build_delivery("t-1", "甲" * (MAX_CHUNK_CHARS + 3))
        self.assertEqual(receipt["manifest"]["chunks"], 2)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(receipt["manifest"]["sha256"], chunks[0]["manifest_sha256"])
    def test_confirmed_transport_stays_pending_parent_acceptance(self):
        receipt, chunks = build_delivery("t-2", "evidence")
        confirm_delivery(receipt, chunks_sent=len(chunks), sender_confirmed=True, office_inbox="PASS")
        self.assertEqual(receipt["status"], "PASS_PENDING_GPT_ACCEPTANCE")
        self.assertEqual(receipt["delivery"]["parent_visibility"], "UNVERIFIED")
    def test_partial_delivery_is_blocked(self):
        receipt, _ = build_delivery("t-3", "evidence")
        confirm_delivery(receipt, chunks_sent=0, sender_confirmed=False)
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertEqual(receipt["delivery"]["transport"], "FAIL")

if __name__ == "__main__": unittest.main()
