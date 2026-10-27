"""Off-slot tests of what plan 0051 Phase 1a staged (no game is run):
  - the plan 0038 S1b leftover pieces: the hover marker CH of tools/gdb/calc.py with `tools/calc.py hover`, the
    SUNITPRE caller `ra` of tools/gdb/seed-tree-core.gdb with `tools/rng.py seedtree`, the step grammar of
    tools/gdb/s1b-pieces.steps, and (when workspace/ holds them) the pinned game.exe's call sites behind both and the
    kept run:2026-10-16-calc and run:2026-10-11-seed-tree logs, which must check as before with CH and ra lines added;
  - the plan 0044 shortfalls: `tools/mp_check.py leave` (MP30) on synthetic QL0..QL1 lines, and (with workspace/) the
    three new tools/mp_saves.py recipes against their own conditions and a recipe that must fail them.
Stdlib only (objdump for the call-site test):
    python3 -I tools/test_p51_staging.py
"""
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import calc  # noqa: E402
import mp_check  # noqa: E402
import rng  # noqa: E402

ROOT = os.path.dirname(HERE)
WS = os.path.join(ROOT, "workspace")
EXE = os.path.join(WS, "install", "app", "game.exe")
LOGS = os.path.join(WS, "logs")
EXCEL = os.path.join(WS, "merged", "data", "global", "excel")
STEP_CMDS = {"click": 2, "rclick": 2, "dclick": 2, "move": 2, "key": 1, "keydown": 1, "keyup": 1, "sleep": 1,
             "shot": 1, "type": 1}


def write(path, lines):
    with open(path, "w") as f:
        f.writelines(lines)


def run_out(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


def ce(ra2, pool="itemscode", off=0, th=1):
    return "CE " + json.dumps({"code": 1, "len": 2, "ra": 0x00627C7F, "ra2": ra2, "pool": pool, "off": off,
                               "th": th}) + "\n"


class Hover(unittest.TestCase):
    def test_synthetic(self):
        lines = ["CALC logger armed\n",
                 "CH " + json.dumps({"ra": 0x0048E97D, "arg": 5, "rec": 0x1000, "n": 0, "b4": 1, "b6": 7, "a4": -1,
                                     "th": 1}) + "\n",
                 "CH " + json.dumps({"ra": 0x0048E97D, "arg": 5, "rec": 0x2000, "n": 40, "b4": 2, "b6": 8, "a4": 12,
                                     "th": 1}) + "\n",
                 ce(0x00486434, off=12), "CX {\"v\": 3, \"th\": 1}\n",
                 ce(0x005BEE04, off=30), "CX {\"v\": 9, \"th\": 1}\n",
                 ce(0x00644E02, pool="skillscode"), "SUNITPRE unit=1 type=0 class=1 p=2 pre=3:4 ra=00569f58\n"]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "h.log")
            write(p, lines)
            rc, out = run_out(calc.cmd_hover, [p])
            self.assertEqual(rc, 0)
            self.assertIn("CH lines 2 (entries >= 42), records 2, b4 1:1 2:1", out)
            self.assertIn("evaluation from 0x00486370: ra2 0x00486434 pool itemscode off 12: 1", out)
            self.assertIn("SURVEY calc_hover logs=1 no_marker=0 ch_lines=2 ch_entries=42 records=2 hover_evals=1 "
                          "item_evals=2 bad=0", out)
            q = os.path.join(d, "old.log")
            write(q, [ce(0x005BEF16), "CH {bad\n"])
            rc, out = run_out(calc.cmd_hover, [q])
            self.assertEqual(rc, 1)
            self.assertIn("no_marker=1", out)
            # the replay parser skips the CH tag: the CE frames are the same with and without it
            ev_with, an_with = calc.parse_calc_log(p)
            r = os.path.join(d, "noch.log")
            write(r, [ln for ln in lines if not ln.startswith("CH ")])
            ev_without, an_without = calc.parse_calc_log(r)
            self.assertEqual([f["ce"] for f in ev_with], [f["ce"] for f in ev_without])
            self.assertEqual(an_with, an_without)


def seedtree_log(n, g, ras):
    lo, hi = rng.step(n & rng.MASK, rng.INIT_HIGH)
    out = ["# d2run seed=%d gdb=tools/gdb/s1b-pieces.gdb\n" % n,
           "GAME override=1 g=%08x map=%08x seed=%08x:%08x\n" % (g, n, n, rng.INIT_HIGH)]
    for i, ra in enumerate(ras):
        tail = "" if ra is None else " ra=%08x" % ra
        out.append("SUNITPRE unit=%08x type=0 class=1 p=%08x pre=%08x:%08x%s\n" % (0x5000 + i, g + 0xD0, lo, hi, tail))
    return out


