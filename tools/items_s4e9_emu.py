#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S4e part 5e (`lane/n66z`): ItemAutoEquipSlot with skipReq 0, through ItemReqCheck to the
return, run on the pinned Game.exe under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuBoundary.java and compared with the model below; `static`, the objdump pins of the static (c)
remainders; `xref`, the full direct-call, writer and reader scans those remainders rest on. Parts 1 to 5d
(tools/stats_s4e_emu.py, items_s4e_emu.py to items_s4e8_emu.py, run/ to run8/) stay unchanged.

    python3 -I tools/items_s4e9_emu.py cases [--dir D] [--limit N]   write D/<family>.cases, .mem, .json
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/items_s4e9_emu.py check [--dir D]               compare, account every traced access, controls
    python3 -I tools/items_s4e9_emu.py static                        objdump pins
    python3 -I tools/items_s4e9_emu.py xref                          the scans of the static remainders
    python3 -I tools/items_s4e9_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66z/s4e/run9. Every draw comes from random.Random("n66z-s4e9-<family>").

Family (function, convention; boundaries; row):
  req    sub_0055D710_ItemAutoEquipSlot (ECX user, EDX item; &loc, skipReq 0): to the return, ItemReqCheck 0x0062EAF0
         emulated with its callees (ITEMS_GetRecord, StatListGetStat and UnitGetStat over declared stat lists, MulDiv
         with the CRT's 64-bit divide, the level requirement 0x0062B5B0 on its quality-default path,
         ITEMS_GetBaseType, ItemTypeClass, MonClassCheck), then the part 5d world (items_s4e8_emu.gen_auto's ItemTypes,
         bits, Items rows, the user, the body page and the worn items, drawn by that generator unchanged) to the
         location.                                                                               items/inventory 67

Controls: each a wrong reading; `sep` counts the cases a control's prediction differs from the model's, `passed` those
where the emulator still equals the control (must be 0 when sep > 0).
Stdlib only, plus objdump for `static` and `xref`.
"""
import argparse
import collections
import json
import os
import random
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_s1e as E  # noqa: E402
import sweep_s4b as S4  # noqa: E402
import items_s4e3_emu as P3  # noqa: E402
import items_s4e8_emu as P8  # noqa: E402
from use_emu import le32  # noqa: E402
from anim_s6f_emu import read_out  # noqa: E402
from combat_s5e_emu import muldiv  # noqa: E402

M32 = 0xFFFFFFFF
DEFDIR = os.path.join(ROOT, "workspace", "logs", "n66z", "s4e", "run9")
FAMILIES = ("req", "evt")
NCASES = {"req": 6000, "evt": 3000}
s32 = P8.s32

# ---------------------------------------------------------------------------------------------------------- req
F_AUTO, F_REQ = 0x0055D710, 0x0062EAF0
ISCT, NISC = 0x26000000, 360
ULIST, UARR = P8.USER + 0x800, P8.USER + 0x900          # the user's stat list (USER is zeroed 0x1000)
ILIST, IARR = P8.ITEM + 0x300, P8.ITEM + 0x380          # the item's (ITEM is zeroed 0x400)
REQ_ZERO = P8.AUTO_ZERO + [(ISCT, NISC * 0x144)]
CLS_OFF = 0x21                                           # ItemTypes class byte (ItemTypeClass 0x0062C0E7)


class Capture(P8.AW):
    """items_s4e8_emu.AW, kept so the generator's world is visible to this model."""
    last = None

    def __init__(self):
        super().__init__()
        Capture.last = self


def put_list(c, sl, arr, stats, special):
    ao, co = (0x48, 0x4C) if special else (0x24, 0x28)
    c.d32(sl + 0x10, 0x80000000 if special else 0)
    ks = sorted(stats)
    c.d32(sl + ao, arr)
    c.d16(sl + co, len(ks))
    for i, k in enumerate(ks):
        c.put(arr + 8 * i, le32(k) + le32(stats[k] & M32))


def getstat(lst, s, p=0):
    """UnitGetStat / StatListGetStat over a declared list ({key: value}); ISC rows are zero (no floor)."""
    if lst is None or s < 0 or s >= NISC:
        return 0
    return s32(lst.get((s << 16) | (p & 0xFFFF), 0))


