"""Plan 0066 batches S4a (items/economy) and S4b (items/use): new checks over kept logs, static second sources and
full-table checks. No game run, no Ghidra.

Usage:
  python3 -I tools/sweep2_s4ab.py <section> [<section> ...]      # print the sections' lines
  python3 -I tools/sweep2_s4ab.py all                             # every section, in order

Sections (the inventory row each serves is in its docstring):
  static   r2 and the raw-byte scan (tools/xrefscan.py) as the second tool next to economy_scan.py (objdump) and Ghidra;
           objdump (tools/sweep_s4b.py's walker) as the second tool next to Ghidra for the use entries
  tables   full-table checks over the .bin tables (and the .txt where a column is not decoded in the .bin)
  econ     the economy and economy2 claim logs (run:2026-10-17-economy, run:2026-10-19-economy2)
  price    the price controls over the same claim logs (tools/economy.py's model with one quality branch changed)
  use      the kept logs of run:2026-11-04-inventory-2 (pot, drops2, crowd)

Each section prints `S4 <section> <check> key=value ...` lines and detail lines; `bad=` counts an observation that
contradicts the statement the check tests. A statement with no stock case shows as a zero count, never as a failure.
The record is the "plan 0066 batches S4a and S4b" addendum of findings/items/experiments.md.

Stdlib only, plus objdump and r2 (radare2). Read-only.
"""
import collections
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as S  # noqa: E402

ROOT = S.ROOT
EXE = S.EXE
EXCEL = S.EXCEL
LOGS = S.LOGS
LCG_MUL = S.LCG_MUL


