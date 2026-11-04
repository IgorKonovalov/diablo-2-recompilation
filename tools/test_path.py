#!/usr/bin/env python3
"""No-game tests of tools/path.py (plan 0054 Phase 2): synthetic logs in the format of tools/gdb/path.py, written from the models
themselves, so the parser, the comparator, the controls and the tie are tested without a game. A log the model wrote must check
clean; every mutation of it (the return, a point, the seed, a cell of the live grid) must be reported; the outcome mix must see
what the log holds.

    python3 -I tools/test_path.py
"""
import base64
import collections
import json
import os
import random
import struct
import sys
import tempfile
import types
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

    def test_check_holds_the_review_sections(self):
        """`check` is the whole report: the former review tool's sections, the grid report, the rev 5 sections; RESULT stays the last line."""
        build_log(self.log, seed=9, n=40)
        out = os.path.join(self.d, "o.txt")
        self.assertEqual(P.main(["check", self.log, "--out", out]), 0)
        text = open(out).read()
        for head in ("1. PLANS AFTER A PROBE'S WRITE", "4. CONTROLS PER PATH TYPE", "type-1 controls on greedy-near's switch", "5. PLANS WHOSE OUTPUT NEEDS THE GRID",
                     "7. THE TIE'S FIRST 10 PLANS", "8. THE HEAD, BACKWARDS", "9. SEED WATCHPOINTS", "13. CORPSES IN THE LIVE CELLS", "14. THE TIE'S FIRST-PLAN", "16. THE SPIRAL'S PRODUCTS",
                     "code rules with W1", "W1 (path/0005)", "REV 5, TYPE-1 REQUEST SITES", "first plans per level"):
            self.assertIn(head, text)
        self.assertTrue(text.rstrip().splitlines()[-1].startswith("RESULT OK"), text[-300:])
        short = os.path.join(self.d, "s.txt")
        P.main(["mix", self.log, "--out", short])
        self.assertNotIn("1. PLANS AFTER", open(short).read())

    def test_empty_grid_restores_the_world(self):
        """Section 5 swaps the world builder for its count and must put it back."""
        build_log(self.log, seed=9, n=10)
        g = P.parse(self.log)[0]
        before = P.mk_world
        rows = [("s", g, pl, P.evaluate(pl)[1]) for pl in g.plans if pl.plc]
        P.empty_grid_counts(rows)
        self.assertIs(P.mk_world, before)

    def test_block_write_label(self):
        """A seed watchpoint's control that is not the LCG step is labelled by its writer, and only a listed `rep` with the high dword unmoved is the block write."""
        build_log(self.log, seed=7, n=3)
        k = P.parse(self.log)[0].plans[0].k
        with open(self.log, "a") as fh:
            for pc, to in ((0x00681F4F, "00000000:00000002"), (0x0057CAE6, "00000000:00000002"), (0x00682A1A, "00000005:00000002"), (0x00681F4F, "00000000:00000003"), (0x00401000, "00000000:00000002")):
                fh.write("SEEDW " + json.dumps({"ctl": 1, "k": k, "u": 1, "from": "00000001:00000002", "to": to, "pc": pc, "st": [0] * 6, "fr": 3, "n": 99999}) + "\n")
        rc, text = self.run_check()
        self.assertIn("control: block write rep stos 00681f4f 1", text)
        self.assertIn("control: block write rep movs 0057cae6 1", text)
        self.assertIn("control: block write rep movs 00682a1a 1", text)
        self.assertIn("control: other writer 00681f4f 1", text)                     # the high dword moved: no block write
        self.assertIn("control: other writer 00401000 1", text)
        self.assertNotIn("NOT the LCG step", text)

    def test_w1_arrival(self):
        """W1: after an act change the player is out of the tie's marks until it moves or its own plan; a level change within an act leaves it marked."""
        build_log(self.log, seed=3, n=12)
        g = P.parse(self.log)[0]
        plans = [pl for pl in g.plans if pl.plc]
        room = next(iter(plans[0].rooms))
        rec = dict(plans[0].rooms[room])
        script = [(103, (0, 0)), (29, (5, 5)), (29, (5, 5)), (29, (6, 5)), (29, (6, 5)), (28, (9, 9)), (28, (9, 9)), (40, (1, 1)), (40, (1, 1))]
        for pl, (lid, (x, y)) in zip(plans, script):
            pl.rooms = dict(pl.rooms)
            pl.rooms[room] = dict(rec, lid=lid)
            pl.plc["self"] = [1, 99]
            pl.plc["u"] = [[0, 1, 1, 1, 5000 + x, 5000 + y, room, 3, 1, 0x80, 0]]
        ar = P.player_arrivals(g)
        self.assertEqual([(a["from"], a["to"], a["act"]) for a in ar], [(103, 29, 1), (29, 28, 0), (28, 40, 1)])
        self.assertEqual([pl.w1 for pl in plans[:9]], [False, True, True, False, False, False, False, True, True])
        # its own plan ends the rule: the tail re-marks it
        for pl in plans:
            pl.w1 = False
        plans[2].plc["self"] = [0, 1]
        P.player_arrivals(g)
        self.assertEqual([pl.w1 for pl in plans[:4]], [False, True, False, False])
        # the tie drops the mark only under "code+w1"
        pl = plans[1]
        pl.cb = {a: (list(pl.rooms[a]["r"]), None, list(pl.rooms[a]["cells"])) for a in pl.rooms}
        t0 = P.tie_of(pl, True, False, "code")
        t1 = P.tie_of(pl, True, False, "code+w1")
        self.assertGreater(t0["cells"], t1["cells"])

    def test_l1_reserved_landing(self):
        """L1: a reserved point is in the tie from its L1M to its L1U, only under "code+w1+l1"."""
        build_log(self.log, seed=3, n=6)
        g = P.parse(self.log)[0]
        plans = [pl for pl in g.plans if pl.plc]
        a, b, c = plans[:3]
        room = next(iter(a.rooms))
        for pl in plans:
            pl.plc["u"] = []
            pl.cb = {r: (list(pl.rooms[r]["r"]), None, list(pl.rooms[r]["cells"])) for r in pl.rooms}
        mid1, mid2 = (a.plc["n"] + b.plc["n"]) / 2, (b.plc["n"] + c.plc["n"]) / 2
        g.l1m = [{"n": mid1, "room": room, "x": 5010, "y": 5010, "pat": 1, "mask": 0x80}, {"n": mid1, "room": room, "x": 5011, "y": 5020, "pat": 1, "mask": 0x80}]
        g.l1u = [{"n": mid2, "room": room, "x": 5010, "y": 5010, "pat": 1, "mask": 0x80}]
        self.assertEqual(P.reserved_landings(g), len(plans) - 1)
        self.assertEqual(a.l1, ())
        self.assertEqual(len(b.l1), 2)
        self.assertEqual(c.l1, ((room, 5011, 5020, 1, 0x80),))
        base = P.tie_of(b, True, False, "code+w1")["cells"]
        self.assertNotEqual(P.tie_of(b, True, False, "code+w1+l1")["cells"], base)
        self.assertEqual(P.tie_of(a, True, False, "code+w1+l1")["cells"], P.tie_of(a, True, False, "code+w1")["cells"])

    def test_units_cut(self):
        class Pl:
            pass
        pl = Pl()
        pl.plc = {"u": [0] * 120}
        self.assertTrue(P.units_cut(pl))
        pl.plc = {"u": [0] * 119}
        self.assertFalse(P.units_cut(pl))
        pl.plc = {"u": [0] * 400, "ucut": 0}
        self.assertFalse(P.units_cut(pl))
        pl.plc = {"u": [0] * 2, "ucut": 1}
        self.assertTrue(P.units_cut(pl))

    def test_spiral_stored_products(self):
        """SPX: truncation holds only when every separating product is the truncated one; a rounded line must not pass."""
        tab = [0.37 + i * 0.0017 for i in range(512)]

        def line(fn, n=20):
            xs, ys, r, a = [], [], 0, 0
            for _ in range(n):
                r += 0x2580
                a += 16
                xs.append(fn(tab[(a + 0x80) & 0x1FF] * float(r)))
                ys.append(fn(tab[a & 0x1FF] * float(r)))
            return {"k": 1, "x": xs, "y": ys}

        class G:
            pass
        g = G()
        g.spx = [line(int)]
        c = P.spiral_stored([g], tab)
        self.assertGreater(c["separating"], 0)
        self.assertEqual(c["separating, truncation"], c["separating"])
        self.assertEqual(c["separating, rounding"], 0)
        g.spx = [line(lambda v: int(round(v)))]
        c = P.spiral_stored([g], tab)
        self.assertEqual(c["separating, truncation"], 0)
        self.assertEqual(c["separating, rounding"], c["separating"])
        for kind, want in ((int, "HOLDS"), (lambda v: int(round(v)), "does not hold")):
            g.spx, g.t1s, g.l1m, g.l1u, g.cor = [line(kind)], [], [], [], []
            out = []
            P.rev5_sections([g], out.append, tab)
            self.assertTrue(any("truncation: " + want in s for s in out), out)

    def test_rev5_lines_parse_and_verdicts(self):
        build_log(self.log, seed=7, n=3)
        plus = [0] * 25
        for i in (7, 11, 12, 13, 17):
            plus[i] = 0x8000
        square = [0] * 25
        for i in (6, 7, 8, 11, 12, 13, 16, 17, 18):
            square[i] = 0x8000
        lines = [("COR", {"site": 0x005A65D9, "u": [1, 5, 1, 0, 9, 9], "side": "srv", "arg": 1, "after": square, "c": 1}),
                 ("COR", {"site": 0x004B05E3, "u": [1, 5, 1, 0, 9, 9], "side": "cli", "arg": 0, "after": plus, "c": 1}),
                 ("COR", {"site": 0x004B05E3, "u": [1, 5, 1, 0, 9, 9], "side": "srv", "arg": 0, "after": plus, "c": 2}),
                 ("COR", {"site": 0x00401000, "u": [1, 5, 1, 0, 9, 9], "side": "srv", "arg": 1, "after": [0] * 25, "c": 1}),
                 ("T1S", {"site": 0x005E3BCC, "u": [1, 5, 1, 0, 9, 9], "side": "srv", "c": 1}),
                 ("T1S", {"site": 0x005E3BCC, "u": [1, 5, 1, 0, 9, 9], "side": "srv", "c": 64}),
                 ("L1M", {"site": 0x005D9EF8, "u": [0, 5, 1, 18, 9, 9], "side": "srv", "x": 1, "y": 1, "pat": 1, "mask": 0x80, "room": 1, "c": 1}),
                 ("L1M", {"site": 0x005CB902, "u": [1, 5, 1, 18, 9, 9], "side": "srv", "x": 1, "y": 1, "pat": 1, "mask": 0x80, "room": 1, "c": 1}),
                 ("BRK", {"fn": 0x00679C80, "ty": 13, "side": "srv", "ra": 1, "pra": 2, "ctl": 1, "c": 20, "fr": 3}),
                 ("BRK", {"fn": 0x00679C80, "ty": 13, "side": "srv", "ra": 1, "pra": 2, "ctl": 1, "c": 512, "fr": 3})]
        with open(self.log, "a") as fh:
            for tag, d in lines:
                fh.write(tag + " " + json.dumps(dict(d, n=99999)) + "\n")
        out = os.path.join(self.d, "o.txt")
        P.main(["check", self.log, "--out", out])
        text = open(out).read()
        self.assertIn("'3x3', 'as read'", text)
        self.assertIn("'plus', 'as read'", text)
        self.assertIn("AGAINST THE TABLE", text)
        self.assertIn("UNLISTED CALLER", text)
        self.assertIn("AGAINST THE READING", text)
        self.assertRegex(text, r"005e3bcc AiHireFollow +srv 64 cli 0")
        self.assertRegex(text, r"00679c80 control: greedy side=srv control hits=512")

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