def reqcheck(w, x, ctl=None, br=None):
    """ItemReqCheck 0x0062EAF0 (item, user, 0, 0, 0, 0) -> 0/1."""
    it = w.units[P8.ITEM]
    rec = w.recs[it["file"]]
    fl = it["flags"]
    ident = fl & 0x10
    strq, dexq = x["strq"], x["dexq"]
    pct = getstat(x["ilist"], 91)
    a = b = 0
    if pct and ctl != "nopct":
        a, b = muldiv(strq, pct, 100), muldiv(dexq, pct, 100)
    if fl & 0x400000 and ctl != "noeth":
        a, b = a - 10, b - 10
    us, ud, ul = (getstat(x["ulist"], k) for k in (0, 2, 12))
    okS = (us > 0 or ctl == "strpos") and us >= s32(strq + a)
    okD = (ud > 0 or ctl == "strpos") and ud >= s32(dexq + b)
    if ctl == "strdex":
        okS, okD = us >= s32(strq + b) and us > 0, ud >= s32(dexq + a) and ud > 0
    lv = x["lvq"]
    if ctl != "nobonus":
        lv += getstat(x["ilist"], 92)
    lv = lv if lv > 0 else 0
    okL = ul >= lv or ctl == "nolevel"
    if br is not None:
        br.update([("s" if okS else "S") + ("d" if okD else "D") + ("l" if okL else "L")])
    if not (okS and okD and okL and ident):
        return 0
    if w.base(P8.ITEM) == 18 and getstat(x["ilist"], 70) <= 0 and ctl != "no18":
        return 0
    t = w.base(P8.ITEM)
    cls = x["tcls"].get(t, 7) if 0 <= t < P8.NTY else 7
    cls = cls if cls < 7 else 7
    if cls == 7 or ctl == "anyclass":
        return 1
    u = w.units[P8.USER]
    if u["type"] == 1 and cls == 4 and ctl != "nomerc":
        m = u["cls"] if 0 <= s32(u["cls"]) < x["nmon"] else -1
        if ((m - 560) & M32) <= 1:
            return 1
    return int(u["type"] == 0 and cls == u["cls"])


def model_req(w, x, ctl=None, br=None):
    ok = reqcheck(w, x, ctl, br)
    if ctl == "noreq":
        ok = 1
    if not ok:
        return ["ret", 0, None]
    return P8.model_auto(w, {"skip": 1})


REQ_CTLS = ("noreq", "nopct", "noeth", "strpos", "strdex", "nobonus", "nolevel", "no18", "anyclass", "nomerc")


def near(r, need):
    return r.choices([need, need + r.randrange(1, 30), need - 1, 0, -r.randrange(1, 50), r.randrange(0, 300)],
                     [0.3, 0.3, 0.15, 0.04, 0.04, 0.17])[0]


def gen_req(r, i):
    """One case, drawn by rejection so that returns of 1 and requirement passes are not swamped (at most 60 draws)."""
    for _ in range(60):
        body, m, okreq = gen_req1(r, i)
        acc = 1.0 if m["want"][1] else (0.45 if okreq else 0.3)
        if r.random() < acc:
            break
    return body, m


