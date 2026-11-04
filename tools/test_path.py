#!/usr/bin/env python3
"""No-game tests of tools/path.py (plan 0054 Phase 2): synthetic logs in the format of tools/gdb/path.py, written from the models
themselves, so the parser, the comparator, the controls and the tie are tested without a game. A log the model wrote must check
clean; every mutation of it (the return, a point, the seed, a cell of the live grid) must be reported; the outcome mix must see
what the log holds.

    python3 -I tools/test_path.py
"""
import base64
import json
import os
import random
import struct
import sys
import tempfile
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import io  # noqa: E402

import path as P  # noqa: E402
import path_emu2 as P2  # noqa: E402
import path_emu3 as P3  # noqa: E402

UNIT_ID = 7


def zb(b):
    return base64.b64encode(zlib.compress(b)).decode()


def rec_bytes(sx, sy, tx, ty, room, pattern=1, mask=0x1C09, ty_=13, flags=0x100, limit=14, b90=14, speed=0x800, param=0, unit=0xAAAA, target=0):
    b = bytearray(0x200)
    struct.pack_into("<HHHH", b, 0, 0x8000, sx, 0x8000, sy)
    struct.pack_into("<HH", b, 0x10, tx, ty)
    struct.pack_into("<I", b, 0x1C, room)
    struct.pack_into("<I", b, 0x30, unit)
    struct.pack_into("<I", b, 0x34, flags)
    struct.pack_into("<i", b, 0x3C, ty_)
    struct.pack_into("<I", b, 0x44, 1)
    struct.pack_into("<I", b, 0x48, pattern)
    struct.pack_into("<I", b, 0x50, mask)
    struct.pack_into("<I", b, 0x58, target)
    struct.pack_into("<I", b, 0x7C, speed)
    b[0x90], b[0x91] = b90, limit
    struct.pack_into("<I", b, 0x98, param)
    return bytes(b)


def room_lines(addr, x0, y0, w, h, cells, near, n0):
    raw = struct.pack("<%dH" % len(cells), *cells)
    d = {"a": addr, "r": [x0, y0, w, h], "mr": [x0, y0, w, h], "nr": near, "h": zlib.crc32(raw), "nh": 0, "lid": 1, "z": zb(raw), "n": n0}
    return "PLG " + json.dumps(d), d["h"]


class Synth:
    """Writes a log of one game from cases: the live grid is the cells given."""

    def __init__(self):
        self.lines = ['AGM {"game":1,"n":1}']
        self.n = 1
        self.rooms = {}

    def nn(self):
        self.n += 1
        return self.n

    def room(self, addr, x0, y0, w, h, cells, near):
        ln, hsh = room_lines(addr, x0, y0, w, h, cells, near, self.nn())
        self.lines.append(ln)
        self.rooms[addr] = hsh

    def plan(self, unit_type, rec, seed, planner, ctx, rooms, exit_rec, eax, exit_seed, units=(), ty=None, fl=None, ra=0x57F11C, with_plc=True):
        k = self.nn()
        ty = struct.unpack_from("<i", rec, 0x3C)[0] if ty is None else ty
        fl = struct.unpack_from("<I", rec, 0x34)[0] if fl is None else fl
        self.lines.append("PLN " + json.dumps({"u": [unit_type, 4, UNIT_ID, 1, 5021, 5028], "p": 1, "ty": ty, "fl": fl, "fo": 0, "ra": ra,
                                               "s0": seed, "fr": 5, "rec": zb(rec), "tg": None, "ar": 1, "n": k}))
        if with_plc:
            self.lines.append("PLC " + json.dumps({"k": k, "pl": planner, "ctx": ctx.hex(), "rec": zb(rec), "rm": [[a, self.rooms[a], 0] for a in rooms],
                                                   "s": seed, "u": list(units), "self": [unit_type, UNIT_ID], "tgt": None, "n": self.nn()}))
        self.lines.append("PLX " + json.dumps({"k": k, "eax": eax, "n28": eax, "n24": 0, "fl": fl, "pts": [], "t": [0, 0], "f18": [0, 0],
                                               "s": exit_seed, "rec": zb(exit_rec), "fr": 5, "n": self.nn()}))

    def write(self, path):
        with open(path, "w") as fh:
            fh.write("\n".join(self.lines) + "\n")


def ctx_bytes(sx, sy, tx, ty, room, troom, refresh, limit, b1c, typ, pattern, mask, path=1):
    b = bytearray(0x34)
    struct.pack_into("<HHHHII", b, 0, sx, sy, tx, ty, room, troom)
    b[0x14] = refresh
    struct.pack_into("<I", b, 0x18, limit)
    b[0x1C] = b1c
    struct.pack_into("<iiiII", b, 0x20, typ, 1, pattern, mask, path)
    return bytes(b)


