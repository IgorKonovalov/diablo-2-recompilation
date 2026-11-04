"""Tests for the plan 0055 Phase 2b tools (no game, no gdb, no wine): python3 -I tools/test_frame_window.py

  - the reader and checker on synthetic windows: the clean window passes (a) whole and (b) unmoved, and each negative
    control (a gap, a repeat, an unclosed pair, a seed off by one, a reversed pair, an unparsed line, a lost FT1) fails
    the test it is for (`frame.py window-selftest` runs the same);
  - the logger tools/gdb/frame.py run under a fake `gdb` module over a fake memory: a simulated window of frames is
    written by the logger's own handlers, read back by the reader (whole and unmoved), the logger writes no byte of
    memory, a control-file window opens at the next FT0, and the window breakpoints are disabled outside a window;
  - the logger's source holds no write (rule 17) and every breakpoint address is a symbols.csv address, a finding's
    address, or one of the derived return sites checked against the binary when it is present;
  - the session runner's plan (--dry), its refusal to launch without --launch, and its gate on a clean and a broken log;
  - tools/frame_volume.py estimate13 prints what it printed before estimate13_rows existed (row counts and the totals).
"""
import io
import json
import os
import re
import runpy
import subprocess
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import frame_window as fw  # noqa: E402

EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
LOGGER = os.path.join(HERE, "gdb", "frame.py")


# ---------------------------------------------------------------------------------------------------- a fake gdb
class FakeMem:
    """Sparse memory in two regions; read-only for the logger (write_memory does not exist)."""

    def __init__(self):
        self.low = bytearray(0x200000)
        self.hc = bytearray(0x1000)      # g_HitClassCounter's page, 0x0088C000

    def get(self, a, n):
        if 0 <= a and a + n <= len(self.low):
            return bytes(self.low[a:a + n])
        if 0x0088C000 <= a and a + n <= 0x0088C000 + len(self.hc):
            return bytes(self.hc[a - 0x0088C000: a - 0x0088C000 + n])
        raise FakeMemoryError("unmapped %#x" % a)

    readonly = False      # set while the logger's handler runs: any write is a test failure

    def put(self, a, data):
        if self.readonly:
            raise AssertionError("the logger wrote memory at %#x" % a)
        if 0x0088C000 <= a < 0x0088D000:
            self.hc[a - 0x0088C000: a - 0x0088C000 + len(data)] = data
        else:
            self.low[a:a + len(data)] = data

    def u32(self, a, v):
        self.put(a, int(v & 0xFFFFFFFF).to_bytes(4, "little"))


class FakeMemoryError(Exception):
    pass


def make_gdb(mem, regs, out):
    g = types.ModuleType("gdb")
    g.MemoryError = FakeMemoryError
    g.registry = {}

    class Breakpoint:
        def __init__(self, spec, internal=False):
            self.addr = int(spec[1:], 16)
            self.enabled = True
            self.hit_count = 0
            self.silent = False
            g.registry.setdefault(self.addr, []).append(self)

    g.Breakpoint = Breakpoint

    class Inf:
        def read_memory(self, a, n):
            return mem.get(a, n)

    g.thread = 1
    g.selected_thread = lambda: types.SimpleNamespace(num=g.thread)
    g.selected_inferior = lambda: Inf()
    g.parse_and_eval = lambda e: regs[e[1:]]
    g.write = lambda s: out.write(s)
    return g