def gen_req1(r, i):
    P8.AW = Capture
    try:
        line, _ = P8.gen_auto(r, i)
    finally:
        P8.AW = Capture.__mro__[1]
    w = Capture.last
    head = line.rsplit("\n", 1)[0].split("\n")
    pre = [ln for ln in head if not ln.startswith("d ")]
    dumps = [ln for ln in head if ln.startswith("d ")]
    c = P8.Case()
    it = w.units[P8.ITEM]
    rec_i = it["file"]
    # the item: quality on the level requirement's default path, ethereal or not, its Items row's requirements
    q = r.choice([0, 1, 2, 3, 3, 9, r.getrandbits(32) | 0x10])
    c.d32(P8.IDATA, q)
    if r.random() < 0.35:
        it["flags"] |= 0x400000
    if r.random() < 0.15:
        it["flags"] &= ~0x10
    c.d32(P8.IDATA + 0x18, it["flags"])
    strq = r.choice([0, 0, r.randrange(1, 200), r.randrange(1, 60), r.randrange(1, 60), 0xFFFF])
    dexq = r.choice([0, 0, r.randrange(1, 200), r.randrange(1, 60)])
    lvq = r.choice([0, 0, r.randrange(1, 99), 255])
    a = P8.RECS + rec_i * 0x1A8
    c.d16(a + 0x10A, strq)
    c.d16(a + 0x10C, dexq)
    c.d8(a + 0x13F, lvq)
    # the item's stat list: 91 (requirement percent), 92 (level requirement bonus), 70 (quantity), decoys
    ilist = None
    if r.random() < 0.15:                                   # the stack test's type 18
        w.recs[rec_i]["t"] = 18
        c.d16(a + 0x11E, 18)
    if r.random() < 0.7:
        ilist = {}
        if r.random() < 0.6:
            ilist[91 << 16] = r.choice([20, -20, 100, -100, r.randrange(-120, 200), 0x20000 + r.randrange(99)])
        if r.random() < 0.4:
            ilist[92 << 16] = r.choice([5, -5, r.randrange(-40, 40), -300])
        if r.random() < 0.5:
            ilist[70 << 16] = r.choice([0, 1, 20, -1])
        if w.recs[rec_i]["t"] == 18 and r.random() < 0.5:
            ilist.pop(70 << 16, None)
        for _ in range(r.randrange(3)):
            k = (r.choice([90, 93, 69, 71, 1]) << 16) | r.choice([0, 0, 1])
            ilist.setdefault(k, r.getrandbits(32))
        if r.random() < 0.15:
            ilist[(91 << 16) | 1] = 77                       # stat 91 at param 1: not read
        put_list(c, ILIST, IARR, ilist, r.random() < 0.8)
        c.d32(P8.ITEM + 0x5C, ILIST)
    # ItemTypes class bytes
    tcls = {}
    for t in range(P8.NTY):
        v = r.choice([7, 7, 7, 0, 1, 2, 3, 4, 4, 5, 6, 8, 255])
        tcls[t] = v
        if t == w.base(P8.ITEM) or r.random() < 0.3:
            v = tcls[t] = r.choices([7, w.units[P8.USER]["cls"] & 0xFF, 4, v], [0.45, 0.25, 0.15, 0.15])[0]
        c.d8(P8.TYPES + t * 0xE4 + CLS_OFF, v)
    # the user: class (monsters 560/561 favoured), stats 0, 2, 12 near the needs
    u = w.units[P8.USER]
    if u["type"] == 1 and r.random() < 0.6:
        u["cls"] = r.choice([560, 561, 559, 562, 4])
        c.d32(P8.USER + 4, u["cls"])
    nmon = r.choice([734, 734, 561, 0])
    c.d32(P8.DTBL + 0xA80, nmon)
    pctv = s32(ilist.get(91 << 16, 0)) if ilist else 0
    ul = {}
    if r.random() < 0.95:
        ul[0] = near(r, strq + (muldiv(strq, pctv, 100) if pctv else 0))
        ul[2 << 16] = near(r, dexq + (muldiv(dexq, pctv, 100) if pctv else 0))
        bon = s32(ilist.get(92 << 16, 0)) if ilist else 0
        ul[12 << 16] = near(r, max(lvq + bon, 0) if r.random() < 0.8 else lvq)
        if r.random() < 0.04:
            del ul[r.choice([0, 2 << 16, 12 << 16])]
        for _ in range(r.randrange(3)):
            ul.setdefault((r.choice([1, 3, 7, 11, 13]) << 16), r.getrandbits(32))
        put_list(c, ULIST, UARR, ul, r.random() < 0.8)
        c.d32(P8.USER + 0x5C, ULIST)
    x = dict(strq=strq, dexq=dexq, lvq=lvq, ilist=ilist, ulist=ul if ul else None, tcls=tcls, nmon=nmon)
    if not ul:
        x["ulist"] = None
    body = "\n".join(pre + c.lines + dumps)
    sk = 0
    call = "call %08x %08x %08x %08x %08x" % (F_AUTO, P8.USER, P8.ITEM, P8.LOC, sk)
    br = collections.Counter()
    want = model_req(w, x, None, br)
    ctl = {k: model_req(w, x, k) for k in REQ_CTLS}
    bl = list(br)
    bl.append("q%d" % q if q < 16 else "qbig")
    if it["flags"] & 0x400000:
        bl.append("eth")
    bl.append("ret%d" % want[1])
    m = dict(want=want, ctl=ctl, br=bl)
    return body + "\n" + call, m, reqcheck(w, x)


