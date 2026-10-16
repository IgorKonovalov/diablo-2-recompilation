"""Plan 0038 batch S4b: static second sources for drlg and objects claims (no game run, no slot).

Usage:
  python3 -I tools/sweep_s4b.py <check> [-v]
  python3 -I tools/sweep_s4b.py all

Each check prints one `S4B <check> key=value ...` line of counts plus a few detail lines, and exits 1 when an observation
contradicts the claim it tests (a `bad=` count above 0). A claim with no stock case shows up as a zero count, never as a
failure. The batch record is the "Plan 0038 batch S4b" section of each finding (docs/findings/drlg/*, objects/0001).

The second tool next to Ghidra is GNU objdump (binutils; `objdump -d -M intel` of .text, a linear sweep that knows
nothing of Ghidra's analysis), walked here by recursive descent:
  - a body is every instruction reached from an entry by fall-through and direct jumps (jmp/jcc), plus the targets of
    `jmp [reg*4 + table]` switch tables (entries read from the image while they point at instructions near the jump);
  - `call imm` is an edge to a new body; an indirect call is counted and not followed (as RngCallGraph.java does);
  - the RNG primitives are leaves (their call sites are recorded), and an LCG site is any instruction with the
    multiplier 0x6AC690C5 as an operand;
  - where the linear sweep did not decode an instruction at a branch target (code after data), the window from that
    address is decoded again with `--start-address`.
Unit tests of the pure helpers: python3 -I tools/test_sweep_s4b.py.

Stdlib only, plus the objdump binary. Read-only.
"""
import collections
import functools
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "workspace", "logs")
DATA = os.path.join(ROOT, "workspace", "merged")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
EXCEL = os.path.join(DATA, "data", "global", "excel")

LCG_MUL = 0x6AC690C5
RNG_FNS = {0x0045C370: "RNG_Step", 0x0045C390: "RNG_Range", 0x0045C3E0: "RNG_RangeB", 0x00472210: "RNG_RangePow2",
           0x00472240: "RNG_RangePow2Plus", 0x00650E30: "RNG_SeedInitOne", 0x00650E40: "RNG_SeedInit"}


# ------------------------------------------------------------------------------------------------------------- image
@functools.lru_cache(maxsize=None)
def image():
    """(bytes, image_base, [(va, vsize, raw, rawsize, name, characteristics)])."""
    import pe_info
    p = pe_info.parse(EXE)
    data = open(EXE, "rb").read()
    secs = [(s["va"] + p["image_base"], s["vsize"], s["raw"], s["rsize"], s["name"],
             s["flags"]) for s in p["sections"]]
    return data, p["image_base"], secs


def va_off(va):
    data, base, secs = image()
    for sva, vsz, raw, rsz, name, _ in secs:
        if sva <= va < sva + vsz:
            off = va - sva
            return raw + off if off < rsz else None     # None: inside the section, beyond its file bytes (zero)
    raise ValueError("va 0x%08X not in the image" % va)


def dword(va):
    off = va_off(va)
    if off is None:
        return 0
    return struct.unpack_from("<I", image()[0], off)[0]


def dwords(va, n):
    return [dword(va + 4 * k) for k in range(n)]


def section_of(va):
    for sva, vsz, raw, rsz, name, _ in image()[2]:
        if sva <= va < sva + vsz:
            return name
    return None


# ------------------------------------------------------------------------------------------------------------ objdump
LINE = re.compile(r"^\s*([0-9a-f]+):\t(\S+)(?:\s+(.*))?$")


def parse_listing(text):
    """{va: (mnemonic, operands)} from `objdump -d -M intel --no-show-raw-insn` output."""
    out = {}
    for ln in text.splitlines():
        m = LINE.match(ln)
        if not m:
            continue
        mn, ops = m.group(2), (m.group(3) or "").strip()
        if mn in ("(bad)",):
            continue
        out[int(m.group(1), 16)] = (mn, ops)
    return out


