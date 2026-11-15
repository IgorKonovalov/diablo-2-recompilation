"""Off-slot tests of what plan 0065 Phase 0 staged (no game is run):
  - tools/sweep8_check.py: pick, p12, c2, h2, h3, b8 and xs on synthetic lines, each with a good and a bad case;
  - tools/mp_check.py gold, rooms and portalquest on synthetic lines;
  - tools/combat.py's use of the logged shield flag (DRB "sh") in place of --no-shield;
  - with workspace/: tools/sweep8_sessions.py check, the breakpoint addresses of the new logger lines as instruction
    starts of the pinned image (objdump, linear decode from the function's start), and gdb parsing and arming the new
    loggers against it with no process.
Stdlib only (objdump and gdb for the image tests):
    python3 -I tools/test_sweep8.py
"""
import base64
import contextlib
import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import combat  # noqa: E402
import mp_check  # noqa: E402
import sweep8_check as sc  # noqa: E402

ROOT = os.path.dirname(HERE)
WS = os.path.join(ROOT, "workspace")
EXE = os.path.join(WS, "install", "app", "game.exe")
EXCEL = os.path.join(WS, "merged", "data", "global", "excel")
HAVE_EXCEL = os.path.exists(os.path.join(EXCEL, "missiles.txt"))
HAVE_EXE = os.path.exists(EXE) and shutil.which("objdump") is not None

# every breakpoint address plan 0065 Phase 0 added, with the function start it lies in (re/symbols.csv, or the
# function's own entry); the test decodes linearly from the start and requires an instruction at the address
NEW_BPS = {
    0x005AE1F0: (0x005AE2CB, 0x005AE3F1, 0x005AE3C3),                                   # p12.py
    0x005BE3F0: (0x005BE480, 0x005BE6C1),                                               # use-sweep8.py H2
    0x00580610: (0x00580650,), 0x005806F0: (0x005807B7,),
    0x00562390: (0x00562453, 0x0056246C, 0x00562478, 0x00562484, 0x00562499),          # H3
    0x0054D230: (0x0054D230, 0x0054D294, 0x0054D2A4, 0x0054D2B4), 0x005BF240: (0x005BF240,),
    0x0057F700: (0x0057F700, 0x0057F72D), 0x0057F410: (0x0057F410, 0x0057F47F), 0x005608C0: (0x005608C0,),   # B8
    0x0057E7B0: (0x0057E7DF, 0x0057E7E9, 0x0057E7F8, 0x0057E807, 0x0057E816, 0x0057E822, 0x0057E82A, 0x0057E835,
                 0x0057E846, 0x0057E84B),                                               # player.py XS
    0x00622720: (0x0062279C,),                                                          # combat.py sh
    0x00584870: (0x00584A19, 0x00584A1E),                                               # two-players.py PQF/PQR
    0x0055C850: (0x0055C87C, 0x0055C8A9, 0x0055C8DC, 0x0055C92F),                       # two-gold.py
    0x00540900: (0x00540900, 0x00540A20, 0x00540ADF), 0x00540650: (0x0054066C,), 0x0053FF00: (0x0053FF00,),
}


def write(path, lines):
    with open(path, "w") as f:
        f.writelines(lines)


def L(tag, d):
    return "%s %s\n" % (tag, json.dumps(d))