class LoggerRig:
    """Runs tools/gdb/frame.py against a fake gdb; `hit(addr, **regs)` is a stop at that breakpoint."""

    GAME = 0x100000

    def __init__(self, env=None):
        self.mem, self.regs, self.out = FakeMem(), {}, io.StringIO()
        self.gdb = make_gdb(self.mem, self.regs, self.out)
        self.env = dict(env or {})
        self.before = None
        old_gdb, old_env = sys.modules.get("gdb"), dict(os.environ)
        sys.modules["gdb"] = self.gdb
        os.environ.update(self.env)
        try:
            runpy.run_path(LOGGER)
        finally:
            os.environ.clear()
            os.environ.update(old_env)
            if old_gdb is None:
                del sys.modules["gdb"]
            else:
                sys.modules["gdb"] = old_gdb
        for n in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp"):
            self.regs[n] = 0
        self.regs["esp"] = 0x1F0000

    def hit(self, addr, **r):
        for k, v in r.items():
            self.regs[k] = v
        res = []
        self.mem.readonly = True
        try:
            for b in self.gdb.registry[addr]:
                if b.enabled:
                    res.append(b.stop())
        finally:
            self.mem.readonly = False
        return res

    def enabled(self):
        return sorted({a for a, bs in self.gdb.registry.items() for b in bs if b.enabled})

    def lines(self):
        return [ln for ln in self.out.getvalue().splitlines() if fw.LINE.match(ln)]


def seed_put(mem, a, t):
    mem.u32(a, t[0])
    mem.u32(a + 4, t[1])


def put(path, lines):
    with open(path, "w") as f:
        f.write("# d2run\n" + "\n".join(lines) + "\n")