# ---------------------------------------------------------------------------------------------------------- evt
F_FIND, F_REM, F_ADDEV, F_EVADD, F_ALLOC, F_FREE = 0x005C0BE0, 0x005C0B50, 0x0056E740, 0x005C0AD0, 0x0040B430, 0x0040B480
GAME, EUNIT, NODES = 0x27000000, 0x27010000, 0x27020000
EPOOL = 0x7E570000
EVT_ZERO = [(GAME, 0x100), (EUNIT, 0x100), (NODES, 0x40 * 8)]
EVT_TAB = 0x007325B0


def evt_tab():
    return S4.dwords(EVT_TAB, 50)


def model_evt(x, ctl=None):
    """x: kind (find, rem, add), unit (0 or EUNIT), nodes [dict(w2, k, s, c)] in list order, args."""
    ns, a = x["nodes"], x["args"]
    if x["kind"] == "find":
        if not x["unit"]:
            return ["ret", 0, None]
        hit = [i for i, n in enumerate(ns) if n["k"] == a[0] and n["s"] == a[1] and (n["c"] == a[2] or ctl == "noc")]
        if ctl == "last" and hit:
            return ["ret", NODES + 0x40 * hit[-1], None]
        return ["ret", NODES + 0x40 * hit[0] if hit else 0, None]
    if x["kind"] == "rem":
        marks = {}
        if not x["unit"]:
            return ["ret", None, marks]
        for i, n in enumerate(ns):
            if n["k"] == a[0] and (n["s"] == a[1] or ctl == "nostat"):
                if n["w2"] & 1 and ctl != "nomark":
                    if not n["w2"] & 2:                     # a mark that changes the word
                        marks[i] = (n["w2"] | 2) & 0xFFFF
                    continue
                prev = NODES + 0x40 * (i - 1) if i else None
                nxt = NODES + 0x40 * (i + 1) if i + 1 < len(ns) else 0
                return ["obs", F_FREE, NODES + 0x40 * i, prev, nxt, marks]
        return ["ret", None, marks]
    f = a[3] & M32
    fn = evt_tab()[f] if f <= 0x31 and ctl != "nobound" else (evt_tab()[f] if f < 50 else 0)
    if ctl == "nobound" and f > 0x31:
        fn = 1
    if not fn:
        return ["ret", 0, None]
    if not x["unit"]:
        return ["ret", 0, None]
    return ["obs", F_ALLOC, fn]


EVT_CTLS = {"find": ("noc", "last"), "rem": ("nostat", "nomark"), "add": ("nobound",)}


def gen_evt(r, i):
    c = P8.Case()
    kind = r.choice(["find", "find", "rem", "rem", "add"])
    unit = EUNIT if r.random() < 0.95 else 0
    n = r.choice([0, 1, 2, 3, 4, 6, 8])
    stat = r.randrange(0, 360)
    ns = []
    for k in range(n):
        nd = dict(w2=r.choice([0, 0, 1, 3, 2, r.getrandbits(16)]), k=r.choice([2, 2, 2, 1, 3]),
                  s=r.choice([stat, stat, stat + 1, r.randrange(360)]), c=r.choice([stat, stat, r.randrange(360)]))
        ns.append(nd)
        a = NODES + 0x40 * k
        c.put(a, bytes(r.getrandbits(8) for _ in range(0x20)))
        c.d16(a + 2, nd["w2"])
        c.d32(a + 4, nd["k"])
        c.d32(a + 8, nd["s"])
        c.d32(a + 0xC, nd["c"])
        c.d32(a + 0x18, NODES + 0x40 * (k - 1) if k else 0)
        c.d32(a + 0x1C, NODES + 0x40 * (k + 1) if k + 1 < n else 0)
    c.d32(EUNIT + 0x90, NODES if n else 0)
    c.d32(GAME + 0x1C, EPOOL)
    for k in range(n):
        c.dump(NODES + 0x40 * k, 0x20)
    c.dump(EUNIT + 0x90, 4)
    if kind == "find":
        args = [r.choice([2, 2, 1]), r.choice([stat, stat + 1]), r.choice([stat, stat, r.randrange(360)])]
        line = c.call(F_FIND, GAME, unit, *args)
    elif kind == "rem":
        args = [r.choice([2, 2, 2, 3]), r.choice([stat, stat, stat + 1])]
        line = c.call(F_REM, GAME, unit, *args)
    else:
        f = r.choice([r.randrange(0, 50), r.randrange(1, 32), r.randrange(32, 50), 0, 0x80000001])
        args = [r.randrange(1, 300), stat, 0, f, 2, stat]
        line = c.call(F_ADDEV, GAME, unit, *args)
    x = dict(kind=kind, unit=unit, nodes=ns, args=args)
    want = model_evt(x)
    ctl = {k: model_evt(x, k) for k in EVT_CTLS[kind]}
    br = [kind, kind + ("_obs" if want[0] == "obs" else "_ret")]
    if not unit:
        br.append(kind + "_nounit")
    if kind == "find" and unit:
        br.append("find_hit" if want[1] else "find_miss")
    if kind == "rem" and want[-1]:
        br.append("rem_marked")
    if kind == "add" and unit:
        f = args[3] & M32
        br.append("add_outside" if f > 0x31 else ("add_nullfn" if not evt_tab()[f] else "add_fn"))
    return line, dict(want=want, ctl=ctl, br=br, x=x)