def run_out(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-sweep8-")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def log(self, name, lines):
        p = os.path.join(self.tmp, name)
        write(p, lines)
        return p


def cb_line(lid, x0, y0, w, h, cells):
    raw = b"".join(struct.pack("<H", cells.get((x0 + i % w, y0 + i // w), 0)) for i in range(w * h))
    z = base64.b64encode(zlib.compress(json.dumps({"cells": [x0, y0, w, h, raw.hex()]}).encode())).decode()
    return L("CB", {"th": 1, "room": 1, "lid": lid, "rect": [x0, y0, w, h], "z": z})


class P12Test(Tmp):
    def grid(self):
        cells = {(x, 10): 1 for x in range(0, 20)}           # a row of bit-0-only cells at y 10, the rest free
        return cb_line(2, 0, 0, 20, 20, cells)

    def test_pick(self):
        p = self.log("a.log", [self.grid(), L("PLR", {"th": 1, "room": 1, "lid": 2, "x": 5, "y": 4})])
        pk = sc.pick(p, 2)
        self.assertEqual(pk["v"], 1)
        self.assertEqual(pk["cell"][1], 10)
        sx, sy = pk["stand"]
        self.assertTrue(2 <= max(abs(sx - pk["cell"][0]), abs(sy - 10)) <= 5)
        self.assertNotEqual(sy, 10)

    def mm(self, again):
        out = [self.grid(), L("PLR", {"th": 1, "room": 1, "lid": 2, "x": 5, "y": 4}),
               L("MMC", {"mid": 7, "cls": 90, "ct": 3, "c": 0, "x": 5, "y": 8, "sz": 1, "cached": 0, "f": 1}),
               L("MMR", {"mid": 7, "r": 1}),
               L("MMC", {"mid": 7, "cls": 90, "ct": 3, "c": 1, "x": 5, "y": 10, "sz": 1, "cached": 0, "f": 2}),
               L("MMR", {"mid": 7, "r": 2})]
        if again:
            out.append(L("MMC", {"mid": 7, "cls": 90, "ct": 3, "c": 0, "x": 5, "y": 11, "sz": 1, "cached": 0, "f": 3}))
        return out

    def test_d3_holds(self):
        rc, out = run_out(sc.check_p12, [self.log("a.log", self.mm(False))])
        self.assertEqual(rc, 0, out)
        self.assertIn("separating=1 lead=0 mismatches=0 verdict=D3 holds", out)
        self.assertIn("bit 0 set", out)

    def test_lead_holds(self):
        rc, out = run_out(sc.check_p12, [self.log("a.log", self.mm(True))])
        self.assertEqual(rc, 1, out)
        self.assertIn("verdict=against D3", out)

    def lead_log(self, fresh, again=True):
        out = [self.grid(), L("PLR", {"th": 1, "room": 1, "lid": 2, "x": 5, "y": 4}),
               L("MMC", {"mid": 9, "cls": 90, "ct": 3, "c": 0, "x": 5, "y": 10, "sz": 1, "cached": 0 if fresh else 1,
                         "f": 1}),
               L("MMR", {"mid": 9, "r": 1})]
        if again:
            out.append(L("MMC", {"mid": 9, "cls": 90, "ct": 3, "c": 0, "x": 5, "y": 11, "sz": 1, "cached": 0, "f": 2}))
        return out

    def test_lead_outcome_fresh(self):
        # a Nova carries on over a cell the grid marks bit-0-only, with a fresh word of 0: the lead's outcome
        rc, out = run_out(sc.check_p12, [self.log("a.log", self.lead_log(True))])
        self.assertEqual(rc, 1, out)
        self.assertIn("lead=1", out)
        self.assertIn("verdict=against the grid reading", out)

    def test_lead_outcome_cached_not_decisive(self):
        # a cached word is another point's: counted, but it tested nothing at this cell
        rc, out = run_out(sc.check_p12, [self.log("a.log", self.lead_log(False))])
        self.assertEqual(rc, 0, out)
        self.assertIn("lead=0", out)
        self.assertIn("LEAD-OUTCOME at a grid bit-0-only point, word c&5=0 (cached), the missile steps again", out)
        self.assertIn("verdict=not separated", out)

    def test_neighbour_bit_not_separating(self):
        # size 2 or 3: the word holds the neighbours' bits; own grid cell clear -> freed but not separating
        ev = [self.grid(), L("PLR", {"th": 1, "room": 1, "lid": 2, "x": 5, "y": 4}),
              L("MMC", {"mid": 8, "cls": 90, "ct": 3, "c": 1, "x": 5, "y": 9, "sz": 3, "cached": 0, "f": 1}),
              L("MMR", {"mid": 8, "r": 2})]
        rc, out = run_out(sc.check_p12, [self.log("a.log", ev)])
        self.assertEqual(rc, 0, out)
        self.assertIn("separating=0", out)
        self.assertIn("bit 0 clear", out)


@unittest.skipUnless(HAVE_EXCEL, "needs workspace/merged excel")
class C2Test(Tmp):
    def mc(self, v, lvl=1, f=0):
        blk = bytearray(0x50)
        struct.pack_into("<I", blk, 0, f)
        struct.pack_into("<i", blk, 0x10, 7)
        struct.pack_into("<iii", blk, 0x2C, 0, lvl, 0)
        return [L("MC0", {"p": blk.hex(), "n": 1}), L("MC1", {"k": 1, "m": {"path": {"v": v}}, "n": 2})]

    def test_read(self):
        rc, out = run_out(sc.check_c2, [self.log("a.log", self.mc(2112))], EXCEL)
        self.assertEqual(rc, 0, out)
        self.assertIn("spike1=1 separating=1 mismatches=0", out)

    def test_lead(self):
        rc, out = run_out(sc.check_c2, [self.log("a.log", self.mc(1920))], EXCEL)
        self.assertEqual(rc, 1, out)

    def test_predict_table(self):
        out = sc.predict(EXCEL)
        self.assertIn("  level 1: 2112 / 1920", out)
        self.assertTrue(any(x.startswith("  mp1 (type mpot)") and x.endswith("refused") for x in out))


class H2Test(Tmp):
    def lines(self, rate2):
        return [L("URM", {"uid": 1, "list": 0, "rem": 0, "len": 192, "state": 100, "f": 10}),
                L("UDV", {"v": 7680, "stat": 0}),
                L("USS", {"list": 55, "stat": 74, "rate": 40, "f": 10}),
                L("URM", {"uid": 1, "list": 55, "rem": 150, "len": 192, "state": 100, "f": 52}),
                L("UDV", {"v": 46080, "stat": 0}),
                L("UBL", {"num": 40 * 150 + 46080, "den": 342, "list": 55, "stat": 74, "slot": 0, "f": 52}),
                L("USS", {"list": 55, "stat": 74, "rate": rate2, "f": 52}),
                L("UFL", {"uid": 1, "list": 55, "f": 300}),
                L("URM", {"uid": 1, "list": 0, "rem": 0, "len": 192, "state": 100, "f": 400})]

    def test_blend(self):
        rc, out = run_out(sc.check_h2, [self.log("a.log", self.lines((40 * 150 + 46080) // 342))])
        self.assertEqual(rc, 0, out)
        self.assertIn("blends=1 separating=1 frees=1 mismatches=0", out)
        self.assertIn("use after a free", out)

    def test_wrong(self):
        rc, out = run_out(sc.check_h2, [self.log("a.log", self.lines(46080 // 192))])
        self.assertEqual(rc, 1, out)


@unittest.skipUnless(HAVE_EXCEL, "needs workspace/merged excel")
class H3Test(Tmp):
    def cls(self, code):
        return [c for c, _t in sc.item_codes(EXCEL)].index(code)

    def give(self, code, iid, results, user_type):
        out = [L("T26", {"th": 1, "flag": 1, "pt": 0, "pid": 1, "exp": 1, "item": {"id": iid, "c": self.cls(code)}})]
        for tag, ty, r in zip(("T26A", "T26B", "T26C"), (0x4C, 0x51, 0x50), results):
            out.append(L(tag, {"th": 1, "type": ty, "r": r, "iid": iid}))
        if user_type is not None:
            out += [L("T26P", {"th": 1, "pet": {"t": 1}}),
                    L("IU0", {"th": 1, "user": {"t": user_type}, "item": {"id": iid}, "ret": 0})]
        return out

    def test_reading(self):
        p = self.log("a.log", self.give("mp1", 5, (0, 0, 0), None) + self.give("hp1", 6, (1,), 1)
                     + self.give("wms", 7, (0, 1), 1) + self.give("yps", 8, (0, 0, 1), 1))
        rc, out = run_out(sc.check_h3, [p], EXCEL)
        self.assertEqual(rc, 0, out)
        self.assertIn("flagged=4 separating=1 mismatches=0", out)

    def test_lead(self):
        rc, out = run_out(sc.check_h3, [self.log("a.log", self.give("mp1", 5, (0, 0, 0), 1))], EXCEL)
        self.assertEqual(rc, 1, out)


class B8Test(Tmp):
    def lines(self, room, good=True):
        inv = [[100 + b, 0, 255, b, 0, 2, None] for b in range(16)] + [[1, 9, 255, 0, 0, 1, 8]]
        if not room:
            inv += [[200 + k, 0, 0, k % 10, k // 10, 0, None] for k in range(40)]
        moves, _stay = sc.b8_expect(inv, room)
        after = [r for r in inv if not (r[5] == 2 and r[3] >= 4)]
        ground = []
        for iid, m in moves.items():
            if m == "ground":
                ground.append(L("IPG", {"th": 1, "item": {"id": iid}}))
            else:
                after.append([iid, 0, 0, m[1] if good else m[1] - 1, m[2], 0, None])
        return [L("CCR", {"th": 1, "pid": 1, "inv": inv, "f": 5}), L("CCN", {"th": 1, "n": 3}),
                L("BOV0", {"th": 1, "ret": sc.CORPSE_BOV_RET, "pid": 1, "belt": 0, "inv": inv, "f": 5})] + ground + \
               [L("BOV1", {"th": 1, "pid": 1, "inv": after, "f": 5})]

    def test_room(self):
        rc, out = run_out(sc.check_b8, [self.log("a.log", self.lines(True))], True)
        self.assertEqual(rc, 0, out)
        self.assertIn("calls=1 moved=12 mismatches=0", out)

    def test_full(self):
        rc, out = run_out(sc.check_b8, [self.log("a.log", self.lines(False))], False)
        self.assertEqual(rc, 0, out)
        self.assertIn("box >= 4 item to the ground, as predicted", out)

    def test_wrong_cell(self):
        rc, out = run_out(sc.check_b8, [self.log("a.log", self.lines(True, good=False))], True)
        self.assertEqual(rc, 1, out)


class XsTest(Tmp):
    def lines(self, credit):
        return [L("XK0", {"th": 1, "ktype": 1, "kcls": 5, "kid": 40, "kxs": [53], "mtype": 1, "mid": 41, "vxs": []}),
                L("XSO", {"th": 1, "r": None}), L("XSK", {"th": 1, "r": 1}), L("XSKL", {"th": 1, "r": 4660}),
                L("XSV", {"th": 1, "r": 0}), L("XSL", {"th": 1, "r": 0}), L("XSG", {"th": 1, "r": 1}),
                L("XSF", {"th": 1, "r": [0, 3, 1]}), L("XSR", {"th": 1, "r": credit})]

    def test_state_killer(self):
        rc, out = run_out(sc.check_xs, [self.log("a.log", self.lines([0, 3, 1]))])
        self.assertEqual(rc, 0, out)
        self.assertIn("state_kills=1 separating=1 mismatches=0", out)

    def test_no_credit(self):
        rc, out = run_out(sc.check_xs, [self.log("a.log", self.lines(None))])
        self.assertEqual(rc, 1, out)


class GoldTest(Tmp):
    def lines(self, A, gj, give_j, give_h, n=2):
        plrs = {"t": 0, "p": [{"id": 1, "lid": 2, "mode": 1}, {"id": 2, "lid": 2, "mode": 1}],
                "pty": [{"id": 0, "m": [1, 2]}]}
        pl0 = [[1, 1000, 30, 1], [2, gj, 9, 1]]
        pl1 = [[1, 1000 + give_h, 30, 1], [2, gj + give_j, 9, 1]]
        share = A // n
        return [L("PLRS", plrs), L("GP0", {"pid": 1, "cap": 300000, "gold": 1000, "amt": A, "pile": 9, "c8": 0, "pl": pl0}),
                L("GPO", {"owner": None}), L("GS0", {"pid": 1, "amt": A}), L("GSN", {"amt": A, "n": n}),
                L("GC", {"mid": 2, "share": share, "cap": 90000, "gold": gj}),
                L("GSF", {"pid": 1, "left": A - share + (share - give_j), "cap": 300000, "gold": 1000}),
                L("GPR", {"rest": 0}), L("GPE", {"pl": pl1})]

    def test_odd(self):
        rc, out = run_out(mp_check.check_gold, [self.log("a.log", self.lines(7, 0, 3, 4))])
        self.assertEqual(rc, 0, out)
        self.assertIn("SEPARATING: odd A at n = 2", out)

    def test_overflow(self):
        rc, out = run_out(mp_check.check_gold, [self.log("a.log", self.lines(20, 89995, 5, 15))])
        self.assertEqual(rc, 0, out)
        self.assertIn("SEPARATING: the member's overflow returned to the picker", out)

    def test_even_split_reading_fails(self):
        rc, out = run_out(mp_check.check_gold, [self.log("a.log", self.lines(7, 0, 4, 3))])
        self.assertEqual(rc, 1, out)


class RoomsTest(Tmp):
    def test_shared(self):
        rows = lambda n78: {"acts": [{"a50": 0, "rooms": [[0xA, 0xB, 0, n78, 0, 2, 0, 2, None]]}], "diff": 0, "exp": 1}  # noqa: E731
        p = self.log("a.log", [L("CRC", {"c": 100, "old": 0, "new": 0xA}), L("ACTA", {"f": 1}),
                               L("CE", {"r": 0xA, "c": 100, "n78": 0}), L("CE", {"r": 0xA, "c": 200, "n78": 1}),
                               L("RP", rows(2)), L("CL", {"r": 0xA, "c": 100, "n78": 2}), L("RP", rows(1)),
                               L("CL", {"r": 0xA, "c": 200, "n78": 1}), L("RP", rows(0)), L("FREE", {"r": 0xA, "d": 0xB})])
        rc, out = run_out(mp_check.check_rooms, [p])
        self.assertEqual(rc, 0, out)
        self.assertIn("rp=3 frees=1 separating=1 mismatches=0", out)

    def test_free_held(self):
        p = self.log("a.log", [L("CE", {"r": 0xA, "c": 100, "n78": 0}), L("FREE", {"r": 0xA, "d": 0xB})])
        rc, out = run_out(mp_check.check_rooms, [p])
        self.assertEqual(rc, 1, out)


class PortalQuestTest(Tmp):
    def test_refuse_and_pass(self):
        p = self.log("a.log", [L("PQF", {"id": 2, "rec": 1, "flag": 21, "exp": 1}), L("PQR", {"r": 0})])
        self.assertEqual(run_out(mp_check.check_portalquest, [p], "refuse", 21)[0], 0)
        self.assertEqual(run_out(mp_check.check_portalquest, [p], "pass", 21)[0], 1)


class ShieldFlagTest(unittest.TestCase):
    def defend(self, sh, b, no_shield=()):
        ck = combat.Checker(None, no_shield=no_shield)
        d = {"t": 0, "id": 1, "m": 1, "st": {}}
        lines = [("DRB", {"u": 1, "b": b, "sh": sh})]
        ck.defence(d, (1, 2), lines, 0, False, True, {"exp": 1})
        return ck

    def test_logged_none(self):
        ck = self.defend(0, 0)
        self.assertEqual(ck.cases.get("player shield flag logged: none held"), 1)
        self.assertEqual(ck.cases.get("player block chance 0: no shield held (logged flag)"), 1)

    def test_logged_none_but_chance(self):
        with self.assertRaises(combat.Mismatch):
            self.defend(0, 5)

    def test_hand_fed_contradicted(self):
        with self.assertRaises(combat.Mismatch):
            self.defend(1, 0, no_shield=(1,))


@unittest.skipUnless(HAVE_EXE, "needs the pinned game.exe and objdump")
class ImageTest(unittest.TestCase):
    def test_breakpoints_are_instruction_starts(self):
        for start, addrs in NEW_BPS.items():
            out = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x%x" % start,
                                  "--stop-address=0x%x" % (max(addrs) + 16), EXE], capture_output=True, text=True).stdout
            starts = {int(m.group(1), 16) for m in re.finditer(r"^ +([0-9a-f]+):", out, re.M)}
            for a in addrs:
                with self.subTest(addr=hex(a)):
                    self.assertIn(a, starts)

    def test_sessions_check(self):
        import sweep8_sessions
        rc, out = run_out(sweep8_sessions.cmd_check)
        self.assertEqual(rc, 0, out)
        self.assertIn("SURVEY sweep8_sessions recipes=6 bad=0 sessions=7", out)

    @unittest.skipUnless(shutil.which("gdb"), "needs gdb")
    def test_gdb_arms(self):
        for g, ready in (("p12", "P12 logger armed"), ("sweep8-use", "USE8 logger armed"),
                         ("sweep8-xs", "PLAYER logger armed"), ("two-gold", "TWO-GOLD logger armed")):
            with self.subTest(logger=g):
                out = subprocess.run(["gdb", "-nx", "-batch", "-ex", "file " + EXE, "-x", "tools/gdb/%s.gdb" % g],
                                     cwd=ROOT, capture_output=True, text=True, timeout=600).stdout
                self.assertIn(ready, out)
                self.assertNotIn("LOGERR", out)
                self.assertNotIn("Traceback", out)


if __name__ == "__main__":
    unittest.main()