class FakeGdb:
    """The part of gdb's Python API tools/gdb/path.py uses, over a sparse memory: every read is served and every write fails the test."""

    def __init__(self):
        self.memv = {}
        self.regs = collections.defaultdict(int)
        self.bps = {}
        self.out = []
        self.module = types.ModuleType("gdb")
        fake = self

        class Breakpoint:
            def __init__(self, spec, *a, **k):
                self.spec = spec
                if spec.startswith("*0x"):
                    fake.bps[int(spec[1:], 16)] = self

        class Inferior:
            def read_memory(self, a, n):
                return bytes(fake.memv.get(a + i, 0) for i in range(n))

            def write_memory(self, *a):
                raise AssertionError("the logger wrote game memory")

        def parse_and_eval(e):
            if e.startswith("$") and "=" not in e:
                return fake.regs[e[1:]]
            raise AssertionError("unexpected expression %r" % e)
        m = self.module
        m.Breakpoint, m.parse_and_eval = Breakpoint, parse_and_eval
        m.MemoryError = type("MemoryError", (Exception,), {})
        m.selected_inferior = Inferior
        m.write = self.out.append
        m.execute = lambda *a, **k: (_ for _ in ()).throw(AssertionError("the logger ran a gdb command"))
        m.BP_WATCHPOINT, m.WP_WRITE = 6, 1

    def w32(self, a, v):
        for i, b in enumerate(struct.pack("<I", v & 0xFFFFFFFF)):
            self.memv[a + i] = b

    def w16(self, a, v):
        for i, b in enumerate(struct.pack("<H", v & 0xFFFF)):
            self.memv[a + i] = b

    def hit(self, addr, **regs):
        self.regs.update(regs)
        self.bps[addr].stop()

    def lines(self, tag):
        return [json.loads(s[len(tag) + 1:]) for s in "".join(self.out).splitlines() if s.startswith(tag + " ")]


