import unittest
from micro_tasks import run


class MicroTaskTests(unittest.TestCase):
    def test_bounded_chain_and_rejection(self):
        result = run()
        self.assertEqual(result["T3"]["inference"], False)
        self.assertEqual(result["T4"]["value"], 45)
        self.assertEqual(result["T5"]["decision"], "REJECT")
        self.assertEqual(result["T6"]["depends_on"], ["T2", "T4"])


if __name__ == "__main__": unittest.main()
