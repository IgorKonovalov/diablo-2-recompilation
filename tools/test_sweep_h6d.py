#!/usr/bin/env python3
"""Tests for tools/sweep_h6d.py (plan 0038 batch H6d) on synthetic quests.gdb lines; no game data needed.

    python3 -I tools/test_sweep_h6d.py
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng  # noqa: E402
import sweep_h6d  # noqa: E402

PLAYER = [0, 1, 1]
MERC = [1, 271, 77]
ANDY = [1, 156, 90]


def line(tag, d):
    return "%s %s\n" % (tag, json.dumps(d, separators=(",", ":")))


def merc_kill(word=0, b6x_killer=MERC, qme_player=PLAYER):
    s = line("MMR", {"mon": ANDY, "mode": 0, "rec": "006e2260", "start": "005a6ff0"})
    s += line("B60", {"mon": ANDY, "qid": 6, "cp": 1, "diff": 0, "tc4": 833, "tc": 830, "ctx": 1, "killer": MERC})
    s += line("B6O", {"owner": PLAYER})
    s += line("B6E", {"exp": 0})
    s += line("B6P", {"unit": PLAYER, "rec": 5, "word": word})
    s += line("B6G", {"k": 15, "r": (word >> 15) & 1})
    if not (word >> 15) & 1:
        s += line("B6G", {"k": 1, "r": (word >> 1) & 1})
        if not (word >> 1) & 1:
            s += line("B6G", {"k": "cp", "r": (word >> 1) & 1})
    s += line("B6X", {"tc": 833 if not word & 0x8002 else 830, "killer": b6x_killer})
    s += line("QME", {"mon": ANDY, "killer": MERC, "player": qme_player})
    s += line("QS", {"ret": "0059621d", "rec": 5, "w": 6, "b": 1, "old": word})
    return s


def run(cmd, text):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.log")
        with open(p, "w") as f:
            f.write(text)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = sweep_h6d.check_logs([p], False) if cmd == "logs" else None
        return rc, out.getvalue()


class RandLoHi(unittest.TestCase):
    def test_not_pow2(self):
        s = (0x12345678, 666)
        lo, hi = 1500, 3000
        v, s2 = sweep_h6d.rand_lohi(s, lo, hi)
        st = rng.step(*s)
        self.assertEqual(v, lo + st[0] % 1500)
        self.assertEqual(s2, st)

    def test_pow2_and_empty(self):
        s = (7, 666)
        v, _ = sweep_h6d.rand_lohi(s, 0, 1024)
        self.assertEqual(v, rng.step(*s)[0] & 1023)
        self.assertEqual(sweep_h6d.rand_lohi(s, 10, 10), (10, s))


class Logs(unittest.TestCase):
    def test_merc_kill_ok(self):
        rc, out = run("logs", merc_kill())
        self.assertEqual(rc, 0, out)
        self.assertIn("killer hireling -> owner player: taken", out)

    def test_resolved_killer_passed_on_is_bad(self):
        rc, out = run("logs", merc_kill(b6x_killer=PLAYER))
        self.assertEqual(rc, 1, out)

    def test_qme_player_must_be_owner(self):
        rc, out = run("logs", merc_kill(qme_player=0))
        self.assertEqual(rc, 1, out)

    def test_write_before_drop_is_bad(self):
        t = merc_kill()
        i = t.index("B60 ")
        t = t[:i] + line("QS", {"ret": "0059621d", "rec": 5, "w": 6, "b": 1, "old": 0}) + t[i:]
        rc, out = run("logs", t)
        self.assertEqual(rc, 1, out)

    def test_baal_gold(self):
        q = (0x0BADF00D, 666)
        amt, s = sweep_h6d.rand_lohi(q, 1500, 3000)
        t = line("BG0", {"lo": 1500, "hi": 3000, "n": 1, "diff": 0, "qs": "%08x:%08x" % q})
        t += line("QGS", {"ret": "0058e057", "qs": "%08x:%08x" % q})
        t += line("BGR", {"amt": amt, "qs": "%08x:%08x" % s})
        t += line("GLD", {"item": [4, 523, 9], "amt": amt, "s14": amt})
        rc, out = run("logs", t)
        self.assertEqual(rc, 0, out)
        t2 = t.replace('"amt":%d,"qs"' % amt, '"amt":%d,"qs"' % (amt + 1))
        rc, out = run("logs", t2)
        self.assertEqual(rc, 1, out)

    def test_warriv(self):
        t = line("QC", {"ret": "00595d92", "rec": 5, "w": 6, "b": 1, "old": 0x2002})
        t += line("QS", {"ret": "00595d9c", "rec": 5, "w": 6, "b": 0, "old": 0x2000})
        rc, out = run("logs", t)
        self.assertEqual(rc, 0, out)
        self.assertIn("warriv: QC bit 1", out)


if __name__ == "__main__":
    unittest.main()