def world(rnd, wall=0.12):
    """Two touching rooms of 40 x 40 with seeded walls."""
    cells = [[0x1C01 if rnd.random() < wall else 0 for _ in range(1600)] for _ in range(2)]
    return cells


def build_log(path, seed=1, n=60):
    rnd = random.Random(seed)
    S = Synth()
    cells = world(rnd)
    A, B = 0x2000, 0x2100
    S.room(A, 5000, 5000, 40, 40, cells[0], [A, B])
    S.room(B, 5040, 5000, 40, 40, cells[1], [A, B])
    R = {A: P2.Room(0, (5000, 5000, 40, 40), list(cells[0]), "t"), B: P2.Room(1, (5040, 5000, 40, 40), list(cells[1]), "t")}
    R[A].addr, R[B].addr = A, B
    R[A].near = R[B].near = [R[A], R[B]]
    made = 0
    while made < n:
        sx, sy = rnd.randint(5002, 5070), rnd.randint(5002, 5036)
        tx, ty = sx + rnd.randint(-30, 30), sy + rnd.randint(-20, 20)
        if (tx, ty) == (sx, sy) or not (5002 <= tx <= 5077) or not (5002 <= ty <= 5037):
            continue
        # keep the start free of walls
        if any(R[a].has(sx, sy) and R[a].cell(sx, sy) for a in R):
            continue
        typ = rnd.choice((13, 2, 7, 15, 1))
        fn = {13: P.PL and 0x00679C80, 2: 0x00679C80, 7: 0x00679ED0, 15: 0x0067C2D0, 1: 0x0067B850}[typ]
        room = A if sx < 5040 else B
        rec = rec_bytes(sx, sy, tx, ty, room, ty_=typ, limit=rnd.choice((14, 40, 77)))
        ctx = ctx_bytes(sx, sy, tx, ty, room, room, 1, struct.unpack_from("<I", rec, 0x91 - 1)[0] >> 8 & 0xFF if False else rec[0x91], 0, typ, 1, 0x1C09)
        seed_s = "%08x:%08x" % (rnd.getrandbits(32), rnd.getrandbits(31) + 1)
        # run the model through the same code path the checker uses
        tmp = Synth()
        tmp.lines = list(S.lines)
        tmp.rooms = dict(S.rooms)
        tmp.n = S.n
        tmp.plan(0, rec, seed_s, fn, ctx, [A, B], rec, 0, seed_s)
        tmp.write(path)
        g = P.parse(path)[0]
        pl = g.plans[-1]
        pred = P.predict_planner(pl)
        out = bytearray(rec)
        for i, p in enumerate(pred["pts"]):
            struct.pack_into("<I", out, 0x9C + 4 * i, p)
        S.plan(0, rec, seed_s, fn, ctx, [A, B], bytes(out), pred["eax"], P.seed_str(pred["seed"]))
        made += 1
    S.write(path)
    return S


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.log = os.path.join(self.d, "a.log")

    def run_check(self, path=None):
        out = io.StringIO()
        rc = P.report([path or self.log], out)
        return rc, out.getvalue()

    def test_clean_log_checks_clean(self):
        build_log(self.log)
        rc, text = self.run_check()
        self.assertEqual(rc, 0, text[-2000:])
        self.assertIn("mismatched=0", text)
        self.assertIn("detected 60 of 60", text)                      # the comparator's mutations

    def test_outcome_mix_counts_types(self):
        build_log(self.log, seed=2, n=80)
        g = P.parse(self.log)[0]
        types = {pl.ty for pl in g.plans}
        self.assertTrue(types <= {13, 2, 7, 15, 1})
        rc, text = self.run_check()
        self.assertIn("OUTCOME MIX", text)
        self.assertIn("plans=80", text)

    def mutate(self, f):
        build_log(self.log, seed=3, n=30)
        lines = open(self.log).read().split("\n")
        out = f(lines)
        p2 = os.path.join(self.d, "b.log")
        open(p2, "w").write("\n".join(out))
        return self.run_check(p2)

    def test_changed_return_fails(self):
        def f(lines):
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith("PLX "):
                    d = json.loads(lines[i][4:])
                    d["eax"] += 1
                    lines[i] = "PLX " + json.dumps(d)
                    break
            return lines
        rc, text = self.mutate(f)
        self.assertEqual(rc, 1)
        self.assertIn("MISMATCH", text)

    def test_changed_seed_fails(self):
        def f(lines):
            for i, l in enumerate(lines):
                if l.startswith("PLX "):
                    d = json.loads(l[4:])
                    d["s"] = "00000000:00000001"
                    lines[i] = "PLX " + json.dumps(d)
                    break
            return lines
        rc, text = self.mutate(f)
        self.assertEqual(rc, 1)

    def test_changed_point_fails(self):
        def f(lines):
            for i, l in enumerate(lines):
                if l.startswith("PLX "):
                    d = json.loads(l[4:])
                    r = bytearray(P.unz(d["rec"]))
                    if d["eax"]:
                        r[0x9C] ^= 1
                        d["rec"] = zb(bytes(r))
                        lines[i] = "PLX " + json.dumps(d)
                        break
            return lines
        rc, text = self.mutate(f)
        self.assertEqual(rc, 1)

    def test_changed_live_cell_changes_prediction(self):
        """Flipping a cell on the route in the live grid must change the model's output for some plan (the grid is read)."""
        build_log(self.log, seed=4, n=40)
        g = P.parse(self.log)[0]
        changed = 0
        for pl in g.plans:
            base = P.predict_planner(pl)
            if not base["tested"]:
                continue
            a, x, y, pat, mask = base["tested"][0]
            R = P.mk_world(pl)
            r = [rr for rr in R.values() if rr.has(x, y)][0]
            idx = (y - r.y0) * r.w + (x - r.x0)
            for v in (0xFFFF, 0):
                try:
                    p2 = P.predict_planner(pl, None, [(r.addr, idx, v)])
                except P.Unmodelled:
                    continue
                if P.pred_key(p2) != P.pred_key(base):
                    changed += 1
                    break
        self.assertGreater(changed, 5)

    def test_refusal_and_reasons(self):
        S = Synth()
        S.room(0x2000, 5000, 5000, 40, 40, [0] * 1600, [0x2000])
        rec = rec_bytes(5010, 5010, 5010, 5010, 0x2000)
        S.plan(1, rec, "00000001:00000002", 0, b"", [], rec, 0, "00000001:00000002", with_plc=False)
        rec2 = rec_bytes(5010, 5010, 5300, 5010, 0x2000)
        S.plan(1, rec2, "00000001:00000002", 0, b"", [], rec2, 0, "00000001:00000002", with_plc=False)
        S.write(self.log)
        rc, text = self.run_check()
        self.assertIn("refused:target=start=1", text)
        self.assertIn("refused:window=1", text)
        self.assertEqual(rc, 0, text[-1500:])

    def test_refusal_with_draw_fails(self):
        S = Synth()
        rec = rec_bytes(5010, 5010, 5010, 5010, 0x2000)
        S.plan(1, rec, "00000001:00000002", 0, b"", [], rec, 0, "00000009:00000002", with_plc=False)
        S.write(self.log)
        rc, text = self.run_check()
        self.assertEqual(rc, 1)

    def test_straight_types(self):
        S = Synth()
        rnd = random.Random(5)
        for i in range(12):
            rec = rec_bytes(5010 + i, 5010, 5030, 5020, 0x2000, ty_=10, flags=0x40000, limit=rnd.choice((14, 40, 77)))
            seed = "%08x:%08x" % (rnd.getrandbits(32), rnd.getrandbits(31) + 1)
            M = P.mk_mem(type("X", (), {"pln": {"tg": None}, "unit_type": 3})(), rec, P.seed_of(seed))
            st = {}
            n = P3.rwalk(M, P3.UNIT + 0x20, None, st)
            out = bytearray(rec)
            for k in range(n):
                struct.pack_into("<I", out, 0x9C + 4 * k, M.r32(P3.UPATH + 0x9C + 4 * k))
            S.plan(3, rec, seed, 0, b"", [], bytes(out), n, "%08x:%08x" % (M.r32(P3.UNIT + 0x20), M.r32(P3.UNIT + 0x24)), ty=10, fl=0x40000,
                   with_plc=False)
        for i in range(5):
            rec = rec_bytes(5010, 5010 + i, 5030, 5020, 0x2000, ty_=14, flags=0x40000)
            M = P.mk_mem(type("X", (), {"pln": {"tg": None}, "unit_type": 3})(), rec, (1, 2))
            n = P3.spiral(M, None, {})
            out = bytearray(rec)
            for k in range(n):
                struct.pack_into("<I", out, 0x9C + 4 * k, M.r32(P3.UPATH + 0x9C + 4 * k))
            S.plan(3, rec, "00000001:00000002", 0, b"", [], bytes(out), n, "00000001:00000002", ty=14, fl=0x40000, with_plc=False)
        S.write(self.log)
        rc, text = self.run_check()
        self.assertEqual(rc, 0, text[-1500:])
        self.assertIn("SPIRAL", text)

    def test_tie_marks_and_residual(self):
        """A unit's marks on the built map explain the live cells; a cell of unknown origin is reported."""
        rnd = random.Random(6)
        S = Synth()
        base = [0] * 1600
        live = list(base)
        # a monster at (5010, 5010), pattern 1 (plus), mask 0x100: the live cells hold plus + 0x1000
        for dx, dy in ((-1, 0), (0, 0), (1, 0), (0, -1), (0, 1)):
            live[(10 + dy) * 40 + 10 + dx] |= 0x100
        live[10 * 40 + 10] |= 0x1000
        live[20 * 40 + 20] |= 0x400                                   # an unexplained cell
        S.room(0x2000, 5000, 5000, 40, 40, live, [0x2000])
        rec = rec_bytes(5030, 5030, 5035, 5030, 0x2000, ty_=13)
        ctx = ctx_bytes(5030, 5030, 5035, 5030, 0x2000, 0x2000, 1, 14, 0, 13, 1, 0x1C09)
        S.plan(0, rec, "00000001:00000002", 0x00679C80, ctx, [0x2000], rec, 0, "00000001:00000002",
               units=[[1, 99, 3, 1, 5010, 5010, 0x2000, 1, 1, 0x100, 0]])
        S.write(self.log)
        # the built map the room had
        z = zb(json.dumps({"cells": [5000, 5000, 40, 40, struct.pack("<1600H", *base).hex()]}).encode())
        lines = open(self.log).read().split("\n")
        lines.insert(1, "CB " + json.dumps({"th": 1, "room": 0x2000, "lid": 1, "rect": [5000, 5000, 40, 40], "z": z, "n": 1}))
        open(self.log, "w").write("\n".join(lines))
        g = P.parse(self.log)[0]
        t = P.tie_of(g.plans[0])
        self.assertEqual(t["compared"], 1)
        self.assertEqual(t["cells"], 1)
        self.assertEqual(t["bits"], 0x400)

    def test_grid_rules(self):
        """path/0005: O1 reads HasCollision[mode] (the logged byte of rev 5 first); C1..C3 pick the dead monster's mark."""
        hc = {374: (0,) * 8, 7: (1, 1, 0, 0, 0, 0, 0, 0)}
        obj = [2, 1, 7, 10, 10, 0xA, 0, 1, 1, 0, 0, 0, 0]
        self.assertTrue(P.object_marked(obj, hc))
        self.assertFalse(P.object_marked(obj[:6] + [2] + obj[7:], hc))
        self.assertFalse(P.object_marked(obj[:2] + [374] + obj[3:], hc))
        self.assertFalse(P.object_marked(obj + [0], hc))
        room = P2.Room(0, (0, 0, 9, 9), [0] * 81, "t")
        room.addr, room.near = 1, [room]
        R = {1: room}
        P.corpse_mark(R, 1, 4, 4, 1, 0x100, 0)
        self.assertEqual(sum(1 for c in room.c if c == 0x8000), 9)
        room.c = [0] * 81
        P.corpse_mark(R, 1, 4, 4, 1, 0x100, 1)
        self.assertEqual(sum(1 for c in room.c if c & 0x100), 5)
        room.c = [0] * 81
        P.corpse_mark(R, 1, 4, 4, 5, 0x8000, 0)
        self.assertEqual(sum(1 for c in room.c if c == 0x8000), 5)

    def test_break_lines_and_control(self):
        build_log(self.log, seed=7, n=5)
        with open(self.log, "a") as fh:
            fh.write("BRK " + json.dumps({"fn": 0x00679C80, "ty": 13, "side": "srv", "ra": 1, "pra": 2, "ctl": 1, "fr": 3, "n": 9990}) + "\n")
            fh.write("BRK " + json.dumps({"fn": 0x00679E50, "ty": 3, "side": "srv", "ra": 1, "pra": 2, "ctl": 0, "fr": 3, "n": 9991}) + "\n")
        rc, text = self.run_check()
        self.assertIn("server-caller hits on a watched function: 1", text)

    def test_controls_separate_on_this_log(self):
        build_log(self.log, seed=8, n=120)
        rc, text = self.run_check()
        self.assertEqual(rc, 0, text[-1500:])
        # at least the order control of greedy separates some plan and passes none
        for line in text.split("\n"):
            if line.startswith("  greedy   order"):
                sep = int(line.split("separating")[1].split()[0])
                self.assertGreater(sep, 0)
                self.assertTrue(line.rstrip().endswith("passed 0"))
                break
        else:
            self.fail("no greedy order control line")


if __name__ == "__main__":
    unittest.main(verbosity=1)