def judge_evt(c, want, x):
    if "stop" in c:
        return False, ["stop", c.get("stop")]
    dm = dict(c["dumps"])
    if want[0] == "ret" and x["kind"] != "rem":
        return ("obs" not in c and c.get("eax") == want[1]), ["ret", c.get("eax"), c.get("obs")]
    if want[0] == "obs" and x["kind"] == "add":
        ok = "obs" in c and c["obs"] == F_ALLOC and c["regs"].get("edx") == 0x20 and c["regs"].get("ecx") == EPOOL
        ok = ok and c["args"][1:4] == (0x006E2FFC, 0x57, 0)
        return ok, ["obs", c.get("obs"), c.get("regs")]
    marks = want[-1]
    for i, nd in enumerate(x["nodes"]):
        w2 = struct.unpack("<H", dm[NODES + 0x40 * i][2:4])[0]
        if w2 != (marks.get(int(i), marks.get(str(i), nd["w2"])) if marks else nd["w2"]):
            return False, ["mark", i, w2]
    if want[0] == "ret":
        return "obs" not in c and "eax" in c, ["ret"]
    node, prev, nxt = want[2], want[3], want[4]
    if "obs" not in c or c["obs"] != F_FREE or c["regs"].get("edx") != node or c["regs"].get("ecx") != EPOOL:
        return False, ["obs", c.get("obs"), c.get("regs")]
    if c["args"][1:4] != (0x006E2FFC, 0x95, 0):
        return False, ["args", c["args"][1:4]]
    head = struct.unpack("<I", dm[EUNIT + 0x90])[0]
    if prev is None:
        if head != nxt:
            return False, ["head", head]
    else:
        if struct.unpack("<I", dm[prev][0x1C:0x20])[0] != nxt:
            return False, ["prevnext"]
    if nxt and struct.unpack("<I", dm[nxt][0x18:0x1C])[0] != (prev or 0):
        return False, ["nextprev"]
    return True, ["obs"]


# ---------------------------------------------------------------------------------------------------------- cases
GEN = {"req": gen_req, "evt": gen_evt}


def mem_spec(fam):
    if fam == "evt":
        out = ["# plan 0066 S4e part 5e (evt): a game, a unit and its event nodes, zero-filled"]
        for lo, n in EVT_ZERO:
            out.append("bytes %08x %s" % (lo, "00" * n))
        out += ["guard %08x" % g for g in (0x00408A60, 0x00681E09, 0x0040B4B0)]
        out += ["observe %08x" % a for a in (F_ALLOC, F_FREE, P8.F_FATAL)]
        return out
    out = ["# plan 0066 S4e part 5e (req): the part 5d auto world plus ItemStatCost rows, zero-filled before every case"]
    for lo, n in REQ_ZERO:
        out.append("bytes %08x %s" % (lo, "00" * n))
    out += ["dword 00744304 %08x" % P8.DTBL, "dword %08x %08x" % (P8.DTBL + 0xBF8, P8.TYPES),
            "dword %08x %08x" % (P8.DTBL + 0xBFC, P8.NTY), "dword %08x %08x" % (P8.DTBL + 0xC00, P8.BSTRIDE),
            "dword %08x %08x" % (P8.DTBL + 0xC04, P8.BITS), "dword %08x %08x" % (P8.DTBL + 0xBCC, ISCT),
            "dword %08x %08x" % (P8.DTBL + 0xBD4, NISC),
            "dword 0096ca58 %08x" % P8.NREC, "dword 0096ca5c %08x" % P8.RECS]
    out += ["guard %08x" % g for g in P8.GUARDS_ALL]
    out += ["observe %08x" % P8.F_FATAL]
    return out


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        r = random.Random("n66z-s4e9-%s" % fam)
        cases, meta = [], []
        for i in range(limit or NCASES[fam]):
            line, m = GEN[fam](r, i)
            cases.append(line)
            meta.append(m)
        E.write_family(d, fam, cases, mem_spec(fam), {"cases": meta})
        print("%s: %d cases" % (fam, len(meta)))


