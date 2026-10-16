"""Synthetic tests for the plan 0038 batch S3a pieces: python3 -I tools/test_mon_sweep.py

No game file is read: the MonStats/MonStats2 records and the log lines are built in memory.
  - mon_sweep.findadd: the excluded classes, a class already in the region, a full region, a class whose TotalPieces
    is at most 2 (no append) and an append whose sets come from the unit seed exactly as tools/monpool.py rolls them;
  - mon_sweep.variant_roll_counted with the tries = 0 stop equals tools/monpool.py's variant_roll on random entries
    (sets and seed), and counts a try that meets two equal sets;
  - mon_sweep.scan_spawn: a flag-0x80 request created on a cell CollisionTest refused is counted as the bypass, the
    same request without the flag is counted apart, and the SCI/SCD lines follow the live count in a snapshot;
  - the small helpers: div3 (signed, truncating), hash_ok (shortened hashes), parse_hire_table, ColumnSwap.
"""
import json
import os
import random
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mon_sweep  # noqa: E402
import monpool  # noqa: E402


class FakeT:
    """The monpool.Tables surface the FindAdd and variant models use: ms, ms2rec."""
    def __init__(self, comps, pieces=3):
        self.ms, self.ms2 = [], []
        for i, comp in enumerate(comps):
            r = bytearray(0x1A8)
            struct.pack_into("<h", r, 0x18, i)
            self.ms.append(bytes(r))
            m2 = bytearray(0x134)
            m2[0x15:0x25] = bytes(comp)
            m2[0x25] = min(254, sum(c - 1 for c in comp if c >= 2))
            m2[0xEC] = pieces if i != 1 else 2          # class 1: TotalPieces 2 -> no append
            self.ms2.append(bytes(m2))

    def ms2rec(self, c):
        return self.ms2[c] if 0 <= c < len(self.ms2) else None


COMPS = [[1] * 16, [3] + [1] * 15, [2, 3] + [1] * 14, [4, 1, 2, 5] + [1] * 12] + [[2] * 16] * 300


class FindAdd(unittest.TestCase):
    def test_kinds(self):
        T = FakeT(COMPS)
        s = monpool.Seed(12345)
        self.assertEqual(mon_sweep.findadd(T, [], 0xC3, s)[0], "none")
        reg = [[3, 1, []]]
        self.assertEqual(mon_sweep.findadd(T, reg, 3, s)[0], "found")
        self.assertEqual(mon_sweep.findadd(T, [[k + 100, 1, []] for k in range(13)], 3, s)[0], "none")
        self.assertEqual(mon_sweep.findadd(T, [], 1, s)[0], "stale")
        self.assertEqual(str(s), str(monpool.Seed(12345)))      # none of these drew

    def test_append_draws_like_monpool(self):
        T = FakeT(COMPS)
        for seed in (1, 77, 0xDEADBEEF):
            s1, s2 = monpool.Seed(seed), monpool.Seed(seed)
            reg = [[0, 1, []]]
            kind, e = mon_sweep.findadd(T, reg, 3, s1)
            want = [3, 0, []]
            monpool.variant_roll(T, s2, want, 3)
            self.assertEqual(kind, "added")
            self.assertEqual(e[2], want[2])
            self.assertEqual(str(s1), str(s2))
            self.assertEqual(len(reg), 2)