class TestReader(unittest.TestCase):
    def test_selftest(self):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = fw.selftest()
        finally:
            sys.stdout = old
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertGreaterEqual(buf.getvalue().count("PASS"), 10)

    def test_pilot_cli(self):
        with tempfile.TemporaryDirectory() as d:
            ok, bad = os.path.join(d, "ok.log"), os.path.join(d, "bad.log")
            lines = fw.synth(frames=250)
            put(ok, lines)
            cut = [ln for i, ln in enumerate(lines) if not (ln.startswith("FT1 ") and '"fr":1100' in ln)]
            put(bad, cut)
            r = lambda p: subprocess.run([sys.executable, "-I", os.path.join(HERE, "frame.py"), "window", "--pilot", p],
                                         capture_output=True, text=True)
            self.assertEqual(r(ok).returncode, 0, r(ok).stdout)
            self.assertIn("PILOT (a) whole: PASS  (b) unmoved: PASS", r(ok).stdout)
            self.assertEqual(r(bad).returncode, 1)
            self.assertIn("(a) whole: FAIL", r(bad).stdout)

    def test_report_numbers(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.log")
            put(p, fw.synth(frames=250))
            buf = io.StringIO()
            fw.run([p], out=buf)
            t = buf.getvalue()
            for key in ("lines_per_frame=", "estimate13_mid=15.9", "queue QE=", "chained_events=", "timers T20(",
                        "shared-seed pairs=", "draw-free runs", "HITS ", "DONE-WHEN"):
                self.assertIn(key, t)

    def test_chain_is_not_resynchronised(self):
        lines = fw.synth(frames=60)
        j = [i for i, ln in enumerate(lines) if ln.startswith("UE0 ")][5]
        o = json.loads(lines[j].split(" ", 1)[1])
        o["gs"] = fw.fmt(fw.step(fw.step(fw.sd(o["gs"]))))
        lines[j] = "UE0 " + json.dumps(o, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.log")
            put(p, lines)
            ws, _o = fw.parse_log(p)
            ch = fw.check_chain(ws[0])
            self.assertEqual([(m["tag"], m["rel"], m["k"]) for m in ch["mism"]][:1], [("UE0", "stepped", 2)])
            # the UE1 exit of the moved event is the real stream again: later entries still hand off, no cascade
            self.assertEqual(len(ch["mism"]), 1, ch["mism"])


class TestLogger(unittest.TestCase):
    def test_window_from_env_and_reader(self):
        rig = LoggerRig({"FRAME_WINDOWS": "now:5:town"})
        m, G = rig.mem, rig.GAME
        gs = (0x2A, 0x29A)
        unit_p, rec = 0x121000, 0x130000
        for f in range(1000, 1012):
            m.u32(G + 0xA8, f - 1)
            seed_put(m, G + 0xD0, gs)
            seed_put(m, unit_p + 0x20, (7, 8))
            m.u32(unit_p, 0)
            m.u32(unit_p + 0x0C, 100)
            m.put(0x0088CAD0, bytes([f % 9]))
            rig.hit(0x0052D870, ecx=G)
            m.u32(G + 0xA8, f)
            if f % 20 == 0:
                rig.hit(0x0052D920, edi=G)
            m.low[rec] = 11
            m.u32(rec + 4, f)
            m.u32(rec + 8, unit_p)
            m.u32(rec + 0x0C, 100)
            rig.hit(0x00540FC4, esi=rec)
            rig.hit(0x00540FC9)
            rig.hit(0x0052D974)
        out = rig.lines()
        tags = [ln.split(" ", 1)[0] for ln in out]
        self.assertEqual(tags[0], "RDY")
        self.assertEqual(tags.count("FT0"), 5)
        self.assertEqual(tags.count("FT1"), 5)
        self.assertEqual(tags.count("WIN"), 1)
        self.assertEqual(tags.count("WEND"), 1)
        self.assertEqual(tags.count("UE0"), 5)
        self.assertEqual(tags.count("UE1"), 5)
        self.assertEqual(tags.count("LOGERR"), 0, out)
        # opened at the first FT0, closed at the FT1 of the fifth frame, the breakpoints disabled again
        self.assertEqual(rig.enabled(), [0x0052D870, 0x0052D974])
        wend = json.loads([ln for ln in out if ln.startswith("WEND")][0].split(" ", 1)[1])
        self.assertEqual((wend["ok"], wend["frames"]), (1, 5))
        self.assertEqual(wend["hits"]["FT0"], 5)
        self.assertEqual(wend["hits"]["UE0"], 5)
        # the reader accepts what the logger wrote
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.log")
            put(p, out)
            ws, _o = fw.parse_log(p)
            self.assertEqual(len(ws), 1)
            self.assertEqual(fw.check_whole(ws[0]), [])
            self.assertEqual(fw.check_chain(ws[0])["mism"], [])
            ft0 = [o for _n, t, o in ws[0]["lines"] if t == "FT0"]
            self.assertEqual([o["fr"] for o in ft0], [1000, 1001, 1002, 1003, 1004])
            self.assertEqual(ft0[0]["pre"], 999)
            self.assertEqual(ft0[2]["hc"], 1002 % 9)

    def test_control_file_opens_at_next_ft0(self):
        with tempfile.TemporaryDirectory() as d:
            ctl = os.path.join(d, "c.ctl")
            open(ctl, "w").close()
            rig = LoggerRig({"FRAME_CTL": ctl})
            m, G = rig.mem, rig.GAME
            seed_put(m, G + 0xD0, (1, 2))

            def tick(f):
                m.u32(G + 0xA8, f - 1)
                rig.hit(0x0052D870, ecx=G)
                m.u32(G + 0xA8, f)
                rig.hit(0x0052D974)

            for f in range(10, 13):
                tick(f)
            self.assertEqual([ln.split(" ", 1)[0] for ln in rig.lines()], ["RDY"])
            with open(ctl, "a") as fh:
                fh.write("open 2 pack\n")
            for f in range(13, 17):
                tick(f)
            tags = [ln.split(" ", 1)[0] for ln in rig.lines()]
            self.assertEqual(tags, ["RDY", "WIN", "FT0", "FT1", "FT0", "FT1", "WEND"])
            # cover: a window of 4 around frame 20 starts at 18
            with open(ctl, "a") as fh:
                fh.write("open 4 town cover=20\n")
            for f in range(17, 30):
                tick(f)
            wins = [json.loads(ln.split(" ", 1)[1]) for ln in rig.lines() if ln.startswith("WIN ")]
            self.assertEqual([w["start"] for w in wins], [13, 18])

    def test_sv1_only_after_sv0(self):
        """Smoke session 1: the instruction after a skipped SaveGameClients call is reached with no entry; no SV1 then."""
        with tempfile.TemporaryDirectory() as d:
            ctl = os.path.join(d, "c.ctl")
            open(ctl, "w").close()
            rig = LoggerRig({"FRAME_CTL": ctl})
            m, G = rig.mem, rig.GAME
            seed_put(m, G + 0xD0, (1, 2))
            m.u32(G + 0xA8, 9)
            rig.hit(0x0052D870, ecx=G)
            with open(ctl, "a") as fh:
                fh.write("open 1 town\n")
            m.u32(G + 0xA8, 10)
            rig.hit(0x0052D974)
            m.u32(G + 0xA8, 10)
            rig.hit(0x0052D870, ecx=G)
            rig.hit(0x0052D4C2)
            self.assertNotIn("SV1", [ln.split(" ", 1)[0] for ln in rig.lines()])
            rig.hit(0x0052CA10)
            rig.hit(0x0052D4C2)
            rig.hit(0x0052D4C2)
            tags = [ln.split(" ", 1)[0] for ln in rig.lines()]
            self.assertEqual((tags.count("SV0"), tags.count("SV1")), (1, 1))

    def test_callback_path_ue1_pairs_once(self):
        """Smoke session (pack): the callback path jumps to the dispatch call's next instruction, so both UE1 sites
        fire for one event; the pair closes once and the outer open event stays open."""
        with tempfile.TemporaryDirectory() as d:
            ctl = os.path.join(d, "c.ctl")
            open(ctl, "w").close()
            rig = LoggerRig({"FRAME_CTL": ctl})
            m, G = rig.mem, rig.GAME
            seed_put(m, G + 0xD0, (1, 2))
            m.u32(G + 0xA8, 9)
            rig.hit(0x0052D870, ecx=G)
            with open(ctl, "a") as fh:
                fh.write("open 1 town\n")
            m.u32(G + 0xA8, 10)
            rig.hit(0x0052D974)
            m.u32(G + 0xA8, 10)
            rig.hit(0x0052D870, ecx=G)
            for rec, u, ident in ((0x1000, 0x2000, 5), (0x1100, 0x2100, 6)):
                m.put(rec, bytes(0x20))
                m.u32(rec + 8, u)
                m.u32(rec + 0x0C, ident)
                seed_put(m, u + 0x20, (7, 8))
            rig.hit(0x00540FB2, esi=0x1000)              # outer: a callback-path event
            rig.hit(0x00541016, esi=0x1100)              # inner event opened inside it
            rig.hit(0x00541018)                          # the inner callback returns, jumping to
            rig.hit(0x00541030)                          # the dispatch return: one return, no line
            rig.hit(0x00540FB4)
            rig.hit(0x00540FC9)
            tags = [ln.split(" ", 1)[0] for ln in rig.lines()]
            self.assertEqual((tags.count("UE0"), tags.count("UE1"), tags.count("LOGERR")), (2, 2, 0))
            ids = [json.loads(ln.split(" ", 1)[1])["id"] for ln in rig.lines() if ln.startswith("UE1 ")]
            self.assertEqual(ids, [6, 5])

    def test_no_writes_in_source(self):
        with open(LOGGER) as fh:
            src = fh.read()
        code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
        for pat in (r"write_memory", r"set var", r"\$[a-z]+\s*=[^=]", r"\bexecute\(", r"\.value\s*=", r"gdb\.parse_and_eval\([^)]*=[^=]"):
            self.assertIsNone(re.search(pat, code), pat)
        with open(os.path.join(HERE, "gdb", "frame.gdb")) as fh:
            gdbf = fh.read()
        self.assertNotRegex(gdbf, r"(?m)^\s*(set var|set \$|print .*=|call |poke)")
        # every breakpoint answers False: the game is never stopped by the logger
        self.assertIn("return False", src)

    def test_breakpoint_addresses_have_a_source(self):
        rig = LoggerRig()
        addrs = sorted(rig.gdb.registry)
        sym = set()
        for ln in open(os.path.join(ROOT, "re", "symbols.csv")):
            if ln.startswith("0x"):
                sym.add(int(ln.split(",", 1)[0], 16))
        text = ""
        for fn in os.listdir(os.path.join(ROOT, "docs", "findings", "frame")):
            text += open(os.path.join(ROOT, "docs", "findings", "frame", fn)).read()
        text = text.upper()
        derived = []
        lcg = {int(ln.split()[0], 16) for ln in open(os.path.join(HERE, "gdb", "lcg-sites.txt")) if ln.startswith("0x")}
        for a in addrs:
            if a in lcg:        # rev 2's XS sites: checked by TestXS against the binary
                continue
            if a in sym or ("0X%08X" % a) in text:
                continue
            derived.append(a)
        # the sites no symbol or finding names: returns of named functions, the instruction after a named call, and
        # the per-pass call sites inside the range frame/0001 § 3 gives (0x0052D8DF-0x0052D96C)
        expected = {0x0052D8E6, 0x0052D8F2, 0x0052D8F9, 0x0052D900, 0x0052D907,                       # pass calls
                    0x00540FB4, 0x00540FC9, 0x00541018, 0x00541030, 0x005410B4, 0x005410C9, 0x00541118, 0x00541130,
                    0x005411B4, 0x005411C4, 0x0054120B, 0x0054121B, 0x00541294, 0x005412A4, 0x005412EB, 0x005412FB,
                    0x00541374, 0x00541384, 0x005413CB, 0x005413DB,                                   # UE1
                    0x0054D785, 0x0054D81E, 0x0054D827, 0x0054D832,                                   # MSG1
                    0x0052D430, 0x0052D4C2, 0x00530446, 0x00543E87}                                   # SV1, TQ1
        self.assertLessEqual(set(derived), expected, ["%#x" % a for a in sorted(set(derived) - expected)])
        if os.path.exists(EXE):
            self.check_derived(derived)

    def check_derived(self, derived):
        """Each derived site is the instruction after a call (rel32 or `call eax`) or a ret, of the code the finding names."""
        def decode(a, b):
            out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=%#x" % a,
                                  "--stop-address=%#x" % b, EXE], capture_output=True, text=True).stdout
            return [m.group(2).strip() for m in re.finditer(r"^\s*([0-9a-f]+):\t(.*)$", out, re.M)]
        for a in derived:
            if a in (0x0054D785, 0x0054D81E, 0x0054D827, 0x0054D832):
                self.assertTrue(decode(a, a + 3)[0].startswith("ret"), hex(a))
                continue
            if a in (0x0052D8E6, 0x0052D8F2, 0x0052D8F9, 0x0052D900, 0x0052D907):    # a pass call: the site is the call
                self.assertTrue(decode(a, a + 1)[0].startswith("call"), hex(a))
                continue
            ok = False
            for n in (5, 2, 6):
                ins = decode(a - n, a)
                ok = ok or (len(ins) == 1 and ins[0].startswith("call"))
            self.assertTrue(ok, "%#x does not follow a call" % a)


