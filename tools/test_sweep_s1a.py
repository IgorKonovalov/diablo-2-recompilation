"""Unit tests of the pure helpers of tools/sweep_s1a.py (no game files needed). Run: python3 -I tools/test_sweep_s1a.py"""
import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep_s1a as S  # noqa: E402


class T(unittest.TestCase):
    def test_jlines_keeps_order_and_skips_bad_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.log")
            with open(p, "w") as f:
                f.write('SAVE {"a":1}\nSBIT not json\nSBIT {"final":true,"off":3}\nWDONE {"hex":""}\n')
            self.assertEqual([t for t, _ in S.jlines(p)], ["SAVE", "SBIT", "WDONE"])
            self.assertEqual(list(S.jlines(p, ("SBIT",))), [("SBIT", {"final": True, "off": 3})])

    def test_writes_of_splits_final_and_earlier_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "w.log")
            with open(p, "w") as f:
                f.write('SBIT {"final":true,"off":1}\nSAVE {}\nWHDR {"wsw":0}\nSBIT {"final":false,"code":"jav "}\n'
                        'SBIT {"final":true,"off":9}\nWDONE {"hex":"00"}\n')
            w = S.writes_of(p)
            self.assertEqual(len(w), 1)
            self.assertEqual([x["off"] for x in w[0]["sbit"]], [9])
            self.assertEqual([x["code"] for x in w[0]["pre"]], ["jav "])

    def test_bits_at_is_lsb_first(self):
        self.assertEqual(S.bits_at(bytes([0b10110000]), 4, 3), 0b011)
        self.assertEqual(S.bits_at(bytes([0x80, 0x01]), 7, 2), 0b11)

    def test_groups(self):
        self.assertEqual(S.FOLLOWERS[56], 54)
        self.assertEqual(sorted(S.GROUP_HEADS), [17, 48, 50, 52, 54, 57])

    def test_report_exit_status(self):
        R = S.Report("x")
        R.add("n", 2)
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            self.assertEqual(R.done(), 0)
        self.assertIn("S1A x bad=0 n=2", buf.getvalue())
        R.expect(False, "why")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(R.done(), 1)


if __name__ == "__main__":
    unittest.main()