# ------------------------------------------------------------------------------------------------------------ helpers
class Rep:
    def __init__(self, sec, name):
        self.sec, self.name = sec, name
        self.c = collections.Counter()
        self.notes = []

    def add(self, k, n=1):
        self.c[k] += n

    def note(self, s):
        self.notes.append(s)

    def done(self):
        if "bad" not in self.c:
            self.c["bad"] += 0
        print("S4 %s %s %s" % (self.sec, self.name, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
        for s in self.notes:
            print("  " + s)
        return self.c["bad"]


_FUNCS = None


def funcs():
    """Sorted (address, name) of re/symbols.csv's func rows."""
    global _FUNCS
    if _FUNCS is None:
        out = []
        for ln in open(os.path.join(ROOT, "re", "symbols.csv")):
            f = ln.rstrip("\n").split(",")
            if len(f) > 2 and f[1] == "func":
                try:
                    out.append((int(f[0], 16), f[2], f[5] if len(f) > 5 else ""))
                except ValueError:
                    pass
        _FUNCS = sorted(out)
    return _FUNCS


def owner(va):
    """The nearest func symbol at or below va (name, entry)."""
    import bisect
    F = funcs()
    i = bisect.bisect_right([a for a, _, _ in F], va) - 1
    return (F[i][1], F[i][0], F[i][2]) if i >= 0 else ("?", 0, "")


def pad_entry(va):
    """The nearest address at or below va that follows int3 padding (0xCC) and is not itself 0xCC: the start of the
    padded block, an entry guess independent of re/symbols.csv."""
    data = open(EXE, "rb").read() if not hasattr(pad_entry, "d") else pad_entry.d
    pad_entry.d = data
    a = va
    while a > 0x401000:
        o = S.va_off(a)
        if data[o - 1] == 0xCC and data[o] != 0xCC:
            return a
        a -= 1
    return None


def raw(target):
    """(rel32 call/jmp/jcc sites, abs32 sites) of target from the raw bytes (tools/xrefscan.py)."""
    import xrefscan
    data = open(EXE, "rb").read()
    base, secs = xrefscan.sections(EXE)
    hits = xrefscan.scan(data, base, secs, target)
    rel = sorted(va for kind, va, _ in hits if not kind.startswith("abs"))
    ab = sorted(va for kind, va, _ in hits if kind.startswith("abs"))
    return rel, ab


R2_CACHE = {}


def r2(cmd):
    if cmd not in R2_CACHE:
        R2_CACHE[cmd] = subprocess.run(["r2", "-q", "-e", "scr.color=0", "-e", "asm.bytes=false", "-e", "asm.lines=false",
                                        "-e", "asm.comments=false", "-e", "asm.xrefs=false", "-c", cmd, EXE],
                                       capture_output=True, text=True).stdout
    return R2_CACHE[cmd]


R2_LINE = re.compile(r"^\s*0x([0-9a-f]{8})\s+(\S+)\s*(.*?)\s*$")


def r2_range(lo, hi):
    """[(va, mnemonic, operands)] from r2's linear disassembly of [lo, hi)."""
    out = []
    for ln in r2("pD %d @ 0x%x" % (hi - lo, lo)).splitlines():
        m = R2_LINE.match(ln)
        if m:
            out.append((int(m.group(1), 16), m.group(2), m.group(3)))
    return out


def imms(ops):
    return [int(h, 16) for h in re.findall(r"0x([0-9a-f]+)", ops)] + [int(d) for d in re.findall(r"(?<![x0-9a-f])\b(\d+)\b", ops)]


def body(entry):
    A = S.asm()
    return S.body(A, entry)


def read_events(path):
    out = []
    with open(path, errors="replace") as fh:
        for ln, line in enumerate(fh, 1):
            m = re.match(r"^([A-Z0-9]{2,5}) (\{.*)$", line)
            if not m:
                continue
            try:
                out.append((m.group(1), json.loads(m.group(2)), ln))
            except ValueError:
                pass
    return out


def claim_logs():
    out = []
    for lst in ("economy/claim-logs.txt", "economy2/claim-logs.txt"):
        out += open(os.path.join(LOGS, lst)).read().split()
    return [os.path.join(ROOT, p) for p in out]


def seedpair(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def steps(a, b):
    import rng
    if a == b:
        return 0
    return rng.steps_between(seedpair(a), seedpair(b), 2000)


# ------------------------------------------------------------------------------------------------------------- static
def st_npc():
    """economy row 2 (line 63): the NPC class tests of NpcRepair, MERC_Resurrect and NPC_CainIdentify, read by r2."""
    r = Rep("static", "npc-classes")
    want = {"repair": {154, 178, 253, 257, 511}, "resurrect": {150, 198, 252, 367, 515}, "cain": {244, 245, 246, 265, 520}}
    # NpcRepair: a cmp/je chain on [ebx+4] at 0x005780AE..; MERC_Resurrect: cmp/sub chain 0x00579C31..0x00579C55;
    # NPC_CainIdentify: the ranges 0x00578495..0x005784C1.
    got = {}
    ins = r2_range(0x005780AE, 0x005780EF)
    got["repair"] = {v for va, mn, ops in ins if mn == "cmp" for v in imms(ops.split(",")[1])}
    r.note("NpcRepair 0x005780AE..0x005780EF: " + "; ".join("%x %s %s" % i for i in ins))
    ins = r2_range(0x00579C31, 0x00579C57)
    acc, s = None, set()
    for va, mn, ops in ins:      # eax compared, or reduced by sub: track the running value
        if mn == "mov" and "dword [eax + 4]" in ops:
            acc = 0
        elif mn == "cmp":           # a cmp compares the loaded value itself
            s.add(imms(ops.split(",")[1])[0])
        elif mn == "sub":
            acc += imms(ops.split(",")[1])[0]
            s.add(acc)
    got["resurrect"] = s
    r.note("MERC_Resurrect 0x00579C31..0x00579C57: " + "; ".join("%x %s %s" % i for i in ins))
    ins = r2_range(0x00578495, 0x005784C7)
    cm = [imms(ops.split(",")[1])[0] for va, mn, ops in ins if mn == "cmp"]
    # cmp 0x109 / ja / je ; cmp 0xf4 / jb ; cmp 0xf6 / jbe -> 244..246 ; cmp 0x208 / jne
    got["cain"] = {cm[0]} | set(range(cm[1], cm[2] + 1)) | {cm[3]}
    r.note("NPC_CainIdentify 0x00578495..0x005784C7: " + "; ".join("%x %s %s" % i for i in ins))
    ms = S.tsv("monstats")
    for k in want:
        if got[k] != want[k]:
            r.add("bad")
        r.note("%s: r2 %s, spec %s; MonStats Id %s" % (k, sorted(got[k]), sorted(want[k]),
                                                    ", ".join("%d %s" % (c, ms[c]["Id"]) for c in sorted(got[k]))))
        r.add(k + " classes", len(got[k]))
    return r.done()


def st_sites(name, targets, want=None):
    r = Rep("static", name)
    for t, label in targets:
        rel, ab = raw(t)
        r.add("%s rel" % label, len(rel))
        r.add("%s abs" % label, len(ab))
        r.note("%s 0x%08X: rel32 %d: %s; abs32 %d: %s" % (label, t, len(rel), " ".join(
            "0x%08X(%s)" % (v, owner(v)[0]) for v in rel), len(ab), " ".join("0x%08X(%s)" % (v, owner(v)[0]) for v in ab)))
        if want is not None and label in want and want[label] != (len(rel), len(ab)):
            r.add("bad")
            r.note("  expected rel, abs %r" % (want[label],))
    return r.done()


def st_client():
    """economy row 3 (line 71): the client's call sites of the price wrapper and RepairCost."""
    r = Rep("static", "client-sites")
    for t, label, n in ((0x0062FDC0, "ItemTradePrice", 6), (0x0062FE60, "RepairCost", 2)):
        rel, ab = raw(t)
        cl = [v for v in rel if v < 0x00500000]
        r.add(label + " sites", len(rel))
        r.add(label + " client sites", len(cl))
        r.add(label + " abs", len(ab))
        r.note("%s: %s" % (label, " ".join("0x%08X(%s)" % (v, owner(v)[0]) for v in rel)))
        if len(cl) != n or ab:
            r.add("bad")
    return r.done()


def st_goldcap():
    """economy rows 6, 49 (lines 134, 564): PLAYER_GoldCap's body and PlayerGiveGold's three branches, by r2."""
    r = Rep("static", "goldcap")
    ins = r2_range(0x00622E70, 0x00622E8A)
    r.note("PLAYER_GoldCap: " + "; ".join("%x %s %s" % i for i in ins))
    ok = any(mn == "imul" and 0x2710 in imms(ops) for _, mn, ops in ins) and any(
        mn == "push" and ops == "0xc" for _, mn, ops in ins)
    r.add("stat 12 x 10000", int(ok))
    ins = r2_range(0x0055B060, 0x0055B100)
    r.note("PlayerGiveGold: " + "; ".join("%x %s %s" % i for i in ins))
    for va in (0x0055B085, 0x0055B087, 0x0055B0B3, 0x0055B0B7):
        r.note("  %x %s" % (va, [x for x in ins if x[0] == va]))
    if not ok:
        r.add("bad")
    return r.done()


def st_drain():
    """use rows 9, 13, 64 (lines 115, 137, 534) and 17, 59 (152, 504): the drain and the gate, by objdump."""
    r = Rep("static", "drain")
    A = S.asm()
    for va in (0x0053F459, 0x0053F45E, 0x0053F460, 0x0052D03E, 0x0052D043, 0x0052D020, 0x0052D02C, 0x0052D031,
               0x0052D034, 0x0054D7A8, 0x0054D7AA, 0x0054D7AC, 0x0054D7B0, 0x0054D818, 0x0054D81A, 0x0057EEFB, 0x0057EEFF):
        r.note("%x %s %s" % (va, *A.at(va)))
    # the dispatch's return: is EAX read between 0x0053F45E and the next write of EAX in SrvProcessClientMessage?
    v, read = 0x0053F45E, False
    while v < 0x0053F46C:
        mn, ops = A.at(v)
        if "eax" in ops and not ops.startswith("eax"):
            read = True
        if mn == "call":
            break
        v = A.next_va(v)
    r.add("eax read after the dispatch before the next call", int(read))
    v, read2 = 0x0052D043, False
    mn, ops = A.at(v)
    r.add("SrvProcessClientMessage's caller jumps back to the pop", int(mn == "jmp" and S.branch_target(ops) == 0x0052D020))
    for t, label in ((0x0054D750, "SrvPacketDispatch"), (0x0053F3D0, "SrvProcessClientMessage")):
        rel, ab = raw(t)
        r.add(label + " rel", len(rel))
        r.add(label + " abs", len(ab))
        r.note("%s callers: %s; abs %s" % (label, " ".join("0x%08X" % x for x in rel), " ".join("0x%08X" % x for x in ab)))
    # the gate's call: pushes 0, 0, 1 (arg 3, 2, 1), then ECX game, EDX the player
    pushes = [A.at(va)[1] for va in (0x0054D7A8, 0x0054D7AA, 0x0054D7AC)]
    r.add("gate pushes 0,0,1", int(pushes == ["0x0", "0x0", "0x1"]))
    mn, ops = A.at(0x0057EEFB)
    mn2, ops2 = A.at(0x0057EEFF)
    r.add("gate tests arg 2 then jumps past the draw", int(ops == "DWORD PTR [ebp+0xc],0x0" and mn2 == "je"
                                                          and S.branch_target(ops2) == 0x0057EFF2))
    # every RNG site of PlayerModeAllowed lies before the arg-2 jump's target? list them
    vas, calls, ic = body(0x0057EEC0)
    lcg, rc = S.rng_sites(A, vas)
    r.note("PlayerModeAllowed body: %d instructions, rng calls %s, lcg %s, indirect %d" % (
        len(vas), ["%x %s" % x for x in rc], ["%x" % x for x in lcg], len(ic)))
    # from 0x0057EFF2 (the jump target), is any rng site reachable within the body?
    seen, work = set(), [0x0057EFF2]
    while work:
        va = work.pop()
        while va is not None and va not in seen and va in vas:
            seen.add(va)
            mn, ops = A.at(va)
            t = S.branch_target(ops) if (mn.startswith("j") or mn == "call") else None
            if mn in ("ret",):
                break
            if mn == "jmp":
                if t is not None:
                    work.append(t)
                break
            if mn.startswith("j") and t is not None:
                work.append(t)
            va = A.next_va(va)
    r.add("rng sites reachable from 0x0057EFF2", sum(1 for x, _ in rc if x in seen) + sum(1 for x in lcg if x in seen))
    r.add("instructions from 0x0057EFF2", len(seen))
    if read or r.c["SrvPacketDispatch rel"] != 1 or r.c["SrvProcessClientMessage rel"] != 1 or r.c["SrvPacketDispatch abs"] \
            or r.c["SrvProcessClientMessage abs"] or not r.c["gate pushes 0,0,1"] or r.c["rng sites reachable from 0x0057EFF2"]:
        r.add("bad")
    return r.done()


def st_dispatch_table():
    """use row 11 (line 129): the logger's handler addresses are g_SrvPacketTable's rows (0x006E0D18 + 8·op)."""
    r = Rep("static", "packet-table")
    import importlib.util
    src = open(os.path.join(ROOT, "tools", "gdb", "inventory.py")).read()
    m = re.search(r"ITEM_OPS = (\{.*?\})", src, re.S)
    ops = eval(m.group(1), {})
    for op, a in sorted(ops.items()):
        t = S.dword(0x006E0D18 + 8 * op)
        r.add("rows")
        if t != a:
            r.add("bad")
            r.note("op 0x%02X logger 0x%08X table 0x%08X" % (op, a, t))
    return r.done()


def st_calls(name, pairs):
    """caller -> callee claims, by objdump's recursive descent of the caller (the second tool next to Ghidra)."""
    r = Rep("static", name)
    for caller, callee, label in pairs:
        vas, calls, ic = body(caller)
        sites = [s for s, t in calls if t == callee]
        r.add(label, len(sites))
        r.note("%s: 0x%08X calls 0x%08X at %s (%d direct calls, %d indirect)" % (
            label, caller, callee, " ".join("0x%08X" % s for s in sites), len(calls), len(ic)))
        if not sites:
            r.add("bad")
    return r.done()


def st_reach(name, root, target, depth=8):
    """the shortest direct-call path from root to target (objdump walk)."""
    r = Rep("static", name)
    G = S.graph([root])
    if target in G:
        path, e = [], target
        while e is not None:
            path.append(e)
            e = G[e][1]
        r.add("depth", G[target][0])
        r.note("path " + " -> ".join("0x%08X(%s)" % (x, owner(x)[0]) for x in reversed(path)))
    else:
        r.add("bad")
        r.note("0x%08X not reached from 0x%08X (%d functions)" % (target, root, len(G)))
    r.add("functions walked", len(G))
    return r.done()


def st_draw_reach():
    """economy row 44 (line 523): drawing code under ItemRepairBroken (objdump walk, then r2 for the LCG site)."""
    r = Rep("static", "repairbroken-reach")
    G = S.graph([0x0055F900])
    D = S.rng_functions(G)
    r.add("functions walked", len(G))
    r.add("drawing functions", len(D))
    best = sorted(((G[e][0], e) for e in D))
    for d, e in best[:3]:
        path, x = [], e
        while x is not None:
            path.append(x)
            x = G[x][1]
        r.note("depth %d: %s; sites %s" % (d, " -> ".join("0x%08X(%s)" % (p, owner(p)[0]) for p in reversed(path)),
                                           [("%x" % v) if isinstance(v, int) else "%x %s" % v for v in D[e][0] + D[e][1]]))
    vas, calls, ic = body(0x0055F900)
    lcg, rc = S.rng_sites(S.asm(), vas)
    r.add("own body rng sites", len(lcg) + len(rc))
    r.add("min depth", best[0][0] if best else -1)
    if best:     # the shortest path's edges and its draw, each read again in r2's own listing of the caller
        path, x = [], best[0][1]
        while x is not None:
            path.append(x)
            x = G[x][1]
        path.reverse()
        ok = 0
        for a, b in zip(path, path[1:]):
            hit = [va for va, mn, ops in r2_range(a, a + 0x1400) if mn == "call" and ops == "0x%x" % b]
            ok += bool(hit)
            r.note("r2 edge 0x%08X -> 0x%08X at %s" % (a, b, " ".join("0x%08X" % h for h in hit) or "none"))
        r.add("r2 edges confirmed", ok)
        site = D[best[0][1]][1][0][0] if D[best[0][1]][1] else None
        if site:
            r.note("r2 at the draw: %s" % (r2_range(site, site + 5)[:1],))
        if ok != len(path) - 1:
            r.add("bad")
    if not best:
        r.add("bad")
    return r.done()


def st_repair_scan():
    """economy row 45 (line 535): the sites of the six repair functions by the raw scan, and the quest functions."""
    r = Rep("static", "repair-sites")
    T = [(0x005761C0, "ItemRepairAll"), (0x005762B0, "ItemRepairAllThunk"), (0x0055F900, "ItemRepairBroken"),
         (0x00578050, "NpcRepair"), (0x0062FE60, "RepairCost"), (0x0062E660, "ItemCanRepair")]
    quest = [(a, n) for a, n, sub in funcs() if sub.startswith("quests") or re.search(r"_A[1-5]Q[0-9]", n)]
    qset = {a for a, _ in quest}
    allsites = []
    for t, label in T:
        rel, ab = raw(t)
        allsites += rel + ab
        r.add("sites", len(rel) + len(ab))
        r.note("%s: rel %s; abs %s" % (label, " ".join("0x%08X(%s)" % (v, owner(v)[0]) for v in rel),
                                        " ".join("0x%08X(%s)" % (v, owner(v)[0]) for v in ab)))
    r.add("quest functions", len(quest))
    qs = [v for v in allsites if owner(v)[1] in qset]
    r.add("sites in quest functions", len(qs))
    r.note("in quest functions: " + " ".join("0x%08X(%s)" % (v, owner(v)[0]) for v in qs))
    return r.done()


def st_gametype():
    """economy row 60 (line 677): the stores to game+0x6A and the create message's map, by r2."""
    r = Rep("static", "gametype")
    A = S.asm()
    st, rd = [], []
    for va, (mn, ops) in A.ins.items():
        if re.search(r"BYTE PTR \[e[a-z]{2}\+0x6a\]", ops):
            (st if ops.startswith("BYTE PTR") and mn == "mov" else rd).append(va)
    r.add("byte stores at +0x6a", len(st))
    r.add("byte reads at +0x6a", len(rd))
    r.note("stores: " + " ".join("0x%08X(%s)" % (v, owner(v)[0]) for v in sorted(st)))
    for v in sorted(st):
        ins = r2_range(v, v + 8)
        r.note("r2 at the store 0x%08X: %s" % (v, ins[:1]))
        prev, k = [], v
        for _ in range(4):
            k = max(a for a in A.ins if a < k)
            prev.append("%x %s %s" % (k, *A.ins[k]))
        r.note("  objdump before it: " + "; ".join(reversed(prev)))
    ins = r2_range(0x00477CB9, 0x00477CE3)
    r.note("ClientGameCreateMsg's map: " + "; ".join("%x %s %s" % i for i in ins))
    rel, ab = raw(0x007A0610)
    r.add("g_ClientGameMode abs refs", len(ab))
    r.note("g_ClientGameMode refs: " + " ".join("0x%08X(%s)" % (v, owner(v)[0]) for v in ab))
    return r.done()


def callee_argbytes(t):
    """The stack bytes a callee pops (its `ret N`), from r2's disassembly of its body (all ret forms must agree)."""
    vas, calls, ic = body(t)
    A = S.asm()
    rets = {A.at(v)[1] for v in vas if A.at(v)[0] == "ret"}
    n = {int(x, 16) if x else 0 for x in rets}
    return n.pop() if len(n) == 1 else None


def push_back(site, nth, entry):
    """The operand of the nth push before the call at site, walking back by r2's listing: a join reached only by a
    branch (its fall-through predecessor is a jmp or ret) continues at the branch; a nested call's own pushes are
    skipped by its `ret N`. Returns (operand or '?', trail)."""
    ins = r2_range(max(entry, site - 0x100), site + 1)
    idx = {va: i for i, (va, _, _) in enumerate(ins)}
    targets = collections.defaultdict(list)
    for va, mn, ops in ins:
        if mn.startswith("j"):
            t = re.match(r"0x([0-9a-f]+)$", ops)
            if t:
                targets[int(t.group(1), 16)].append(va)
    cur, n, skip, trail = idx[site], 0, 0, []
    while True:
        va = ins[cur][0]
        if cur > 0 and va in targets and (ins[cur - 1][1] == "jmp" or ins[cur - 1][1].startswith("ret")):
            j = targets[va][0]
            trail.append("join %x <- %x" % (va, j))
            cur = idx[j]
        else:
            cur -= 1
        if cur < 0:
            break
        va, mn, ops = ins[cur]
        if mn == "call":
            t = re.match(r"0x([0-9a-f]+)$", ops)
            nb = callee_argbytes(int(t.group(1), 16)) if t else None
            if nb is None:
                return "?", trail + ["call %s" % ops]
            skip += nb // 4
            trail.append("call %s skips %d" % (ops, nb // 4))
        elif mn == "push":
            if skip:
                skip -= 1
            else:
                n += 1
                if n == nth:
                    return ops, trail
        elif mn.startswith("ret"):
            return "?", trail + ["ret at %x" % va]
    return "?", trail + ["window start"]


def st_ammo():
    """economy row 75 (line 806): useAmmo, the 8th stack argument (pushed first), at each call of the line and lob
    creators, read by r2 (push_back)."""
    r = Rep("static", "useammo")
    out = collections.Counter()
    for t, label in ((0x0056ECB0, "line"), (0x0056EE90, "lob")):
        rel, ab = raw(t)
        r.add(label + " abs", len(ab))
        for site in rel:
            name, entry, _ = owner(site)
            val, trail = push_back(site, 8, entry)
            out[val] += 1
            r.add("sites")
            r.note("%s 0x%08X in %s (padded block from 0x%08X): useAmmo %s%s" % (
                label, site, name, pad_entry(site), val, (" (" + "; ".join(trail) + ")") if trail else ""))
    for k, v in sorted(out.items()):
        r.add("useAmmo %s" % k, v)
    return r.done()


def st_use_bodies():
    """use rows 29-31, 58 (lines 289, 293, 296, 503): draws in the entry's own body for kinds 2, 6, 9 (objdump)."""
    r = Rep("static", "use-kinds")
    A = S.asm()
    for e, label in ((0x005BE290, "kind 2 TownPortal"), (0x005BEF90, "kind 6 Cure"), (0x005BEDA0, "kind 9 TimedState")):
        vas, calls, ic = body(e)
        lcg, rc = S.rng_sites(A, vas)
        r.add(label + " rng", len(lcg) + len(rc))
        r.note("%s: %d instructions, %d direct calls (%s), %d indirect; rng %s lcg %s" % (
            label, len(vas), len(calls), " ".join(sorted({"0x%08X" % t for _, t in calls})), len(ic), rc, lcg))
        if lcg or rc:
            r.add("bad")
    ins, raw_ = S.lcg_scan()
    r.add("lcg operands in .text", len(ins))
    r.add("lcg raw occurrences", len(raw_))
    inside = [v for v in raw_ if 0x005BE290 <= v < 0x005BF240]
    r.add("lcg raw occurrences in 0x005BE290..0x005BF240", len(inside))
    return r.done()


def st_groupclear():
    """use row 41 (line 402): kind 3 and STATE_GroupClear 0x0056C740."""
    r = Rep("static", "kind3-groupclear")
    vas, calls, ic = body(0x005BE3F0)
    r.add("direct calls of GroupClear in kind 3's body", sum(1 for _, t in calls if t == 0x0056C740))
    r.add("indirect calls in kind 3's body", len(ic))
    G = S.graph([0x005BE3F0])
    r.add("functions under kind 3", len(G))
    r.add("GroupClear reached under kind 3", int(0x0056C740 in G))
    rel, ab = raw(0x0056C740)
    r.note("GroupClear callers (raw): " + " ".join("0x%08X(%s)" % (v, owner(v)[0]) for v in rel) + "; abs %d" % len(ab))
    if r.c["direct calls of GroupClear in kind 3's body"]:
        r.add("bad")
    return r.done()


def st_clearmarks():
    """use row 28 (line 282): InvClearUseMarks' direct calls, by the raw scan, attributed to symbols.csv functions."""
    r = Rep("static", "clearmarks")
    rel, ab = raw(0x0055BF50)
    own = collections.Counter(owner(v)[0] for v in rel)
    r.add("rel sites", len(rel))
    r.add("abs", len(ab))
    r.add("functions", len(own))
    r.add("self sites", own.get("sub_0055BF50_InvClearUseMarks", 0))
    for n, k in sorted(own.items()):
        r.note("%s %d: %s" % (n, k, " ".join("0x%08X" % v for v in rel if owner(v)[0] == n)))
    return r.done()


def st_f2():
    """use row 35 (line 357): F2's calls and operands (objdump), the fresh list's path."""
    r = Rep("static", "f2")
    A = S.asm()
    for va in (0x005BE5FE, 0x005BE5FF, 0x005BE602, 0x005BE61A, 0x005BE622, 0x005BE626, 0x005BE62D, 0x005BE634,
               0x005BE639, 0x005BE63B, 0x005BE63F, 0x005BE647, 0x005BE651, 0x005BE655, 0x005BE659, 0x005BE661,
               0x005BE667, 0x005BE66F, 0x005BE673):
        r.note("%x %s %s" % (va, *A.at(va)))
    return r.done()


# ------------------------------------------------------------------------------------------------------------- tables
def tables():
    import economy
    T = economy.Tables(EXCEL)
    bad = 0
    # economy row 24 (line 326): Skills cost mult
    r = Rep("tables", "skills-cost-mult")
    ms = [economy.s32(k, 0x234) for k in T.skills]
    txt = S.tsv("skills")
    tm = [int(x["cost mult"] or 0) for x in txt]
    r.add("rows", len(ms))
    r.add("max", max(ms))
    r.add("min", min(ms))
    r.add("abs above 1023", sum(1 for m in ms if abs(m) > 1023))
    r.add("txt rows agreeing", sum(1 for a, b in zip(ms, tm) if a == b))
    r.add("nonzero", sum(1 for m in ms if m))
    if max(ms) > 896 or min(ms) < -1023 or len(tm) != len(ms):
        r.add("bad")
    bad += r.done()
    # economy row 40 (line 483): own-type Repair against the Equiv closure
    r = Rep("tables", "repair-own-vs-equiv")
    wt = {x["code"]: x for x in S.tsv("weapons") + S.tsv("armor") + S.tsv("misc")}
    for i, b in enumerate(T.items):
        code = b[0x80:0x84].decode("latin-1").strip()
        own = economy.s16(b, 0x11E)
        if own <= 0 or own >= len(T.types):
            r.add("no type")
            continue
        o = T.types[own][8] != 0
        e = any(T.types[t][8] != 0 for t in T.closure(own))
        r.add("bases")
        r.add("own repair %d equiv %d" % (o, e))
        if o != e:
            r.add("bad")
            r.note("differs: %s" % b[0x80:0x84])
        nod = b[0x113] != 0
        if nod != (((wt.get(code) or {}).get("nodurability") or "0").strip() == "1"):
            r.add("nodurability bin/txt differ")
        if o and nod:
            r.add("Repair type and nodurability")
            r.add("Repair type and nodurability, type %s" % T.types[own][0:4].decode("latin-1").strip())
            r.note("Repair+nodurability: %s %s type %s" % (code, (wt.get(code) or {}).get("name"),
                                                         T.types[own][0:4].decode("latin-1").strip()))
    for code in ("bow", "tpot", "xbow"):
        t = T.tcode.get(code)
        r.note("type %s Repair %s" % (code, T.types[t][8] if t is not None else None))
    bad += r.done()
    # use row 53 (line 488): key's row
    r = Rep("tables", "misc-key")
    misc = S.tsv("misc")
    for i, x in enumerate(misc):
        if x["code"] == "key":
            b = T.items[T.by_code[b"key "]]
            r.add("useable txt", int(x["useable"] or 0))
            r.add("useable bin +0x11D", b[0x11D])
            r.note("key: useable %r pSpell %r type %r" % (x["useable"], x.get("pSpell"), x.get("type")))
            if int(x["useable"] or 0) or b[0x11D] or (x.get("pSpell") or "").strip() not in ("", "0"):
                r.add("bad")
    bad += r.done()
    return bad


# --------------------------------------------------------------------------------------------------------------- econ
def econ():
    bad = 0
    logs = claim_logs()
    rg = Rep("econ", "giveold")
    rs = Rep("econ", "giveold-seeds")
    ri = Rep("econ", "repairall")
    rr = Rep("econ", "replenish-arm")
    ro = Rep("econ", "outputs")
    rd = Rep("econ", "wear-site")
    lv_hi = collections.defaultdict(int)
    for path in logs:
        ev = read_events(path)
        name = os.path.basename(path)
        gg = None
        nr = None
        last_rp, touch = {}, {}
        for i, (tag, d, ln) in enumerate(ev):
            if tag == "GG0":
                gg = {"d": d, "ln": ln, "da": []}
            elif tag == "DA0" and gg is not None:
                gg["da"].append([d, None])
            elif tag == "DA1" and gg is not None and gg["da"]:
                gg["da"][-1][1] = d
            elif tag == "GG1" and gg is not None:
                d0, s0, s1 = gg["d"], gg["d"]["sn"], d["sn"]
                n, L, g0, g1 = d0["a"][0], s0["lv"], s0["g"], s1["g"]
                cap = L * 10000
                if g0 == cap:
                    br, add, drop = "at cap (0x0055B089)", 0, n
                elif (g0 + n) & 0xFFFFFFFF > cap:
                    br, add, drop = "over cap (0x0055B0B9)", cap - g0, n - (cap - g0)
                else:
                    br, add, drop = "under cap (0x0055B0EE)", n, None
                rg.add(br)
                rg.add("L %d %s" % (L, br.split(" (")[0]))
                lv_hi[L] = max(lv_hi[L], g1)
                das = [a for a, _ in gg["da"]]
                got_drop = das[0]["amt"] if das else None
                if g1 != g0 + add or got_drop != drop or len(das) > 1:
                    rg.add("bad")
                    rg.note("%s:%d n %d L %d gold %d -> %d, drop %r (model add %d drop %r)" % (
                        name, gg["ln"], n, L, g0, g1, got_drop, add, drop))
                elif das:
                    rg.note("%s:%d n %d L %d gold %d = cap %d: DA %d (ra 0x%08X), gold after %d" % (
                        name, gg["ln"], n, L, g0, cap, got_drop, das[0]["ra"], g1))
                gs = steps(s0["gs"], s1["gs"])
                if gg["da"]:
                    a0, a1 = gg["da"][0]
                    ds = steps(a0["sn"]["gs"], a1["sn"]["gs"]) if a1 else None
                    pre = steps(s0["gs"], a0["sn"]["gs"])
                    post = steps(a1["sn"]["gs"], s1["gs"]) if a1 else None
                    rs.add("GG +%s with a DA of +%s (before %s, after %s)" % (gs, ds, pre, post))
                    if not (gs == ds == 2 and pre == 0 and post == 0):
                        rs.add("bad")
                else:
                    rs.add("GG +%s without a DA" % gs)
                    if gs != 0:
                        rs.add("bad")
                gg = None
            elif tag == "NR0":
                nr = {"d": d, "ir": [], "ln": ln}
            elif tag == "IR0":
                it = d["it"]
                touch[it["u"]] = d["fr"]
                if nr is not None:
                    nr["ir"].append(d)
                ri.add("IR calls")
                ri.add("IR from 0x%08X (%s)" % (d["ra"], owner(d["ra"] - 5)[0]))
            elif tag == "IR1":
                it = d["it"]
                ro.add("IR1 item dumps")
            elif tag == "NR1" and nr is not None:
                b0 = {x["u"]: x for x in nr["d"]["its"]}
                b1 = {x["u"]: x for x in d["its"]}
                ch = {u for u in b0 if u in b1 and (b0[u]["d"], b0[u]["n"], b0[u]["fl"]) != (b1[u]["d"], b1[u]["n"], b1[u]["fl"])}
                irs = {x["it"]["u"] for x in nr["ir"]}
                via = collections.Counter("0x%08X" % x["ra"] for x in nr["ir"])
                kind = "repair-all" if nr["d"]["a"][3] & 0x80000000 else "single"
                if kind == "single":
                    iid = nr["d"]["a"][1]
                    tgt = {x["u"] for x in nr["d"]["its"] if x.get("id") == iid}
                    if not ch <= tgt:
                        ri.add("bad")
                    ri.add("single: changed only the requested item", int(ch <= tgt))
                    ri.add("single with %d IR, %d changed" % (len(nr["ir"]), len(ch)))
                ri.add("NpcRepair %s" % kind)
                ri.add("NpcRepair %s IR calls" % kind, len(nr["ir"]))
                ri.add("NpcRepair %s items changed" % kind, len(ch))
                ri.note("%s:%d NpcRepair a %r: %d IR (%s), %d items changed, changed in IR set %s" % (
                    name, nr["ln"], nr["d"]["a"], len(nr["ir"]), dict(via), len(ch), ch <= irs))
                if kind == "repair-all":
                    if ch != irs or len(irs) != len(nr["ir"]):
                        ri.add("bad")
                    ri.add("repair-all: changed = the IR items, one IR per item", int(ch == irs and len(irs) == len(nr["ir"])))
                nr = None
            elif tag == "RP0":
                it = d["it"]
                u, rr_ = it["u"], it["s252"] or it["s253"]
                if u not in last_rp:
                    if u in touch:
                        gap = d["fr"] - touch[u]
                        want = 2500 // rr_ + 1
                        rr.add("first tick after a store creation's IR, r %d" % rr_)
                        if gap != want:
                            rr.add("bad")
                            rr.note("%s:%d r %d gap %d want %d" % (name, ln, rr_, gap, want))
                    else:
                        rr.add("first tick, no IR before (r %d, frame %d)" % (rr_, d["fr"]))
                last_rp[u] = d["fr"]
            elif tag in ("DL1", "IC1", "RP1"):
                ro.add(tag + " item dumps")
            elif tag == "CD0":
                rd.add("CD from 0x%08X" % d.get("ra", 0))
            elif tag == "DG0":
                rd.add("death game type %s" % d.get("gt"))
    for L in sorted(lv_hi):
        rg.note("L %d: highest gold after a GG %d (cap %d)" % (L, lv_hi[L], L * 10000))
        if lv_hi[L] > L * 10000:
            rg.add("bad")
    for r in (rg, rs, ri, rr, ro, rd):
        bad += r.done()
    # economy row 53 (line 587): the mul= lines of the h2a logs
    r = Rep("econ", "mul")
    h2a = os.path.join(LOGS, "h2a")
    for n in sorted(os.listdir(h2a)):
        if not n.endswith(".log"):
            continue
        prev = None
        for ln, line in enumerate(open(os.path.join(h2a, n), errors="replace"), 1):
            if line.startswith("GMUL "):
                prev = (ln, dict(kv.split("=") for kv in line.split()[1:]))
            elif line.startswith("GMULX ") and prev:
                v = int(line.split("v=")[1])
                g, m = int(prev[1]["gold"]), int(prev[1]["mul"])
                r.add("mul products")
                r.note("%s:%d gold %d mul %d -> %d; (g*m)>>8 %d; g*(m>>8) %d" % (n, prev[0], g, m, v, (g * m) >> 8, g * (m >> 8)))
                if v != (g * m) >> 8:
                    r.add("bad")
                if (g * m) >> 8 != g * (m >> 8):
                    r.add("separating the order")
                prev = None
    bad += r.done()
    return bad


# -------------------------------------------------------------------------------------------------------------- price
CONTROLS = {
    "set-terms": ("            elif qual == 5:\n", "            elif qual == 5:\n                terms = True\n"),
    "unique-terms": ("            elif qual == 7 and 0 <= it.fi < len(T.uniques):\n",
                     "            elif qual == 7 and 0 <= it.fi < len(T.uniques):\n                terms = True\n"),
    "superior-no-terms": ("            elif qual in (3, 9):\n                terms = True\n",
                          "            elif qual in (3, 9):\n                terms = False\n"),
}


def price():
    import types
    import io
    import contextlib
    src0 = open(os.path.join(HERE, "economy.py")).read()
    bad = 0
    logs = claim_logs()
    for name, (old, new) in [("stock", ("", ""))] + sorted(CONTROLS.items()):
        r = Rep("price", name)
        if old:
            if src0.count(old) != 1:
                r.add("bad")
                r.note("pattern not found once")
                bad += r.done()
                continue
            src = src0.replace(old, new)
        else:
            src = src0
        mod = types.ModuleType("economy_" + name.replace("-", "_"))
        mod.__file__ = os.path.join(HERE, "economy.py")
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
        T = mod.Tables(EXCEL)
        ck = mod.Checker(T)
        with contextlib.redirect_stdout(io.StringIO()):
            for p in logs:
                ck.check_log(p)
        pr = [m for m in ck.mis if "price" in m or "mode" in m]
        r.add("mismatch lines", len(ck.mis))
        r.add("price mismatch lines", len(pr))
        r.add("price calls", ck.n.get("events PR", 0))
        q = collections.Counter()
        for m in pr:
            mm = re.search(r"'q': (\d+)|q=(\d+)| q (\d+)", m)
            q[mm.group(1) or mm.group(2) or mm.group(3) if mm else "?"] += 1
        for k, v in sorted(q.items()):
            r.add("quality %s" % k, v)
        for m in pr[:3]:
            r.note(m[:300])
        if name == "stock":
            if ck.mis:
                r.add("bad")
            for k in sorted(ck.n):
                if any(w in k for w in ("ItemRepair", "NpcRepair", "wear", "quantity", "replenish", "restor")):
                    r.note("n %s %d" % (k, ck.n[k]))
            for k in sorted(ck.cases):
                if any(w in k for w in ("ItemRepair", "NpcRepair", "replenish", "durab", "broken")):
                    r.note("case %s %d" % (k, ck.cases[k]))
        if name != "stock" and not pr:
            r.add("control passed")
        bad += r.done()
    return bad


# ---------------------------------------------------------------------------------------------------------------- use
def use():
    bad = 0
    d = os.path.join(LOGS, "inventory")
    names = ["2026-11-04-inventory-2-s2-6001-pot.log", "2026-11-04-inventory-2-s2-6001-drops2.log",
             "2026-11-04-inventory-2-s2-6001-crowd.log"]
    rp = Rep("use", "packets")
    rg = Rep("use", "gate-seeds")
    rf = Rep("use", "fresh-lists")
    for n in names:
        ev = read_events(os.path.join(d, n))
        last_sd = None
        pend = {}
        cur = None
        for tag, x, ln in ev:
            if tag == "PKT":
                op = x["op"]
                rp.add("PKT op 0x%02X" % op)
                if int(x["pkt"][:2], 16) != op:
                    rp.add("bad")
                if x["ret"] != 0x0054D81A:
                    rp.add("bad")
                    rp.note("%s:%d ret 0x%08X" % (n, ln, x["ret"]))
                else:
                    rp.add("ret 0x0054D81A")
                if last_sd is not None:
                    k = "PKR->PKT player seed %s" % ("same" if last_sd == x["sd"] else "changed")
                    rg.add(k)
                    if last_sd == x["sd"]:
                        rg.add("same before op 0x%02X" % op)
                cur = {"op": op, "up": 0, "ln": ln}
            elif tag == "UP0" and cur is not None:
                cur["up"] += 1
            elif tag == "UAL":
                pend = {"a": x["a"], "f": x["f"]}
            elif tag == "USS" and pend:
                rf.add("fresh lists")
                a = pend["a"]
                rf.add("alloc word 2 = 2", int(a[1] == 2))
                rf.add("alloc user type 0", int(a[3] == 0))
                rf.add("rate x (end - frame)", int(x["rate"] * (a[2] - pend["f"]) > 0))
                rf.note("%s:%d UAL %r f %d; USS rate %d" % (n, ln, a, pend["f"], x["rate"]))
                pend = {}
            elif tag == "UQE":
                rf.add("UQE lines")
                rf.add("UQE event 12", int(x["a"][0] == 12))
            elif tag == "PKR" and cur is not None:
                rp.add("op 0x%02X with %d UP0 before its PKR" % (cur["op"], cur["up"]))
                last_sd = x.get("sd")
                cur = None
    for r in (rp, rg, rf):
        bad += r.done()
    return bad


# ----------------------------------------------------------------------------------------------------------- sections
def static():
    bad = 0
    bad += st_npc()
    bad += st_client()
    bad += st_goldcap()
    bad += st_draw_reach()
    bad += st_repair_scan()
    bad += st_sites("gold-drops", [(0x0055A090, "DropGoldAmount"), (0x0055B030, "DropGold")])
    bad += st_gametype()
    bad += st_sites("pets-ondeath", [(0x006637B0, "MERC_ResurrectCost")])
    bad += st_calls("pets-ondeath-call", [(0x005751A0, 0x006637B0, "PETS_OnDeath -> MERC_ResurrectCost")])
    print("  r2 after 0x00575255: " + "; ".join("%x %s %s" % i for i in r2_range(0x0057525A, 0x00575280)))
    bad += st_sites("healdead", [(0x00578ED0, "NpcHealDead"), (0x00622DE0, "HealCost"), (0x00576D90, "PayGold")],
                    want={"NpcHealDead": (0, 0)})
    bad += st_sites("durabilityloss", [(0x0057D3D0, "COMBAT_DurabilityLoss")], want={"COMBAT_DurabilityLoss": (1, 0)})
    bad += st_ammo()
    bad += st_sites("weaponwear", [(0x005DAA40, "SkillWeaponWear")], want={"SkillWeaponWear": (1, 0)})
    bad += st_sites("replenish-timers", [(0x00558530, "ItemReplenishDurTimer"), (0x00558580, "ItemReplenishQtyTimer")])
    # S4b
    bad += st_calls("use-entries", [(0x0054B1E0, 0x0055E170, "Pkt20 -> PlayerUseInvItem"),
                                    (0x0054B560, 0x00562390, "Pkt26 -> PlayerUseBeltItem")])
    bad += st_reach("do113-inv", 0x005BF3D0, 0x0055E170)
    bad += st_reach("do113-belt", 0x005BF3D0, 0x00562390)
    bad += st_drain()
    bad += st_dispatch_table()
    bad += st_clearmarks()
    bad += st_use_bodies()
    bad += st_f2()
    bad += st_groupclear()
    bad += st_sites("keyconsume", [(0x0055F140, "KeyConsume")])
    bad += st_sites("column-getters", [(0x00621ED0, "ItemBeltByte"), (0x006297A0, "ItemDurWarning"),
                                       (0x00629800, "ItemQntWarning"), (0x0063C830, "BeltBoxQuery")],
                    want={"ItemBeltByte": (3, 0), "ItemDurWarning": (0, 0), "ItemQntWarning": (1, 0),
                          "BeltBoxQuery": (1, 0)})
    return bad


SECTIONS = {"static": static, "tables": tables, "econ": econ, "price": price, "use": use}


def main(argv):
    secs = list(SECTIONS) if argv[1:] == ["all"] else argv[1:]
    if not secs or any(s not in SECTIONS for s in secs):
        print(__doc__)
        return 2
    bad = 0
    for s in secs:
        bad += SECTIONS[s]()
    print("S4 total bad=%d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