class TestXS(unittest.TestCase):
    """Logger rev 2 (XS, KD, FRAME_HOOKS) under the fake gdb, and the static facts its fields rest on, against the binary."""

    SITES = [int(ln.split()[0], 16) for ln in open(os.path.join(HERE, "gdb", "lcg-sites.txt")) if ln.startswith("0x")]

    def window(self, env=None):
        rig = LoggerRig(dict({"FRAME_WINDOWS": "now:2:pack"}, **(env or {})))
        m, G = rig.mem, rig.GAME
        seed_put(m, G + 0xD0, (0x2A, 0x29A))
        m.u32(G + 0xA8, 999)
        rig.hit(0x0052D870, ecx=G)
        m.u32(G + 0xA8, 1000)
        return rig, m, G

    def close(self, rig, m, G):
        rig.hit(0x0052D974)
        m.u32(G + 0xA8, 1000)
        rig.hit(0x0052D870, ecx=G)
        m.u32(G + 0xA8, 1001)
        rig.hit(0x0052D974)

    def test_xs_fields(self):
        rig, m, G = self.window()
        self.assertEqual(len(self.SITES), 852)
        self.assertTrue(all(a in rig.gdb.registry for a in self.SITES))
        rig.hit(0x0046C257, eax=0x1234)                      # an inlined site: EAX
        rig.hit(0x004F2959, eax=1, esi=0x5678)                                         # ESI
        m.u32(0x150000, 0x9ABC)
        rig.hit(0x005F7C17, eax=1, esi=0x150000)                                       # [ESI]
        m.u32(0x1F0000 + 12, 0x00411111)
        rig.hit(0x0045C39F, eax=0x4242, esp=0x1F0000)                                  # RNG_Range: ra at esp+12
        m.u32(0x1F0000, 0x00422222)
        rig.hit(0x0045C372, eax=0x4343, esp=0x1F0000)                                  # RNG_Step: ra at esp
        xs = [json.loads(ln.split(" ", 1)[1]) for ln in rig.lines() if ln.startswith("XS ")]
        self.assertEqual([x["low"] for x in xs], [0x1234, 0x5678, 0x9ABC, 0x4242, 0x4343])
        self.assertEqual([x.get("ra") for x in xs], [None, None, None, 0x00411111, 0x00422222])
        self.assertTrue(all(x["fr"] == 1000 for x in xs))

    def test_other_thread_not_written(self):
        rig, m, G = self.window()
        rig.gdb.thread = 2
        rig.hit(0x0046C257, eax=7)
        rig.gdb.thread = 1
        rig.hit(0x0046C257, eax=8)
        self.assertEqual([json.loads(ln.split(" ", 1)[1])["low"] for ln in rig.lines() if ln.startswith("XS ")], [8])
        self.close(rig, m, G)
        wend = json.loads([ln for ln in rig.lines() if ln.startswith("WEND")][0].split(" ", 1)[1])
        self.assertEqual((wend["hits"]["XS"], wend["hits"]["XS_other"]), (2, 1))

    def test_kd_and_hooks(self):
        rig, m, G = self.window({"FRAME_HOOKS": "1"})
        mon, ev = 0x121000, 0x130000
        m.u32(mon, 1)
        m.u32(mon + 0x0C, 77)
        m.u32(ev + 4, mon)
        rig.hit(0x005A6830, edx=ev)
        kd = [json.loads(ln.split(" ", 1)[1]) for ln in rig.lines() if ln.startswith("KD ")]
        self.assertEqual((kd[0]["ty"], kd[0]["id"]), (1, 77))
        hooks = [int(ln.split()[0], 16) for ln in open(os.path.join(HERE, "gdb", "frame-hooks.txt")) if ln.startswith("0x")]
        self.assertEqual(len(hooks), 65)
        self.assertTrue(all(a in rig.gdb.registry for a in hooks))
        rig.hit(hooks[0])
        self.close(rig, m, G)
        wend = json.loads([ln for ln in rig.lines() if ln.startswith("WEND")][0].split(" ", 1)[1])
        self.assertEqual(wend["hk"]["%08X" % hooks[0]], {"none": 1})
        self.assertNotIn("HK", [ln.split(" ", 1)[0] for ln in rig.lines()])

    def test_no_hooks_without_env(self):
        rig, m, G = self.window()
        hooks = [int(ln.split()[0], 16) for ln in open(os.path.join(HERE, "gdb", "frame-hooks.txt")) if ln.startswith("0x")]
        own = {0x0052D870, 0x0052D974}
        self.assertFalse([a for a in hooks if a in rig.gdb.registry and a not in own and
                          any(b.name == "HK" for b in rig.gdb.registry[a] if hasattr(b, "name"))])

    def test_xs_disabled_outside_window(self):
        rig = LoggerRig({"FRAME_WINDOWS": "r100:2:pack"})
        self.assertFalse(any(a in rig.enabled() for a in self.SITES))

    @unittest.skipUnless(os.path.exists(EXE), "needs the pinned game.exe")
    def test_sites_against_the_binary(self):
        """852 sites, each `mov ecx|edx, 0x6ac690c5`; EAX is the multiplicand on every path at 850, and the two others are the
        two exceptions the logger reads from ESI and [ESI]; the six primitive sites' return-address offsets are 4 x the pushes."""
        out = subprocess.run(["objdump", "-d", "-M", "intel", EXE], capture_output=True, text=True).stdout
        dis, idx = [], {}
        for m in re.finditer(r"^\s+([0-9a-f]+):\t(?:[0-9a-f]{2} )+\s*\t?(.*)$", out, re.M):
            idx[int(m.group(1), 16)] = len(dis)
            dis.append((int(m.group(1), 16), m.group(2).strip()))
        self.assertEqual(len(self.SITES), len(set(self.SITES)))
        wr = re.compile(r"(mov|lea|xor|movzx|movsx|pop|add|sub|and|or|imul|not|neg|shl|shr|sar|inc|dec|adc|sbb|xchg|cwde)\s+(eax|ax|al|ah)\b")

        def walk(i, reg, seen):
            for _ in range(40):
                if i in seen:
                    return True
                seen.add(i)
                t = dis[i][1]
                if re.match(r"mul\s+" + reg + r"$", t):
                    return True
                if t.startswith(("call", "ret", "int", "cdq", "div", "idiv", "lodsd")) or wr.match(t):
                    return False
                m = re.match(r"(j\w+)\s+0x([0-9a-f]+)$", t)
                if m:
                    tgt = int(m.group(2), 16)
                    if tgt not in idx:
                        return False
                    if m.group(1) == "jmp":
                        i = idx[tgt]
                        continue
                    if not walk(idx[tgt], reg, seen):
                        return False
                elif t.startswith("j"):
                    return False
                i += 1
            return False
        ready, notready = [], []
        for a in self.SITES:
            m = re.match(r"mov\s+(ecx|edx),0x6ac690c5$", dis[idx[a]][1])
            self.assertIsNotNone(m, hex(a))
            (ready if walk(idx[a] + 1, m.group(1), set()) else notready).append(a)
        self.assertEqual((len(ready), sorted(notready)), (850, [0x004F2959, 0x005F7C17]))
        self.assertTrue(re.match(r"mov\s+eax,esi$", dis[idx[0x004F2959] + 1][1]))
        self.assertTrue(re.match(r"mov\s+eax,DWORD PTR \[esi\]$", dis[idx[0x005F7C17] + 2][1]))
        # the primitives: pushes between the function's start and the site (ebp frames push ebp first)
        starts = {0x0045C372: 0x0045C370, 0x0045C39F: 0x0045C390, 0x0045C3F9: 0x0045C3E0, 0x00472217: 0x00472210,
                  0x0047224A: 0x00472240, 0x004722A4: 0x00472280}
        src = open(LOGGER).read()
        prim = eval(re.search(r"PRIM_RA = (\{[^}]*\})", src).group(1))
        for site, start in starts.items():
            pushes = sum(1 for k in range(idx[start], idx[site]) if dis[k][1].startswith("push"))
            self.assertEqual(prim[site], 4 * pushes, hex(site))
        self.assertEqual(sorted(prim), sorted(starts))