class VariantRoll(unittest.TestCase):
    def test_equals_monpool(self):
        rnd = random.Random(7)
        comps = [[rnd.choice([0, 1, 2, 2, 3, 4]) for _ in range(16)] for _ in range(40)]
        T = FakeT(comps)
        for _ in range(400):
            cls = rnd.randrange(len(comps))
            seed = rnd.randrange(1 << 32)
            a, b = monpool.Seed(seed), monpool.Seed(seed)
            ea, eb = [cls, 0, []], [cls, 0, []]
            monpool.variant_roll(T, a, ea, 3)
            mon_sweep.variant_roll_counted(T, b, eb, 3)
            self.assertEqual(ea[2], eb[2])
            self.assertEqual(str(a), str(b))

    def test_two_set_hit_counted(self):
        # two components with two values each: a set equal to set 0 is appended once the tries run out, and the
        # next set's tests can then meet two existing sets
        T = FakeT([[2, 2] + [1] * 14])
        cnt = __import__("collections").Counter()
        hit = False
        for seed in range(1, 50000):
            cnt.clear()
            e = [0, 0, []]
            mon_sweep.variant_roll_counted(T, monpool.Seed(seed), e, 3, False, cnt)
            if cnt["duplicate tests meeting 2 existing set(s)"]:
                hit = True
                self.assertEqual(e[2][0], e[2][1])
                break
        self.assertTrue(hit)


def write_log(lines):
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w") as f:
        f.write("# d2run seed=1\n")
        for tag, d in lines:
            f.write("%s %s\n" % (tag, json.dumps(d)))
    return path


class ScanSpawn(unittest.TestCase):
    def test_bypass_and_special_count(self):
        reg = {"r": 7, "nrooms": 3, "nspec": 2}
        lines = [
            ("P0", {"diff": 0, "exp": 1, "reg": reg}), ("PX", {"reg": reg}),
            ("MT0", {"room": 1, "rad": -1, "fl": 0xE2}), ("MK0", {"x": 5, "y": 6}), ("MK", {"r": 1}),
            ("MU0", {"x": 5, "y": 6}), ("MTX", {}),
            ("MT0", {"room": 1, "rad": -1, "fl": 0}), ("MK0", {"x": 5, "y": 6}), ("MK", {"r": 1}),
            ("MU0", {"x": 5, "y": 6}), ("MTX", {}),
            ("SCI", {"reg": 7, "before": 2}), ("SCD", {"reg": 7, "before": 3, "unit": 9}),
            ("P0", {"diff": 0, "exp": 1, "reg": dict(reg, nspec=2)}),
        ]
        path = write_log(lines)
        try:
            c = mon_sweep.scan_spawn(path)
        finally:
            os.unlink(path)
        self.assertEqual(c["requests with flag 0x80 created on a cell CollisionTest refused"], 1)
        self.assertEqual(c["requests WITHOUT flag 0x80 created on a cell CollisionTest refused"], 1)
        self.assertEqual(c["SCI: before = the live count"], 1)
        self.assertEqual(c["SCD: before = the live count"], 1)
        self.assertEqual(c["region snapshots: live special count = SCI/SCD model"], 2)


class Helpers(unittest.TestCase):
    def test_div3(self):
        self.assertEqual([mon_sweep.div3(v) for v in (-7, -3, -1, 0, 1, 5, 6)], [-2, -1, 0, 0, 0, 1, 2])

    def test_hash_ok(self):
        h = "d4cf9a8f" + "0" * 52 + "3b3d"
        self.assertTrue(mon_sweep.hash_ok(h, ("d4cf9a8f", "3b3d")))
        self.assertFalse(mon_sweep.hash_ok(h, ("d4cf9a8f", "3b3e")))
        self.assertTrue(mon_sweep.hash_ok(h, h))

    def test_hire_table(self):
        raw = struct.pack("<HHIII", 3411, 0, 99, 0, 1) + bytes(16 * 68)
        t = mon_sweep.parse_hire_table(raw.hex())
        self.assertEqual(len(t), 69)
        self.assertEqual(t[0], (3411, 0, 99, 0, 1))
        self.assertEqual(t[68], (0, 0, 0, 0, 0))

    def test_column_swap(self):
        class T:
            def slots(self, lid, off):
                return [off]
        self.assertEqual(mon_sweep.ColumnSwap(T()).slots(4, 0x36), [0x68])
        self.assertEqual(mon_sweep.ColumnSwap(T()).slots(4, 0x9A), [0x9A])


if __name__ == "__main__":
    unittest.main()