def objdump(start=None, stop=None):
    cmd = ["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "-j", ".text"]
    if start is not None:
        cmd += ["--start-address=0x%x" % start, "--stop-address=0x%x" % stop]
    return subprocess.run(cmd + [EXE], check=True, capture_output=True, text=True).stdout


class Asm:
    """The objdump decoding of .text, with lazy re-decoding at addresses the linear sweep stepped over."""

    def __init__(self):
        self.ins = parse_listing(objdump())
        self.redecoded = 0
        self._sorted = None

    def at(self, va):
        if va not in self.ins:
            text = image()[2][0]
            if not (text[0] <= va < text[0] + text[1]):
                return None
            more = parse_listing(objdump(va, va + 0x400))
            if va not in more:
                return None
            self.redecoded += 1
            self.ins.update(more)
            self._sorted = None
        return self.ins[va]

    def next_va(self, va):
        """The address after the instruction at va (by the next decoded address)."""
        if self._sorted is None:
            self._sorted = sorted(self.ins)
        import bisect
        i = bisect.bisect_right(self._sorted, va)
        return self._sorted[i] if i < len(self._sorted) else None

    def range(self, lo, hi):
        if self._sorted is None:
            self._sorted = sorted(self.ins)
        import bisect
        i = bisect.bisect_left(self._sorted, lo)
        while i < len(self._sorted) and self._sorted[i] < hi:
            yield self._sorted[i], self.ins[self._sorted[i]]
            i += 1


@functools.lru_cache(maxsize=None)
def asm():
    return Asm()


IMM = re.compile(r"0x([0-9a-f]+)")
JTAB = re.compile(r"^DWORD PTR \[(?:e[a-z]{2})\*4\+0x([0-9a-f]+)\]$")
BRANCH_TARGET = re.compile(r"^0x([0-9a-f]+)$")


def has_imm(ops, value):
    return any(int(h, 16) == value for h in IMM.findall(ops))


def branch_target(ops):
    m = BRANCH_TARGET.match(ops.split()[0]) if ops else None
    return int(m.group(1), 16) if m else None


def switch_targets(A, jva, table):
    """Entries of a `jmp [reg*4 + table]`: read while each points at a decoded instruction within 0x4000 of the jump."""
    out = []
    for k in range(512):
        t = dword(table + 4 * k)
        if not (jva - 0x4000 <= t < jva + 0x4000) or A.at(t) is None:
            break
        out.append(t)
    return out


def body(A, entry):
    """Recursive descent of one function. Returns (instruction vas, direct call targets [(site, target)],
    indirect call sites, tail-jump targets that are outside reach of the body's own flow)."""
    seen, calls, icalls = set(), [], []
    work = [entry]
    while work:
        va = work.pop()
        while va is not None and va not in seen:
            ins = A.at(va)
            if ins is None:
                break
            seen.add(va)
            mn, ops = ins
            nxt = A.next_va(va)
            if mn == "call":
                t = branch_target(ops)
                if t is not None:
                    calls.append((va, t))
                else:
                    icalls.append(va)
            elif mn in ("ret", "retn", "iret", "hlt", "int3"):
                break
            elif mn == "jmp":
                t = branch_target(ops)
                if t is not None:
                    work.append(t)
                else:
                    m = JTAB.match(ops)
                    if m:
                        work.extend(switch_targets(A, va, int(m.group(1), 16)))
                    else:
                        icalls.append(va)
                break
            elif mn.startswith("j") or mn.startswith("loop"):
                t = branch_target(ops)
                if t is not None:
                    work.append(t)
            va = nxt
    return seen, calls, icalls


def rng_sites(A, vas):
    """(lcg sites, rng calls [(site, name)]) among the given instruction vas."""
    lcg, rc = [], []
    for va in sorted(vas):
        mn, ops = A.ins[va]
        if has_imm(ops, LCG_MUL):
            lcg.append(va)
        if mn == "call":
            t = branch_target(ops)
            if t in RNG_FNS:
                rc.append((va, RNG_FNS[t]))
    return lcg, rc


def graph(roots, stop=()):
    """Walk the direct-call graph under roots. Returns {entry: (depth, parent, vas, calls, icalls)}."""
    A = asm()
    out = collections.OrderedDict()
    q = collections.deque()
    for r in roots:
        if r not in out:
            out[r] = None
            q.append((r, 0, None))
    while q:
        e, d, p = q.popleft()
        vas, calls, icalls = body(A, e)
        out[e] = (d, p, vas, calls, icalls)
        for t in [t for _, t in calls]:
            if t in RNG_FNS or t in stop or t in out:
                continue
            out[t] = None
            q.append((t, d + 1, e))
    return out


def rng_functions(G):
    """{entry: (lcg sites, rng calls)} for every walked function that draws."""
    A = asm()
    res = {}
    for e, (d, p, vas, calls, icalls) in G.items():
        lcg, rc = rng_sites(A, vas)
        if lcg or rc:
            res[e] = (lcg, rc)
    return res


def ghidra_rng(path):
    """The rng functions and their sites from a RngCallGraph.java output file."""
    fns, cur = {}, None
    for ln in open(path, errors="replace"):
        if ln.startswith("fn "):
            f = ln.split()
            cur = int(f[1], 16)
            fns[cur] = [" rng" in ln, set(), f[2]]
        elif cur is not None and ln.startswith("   lcg "):
            fns[cur][1].add(int(ln.split()[1], 16))
        elif cur is not None and ln.startswith("   call "):
            fns[cur][1].add(int(ln.split()[1], 16))
    return fns


def lcg_scan():
    """Every instruction in .text with the LCG multiplier as an operand (objdump), and every raw occurrence of its
    four bytes anywhere in the image."""
    A = asm()
    ins = sorted(va for va, (mn, ops) in A.ins.items() if has_imm(ops, LCG_MUL))
    data, base, secs = image()
    pat = struct.pack("<I", LCG_MUL)
    raw, i = [], data.find(pat)
    while i >= 0:
        for sva, vsz, rawoff, rsz, name, _ in secs:
            if rawoff <= i < rawoff + rsz:
                raw.append(sva + i - rawoff)
        i = data.find(pat, i + 1)
    return ins, raw


# ------------------------------------------------------------------------------------------------------------ report
class Report:
    """One `S4B <check> key=value ...` line. `bad` counts observations that contradict a claim the batch raises;
    `contra` counts observations that contradict a claim the batch records as a correction (not a failure of the
    check)."""

    def __init__(self, name):
        self.name = name
        self.c = collections.Counter()
        self.notes = []

    def add(self, k, n=1):
        self.c[k] += n

    def note(self, s):
        self.notes.append(s)

    def done(self):
        print("S4B %s %s" % (self.name, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
        for s in self.notes:
            print("  " + s)
        return 1 if self.c["bad"] else 0


SCRATCH = os.path.join(ROOT, "workspace", "scratch-s4b")


def raw_callers(target):
    """rel32 call/jmp sites of target, from the raw bytes (tools/xrefscan.py)."""
    import xrefscan
    data = open(EXE, "rb").read()
    base, secs = xrefscan.sections(EXE)
    return sorted(va for kind, va, _ in xrefscan.scan(data, base, secs, target) if kind in ("call", "jmp"))


def raw_abs(target):
    import xrefscan
    data = open(EXE, "rb").read()
    base, secs = xrefscan.sections(EXE)
    return sorted(va for kind, va, _ in xrefscan.scan(data, base, secs, target) if kind.startswith("abs"))


def ghidra_xrefs(path=None):
    """{target: [(site, kind)]} from a `tools/ghidra.sh xrefs` output saved in workspace/scratch-s4b/ghidra-xrefs.txt."""
    path = path or os.path.join(SCRATCH, "ghidra-xrefs.txt")
    out, cur = {}, None
    if not os.path.exists(path):
        return None
    for ln in open(path, errors="replace"):
        if ln.startswith("# "):
            cur = int(ln.split("@")[1].split()[0], 16)
            out[cur] = []
        elif ln.startswith("to ") and cur is not None:
            f = ln.split()
            out[cur].append((int(f[1], 16), f[2]))
    return out


def excel(name):
    import excel_bin
    return excel_bin.read_bin(excel_bin.find_file(EXCEL, name, ".bin"))[0]


def tsv(name):
    import csv
    with open(os.path.join(EXCEL, name + ".txt"), errors="replace") as f:
        return [r for r in csv.DictReader(f, delimiter="\t") if (r.get("Name") or r.get("Id") or r.get("code")) != "Expansion"]


# --------------------------------------------------------------------------------------------------------------- rng
def chk_rng(a):
    """drlg/README row 17 (spec L432), room-tiles row 17 (L581): the RNG-bearing functions under the dispatch roots and
    in the room-build window. The objdump walk (this file) is compared with RngCallGraph.java's output, which must be
    saved first:
      tools/ghidra.sh rngcallgraph re/rngclass/drlg-gen.txt 0x006424A0 0x00642AE0 > workspace/scratch-s4b/rcg-gen.txt
      tools/ghidra.sh rngcallgraph re/rngclass/drlg-room-build.txt 0x0067D2D0 0x0067D710 0x006667D0 0x00666AC0 \\
          table@0x00749BAC:6 > workspace/scratch-s4b/rcg-room.txt
    Both tools must list the same RNG-bearing functions and the same LCG and RNG-call sites. Ghidra's extra entries are
    import thunks and functions it reached through calls it resolved (a register loaded with a constant, the grid-op
    table); those are walked here as roots and must hold no RNG site."""
    R = Report("rng")
    sets = [("gen", [0x006424A0, 0x00642AE0], "rcg-gen.txt", 56),
            ("room", [0x0067D2D0, 0x0067D710, 0x006667D0, 0x00666AC0] + dwords(0x00749BAC, 6), "rcg-room.txt", 4)]
    for name, roots, gfile, want in sets:
        gpath = os.path.join(SCRATCH, gfile)
        if not os.path.exists(gpath):
            R.note("%s: %s missing (run the ghidra.sh command in this check's docstring)" % (name, gpath))
            R.add("bad")
            continue
        G = graph(roots)
        Rf = rng_functions(G)
        g = ghidra_rng(gpath)
        grng = {e for e, v in g.items() if v[0]}
        gsites = set().union(*[v[1] for v in g.values()])
        osites = set()
        for e, (l, c) in Rf.items():
            osites |= set(l) | {s for s, _ in c}
        allv = set().union(*[v[2] for v in G.values()])
        extra = [e for e in g if e >= 0x400000 and e not in G and e not in allv]
        G2 = graph(extra) if extra else {}
        R.add("%s_objdump_functions" % name, len(G))
        R.add("%s_ghidra_functions" % name, len(g))
        R.add("%s_ghidra_import_thunks" % name, sum(1 for e in g if e < 0x400000))
        R.add("%s_ghidra_resolved_extra" % name, len(extra))
        R.add("%s_rng_objdump" % name, len(Rf))
        R.add("%s_rng_ghidra" % name, len(grng))
        R.add("%s_sites" % name, len(osites))
        R.add("%s_rng_in_extra" % name, len(rng_functions(G2)) if G2 else 0)
        if set(Rf) != grng or osites != gsites or len(Rf) != want or (G2 and rng_functions(G2)):
            R.add("bad")
            R.note("%s: objdump-only %s, ghidra-only %s" % (name, sorted(map(hex, set(Rf) - grng)),
                                                            sorted(map(hex, grng - set(Rf)))))
    ins, raw = lcg_scan()
    R.add("lcg_instructions_in_text", len(ins))
    R.add("lcg_raw_occurrences", len(raw))
    R.note("redecoded windows: %d" % asm().redecoded)
    return R.done()


# objects row 25: the depth-3 InitFn table of objects/0001 § 7 (InitFn -> draws listed there)
INITFN_LISTED = {1, 2, 3, 57, 27, 28, 34, 58, 79, 46, 47, 54, 55, 62, 66, 68, 69}
SPAWN_FNS = {0x005B2F20: "SpawnAtPos", 0x0054E600: "PresetMonSpawn", 0x005A43E0: "SpecialMonSpawn",
             0x00555230: "SUnitCreate"}
STOP_FNS = {0x00624690: "UNIT_SetMode", 0x005544B0: "queue insert, monster-only branch (0x0054170D)"}


def chk_initfn(a):
    """objects row 25 (spec L601): the InitFn draws. Every one of the 80 g_ObjInitFns slots is walked to full depth
    (objdump), stopping at UNIT_SetMode (the animation draw the finding names for every handler), at the event-queue
    insert's monster-only call (0x005544B0, behind unit type 1 and event 2 at 0x005416F7-0x00541712, which an object
    never takes) and at the monster-spawn entry points (SpawnAtPos, PresetMonSpawn, SpecialMonSpawn, SUnitCreate: the
    draws of a created unit). A handler whose walk draws, or reaches a spawn entry, is a draw site; one that is not in
    the finding's table contradicts its "only in these" (counted as contra). RngCallGraph.java scans the 29 slots that
    have no Ghidra function only linearly to the first return (stub lines), which is why it misses tail jumps such as
    InitFn 18's jmp 0x0059F380."""
    R = Report("initfn")
    tab = dwords(0x00731BC0, 80)
    byh = collections.defaultdict(list)
    for i, t in enumerate(tab):
        byh[t].append(i)
    R.add("slots", len(tab))
    R.add("null_slots", len(byh.get(0, [])))
    R.add("distinct_handlers", len([t for t in byh if t]))
    missing = []
    for h, idx in sorted(byh.items(), key=lambda kv: kv[1][0]):
        if not h:
            continue
        G = graph([h], stop=set(SPAWN_FNS) | set(STOP_FNS))
        Rf = rng_functions(G)
        reach = set()
        for e, v in G.items():
            for site, t in v[3]:
                if t in SPAWN_FNS:
                    reach.add(SPAWN_FNS[t])
        draws = bool(Rf) or bool(reach)
        listed = any(i in INITFN_LISTED for i in idx)
        if draws:
            R.add("handlers_drawing")
        if draws and listed:
            R.add("listed_and_drawing")
        if listed and not draws:
            R.add("bad")
            R.note("InitFn %s listed but no draw found" % idx)
        if draws and not listed:
            R.add("contra")
            missing.append((idx, hex(h), sorted(reach), len(Rf)))
    for m in missing:
        R.note("not in the table: InitFn %s at %s reaches %s, %d drawing functions below it" % m)
    return R.done()


def chk_operate(a):
    """objects row 43 (spec L796, J5): the g_ObjOperateFns slots read from the image, the Objects OperateFn column against
    them, and the handler bodies (objdump, no callees) with an LCG step, each placed on its seed: the context seed
    (a load from [reg+0xC] of the handler context) or QUESTS_GetSeed's (a call to 0x005438B0 just before)."""
    R = Report("operate")
    tab = dwords(0x00732D18, 101)
    null = [i for i, t in enumerate(tab) if t == 0]
    R.add("slots", len(tab))
    R.add("handlers", 101 - len(null))
    R.add("distinct_handlers", len({t for t in tab if t}))
    if null != [0, 35, 36, 37, 38, 60] + list(range(74, 101)):
        R.add("bad")
        R.note("null slots %s" % null)
    use = collections.defaultdict(list)
    for i, r in enumerate(tsv("objects")):
        if r["OperateFn"].lstrip("-").isdigit():
            use[int(r["OperateFn"])].append(i)
    R.add("rows_on_null_slots_35_38", sum(len(use[k]) for k in (35, 36, 37, 38)))
    R.note("rows on slots 35-38: %s; rows on slot 60 or above 73: %d" % (
        [use[k] for k in (35, 36, 37, 38)], sum(len(v) for k, v in use.items() if k == 60 or k > 73)))
    if sum(len(v) for k, v in use.items() if k == 60 or k > 73):
        R.add("bad")
    A = asm()
    ctx, quest = [], []
    for i, t in enumerate(tab):
        if not t:
            continue
        vas, calls, ic = body(A, t)
        lcg, rc = rng_sites(A, vas)
        sv = sorted(vas)
        for site in lcg:
            k = sv.index(site)
            src = "?"
            for v in reversed(sv[max(0, k - 16):k]):
                mn, ops = A.ins[v]
                if mn == "call" and branch_target(ops) == 0x005438B0:
                    src = "quest"
                    break
                if mn == "mov" and re.search(r"\[e(si|di|bx)\+0xc\]$", ops):
                    src = "ctx"
                    break
            (ctx if src == "ctx" else quest if src == "quest" else R.notes).append(i)
            if src == "?":
                R.add("bad")
    ctx, quest = sorted(set(ctx)), sorted(set(quest))
    R.add("handlers_stepping_ctx", len(ctx))
    R.add("handlers_stepping_quest_seed", len(quest))
    R.note("context seed: %s; quest seed: %s" % (ctx, quest))
    if ctx != [1, 3, 4, 5, 26, 48, 68]:
        R.add("bad")
    return R.done()


def chk_portal(a):
    """outdoor row 3 (spec L53): every call of PortalObjectCreate (0x0056D130) and the level it passes (its 4th stack
    argument, [ebp+0x14]): a pushed constant, or traced to its source."""
    R = Report("portal")
    sites = raw_callers(0x0056D130)
    R.add("call_sites", len(sites))
    gx = ghidra_xrefs()
    if gx and 0x0056D130 in gx:
        gs = sorted(s for s, k in gx[0x0056D130] if "CALL" in k)
        R.add("ghidra_call_sites", len(gs))
    A = asm()
    traced = {
        0x0054B8F3: "param_1 of 0x0054B830; its five callers push 40, 75, 109, 103, 109",
        0x00582AA8: "0x0061AB70(act of the unit's level): the act's town",
        0x0059CBA8: "constant 40 (0x0059CB87 push 0x28, a2q6)",
        0x005A99BD: "param_1 of 0x005A9930 = Missiles +0x44 (missile functions 0x005ABE50, 0x005AF240)",
        0x005BE32A: "0x0061AB70(act of the unit's level): the act's town",
        0x0058B01D: "constant 121 (0x0058B004 push 0x79; an inner call's argument is pushed after it)",
        0x0058BD33: "constant 121 (0x0058BD1E push 0x79; as above)",
        0x00592DE8: "constant 38 (0x00592DD3 push 0x26; as above)",
    }
    levels = [121, 121, 38]
    for s in sites:
        # the pushes before the call, newest last
        prev = [x for x in range(s - 0x30, s) if x in A.ins]
        pushes = [A.ins[x][1] for x in prev if A.ins[x][0] == "push"]
        if len(pushes) >= 4 and BRANCH_TARGET.match(pushes[-4]) and s not in traced:
            levels.append(int(pushes[-4], 16))
            R.add("constant_level")
        elif s in traced:
            R.add("traced_level")
        else:
            R.add("bad")
            R.note("untraced site 0x%08X pushes %s" % (s, pushes))
    for c in raw_callers(0x0054B830):
        prev = [x for x in range(c - 0x10, c) if x in A.ins and A.ins[x][0] == "push"]
        levels.append(int(A.ins[prev[-1]][1], 16))
    miss = [struct.unpack_from("<i", r, 0x44)[0] for r in excel("missiles")]
    R.note("constant and town levels: %s; Missiles +0x44 values: %s" % (sorted(levels), sorted(collections.Counter(miss).items())))
    if any(133 <= x <= 136 for x in levels + miss):
        R.add("bad")
    return R.done()


def chk_grid3(a):
    """outdoor row 5 (spec L194): under OutdoorLevelBuild (0x00675360, OutdoorRoomsCreate excluded), every operand at
    displacement +0x40 or `add reg, 0x40` (objdump). Expected: the allocation of grid3 (0x006753E1) and LvlPrest `Files`
    reads; the rest in the C runtime and allocator (below 0x00420000 or above 0x00680000)."""
    R = Report("grid3")
    A = asm()
    G = graph([0x00675360], stop={0x006750F0})
    R.add("functions", len(G))
    pat = re.compile(r"\[(e[a-z]{2})\+0x40\]")
    known = {0x006753E1: "GridAlloc(O+0x40), before the act switch", 0x00674380: "LvlPrest Files",
             0x00674386: "LvlPrest Files", 0x00667490: "LvlPrest Files", 0x0067F502: "LvlPrest Files (LvlPrestByDef)"}
    for e, (d, p, vas, calls, ic) in G.items():
        for va in vas:
            mn, ops = A.ins[va]
            if pat.search(ops) or (mn == "add" and ops.endswith(",0x40")):
                if va in known:
                    R.add("game_sites_named")
                elif e < 0x00420000 or e >= 0x00680000:
                    R.add("runtime_sites")
                else:
                    R.add("bad")
                    R.note("0x%08X in 0x%08X: %s %s" % (va, e, mn, ops))
    vas, calls, ic = body(A, 0x006750F0)
    R.add("roomscreate_grid3_reads", sum(1 for v in vas if A.ins[v] == ("add", "ecx,0x40")))
    return R.done()


def chk_defs(a):
    """outdoor row 19 (spec L1290): Defs 852-856 under the outdoor generators. No immediate 852..856 in the walked
    bodies, no 16-bit value 852..856 within 0x800 bytes of any data address they name, the records' LevelId (0: no
    by-level lookup finds them), and the `defs` grids of every logged outdoor window (ODG lines)."""
    R = Report("defs")
    import glob
    import json
    A = asm()
    G = graph([0x00675360], stop={0x006750F0})
    want = set(range(852, 857))
    refs = set()
    for e, (d, p, vas, calls, ic) in G.items():
        for va in vas:
            mn, ops = A.ins[va]
            for h in IMM.findall(ops):
                v = int(h, 16)
                if v in want and not ops.startswith("0x"):
                    R.add("bad")
                    R.note("immediate %d at 0x%08X" % (v, va))
                if e >= 0x00660000 and section_of(v) in (".rdata", ".data"):
                    refs.add(v)
    for v in refs:
        for k in range(0, 0x800, 2):
            off = va_off(v + k)
            if off is None:
                break
            w = struct.unpack_from("<H", image()[0], off)[0]
            if w in want:
                R.add("table_values")
    R.add("data_refs_scanned", len(refs))
    lid = [struct.unpack_from("<I", r, 0x04)[0] for r in excel("lvlprest")]
    defs = [struct.unpack_from("<I", r, 0x00)[0] for r in excel("lvlprest")]
    R.note("LevelId of Defs 852-856: %s" % [lid[defs.index(d)] for d in sorted(want)])
    n = 0
    ids = collections.Counter()
    for p in sorted(glob.glob(os.path.join(LOGS, "**", "*.log"), recursive=True)):
        for ln in open(p, errors="replace"):
            if ln.startswith("ODG "):
                try:
                    d = json.loads(ln[4:])
                except ValueError:
                    continue
                n += 1
                ids[d["id"]] += 1
                R.add("logged_defs_852_856", sum(1 for v in d["defs"] if v in want))
    R.add("odg_windows", n)
    R.add("odg_levels", len(ids))
    R.add("odg_windows_level_108", ids[108])
    if R.c["table_values"] or R.c["logged_defs_852_856"]:
        R.add("bad")
    return R.done()


# (target, expected call sites, rows) for the caller claims: the raw rel32 scan (tools/xrefscan.py) next to Ghidra
CALLERS = [
    (0x0064C860, [0x0066E822, 0x0066E8B6, 0x0066E916], "collision 10: TileCollisionUpdate, only Bit2TileMerge"),
    (0x0061F490, [0x00673B19], "maze 2: LvlMazeByLevel, only MazeLevelCreate"),
    (0x00666ED0, [0x00668129, 0x00673A7E, 0x006751C9], "README 11: PresetInstanceCreate (level, maze, outdoor builders)"),
    (0x00666EC0, [0x006751DB], "README 11: PresetSetFile, only OutdoorRoomsCreate"),
    (0x0061E4A0, [0x0061EA57, 0x0061EFA8, 0x0061F938], "room-tiles 7: TilePathPrefix, only the three table loaders"),
    (0x0061EAE0, [0x0044DB74], "room-tiles 19: LvlTypesIsAct, only ActDt1Preload"),
    (0x006429E0, [], "room-tiles 19: the Act wrapper 0x006429E0, unreferenced"),
    (0x00665F40, [0x0061EFDB, 0x0061F966, 0x006678D2, 0x00667A1F, 0x00670503], "room-tiles 23: DS1_LoadCached"),
    (0x0066BA70, [0x0061AA51], "preset 27: the room-outdoors test, via 0x0061AA40"),
    (0x0061AA40, [0x00460EEA, 0x005DD9A1], "preset 27: callers of the room-outdoors wrapper"),
]
ABS = [
    (0x00731BBC, [0x00552793], "objects 2: g_ObjGoreLimit, one reference (the read at 0x00552791)"),
    (0x0096D60C, [0x00665F58, 0x00665FFD, 0x00666021, 0x00666072, 0x00668322, 0x00668374],
     "room-tiles 23: g_Ds1Cache, the cache's own load, search (0x00666070) and release (0x00668300)"),
    (0x0096D470, None, "objects 22: the Objects table pointer"),
    (0x006429E0, [], "room-tiles 19: the Act wrapper, no pointer to it"),
]


def chk_callers(a):
    """Caller and reference claims: the raw byte scan against the expected list (and Ghidra's, when
    workspace/scratch-s4b/ghidra-xrefs.txt holds `tools/ghidra.sh xrefs` output for the target)."""
    R = Report("callers")
    gx = ghidra_xrefs() or {}
    for t, want, what in CALLERS:
        got = raw_callers(t)
        ok = got == sorted(want)
        R.add("targets")
        if t in gx:
            gs = sorted(s for s, k in gx[t] if "CALL" in k)
            R.add("ghidra_compared")
            if gs != got:
                R.note("0x%08X Ghidra %s (raw adds %s)" % (t, [hex(x) for x in gs], [hex(x) for x in sorted(set(got) - set(gs))]))
        if not ok:
            R.add("bad")
        R.note("%s: %s%s" % (what, [hex(x) for x in got], "" if ok else " (expected %s)" % [hex(x) for x in want]))
    A = asm()
    for t, want, what in ABS:
        got = raw_abs(t)
        R.add("targets")
        if want is not None and got != sorted(want):
            R.add("bad")
        R.note("%s: %s" % (what, [hex(x) for x in got]))
    # the Objects table pointer: every instruction naming it, and OBJECTS_GetRecord's index arithmetic
    users = sorted(va for va, (mn, ops) in A.ins.items() if "0x96d470" in ops)
    R.add("objects_table_pointer_users", len(users))
    if users != [0x00640DE9, 0x00640E00, 0x00640ECE, 0x00640EE0, 0x00640EED] or \
            A.ins.get(0x00640EC8) != ("imul", "eax,eax,0x1c0"):
        R.add("bad")
    return R.done()


def chk_scans(a):
    """Operand scans of the objdump listing:
    - preset 27: every 0x80000 immediate; the reader 0x0066BA70 (room type 1 -> 1, type 2 -> flags & 0x80000);
    - preset 6: the two act rewrites test `id < nMonStats` first (0x00665CC0, 0x00665CFC) and SuperUnique/MonPlace
      ids are mapped to nMonStats + k (0x00665C8E, 0x00665CA9);
    - room-tiles 19: every operand at +0x780 (Act) or +0x784 (Expansion);
    - room-tiles 25: every memory store in DRLG_PresetClientObjects and its game callees (the walk stops at the
      allocator 0x0040B430);
    - room-tiles 29: every `or [reg+0x14], 0x20000|0x40000`;
    - room-tiles 32: the counter copy in both tile builders and the activation test;
    - objects 1: the six unread column offsets in the bodies of the functions the objects spec names."""
    R = Report("scans")
    A = asm()
    ins = A.ins
    if ins.get(0x0066BA80) != ("mov", "eax,DWORD PTR [ecx+0x28]") or ins.get(0x0066BA83) != ("and", "eax,0x80000"):
        R.add("bad")
    R.add("readers_of_0x80000_room_bit", 1)
    for va, exp in ((0x00665CC0, "edi,DWORD PTR [edx+0xa80]"), (0x00665CFC, "edi,DWORD PTR [eax+0xa80]"),
                    (0x00665C8E, "edi,DWORD PTR [eax+0xa80]"), (0x00665CA9, "edi,DWORD PTR [ecx+0xa80]")):
        if ins.get(va, ("", ""))[1] != exp:
            R.add("bad")
            R.note("0x%08X: %s" % (va, ins.get(va)))
        else:
            R.add("rewrite_guard_operands")
    act = sorted(va for va, (mn, ops) in ins.items() if re.search(r"\+0x78[04]\]", ops))
    R.add("lvltypes_act_expansion_operands", len(act))
    if act != [0x0061EB19, 0x0061FB97, 0x006429EC]:
        R.add("bad")
    R.note("+0x780/+0x784 operands: %s" % [hex(x) for x in act])
    G = graph([0x006663C0], stop={0x0040B430})        # the allocator (its heap stores are not grids)
    stores = collections.Counter()
    st = re.compile(r"^(?:BYTE|WORD|DWORD) PTR \[(?!ebp|esp)")
    for e, (d, p, vas, calls, ic) in G.items():
        if not (0x00420000 <= e < 0x00680000):
            continue
        for va in vas:
            mn, ops = ins[va]
            if mn in ("mov", "or", "and", "add", "sub", "xor", "inc", "dec") and st.match(ops):
                stores[e] += 1
    R.note("client objects: stores per game function %s" % {hex(k): v for k, v in sorted(stores.items())})
    if set(stores) - {0x0067CD30, 0x006661A0, 0x00666220, 0x0067CDC0, 0x00643560, 0x0066BF30}:
        R.add("bad")
    R.add("client_objects_game_functions_storing", len(stores))
    w = sorted(va for va, (mn, ops) in ins.items() if mn == "or" and re.search(r"\+0x14\],0x[24]0000$", ops))
    R.add("entry_flag_writers_0x20000", sum(1 for v in w if ins[v][1].endswith("0x20000")))
    R.add("entry_flag_writers_0x40000", sum(1 for v in w if ins[v][1].endswith("0x40000")))
    if any(0x00660000 <= v < 0x00680000 for v in w):
        R.add("bad")
    R.note("or [reg+0x14],0x20000|0x40000: %s" % [hex(x) for x in w])
    for va, exp in ((0x0067D783, "DWORD PTR [eax+0x18],ecx"), (0x0067D789, "DWORD PTR [eax+0x20],edx"),
                    (0x00666D94, "DWORD PTR [eax+0x18],ecx"), (0x00666D9A, "DWORD PTR [eax+0x20],edx"),
                    (0x00642308, "DWORD PTR [ecx+0x4],0x0"), (0x0064230E, "DWORD PTR [ecx+0xc],0x0")):
        if ins.get(va, ("", ""))[1] != exp:
            R.add("bad")
            R.note("0x%08X: %s" % (va, ins.get(va)))
        else:
            R.add("counter_operands")
    spec = open(os.path.join(ROOT, "docs", "specs", "objects", "README.md")).read()
    fns = sorted({int(x, 16) for x in re.findall(r"fn:[A-Za-z0-9_]+@(0x[0-9A-F]{8})", spec)})
    pat = re.compile(r"\[(e[a-z]{2})(?:\+e[a-z]{2}\*\d)?\+0x(c3|cc|170|11|30|31)\]")
    hits = []
    for f in fns:
        vas, calls, ic = body(A, f)
        hits += [(va, ins[va]) for va in sorted(vas) if pat.search(ins[va][1])]
    R.add("objects_spec_functions", len(fns))
    R.add("objects_column_offset_operands", len(hits))
    expected = {0x00530D84, 0x005426AF, 0x00542B89, 0x0054306C, 0x00546DD6, 0x00593C75, 0x00593C84, 0x005B7B3E,
                0x0062445D, 0x006244E6}
    if {va for va, _ in hits} != expected:
        R.add("bad")
        R.note("operands: %s" % [(hex(v), i) for v, i in hits])
    return R.done()


def chk_data(a):
    """Full-table and image-data checks (rule 2)."""
    R = Report("data")
    import ds1 as ds1mod
    # LevelIsTown's byte table
    jt = dwords(0x006426C0, 2)
    off = va_off(0x006426C8)
    b = image()[0][off:off + 0x6D]
    towns = [i + 1 for i in range(0x6D) if jt[b[i]] == 0x006426B6]
    R.note("LevelIsTown true for %s" % towns)
    if towns != [1, 40, 75, 103, 109]:
        R.add("bad")
    # the Burial Grounds slots
    t = [[struct.unpack("<i", struct.pack("<I", v))[0] for v in dwords(0x006F0750 + 16 * k, 4)] for k in range(15)]
    R.note("0x006F0750 anchors (+8) of slots 0-14: %s; slot 4 level %d" % ([x[2] for x in t], t[4][1]))
    if t[4][1] != 17 or any(x[2] == t[4][2] for x in t[5:]):
        R.add("bad")
    R.add("burial_slots_cannot_match", 10)
    # lvlprest
    pr = excel("lvlprest")
    R.add("lvlprest_records", len(pr))
    R.add("lvlprest_0x24_nonzero", sum(1 for r in pr if struct.unpack_from("<I", r, 0x24)[0]))

    def named(r):
        return sum(1 for k in range(6) if r[0x44 + 60 * k:0x44 + 60 * k + 60].split(b"\0")[0] not in (b"", b"0"))
    R.add("lvlprest_files_ne_named", sum(1 for r in pr if struct.unpack_from("<I", r, 0x40)[0] != named(r)))
    # lvlmaze
    lv = tsv("levels")
    maze = {r["Id"] for r in lv if r.get("DrlgType") == "1"}
    lm = collections.Counter(r["Level"] for r in tsv("lvlmaze"))
    R.add("maze_levels", len(maze))
    R.add("maze_levels_one_row", sum(1 for k in maze if lm[k] == 1))
    R.add("lvlmaze_rows_of_other_levels", sum(v for k, v in lm.items() if k not in maze))
    if any(lm[k] != 1 for k in maze):
        R.add("bad")
    # Maggot Lair room size (the shared maze DS1s, preset 41)
    R.note("Maggot Lair LvlMaze sizes: %s" % [(r["Level"], r["SizeX"], r["SizeY"]) for r in tsv("lvlmaze") if r["Level"] in ("62", "63", "64")])
    # objects
    ob = excel("objects")
    otx = tsv("objects")
    R.add("objects_id_ne_index", sum(1 for i, r in enumerate(otx) if r["Id"] != str(i)))
    R.note("Objects Id != index at %s" % [(i, r["Id"]) for i, r in enumerate(otx) if r["Id"] != str(i)])
    R.add("objects_gore_above_1", sum(1 for r in otx if r["Gore"] not in ("0", "1", "")))
    R.note("gore limit byte: %d" % image()[0][va_off(0x00731BBC)])
    z = [i for i, r in enumerate(ob) if (struct.unpack_from("<i", r, 0xD0)[0] == 0 or struct.unpack_from("<i", r, 0xD4)[0] == 0)
         and any(r[0x120:0x128])]
    R.add("objects_size0_with_collision", len(z))
    R.note("size 0 with HasCollision: %s" % z)
    # sizes a path can carry (collision 4)
    for name, off, fmt in (("monstats2", 0x08, "<b"), ("missiles", 0x18A, "<B")):
        v = [struct.unpack_from(fmt, r, off)[0] for r in excel(name)]
        R.add("%s_size_above_3" % name, sum(1 for x in v if not 0 <= x <= 3))
    # pool footprints (collision 26)
    ms = tsv("monstats")
    m2 = {r["Id"]: r for r in tsv("monstats2")}
    mid = {r["Id"]: r for r in ms}
    cols = [c for c in lv[0] if c.lower().rstrip("0123456789") in ("mon", "nmon", "umon")]
    pool = {r[c] for r in lv for c in cols if r[c] in mid}
    sz = collections.Counter(m2[mid[i]["MonStatsEx"] or i]["SizeX"] for i in pool)
    R.note("pool classes %d, SizeX %s, size 0: %s" % (len(pool), dict(sz),
                                                     [i for i in pool if m2[mid[i]["MonStatsEx"] or i]["SizeX"] == "0"]))
    R.add("pool_classes", len(pool))
    if set(sz) - {"2", "3", "0"}:
        R.add("bad")
    # names (preset 11)
    mp = tsv("monplace")
    names = [ms[i]["Id"] for i in (204, 205, 371, 372)] + [mp[i]["code"] for i in (33, 34, 35)]
    R.note("names: %s" % names)
    if names != ["act2vendor1", "act2vendor2", "lightningspire", "firetower", "place_group25", "place_group50", "place_group75"]:
        R.add("bad")
    # DS1 path points (preset 8)
    root = os.path.join(DATA, "data", "global", "tiles")
    ver = collections.Counter()
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f.lower().endswith(".ds1"):
                try:
                    d = ds1mod.parse(open(os.path.join(dp, f), "rb").read())
                except Exception:
                    R.add("ds1_unparsed")
                    continue
                R.add("ds1_files")
                if any(p["points"] for p in d["paths"]):
                    ver["below15" if d["version"] < 15 else "15plus"] += 1
    R.add("ds1_with_points_below_v15", ver["below15"])
    R.add("ds1_with_points_v15_plus", ver["15plus"])
    return R.done()


def chk_dt1(a):
    """room-tiles 3, 35 (the 40-candidate cap) and 7 (a mask bit on a "0" cell): per level type, the DT1 list of the OR
    of every mask that can meet it (LvlPrest Dt1Mask of the records placed in levels of that type, of every LevelId-0
    record, every LvlSub Dt1Mask, the out-room mask) plus the three fixed files: an upper bound on any room's
    candidates per key. The "0" cells are counted with the masks of records whose level is known."""
    R = Report("dt1")
    import csv
    import drlg
    D = drlg.Data(DATA, EXE)
    ltype_of = [struct.unpack_from("<I", r, 0x34)[0] for r in excel("leveldefs")]
    pm = [(struct.unpack_from("<I", r, 0x04)[0], struct.unpack_from("<I", r, 0x1AC)[0]) for r in excel("lvlprest")]
    U = collections.defaultdict(int)
    any0 = 0
    for lid, m in pm:
        if lid and lid < len(ltype_of):
            U[ltype_of[lid]] |= m
        else:
            any0 |= m
    sub = 0
    for m in D.lvlsub_dt1mask:
        sub |= m
    worst = 0
    for T in range(len(D.lvltypes)):
        mask = U[T] | any0 | sub | drlg.OUTROOM_MASK.get(T, 0)
        cnt = collections.Counter()
        for n in D.dt1_list(T, mask):
            if n.endswith("\\0"):
                continue
            try:
                for k, rs in D.dt1_keys(n).items():
                    cnt[k] += len(rs)
            except FileNotFoundError:
                R.add("dt1_missing")
        if cnt:
            worst = max(worst, max(cnt.values()))
    R.add("max_candidates_per_key_upper_bound", worst)
    if worst > 40:
        R.add("bad")
    lvl = [r for r in csv.DictReader(open(os.path.join(EXCEL, "levels.txt"), errors="replace"), delimiter="\t")
           if r["Name"] != "Expansion"]
    subtypes = collections.defaultdict(set)
    for r in lvl:
        if r["LevelType"] and r["SubType"] not in ("", "-1"):
            subtypes[int(r["LevelType"])].add(int(r["SubType"]))
    ltyp = [struct.unpack_from("<i", r, 0)[0] for r in excel("lvlsub")]
    for T in range(1, len(D.lvltypes)):
        m = U[T] | drlg.OUTROOM_MASK.get(T, 0)
        for k, t in enumerate(ltyp):
            if t in subtypes[T]:
                m |= D.lvlsub_dt1mask[k]
        R.add("zero_cells_selected_known_level", sum(1 for i in range(32) if m >> i & 1 and D.lvltypes[T][i] == "0"))
    R.add("lvlprest_levelid0_records", sum(1 for lid, m in pm if not lid))
    return R.done()


def chk_temple(a):
    """maze row 9 (spec L356): tools/drlg.py gen over the gen and maze logs (as sweep_s4a.py runs it) with the Temple
    finisher's table reads counted: Down from 0x006F02F8 + 16r, Waypoint from 0x006F0328 + 16r. Every read must be
    Down entry 0..2 or Waypoint entry 1..3, with 0 mismatches."""
    R = Report("temple")
    import drlg
    import sweep_s4a
    seen = collections.Counter()
    orig = drlg.Maze.tsp

    def tsp(M, base, rot):
        if base in (0x6F02F8, 0x6F0328):
            seen[(base, rot[0])] += 1
        return orig(M, base, rot)
    sa = sweep_s4a.Args([])
    with sweep_s4a.patched(drlg.Maze, "tsp", tsp):
        m, rk, bad = sweep_s4a.run_gen(sweep_s4a.gen_logs(sa, ("gen", "maze")))
    R.add("mismatches", bad)
    for (base, r), n in sorted(seen.items()):
        R.add("down_reads" if base == 0x6F02F8 else "waypoint_reads", n)
        if (base == 0x6F02F8 and not 0 <= r <= 2) or (base == 0x6F0328 and not 1 <= r <= 3):
            R.add("bad")
    R.note("(table, entry): count %s" % {("down" if b == 0x6F02F8 else "waypoint", r): n for (b, r), n in sorted(seen.items())})
    if bad:
        R.add("bad")
    return R.done()


def chk_chestroom(a):
    """items/tc row 64 (S2a ledger, chest tier): tools/tc_sweep.py chest takes the object's level from the operating
    player's PLR line. Here each chest call is tied to the chest itself: the resolver's source (TCR `src`, the object
    unit) -> the room it was created in (OI0 `u`/`room` for the populate pass; OU0 `room` then OUX `o.u` for a preset
    or restored object) -> the latest CB line for that room (`lid`). That level must equal the PLR level the model
    used, for every chest call of the 29 sessions tc_sweep.py reads."""
    R = Report("chestroom")
    import glob
    import json
    for k in range(2, 31):
        for p in sorted(glob.glob(os.path.join(LOGS, "objects-s%d-*.log" % k))):
            room_lid, unit_room, plr, ou_room = {}, {}, None, None
            for ln in open(p, errors="replace"):
                tag, _, rest = ln.partition(" ")
                if tag == "TCR":
                    if " stype=2 " not in ln:
                        continue
                    src = int(ln.split(" src=", 1)[1].split()[0], 16)
                    lid = room_lid.get(unit_room.get(src))
                    R.add("chest_calls")
                    if lid is None:
                        R.add("bad")
                        R.note("%s: no creation room for 0x%08x" % (os.path.basename(p), src))
                    elif lid == plr:
                        R.add("chest_level_eq_player_level")
                    else:
                        R.add("bad")
                        R.note("%s: chest level %s, PLR level %s" % (os.path.basename(p), lid, plr))
                    continue
                if tag not in ("CB", "OI0", "OU0", "OUX", "PLR"):
                    continue
                d = json.loads(rest)
                if tag == "CB":
                    room_lid[d["room"]] = d["lid"]
                elif tag == "OI0":
                    unit_room[d["u"]] = d["room"]
                elif tag == "OU0":
                    ou_room = d["room"]
                elif tag == "OUX":
                    if ou_room is not None:
                        unit_room[d["o"]["u"]] = ou_room
                    ou_room = None
                elif tag == "PLR":
                    plr = d["lid"]
    return R.done()


CHECKS = {"rng": chk_rng, "initfn": chk_initfn, "operate": chk_operate, "portal": chk_portal, "grid3": chk_grid3,
          "defs": chk_defs, "callers": chk_callers, "scans": chk_scans, "data": chk_data, "dt1": chk_dt1,
          "temple": chk_temple, "chestroom": chk_chestroom}


def main(argv):
    if len(argv) < 2 or (argv[1] not in CHECKS and argv[1] != "all"):
        print(__doc__)
        print("checks: " + " ".join(sorted(CHECKS)))
        return 2
    rc = 0
    for n in (sorted(CHECKS) if argv[1] == "all" else [argv[1]]):
        rc |= CHECKS[n](argv[2:])
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