# ---------------------------------------------------------------------------------------------------------- check
def form(x):
    return json.dumps(x, sort_keys=True)


def declared():
    return list(P8.RS) + [(EVT_TAB, EVT_TAB + 4 * 50, "r", "g_StatEventFuncs 0x007325B0 (.data, no writer: xref.txt)")]


class Report(E.Report):
    def line(self):
        keys = ["cases", "match", "bad", "neg", "traced", "undeclared", "stopped"]
        rest = sorted(k for k in self.c if k not in keys)
        return "S4E9 %s " % self.fam + " ".join("%s=%d" % (k, self.c[k]) for k in keys + rest)


def cmd_check(d, fams=FAMILIES):
    rc = 0
    for fam in fams:
        p = os.path.join(d, fam + ".out")
        if not os.path.exists(p):
            print("S4E9 %s: no output" % fam)
            rc = 1
            continue
        calls, reads, writes = read_out(p)
        meta = json.load(open(os.path.join(d, fam + ".json")))["cases"]
        rep = Report(fam)
        sep, passed, outs = collections.Counter(), collections.Counter(), collections.Counter()
        if len(calls) != len(meta):
            rep.bad("%d calls for %d cases" % (len(calls), len(meta)))
        for c, a in zip(calls, meta):
            rep.c["cases"] += 1
            if "stop" in c:
                rep.c["stopped"] += 1
                rep.bad("case %d stopped at %08X: %s" % (c["n"], c["stop"], c.get("msg")))
                continue
            if fam == "req" and "obs" in c:
                rep.bad("case %d observed %s" % (c["n"], c["obs"]))
                continue
            jf = (lambda cc, w: judge_evt(cc, w, a["x"])) if fam == "evt" else (lambda cc, w: P8.judge("auto", cc, w))
            ok, got = jf(c, a["want"])
            rep.c["match"] += ok
            if not ok:
                rep.bad("case %d: got %s want %s" % (c["n"], got, a["want"]))
                continue
            rep.branches.update(a["br"])
            outs[form(a["want"][:3] if fam == "req" else [a["x"]["kind"], a["want"][0]])] += 1
            for k, v in a["ctl"].items():
                if form(v) != form(a["want"]):
                    sep[k] += 1
                    passed[k] += jf(c, v)[0]
        E.account(rep, reads, writes, declared())
        for k in sorted(outs):
            rep.notes.append("  outcome %s: %d" % (k, outs[k]))
        for k in sorted(set(k for a in meta for k in a["ctl"])):
            rep.notes.append("  control %s: sep=%d passed=%d" % (k, sep[k], passed[k]))
            if passed[k] or not sep[k]:
                rep.bad("control %s sep=%d passed=%d" % (k, sep[k], passed[k]))
        rc |= E.finish(rep, sum(sep.values()))
    return rc