class TestReader2(unittest.TestCase):
    def test_controls(self):
        import frame_xs
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = frame_xs.selftest2()
        finally:
            sys.stdout = old
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertEqual(buf.getvalue().count("PASS"), 13)

    def test_tables_are_sourced(self):
        for row in fw.TOUCH:
            self.assertIn(row["trigger"], ("kill", "defender", "owner"))
            self.assertTrue(row["at"] and row["fn"].startswith("fn:") and row["spec"])
        for loc, (fn, spec) in fw.PASSDRAW.items():
            self.assertTrue(fn.startswith("fn:") and spec, hex(loc))


class TestRunner(unittest.TestCase):
    def run_cli(self, *a):
        return subprocess.run([sys.executable, "-I", os.path.join(HERE, "frame_sessions.py")] + list(a), capture_output=True,
                              text=True, cwd=ROOT)

    def test_recipe_starts_in_act_one(self):
        """Smoke session 1: SpecNova's difficulty bytes 131 start the game in Act IV; the frame scenes start in Act I."""
        with open(os.path.join(ROOT, "tools", "d2s_recipes", "framenova.json")) as f:
            rec = json.load(f)
        self.assertEqual([d & 7 for d in rec["difficulty"]], [0, 0, 0])
        with open(os.path.join(ROOT, "tools", "frame_sessions.py")) as f:
            self.assertIn('p.add_argument("--recipe", default="framenova")', f.read())

    def test_monsters_near(self):
        import frame_sessions as fs
        with tempfile.TemporaryDirectory() as d:
            lg = os.path.join(d, "x.log")
            mon = {"x": 100, "y": 100, "m": [{"id": 1, "mode": 1, "x": 110, "y": 100, "hp": 5},
                                             {"id": 2, "mode": 1, "x": 200, "y": 100, "hp": 5},
                                             {"id": 3, "mode": 12, "x": 105, "y": 100, "hp": 5},
                                             {"id": 4, "mode": 1, "x": 101, "y": 100, "hp": None}]}
            with open(lg, "w") as f:
                f.write("PLR {}\nMON " + json.dumps(mon) + "\n")
            self.assertEqual(fs.monsters_near(lg, 22), 1)
            self.assertEqual(fs.monsters_near(os.path.join(d, "none.log"), 22), 0)

    def test_dry_plan_and_no_launch(self):
        for extra in (["--dry"], []):
            r = self.run_cli("run", "--slot", "2", "--tag", "t", "--saves", "/nonexistent", "--run", "x", *extra, "town", "pack", "maze")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("SCENE town", r.stdout)
            self.assertIn("SCENE pack", r.stdout)
            self.assertIn("SCENE maze", r.stdout)
            self.assertIn("not launching", r.stdout)
            self.assertIn("window town len=250", r.stdout)
            self.assertIn("cover=1500", r.stdout)
        r = self.run_cli("plan", "--long", "town")
        self.assertIn("cover=8192", r.stdout)

    def test_slot_zero_refused(self):
        r = self.run_cli("run", "--slot", "0", "--tag", "t", "--saves", "/x", "--run", "x", "--launch", "town")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("1 or 2", r.stderr + r.stdout)

    def test_gate(self):
        import frame_sessions as fs
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "g.log")
            put(p, fw.synth(frames=250))
            ok, text = fs.gate(p, "town")
            self.assertTrue(ok, text)
            # a window of a scene whose lines per frame pass three times its estimate stops the session
            lines = fw.synth(frames=250)
            extra = []
            for i in range(300):          # pad the first frame with 300 queue lines: far above 47.6 lines per frame
                extra.append('QE {"fr":1000,"kind":3,"asked":1005,"ut":1,"id":201,"ra":1,"n":0}')
            i0 = next(i for i, ln in enumerate(lines) if ln.startswith("FT0 "))
            heavy = lines[:i0 + 1] + extra * 50 + lines[i0 + 1:]
            q = os.path.join(d, "h.log")
            put(q, heavy)
            ok, text = fs.gate(q, "town")
            self.assertFalse(ok)
            self.assertIn("above 3 x", text)


class TestVolume(unittest.TestCase):
    def test_estimate13_unchanged(self):
        import frame_volume
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            frame_volume.cmd_estimate13()
        finally:
            sys.stdout = old
        t = buf.getvalue().splitlines()
        self.assertEqual(len(t), 1 + 9 + 3 + 1)
        self.assertIn("town (1 player, 8 NPCs) rate=mid", t[2])
        self.assertIn("lines=15.9", t[2])
        self.assertIn("stops=32.9", t[2])
        self.assertIn("EST13 p45 lines_per_frame=4.09", t[-1])


if __name__ == "__main__":
    unittest.main()
