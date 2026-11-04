"""No-game test of tools/ai_r5_scan.py: python3 -I tools/test_ai_r5_scan.py (a written log, nothing launched)."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai_r5_scan as S  # noqa: E402

LOG = """AI logger armed rev 5 bmax 48
AID {"k":1,"ai":20,"st":0}
MSM0 {"k":1,"n":10}
AIB {"k":1,"n":11}
MSM1 {"k":1,"n":12}
AIB {"k":1,"n":13}
AID {"k":2,"ai":20,"st":13}
MSM0 {"k":2,"n":20}
AIB {"k":2,"n":21}
AIL {"k":3,"pend":0}
AIL {"k":3,"pend":2}
AID {"k":4,"ai":34,"st":0}
"""


class Scan(unittest.TestCase):
    def test_counts(self):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
            f.write(LOG)
        try:
            r = S.scan(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(r["rev"], (5, 48))
        self.assertEqual(r["rows"], {20: 2, 34: 1})
        self.assertEqual(r["states"], {0: 2, 13: 1})
        self.assertEqual((r["ail"], r["ail_pend0"]), (2, 1))
        self.assertEqual((r["msm_spans"], r["msm_open"]), (2, 1))
        self.assertEqual((r["aib"], r["aib_in_msm"]), (3, 2))       # the AIB at n 11 and the one in the open span at 21


if __name__ == "__main__":
    unittest.main()
