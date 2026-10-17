#!/usr/bin/env python3
"""Plan 0038 batch S2c: the second sources and log re-checks for items/affixes, cube, properties, quality,
quest-drops, sockets-runewords, uniques-sets and vendors (static; no game, no slot).

    python3 -I tools/sweep_s2c.py logs [--write FILE]   the run logs, sha256 checked against their run manifests
    python3 -I tools/sweep_s2c.py <check> [-v]          one check
    python3 -I tools/sweep_s2c.py all                    every check

Checks (each prints `S2C <check> key=value ...` lines and a few detail lines; exit 1 when an observation contradicts a
claim the batch raises, i.e. a `bad=` count above 0; a claim with no stock case shows as a zero count):

  static    the pinned Game.exe read by a second tool next to Ghidra: GNU objdump (`objdump -d -M intel`, a linear
            sweep that knows nothing of Ghidra's analysis), the raw byte scan of tools/xrefscan.py, and a small
            evaluator (`emu`) that runs a compare-and-jump-table dispatch for one register value through the objdump
            instructions (cmp, sub, add, lea, movzx from a byte table, jmp through a dword table, push, mov, call).
            Sub-checks: dispatch (NPC_MenuAction's trade and gamble class lists, the store-record and list-builder
            switches, the cube's PlayerOp switch), callers (VENDOR_BuildStock, NPCSTORE_Reset, ITEMS_SetSockets,
            QUESTS_GetSeed, ITEMRATIO_Select with its pushed version argument, g_CubeAllRows), store (the 64 x 0x44
            records and the 43-entry slot table), cow (the cow portal's pushed level and object class), rngwalk (the
            RNG sites under the cow portal's spot search and portal object, and under sub_005761C0_ItemRepairAll),
            copy (sub_0055A2A0_ItemCopy's serialiser calls), readers (the socket readers' UNIT_SetMode(child, 4) and
            option pushes), match (RUNEWORD_Match's memory operands), setstate (every QUESTRECORD_SetState and
            ClearState call with its pushed word and bit), questinit (the record word each quest init function
            stores at Quest+0xE0 against g_QuestDescs), qgraph (the call graph under the Diablo, a5q4 and a5q5 quest
            callbacks), inline (the multiply-shift divisions next to the quest-seed LCG steps), imbue (the quest
            tests of the imbue service), anya (the three Anya reward arrays).
  tables    full-table checks of the stock .bin/.txt (rule 2): CubeMain counts, op 28, input cells, the crafted
            candidate survey, the random-of-type survey, Runes layout and cells, gem groups, ItemTypes StorePage,
            MonStats TCQuestId, ItemRatio versions.
  cube      tools/cube.py's model run per transmute over the run:2026-10-15-cube logs, with scans: the creation
            records, the forced picks against their level windows, the output placement (new: the inventory spot
            search of tools/player.py, run:2026-10-16-player, on the 3 x 4 cube grid), the quality-0 creation rolls,
            the ethereal and socket skip bits, exc inputs, the op 28 rows, the cow portal's game-seed steps.
  sockets   run:2026-10-15-sockets: reader inserts (child mode, parent flags), packet inserts (parent flags), the
            runes and gems inserted, the Spirit match, the SetSockets calls of the props, cube and quest logs.
  vendors   run:2026-10-15-vendors: the stock and gamble creations (quality, identified flag, passes), the store
            records per class, the buildTick order.
  quests    run:2026-10-16-quest-drops (and its owner-played addendum): GetState against the logged words, the bit
            writes of the Mephisto and orifice sessions, the scripted creations, the imbue and socket services.
  props     the stock drop logs: the creation-record skip and forced bits at the ethereal and socket rolls.

Stdlib only, plus the objdump binary. Read-only (logs --write writes the manifest file it is given). The batch record
is the "Plan 0038 batch S2c" section of docs/findings/items/0002, 0004, 0005, 0006, 0007, 0008, 0009 and 0010.
"""
import argparse
import collections
import contextlib
import io
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_s4b as S4  # noqa: E402  (objdump walker, image access, raw callers)

ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "workspace", "logs")
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
LNG = os.path.join(ROOT, "workspace", "merged", "data", "local", "lng", "eng")
SCRATCH = os.path.join(ROOT, "workspace", "scratch-s2c")
SYMBOLS = os.path.join(ROOT, "re", "symbols.csv")

RUNS = [  # (run id, list file, manifest)
    ("run:2026-10-15-cube", "cube-run.lst", "cube-run-manifest.txt"),
    ("run:2026-10-15-sockets", "sockets-run.lst", "sockets-run-manifest.txt"),
    ("run:2026-10-15-vendors", "vendors-run.lst", "vendors-run-manifest.txt"),
    ("run:2026-10-16-quest-drops", "quests-run.lst", "quests-run-manifest.txt"),
    ("run:2026-10-16-quest-drops (owner-played addendum)", "quests-owner-run.lst", "quests-owner-manifest.txt"),
]
VERBOSE = False