class SeedTree(unittest.TestCase):
    def test_synthetic(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "s.log")
            write(p, seedtree_log(12345, 0x02DF007C, [0x00569F58, 0x005338DD, 0x00401234, None]))
            rc, out = run_out(rng.seedtree, [p])
            self.assertIn("server unit caller: call at 0x00569f53 (ra 0x00569f58), type 0: 1", out)
            self.assertIn("server unit caller: call at 0x005338d8 (ra 0x005338dd), type 0: 1", out)
            self.assertIn("server unit caller: ra 0x00401234, not one of the six direct calls of 0x00552DF0, type 0: 1",
                          out)
            self.assertIn("server unit caller: ra not logged (seed-tree-core.gdb before plan 0051): 1", out)
            self.assertIn("seedtree: 1/1 match", out)


class Steps(unittest.TestCase):
    def test_grammar(self):
        path = os.path.join(HERE, "gdb", "s1b-pieces.steps")
        n = 0
        with open(path) as f:
            raw_lines = f.readlines()
        for raw in raw_lines:
            line = raw.split("#", 1)[0].strip()   # tools/xdrive.py's own reading of a steps line
            if not line:
                continue
            cmd, *a = line.split(None, 2) if not line.startswith("type ") else ["type", line[5:]]
            self.assertIn(cmd, STEP_CMDS, line)
            self.assertEqual(len(a), STEP_CMDS[cmd], line)
            if cmd in ("click", "rclick", "dclick", "move"):
                x, y = int(a[0]), int(a[1])
                self.assertTrue(0 <= x < 800 and 0 <= y < 600, line)
            n += 1
        self.assertGreater(n, 30)


@unittest.skipUnless(os.path.exists(EXE) and shutil.which("objdump"), "pinned game.exe or objdump missing")
class CallSites(unittest.TestCase):
    def test_sites(self):
        dis = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x00401000",
                              "--stop-address=0x006D0000", EXE], capture_output=True, text=True, check=True).stdout
        calls = re.findall(r"^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*call\s+0x552df0$", dis, re.M)
        rets = {int(a, 16) + len(b.split()): int(a, 16) for a, b in calls}
        self.assertEqual(rets, rng.UNITSEED_CALLS)
        evals = re.findall(r"^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*call\s+0x627c20$", dis, re.M)
        inside = sorted(int(a, 16) + len(b.split()) for a, b in evals if 0x486370 <= int(a, 16) < 0x486565)
        self.assertEqual(tuple(inside), calc.HOVER_RA)
        self.assertRegex(dis, r"(?m)^\s*48e978:\s+e8 f3 79 ff ff\s+call\s+0x486370$")


@unittest.skipUnless(os.path.isdir(EXCEL) and os.path.exists(os.path.join(LOGS, "calc-s3-sor-hover.log")),
                     "kept run:2026-10-16-calc logs missing")
class KeptCalc(unittest.TestCase):
    def test_check_unchanged_with_ch(self):
        src = os.path.join(LOGS, "calc-s3-sor-hover.log")
        with tempfile.TemporaryDirectory() as d:
            dst = os.path.join(d, "with-ch.log")
            with open(src, errors="replace") as fi, open(dst, "w") as fo:
                for i, ln in enumerate(fi):
                    if i % 500 == 0:
                        fo.write("CH " + json.dumps({"ra": 0x0048E97D, "arg": i, "rec": 0, "n": 0, "th": 1}) + "\n")
                    fo.write(ln)
            rc1, a = run_out(calc.cmd_check, EXCEL, [src])
            rc2, b = run_out(calc.cmd_check, EXCEL, [dst])
            survey = [ln for ln in a.splitlines() if ln.startswith("SURVEY")]
            self.assertEqual(rc1, rc2)
            self.assertEqual(survey, [ln for ln in b.splitlines() if ln.startswith("SURVEY")])


