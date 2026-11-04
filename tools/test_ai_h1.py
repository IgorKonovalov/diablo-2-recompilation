"""No-game test of tools/ai_h1.py: python3 -I tools/test_ai_h1.py (a written log, nothing launched)."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai_h1 as H  # noqa: E402
import skills  # noqa: E402


class H1(unittest.TestCase):
    def test_steps_after_a_decision(self):
        p = (1, 2)
        fmt = skills.sd_fmt
        lines = [("AID", {"u": 5, "n": 1, "s0": fmt(p)}), ("AIX", {"k": 1, "s": fmt(p)}),
                 ("MAS0", {"u": {"u": 5, "s": fmt(skills.step_n(p, 3))}}),          # 3 steps on
                 ("AID", {"u": 6, "n": 2, "s0": fmt(p)}), ("AIX", {"k": 2, "s": fmt(p)}),
                 ("SST0", {"u": {"u": 6, "s": fmt(p)}}),                              # 0 steps: closes
                 ("AID", {"u": 7, "n": 3, "s0": fmt(p)}), ("AIX", {"k": 3, "s": fmt(p)})]   # none
        fd, path = tempfile.mkstemp(suffix=".log")
        with os.fdopen(fd, "w") as fh:
            for t, d in lines:
                fh.write("%s %s\n" % (t, json.dumps(d)))
        try:
            r = H.scan(path)
        finally:
            os.unlink(path)
        self.assertEqual((r[3], r[0], r["none"]), (1, 1, 1))


if __name__ == "__main__":
    unittest.main()