# ------------------------------------------------------------------------------------------------------------ report
class Report(S4.Report):
    def done(self):
        print("S2C %s %s" % (self.name, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
        for s in self.notes:
            print("  " + s)
        return 1 if self.c["bad"] else 0


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def run_logs(check=True):
    """{run: [path]} from the run lists, each file's sha256 checked against its run manifest."""
    out = collections.OrderedDict()
    for run, lst, man in RUNS:
        want = {}
        for ln in open(os.path.join(LOGS, man)):
            if ln.strip():
                h, name = ln.split()
                want[os.path.basename(name)] = h
        paths = []
        for ln in open(os.path.join(LOGS, lst)):
            if not ln.strip():
                continue
            p = os.path.join(LOGS, os.path.basename(ln.strip()))
            if check and sha256(p) != want.get(os.path.basename(p)):
                raise SystemExit("%s: sha256 differs from %s" % (p, man))
            paths.append(p)
        out[run] = paths
    return out


def cmd_logs(ns):
    sets = run_logs()
    lines = []
    for run, paths in sets.items():
        print("S2C logs %s files=%d" % (run, len(paths)))
        lines += ["%s  %s" % (sha256(p), os.path.relpath(p, ROOT)) for p in paths]
    print("S2C logs total=%d (sha256 checked against the run manifests)" % sum(len(v) for v in sets.values()))
    if ns.write:
        with open(ns.write, "w") as f:
            f.write("\n".join(lines) + "\n")
        print("manifest written: %s (sha256 %s)" % (ns.write, sha256(ns.write)))
    return 0


def events(path, tags=None):
    """(tag, dict) per JSON log line, in order."""
    with open(path, errors="replace") as f:
        for line in f:
            tag, _, rest = line.rstrip("\n").partition(" ")
            if not rest.startswith("{") or (tags and tag not in tags):
                continue
            try:
                yield tag, json.loads(rest)
            except ValueError:
                continue


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a, **k)
    return rc, buf.getvalue()


# --------------------------------------------------------------------------------------------------- symbols, image
_SYM = None


def symbols():
    global _SYM
    if _SYM is None:
        _SYM = {}
        for ln in open(SYMBOLS):
            f = ln.split(",")
            if len(f) > 2 and f[0].startswith("0x") and f[1] == "func":
                _SYM[int(f[0], 16)] = f[2]
    return _SYM


def name(va):
    return symbols().get(va, "0x%08X" % va)


def containing(va):
    """The nearest symbol-file function at or below va (a label for reports; the walks below do not rely on it)."""
    best = None
    for a in symbols():
        if a <= va and (best is None or a > best):
            best = a
    return best


def ins_at(va):
    return S4.asm().at(va)


def window(lo, hi):
    """[(va, mnemonic, operands)] decoded from lo to hi (re-decoded from lo so the start is an instruction)."""
    txt = S4.objdump(lo, hi)
    out = sorted(S4.parse_listing(txt).items())
    return [(va, mn, ops) for va, (mn, ops) in out]


def pushes_before(site, back=0x40):
    """The push operands before a call site, nearest last (decoded from the window before it)."""
    w = [x for x in window(site - back, site + 5) if x[0] < site]
    return [ops for va, mn, ops in w if mn == "push"]


def imm(ops):
    m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
    return int(m.group(1), 16) if m else None


def u8_at(va):
    data, _, _ = S4.image()
    return data[S4.va_off(va)]


# ----------------------------------------------------------------------------------------------- the dispatch evaluator
REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi")
M32 = 0xFFFFFFFF


def s32v(x):
    x &= M32
    return x - (1 << 32) if x & 0x80000000 else x


class EmuError(Exception):
    pass


# Flag-setting instructions emu does not model: they clear its flags (the S2c review's follow-up; a non-self xor too).
FLAG_CLOBBER = {"test", "and", "or", "xor", "shl", "shr", "sar", "sal", "rol", "ror", "rcl", "rcr", "shld", "shrd",
                "inc", "dec", "neg", "imul", "mul", "idiv", "div", "adc", "sbb", "bt", "bts", "btr", "btc", "bsf",
                "bsr"}


def emu(start, regs, stops, maxsteps=400):
    """Run the objdump instructions from `start` with the given register values until an address in `stops`.
    Returns (stop address, registers, pushes, calls [(site, target, eax)], stores [(operand, value)]).
    Only what a compiled switch uses is modelled; anything that would change a tracked register in an unknown way
    makes it None, and a branch on unknown flags raises EmuError."""
    R = {r: None for r in REGS}
    R.update(regs)
    flags = None                  # ("cmp", a, b) or ("res", value)
    pushes, calls, stores = [], [], []
    va = start
    for _ in range(maxsteps):
        if va in stops:
            return va, R, pushes, calls, stores
        x = ins_at(va)
        if x is None:
            raise EmuError("no instruction at 0x%08X" % va)
        mn, ops = x
        nxt = S4.asm().next_va(va)
        a = [o.strip() for o in ops.split(",")] if ops else []
        dst = a[0] if a else None

        def val(o):
            if o in R:
                return R[o]
            v = imm(o)
            if v is None:
                raise EmuError("operand %s at 0x%08X" % (o, va))
            return v

        if mn in FLAG_CLOBBER and not (mn == "xor" and len(a) > 1 and a[1] == dst):
            flags = None              # flags this model does not compute: a later jcc raises EmuError (S2c review)
        if mn == "call" or (mn in ("cmp", "sub", "add") and dst not in R):
            flags = None              # a callee, or a compare/arithmetic on memory, leaves flags emu does not know
                                      # (lane/rbs review)
        if mn == "cmp" and dst in R:
            flags = ("cmp", val(dst), val(a[1]))
        elif mn in ("sub", "add") and dst in R:
            v0, v1 = val(dst), val(a[1])
            if v0 is None:
                raise EmuError("unknown %s at 0x%08X" % (dst, va))
            r = (v0 - v1) & M32 if mn == "sub" else (v0 + v1) & M32
            flags = ("cmp", v0, v1) if mn == "sub" else ("res", r)
            R[dst] = r
        elif mn == "mov" and dst in R:
            try:
                R[dst] = val(a[1])
            except EmuError:
                R[dst] = None
        elif mn == "xor" and dst in R and a[1] == dst:
            R[dst] = 0
            flags = ("res", 0)
        elif mn == "lea" and dst in R:
            m = re.fullmatch(r"\[(e[a-z]{2})([+-])0x([0-9a-f]+)\]", a[1])
            if not m or R.get(m.group(1)) is None:
                R[dst] = None
            else:
                d = int(m.group(3), 16)
                R[dst] = (R[m.group(1)] + (d if m.group(2) == "+" else -d)) & M32
        elif mn == "movzx" and dst in R:
            m = re.fullmatch(r"BYTE PTR \[(e[a-z]{2})\+0x([0-9a-f]+)\]", a[1])
            if m and R.get(m.group(1)) is not None:
                R[dst] = u8_at((R[m.group(1)] + int(m.group(2), 16)) & M32)
            else:
                R[dst] = None
        elif mn == "push":
            v = imm(ops)
            pushes.append(v if v is not None else ops)
        elif mn == "call":
            calls.append((va, S4.branch_target(ops), R["eax"]))
            R["eax"] = None
        elif mn == "mov" and dst and "PTR" in dst:
            src = a[1] if len(a) > 1 else None
            stores.append((dst, R[src] if src in R else imm(src) if src and imm(src) is not None else src))
        elif mn == "jmp":
            t = S4.branch_target(ops)
            if t is not None:
                va = t
                continue
            m = re.fullmatch(r"DWORD PTR \[(e[a-z]{2})\*4\+0x([0-9a-f]+)\]", ops)
            if not m or R.get(m.group(1)) is None:
                raise EmuError("jmp %s at 0x%08X" % (ops, va))
            va = S4.dword((int(m.group(2), 16) + 4 * R[m.group(1)]) & M32)
            continue
        elif mn.startswith("j"):
            t = S4.branch_target(ops)
            if flags is None:
                raise EmuError("%s with no flags at 0x%08X" % (mn, va))
            if flags[0] == "cmp":
                x0, x1 = flags[1], flags[2]
                if x0 is None or x1 is None:
                    raise EmuError("unknown compare at 0x%08X" % va)
                u0, u1, i0, i1 = x0 & M32, x1 & M32, s32v(x0), s32v(x1)
            else:
                u0, u1, i0, i1 = flags[1] & M32, 0, s32v(flags[1]), 0
                if mn not in ("je", "jne"):
                    raise EmuError("%s after an add at 0x%08X" % (mn, va))
            take = {"je": u0 == u1, "jne": u0 != u1, "ja": u0 > u1, "jae": u0 >= u1, "jb": u0 < u1,
                    "jbe": u0 <= u1, "jg": i0 > i1, "jge": i0 >= i1, "jl": i0 < i1, "jle": i0 <= i1}.get(mn)
            if take is None:
                raise EmuError("%s at 0x%08X" % (mn, va))
            if take:
                va = t
                continue
        elif mn in ("ret", "retn"):
            return va, R, pushes, calls, stores
        elif dst in R:
            R[dst] = None
        va = nxt
    raise EmuError("no stop within %d steps from 0x%08X" % (maxsteps, start))


# =========================================================================================================== static
NPC_ACTION1 = (0x00579E23, 0x00579E7D, 0x0057A7DB)      # entry (EAX = NPC class), accept, refuse
NPC_ACTION2 = (0x00579EA6, 0x00579ED5, 0x0057A7DB)
REC_SWITCH = (0x00536252, 0x005363F8)                   # NPCSTORE_CtlCreate's vendor-index switch (EAX = class)
LIST_SWITCH = (0x00536FDA, 0x0053704D, 0x00537052)       # VENDOR_BuildAllLists' switch (ESI = class): push N, call
PLAYER_OP = (0x005666C5, 0x00566A42)                    # CUBE_Transmute after `movzx eax, byte [ebx+4]` (op)
SPEC_TRADE = {147, 148, 154, 177, 178, 199, 202, 252, 253, 254, 255, 257, 405, 511, 512, 513}
SPEC_GAMBLE = {147, 199, 254, 405, 512, 514}


def slot_table():
    n = S4.dword(0x00731184)
    data, _, _ = S4.image()
    off = S4.va_off(0x00731188)
    return [dict(cls=struct.unpack_from("<I", data, off + 8 * i)[0], store=data[off + 8 * i + 4],
                 act=data[off + 8 * i + 5], f6=data[off + 8 * i + 6]) for i in range(n)]


def chk_dispatch(R):
    acc1 = set()
    acc2 = set()
    for cls in range(0, 800):
        for (st, ok, no), acc in ((NPC_ACTION1, acc1), (NPC_ACTION2, acc2)):
            stop = emu(st, {"eax": cls}, {ok, no})[0]
            if stop == ok:
                acc.add(cls)
    R.add("trade_classes", len(acc1))
    R.add("gamble_classes", len(acc2))
    if acc1 != SPEC_TRADE or acc2 != SPEC_GAMBLE:
        R.add("bad")
        R.note("NPC_MenuAction lists differ from the spec: trade %s, gamble %s" % (sorted(acc1), sorted(acc2)))
    slots = slot_table()
    store = {s["cls"] for s in slots if s["store"] == 1}
    R.note("NPC_MenuAction action 1 (emu from 0x%08X): %s" % (NPC_ACTION1[0], sorted(acc1)))
    R.note("NPC_MenuAction action 2 (emu from 0x%08X): %s" % (NPC_ACTION2[0], sorted(acc2)))
    R.note("g_NpcStoreTable store flag 1: %s; minus the trade list: %s" % (sorted(store), sorted(store - acc1)))
    # the record filler (list index from the call 0x00535FB0's EAX, gambler from a store to [esi-0x8])
    rec, gam = {}, set()
    for cls in sorted({s["cls"] for s in slots}):
        stop, Rg, pu, calls, stores = emu(REC_SWITCH[0], {"eax": cls}, {REC_SWITCH[1]})
        lst = [c[2] for c in calls if c[1] == 0x00535FB0]
        rec[cls] = lst[0] if lst else None
        if any(d == "DWORD PTR [esi-0x8]" and v == 1 for d, v in stores):
            gam.add(cls)
    bld = {}
    for cls in sorted({s["cls"] for s in slots}):
        stop, Rg, pu, calls, stores = emu(LIST_SWITCH[0], {"esi": cls}, {LIST_SWITCH[1], LIST_SWITCH[2]})
        bld[cls] = pu[-1] if stop == LIST_SWITCH[1] else None
    agree = [c for c in rec if rec[c] is not None and rec[c] == bld[c]]
    differ = [(c, rec[c], bld[c]) for c in rec if rec[c] != bld[c]]
    R.add("filler_builder_agree", len(agree))
    R.note("record filler vs list builder (class: filler, builder): agree on %d classes %s; differ %s" % (
        len(agree), sorted(agree), differ))
    used = set(v for v in rec.values() if v is not None) | set(v for v in bld.values() if v is not None)
    R.note("vendor indices used: %s (unused in 0..16: %s); gamblers set by the filler: %s" % (
        sorted(used), sorted(set(range(17)) - used), sorted(gam)))
    if gam != SPEC_GAMBLE or acc2 != gam:
        R.add("bad")
    if differ != [(514, 15, 16)] or 514 in acc1 or 11 in used:
        R.add("bad")
    if store - acc1 != {514} or not acc1 <= store:
        R.add("bad")
    # the cube's PlayerOp switch
    tgt = {}
    for op in range(256):
        try:
            stop = emu(PLAYER_OP[0], {"eax": op}, {PLAYER_OP[1]} | set(range(0x005666D8, 0x00566A42)),
                       maxsteps=8)[0]
        except EmuError:
            stop = None
        tgt[op] = stop
    passing = sorted(op for op, s in tgt.items() if s == PLAYER_OP[1])
    tested = sorted(op for op, s in tgt.items() if s != PLAYER_OP[1])
    R.add("playerop_pass", len(passing))
    R.add("playerop_tested", len(tested))
    R.note("PlayerOp (emu from 0x%08X): ops passing to the matcher 0x%08X with no test: 0 and %d..%d (%d values); "
           "tested: %s" % (PLAYER_OP[0], PLAYER_OP[1], min(p for p in passing if p), max(passing), len(passing),
                           tested))
    if passing != [0] + list(range(15, 256)) or tested != list(range(1, 15)):
        R.add("bad")
    tab = [S4.dword(0x00566AA8 + 4 * i) for i in range(14)]
    R.note("op 1..14 jump table 0x00566AA8: %s" % " ".join("%d:0x%X" % (i + 1, t) for i, t in enumerate(tab)))
    if PLAYER_OP[1] in tab:
        R.add("bad")


def ghidra_xrefs():
    path = os.path.join(SCRATCH, "ghidra-xrefs.txt")
    return S4.ghidra_xrefs(path)


def chk_callers(R):
    gx = ghidra_xrefs() or {}

    def both(target, label, want=None):
        raw = S4.raw_callers(target)
        gh = sorted(s for s, k in gx.get(target, []) if "CALL" in k)
        R.add("%s_raw" % label, len(raw))
        R.add("%s_ghidra" % label, len(gh))
        R.note("%s 0x%08X: raw %s; Ghidra %s" % (label, target, " ".join("0x%08X" % s for s in raw),
                                                 "same" if gh == raw else " ".join("0x%08X" % s for s in gh)))
        if gx and gh != raw:
            R.add("bad")
        if want is not None and raw != sorted(want):
            R.add("bad")
        return raw
    both(0x00576980, "VENDOR_BuildStock", [0x00578BCB, 0x005794C2, 0x00579116])
    both(0x00536D10, "NPCSTORE_Reset", [0x005372D8, 0x005794B3])
    both(0x0062BCB0, "ITEMS_SetSockets", [0x00556C5C, 0x00556C8A, 0x00558F60, 0x005663B6, 0x0057A3E2])
    gs = both(0x005438B0, "QUESTS_GetSeed")
    both(0x00637910, "ITEMRATIO_Select", [0x00556FD9, 0x005586DB])
    # the callers' functions not reached by quest code: a walk from every quest callback the init functions store
    roots = quest_callbacks()
    G = S4.graph(sorted(roots))
    for t, label in ((0x00576980, "VENDOR_BuildStock"), (0x00536D10, "NPCSTORE_Reset")):
        R.add("%s_in_quest_closure" % label, int(t in G))
        if t in G:
            chain = [t]
            while G[chain[-1]][1] is not None:
                chain.append(G[chain[-1]][1])
            R.note("%s is reached from quest code by: %s" % (label, " <- ".join(name(c) for c in chain)))
            if t == 0x00576980 or 0x0052E2A0 not in chain:
                R.add("bad")
    R.note("quest closure: %d functions from %d callbacks of the 37 init functions (indirect calls not followed: %d "
           "sites)" % (len(G), len(roots), sum(len(v[4]) for v in G.values())))
    # ITEMRATIO_Select's version argument at each call
    drop = pushes_before(0x005586DB, 0x10)
    R.note("ITEMRATIO_Select at 0x005586DB (ITEMS_DropRollQuality): pushes %s (version argument first: 0x64)" % drop)
    if not drop or imm(drop[0]) != 0x64:
        R.add("bad")
    w = window(0x00556FB1, 0x00556FDE)
    seq = [(mn, ops) for _, mn, ops in w]
    want = [("cmp", "ax,0x1"), ("sbb", "ecx,ecx"), ("and", "ecx,0xffffff9c"), ("add", "ecx,0x64")]
    ok = all(x in seq for x in want)
    R.add("creation_roll_version_arg_0_or_100", int(ok))
    R.note("ITEMRATIO_Select at 0x00556FD9 (ItemRollQualityCreate): ecx = version < 1 ? 0 : 100 by %s" % (
        "cmp ax,1; sbb ecx,ecx; and ecx,-100; add ecx,100" if ok else "NOT FOUND"))
    if not ok:
        R.add("bad")
    # g_CubeAllRows
    ab = S4.raw_abs(0x0088CAC0)
    sec = S4.section_of(0x0088CAC0)
    R.add("g_CubeAllRows_refs", len(ab))
    data, base, secs = S4.image()
    init = None
    for sva, vsz, raw, rsz, nm, _ in secs:
        if sva <= 0x0088CAC0 < sva + vsz:
            o = 0x0088CAC0 - sva
            init = struct.unpack_from("<I", data, raw + o)[0] if o + 4 <= rsz else "zero-filled (past the raw data)"
    R.note("g_CubeAllRows 0x0088CAC0: absolute references %s (Ghidra: %s); section %s; initial value %s" % (
        " ".join("0x%08X" % a for a in ab), gx.get(0x0088CAC0), sec, init))
    if len(ab) != 1 or init not in (0, "zero-filled (past the raw data)"):
        R.add("bad")
    return gs


QUEST_COUNT, QUEST_DESCS = 0x00731888, 0x00731510


def quest_descs():
    n = S4.dword(QUEST_COUNT)
    return [dict(init=S4.dword(QUEST_DESCS + 0x18 * i), act=S4.dword(QUEST_DESCS + 0x18 * i + 4),
                 id=S4.dword(QUEST_DESCS + 0x18 * i + 0x10), word=S4.dword(QUEST_DESCS + 0x18 * i + 0x14))
            for i in range(n)]


def init_stores(init):
    """{(offset): value} of `mov DWORD PTR [reg+off], imm` in a quest init function's body."""
    A = S4.asm()
    vas, _, _ = S4.body(A, init)
    out = collections.defaultdict(list)
    reg = {}
    for va in sorted(vas):
        mn, ops = A.ins[va]
        a = [o.strip() for o in ops.split(",")]
        if mn == "mov" and a[0] in REGS:
            reg[a[0]] = imm(a[1])
        elif mn == "xor" and a[0] in REGS and len(a) > 1 and a[1] == a[0]:
            reg[a[0]] = 0
        elif mn == "call":
            for r in ("eax", "ecx", "edx"):
                reg[r] = None
        elif a and a[0] in REGS and mn not in ("push", "cmp", "test"):
            reg[a[0]] = None
        m = re.fullmatch(r"DWORD PTR \[e[a-z]{2}\+0x([0-9a-f]+)\]", a[0]) if mn == "mov" and len(a) > 1 else None
        if m:
            v = imm(a[1]) if imm(a[1]) is not None else reg.get(a[1])
            if v is not None:
                out[int(m.group(1), 16)].append(v)
    return out


def quest_callbacks(descs=None):
    """The function pointers the init functions store into the quest object (Quest+0xA0 .. +0xEC)."""
    text = S4.image()[2][0]
    out = set()
    for d in (descs or quest_descs()):
        for off, vals in init_stores(d["init"]).items():
            for v in vals:
                if text[0] <= v < text[0] + text[1] and 0xA0 <= off <= 0xF0:
                    out.add(v)
    return out


def chk_questinit(R):
    """g_QuestDescs +0x14 (the word QuestsPlayerJoin reads at 0x005462F4) against the word each init function stores
    at Quest+0xE0 (the word the quest's own scripts use)."""
    descs = quest_descs()
    R.add("records", len(descs))
    differ = []
    for d in descs:
        w = init_stores(d["init"]).get(0xE0, [])
        if w == [d["word"]]:
            R.add("init_word_agrees")
        else:
            differ.append((d["id"], d["word"], w))
            R.add("init_word_differs")
            R.note("object %d (act %d): g_QuestDescs word %d; its init 0x%08X stores %s at Quest+0xE0" % (
                d["id"], d["act"], d["word"], d["init"], w))
    R.note("object -> word (g_QuestDescs +0x10 -> +0x14): %s" % ", ".join(
        "%d->%d" % (d["id"], d["word"]) for d in sorted(descs, key=lambda d: d["id"])))
    spec = dict([(i, i) for i in range(7)] + [(7 + i, 8 + i) for i in range(7)] + [(14 + i, 16 + i) for i in range(7)]
                + [(21 + i, 24 + i) for i in range(4)] + [(25, 29), (26, 30), (27, 31), (28, 32), (29, 33), (30, 41)]
                + [(31 + i, 35 + i) for i in range(6)])
    got = {d["id"]: d["word"] for d in descs}
    if got != spec:
        R.add("bad")
        R.note("spec map differs: %s" % sorted(set(spec.items()) ^ set(got.items())))
    else:
        R.add("spec_map_equal")
    # the join path reads +0x14 as a record word
    w = window(0x005462DF, 0x0054633E)
    seq = [(mn, o) for _, mn, o in w]
    join = ("mov", "esi,0x731524") in seq and ("mov", "eax,DWORD PTR [esi]") in seq and \
        sum(1 for mn, o in seq if mn == "call" and S4.branch_target(o) in (0x0065C310, 0x0065C360)) == 3
    R.add("join_reads_desc_word", int(join))
    R.note("QuestsPlayerJoin 0x005462DF: esi = &g_QuestDescs[0].word, GetState(rec, [esi], 0/15) and SetState(game rec, "
           "[esi], 15): %s" % join)
    if not join or sorted(x[0] for x in differ) != [28, 30]:
        R.add("bad")


def chk_store(R):
    w = window(0x00535EA0, 0x00535F30)
    ops = " | ".join("%s %s" % (mn, o) for _, mn, o in w)
    has40 = any(mn == "cmp" and o.endswith(",0x40") for _, mn, o in w)
    seq = [(mn, o) for _, mn, o in w]
    has44 = ("shl", "edi,0x4") in seq and ("add", "edi,eax") in seq and ("cmp", "DWORD PTR [esi+edi*4],edx") in seq
    R.add("findrec_bound_0x40", int(has40))
    R.add("findrec_stride_0x44", int(has44))
    if VERBOSE:
        R.note("NPCSTORE_FindRec: " + ops)
    wc = window(0x00536070, 0x005360D2)
    alloc = [o for _, mn, o in wc if mn == "push" and imm(o) == 0x1100]
    R.add("ctlcreate_alloc_0x1100", len(alloc))
    if not (has40 and has44 and alloc):
        R.add("bad")
    R.note("NPCSTORE_FindRec 0x00535EA0: loop bound cmp eax,0x40 %s, record i at recs + 4 * (16i + i) = 0x44 i %s; NPCSTORE_CtlCreate allocates "
           "0x1100 = 64 x 0x44 (%s)" % (has40, has44, bool(alloc)))
    slots = slot_table()
    R.add("slot_entries", len(slots))
    acts = collections.Counter(s["act"] for s in slots)
    R.note("g_NpcStoreTable 0x00731184: count %d, acts %s, store flags %s" % (
        len(slots), dict(sorted(acts.items())), dict(collections.Counter(s["store"] for s in slots))))
    # the slot-table readers: every eax*8 + 0x0073118x operand of the image
    A = S4.asm()
    reads = [(va, o) for va, (mn, o) in A.ins.items() if re.search(r"\[e[a-z]{2}\*8\+0x7311(8[89a-f]|9[0-9a-f])\]", o)]
    R.add("slot_reads_stride8", len(reads))
    R.note("stride-8 reads of the slot table: %s" % ", ".join("0x%08X %s" % r for r in sorted(reads)))
    if len(slots) != 43 or set(acts) != {0, 1, 2, 3, 4} or not reads:
        R.add("bad")


def chk_cow(R):
    pu = pushes_before(0x00594228, 0x28)
    R.note("CUBE_CowPortalOpen's PortalObjectCreate call 0x00594228: pushes %s" % pu)
    vals = [imm(p) for p in pu]
    lvl, cls = 39 in vals, 60 in vals
    R.add("push_level_39", int(lvl))
    R.add("push_class_60", int(cls))
    lv = [l.rstrip("\n").split("\t") for l in open(os.path.join(EXCEL, "levels.txt"), errors="replace")]
    lrows = [r for r in lv[1:] if r and r[0] != "Expansion"]
    ob = [l.rstrip("\n").split("\t") for l in open(os.path.join(EXCEL, "objects.txt"), errors="replace")]
    orows = [r for r in ob[1:] if r and r[0] != "Expansion"]
    R.note("Levels row 39: %s; Objects row 60: %s" % (lrows[39][0], orows[60][0]))
    if not (lvl and cls) or "Moo" not in lrows[39][0]:
        R.add("bad")


def chk_rngwalk(R):
    for root, label, stop in ((0x00545340, "spot_search", ()), (0x0056D130, "PortalObjectCreate", ()),
                              (0x005761C0, "ItemRepairAll", (0x0055F900,))):
        # ItemRepairAll: the broken-item branch (sub_0055F900_ItemRepairBroken, item flag 0x100) is not walked: a
        # new stock item is never broken
        G = S4.graph([root], stop=set(stop))
        rf = S4.rng_functions(G)
        ic = sum(len(v[4]) for v in G.values())
        R.add("%s_functions" % label, len(G))
        R.add("%s_rng_functions" % label, len(rf))
        R.note("%s 0x%08X: %d functions walked, %d indirect call sites not followed; drawing functions: %s" % (
            label, root, len(G), ic, ", ".join("%s (lcg %s, calls %s)" % (
                name(e), ["0x%08X" % x for x in v[0]], [(hex(s), n) for s, n in v[1]]) for e, v in rf.items()) or "none"))
        if label == "ItemRepairAll" and rf:
            R.add("bad")


def chk_copy(R):
    G = S4.graph([0x0055A2A0], stop={0x0062FFF0, 0x0062CBE0, 0x00558CB0})
    _, _, vas, calls, icalls = G[0x0055A2A0]
    tg = [t for _, t in calls]
    reach = {t for e in G for t in [x for _, x in (G[e][3] or [])]}
    for t, label in ((0x0062FFF0, "ITEMS_WriteFull"), (0x00558CB0, "ItemCreateFromSave"), (0x0062CBE0, "ITEMS_ReadFull")):
        R.add("%s_reached" % label, int(t in reach or t in tg))
    G2 = S4.graph([0x00558CB0], stop={0x0062CBE0})
    reads = 0x0062CBE0 in {t for e in G2 for _, t in G2[e][3]}
    R.add("ItemCreateFromSave_calls_ReadFull", int(reads))
    R.note("ItemCopy 0x0055A2A0 calls: %s" % ", ".join("0x%08X %s" % (s, name(t)) for s, t in calls))
    if not ((0x0062FFF0 in reach or 0x0062FFF0 in tg) and 0x00558CB0 in tg and reads):
        R.add("bad")


READER_SITES = [0x00531355, 0x00531578, 0x005311B5, 0x005313F0, 0x0055A41C, 0x0056AE18]


def chk_readers(R):
    for site in READER_SITES:
        w = [x for x in window(site - 0x70, site + 5) if x[0] < site]
        pu = [o for _, mn, o in w if mn == "push"]
        mode4 = False
        for i, (va, mn, o) in enumerate(w):
            if mn == "call" and S4.branch_target(o) == 0x00624690:
                pv = [x for x in w[max(0, i - 3):i] if x[1] == "push"]
                if pv and imm(pv[0][2]) == 4:
                    mode4 = True
        p_last4 = pu[-7:-3] if len(pu) >= 7 else pu
        R.add("sites")
        R.add("setmode4", int(mode4))
        R.note("insert call 0x%08X (%s): UNIT_SetMode(child, 4) before it: %s; pushes %s" % (
            site, name(containing(site) or 0), mode4, pu[-8:]))
        if site != 0x00531355 and not mode4:
            R.add("no_setmode_here")
    # the p7 gate before the refill call
    w = window(0x0056282C, 0x00562850)
    R.note("refill gate: %s" % " | ".join("%08X %s %s" % x for x in w))
    gate = any(mn == "cmp" and "0x24]" in o or mn == "cmp" and "[ebp+0x20]" in o for _, mn, o in w)
    R.add("p7_gate_seen", int(gate))


def chk_match(R):
    A = S4.asm()
    vas, calls, icalls = S4.body(A, 0x0062BED0)
    mem = collections.Counter()
    for va in sorted(vas):
        mn, ops = A.ins[va]
        for m in re.finditer(r"(BYTE|WORD|DWORD) PTR (?:ds:)?\[([^\]]+)\]", ops):
            mem[(m.group(1), m.group(2))] += 1
    glob = [k for k in mem if re.fullmatch(r"0x[0-9a-f]+", k[1])]
    ver = [k for k in mem if re.search(r"\+0x(30|f6|70|78|6a|74)$", k[1]) and "ebp" not in k[1] and "esp" not in k[1]]
    R.add("instructions", len(vas))
    R.add("calls", len(calls))
    R.add("version_or_game_operands", len(ver))
    R.note("RUNEWORD_Match: callees %s; global operands %s; operands at +0x30/+0xF6/+0x6A/+0x70/+0x74/+0x78: %s" % (
        sorted({name(t) for _, t in calls}), sorted(g[1] for g in glob), ver))
    if VERBOSE:
        R.note("memory operands: %s" % sorted(mem.items()))


def ghidra_fn_of(site):
    """The Ghidra function containing a call site, from the saved xrefs ("in NAME@ADDR")."""
    path = os.path.join(SCRATCH, "ghidra-xrefs.txt")
    if not hasattr(ghidra_fn_of, "m"):
        ghidra_fn_of.m = {}
        if os.path.exists(path):
            for ln in open(path, errors="replace"):
                m = re.match(r"to\s+0x([0-9A-F]+) \S+ in (\S+)@0x([0-9A-F]+)", ln)
                if m:
                    ghidra_fn_of.m[int(m.group(1), 16)] = (m.group(2), int(m.group(3), 16))
    return ghidra_fn_of.m.get(site)


def traced_pushes(site, back=0x40):
    """The push operands before a call, nearest last, a register resolved to the constant last moved into it
    within the window (None when not a constant)."""
    w = [x for x in window(site - back, site + 5) if x[0] < site]
    reg, out = {}, []
    for va, mn, o in w:
        a = [x.strip() for x in o.split(",")]
        if mn == "push":
            out.append(imm(o) if imm(o) is not None else reg.get(o))
        elif mn == "mov" and a[0] in REGS:
            reg[a[0]] = imm(a[1]) if len(a) > 1 else None
        elif mn == "xor" and a[0] in REGS and len(a) > 1 and a[1] == a[0]:
            reg[a[0]] = 0
        elif mn == "call":
            for r in ("eax", "ecx", "edx"):
                reg[r] = None
        elif a and a[0] in REGS and mn not in ("cmp", "test"):
            reg[a[0]] = None
    return out


def setstate_sites():
    """[(site, function name, word, bit, kind)] for every SetState/ClearState call (stdcall rec, word, bit: pushed
    bit, word, rec); word/bit None when not a constant in the window before the call."""
    out = []
    for target, kind in ((0x0065C360, "set"), (0x0065C3A0, "clear")):
        for site in S4.raw_callers(target):
            pu = traced_pushes(site, 0x30)
            bit = pu[-3] if len(pu) >= 3 else None
            word = pu[-2] if len(pu) >= 2 else None
            g = ghidra_fn_of(site)
            out.append((site, g[0] if g else name(containing(site) or 0), word, bit, kind))
    return out


def chk_setstate(R):
    sites = setstate_sites()
    R.add("set_sites", sum(1 for s in sites if s[4] == "set"))
    R.add("clear_sites", sum(1 for s in sites if s[4] == "clear"))
    R.add("nonconstant", sum(1 for s in sites if s[2] is None or s[3] is None))
    b15 = [s for s in sites if s[3] == 15]
    for s in b15:
        R.note("bit 15 %s: 0x%08X in %s, word %s" % (s[4], s[0], s[1], s[2]))
    R.add("bit15_set", sum(1 for s in b15 if s[4] == "set"))
    R.add("bit15_clear", sum(1 for s in b15 if s[4] == "clear"))
    for s in sites:
        if s[2] is None or s[3] is None:
            R.note("non-constant %s 0x%08X in %s: word %s bit %s" % (s[4], s[0], s[1], s[2], s[3]))
    for w_, b_, k in ((14, 5, "clear"), (14, 1, "set"), (22, 0, "set"), (26, 0, "set"), (40, 0, "set"), (22, 13, "set"),
                      (22, 11, "set"), (10, 0, "set"), (10, 13, "set")):
        hit = [s for s in sites if s[2] == w_ and s[3] == b_ and s[4] == k]
        R.add("w%d_b%d_%s" % (w_, b_, k), len(hit))
        R.note("word %d bit %d %s: %s" % (w_, b_, k, ", ".join("0x%08X %s" % (s[0], s[1]) for s in hit) or "none"))
    return sites


def chk_qgraph(R):
    descs = quest_descs()
    by_word = {d["word"]: d for d in descs}
    sinks = {0x00558D90: "ItemCreate", 0x00558CB0: "ItemCreateFromSave", 0x0055A2A0: "ItemCopy",
             0x00559A30: "DropItemAtUnit", 0x005466B0: "QUESTS_GiveItem", 0x00559CE0: "ITEMS_CreateForStore",
             0x00585970: "DropItemCodeAt", 0x0055AFA0: "TC_DropByIndex", 0x00585B90: "ObjectChestDrop"}
    # the generic engine entries the scripts call (a unit's creation, a mode change, a kill, experience and level-up, a
    # portal): their own item creations (a monster's equipment, room restores, skill items) are not the scripts'
    engine = {0x00555230: "SUnitCreate", 0x005A7C20: "MonSetMode", 0x0057CCB0: "UnitKilled",
              0x0057E510: "PLAYER_AddExperience", 0x00570880: "PLAYER_LevelUp", 0x0056D130: "PortalObjectCreate"}
    for label, roots in (("diablo_death", [0x005B52E0]),
                         ("a5q4", sorted(quest_callbacks([by_word[38]]))),
                         ("a5q5", sorted(quest_callbacks([by_word[39]])))):
        G = S4.graph(roots, stop=set(engine))
        stops = sorted({engine[t] for e in G for _, t in G[e][3] if t in engine})
        R.note("%s: engine entries called (not walked): %s" % (label, stops))
        hit = sorted(set(G) & set(sinks))
        ic = sum(len(v[4]) for v in G.values())
        R.add("%s_functions" % label, len(G))
        R.add("%s_creators_reached" % label, len(hit))
        R.note("%s: roots %s; %d functions, %d indirect call sites not followed; creators reached: %s" % (
            label, " ".join("0x%08X" % r for r in roots), len(G), ic, [sinks[h] for h in hit] or "none"))
        if hit:
            R.add("bad")


def magic_exact(m, s, d):
    """True when floor(n * m / 2**s) == n // d for every 32-bit n (Granlund-Montgomery: 0 < m*d - 2**s <= 2**(s-32))."""
    e = m * d - (1 << s)
    return 0 < e <= (1 << (s - 32))


def chk_inline(R):
    """The inline quest-seed draws: in every function that calls QUESTS_GetSeed, the LCG multiplier sites and the
    multiply-shift constants after them."""
    gx = ghidra_xrefs() or {}
    fns = sorted({containing(s) for s in S4.raw_callers(0x005438B0)})
    A = S4.asm()
    magic = collections.Counter()
    for f in fns:
        vas, calls, _ = S4.body(A, f)
        lcg = [va for va in sorted(vas) if S4.has_imm(A.ins[va][1], S4.LCG_MUL)]
        mags = [(va, imm(A.ins[va][1].split(",")[1])) for va in sorted(vas)
                if A.ins[va][0] == "mov" and "," in A.ins[va][1] and imm(A.ins[va][1].split(",")[1]) in
                (0xCCCCCCCD, 0x24924925, 0x2E8BA2E9)]
        rc = [(hex(s), S4.RNG_FNS[t]) for s, t in calls if t in S4.RNG_FNS]
        rl = [hex(s) for s, t in calls if t == 0x004BC500]
        for _, v in mags:
            magic[v] += 1
        R.note("%s: lcg %d, magic %s, rng calls %s, RandLoHi %s" % (
            name(f), len(lcg), [hex(v) for _, v in mags], rc, rl))
    # exactness of the two divisors the scripts use
    ok5 = magic_exact(0xCCCCCCCD, 34, 5)
    ok7 = magic_exact(0x124924925, 35, 7)
    R.add("mod5_magic_exact", int(ok5))
    R.add("mod7_magic_exact", int(ok7))
    R.note("magic constants seen: %s; 0xCCCCCCCD >> 34 is exact /5: %s; (2^32 + 0x24924925) >> 35 is exact /7: %s" % (
        {hex(k): v for k, v in magic.items()}, ok5, ok7))
    if not (ok5 and ok7):
        R.add("bad")


def chk_imbue(R):
    # NPC_MenuAction's imbue branch: the GetState calls with their pushed word and bit up to the ItemCreate call
    sites = []
    for va, mn, o in window(0x00579F32, 0x0057A0D0):
        if mn == "call" and S4.branch_target(o) == 0x0065C310:
            pu = pushes_before(va, 0x10)
            sites.append((va, imm(pu[-2]) if len(pu) >= 2 else None, imm(pu[-3]) if len(pu) >= 3 else None))
    R.note("imbue branch GetState calls (site, word, bit): %s" % [("0x%08X" % a, w, b) for a, w, b in sites])
    w3 = sorted({b for _, w, b in sites if w == 3})
    R.add("word3_bits_tested", len(w3))
    R.note("word 3 bits tested: %s" % w3)
    if w3 != [1]:
        R.add("bad")


ANYA = {"Normal": 0x00735F6C, "Nightmare": 0x00735EFC, "Hell": 0x00735F34}


def chk_anya(R):
    data, _, _ = S4.image()
    out = {}
    for k, a in ANYA.items():
        rows = []
        for c in range(7):
            p, n = S4.dword(a + 8 * c), S4.dword(a + 8 * c + 4)
            rows.append([data[S4.va_off(p + 4 * i):S4.va_off(p + 4 * i) + 4].decode("latin1").strip() for i in range(n)])
        out[k] = rows
        R.note("%s 0x%08X: %s" % (k, a, rows))
    want_n = [["am%d" % i for i in range(1, 6)], ["ob%d" % i for i in range(1, 6)], ["ne%d" % i for i in range(1, 6)],
              ["pa%d" % i for i in range(1, 6)], ["ba%d" % i for i in range(1, 6)], ["dr%d" % i for i in range(1, 6)],
              ["ktr", "wrb", "axf", "ces", "clw", "btl", "skr"]]
    if out["Normal"] != want_n:
        R.add("bad")
        R.note("Normal differs from the spec list")
    else:
        R.add("normal_equal")
    nm_ok = all(all(c[-1] in "6789a" for c in row) for row in out["Nightmare"][:6]) and \
        all(c.startswith("9") for c in out["Nightmare"][6])
    h_ok = all(all(c[-1] in "bcdef" for c in row) for row in out["Hell"][:6]) and \
        all(c.startswith("7") for c in out["Hell"][6])
    R.add("nightmare_pattern", int(nm_ok))
    R.add("hell_pattern", int(h_ok))
    if not (nm_ok and h_ok):
        R.add("bad")
    # the reader
    gx = ghidra_xrefs() or {}
    refs = {k: S4.raw_abs(a) for k, a in ANYA.items()}
    R.note("absolute references: %s" % {k: ["0x%08X" % x for x in v] for k, v in refs.items()})


def chk_qseed(R):
    """quest-drops 49: every QUESTS_GetSeed call site, its function (Ghidra), whether that function draws (an LCG
    multiplier or an RNG call) and whether it calls an item creator directly."""
    creators = {0x00559A30, 0x005466B0, 0x00558D90, 0x00559CE0, 0x00585970, 0x0055AFA0, 0x00585B90}
    A = S4.asm()
    fns = collections.OrderedDict()
    for site in S4.raw_callers(0x005438B0):
        g = ghidra_fn_of(site)
        fns.setdefault(g[1] if g else containing(site), []).append(site)
    for f, sites in fns.items():
        vas, calls, _ = S4.body(A, f)
        lcg = [va for va in vas if S4.has_imm(A.ins[va][1], S4.LCG_MUL)]
        rc = [t for _, t in calls if t in S4.RNG_FNS or t == 0x004BC500]
        cr = sorted({name(t) for _, t in calls if t in creators})
        draws = bool(lcg or rc)
        R.add("functions")
        R.add("drawing" if draws else "not_drawing")
        R.add("creating" if cr else "not_creating")
        g = ghidra_fn_of(sites[0])
        R.note("%s 0x%08X: GetSeed calls %d, LCG sites %d, RNG calls %d, item creators called %s" % (
            g[0] if g else name(f), f, len(sites), len(lcg), len(rc), cr or "none"))
        if f in (0x0058E830, 0x00592E90, 0x0059B1C0, 0x0059EDC0, 0x005BD390):
            R.add("named_non_item")
            if not draws or cr:
                R.add("bad")


def cmd_static(ns):
    rc = 0
    for label, fn in (("dispatch", chk_dispatch), ("callers", chk_callers), ("store", chk_store), ("cow", chk_cow),
                      ("rngwalk", chk_rngwalk), ("copy", chk_copy), ("readers", chk_readers), ("match", chk_match),
                      ("setstate", chk_setstate), ("questinit", chk_questinit), ("qgraph", chk_qgraph),
                      ("inline", chk_inline), ("imbue", chk_imbue), ("anya", chk_anya), ("qseed", chk_qseed)):
        if ns.only and label not in ns.only:
            continue
        R = Report("static-" + label)
        try:
            fn(R)
        except EmuError as e:
            R.add("bad")
            R.note("emu: %s" % e)
        rc |= R.done()
    return rc


# =========================================================================================================== tables
def txt(name):
    import excel_bin
    h, rows = excel_bin.read_txt(excel_bin.find_file(EXCEL, name, ".txt"))
    return {k: i for i, k in enumerate(h)}, rows


def binrecs(name):
    import excel_bin
    return excel_bin.read_bin(excel_bin.find_file(EXCEL, name, ".bin"))[0]


def tbl_cube(R):
    import cube
    T = cube.Tables(EXCEL)
    H, rows = txt("cubemain")
    R.add("rows", len(T.rows))
    bad_n = [i for i, r in enumerate(T.rows)
             if r["n"] != sum(max(x["qty"], 1) for x in r["ins"] if x["flags"] & 3)]
    R.add("numinputs_eq_sum_qty", len(T.rows) - len(bad_n))
    if bad_n:
        R.add("bad")
        R.note("numinputs differs from the summed qty: rows %s" % bad_n)
    R.note("disabled rows: %s" % [i for i, r in enumerate(T.rows) if not r["enabled"]])
    # op 28: which inputs bind (base quest and questdiffcheck both set)
    for i, r in enumerate(T.rows):
        if r["op"] != 28:
            continue
        binds, free = [], []
        for x in r["ins"]:
            if not x["flags"] & 3:
                continue
            if x["flags"] & 1 and x["index"] != 0xFFFF:
                raw = T.raw(x["index"])
                (binds if raw[0x12A] and raw[0x12B] else free).append(T.code(x["index"]).decode().strip())
            else:
                free.append("type %d" % x["index"])
        R.add("op28_rows")
        R.note("op 28 row %d (%s): bound %s; not tested %s" % (i, rows[i][H["description"]], binds, free))
    # input cells: `sock=N`
    cols = [k for k in H if re.fullmatch(r"input \d", k)]
    cells = [(i, k, rows[i][H[k]]) for i in range(len(rows)) for k in cols if rows[i][H[k]]]
    sockn = [(i, k, c) for i, k, c in cells if re.search(r"sock=\d", c)]
    sock = [(i, k, c) for i, k, c in cells if re.search(r"(^|,)sock(,|$)", c.strip('"'))]
    R.add("input_cells", len(cells))
    R.add("input_cells_sock_eq_n", len(sockn))
    R.add("input_cells_sock", len(sock))
    R.note("input cells with `sock=N`: %s; with `sock`: %s" % (sockn, [(i, k, c) for i, k, c in sock][:6]))
    # stackable inputs (the got >= qty relaxation): each row has at most one, and numinputs = the summed qty
    st = collections.Counter()
    for i, r in enumerate(T.rows):
        n = sum(1 for x in r["ins"] if x["flags"] & 1 and x["index"] != 0xFFFF and T.P.base(x["index"])["stackable"])
        if n:
            st[n] += 1
    R.note("rows with a stackable input, by count of such inputs: %s" % dict(st))
    R.add("rows_two_stackable_inputs", sum(v for k, v in st.items() if k > 1))
    # exc / eli inputs
    R.note("rows with an exc/eli input: %s" % [i for i, r in enumerate(T.rows) if any(x["flags"] & 0x600 for x in r["ins"])])
    # outputs: eth, bare sock
    R.add("outputs_eth", sum(1 for r in T.rows for o in r["outs"] if o["kind"] and o["flags"] & 4))
    R.add("outputs_sock_without_count", sum(1 for r in T.rows for o in r["outs"] if o["kind"] and o["flags"] & 2
                                           and o["qty"] == 0))
    return T


def crafted_candidates(T, cls, ilvl, side):
    """ITEMS_PickMagicAffix's candidates for a crafted item (spawnable 1, quality 8, no group taken), as tools/affixes.py
    filters them (items/0005 section 3): [(id, group)]."""
    import affixes
    A = T.A
    it = affixes.Item(A, {"cls": cls, "ilvl": ilvl, "ver": 101})
    it.q = 8
    alvl = affixes.alvl_of(it)
    a0, a1 = A.blk_p if side == "p" else A.blk_s
    out = []
    for i in range(a0, a1):
        r = A.magic[i]
        if r["spawn"] == 0 or r["level"] > alvl or (r["maxlevel"] != 0 and r["maxlevel"] < alvl):
            continue
        if r["rare"] == 0 or not affixes.type_ok(A, it, r) or r["freq"] == 0:
            continue
        if r["cs"] != 0xFF and A.tclass(cls) != 7 and r["cs"] != A.tclass(cls):
            continue
        out.append((i + 1, r["group"]))
    return out


def tbl_crafted(R, T):
    """cube 49: the crafted builder's pick of 0 needs a pick with no candidate. The pick skips the groups already
    taken; a side holds at most 3 affixes, and the prefix and suffix groups are disjoint, so the k-th pick of a side
    (k <= 3) has a candidate whenever the side's candidates span k or more groups. A side spanning g <= 2 groups gives a
    pick of 0 at its (g + 1)-th affix, which a count of 4 (or 3) can reach."""
    A = T.A
    pg = {A.magic[i]["group"] for i in range(*A.blk_p)}
    sg = {A.magic[i]["group"] for i in range(*A.blk_s)}
    R.add("prefix_suffix_groups_shared", len(pg & sg))
    rows = [(i, r) for i, r in enumerate(T.rows) if r["enabled"] and any(o["kind"] and o["q"] == 8 for o in r["outs"])]
    R.add("crafted_rows", len(rows))
    low = collections.defaultdict(list)
    nb = 0
    for i, r in rows:
        x = r["ins"][0]
        cls_ = [c for c in range(len(T.P.items))
                if (x["flags"] & 2 and T.A.is_type(c, x["index"]) or x["flags"] & 1 and c == x["index"])
                and T.P.items[c][0x133]]                      # spawnable bases only
        nb += len(cls_)
        o = r["outs"][0]
        for c in cls_:
            for ilvl in range(1, 100):
                for side in ("p", "s"):
                    g = len(set(y[1] for y in crafted_candidates(T, c, ilvl, side)))
                    if g <= 2:
                        low[(i, T.code(c).decode().strip(), side, g)].append(ilvl)
    R.add("crafted_row_bases", nb)
    R.add("cases_side_le_2_groups", len(low))
    R.note("prefix groups %d, suffix groups %d, shared %d" % (len(pg), len(sg), len(pg & sg)))
    for (i, code, side, g), lv in sorted(low.items()):
        o = T.rows[i]["outs"][0]
        R.note("row %d (output lvl %d plvl %d ilvl %d) base %s side %s: %d group(s) at output ilvl %s" % (
            i, o["lvl"], o["plvl"], o["ilvl"], code, side, g, "%d..%d" % (lv[0], lv[-1]) if lv == list(range(lv[0], lv[-1] + 1)) else lv))


def tbl_pick_type(R, T):
    """cube 51: the random item of a type (kind 0xFD): the stock rows, their candidates per ilvl."""
    for i, r in enumerate(T.rows):
        for s, o in enumerate(r["outs"]):
            if o["kind"] != 0xFD:
                continue
            typ = o["index"]
            cand = [c for c in range(len(T.P.items)) if T.A.is_type(c, typ) and T.P.items[c][0x133]]
            lv = sorted(T.P.items[c][0xFD] for c in cand)
            R.add("type_rows")
            R.add("row%d_typed_spawnable" % i, len(cand))
            R.note("row %d output %s: type %d, %d spawnable items of the type (cap 256), levels %d..%d; output lvl %d, plvl %d, "
                   "ilvl %d" % (i, "ABC"[s], typ, len(cand), lv[0], lv[-1], o["lvl"], o["plvl"], o["ilvl"]))
            if len(cand) >= 256:
                R.add("bad")


def tbl_runes(R):
    import props
    H, rows = txt("runes")
    recs = binrecs("runes")
    Ht, trows = txt("itemtypes")
    tcode = {r[Ht["Code"]]: i for i, r in enumerate(trows) if r[Ht["Code"]]}
    ok = n4 = ne = 0
    for r, b in zip(rows, recs):
        it = [tcode.get(r[H["itype%d" % k]], 0) if r[H["itype%d" % k]] else 0 for k in range(1, 7)]
        et = [tcode.get(r[H["etype%d" % k]], 0) if r[H["etype%d" % k]] else 0 for k in range(1, 4)]
        bit = [props.u16(b, 0x86 + 2 * k) for k in range(6)]
        bet = [props.u16(b, 0x92 + 2 * k) for k in range(3)]
        if it == bit and et == bet:
            ok += 1
        else:
            R.add("bad")
            R.note("row %s: txt itype %s etype %s, bin %s %s" % (r[0], it, et, bit, bet))
        n4 += any(it[3:])
        ne += any(et)
    R.add("rows", len(rows))
    R.add("itype_etype_equal", ok)
    R.add("rows_itype4to6", n4)
    R.add("rows_etype", ne)
    R.add("complete_rows_etype", sum(1 for r in rows if r[H["complete"]] == "1" and any(r[H["etype%d" % k]] for k in (1, 2, 3))))
    # T1Param cells through the name links
    Hs, srows = txt("skills")
    Hm, mrows = txt("montype")
    Hst, strows = txt("states")
    links = [{r[Hs["skill"]].lower(): i for i, r in reversed(list(enumerate(srows)))},
             {r[Hm["type"]].lower(): i for i, r in reversed(list(enumerate(mrows)))},
             {r[Hst["state"]].lower(): i for i, r in reversed(list(enumerate(strows)))}]
    cells = eq_ = 0
    for r, b in zip(rows, recs):
        blk = props.blocks(b, 0xB0, 7)
        for k in range(7):
            c = r[H["T1Param%d" % (k + 1)]]
            if c == "":
                continue
            cells += 1
            if c[0] == "-" or c[0].isdigit():
                m = re.match(r"-?\d+", c)
                want = int(m.group(0)) if m else 0
            else:
                want = next((l[c.lower()] for l in links if c.lower() in l), 0)
            if want == blk[k][1]:
                eq_ += 1
            else:
                R.add("bad")
                R.note("T1Param row %s line %d: %r -> %d, bin %d" % (r[0], k + 1, c, want, blk[k][1]))
    R.add("t1param_cells", cells)
    R.add("t1param_equal", eq_)
    R.add("t1param_named", sum(1 for r in rows for k in range(7) if r[H["T1Param%d" % (k + 1)]][:1].isalpha()))
    # names: Runeword95 twice; the Steel save's runeword u16
    names = collections.Counter(r[H["Name"]] for r in rows)
    dup = {k: v for k, v in names.items() if v > 1}
    R.note("Name keys used more than once: %s (%s)" % (dup, [r[H["Rune Name"]] for r in rows if r[H["Name"]] in dup]))
    try:
        import tbl
        S = tbl.Strings(LNG)
        i134, i95 = S.index("Runeword134"), S.index("Runeword95")
        R.note("string index of Runeword134 %d (0x%04X); of Runeword95 %d" % (i134, i134, i95))
        R.add("runeword134_index_0x509F", int(i134 == 0x509F))
        if i134 != 0x509F:
            R.add("bad")
    except Exception as e:                       # noqa: BLE001
        R.note("strings: %s" % e)
    # complete rows: rune sequences
    seqs = [(r[H["Rune Name"]], tuple(x for x in (r[H["Rune%d" % k]] for k in range(1, 7)) if x))
            for r in rows if r[H["complete"]] == "1"]
    same = [(a, b) for i, (a, x) in enumerate(seqs) for (b, y) in seqs[i + 1:] if x == y]
    pref = [(a, b) for (a, x) in seqs for (b, y) in seqs if len(y) == len(x) + 1 and y[:len(x)] == x]
    R.add("complete_rows", len(seqs))
    R.add("complete_same_sequence", len(same))
    R.add("complete_one_shorter_prefix", len(pref))
    if same or pref:
        R.note("shared sequences %s; one-shorter prefixes %s" % (same, pref))
    # T1Code gaps and unknown codes
    Hp, prows = txt("properties")
    pcodes = {r[0].lower() for r in prows}
    gaps = unk = 0
    for r in rows:
        codes = [r[H["T1Code%d" % k]] for k in range(1, 8)]
        last = max([i for i, c in enumerate(codes) if c] or [-1])
        if any(not c for c in codes[:last + 1]):
            gaps += 1
        unk += sum(1 for c in codes if c and c.lower() not in pcodes)
    R.add("t1code_gaps", gaps)
    R.add("t1code_unknown", unk)
    if gaps or unk:
        R.add("bad")


NWEAP_ARMOR = 306 + 202          # item records: weapons, then armor, then misc


def tbl_gems(R):
    import props
    P = props.Tables(EXCEL)
    groups = collections.defaultdict(set)
    n = 0
    zero = collections.Counter()
    for cls in range(len(P.items)):
        b = P.base(cls)
        r = P.items[cls]
        if cls >= NWEAP_ARMOR or not b["hasinv"] or b["gemsockets"] <= 0:
            continue
        n += 1
        t = P.itypes[b["type"]][0:4].decode("latin1").strip("\0 ") if 0 <= b["type"] < len(P.itypes) else str(b["type"])
        groups[r[0x13E]].add(t)
    R.add("hasinv_gemsockets_rows", n)
    for g in sorted(groups):
        R.note("gemapplytype %d: types %s" % (g, sorted(groups[g])))
    if any(g >= 3 for g in groups):
        R.add("bad")
    socketed_types = set().union(*groups.values()) if groups else set()
    for t in ("belt", "boot", "glov"):
        R.add("type_%s_socketable" % t, int(t in socketed_types))
    # gems: nummods against the blocks before the first blank, per group
    recs = binrecs("gems")
    diff = 0
    for r in recs:
        nm = r[0x2E]
        for g in range(3):
            bl = props.blocks(r, 0x30 + 0x30 * g, 3)
            k = next((i for i, x in enumerate(bl) if x[0] < 0), 3)
            if k != nm:
                diff += 1
    R.add("gem_rows", len(recs))
    R.add("gem_groups_nummods_differs", diff)
    R.note("gems rows %d; groups whose block count before the first blank differs from nummods: %d" % (len(recs), diff))
    # gemoffset of the parents (non-gem bases) against the gems row their own +0x0F0 would name
    nz = sum(1 for cls in range(len(P.items)) if not P.is_type(cls, 20) and not P.is_type(cls, 74)
             and struct.unpack_from("<I", P.items[cls], 0xF0)[0])
    R.add("non_gem_bases_with_gemoffset", nz)


def tbl_misc(R):
    # ItemTypes StorePage
    H, rows = txt("itemtypes")
    Hs, srows = txt("storepage")
    codes = [r[Hs["Code"]] for r in srows]
    pages = collections.Counter(r[H["StorePage"]] for r in rows)
    R.note("StorePage codes in storepage.txt order: %s; ItemTypes.StorePage values: %s" % (codes, dict(pages)))
    R.add("types_storepage_mag", pages.get("mag", 0))
    recs = binrecs("itemtypes")
    vals = collections.Counter(r[0x22] for r in recs)
    R.note("itemtypes.bin byte +0x22: %s" % dict(sorted(vals.items())))
    mapped = all(r[0x22] == (codes.index(t[H["StorePage"]]) if t[H["StorePage"]] in codes else 0xFF)
                 for r, t in zip(recs, rows))
    R.add("storepage_bin_is_row_index", int(mapped))
    if pages.get("mag") or not mapped:
        R.add("bad")
    try:
        sp = S4.raw_abs(0)  # placeholder to keep the image loaded
    except Exception:                            # noqa: BLE001
        pass
    data, _, _ = S4.image()
    R.note("'storepage' strings in the image: %d" % data.lower().count(b"storepage"))
    # MonStats TCQuestId
    H, rows = txt("monstats")
    q = [(i, r[H["Id"]], r[H["TCQuestId"]], r[H["TCQuestCP"]]) for i, r in enumerate(rows) if r[H["TCQuestId"]] not in ("", "0")]
    R.add("monstats_tcquestid_rows", len(q))
    R.note("MonStats rows with TCQuestId: %s" % q)
    if sorted(x[1] for x in q) != sorted(["andariel", "duriel", "mephisto", "diablo", "baalcrab"]):
        R.add("bad")
    # ItemRatio versions
    H, rows = txt("itemratio")
    R.note("ItemRatio rows (Version, Uber, Class Specific): %s" % [(i, r[H["Version"]], r[H["Uber"]], r[H["Class Specific"]])
                                                                  for i, r in enumerate(rows)])
    R.add("itemratio_version0_rows", sum(1 for r in rows if r[H["Version"]] in ("0", "")))


def cmd_tables(ns):
    rc = 0
    R = Report("tables-cube")
    T = tbl_cube(R)
    rc |= R.done()
    R = Report("tables-crafted")
    tbl_crafted(R, T)
    rc |= R.done()
    R = Report("tables-picktype")
    tbl_pick_type(R, T)
    rc |= R.done()
    R = Report("tables-runes")
    tbl_runes(R)
    rc |= R.done()
    R = Report("tables-gems")
    tbl_gems(R)
    rc |= R.done()
    R = Report("tables-misc")
    tbl_misc(R)
    rc |= R.done()
    return rc


# ============================================================================================================= cube
CUBE_GRID = (3, 4)                 # inventory.txt "Transmogrify Box Page 1": gridX 3, gridY 4


def crafted_rare_names(T):
    """cube 47: rare-name candidates (ITEMS_RareNameTypeOk) of every crafted base, per side: the builder fails only
    when one side has none."""
    import affixes
    A = T.A
    out = {}
    for i, r in enumerate(T.rows):
        if not (r["enabled"] and any(o["kind"] and o["q"] == 8 for o in r["outs"])):
            continue
        x = r["ins"][0]
        for c in range(len(T.P.items)):
            if not ((x["flags"] & 2 and A.is_type(c, x["index"]) or x["flags"] & 1 and c == x["index"])
                    and T.P.items[c][0x133]):
                continue
            it = affixes.Item(A, {"cls": c, "ilvl": 50, "ver": 101})
            it.q = 8
            out[c] = tuple(sum(1 for k in range(*blk) if affixes.rare_name_ok(A, it, A.rare[k]))
                           for blk in (A.rblk_p, A.rblk_s))
    return out


def cmd_cube(ns):
    import affixes
    import cube
    import items_chain
    import player
    import rng
    T = cube.Tables(EXCEL)
    affixes.PROPS_HOOK = items_chain.make_hook(T.P)
    forced = []
    orig_pick = affixes.Walk.pick

    def pick(self, kind, spawn, must, apply, pre, forced_=0, auto=0):
        if forced_:
            a0, a1 = self.T.blk_a if auto else self.T.blk_p if pre else self.T.blk_s
            r = self.T.magic[a0 + forced_ - 1]
            alvl = affixes.alvl_of(self.it)
            inside = r["level"] <= alvl and (r["maxlevel"] == 0 or r["maxlevel"] >= alvl)
            forced.append(dict(id=forced_, name=r.get("name", ""), level=r["level"], maxlevel=r["maxlevel"], alvl=alvl,
                               inside=inside, ilvl=self.it.ilvl))
        return orig_pick(self, kind, spawn, must, apply, pre, forced_, auto)
    affixes.Walk.pick = pick
    R = Report("cube")
    S = collections.Counter()
    notes = collections.defaultdict(list)
    place = collections.Counter()
    crec = collections.Counter()
    q0 = collections.Counter()
    ethsok = collections.Counter()
    excn = collections.Counter()
    ops = collections.Counter()
    cow = []
    logs = run_logs()["run:2026-10-15-cube"]
    for path in logs:
        made = set()
        pdt = (0, 0)
        for t, d in events(path, ("PDT",)):
            pdt = (d["c6c"], d["c70"])
            break
        for tx in cube.read_log(path):
            c = tx.c
            try:
                res = cube.check_tx(T, tx, S, notes, pdt, made)
            except Exception as e:                       # noqa: BLE001
                R.add("bad")
                R.note("FAIL %s: %s" % (os.path.basename(path), e))
                continue
            R.add("transmutes")
            game = {"diff": c["diff"]}
            # rows that reached the matcher, by op
            for t, d in tx.ev:
                if t == "CMI":
                    ops[T.rows[d["row"]]["op"]] += 1
                    if d["row"] in (131, 132, 135, 136):
                        r = T.rows[d["row"]]
                        r2 = json.loads(json.dumps(r))
                        r2["ins"][0]["flags"] &= ~0x600
                        for it in c["items"]:
                            a = cube.item_test(T, r, 0, it, game)
                            b = cube.item_test(T, r2, 0, it, game)
                            excn["items tested" if True else ""] += 1
                            if a != b:
                                excn["exc test decided"] += 1
            # the creation records
            for t, d in tx.ev:
                if t == "CREC":
                    crec["records"] += 1
                    crec["w28=1"] += d["w28"] == 1
                    crec["ver=game item version"] += d["ver"] == c["iver"]
                    crec["k18=4"] += d["k18"] == 4
                    crec["ver %d" % d["ver"]] += 1
                    if d["q"] == 0:
                        q0["exp" if c["exp"] else "classic"] += 1
                        q0["ver %d" % d["ver"]] += 1
            # ethereal and socket skip bits on the created items
            blk = None
            for t, d in tx.ev:
                if t == "CREC":
                    blk = dict(rfl=d["rfl"], cls=d["idx"], tags=[])
                elif blk is not None and t in ("ETH0", "ETHR", "SOK0", "SOKM", "SOKR", "SSET", "IC0"):
                    blk["tags"].append((t, d))
                elif blk is not None and t == "CRECX":
                    tags = [x[0] for x in blk["tags"]]
                    b = T.P.base(blk["cls"])
                    durable = (T.P.is_type(blk["cls"], 45) or T.P.is_type(blk["cls"], 50)) and not b["nodur"] and b["dur"]
                    q = d["it"]["q"]
                    if "ETH0" in tags:
                        ethsok["ETH0 rfl&2" if blk["rfl"] & 2 else "ETH0 rfl no 2"] += 1
                        if blk["rfl"] & 2 and "ETHR" not in tags:
                            ethsok["ethereal: skip bit, no draw"] += 1
                            if durable and q not in (1, 5) and not b["quest"]:
                                ethsok["ethereal: skip bit, no draw, on a base the roll would draw on"] += 1
                        if blk["rfl"] & 2 and "ETHR" in tags:
                            R.add("bad")
                    if "SOK0" in tags:
                        ethsok["SOK0 rfl&8" if blk["rfl"] & 8 else "SOK0 rfl no 8"] += 1
                        if blk["rfl"] & 8 and "SOKR" in tags and "SSET" not in tags:
                            ethsok["sockets: draw, then the skip bit (no SetSockets)"] += 1
                        if blk["rfl"] & 8 and "SSET" in tags:
                            R.add("bad")
                    blk = None
            # placement in the cube (CUBX items with their grid cell; logger r2 and r3)
            if res.get("produced"):
                x = [d for t, d in tx.ev if t == "CUBX"][-1]
                if x["items"] and all("xy" in it for it in x["items"]):
                    g = player.Grid(*CUBE_GRID)
                    for it in x["items"]:
                        b = T.P.base(it["cls"])
                        at = g.find(b["invw"], b["invh"])
                        got = tuple(it["xy"])
                        key = "%dx%d" % (b["invw"], b["invh"])
                        if at is None or tuple(at) != got:
                            place["mismatch"] += 1
                            R.add("bad")
                            R.note("placement %s %s: model %s, log %s" % (os.path.basename(path), key, at, got))
                        else:
                            place["%s at %s" % (key, got)] += 1
                            place["reproduced"] += 1
                            g.put(at[0], at[1], b["invw"], b["invh"], 1)
                else:
                    place["no xy (logger r1)"] += 1
            # the cow portal: game-seed steps over the spot search and the portal object
            gs0 = None
            for t, d in tx.ev:
                if t == "COW0":
                    gs0 = cube.seedpair(d["gs"])
                if t == "COWT" and d["t"] in ("spot", "portal") and gs0 is not None:
                    g1 = cube.seedpair(d["gs"])
                    cow.append((os.path.basename(path), d["t"], rng.steps_between(gs0, g1, 200), d["v"]))
                    gs0 = g1
    affixes.Walk.pick = orig_pick
    for k in sorted(crec):
        R.add("crec " + k.replace(" ", "_"), crec[k])
    if crec["w28=1"] != crec["records"] or crec["ver=game item version"] != crec["records"]:
        R.add("bad")
    R.note("rows reaching the matcher, by op: %s" % dict(ops))
    R.note("exc inputs (rows 131, 132, 135, 136) at the matcher: %s" % dict(excn))
    R.note("forced picks: %d; outside their row's level window: %d" % (len(forced), sum(1 for f in forced if not f["inside"])))
    for f in forced:
        R.note("  forced id %(id)d level %(level)d maxlevel %(maxlevel)d alvl %(alvl)d ilvl %(ilvl)d inside %(inside)s" % f)
    R.note("quality-0 creation records: %s" % dict(q0))
    R.note("creation rolls: %s" % {k: v for k, v in S.items() if k.startswith("creation roll")})
    R.note("ethereal/socket bits: %s" % dict(ethsok))
    R.note("placement: %s" % dict(place))
    R.note("cow portal game-seed steps (log, oracle, steps, value): %s" % cow)
    R.note("model counters: crafted builds %s, ItemInitStats %s, join seeds %s, ItemApplyProps %s, forced picks %s" % (
        S.get("builders run by the affix model: crafted"), S.get("ItemInitStats (created)"), S.get("join seeds predicted"),
        S.get("ItemApplyProps calls predicted (affix model -> APE)"),
        sum(v for k, v in S.items() if k.startswith("pick forced row"))))
    rn = crafted_rare_names(T)
    R.add("crafted_bases_without_rare_name_side", sum(1 for v in rn.values() if 0 in v))
    R.note("crafted bases %d; rare-name candidates per side, min %s" % (len(rn), min(rn.values()) if rn else None))
    if VERBOSE:
        for k in sorted(S):
            R.note("  %-60s %d" % (k, S[k]))
    return R.done()


# ========================================================================================================== sockets
RUNE_CODES = {"r21": "Pul", "r06": "Ith", "r12": "Sol", "r27": "Ohm", "r33": "Zod"}


def set_sockets_model(q, invw, invh, ms, n, cur):
    """ITEMS_SetSockets (items/0007 section 7) on plain values; returns (count written or 0, the binding term)."""
    cap = min(invw * invh, 6)
    bind = "size" if invw * invh < 6 else "6"
    if cap == 0:
        return 0, "size 0"
    if q == 4 and cap > 4:
        cap, bind = 4, "quality (magic 4)"
    elif q in (5, 7):
        if cur >= 1:
            n = cur
        elif cap:
            cap, bind = 1, "quality (set/unique 1)"
    elif q == 6 and cap > 2:
        cap, bind = 2, "quality (rare 2)"
    elif q in (8, 9) and cap > 3:
        cap, bind = 3, "quality (crafted 3)"
    if ms < cap:
        cap, bind = ms, "ItemMaxSockets"
    r = max(n, 1) if max(n, 1) < cap else cap
    return (r if r >= 1 else 0), (bind if max(n, 1) >= cap else "request")


def cmd_sockets(ns):
    import props
    import sockets
    T = sockets.Tables(EXCEL)
    R = Report("sockets")
    logs = run_logs()["run:2026-10-15-sockets"]
    c = collections.Counter()
    runes = collections.Counter()
    for path in logs:
        classic = "classic" in os.path.basename(path)
        for tag, b in sockets.read_log(path):
            if tag != "INS":
                continue
            ins = b.ins
            ev = dict()
            for t, d in b.ev:
                ev.setdefault(t, []).append(d)
            ch = (ev.get("CH") or [None])[0]
            pa = (ev.get("PA") or [None])[0]
            x = ev["INSX"][-1]
            ok = x.get("r", x.get("ret")) if isinstance(x, dict) else None
            reader = ins["p"] == [0, 0, 0, 0]
            kind = "reader" if reader else "packet" if ins["p"] == [1, 1, 1, 1] else "other"
            c["inserts %s" % kind] += 1
            if ch and reader:
                c["reader: child mode %d at the lookup" % ch["mode"]] += 1
            pa2 = x.get("pa") or x.get("parent")
            if pa and pa2 and "fl" in pa2:
                f0, f1 = pa["fl"], pa2["fl"]
                rw = any(m["row"] >= 0 for m in ev.get("MX", []))
                made = "RWA" in ev and ev.get("RWX") and ev["RWX"][-1].get("r", ev["RWX"][-1].get("eax", 1))
                key = "%s %s%s" % (kind, "runeword" if rw else "no runeword", "" if ok == 1 else " (refused)")
                c["%s: parent bit0 %d->%d" % (key, f0 & 1, f1 & 1)] += 1
                if f0 & 0x4000:
                    c["%s: parent bit14 set before, %d after" % (key, 1 if f1 & 0x4000 else 0)] += 1
            if ch and pa and kind == "packet" and x.get("child") is not None or (ch and "APE" in ev):
                code = T.raw(ch["cls"])[0x80:0x84].decode("latin1").strip()
                if code in RUNE_CODES:
                    runes[RUNE_CODES[code]] += 1
                gemrow = T.gem_of.get(ch["cls"])
                if gemrow is not None and "APE" in ev:
                    grp = T.gemapplytype(pa["cls"])
                    bl = props.blocks(T.gems[gemrow], 0x30 + 0x30 * grp, 3)
                    k = next((i for i, y in enumerate(bl) if y[0] < 0), 3)
                    nm = T.gems[gemrow][0x2E]
                    c["gem/rune transfers"] += 1
                    c["transfers where nummods != blocks before the first blank"] += int(nm != k)
                    # GEMS_Load writes each gems row's index into +0x0F0 of the item it names; no gems row names a
                    # socketable parent base, so the parent's +0x0F0 is 0 and only row 0 would read the same
                    c["transfers whose gems row is not 0 (the parent's +0x0F0)"] += int(gemrow != 0)
                    c["transfers whose parent base is named by a gems row"] += int(pa["cls"] in T.gem_of)
            if classic and ch and "APE" in ev and T.is_type(ch["cls"], sockets.RUNE):
                c["classic rune transfers"] += 1
            if pa2 and pa2.get("fl", 0) & 0x4000000 and ok == 1:
                c["runeword parent at INSX: ItemData+0x38 = %d" % pa2.get("rw", -1)] += 1
            for m in ev.get("MX", []):
                if m["row"] >= 0:
                    r = T.rune(m["row"])
                    if r["server"]:
                        c["match returned a server row (%s)" % r["ename"]] += 1
    for k in sorted(c):
        R.add(re.sub(r"\W+", "_", k).strip("_"), c[k])
    R.note("rune inserts with a transfer (Pul, Ith, Sol, Ohm, Zod): %s" % dict(runes))
    # SetSockets calls: props stock drops (SSET), cube (CSOCK), quest Larzuk (LZX/LZY)
    import tc_sweep
    P = props.Tables(EXCEL)
    calls = collections.Counter()
    vals = collections.Counter()
    sp = [p for run, p, *_ in tc_sweep.stock_logs(check=False)]
    sp += [os.path.join(LOGS, "vendors-s1-3207-hellprops.log")]
    for path in sp:
        ic = sok = sset = None
        for t, d in events(path, ("IC0", "SOK0", "SSET", "LX")):
            if t == "IC0":
                ic, sok, sset = d, None, None
            elif t == "SOK0":
                sok = d
            elif t == "SSET":
                sset = d
            elif t == "LX" and ic and sok and sset:
                b = P.base(ic["cls"])
                ms = P.max_sockets(ic["cls"], ic["ilvl"])
                want, bind = set_sockets_model(sok["q"], b["invw"], b["invh"], ms, sset["n"], 0)
                got = next((e[2] for e in d["b"] if e[0] == 194), 0)
                where = "vendor" if "vendors" in path else "drop"
                calls[where] += 1
                vals["%s q%d n %d -> %d (%s)" % (where, sok["q"], sset["n"], got, bind)] += 1
                if want != got:
                    R.add("bad")
                    R.note("SetSockets drop %s: model %d, log %d" % (os.path.basename(path), want, got))
                ic = None
    for path in run_logs()["run:2026-10-15-cube"]:
        last = None
        for t, d in events(path, ("CSOCK", "CPL")):
            if t == "CSOCK":
                last = d
            elif t == "CPL" and last:
                it = last["it"]
                b = P.base(it["cls"])
                ms = P.max_sockets(it["cls"], it["ilvl"])
                want, bind = set_sockets_model(it["q"], b["invw"], b["invh"], ms, last["n"], 0)
                got = next((e[2] for e in d["it"]["b"] if e[0] == 194), 0)
                calls["cube"] += 1
                vals["cube q%d n %d -> %d (%s)" % (it["q"], last["n"], got, bind)] += 1
                if want != got:
                    R.add("bad")
                last = None
    for path in run_logs()["run:2026-10-16-quest-drops"]:
        lz = lzx = None
        for t, d in events(path, ("LZ0", "LZX", "LZY")):
            if t == "LZ0":
                lz = d
            elif t == "LZX":
                lzx = d
            elif t == "LZY" and lz and lzx:
                calls["quest"] += 1
                vals["quest q%d max %d n %d -> %s" % (lz["q"], lz["max"], lzx["n"], d["sockets"])] += 1
                lz = lzx = None
    R.note("ITEMS_SetSockets calls checked: %s" % dict(calls))
    for k in sorted(vals):
        R.note("  %s: %d" % (k, vals[k]))
    R.add("setsockets_calls", sum(calls.values()))
    return R.done()


# ========================================================================================================== vendors
def cmd_vendors(ns):
    import vendors
    R = Report("vendors")
    logs = run_logs()["run:2026-10-15-vendors"]
    c = collections.Counter()
    slots = {s["cls"]: s for s in slot_table()}
    order_ok = order_bad = 0
    for path in logs:
        cf = None
        known = []          # (log index, tick) of GetTickCount values the log shows: stale marks
        builds = []         # (log index, class)
        seen = {}           # class -> buildTick read after its last build
        idx = 0
        for t, d in events(path):
            idx += 1
            if t == "CF0":
                cf = d
            elif t == "IC0" and cf is not None:
                c["store creations (IC0 after CF0)"] += 1
                c["record +0x80 = 2"] += d["rfl"] == 2
                c["record row 0, restore 0"] += d["rrow"] == 0 and d["rest"] == 0
                c["record quality = argument"] += d["rq"] == cf["q"]
                c["record ilvl = max(1, argument)"] += d["ilvl"] == max(1, cf["ilvl"])
                c["record item version = game"] += d["ver"] == d["gver"]
            elif t == "CFX" and cf is not None:
                stock = cf["ret"] == 0x005764DB
                c["CFX %s" % ("stock" if stock else "gamble")] += 1
                c["CFX %s identified (0x10)" % ("stock" if stock else "gamble")] += bool(d["fl"] & 0x10)
                if stock:
                    c["stock quality %d" % d["q"]] += 1
                cf = None
            elif t in ("CRK", "CMM"):
                c["retry %s" % t] += 1
            elif t == "TO":
                s = slots.get(d["cls"])
                c["TO lines"] += 1
                if s and s["act"] == d["act"] and s["store"] == d["store"]:
                    c["TO record act/store = slot table"] += 1
                c["TO gambler = spec set"] += int(bool(d["gambler"]) == (d["cls"] in SPEC_GAMBLE))
                if d["built"] and d["cls"] in seen and seen[d["cls"]] is None:
                    seen[d["cls"]] = d["tick"]
                    builds[-1 if builds and builds[-1][1] == d["cls"] else -1]
                    for i_, (bi, bc, _) in enumerate(builds):
                        if bc == d["cls"] and builds[i_][2] is None:
                            builds[i_] = (bi, bc, d["tick"])
            elif t == "STALE":
                cl = [r[0] for r in d["recs"]]
                c["STALE record lists in ascending class order (the record array order)"] += cl == sorted(cl)
                c["STALE record lists"] += 1
                for r in d["recs"]:
                    if r[0] in seen and seen[r[0]] is None and r[2]:
                        for i_, (bi, bc, tk) in enumerate(builds):
                            if bc == r[0] and tk is None:
                                builds[i_] = (bi, bc, r[4])
                        seen[r[0]] = r[4]
            elif t == "STALEX":
                for r in d["recs"]:
                    if r[3] == 1:
                        known.append((idx, r[4]))
            elif t == "BS0":
                builds.append((idx, d["cls"], None))
                seen[d["cls"]] = None
            elif t == "RESET":
                pass
        # order: a build's tick lies between the known ticks before and after it in the log
        ticks = sorted([(i, tk, "mark") for i, tk in known] + [(i, tk, "build") for i, _, tk in builds if tk is not None])
        for k, (i, tk, what) in enumerate(ticks):
            if what != "build":
                continue
            before = [x[1] for x in ticks[:k] if x[2] == "mark"]
            after = [x[1] for x in ticks[k + 1:] if x[2] == "mark"]
            ok = (not before or tk >= max(before)) and (not after or tk <= min(after))
            prev_b = [x[1] for x in ticks[:k] if x[2] == "build"]
            ok = ok and (not prev_b or tk >= max(prev_b))
            order_ok += ok
            order_bad += not ok
        c["builds with a read buildTick"] += sum(1 for b in builds if b[2] is not None)
        c["builds"] += len(builds)
        c["stale-mark ticks"] += len(known)
    for k in sorted(c):
        R.add(re.sub(r"\W+", "_", k).strip("_"), c[k])
    R.add("buildtick_order_ok", order_ok)
    R.add("buildtick_order_bad", order_bad)
    if order_bad:
        R.add("bad")
    if c["stock quality 1"]:
        R.add("bad")
    return R.done()


# =========================================================================================================== quests
def tcr_ilvl(path):
    """{monster class: [ilvl]} from the TCR lines (key=value) of a log."""
    out = collections.defaultdict(list)
    with open(path, errors="replace") as f:
        for ln in f:
            if ln.startswith("TCR "):
                kv = dict(x.split("=", 1) for x in ln.split()[1:] if "=" in x)
                if kv.get("stype") == "1":
                    out[int(kv["sclass"])].append(int(kv["ilvl"]))
    return out


def cmd_quests(ns):
    R = Report("quests")
    sets = run_logs()
    logs = sets["run:2026-10-16-quest-drops"] + sets["run:2026-10-16-quest-drops (owner-played addendum)"]
    c = collections.Counter()
    H, lv = txt("levels")
    lvl107 = lv[107]
    forge_ilvl = [int(lvl107[H["MonLvl1Ex"]]), int(lvl107[H["MonLvl2Ex"]]), int(lvl107[H["MonLvl3Ex"]])]
    for path in logs:
        tcr = tcr_ilvl(path)
        b6p = None
        qdi = None
        grec = None
        ma = None
        for t, d in events(path):
            if t == "QI1":
                grec = d["grec"]
            elif t == "B6P":
                b6p = d
            elif t == "B6G" and b6p is not None:
                want = (b6p["word"] >> d["k"]) & 1 if d["k"] in (15, 1) else None
                if d["k"] in (15, 1):
                    c["GetState checked against the logged word"] += 1
                    c["GetState = bit s of word q"] += int(want == d["r"])
                else:
                    c["GetState (TCQuestCP) results"] += 1
            elif t in ("QS", "QC"):
                c["bit writes"] += 1
                if d["b"] == 15:
                    c["bit-15 %s on %s" % ("sets" if t == "QS" else "clears", "the game record" if d["rec"] == grec else
                                            "a player record")] += 1
                if d["w"] == 22 and t == "QS" and d["rec"] != grec and "meph" in path:
                    c["Mephisto session: player word 22 set bit %d (ret %s)" % (d["b"], d["ret"])] += 1
                if d["w"] == 10 and t == "QS" and d["rec"] != grec and d["b"] in (0, 13):
                    c["player word 10 set bit %d (ret %s)" % (d["b"], d["ret"])] += 1
            elif t == "QDI":
                qdi = d
            elif t == "QDX" and qdi is not None:
                src, il = qdi["src"], d["item"]["ilvl"]
                if src[0] == 1:
                    lv_ = tcr.get(src[1], [])
                    ok = il in lv_
                    c["monster source: ilvl = its TC drop's ilvl" if ok else "monster source: no TC ilvl match"] += 1
                elif src[0] == 2:
                    ok = il == forge_ilvl[qdi["diff"]]
                    c["object source (forge, level 107): ilvl = MonLvl%dEx" % (qdi["diff"] + 1) if ok else
                      "object source: ilvl differs"] += 1
                if qdi["code"].strip() == "mss":
                    c["mss created (ret %s, q %d)" % (qdi["ret"], qdi["q"])] += 1
                qdi = None
            elif t == "MA":
                c["MA lines"] += 1
                ma = d
            elif t == "IMB0":
                c["imbues"] += 1
                c["imbues whose item is the action's argument"] += int(ma is not None and ma["arg"] == d["item"]["u"][2])
    for k in sorted(c):
        R.add(re.sub(r"\W+", "_", k).strip("_"), c[k])
    if c["GetState = bit s of word q"] != c["GetState checked against the logged word"]:
        R.add("bad")
    R.note("forge ilvl by difficulty (Levels row 107 MonLvl1..3Ex): %s" % forge_ilvl)
    return R.done()


# ============================================================================================================ props
def cmd_props(ns):
    """The creation record's skip and forced bits at the ethereal and socket rolls: the stock drop logs of tools/tc_sweep.py
    and the run:2026-10-16-player logs (start items, flags 0x0A)."""
    import tc_sweep
    R = Report("props")
    c = collections.Counter()
    paths = [("drops", p) for run, p, *_ in tc_sweep.stock_logs(check=True)]
    lst = os.path.join(ROOT, "workspace", "scratch-h34p2", "player-run.lst")
    man = {ln.split()[1]: ln.split()[0] for ln in open(os.path.join(ROOT, "workspace", "scratch-h34p2",
                                                                    "player-run-manifest.txt")) if ln.strip()}
    for ln in open(lst):
        if ln.strip():
            p_ = os.path.join(ROOT, ln.strip())
            if sha256(p_) != man.get(ln.strip()):
                raise SystemExit("%s: sha256 differs from player-run-manifest.txt" % ln.strip())
            paths.append(("player", p_))
    c["drop logs"] = sum(1 for k, _ in paths if k == "drops")
    c["player logs (sha256 checked against player-run-manifest.txt)"] = sum(1 for k, _ in paths if k == "player")
    for kind, path in paths:
        rfl = None
        sok = None
        for t, d in events(path, ("ETH0", "ETHR", "SOK0", "SOKR", "SSET", "IC0", "LX")):
            if t == "IC0":
                sok = None
            if t in ("ETH0", "SOK0") and "rfl" not in d:
                rfl = sok = None
                continue
            if t == "ETH0":
                rfl = d["rfl"]
                c["%s ETH0" % kind] += 1
                c["%s ETH0 rfl&0x14 (forced bits)" % kind] += bool(rfl & 0x14)
                c["%s ETH0 rfl&2" % kind] += bool(rfl & 2)
            elif t == "ETHR" and rfl is not None and rfl & 2:
                R.add("bad")
            elif t == "SOK0":
                sok = d
                c["%s SOK0" % kind] += 1
                c["%s SOK0 rfl&0x14" % kind] += bool(d["rfl"] & 0x14)
            elif t == "SOKR" and sok:
                if sok["rfl"] & 8:
                    c["%s SOKR with rfl&8 (draw before the skip)" % kind] += 1
                    c["%s SOKR with rfl&8 and r < 33" % kind] += d["r"] < 33
            elif t == "SSET" and sok and sok["rfl"] & 8:
                R.add("bad")
    for k in sorted(c):
        R.add(re.sub(r"\W+", "_", k).strip("_"), c[k])
    return R.done()


# ============================================================================================================ main
def main(argv):
    global VERBOSE
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("logs")
    p.add_argument("--write")
    p.set_defaults(fn=cmd_logs)
    p = sub.add_parser("static")
    p.add_argument("only", nargs="*")
    p.add_argument("-v", action="store_true")
    p.set_defaults(fn=cmd_static)
    p = sub.add_parser("tables")
    p.set_defaults(fn=cmd_tables)
    for nm, fn in (("cube", cmd_cube), ("sockets", cmd_sockets), ("vendors", cmd_vendors), ("quests", cmd_quests),
                   ("props", cmd_props)):
        p = sub.add_parser(nm)
        p.add_argument("-v", action="store_true")
        p.set_defaults(fn=fn)
    p = sub.add_parser("all")
    p.set_defaults(fn=cmd_all)
    ns = ap.parse_args(argv)
    VERBOSE = getattr(ns, "v", False)
    return ns.fn(ns)


def cmd_all(ns):
    rc = 0
    for fn in (cmd_static, cmd_tables, cmd_cube, cmd_sockets, cmd_vendors, cmd_quests, cmd_props):
        rc |= fn(argparse.Namespace(only=[], v=False, write=None))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