@unittest.skipUnless(os.path.exists(os.path.join(LOGS, "run-p1-12345-a.log")), "kept run:2026-10-11 logs missing")
class KeptSeedTree(unittest.TestCase):
    def test_unchanged_with_ra(self):
        src = os.path.join(LOGS, "run-p1-12345-a.log")
        with tempfile.TemporaryDirectory() as d:
            dst = os.path.join(d, "with-ra.log")
            with open(src, errors="replace") as fi, open(dst, "w") as fo:
                for ln in fi:
                    fo.write(ln.rstrip("\n") + " ra=00569f58\n" if ln.startswith("SUNITPRE ") else ln)
            _, a = run_out(rng.seedtree, [src])
            _, b = run_out(rng.seedtree, [dst])
            last = [ln for ln in a.splitlines() if ln.startswith("seedtree:")]
            self.assertEqual(last, [ln for ln in b.splitlines() if ln.startswith("seedtree:")])
            self.assertIn("server unit caller: ra not logged", a)
            self.assertIn("server unit caller: call at 0x00569f53", b)


def jl(tag, d):
    return "%s %s\n" % (tag, json.dumps(d))


class Leave(unittest.TestCase):
    J, H = [0, 0, 2], [0, 1, 1]

    def leave(self, extra=None):
        j = self.J
        out = [jl("QS", {"ret": "0", "rec": 1, "w": 4, "b": 2, "old": 0}),
               jl("QL0", {"pl": j}),
               jl("QE9", {"q": 3, "fn": "00592c80", "item": [4, 524, 9], "pl": j}),
               jl("Q4B", {"cnt": 2}), jl("Q4C", {"code": "bks ", "cnt": 1}),
               jl("QE9", {"q": 3, "fn": "00592c80", "item": [4, 10, 11], "pl": j}),
               jl("Q4B", {"cnt": 1}), jl("Q4C", {"code": "hp1 ", "cnt": 1}),
               jl("QE10", {"pl": j}), jl("QLR", {"ret": "00592d1a", "list": "0abc", "id": 2}),
               jl("QC", {"ret": "0", "rec": 1, "w": 4, "b": 3, "old": 8}), jl("QL1", {})]
        return out + (extra or [])

    def run_leave(self, lines):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.log")
            write(p, lines)
            return run_out(mp_check.check_leave, [p])

    def test_good(self):
        rc, out = self.run_leave(self.leave())
        self.assertEqual(rc, 0, out)
        self.assertIn("SURVEY mp_check leave logs=1 leaves=1 mismatches=0", out)
        self.assertIn("Q4C count predicted (code 'bks ')", out)
        self.assertIn("QC word 4 bit 3 inside a leave", out)
        self.assertNotIn("QS word 4 bit 2 inside a leave", out)

    def test_bad(self):
        lines = self.leave()
        lines[4] = jl("Q4C", {"code": "bks ", "cnt": 2})                  # no decrement
        lines[5] = jl("QE9", {"q": 3, "fn": "00592c80", "item": [4, 10, 11], "pl": self.H})   # another player
        rc, out = self.run_leave(lines + [jl("QE10", {"pl": self.J})])  # outside a leave
        self.assertEqual(rc, 1)
        self.assertIn("mismatches=3", out)
        rc, out = self.run_leave(self.leave()[:9] + [jl("QL0", {"pl": self.J})])   # no QL1 before the next leave
        self.assertIn("QL0 inside an open leave", out)


@unittest.skipUnless(os.path.isdir(EXCEL), "excel tables missing")
class Recipes(unittest.TestCase):
    def test_conditions(self):
        import d2s
        import mp_saves
        if not all(os.path.exists(b) for b in mp_saves.BASES.values()):
            self.skipTest("base saves missing")
        t = d2s.Tables(EXCEL)
        cond = mp_saves.checks(EXCEL)
        with tempfile.TemporaryDirectory() as d:
            parsed = {}
            for n in ("mp-sock-join", "mp-wound-join", "mp-pal-conv", "mp-pvp-join"):
                with contextlib.redirect_stdout(io.StringIO()):
                    b = mp_saves.build_one(EXCEL, n, os.path.join(d, n + ".d2s"))
                parsed[n] = (d2s.parse(b, t.isc, t.kinds), d2s.quest_words(b), d2s.parse_waypoints(b))
        for n in ("mp-sock-join", "mp-wound-join", "mp-pal-conv"):
            self.assertEqual([lab for lab, p in cond[n] if not p(*parsed[n])], [], n)
            self.assertNotEqual([lab for lab, p in cond[n] if not p(*parsed["mp-pvp-join"])], [], n)


if __name__ == "__main__":
    unittest.main()
