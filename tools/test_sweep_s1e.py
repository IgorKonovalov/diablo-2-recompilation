"""Unit tests of the pure models of tools/sweep_s1e.py (no game files, no Ghidra). Run: python3 -I tools/test_sweep_s1e.py"""
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep_s1e as S  # noqa: E402


class T(unittest.TestCase):
    def test_rng_pow2plus(self):
        v, lo, hi = S.rng_model(1, 666, 5, 8)
        self.assertEqual((lo, hi), (0x6AC6935F, 0))
        self.assertEqual(v, (0x6AC6935F & 7) + 5)
        self.assertEqual(S.rng_model(1, 666, 0xFFFFFFFF, 1)[0], 0xFFFFFFFF)     # n = 1: mask 0, base wraps
        self.assertEqual(S.rng_model(1, 666, 0, 0)[0], 0x6AC6935F)              # n = 0: mask all ones

    def test_clampu(self):
        self.assertEqual(S.clampu(0xFFFFFFFF, 7), 0x7F)       # -1 saturates to all ones, not 0
        self.assertEqual(S.clampu(5, 7), 5)
        self.assertEqual(S.clampu(0x80000000, 32), 0x80000000)
        self.assertEqual(S.clampu(0xFFFFFFFF, 7, neg=True), 0)

    def test_findcode_binary_search(self):
        arr = [[1, 10], [5, 11], [0x80000000, 12], [0xFFFFFFFF, 13]]
        self.assertEqual(S.findcode_model(arr, 0x80000000), 12)     # unsigned: above 5
        self.assertEqual(S.findcode_model(arr, 6), -1)
        self.assertEqual(S.findcode_model([], 1), -1)

    def test_addcode_bumps_duplicates(self):
        ret, new = S.addcode_model([[4, 0], [5, 1]], 4)
        self.assertEqual(ret, 2)
        self.assertEqual(new, [[4, 0], [5, 1], [6, 2]])                # 4 -> 5 -> 6
        ret, new = S.addcode_model([[0, 0], [0xFFFFFFFF, 1]], 0xFFFFFFFF)
        self.assertEqual(new[1], [1, 2])                                 # wraps to 0, then 1

    def test_cstrcmp(self):
        self.assertEqual(S.cstrcmp(b"abc", b"abd"), -1)
        self.assertEqual(S.cstrcmp(b"abc\0x", b"abc"), 0)
        self.assertEqual(S.cstrcmp(b"\xe9", b"z"), 1)                   # unsigned bytes

    def test_eval_model(self):
        env = S.EvalEnv("ident", [], 0, 0)
        self.assertEqual(S.eval_model(bytes([7, 9, 7, 0, 0x13, 0]), 6, env), 0)         # zero divisor
        self.assertEqual(S.eval_model(bytes([7, 3, 7, 4, 0x16, 0]), 6, env), 4)         # two values: else wins
        self.assertEqual(S.eval_model(bytes([7, 3, 7, 0, 0x14, 0]), 6, env), 1)         # e <= 0 gives 1
        self.assertEqual(S.eval_model(bytes([4, 0xFF, 0]), 3, env), 0xFF)                # 04 index unsigned
        self.assertEqual(S.eval_model(bytes([5, 0xFE, 0xFF, 0]), 4, env), -2)            # 05 index signed
        self.assertEqual(S.eval_model(bytes([7, 5, 1, 4, 0]), 5, env), 0)                # f >= nFuncs: push 0
        prog = bytes(sum(([7, 1] for _ in range(65)), [])) + bytes([0x10] * 70 + [0])
        self.assertEqual(S.eval_model(prog, len(prog), env), 64)                        # 65th push dropped
        self.assertEqual(S.eval_model(bytes([7, 1]), 0, env), 0)

    def test_dimret_and_dm78(self):
        self.assertEqual(S.dimret(0, 7, 3), 3)          # lvl 0: min(a, b)
        self.assertEqual(S.dimret(0, 3, 7), 3)

    def test_build_tbl_roundtrip(self):
        import tbl
        pairs = [(b"k%d" % i, b"v%d" % i) for i in range(30)]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.tbl")
            open(p, "wb").write(S.build_tbl(pairs))
            t = tbl.Tbl(p)
            self.assertEqual(t.count, 30)
            self.assertEqual([e[1] for e in t.entries], [k for k, _ in pairs])
            f = t.checks()
            self.assertEqual({k: v for k, v in f.items() if k not in ("crc", "hash")}, {k: 0 for k in f
                                                                                        if k not in ("crc", "hash")})

    def test_read_out(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.out")
            open(p, "w").write("C 1 006c0bc0 eax=00000005 edx=00000000 pop=24 steps=9\nD 10000000 0a0b\n"
                               "C 2 006c0bc0 STOP 0030339e steps=5 pc outside\nR 006c0c07 006c117c 4 2\n")
            calls, reads, writes = S.read_out(p)
            self.assertEqual(calls[0]["eax"], 5)
            self.assertEqual(calls[0]["dumps"], [(0x10000000, b"\x0a\x0b")])
            self.assertIn("stop", calls[1])
            self.assertEqual(reads, [(0x006C0C07, 0x006C117C, 4, 2)])

    def test_account(self):
        rep = S.Report("t")
        S.account(rep, [(1, 0x100, 4, 1), (1, 0x200, 4, 1)], [(1, 0x100, 4, 1)], [(0x100, 0x104, "r", "x")])
        self.assertEqual(rep.c["undeclared"], 2)        # the read at 0x200 and the write into a read-only range


if __name__ == "__main__":
    unittest.main()