# ---------------------------------------------------------------------------------------------------------- static
PINS = [  # ItemReqCheck: the requirement adds, the positive tests, the level, the identified flag, the class
    (0x0062EB63, "movzx", "edi,WORD PTR [eax+0x10a]"), (0x0062EB6A, "movzx", "eax,WORD PTR [eax+0x10c]"),
    (0x0062EB72, "push", "0x5b"), (0x0062EB8C, "call", "0x483360"), (0x0062EBB4, "and", "eax,0x400000"),
    (0x0062EBBB, "sub", "ebx,0xa"), (0x0062EBD5, "jg", "0x62ebdc"), (0x0062EBDE, "cmp", "esi,edi"),
    (0x0062EC23, "push", "0x2"), (0x0062EC83, "call", "0x62b5b0"), (0x0062EC91, "push", "0xc"),
    (0x0062EB57, "and", "ecx,0x10"), (0x0062ECE1, "cmp", "eax,0x12"), (0x0062ECE8, "push", "0x46"),
    (0x0062ECF5, "call", "0x62c0b0"), (0x0062ECFC, "cmp", "edi,0x7"), (0x0062ED19, "add", "eax,0xfffffdd0"),
    (0x0062ED26, "cmp", "edi,DWORD PTR [ebx+0x4]"), (0x0062C0E7, "mov", "al,BYTE PTR [eax+0x21]"),
    (0x0062B8D0, "movzx", "eax,BYTE PTR [eax+0x13f]"), (0x0062BA24, "push", "0x5c"), (0x0062BA32, "setle", "al"),
    # ItemAutoEquipSlot's skipReq-0 path: the same four tests after the call
    (0x0055D79C, "call", "0x62eaf0"), (0x0055D7A3, "je", "0x55d788"), (0x0055D7A6, "call", "0x62fdf0"),
    (0x0055D7B9, "push", "0x10"), (0x0055D7C6, "call", "0x62a4e0"), (0x0055D7D5, "cmp", "eax,0x26"),
    # the event list: find, remove, add (aggregate 23)
    (0x005C0BED, "mov", "eax,DWORD PTR [edx+0x90]"), (0x005C0C02, "cmp", "DWORD PTR [eax+0x4],edx"),
    (0x005C0C0A, "cmp", "DWORD PTR [eax+0x8],edi"), (0x005C0C0F, "cmp", "DWORD PTR [eax+0xc],esi"),
    (0x005C0B86, "test", "al,0x1"), (0x005C0B8A, "or", "eax,0x2"), (0x005C0BA2, "mov", "DWORD PTR [eax+0x90],ecx"),
    (0x005C0BBA, "push", "0x95"), (0x005C0BC4, "call", "0x40b480"), (0x0056E746, "cmp", "eax,0x31"),
    (0x0056E74B, "mov", "eax,DWORD PTR [eax*4+0x7325b0]"), (0x005C0AED, "mov", "edx,0x20"),
    (0x005C0AF2, "call", "0x40b430"), (0x005C0B0D, "mov", "BYTE PTR [eax],cl"), (0x005C0B12, "mov", "DWORD PTR [eax+0xc],edx"),
    (0x005C0B2D, "mov", "DWORD PTR [eax+0x4],edx"), (0x005C0B30, "mov", "DWORD PTR [eax+0x8],ecx"),
    (0x0055B872, "push", "edi"), (0x0055B878, "push", "0x2"), (0x0055B8C0, "push", "0x2"), (0x0055B8C2, "call", "0x5c0b50"),
]
PINS_STATIC = [
    ("states 14: the four elemental appliers' lists (STATLIST_Alloc, the state, the remove callback, the link)", [
        (0x0057ACE7, "push", "0x2"), (0x0057ACEA, "call", "0x6251f0"), (0x0057AD14, "push", "0x2"),
        (0x0057AD17, "call", "0x6252d0"), (0x0057AD1C, "push", "0x56e900"), (0x0057AD27, "push", "0x1"),
        (0x0057AD2B, "call", "0x626e10"),
        (0x0057AE67, "push", "0x2"), (0x0057AE6A, "call", "0x6251f0"), (0x0057AE94, "push", "0x73"),
        (0x0057AE97, "call", "0x6252d0"), (0x0057AE9C, "push", "0x56e900"), (0x0057AEA7, "push", "0x1"),
        (0x0057AEAB, "call", "0x626e10"),
        (0x0057B069, "push", "0x2"), (0x0057B06C, "call", "0x6251f0"), (0x0057B084, "push", "0xb"),
        (0x0057B087, "call", "0x6252d0"), (0x0057B08C, "push", "0x57ad80"), (0x0057B097, "push", "0x1"),
        (0x0057B09B, "call", "0x626e10"),
        (0x0057B35D, "push", "0x2"), (0x0057B360, "call", "0x6251f0"), (0x0057B367, "push", "0x1"),
        (0x0057B36A, "call", "0x6252d0"), (0x0057B36F, "push", "0x57b170"), (0x0057B37A, "push", "0x1"),
        (0x0057B37E, "call", "0x626e10"),
        (0x0057ACD5, "mov", "eax,0x6"), (0x0057ACD2, "or", "ecx,0xffffffff"), (0x0057ACDC, "mov", "ecx,DWORD PTR [eax+0xc]"),
        (0x0057ACDF, "mov", "eax,DWORD PTR [eax]"), (0x0057AE55, "mov", "eax,0x6"), (0x0057B057, "mov", "eax,0x6"),
        (0x0057B34B, "mov", "eax,0x6")]),
]