GAME, UNIT, PATH, ROOM, MAP, CELLS, CTX, STK, OBJ, OBJD, OBJR, OBJP = 0x100000, 0x200000, 0x201000, 0x300000, 0x301000, 0x302000, 0x400000, 0x500000, 0x600000, 0x601000, 0x602000, 0x603000


class Logger(unittest.TestCase):
    """tools/gdb/path.py rev 5 on a fake gdb: no game. Read-only, the new lines, the counted breaks, the objects before the cut."""

    def load(self, **env):
        self.g = FakeGdb()
        old = dict(os.environ)
        os.environ.update({k: str(v) for k, v in env.items()})
        sys.modules["gdb"] = self.g.module
        try:
            src = os.path.join(HERE, "gdb", "path.py")
            exec(compile(open(src).read(), src, "exec"), {"__name__": "logger"})
        finally:
            del sys.modules["gdb"]
            os.environ.clear()
            os.environ.update(old)
        g = self.g
        g.hit(0x0052C312, edi=GAME)
        g.w32(UNIT, 1)
        g.w32(UNIT + 4, 561)
        g.w32(UNIT + 0x0C, 77)
        g.w32(UNIT + 0x10, 12)
        g.w32(UNIT + 0x2C, PATH)
        g.w32(UNIT + 0x80, GAME)
        g.w16(PATH + 2, 5005)
        g.w16(PATH + 6, 5005)
        g.w32(PATH + 0x1C, ROOM)
        g.w32(PATH + 0x30, UNIT)
        g.w32(PATH + 0x48, 1)
        g.w32(PATH + 0x4C, 0x100)
        g.w32(ROOM + 0x20, MAP)
        for i, v in enumerate((5000, 5000, 10, 10)):
            g.w32(MAP + 4 * i, v)
        g.w32(MAP + 0x20, CELLS)
        for i, v in enumerate((5000, 5000, 10, 10)):
            g.w32(ROOM + 0x4C + 4 * i, v)
        return g

    def plan(self, g, ty, fl):
        g.w32(PATH + 0x3C, ty)
        g.w32(PATH + 0x34, fl)
        g.w32(STK, 0x0057F11C)
        g.w32(STK + 4, PATH)
        g.w32(STK + 8, UNIT)
        g.hit(0x00649970, esp=STK)

    def test_source_is_read_only(self):
        text = open(os.path.join(HERE, "gdb", "path.py")).read()
        for word in ("write_memory", "PATH_SPIRAL_PROBE", "spiral_probe", "spiral_sim", "gdb.execute", '"probe"'):
            self.assertNotIn(word, text)
        sessions = open(os.path.join(HERE, "path_sessions.py")).read()
        self.assertNotIn("PATH_SPIRAL_PROBE", sessions)

    def test_every_new_break_is_armed(self):
        g = self.load()
        for a in (0x0067A1AF, 0x0067A1E0, 0x005E3BCC, 0x005E4300, 0x005E5DD9, 0x005E5EE7, 0x005E5F40, 0x005CD484, 0x005CBC44, 0x005D9123, 0x005D9EF8, 0x005DA5D5, 0x005CB902,
                  0x005DA1F3, 0x005DA269, 0x005D94E8, 0x005CBA3B, 0x00649F70, 0x00649FB2, 0x00649FE6):
            self.assertIn(a, g.bps)
        self.assertIn("armed rev 5", "".join(g.out))

    def test_spiral_products_join_their_plan(self):
        g = self.load()
        self.plan(g, 14, 0x40000)
        for i, (x, y) in enumerate(((100, -7), (200, -9))):
            g.w32(0x700000 - 0x20, x)
            g.hit(0x0067A1AF, ebp=0x700000)
            g.w32(0x700000 - 0x20, y)
            g.hit(0x0067A1E0, ebp=0x700000)
        g.hit(0x00649C8F, esp=STK, eax=77)
        k = g.lines("PLN")[0]["n"]
        self.assertNotIn("probe", g.lines("PLN")[0])
        spx = g.lines("SPX")
        self.assertEqual([(s["k"], s["x"], s["y"]) for s in spx], [(k, [100, 200], [-7, -9])])
        # with no plan open, and for another type: nothing kept
        g.hit(0x0067A1AF, ebp=0x700000)
        self.plan(g, 13, 0x40000)
        g.hit(0x0067A1AF, ebp=0x700000)
        g.hit(0x00649C8F, esp=STK, eax=0)
        self.assertEqual(len(g.lines("SPX")), 1)
        self.assertFalse([s for s in g.out if "LOGERR" in s], g.out)

    def test_break_lines_are_counted(self):
        g = self.load()
        g.w32(CTX + 0x30, PATH)
        for _ in range(70):
            g.hit(0x00679C80, ecx=CTX, esp=STK)
        lines = g.lines("BRK")
        self.assertEqual([b["c"] for b in lines], list(range(1, 21)) + [32, 64])
        self.assertTrue(all(b["ctl"] == 1 and b["side"] == "srv" for b in lines))

    def test_objects_survive_the_cut_and_carry_hascollision(self):
        g = self.load(PATH_CAP_UNITS=2)
        self.plan(g, 13, 0)
        g.w32(CTX + 0x30, PATH)
        g.w32(CTX + 8, ROOM)
        # one object, mode 2, HasCollision[2] = 1 and [1] = 0 at +0x120 + mode (0x006219D3)
        g.w32(GAME + 0x1520, OBJ)
        g.w32(OBJ, 2)
        g.w32(OBJ + 4, 7)
        g.w32(OBJ + 0x10, 2)
        g.w32(OBJ + 0x14, OBJD)
        g.w32(OBJ + 0x2C, OBJP)
        g.w32(OBJD, OBJR)
        g.w32(OBJP, ROOM)
        g.w32(OBJP + 0x0C, 5003)
        g.w32(OBJP + 0x10, 5003)
        g.memv[OBJR + 0x122] = 1
        # three monsters in one hash chain: one must be cut, objects first
        chain = [0x210000, 0x211000, 0x212000]
        g.w32(GAME + 0x1320, chain[0])
        for i, u in enumerate(chain):
            g.w32(u, 1)
            g.w32(u + 0x2C, u + 0x800)
            g.w16(u + 0x802, 5004)
            g.w16(u + 0x806, 5004)
            g.w32(u + 0xE4, chain[i + 1] if i + 1 < len(chain) else 0)
        g.hit(0x00649BAE, ecx=CTX, eax=0x00679C80)
        plc = g.lines("PLC")[0]
        self.assertEqual(plc["ucut"], 2)
        self.assertEqual(plc["ucap"], 2)
        self.assertEqual(plc["u"][0][0], 2)
        self.assertEqual(len(plc["u"][0]), 14)
        self.assertEqual(plc["u"][0][13], 1)
        self.assertTrue(P.object_marked(plc["u"][0], {}))
        self.assertFalse([s for s in g.out if "LOGERR" in s], g.out)

    def test_type1_landing_and_corpse_lines(self):
        g = self.load()
        g.hit(0x005E3BCC, esi=UNIT, esp=STK)
        g.w32(STK, PATH)
        g.hit(0x005CD484, esp=STK)
        t1 = g.lines("T1S")
        self.assertEqual([(t["site"], t["u"][2], t["side"]) for t in t1], [(0x005E3BCC, 77, "srv"), (0x005CD484, 77, "srv")])
        for i, v in enumerate((ROOM, 5006, 5007, 1, 0x80)):
            g.w32(STK + 4 * i, v)
        g.hit(0x005D9EF8, edi=UNIT, esp=STK)
        l1 = g.lines("L1M")[0]
        self.assertEqual((l1["site"], l1["room"], l1["x"], l1["y"], l1["pat"], l1["mask"], l1["u"][2]), (0x005D9EF8, ROOM, 5006, 5007, 1, 0x80, 77))
        g.hit(0x005CBA3B, edi=UNIT, esp=STK)
        self.assertEqual(g.lines("L1U")[0]["x"], 5006)
        # UnitCorpseColl(unit, 1) from 0x005A65D9: the line comes at the return, with the cells as they are then; a cell of the near room's and one off the grid
        g.w32(STK, 0x005A65D9 + 5)
        g.w32(STK + 4, UNIT)
        g.w32(STK + 8, 1)
        g.hit(0x00649F70, esp=STK)
        self.assertEqual(g.lines("COR"), [])
        g.w16(CELLS + 2 * (5 * 10 + 5), 0x8000)
        g.hit(0x00649FE6, esp=STK)
        c = g.lines("COR")[0]
        self.assertEqual((c["site"], c["arg"], c["side"], c["x"], c["y"]), (0x005A65D9, 1, "srv", 5005, 5005))
        self.assertEqual(len(c["after"]), 25)
        self.assertEqual(c["after"][12], 0x8000)
        self.assertEqual(sum(1 for v in c["after"] if v), 1)
        self.assertFalse([s for s in g.out if "LOGERR" in s], g.out)
        # a client unit's call
        g.w32(UNIT + 0x80, 0x777)
        g.w32(STK, 0x004B05E3 + 5)
        g.w32(STK + 8, 0)
        g.hit(0x00649F70, esp=STK)
        g.hit(0x00649FB2, esp=STK)
        self.assertEqual(g.lines("COR")[1]["side"], "cli")

    def test_reach_walk(self):
        """tools/path_reach.py on a made-up listing: a depth limit, the int3 end of a function, and a target met through a callee."""
        import path_reach as R
        ins = [(0x10, "call   0x20"), (0x15, "ret"), (0x16, "int3"), (0x17, "call   0x99"), (0x20, "call   0x30"), (0x25, "int3"), (0x30, "call   0x99"), (0x35, "int3")]
        self.assertEqual(R.reach(ins, 0x10, {0x99}, 2)[1], [((0x10, 0x20, 0x30), 0x30, 0x99)])
        self.assertEqual(R.reach(ins, 0x10, {0x99}, 1)[1], [])

    def test_line_cap_per_site(self):
        g = self.load(PATH_CAP_LINES=3)
        for i, v in enumerate((ROOM, 5006, 5007, 1, 0x80)):
            g.w32(STK + 4 * i, v)
        for _ in range(6):
            g.hit(0x005D9EF8, edi=UNIT, esp=STK)
        self.assertEqual(len(g.lines("L1M")), 3)
        self.assertEqual(len(g.lines("CAP")), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