def pins_check(pins, tag):
    ok = 0
    for va, mn, sub in pins:
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % va,
                              "--stop-address=0x%x" % (va + 16), S4.EXE], capture_output=True, text=True).stdout
        line = [ln for ln in out.splitlines() if ln.strip().startswith("%x:" % va)]
        txt = line[0].split(":", 1)[1].strip() if line else ""
        good = bool(line) and txt.startswith(mn) and sub in txt
        ok += good
        print("  %s 0x%08X %s" % ("ok " if good else "BAD", va, txt))
    print("S4E9 static %s pins=%d ok=%d" % (tag, len(pins), ok))
    return ok == len(pins)


def cmd_static():
    good = pins_check(PINS, "families")
    for row, pins in PINS_STATIC:
        print("row %s" % row)
        good &= pins_check(pins, row)
    return 0 if good else 1


APPLIERS = [(0x0057AC50, 0x0057AD80, "COMBAT_ApplyPoison"), (0x0057ADD0, 0x0057AF30, "COMBAT_ApplyBurn"),
            (0x0057AF80, 0x0057B170, "COMBAT_ApplyCold"), (0x0057B230, 0x0057B420, "COMBAT_ApplyFreeze")]


def cmd_xref():
    """aggregate 23: every reference to g_StatEventFuncs (a writer would void the image read) and the callers of the
    event list's find, remove and add; states 14: every direct call of STATLIST_Alloc, StatListSetState,
    STATLIST_SetRemoveCallback and the link 0x00626E10 inside each elemental applier's body."""
    data = open(S4.EXE, "rb").read()
    pat = struct.pack("<I", EVT_TAB)
    refs = []
    k = data.find(pat)
    while k >= 0:
        refs.append(k)
        k = data.find(pat, k + 1)
    print("  g_StatEventFuncs 0x%08X: %d raw dword references" % (EVT_TAB, len(refs)))
    for off in refs:
        va = None
        for sva, vsz, raw, rsz, _nm, _ in S4.image()[2]:
            if raw <= off < raw + rsz:
                va = S4.image()[1] + sva + off - raw if sva < 0x400000 else sva + off - raw
        lo = (va or 0) - 8
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % lo,
                              "--stop-address=0x%x" % (lo + 16), S4.EXE], capture_output=True, text=True).stdout
        ins = [ln.strip().replace("\t", " ") for ln in out.splitlines() if ":\t" in ln and "7325b0" in ln]
        print("    at file 0x%X (va 0x%08X): %s" % (off, va or 0, ins[0] if ins else "(not an instruction operand)"))
    for t, nm in ((F_FIND, "event find 0x005C0BE0"), (F_REM, "event remove 0x005C0B50"), (F_ADDEV, "AddStatEvent"),
                  (F_EVADD, "event add 0x005C0AD0")):
        cs = S4.raw_callers(t)
        print("  %s: %d rel32 callers, %d abs32: %s" % (nm, len(cs), len(S4.raw_abs(t)), " ".join("0x%08X" % v for v in cs)))
    tot = 0
    for lo, hi, nm in APPLIERS:
        for t, tn in ((0x006251F0, "STATLIST_Alloc"), (0x006252D0, "StatListSetState"),
                      (0x00625CE0, "STATLIST_SetRemoveCallback"), (0x00626E10, "the link 0x00626E10")):
            cs = [v for v in S4.raw_callers(t) if lo <= v < hi]
            tot += len(cs)
            print("  %s 0x%08X..0x%08X: %s %d: %s" % (nm, lo, hi, tn, len(cs), " ".join("0x%08X" % v for v in cs)))
    print("S4E9 xref table_refs=%d applier_calls=%d" % (len(refs), tot))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["cases", "check", "static", "xref", "manifest"])
    ap.add_argument("--dir", default=DEFDIR)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--fam", action="append")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir, a.limit)
        return 0
    if a.cmd == "check":
        return cmd_check(a.dir, tuple(a.fam) if a.fam else FAMILIES)
    if a.cmd == "static":
        return cmd_static()
    if a.cmd == "xref":
        return cmd_xref()
    return P3.cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
