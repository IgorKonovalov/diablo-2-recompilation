"""Plan 0066 batch S7a (sim/frame, path, drlg/lifecycle, player/party): exhaustive xref, store and call-graph scans
with a second tool for the 63 class-c rows. No game run, no Ghidra.

Usage:
  python3 -I tools/sweep2_s7a.py <section> [<section> ...]
  python3 -I tools/sweep2_s7a.py all

Sections (the inventory rows each check serves are in the check names):
  graphs    the direct-call RNG graphs of the rows that state "no draw by direct reach" (party 2; frame 50, 78-90; path
            README 35-37), walked by tools/sweep_s4b.py's objdump walker with the stops each spec names, draws = calls
            of the RNG primitives, objdump's operand LCG sites and r2's own byte search for the multiplier; with each
            row's route (the stop reached, and draws past it without the stop) printed beside
  xrefs     raw-byte call/jmp/abs32 scans (tools/xrefscan.py) of the functions and data the rows name, each hit decoded
            by r2 (party 20; frame 6, 18, 20, 24, 38, 45, 53, 63, 93, 117, 125; path README 1, 3, 24, 41, 60, 65,
            search 28; lifecycle 2, 7, 12, 20, 27)
  reads     operand scans over the objdump listing next to r2's decoding: stack-block reads after MonPlayerBonus
            (party 14, 22), excel accessors in the frame's own code (frame 7)
  Part 2 (the 18 rows left by part 1; output check-s7a-p2.txt):
  stores    stores to fixed offsets over all of .text, each site re-decoded by r2: the context's +0x10 (path README
            6), the 22 unresolved +0x3C stores (README 63), +0x90/+0x91 (search 14, 34), item +0x24 reach (lifecycle
            11), 0x200000 at room +0x28 (29), the champion bit (36), 0x2000 at unit +0xC4 (48)
  masks     flag and mask readers: the type flags 0x100/0x200 at +0x34/+0x35 (README 38, search 5), the move masks
            in registers and tables (README 56, 76, 79), UNIT_GetSizeY's ten calls (README 17), the MonStats2 flag
            index at every flag-test call (README 77), PathSetType's server arguments (README 41)
  p2xrefs   call scans and graphs: ItemPlaceOnGround's callers (lifecycle 12), the frame's reach to the packet
            senders (frame 117)

Each section prints `S7a <section> <check> key=value ...` lines and detail lines; `bad=` counts an observation that
contradicts the statement the check tests. Stdlib only, plus objdump (through tools/sweep_s4b.py) and r2. Read-only.
The records are the "Plan 0066 batch S7a" sections of findings/frame/0001, path/0001, drlg/0009 and player/0003.
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as S  # noqa: E402
import sweep2_s4cd as T  # noqa: E402

S.RNG_FNS.setdefault(0x00472280, "RNG_RangeOffset")
S.RNG_FNS.setdefault(0x004BC500, "RNG_RandLoHi")


class Rep(T.Rep):
    def done(self):
        if "bad" not in self.c:
            self.c["bad"] += 0
        print("S7a %s %s %s" % (self.sec, self.name, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
        for s in self.notes:
            print("  " + s)
        return self.c["bad"]


def nm(va):
    e, n = T.owner(va)
    return n if e == va else "%s+0x%X" % (n, va - e)


def r2ins(va):
    for ln in T.r2("pd 1 @ 0x%x" % va).splitlines():
        m = T.R2_LINE.match(ln)
        if m and int(m.group(1), 16) == va:
            return m.group(2), m.group(3)
    return None, None


def xref(tgt):
    """(rel32 call/jmp/jcc sites, abs32 hits) from the raw bytes; each rel site decoded by r2."""
    rel, calls, ab = T.raw(tgt)
    dec = [(s, r2ins(s)) for s in rel]
    return dec, ab


def abs_instr(hit, value):
    """The instruction that holds `value` as an operand with its 4 bytes at `hit`: the objdump instruction that starts
    1 to 7 bytes before the hit and names the value, re-decoded by r2 at that address; None outside .text (data)."""
    A = S.asm()
    for back in range(1, 8):
        ins = A.ins.get(hit - back)
        if ins and S.has_imm(ins[1] or "", value):
            mn, ops = r2ins(hit - back)
            return hit - back, mn, ops
    return None


# ================================================================================================== graphs
P = {  # pass entries of GameTick (frame/0001 § 1, § 4): every graph stops at the later passes
    "ActsClockPass": 0x0052D7B0, "GameFpsStats": 0x0052D720, "NewRoomsUpdate": 0x0052D160,
    "GameRunUnitEvents": 0x005414D0, "ClientsRoomSync": 0x0052D440, "ActUnitsFrameReset": 0x0053B000,
    "ActsRoomRemovalsClear": 0x0053A820, "QUESTS_TimersRun": 0x00543E10, "RoomsDeactivate": 0x0052D240,
    "ActLevelsUnloadTickWrap": 0x0061AA20, "ExpirySweepTick": 0x0052D310,
}
SPEC = {  # frame/0001 § 4's specified entries (the `-spec` stops)
    "EquipReqRefresh": 0x0055DBC0, "UnitFree": 0x00555600, "RoomUpdateOne": 0x0052D0F0, "SUnitCreate": 0x00555230,
    "MissileCreate": 0x0059FA30, "UNIT_SetMode": 0x00624690, "SKILLS_SrvDo": 0x0056F7F0, "PlayerSetSkill": 0x005701B0,
}
X = {"UninterruptibleEnd": 0x005544B0, "LevelInit": 0x006424A0, "AutosaveTick": 0x0052D350,
     "SaveGameClients": 0x0052CA10, "PetUnitRelease": 0x00574450, "DRLG_LevelCreate": 0x00642AE0,
     "InactiveUnitSaveTest": 0x005433F0, "ActiveRoomFree": 0x0061A910,
     "PLAYER_AddExperience": 0x0057E510, "MERC_AddExp": 0x0057E860,
     "MissileFrameEvent": 0x005ADCC0, "PlayerEventDispatch": 0x00581220, "MonEventDispatch": 0x005A7F80,
     "OBJ_EventDispatch": 0x00586AD0, "ItemEventDispatch": 0x00562DA0, "RoomActivateA": 0x0061B190,
     "RoomActivateB": 0x0061B730, "Fatal1": 0x00408090, "Fatal2": 0x00408A60, "Exit": 0x00681E09,
     "PathPlanRandomWalk": 0x0067A240, "PathPlanSpiral": 0x0067A140, "PATH_DynamicCreate": 0x00649D00,
     "Alloc1": 0x0040B4B0, "Alloc2": 0x0040B430, "Alloc3": 0x0040B480}
FATAL = ["Fatal1", "Fatal2", "Exit"]
PATH_D1 = [0x00649970, 0x00650350, 0x0064FE40, 0x00648CF0, 0x00648690, 0x006486D0, 0x00648700, 0x00648E70,
           0x00648F00, 0x00649070, 0x006490E0, 0x00647FB0, 0x00648120, 0x006483A0, 0x006498A0, 0x006497D0,
           0x00649760, 0x006492F0, 0x00648050, 0x00678C10, 0x00678DF0]
PLANNERS8 = [0x00679C80, 0x00679ED0, 0x0067A000, 0x00679F70, 0x0067B850, 0x0067C2D0, 0x0067A240, 0x0067A140]
SEARCH3 = [0x0067AD00, 0x0067B850, 0x0067C2D0]
SLOTS_3_11_12 = [0x00679E50, 0x00679FD0, 0x00679E60]

_R2LCG = None


def r2lcg():
    global _R2LCG
    if _R2LCG is None:
        _R2LCG = T.r2_lcg_sites()
    return _R2LCG


NORETURN = {0x00681E09}   # the CRT exit the fatal path ends in (0x00408090, 0x00408A60, then 0x00681E09)
_ENTRIES = None


def entries():
    """Every direct call target in .text (objdump): a function entry, independent of re/symbols.csv."""
    global _ENTRIES
    if _ENTRIES is None:
        A = S.asm()
        _ENTRIES = set(S.branch_target(ops) for mn, ops in A.ins.values() if mn == "call") - {None}
    return _ENTRIES


def body2(A, entry):
    """tools/sweep_s4b.body with two changes: a `jmp` to another function's entry (a call target anywhere in .text)
    is a tail call, an edge, not a continuation of the body; a call of the CRT exit ends its block (no return)."""
    E = entries()
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
                t = S.branch_target(ops)
                if t is not None:
                    calls.append((va, t))
                    if t in NORETURN:
                        break
                else:
                    icalls.append(va)
            elif mn in ("ret", "retn", "iret", "hlt", "int3"):
                break
            elif mn == "jmp":
                t = S.branch_target(ops)
                if t is not None:
                    if t != entry and (t in E or t in S.RNG_FNS):
                        calls.append((va, t))
                    else:
                        work.append(t)
                else:
                    m = S.JTAB.match(ops)
                    if m:
                        work.extend(S.switch_targets(A, va, int(m.group(1), 16)))
                    else:
                        icalls.append(va)
                break
            elif mn.startswith("j") or mn.startswith("loop"):
                t = S.branch_target(ops)
                if t is not None:
                    work.append(t)
            va = nxt
    return seen, calls, icalls


def graph2(roots, stop=()):
    """tools/sweep_s4b.graph over body2."""
    A = S.asm()
    out = collections.OrderedDict()
    q = collections.deque()
    for r in roots:
        if r not in out:
            out[r] = None
            q.append((r, 0, None))
    while q:
        e, d, p = q.popleft()
        vas, calls, icalls = body2(A, e)
        out[e] = (d, p, vas, calls, icalls)
        for t in [t for _, t in calls]:
            if t in S.RNG_FNS or t in stop or t in out:
                continue
            out[t] = None
            q.append((t, d + 1, e))
    return out


GHIDRA7 = (0x0045C370, 0x0045C390, 0x0045C3E0, 0x00472210, 0x00472240, 0x00650E30, 0x00650E40)   # RngCallGraph.java


def walk(roots, stop, seven=False):
    """The objdump walker's direct-call graph; (graph, drawing functions {entry: (lcg, rng calls, r2 lcg)},
    indirect sites, the stops met {stop: [sites]}). seven=True takes RngCallGraph.java's seven RNG functions as the
    leaves (the two later additions are walked into), so that a count compares with the Ghidra script's."""
    A = S.asm()
    saved = dict(S.RNG_FNS)
    if seven:
        for k in list(S.RNG_FNS):
            if k not in GHIDRA7:
                del S.RNG_FNS[k]
    try:
        G = graph2(roots, stop=set(stop))
        return _walk_rest(A, G, stop)
    finally:
        S.RNG_FNS.clear()
        S.RNG_FNS.update(saved)


def _walk_rest(A, G, stop):
    r2s = set(r2lcg()[1])
    draws = {}
    for e, (d, p, vas, calls, icalls) in G.items():
        lcg, rc = S.rng_sites(A, vas)
        r2in = sorted(x for x in r2s if x in vas)
        if lcg or rc or r2in:
            draws[e] = (lcg, rc, r2in)
    ic = [s for v in G.values() for s in v[4]]
    met = collections.defaultdict(list)
    for e, v in G.items():
        for s, t in v[3]:
            if t in stop:
                met[t].append(s)
    return G, draws, ic, met


def path_to(G, e):
    ch = [e]
    while G[ch[-1]][1] is not None:
        ch.append(G[ch[-1]][1])
    return " <- ".join(nm(x) for x in ch)


GRAPHS = [
    # (row label, roots, extra stops beyond the passes and SPEC, expected route stops, use pass/spec stops)
    ("party2 XP_OnMonsterKill+collector", [0x0057E990, 0x0057E5A0],
     ["PLAYER_AddExperience", "MERC_AddExp"], [], False),
    ("frame79 rank1 ActsClockPass", [P["ActsClockPass"]], [], ["EquipReqRefresh"], True),
    ("frame80 rank2 GameFpsStats", [P["GameFpsStats"]], [], [], True),
    ("frame82 rank4-13 GameRunUnitEvents", [P["GameRunUnitEvents"]], ["MissileFrameEvent", "PlayerEventDispatch",
                                                                      "MonEventDispatch", "OBJ_EventDispatch",
                                                                      "ItemEventDispatch"], [], True),
    ("frame83 any queue entries", [0x005417D0, 0x00541650, 0x00541800, 0x005416B0, 0x005415E0, 0x00541680],
     ["UninterruptibleEnd"], ["UninterruptibleEnd"], True),
    ("frame84 rank14 ClientsRoomSync", [P["ClientsRoomSync"]], ["LevelInit", "AutosaveTick", "UninterruptibleEnd",
                                                                "SaveGameClients", "RoomActivateA", "RoomActivateB",
                                                                "DRLG_LevelCreate"],
     ["LevelInit", "AutosaveTick", "SaveGameClients", "RoomActivateB", "DRLG_LevelCreate"], True),
    ("frame85 rank15 ActUnitsFrameReset", [P["ActUnitsFrameReset"]], [], ["UnitFree"], True),
    ("frame86 rank16 ActsRoomRemovalsClear", [P["ActsRoomRemovalsClear"]], [], [], True),
    ("frame87 rank17 QUESTS_TimersRun", [P["QUESTS_TimersRun"]], [], [], True),
    ("frame88 rank18 RoomsDeactivate", [P["RoomsDeactivate"]], ["InactiveUnitSaveTest", "ActiveRoomFree"],
     ["InactiveUnitSaveTest"], True),
    ("frame89 rank19 level-unload tick", [P["ActLevelsUnloadTickWrap"]], ["DRLG_LevelCreate"], ["DRLG_LevelCreate"],
     True),
    ("frame90 rank20 ExpirySweepTick", [P["ExpirySweepTick"]], [], ["UnitFree"], True),
    ("frame50 kind11 PlrEvent11Every30", [0x00580BE0], ["PetUnitRelease", "UninterruptibleEnd"],
     ["PetUnitRelease"], True),
    ("frame50b kind11 callback 0x00574410", [0x00574410], ["PetUnitRelease", "UninterruptibleEnd"], [], True),
    ("pathR35 D1 PathPlan and around it", PATH_D1, ["PathPlanRandomWalk", "PathPlanSpiral", "PATH_DynamicCreate"]
     + FATAL, [], False),
    ("pathR35b PATH_DynamicCreate", [0x00649D00], FATAL + ["Alloc1", "Alloc2", "Alloc3"], [], False),
    ("pathR32-34 slots 3, 11, 12", SLOTS_3_11_12, FATAL, [], False),
]


def named(n):
    return P.get(n) or SPEC.get(n) or X[n]


def chk_graphs():
    bad = 0
    hits, sites = r2lcg()
    A = S.asm()
    ob = sorted(va for va, (mn, ops) in A.ins.items() if S.has_imm(ops, S.LCG_MUL))
    r = Rep("graphs", "lcg_tools")
    r.c["r2_hits"] = len(hits)
    r.c["r2_sites"] = len(sites)
    r.c["objdump_sites"] = len(ob)
    r.c["bad"] = len(set(ob) ^ set(sites))
    for x in sorted(set(ob) ^ set(sites)):
        r.note("differs 0x%08X objdump=%s r2=%s" % (x, x in ob, x in sites))
    bad += r.done()
    for label, roots, extra, route, passes in GRAPHS:
        stop = set(named(n) for n in extra)
        if passes:
            stop |= set(P.values()) | set(SPEC.values())
        stop -= set(roots)
        G, draws, ic, met = walk(roots, stop)
        r = Rep("graphs", label.split()[0])
        r.c["functions"] = len(G)
        r.c["draw_functions"] = len(draws)
        r.c["indirect"] = len(ic)
        r.c["bad"] = len(draws)
        r.c["functions_seven"] = len(walk(roots, stop, seven=True)[0])
        r.note("%s: roots %s; stops met: %s" % (label, ", ".join(nm(x) for x in roots),
                                               ", ".join("%s(%d)" % (nm(t), len(s)) for t, s in sorted(met.items()))))
        for e, (lcg, rc, r2in) in draws.items():
            r.note("  DRAW %s lcg=%s rng=%s r2=%s path %s" % (nm(e), ["0x%08X" % x for x in lcg], [n for _, n in rc],
                                                            ["0x%08X" % x for x in r2in], path_to(G, e)))
        for n in route:
            t = named(n)
            r.c["route_%s_met" % n] = len(met.get(t, []))
            if not met.get(t):
                r.c["bad"] += 1
                r.note("  route stop %s not met" % n)
            G2, d2, _, _ = walk([t], stop - {t} - set(SPEC.values()))
            r.c["route_%s_draws_alone" % n] = len(d2)
            r.c["route_%s_draws_alone_seven" % n] = len(walk([t], stop - {t} - set(SPEC.values()), seven=True)[1])
        bad += r.done()
    bad += graphs_more()
    return bad


def own_draws(e):
    A = S.asm()
    vas, calls, ic = body2(A, e)
    lcg, rc = S.rng_sites(A, vas)
    r2in = [x for x in r2lcg()[1] if x in vas]
    return vas, calls, ic, lcg + r2in, rc


def graphs_more():
    bad = 0
    A = S.asm()
    allstop = set(P.values()) | set(SPEC.values())
    # frame 81: NewRoomsUpdate's own body, and each direct callee's reach
    r = Rep("graphs", "frame81")
    vas, calls, ic, lcg, rc = own_draws(P["NewRoomsUpdate"])
    r.c["own_lcg"], r.c["own_rng_calls"], r.c["own_indirect"] = len(lcg), len(rc), len(ic)
    r.c["bad"] = len(lcg) + len(rc)
    for t in sorted(set(t for _, t in calls)):
        G, d, _, _ = walk([t], allstop - {t})
        r.note("callee %s: functions=%d draw_functions=%d (passes and specified entries stopped)" % (nm(t), len(G), len(d)))
    bad += r.done()
    # frame 78: the packet handlers of g_SrvPacketTable
    r = Rep("graphs", "frame78")
    ents = [S.dword(0x006E0D18 + 8 * i) for i in range(0x67)]   # 8-byte records {handler, word}, 0x0054D772
    roots = sorted(set(e for e in ents if e))
    stubs = [e for e in roots if len(body2(A, e)[0]) <= 2]
    r.c["entries"] = len(ents)
    r.c["nonnull"] = sum(1 for e in ents if e)
    r.c["distinct"] = len(roots)
    r.c["stubs_le2"] = len(stubs)
    r.c["null_index0"] = int(ents[0] == 0)
    G, d, ic, _ = walk(roots, set())
    r.c["functions"], r.c["draw_functions"], r.c["indirect"] = len(G), len(d), len(ic)
    G7, d7, _, _ = walk(roots, set(), seven=True)
    r.c["functions_seven"], r.c["draw_functions_seven"] = len(G7), len(d7)
    own = 0x0054D750   # SrvPacketDispatch
    vas, calls, ic2, lcg, rc = own_draws(own)
    r.c["dispatch_own_draws"] = len(lcg) + len(rc)
    r.c["bad"] = len(lcg) + len(rc) + (0 if d else 1)
    bad += r.done()
    # path 36: under the eight planners, and under the search
    for label, roots in (("pathR36 planners8", PLANNERS8), ("pathR36 search", SEARCH3)):
        r = Rep("graphs", label.split()[0] + "_" + label.split()[1])
        G, d, ic, _ = walk(roots, set(named(n) for n in FATAL))
        sites = sorted(set(x for v in d.values() for x in v[0] + v[2]))
        calls = sorted(set(n for v in d.values() for _, n in v[1]))
        r.c["functions"], r.c["draw_functions"], r.c["indirect"] = len(G), len(d), len(ic)
        r.c["lcg_sites"], r.c["rng_calls"] = len(sites), len(calls)
        r.note("%s: lcg sites %s; rng calls %s; drawing functions %s" % (label, ["0x%08X" % x for x in sites], calls,
                                                                         [nm(e) for e in d]))
        want = {0x0067A315} if label.endswith("planners8") else {0x0067A641, 0x0067A6E1, 0x0067A983}
        r.c["bad"] = len(set(sites) ^ want) + len(calls)
        bad += r.done()
    # path 37: SUnitPathCreate's own body, and its callees past the path
    r = Rep("graphs", "pathR37")
    vas, calls, ic, lcg, rc = own_draws(0x00554850)
    r.c["own_draws"] = len(lcg) + len(rc)
    callees = sorted(set(t for _, t in calls) - {0x00649D00})
    G, d, ic, _ = walk(callees, {0x00649D00})
    G7, d7, _, _ = walk(callees, {0x00649D00}, seven=True)
    r.c["callees"], r.c["functions"], r.c["draw_functions"] = len(callees), len(G), len(d)
    r.c["functions_seven"], r.c["draw_functions_seven"] = len(G7), len(d7)
    near = sorted(d, key=lambda e: G[e][0])[:4]
    r.note("callees: %s" % ", ".join(nm(t) for t in callees))
    for e in near:
        r.note("nearest draw %s depth %d path %s" % (nm(e), G[e][0], path_to(G, e)))
    r.c["bad"] = r.c["own_draws"] + (0 if d else 1)
    bad += r.done()
    return bad



# ================================================================================================== xrefs
def lin(entry, site):
    """r2's linear disassembly from entry up to and including site, or None when it does not land on site."""
    ins = T.r2_range(entry, site + 1)
    return ins if ins and ins[-1][0] == site else None


def reg_before(site, reg, entry=None):
    """The last instruction before site, in r2's linear listing from the function's entry (int3-padded start), that
    writes reg (a mov/xor/lea/pop/or/and/sub/add into it, or a call, which clobbers eax/ecx/edx); None if none."""
    e = entry or T.pad_entry(site)
    ins = lin(e, site)
    if not ins:
        return None
    for va, mn, ops in reversed(ins[:-1]):
        dst = ops.split(",")[0].strip()
        if mn == "call" and reg in ("eax", "ecx", "edx"):
            return va, mn, ops
        if dst == reg and mn in ("mov", "xor", "lea", "pop", "or", "and", "sub", "add", "movzx", "movsx", "inc",
                                 "dec", "imul", "shl", "shr", "sar", "neg", "xchg", "cmovne", "cmove", "sbb", "adc"):
            return va, mn, ops
    return None


def args(site, n):
    """The first n stack arguments at a call site (tools/sweep2_s4cd.pushes_before from the int3-padded entry)."""
    return T.pushes_before(site, entry=T.pad_entry(site), want=n)


def calls_of(tgt):
    dec, ab = xref(tgt)
    calls = [s for s, (mn, ops) in dec if mn == "call"]
    other = [(s, mn) for s, (mn, ops) in dec if mn != "call"]
    return calls, other, ab


def rep_calls(r, tgt, want_calls=None, want_owners=None):
    calls, other, ab = calls_of(tgt)
    r.c["calls"], r.c["jumps"], r.c["abs"] = len(calls), len(other), len(ab)
    owners = sorted(set(T.pad_entry(s) for s in calls))
    r.c["functions"] = len(owners)
    r.note("%s: %s" % (nm(tgt), ", ".join("0x%08X %s" % (s, nm(s)) for s in calls)))
    for a in ab:
        r.note("  abs 0x%08X %s %s" % (a, nm(a), abs_instr(a, tgt)))
    if want_calls is not None:
        r.c["bad"] += int(sorted(calls) != sorted(want_calls)) + len(other) + len(ab)
    return calls


def chk_xrefs():
    bad = 0
    # party 20
    r = Rep("xrefs", "party20")
    rep_calls(r, 0x00535790, [0x0055A8F4, 0x00573974])
    rep_calls(r, 0x00573930, [0x00573DBC, 0x005E8D61, 0x005E9C82, 0x005F0B32, 0x005FC542])
    rel, calls, ab = T.raw(0x00883D70)
    ins = [abs_instr(a, 0x00883D70) for a in ab]
    r.c["override_abs"] = len(ab)
    r.c["override_rel"] = len(rel)
    r.note("g_PlayersOverride refs: %s" % ins)
    r.c["bad"] += int(sorted(i[0] for i in ins if i) != [0x00535785, 0x005357B9]) + len(rel)
    bad += r.done()
    # party 22: the unreferenced build
    r = Rep("xrefs", "party22_unref")
    rel, calls, ab = T.raw(0x005E9750)
    r.c["rel"], r.c["abs"] = len(rel), len(ab)
    r.c["bad"] = len(rel) + len(ab)
    bad += r.done()
    # frame 6
    r = Rep("xrefs", "frame6")
    rep_calls(r, 0x0052D870, [0x0052FD19, 0x00564603])
    rep_calls(r, 0x005645E0, [0x00564C97])
    r.c["stub_entry_padded"] = int(T.pad_entry(0x00564C97) == 0x00564C70)
    into = 0
    for t in range(0x00564C70, 0x00564C97 + 5):
        rel, calls, ab = T.raw(t)
        into += len(rel) + len(ab)
        if rel or ab:
            r.note("  ref into the stub: 0x%08X rel %s abs %s" % (t, rel, ab))
    r.c["refs_into_stub"] = into
    r.c["bad"] += into + (1 - r.c["stub_entry_padded"])
    bad += r.done()
    # frame 18
    r = Rep("xrefs", "frame18")
    calls = rep_calls(r, 0x0052FC20, [0x0044CF61, 0x0044F13D, 0x0044F159])
    for c in calls:
        a = args(c, 1)
        r.note("  0x%08X pushes cap %s" % (c, a))
        r.c["cap_1"] += int(a == ["1"])
    r.c["bad"] += len(calls) - r.c["cap_1"]
    bad += r.done()
    # frame 20
    r = Rep("xrefs", "frame20")
    rel, calls, ab = T.raw(0x0073100C)
    ins = [abs_instr(a, 0x0073100C) for a in ab]
    r.c["lagfixed_refs"], r.c["lagfixed_value"] = len(ab) + len(rel), S.dword(0x0073100C)
    r.note("g_ServerLagFixed refs: %s" % ins)
    r.c["bad"] += int(len(ab) != 1 or not ins[0] or ins[0][1] != "cmp") + int(S.dword(0x0073100C) != 1)
    acc = [(va, mn, ops) for va, (mn, ops) in S.asm().ins.items() if "+0x1dbc]" in (ops or "")]
    for va, mn, ops in sorted(acc):
        st = ops.startswith("DWORD PTR") and mn == "mov"
        r.c["stores" if st else "reads"] += 1
        r.note("  +0x1DBC %s 0x%08X %s %s in %s" % ("store" if st else "read ", va, mn, ops, nm(va)))
    i = [x for x in T.r2_range(0x0052FCAE, 0x0052FD19)]
    r.c["branch_jne_to_0x400"] = int(any(mn == "jne" and "0x52fd0d" in ops for _, mn, ops in i))
    bad += r.done()
    # frame 24
    r = Rep("xrefs", "frame24")
    rel, calls, ab = T.raw(0x0052F630)
    r.c["abend_rel"], r.c["abend_abs"] = len(rel), len(ab)
    acc = [(va, mn, ops) for va, (mn, ops) in S.asm().ins.items() if "+0x1dc8]" in (ops or "")]
    for va, mn, ops in sorted(acc):
        st = ops.startswith("DWORD PTR") and mn == "mov"
        r.c["stores" if st else "reads"] += 1
        r.note("  +0x1DC8 %s 0x%08X %s %s in %s" % ("store" if st else "read ", va, mn, ops, nm(va)))
    r.c["bad"] = len(rel) + len(ab) + int(r.c["stores"] != 2)
    bad += r.done()
    # frame 38 and 45
    r = Rep("xrefs", "frame38")
    calls = rep_calls(r, 0x00541650, [0x00553F19, 0x0059F8D3, 0x005D1982])
    for c in calls:
        r.note("  0x%08X %s kind %s" % (c, nm(c), args(c, 1)))
    rep_calls(r, 0x005415E0, [0x00541666, 0x00541698, 0x005416D7])
    rel, cc, ab = T.raw(0x00541680)
    r.c["everyframecb_refs"] = len(rel) + len(ab)
    m1 = [x for x in T.r2_range(0x005416C5, 0x005416D8)]
    r.c["frame_minus1_test"] = int(any(mn == "cmp" and "0xffffffff" in ops for _, mn, ops in m1))
    r.c["bad"] += r.c["everyframecb_refs"] + (1 - r.c["frame_minus1_test"])
    bad += r.done()
    r = Rep("xrefs", "frame45")
    want = {0: 18, 1: 60, 2: 30, 3: 18, 4: 1, 5: 5, 6: 6, 7: 45, 8: 7, 9: 7, 10: 3, 11: 3, 12: 42, 13: 20}
    for tgt, label in ((0x005417D0, "UnitQueueEvent"), (0x00541800, "UnitQueueEventCb"),
                       (0x00541650, "UnitQueueEveryFrame")):
        calls, other, ab = calls_of(tgt)
        k = collections.Counter()
        for c in calls:
            a = args(c, 1)
            v = T.imm(a[0]) if a else None
            k[v] += 1
            if v is None:
                r.note("  non-constant kind at 0x%08X: %s" % (c, a))
        r.c[label + "_sites"] = len(calls)
        r.c[label + "_jumps_abs"] = len(other) + len(ab)
        r.c["nonconst"] += k[None]
        r.note("%s: %s" % (label, dict(sorted((x, y) for x, y in k.items() if x is not None))))
        if label == "UnitQueueEvent":
            r.c["bad"] += int(dict(k) != want)
        r.c["bad"] += len(other) + len(ab)
    r.c["total_sites"] = r.c["UnitQueueEvent_sites"] + r.c["UnitQueueEventCb_sites"] + r.c["UnitQueueEveryFrame_sites"]
    r.c["bad"] += r.c["nonconst"] + int(r.c["total_sites"] != 269)
    bad += r.done()
    # frame 50: the pushes it names
    r = Rep("xrefs", "frame50")
    a = args(0x005755FB, 2)
    a = args(0x00575600, 2)
    b, c = args(0x00534B1D, 2), args(0x00534B02, 2)
    r.note("PetRemove call 0x00575600 (push at 0x005755FB) args %s; 0x00534B1D args %s; 0x00534B02 args %s" % (a, b, c))
    t = T.r2_range(0x00575132, 0x0057513C)
    r.c["petremove_arg2_zero"] = int(a == ["ecx", "0"])
    r.c["release_gated_on_arg"] = int([m for _, m, _ in t] == ["cmp", "je", "call"] and "ebp + 0xc" in t[0][2]
                                      and "0x574450" in t[2][2])
    r.c["kind11_at_frame_plus_0xfa"] = int(b and b[0] == "0xb" and any("0xfa" in o for _, m, o in
                                                                     T.r2_range(0x00534B07, 0x00534B1D)))
    r.c["kind3_at_frame_plus_1"] = int(c and c[0] == "3" and any(o == "edx, 1" for _, m, o in
                                                                  T.r2_range(0x00534AEE, 0x00534B02)))
    r.c["bad"] = 4 - sum(r.c[k] for k in ("petremove_arg2_zero", "release_gated_on_arg", "kind11_at_frame_plus_0xfa",
                                          "kind3_at_frame_plus_1"))
    bad += r.done()
    # frame 53: the clock tables, every reference and what each does with it
    r = Rep("xrefs", "frame53")
    lo, hi = 0x007443F0, 0x007443F0 + 3 * 0x48
    refs = []
    for va, (mn, ops) in S.asm().ins.items():
        for h in S.IMM.findall(ops or ""):
            v = int(h, 16)
            if lo <= v < hi:
                refs.append((va, mn, ops))
    rawn = 0
    for t in range(lo, hi, 4):
        rel, cc, ab = T.raw(t)
        rawn += len(ab)
    r.c["operand_refs"], r.c["raw_abs_hits"] = len(refs), rawn
    stores = 0
    for va, mn, ops in sorted(refs):
        kind = "load"
        if mn == "lea" or (mn == "mov" and not ops.split(",")[0].strip().startswith(("DWORD", "BYTE", "WORD"))
                           and "PTR" not in ops):
            kind = "pointer"
            reg = ops.split(",")[0].strip()
            for va2, mn2, ops2 in T.r2_range(va, va + 0x60)[1:]:
                d = ops2.split(",")[0]
                if reg in d and "[" in d and mn2 in ("mov", "add", "sub", "or", "and", "inc", "dec", "xor"):
                    stores += 1
                    r.note("  STORE through 0x%08X: 0x%08X %s %s" % (va, va2, mn2, ops2))
                if mn2 in ("ret", "call") or (d.strip() == reg and mn2 in ("mov", "lea", "xor", "pop")):
                    break
        elif ops.split(",")[0].startswith(("DWORD PTR", "BYTE PTR", "WORD PTR")) and mn in ("mov", "add", "sub", "or",
                                                                                             "and", "inc", "dec"):
            kind = "store"
            stores += 1
        r.c[kind] += 1
    r.c["stores"] = stores
    rows = [[S.dwords(b + 12 * i, 3) for i in range(6)] for b in (0x007443F0, 0x00744438, 0x00744480)]
    r.c["max_start"] = max(x[0] for t in rows for x in t)
    r.c["k360_last_fit"] = (2 ** 31 - 1) // 360
    r.c["kstart_last_fit"] = (2 ** 31 - 1) // r.c["max_start"]
    r.c["row_stride_12"] = int(any(mn == "lea" and "[ecx+ecx*2]" in ops.replace(" ", "")
                                   for _, mn, ops in T.r2_range(0x0061BCF0, 0x0061BD00)))
    r.c["next_after_T2_is_pointer"] = int(0x00600000 < S.dword(hi) < 0x00800000)
    r.c["bad"] = stores
    bad += r.done()
    # frame 63: the act's +0x4C
    r = Rep("xrefs", "frame63")
    i = T.r2_range(0x00619910, 0x00619956)
    r.c["edi_is_act_arg"] = int(any(va == 0x00619910 and "ebp - 4" in ops for va, mn, ops in i))
    r.c["reads_4c_then_calls"] = int(any(va == 0x0061994B for va, mn, ops in i) and any(
        va == 0x00619954 and mn == "call" for va, mn, ops in i))
    h = T.r2_range(0x006194A0, 0x00619548)
    r.c["act_alloc_0x60"] = int(any(va == 0x006194B1 and "0x60" in ops for va, mn, ops in h))
    r.c["act_memset"] = int(any(va == 0x006194C4 and mn == "call" for va, mn, ops in h))
    r.c["act_create_stores_4c"] = sum(1 for va, mn, ops in h if "esi + 0x4c]" in ops and mn == "mov")
    st = [(va, ops) for va, (mn, ops) in S.asm().ins.items() if mn == "mov" and re.match(
        r"DWORD PTR \[e[a-z]{2}\+0x4c\],", ops or "")]
    r.c["other_reg_stores_4c"] = len(st)
    r.c["callback_ptrs_client_only"] = sum(len(T.raw(t)[2]) for t in (0x00459150, 0x004591A0))
    r.c["bad"] = r.c["act_create_stores_4c"]
    bad += r.done()
    # frame 93 and 125
    r = Rep("xrefs", "frame93")
    rel, cc, ab = T.raw(0x0088CAD0)
    ins = [abs_instr(a, 0x0088CAD0) for a in ab]
    r.c["refs"], r.c["rel"] = len(ab), len(rel)
    r.note("g_HitClassCounter: %s" % ins)
    stores = [x for x in ins if x and x[1] == "mov" and x[2].startswith("byte [")]
    r.c["stores"] = len(stores)
    r.c["store_is_dl_plus_1"] = int(any(mn == "add" and ops == "dl, 1" for va, mn, ops in T.r2_range(0x0057CE4C,
                                                                                                    0x0057CE4F)))
    sec = [x for x in S.image()[2] if x[4] == ".data"][0]
    r.c["zero_init_bss"] = int(0x0088CAD0 >= sec[0] + sec[3])
    pa = [(va, mn, ops) for va, (mn, ops) in S.asm().ins.items() if "0x88cad0" in (ops or "")]
    r.c["objdump_operands"] = len(pa)
    r.c["bad"] = int(len(stores) != 1) + (1 - r.c["store_is_dl_plus_1"]) + (1 - r.c["zero_init_bss"]) + len(rel)
    bad += r.done()
    return bad

def chk_xrefs2():
    bad = 0
    A = S.asm()
    # path README 1 and 24: PathPlan's 68 sites, their owners, the force argument; force read once
    r = Rep("xrefs", "pathR1_R24")
    calls = rep_calls(r, 0x00649970)
    r.c["bad"] += r.c["jumps"] + r.c["abs"] + int(len(calls) != 68)
    own = collections.Counter(T.pad_entry(c) for c in calls)
    r.c["owners_padentry"] = len(own)
    r.c["owners_symbols"] = len(set(T.owner(c)[0] for c in calls))
    r.c["server_sites_ge_0x52"] = sum(1 for c in calls if c >= 0x00520000)
    r.c["client_sites_lt_0x52"] = sum(1 for c in calls if c < 0x00520000)
    fz = collections.Counter()
    for c in calls:
        a = args(c, 3)
        f = a[2] if a and len(a) > 2 else None
        fz[f] += 1
        if f != "0":
            w = reg_before(c, f) if f and f.startswith("e") else None
            r.note("  force at 0x%08X %s: %s (last write %s)" % (c, nm(c), f, w))
    r.c["force_push_0"] = fz["0"]
    reads = [va for va in body2(A, 0x00649970)[0] if "[ebp+0x10]" in (A.ins[va][1] or "")]
    r.c["force_reads_in_PathPlan"] = len(reads)
    r.note("  force reads: %s" % ["0x%08X %s" % (v, A.ins[v][1]) for v in reads])
    r.c["bad"] += int(fz["0"] != 66) + int(reads != [0x00649AEE])
    bad += r.done()
    # path README 3
    r = Rep("xrefs", "pathR3")
    calls = rep_calls(r, 0x00649D00)
    r.c["server_owner_SUnitPathCreate"] = sum(1 for c in calls if T.owner(c)[0] == 0x00554850)
    r.c["server_owner_UnitRelocate"] = sum(1 for c in calls if T.owner(c)[0] == 0x00554A30)
    r.c["client"] = sum(1 for c in calls if c < 0x00520000)
    bad += r.done()
    # path README 60: requests of type 1
    r = Rep("xrefs", "pathR60")
    hits = []
    for c in calls_of(0x005A6260)[0]:
        w = reg_before(c, "edx")
        r.note("  AiPathOverrideSet 0x%08X %s edx<-%s" % (c, nm(c), w))
        if w and w[1] == "mov" and w[2].endswith(", 1"):
            hits.append(c)
    for c in calls_of(0x00648CF0)[0]:
        a = args(c, 2)
        if a and len(a) > 1 and a[1] == "1":
            hits.append(c)
    r.c["type1_sites"] = len(hits)
    want = [0x005E3BCC, 0x005E4300, 0x005E5DD9, 0x005E5EE7, 0x005E5F40, 0x005CD484, 0x005CBC44]
    r.note("  type-1 sites: %s" % ", ".join("0x%08X %s" % (c, nm(c)) for c in sorted(hits)))
    r.c["server_type1_sites"] = sum(1 for c in hits if c >= 0x00520000)
    r.c["client_type1_sites"] = sum(1 for c in hits if c < 0x00520000)
    r.c["bad"] = len(set(c for c in hits if c >= 0x00520000) ^ set(want))
    bad += r.done()
    # path README 65, search 28
    r = Rep("xrefs", "pathR65_S28")
    for t in (0x00663E00, 0x00663ED0):
        rel, cc, ab = T.raw(t)
        r.c["refs_0x%08X" % t] = len(rel) + len(ab)
    r.c["bad"] = sum(v for k, v in r.c.items() if k.startswith("refs_"))
    c16 = [c for c in calls_of(0x00648CF0)[0] if (args(c, 2) or [None, None])[1:2] == ["0x10"]]
    r.c["settype16_sites"] = len(c16)
    r.note("  PathSetType(16) sites: %s" % ["0x%08X %s" % (c, nm(c)) for c in c16])
    r.c["bad"] += sum(1 for c in c16 if T.pad_entry(c) not in (0x00663E00, 0x00663ED0))
    bad += r.done()
    # lifecycle 2
    r = Rep("xrefs", "life2")
    calls = rep_calls(r, 0x0061B730)
    for c in calls:
        e = T.pad_entry(c)
        r.note("  caller 0x%08X in entry 0x%08X (%s); its callers %s" % (c, e, nm(e), [
            "0x%08X %s" % (x, nm(x)) for x in calls_of(e)[0]]))
    r.c["contra_room_from_coords_caller"] = int(any(T.pad_entry(c) == 0x0061B7B0 for c in calls))
    for e in (0x0066AC30, 0x0066B030):
        rel, cc, ab = T.raw(e)
        r.note("  entry 0x%08X: rel %s abs %s" % (e, ["0x%08X" % x for x in rel], ["0x%08X" % x for x in ab]))
    bad += r.done()
    # lifecycle 7
    r = Rep("xrefs", "life7")
    rep_calls(r, 0x0052D0F0, [0x0055379D, 0x0056CF7D, 0x0059E018])
    bad += r.done()
    # lifecycle 20
    r = Rep("xrefs", "life20")
    calls = rep_calls(r, 0x0061A510, [0x0052D12C, 0x0052D14A, 0x0052D20C])
    for c in calls:
        a = args(c, 2)
        v = a[1] if a and len(a) > 1 else None
        if v and v.startswith("e"):
            w = reg_before(c, v)
            r.note("  0x%08X pushes %s, last write %s" % (c, v, w))
            v = "1" if w and w[1] == "mov" and w[2].endswith(", 1") else v
        r.c["pass_1"] += int(v == "1")
    body = T.r2_range(0x0061A539, 0x0061A54D)
    r.c["sets_or_2_clears_and_fffffffd"] = int(any("or dword [eax + 0x34], 2" == "%s %s" % (m, o) for _, m, o in body)
                                              and any(o.endswith("0xfffffffd") for _, m, o in body))
    clr = [(va, ops) for va, (mn, ops) in A.ins.items() if mn == "and" and re.match(r"DWORD PTR \[e..\+0x34\],0x[0-9a-f]+$", ops or "")
           and not (int(ops.split(",")[1], 16) & 2)]
    r.c["other_and_clears_bit1_at_0x34"] = len([x for x in clr if not (0x0061A510 <= x[0] < 0x0061A550)])
    r.c["bad"] += 3 - r.c["pass_1"]
    bad += r.done()
    # lifecycle 27
    r = Rep("xrefs", "life27")
    calls = rep_calls(r, 0x0061AED0)
    v = collections.Counter()
    by = collections.defaultdict(list)
    for c in calls:
        a = args(c, 2)
        x = a[1] if a and len(a) > 1 else None
        if x and x.startswith("e"):
            w = reg_before(c, x)
            pre = lin(T.pad_entry(c), c) or []
            seq = [(m, o) for _, m, o in pre[-8:]]
            zero_by_test = any(seq[i] == ("test", "%s, %s" % (x, x)) and seq[i + 1][0] == "jne"
                               and seq[i + 2] == ("push", x) for i in range(len(seq) - 2))
            x = (w[2].split(",")[1].strip() if w and w[1] == "mov" else
                 "0" if (w and w[1] == "xor") or zero_by_test else x)
        k = "clear" if x not in ("0", None) else "set"   # DrlgRoomPinFlag: 0 ORs 0x400000 in, non-zero ANDs it out
        if x is None:
            k = "unknown"
        v[k] += 1
        by[k].append("0x%08X %s(%s)" % (c, nm(c), x))
    r.c["set"], r.c["clear"], r.c["unknown"] = v["set"], v["clear"], v["unknown"]
    for k in by:
        r.note("  %s: %s" % (k, ", ".join(by[k])))
    r.c["bad"] = int(len(calls) != 31) + int(r.c["functions"] != 24) + int(v["set"] != 18) + int(v["clear"] != 13)
    bad += r.done()
    return bad


# ================================================================================================== reads
DT_LO, DT_HI = 0x0096BC30, 0x0096D000


def chk_reads():
    bad = 0
    A = S.asm()
    # party 14 and 22: the bonus block's words read after MonPlayerBonus in the four thinks
    r = Rep("reads", "party14_22")
    for site, e in ((0x005E8D61, 0x005E8810), (0x005E9C82, 0x005E9750), (0x005F0B32, 0x005F0B00),
                    (0x005FC542, 0x005FC450)):
        w = reg_before(site, "edx", entry=e)
        base = int(re.search(r"ebp - (0x[0-9a-f]+)", w[2]).group(1), 16)
        words = {base - 4 * k: "+0x%X" % (4 * k) for k in range(5)}
        seen = collections.Counter()
        for va in body2(A, e)[0]:
            for h in re.findall(r"\[ebp-(0x[0-9a-f]+)\]", A.ins[va][1] or ""):
                if int(h, 16) in words:
                    seen[(words[int(h, 16)], A.ins[va][0], va)] += 1
        r.note("%s block [ebp-0x%X]: %s" % (nm(e), base, sorted(seen)))
        rd = set(w for (w, mn, va) in seen if mn != "lea")
        r.c["words_read_" + nm(e).split("_")[-1]] = len(rd)
        r.c["bad"] += int(rd != {"+0xC"})
    bad += r.done()
    # frame 7: no excel accessor in GameTick's own code, the queue, the walks
    r = Rep("reads", "frame7")
    roots = [0x0052D870, 0x005417D0, 0x00541650, 0x00541800, 0x005416B0, 0x005415E0, 0x00541680, 0x005414D0,
             0x00541240, 0x00540F60, 0x00541060, 0x00541160, 0x00541320, 0x00540CD0, 0x00553970]
    acc = set(a for a, n in T.funcs() if n.endswith("_GetRecord") or n.startswith(("DATATBLS_", "EXCEL_"))
              or "GetRecord" in n)
    for e in roots:
        vas, calls, ic = body2(A, e)
        tb = [t for _, t in calls if t in acc]
        dt = [va for va in vas for h in S.IMM.findall(A.ins[va][1] or "")
              if DT_LO <= int(h, 16) < DT_HI or int(h, 16) == 0x00744304]
        r.c["bodies"] += 1
        r.c["accessor_calls"] += len(tb)
        r.c["datatable_refs"] += len(dt)
        r.c["indirect"] += len(ic)
        if tb or dt:
            r.note("  %s: accessor calls %s, data-table refs %s" % (nm(e), [nm(t) for t in tb], ["0x%08X" % x for x in dt]))
    r.c["accessors_known"] = len(acc)
    r.c["bad"] = r.c["accessor_calls"] + r.c["datatable_refs"]
    bad += r.done()
    return bad


# ================================================================================================== part 2
STOPS = {0x00408090, 0x00408A60, 0x00681E09}          # the fatal path's three calls
WIDTH = {"BYTE": 1, "WORD": 2, "DWORD": 4, "QWORD": 8}
MEMOP = re.compile(r"^(\w+) PTR \[(e[a-z]{2})([+-]0x[0-9a-f]+)\]$")
PLANNERS = (0x0067AD00, 0x0067B850, 0x00679C80, 0x00679E50, 0x00679ED0, 0x0067A000, 0x00679F70, 0x00679FD0,
            0x00679E60, 0x0067C2D0)                    # the ten distinct non-null entries of g_PathPlanFuncs
PATH_MOD = (0x00648000, 0x00651000)                   # the path module's address range (re/symbols.csv path rows)


def memop(ops):
    """(width bytes, base register, signed offset) of an objdump operand list's first operand, or None."""
    m = MEMOP.match((ops or "").split(",")[0].strip())
    if not m or m.group(1) not in WIDTH:
        return None
    return WIDTH[m.group(1)], m.group(2), int(m.group(3), 16)


def ival(ops):
    """The second operand's immediate, or None."""
    p = (ops or "").split(",", 1)
    if len(p) < 2:
        return None
    t = p[1].strip()
    m = re.match(r"^(?:0x([0-9a-f]+)|(\d+))$", t)
    return None if not m else int(m.group(1), 16) if m.group(1) else int(m.group(2))


WRITES = ("mov", "or", "and", "add", "sub", "xor", "inc", "dec", "bts", "btr", "btc", "not", "neg", "adc", "sbb",
          "shl", "shr", "sar", "rol", "ror", "movs", "stos", "xchg", "cmpxchg", "setne", "sete", "pop")


def stores(A, lo=None, hi=None):
    """[(va, mnemonic, ops, width, base, offset)] of every instruction writing a [reg+disp] first operand."""
    it = A.range(lo, hi) if lo is not None else sorted(A.ins.items())
    out = []
    for va, (mn, ops) in it:
        if mn.split()[0] not in WRITES and not mn.startswith("set"):
            continue
        m = memop(ops)
        if m:
            out.append((va, mn, ops) + m)
    return out


def r2s(va):
    mn, ops = r2ins(va)
    return "%s %s" % (mn, ops)


def zero_or_cmp(entry, site, reg):
    """The value reg holds at site when site lies on the fall-through of a `jne` right after a `test reg, reg`,
    `and reg, k` or `cmp reg, k`, or after `xor reg, reg`, with no write of reg between (r2's linear listing)."""
    ins = lin(entry, site)
    if not ins:
        return None, "no linear listing"
    for i in range(len(ins) - 2, -1, -1):
        va, mn, ops = ins[i]
        dst = ops.split(",")[0].strip()
        if mn == "xor" and ops.replace(" ", "") == "%s,%s" % (reg, reg):
            return 0, "0x%08X xor %s" % (va, ops)
        if dst == reg and mn in ("test", "and", "cmp") and i + 1 < len(ins) and ins[i + 1][1] == "jne":
            k = 0 if mn in ("test", "and") else T.imm(ops.split(",")[1].strip())
            return k, "0x%08X %s %s; jne" % (va, mn, ops)
        if dst == reg and mn not in ("test", "cmp", "push"):
            return None, "0x%08X %s %s writes %s first" % (va, mn, ops, reg)
    return None, "none"


def no_write(lo, hi, reg):
    """The objdump instructions in [lo, hi) whose destination is reg (a write)."""
    A = S.asm()
    return [(va, mn, ops) for va, (mn, ops) in A.range(lo, hi)
            if ops and ops.split(",")[0].strip() == reg and mn not in ("cmp", "test", "push")]


# ---------------------------------------------------------------------------------------------- stores
# README 63: the 22 sites path/0003 § 12 left (18 register stores of unresolved base, 4 read-modify-write), each with
# the reading that resolves it and the r2 text that reading rests on (checked at the value or base instruction).
B3C = [
    # (site, class, instruction checked, text it must hold, reason)
    (0x00529481, "hash", 0x0052947A, "rol edx, 1", "SHA-1 schedule word: rol 1 of an xor of the buffer's +0x30/+0x1C"),
    (0x0052981A, "hash", 0x00529815, "rol edx, 1", "SHA-1 schedule word, as above"),
    (0x00529BD7, "hash", 0x00529BD2, "rol edx, 1", "SHA-1 schedule word, as above"),
    (0x00529F12, "hash", 0x00529F10, "rol edx, 1", "SHA-1 schedule word, as above"),
    (0x00559002, "base", 0x00558FF1, "cmp eax, 0xff", "ItemCreate's clamp to 0xFF of its own block's +0x3C"),
    (0x0057C628, "base", 0x0057C620, "sar eax, 6", "COMBAT_Leech: a leech amount / 64 into its damage block"),
    (0x005B5389, "value", 0x005B537C, "call 0x620bb0", "a room pointer, tested non-null"),
    (0x005BBC61, "value", 0x005BBC2A, "xor ecx, ecx", "the value 0"),
    (0x005FFF92, "base", 0x005FFF85, "call 0x5fec50", "GfxCelPath's cel block, a call's return"),
    (0x00600225, "base", 0x00600222, "cmp dword [esi + 0x34], ebx", "GfxCelPath's cel block"),
    (0x00600230, "base", 0x0060022B, "call 0x601840", "GfxCelPath's cel block, a call's return"),
    (0x006003B2, "base", 0x006003AB, "call 0x5fec50", "GfxCelPath's cel block, a call's return"),
    (0x006242FF, "base", 0x00623F57, "mov edi, dword [ebp + 8]", "UNIT_AnimSetRate's unit argument: a unit, not a path"),
    (0x00626E9D, "value", 0x00626E92, "mov dword [edi + 0x2c], eax", "a stat list pointer (edi dereferenced)"),
    (0x00670869, "base", 0x00670866, "mov edx, dword [ecx + 0x10]", "a maze level record's room field"),
    (0x0068CFFB, "base", 0x0068CFF6, "cmp eax, dword [ebp + 0x3c]", "a CRT routine's stack frame (ebp = esp - 0x290)"),
    (0x006C3CF6, "base", 0x006C3CE6, "and dword [eax + 0x3c], ecx", "CALC_Compile's own block, flag word"),
    (0x006C3DE9, "value", 0x006C3DDD, "call 0x413020", "an allocation's return pointer (SCMD.CPP)"),
    (0x005BB82C, "base", 0x005BB82C, "add dword [ebx + 0x3c], 1", "A3Q5 cube count: a quest counter"),
    (0x0063D4CF, "base", 0x0063D4CF, "add dword [esi + 0x3c], 1", "InvCorpseAdd: the inventory's corpse count"),
    (0x0063D54C, "base", 0x0063D54C, "add dword [esi + 0x3c], 0xffffffff", "InvCorpseRemove: the inventory's corpse count"),
    (0x0068CDCF, "base", 0x0068CDCF, "or dword [ebp + 0x3c], 0xffffffff", "a CRT routine's stack frame"),
]


def chk_stores():
    bad = 0
    A = S.asm()
    # README 6: the context +0x10 (PathPlan's EBP-0x24) is never written
    r = Rep("stores", "pathR6_ctx10")
    vas = body2(A, 0x00649970)[0]
    for va in sorted(vas):
        mn, ops = A.ins[va]
        m = memop(ops)
        if m and m[1] == "ebp" and m[2] - 0 <= -0x21 and m[2] + m[0] > -0x24 and mn.split()[0] in WRITES:
            r.c["pathplan_ctx10_stores"] += 1
            r.note("  store 0x%08X %s %s" % (va, mn, ops))
        if mn == "lea" and "ebp-0x24" in ops.replace(" ", ""):
            r.c["pathplan_ctx10_lea"] += 1
    ctxlea = sorted(va for va in vas if A.ins[va][0] == "lea" and "[ebp-0x34]" in A.ins[va][1].replace(" ", ""))
    r.c["pathplan_ctx_leas"] = len(ctxlea)
    r.note("PathPlan ctx leas: %s" % ", ".join("0x%08X %s" % (v, A.ins[v][1]) for v in ctxlea))
    # the base of each +0x10 store in the five bodies: the one definer named here, no other write but a pop
    helpers = {0x00649970: [(0x00649977, "mov edi, dword [ebp + 8]")],     # PathPlan's path argument
               0x006498A0: [(0x006498A2, "mov edi, dword [ebx + 0x30]"),  # ctx.pPath (EBX the context)
                            (0x006497D2, "mov edi, dword [eax + 0x30]")],  # its jump into 0x006497D0 (EAX the context)
               0x00648120: None, 0x006483A0: None, 0x00648050: None}
    for e in list(helpers) + list(PLANNERS):
        body = body2(A, e)[0]
        for va in sorted(body):
            mn, ops = A.ins[va]
            m = memop(ops)
            if m and m[2] == 0x10 and mn.split()[0] in WRITES:
                r.c["own_plus10_stores"] += 1
                h = helpers.get(e)
                defs = [d for d, _ in h] if h else []
                others = [x for x in sorted(body) if (A.ins[x][1] or "").split(",")[0].strip() == m[1]
                          and A.ins[x][0] not in ("cmp", "test", "push", "pop") and x not in defs]
                ok = bool(h) and all(r2s(d) == t and t.split(",")[0].split()[-1] == m[1] for d, t in h) and not others
                r.c["plus10_base_path"] += int(ok)
                r.c["bad"] += int(not ok)
                r.note("  %s 0x%08X %s %s; base %s%s" % (nm(e), va, mn, ops, h, "" if ok else " other writes %s" %
                                                         ["0x%08X" % x for x in others]))
    r.c["bodies"] = len(helpers) + len(PLANNERS)
    r.c["bad"] += r.c["pathplan_ctx10_stores"] + r.c["pathplan_ctx10_lea"]
    G = graph2(list(PLANNERS), stop=STOPS)
    deeper = [(e, va) for e, v in G.items() if e not in PLANNERS for va in sorted(v[2])
              if memop(A.ins[va][1]) and memop(A.ins[va][1])[2] == 0x10 and A.ins[va][0].split()[0] in WRITES]
    r.c["planner_graph_functions"] = len(G)
    r.c["deeper_plus10_stores"] = len(deeper)
    r.c["deeper_plus10_functions"] = len(set(e for e, _ in deeper))
    r.c["deeper_stack_arg"] = sum(1 for e, va in deeper if memop(A.ins[va][1])[1] == "ebp")
    for e, va in deeper:
        r.note("  deeper %s 0x%08X %s %s" % (nm(e), va, A.ins[va][0], A.ins[va][1]))
    bad += r.done()

    # README 63: the 22 sites
    r = Rep("stores", "pathR63_3c")
    for site, cls, iv, text, why in B3C:
        got = r2s(site)
        chk = r2s(iv)
        ok = text in chk and "0x3c" in got
        r.c[cls] += 1
        r.c["bad"] += int(not ok)
        r.note("  0x%08X %-28s %-38s %s: %s [0x%08X %s]%s" % (site, nm(site), got, cls, why, iv, chk,
                                                            "" if ok else " MISMATCH"))
    r.c["sites"] = len(B3C)
    bad += r.done()

    # search 14, 34: writers of +0x90 and +0x91
    r = Rep("stores", "search14_34_plus90")
    ws = [x for x in stores(A) if x[4] != "esp" and x[5] <= 0x91 and x[5] + x[3] > 0x90]
    for va, mn, ops, w, base, off in ws:
        v = ival(ops)
        inmod = PATH_MOD[0] <= va < PATH_MOD[1]
        covers91 = off <= 0x91 < off + w
        if inmod:
            r.c["path_module"] += 1
            r.note("  path 0x%08X %s %s %s value=%s" % (va, nm(va), mn, ops, v))
            if covers91 and v is not None and v > 77:
                r.c["bad"] += 1
        elif v is not None:
            b = (v >> (8 * (0x91 - off))) & 0xFF if covers91 else None
            r.c["other_imm"] += 1
            r.c["bad"] += int(b is not None and b > 77 and w == 1)
            if w == 1:
                r.note("  imm 0x%08X %s %s %s" % (va, nm(va), mn, ops))
        else:
            k = "other_reg_w%d" % w
            r.c[k] += 1
            if va >= 0x00520000 and covers91:
                r.c["other_reg_server_cover91"] += 1
                r.note("  reg 0x%08X %s %s %s" % (va, nm(va), mn, ops))
    cap = [r2s(x) for x in (0x00648E7D, 0x00648E7F, 0x00648E81)]
    r.c["byte90_cap_77"] = int(cap == ["cmp al, 0x4d", "jb 0x648e83", "mov al, 0x4d"])
    r.c["bad"] += 1 - r.c["byte90_cap_77"]
    calls = calls_of(0x00648E70)[0]
    r.c["byte90_calls"] = len(calls)
    r.c["byte90_server_calls"] = sum(1 for s in calls if s >= 0x00520000)
    r.note("PathSetByte90 calls: %s" % ", ".join("0x%08X %s %s" % (s, nm(s), args(s, 2)[1:]) for s in calls))
    r.c["stores"] = len(ws)
    bad += r.done()

    # lifecycle 11: ItemCreate's direct-call graph and the item +0x24 writers
    r = Rep("stores", "life11_item24")
    G = graph2([0x00558D90], stop=STOPS)
    r.c["itemcreate_graph"] = len(G)
    r.c["indirect"] = sum(len(v[4]) for v in G.values())
    for w, n in ((0x00558A10, "ItemGroundExpiry"), (0x00558AA0, "ItemPlaceOnGround"), (0x00554A30, "UnitRelocate"),
                 (0x00541990, "InactiveItemRestoreOne")):
        r.c["reached_" + n] = int(w in G)
        if w in G:
            r.note("  %s reached: %s" % (n, path_to(G, w)))
    r.c["ground_expiry_calls"] = len(calls_of(0x00558A10)[0])
    bad += r.done()

    # lifecycle 29: 0x200000 at DRLG room +0x28
    r = Rep("stores", "life29_room28")
    for va, (mn, ops) in sorted(A.ins.items()):
        m = memop(ops)
        if not ops:
            continue
        v = ival(ops)
        if m and m[1] != "esp" and v is not None and ((m[2] == 0x28 and m[0] == 4 and v in (0x200000, 0xFFDFFFFF))
                                                      or (m[2] == 0x2A and m[0] == 1 and v in (0x20, 0xDF))):
            r.c["mem_imm"] += 1
            r.note("  mem 0x%08X %s %s %s" % (va, nm(va), mn, ops))
            r.c["bad"] += int(va != 0x0066F232)
        dst = ops.split(",")[0].strip()
        if mn in ("test", "and", "bt") and re.match(r"^e[a-z]{2}$", dst) and v is not None and \
                (v == 0x15 if mn == "bt" else v == 0x200000):
            r.c["reg_tests"] += 1
            d = reg_before(va, dst)
            from28 = bool(d and "+ 0x28]" in d[2])
            r.c["reg_tests_from_28"] += int(from28)
            r.c["bad"] += int(from28)
            r.note("  reg 0x%08X %s %s %s; loaded %s" % (va, nm(va), mn, ops, d))
    r.c["write_r2_or_200000"] = int(r2s(0x0066F232) == "or dword [esi + 0x28], 0x200000")
    bad += r.done()

    # lifecycle 36: the champion bit 0x04 of monster data +0x16 set, 0x08 cleared
    r = Rep("stores", "life36_champion")
    for va, mn, ops, w, base, off in stores(A):
        if base == "esp" or not (off <= 0x16 < off + w):
            continue
        v = ival(ops)
        sh = 8 * (0x16 - off)
        op = mn.split()[0]
        if v is None:
            r.c["reg_writes"] += 1
            continue
        if op == "or" and (v >> sh) & 4:
            r.c["or_sets"] += 1
            r.note("  or 0x%08X %s %s; r2 %s" % (va, nm(va), ops, r2s(va)))
        elif op in ("and", "btr") and not (v >> sh) & 8:
            crt = base == "ebp" and nm(va).startswith("CRT_")
            r.c["and_clears_crt_frame" if crt else "and_clears"] += 1
            r.note("  and 0x%08X %s %s%s" % (va, nm(va), ops, " (a CRT stack frame)" if crt else ""))
        elif op == "mov":
            r.c["mov_imm"] += 1
            r.c["mov_imm_bit4"] += int(bool((v >> sh) & 4))
            r.c["mov_imm_no8"] += int(not (v >> sh) & 8)
    r.c["bad"] += int(r.c["or_sets"] != 3) + r.c["and_clears"]
    seq = [r2s(0x005A48F4), r2s(0x005A4905)]
    r.c["member_mark_after_monmarkspecial"] = int(seq == ["call 0x5a0320", "or word [eax + 0x16], 5"])
    bad += r.done()

    # lifecycle 48: bit 0x2000 into unit +0xC4
    r = Rep("stores", "life48_c4")
    V = sorted(A.ins)
    idx = {va: i for i, va in enumerate(V)}
    for va, mn, ops, w, base, off in stores(A):
        if base == "esp" or not (off <= 0xC5 < off + w):
            continue
        v = ival(ops)
        op = mn.split()[0]
        if v is not None:
            if op in ("or", "mov") and (v >> (8 * (0xC4 - off) if off <= 0xC4 else 0)) & 0x2000 and off <= 0xC4:
                r.c["mem_imm"] += 1
                isfn = T.pad_entry(v) == v
                r.c["mem_imm_code_pointer"] += int(isfn)
                r.c["bad"] += int(not isfn)
                r.note("  imm 0x%08X %s %s%s" % (va, nm(va), ops, " (a function entry)" if isfn else ""))
            elif off == 0xC5 and w == 1 and op in ("or", "mov") and v & 0x20:
                r.c["mem_imm_byte"] += 1
                r.c["bad"] += 1
            continue
        if op == "mov" and w == 4 and off == 0xC4:
            R = ops.split(",")[1].strip()
            r.c["reg_stores"] += 1
            i = idx[va]
            for j in range(i - 1, max(-1, i - 11), -1):
                m2, o2 = A.ins[V[j]]
                if o2 and o2.split(",")[0].strip() == R:
                    x = ival(o2)
                    if m2 == "or" and x is not None and x & 0x2000:
                        r.c["reg_or_2000"] += 1
                        r.note("  reg 0x%08X %s %s <- 0x%08X or %s" % (va, nm(va), ops, V[j], o2))
                        r.c["bad"] += int(va != 0x0064C097)
                    break
    bad += r.done()
    return bad


# ---------------------------------------------------------------------------------------------- masks
SIZEY_SITES = [
    # (site, class, evidence instruction, its r2 text, reading)
    (0x00581D73, "object", None, None, "ObjEvent7Thunk, an object event handler"),
    (0x00581EDC, "object", None, None, "ObjEvent7Thunk"),
    (0x00581F90, "object", None, None, "ObjEvent7Thunk"),
    (0x005820B0, "object", None, None, "ObjEvent7Thunk"),
    (0x00584628, "object", None, None, "OBJ_OperateDispatch"),
    (0x00620AA5, "any", 0x00620A9D, "call 0x620510", "UNIT_CollMarkRect: no type test; its callers decide"),
    (0x00623754, "object", 0x00623673, "cmp eax, 2", "0x00623660: returns 0 unless [ebp+0xC] is type 2"),
    (0x0062389A, "any", 0x00623893, "call 0x6209d0", "UNIT_CollUnmarkRect: no type test; its callers decide"),
    (0x00649432, "object", 0x00649420, "cmp eax, 2", "UNIT_CollMark: the type-2 branch"),
    (0x00649684, "object", 0x00649586, "sub eax, 1", "UNIT_CollUnmark: the third dispatch arm (type 2, 0x00649589)"),
]
# README 56: the eight register masks given to PathSetCollMask, each with the objdump instructions its value rests on.
# "sel" is the compiler's select `neg r; sbb r, r; and r, K; add r, B`: B or B + K (mod 2^32).
REGMASK = [
    (0x004C923E, "sel", [(0x004C9200, "and ebx,0xffffe008"), (0x004C9206, "add ebx,0x3c01")], "client"),
    (0x004C93C3, "sel", [(0x004C93B5, "and edi,0xffffe008"), (0x004C93BB, "add edi,0x3c01")], "client"),
    (0x004CD132, "table", [(0x004CD129, "mov ecx,DWORD PTR [eax*8+0x72a354]")], "client CollideType table"),
    (0x0054CBE7, "saved", [(0x0054CB5C, "mov DWORD PTR [ebp-0x4],eax"), (0x00648CD6, "mov eax,DWORD PTR [eax+0x50]")],
     "PlrReachTest: the mask PathGetCollMask (0x00648CD0) read before the test"),
    (0x0059FD7C, "table", [(0x0059FD73, "mov edx,DWORD PTR [ecx*8+0x73c724]")], "MissileCreate: g_MissileCollideTypes"),
    (0x005D9082, "sel", [(0x005D903D, "and eax,0xffffe008"), (0x005D9047, "add eax,0x3c01"),
                         (0x005D904D, "mov DWORD PTR [ebp-0x14],eax")], "Whirlwind start: the slot's last store"),
    (0x005D90DC, "sel", [(0x005D903D, "and eax,0xffffe008"), (0x005D9047, "add eax,0x3c01"),
                         (0x005D904D, "mov DWORD PTR [ebp-0x14],eax")], "Whirlwind start, second restore"),
    (0x005D94FF, "sel", [(0x005D94B8, "and eax,0xffffe008"), (0x005D94BD, "add eax,0x3c01"),
                         (0x005D94C6, "mov DWORD PTR [ebp+0xc],eax")], "WhirlwindEnd: the argument slot reused"),
]
MONTESTMASK = [(0x006484B4, "mov eax,0x1804"), (0x006484C7, "and eax,0xfffff800"), (0x006484CC, "add eax,0x3c01")]


# Monster units passed to UNIT_CollUnmarkRect: the AI function's unit (EDX) kept in ESI to the call
UNMARK_MON = [(0x005EE3C0, 0x005EE3CC, 0x005EE452, "AiWussie"), (0x005EF620, 0x005EF62E, 0x005EF6B7, "AiBaalToStairs")]


def chk_masks():
    bad = 0
    A = S.asm()
    # README 38, search 5: the type flags at path +0x34
    r = Rep("masks", "pathR38_S5_typeflags")
    fl = S.dwords(0x006EB690, 17)
    r.c["flags2_xor_flags13"] = fl[2] ^ fl[13]
    r.c["bad"] += int(fl[2] ^ fl[13] != 0x100)
    r.note("g_PathTypeFlags: %s" % " ".join("%d:%X" % (i, x) for i, x in enumerate(fl)))
    G = graph2(list(PLANNERS), stop=STOPS)
    gv = {va: e for e, v in G.items() for va in v[2]}
    r.c["planner_graph"] = len(G)
    r.c["planner_graph_indirect"] = sum(len(v[4]) for v in G.values())
    for va, (mn, ops) in sorted(A.ins.items()):
        m = memop(ops)
        if not m or mn not in ("test", "and", "bt", "or", "cmp"):
            continue
        v = ival(ops)
        if v is None or not (mn in ("test", "bt") or (mn == "and" and v in (0x100, 0x200, 0x300, 1, 2, 3))):
            continue
        if (m[2] == 0x34 and m[0] >= 2 and (v & 0x300 if mn != "bt" else v in (8, 9))) or \
                (m[2] == 0x35 and (v & 3 if mn != "bt" else v in (0, 1))):
            r.c["text_tests_100_200"] += 1
            r.c["planner_graph_tests"] += int(va in gv)
            r.note("  0x%08X %s %s %s%s" % (va, nm(va), mn, ops, " (planner graph)" if va in gv else ""))
            r.c["bad"] += int(va in gv and not (v == 0x200 and va == 0x0064FED5))
    for va in sorted(gv):
        mn, ops = A.ins[va]
        m = memop(ops) or (re.search(r"\+0x3[45]\]", ops or "") and (0, "", 0x34))
        if m and re.search(r"\+0x3[45]\]", ops or ""):
            r.c["planner_graph_34_operands"] += 1
            r.note("  graph 0x%08X %s %s %s" % (va, nm(va), mn, ops))
    r.c["abs_refs_flags"] = len(T.raw(0x006EB690)[2])
    bad += r.done()

    # README 56, 76, 79: move masks through PathSetCollMask, the tables, the creation and PATH_MonTestMask
    r = Rep("masks", "pathR56_mask8000")
    calls = calls_of(0x00648CE0)[0]
    for s in calls:
        a = args(s, 2)
        v = T.imm(a[1]) if a and len(a) > 1 else None
        if v is not None:
            r.c["imm_args"] += 1
            r.c["bad"] += int(bool(v & 0x8000))
        else:
            r.c["reg_args"] += 1
    rm = {x[0]: x for x in REGMASK}
    r.c["bad"] += int(sorted(rm) != sorted(s for s in calls if T.imm((args(s, 2) or [0, 0])[1]) is None))
    for site, kind, ev, why in REGMASK:
        ok = all((A.ins.get(va) and "%s %s" % A.ins[va] == t) for va, t in ev)
        r.c["reg_" + kind] += 1
        r.c["bad"] += int(not ok)
        vals = ""
        if kind == "sel":
            k, b = (int(ev[0][1].split(",")[1], 16), int(ev[1][1].split(",")[1], 16))
            vv = {b, (b + k) & 0xFFFFFFFF}
            r.c["sel_bit8000"] += sum(1 for x in vv if x & 0x8000)
            vals = " values %s" % sorted("%X" % x for x in vv)
        r.note("  reg 0x%08X %s %s: %s%s%s" % (site, nm(site), kind, why, vals, "" if ok else " MISMATCH"))
    r.c["bad"] += r.c["sel_bit8000"]
    r.c["calls"] = len(calls)
    for tab, n in ((0x0073C720, "server"), (0x0072A350, "client")):
        ent = S.dwords(tab, 18)
        masks = ent[1::2][:9]
        r.c["table_%s_bit8000" % n] = sum(1 for x in masks if x & 0x8000)
        r.c["bad"] += r.c["table_%s_bit8000" % n]
        r.note("  table 0x%08X %s masks %s" % (tab, n, " ".join("%X" % x for x in masks)))
    ct = [int(x.get("CollideType") or 0) for x in S.tsv("missiles")]
    r.c["missiles_rows"] = len(ct)
    r.c["missiles_collidetype_max"] = max(ct)
    r.c["bad"] += int(max(ct) > 8)
    comp = [r2s(x) for x in (0x004C93B5, 0x004C93BB)]
    r.c["client_computed_1c09_3c01"] = int(comp == ["and edi, 0xffffe008", "add edi, 0x3c01"])
    ok = all("%s %s" % A.ins[va] == t for va, t in MONTESTMASK)
    mv = {0x1804, 0x3C01, (0x3C01 + 0xFFFFF800) & 0xFFFFFFFF}
    r.c["montestmask_values"] = len(mv) if ok else 0
    r.c["montestmask_imm_8000"] = sum(1 for x in mv if x & 0x8000) + int(not ok)
    r.note("  PATH_MonTestMask returns %s" % sorted("%X" % x for x in mv))
    r.c["bad"] += r.c["montestmask_imm_8000"]
    for va, mn, ops, w, base, off in stores(A, 0x00649D00, 0x00649F00):
        if off == 0x50:
            r.c["create_50_stores"] += 1
            r.note("  create 0x%08X %s %s" % (va, mn, ops))
    ws = [x for x in stores(A) if x[5] == 0x50 and x[3] == 4 and x[4] != "esp" and x[1].split()[0] == "mov"]
    r.c["text_50_dword_movs"] = len(ws)
    r.c["text_50_reg_movs"] = sum(1 for x in ws if ival(x[2]) is None)
    pm = [x for x in ws if ival(x[2]) is None and PATH_MOD[0] <= x[0] < PATH_MOD[1]]
    r.c["text_50_reg_movs_path_module"] = len(pm)
    for x in pm:
        r.note("  path-module reg mov 0x%08X %s %s; source %s" % (x[0], nm(x[0]), x[2], reg_before(x[0], x[2].split(",")[1].strip())))
    bad += r.done()

    # README 17: UNIT_GetSizeY's ten calls
    r = Rep("masks", "pathR17_sizey")
    calls = calls_of(0x006205A0)[0]
    r.c["calls"] = len(calls)
    r.c["bad"] += int(sorted(calls) != sorted(s for s, _, _, _, _ in SIZEY_SITES))
    tab = S.dwords(0x0062062C, 6)
    r.c["sizey_monster_reads_ms2_09"] = int(tab[1] == 0x006205E0 and r2s(0x006205EC) == "movsx eax, byte [eax + 9]")
    for s, cls, ev, txt, why in SIZEY_SITES:
        r.c[cls] += 1
        ok = ev is None or txt in r2s(ev)
        r.c["bad"] += int(not ok)
        r.note("  0x%08X %-30s %-6s %s%s" % (s, nm(s), cls, why, "" if ok else " MISMATCH"))
    for e, mv, site, n in UNMARK_MON:
        w = no_write(mv + 1, site, "esi")
        ok = r2s(mv) == "mov esi, edx" and not w and r2s(site - 1) == "push esi"
        r.c["contra_monster_unmark"] += int(ok)
        r.note("  CONTRA %s: unit EDX kept in ESI 0x%08X..0x%08X, UNIT_CollUnmarkRect(ESI) at 0x%08X%s" %
               (n, mv, site, site, "" if ok else " (unverified: %s)" % w))
    mr = calls_of(0x00620A70)[0]
    ur = calls_of(0x00623830)[0]
    r.c["markrect_callers"] = len(mr)
    r.c["unmarkrect_callers"] = len(ur)
    r.c["markrect_client_callers"] = sum(1 for s in mr if s < 0x00520000)
    r.c["unmarkrect_client_callers"] = sum(1 for s in ur if s < 0x00520000)
    bad += r.done()

    # README 77: the MonStats2 flag index at each flag-test call
    r = Rep("masks", "pathR77_unflatdead")
    calls = calls_of(0x004638A0)[0]
    r.c["calls"] = len(calls)
    idx14 = []
    for s in calls:
        e = T.pad_entry(s)
        d = reg_before(s, "edx", entry=e)
        k, how = None, ""
        if d and d[1] == "mov":
            k = T.imm(d[2].split(",")[1].strip())
            how = "mov"
        elif d and d[1] == "lea":
            m = re.match(r"edx, \[(e[a-z]{2}) \+ (0x[0-9a-f]+|\d+)\]", d[2])
            if m:
                base, how = zero_or_cmp(e, d[0], m.group(1))
                k = None if base is None else base + int(m.group(2), 0)
        if k is None:
            r.c["unresolved"] += 1
            r.c["bad"] += 1
        r.c["index_%02X" % k if k is not None else "index_none"] += 1
        if k == 0x14:
            idx14.append(s)
        if d and d[1] != "mov":
            r.note("  0x%08X %s edx %s -> index %s (%s)" % (s, nm(s), d[2], k, how))
    r.c["index14_sites"] = len(idx14)
    r.c["bad"] += int(idx14 != [0x004648AB])
    up = calls_of(0x00464860)[0]
    r.c["flatdrawtest_calls"] = len(up)
    r.c["bad"] += int(up != [0x004DDAD6])
    r.note("index 0x14 at %s; UnitFlatDrawTest called at %s" % (["0x%08X" % x for x in idx14], ["0x%08X" % x for x in up]))
    for va, (mn, ops) in sorted(A.ins.items()):
        m = memop(ops)
        v = ival(ops)
        if m and v is not None and (mn in ("test", "bt") or (mn == "and" and v in (0x10, 0x100000))) and (
                (m[2] == 6 and m[0] == 1 and v & 0x10) or (m[2] == 4 and m[0] == 4 and v & 0x100000 and mn != "bt")
                or (mn == "bt" and m[2] == 4 and v == 0x14)):
            r.c["direct_bit_tests"] += 1
            r.note("  direct 0x%08X %s %s %s" % (va, nm(va), mn, ops))
    bad += r.done()

    # README 41: the types the server's PathSetType calls give, by owner
    r = Rep("masks", "pathR41_types")
    calls = calls_of(0x00648CF0)[0]
    srv = [s for s in calls if s >= 0x00520000]
    r.c["calls"], r.c["server"] = len(calls), len(srv)
    for s in srv:
        a = args(s, 2)
        n = nm(s)
        v = T.imm(a[1]) if a and len(a) > 1 else None
        missile = "MissCb" in n or "BlessedHammer" in n or s == 0x00649DBB
        if missile:
            r.c["missile_sites"] += 1
            r.c["bad"] += int(v not in (4, 10, 14))
        r.note("  0x%08X %-40s type %s%s" % (s, n, a[1] if a else "?", " (missile path)" if missile else ""))
    r.c["create_missile_arm_4"] = int([r2s(x) for x in (0x00649DA9, 0x00649DB2)] == ["sub eax, 2", "push 4"])
    bad += r.done()
    return bad


# ---------------------------------------------------------------------------------------------- p2xrefs
LIFE12_SPEC = {"CursorDrop", "DropGoldAmount", "NPC_MenuAction", "CubeDropEmptied", "BeltOverflow",
               "CorpseOverflowDrop"}   # the spec's list: CursorDrop, "an overflow", DropGoldAmount, NPC menus, the cube's


def chk_p2xrefs():
    bad = 0
    # lifecycle 12
    r = Rep("p2xrefs", "life12_placeonground")
    calls = rep_calls(r, 0x00558AA0)
    extra = sorted(set(nm(T.owner(s)[0]) for s in calls
                       if not any(k in nm(T.owner(s)[0]) for k in LIFE12_SPEC)))
    r.c["contra_unlisted_callers"] = len(extra)
    r.note("callers outside the spec's list: %s" % ", ".join(extra))
    bad += r.done()
    # frame 117
    r = Rep("p2xrefs", "frame117_flush")
    A = S.asm()
    G = graph2([0x0052D870], stop=STOPS)
    r.c["gametick_graph"] = len(G)
    r.c["indirect"] = sum(len(v[4]) for v in G.values())
    fc = calls_of(0x0052E320)[0]
    r.c["flushpackets_calls"] = len(fc)
    r.note("ClientFlushPackets called at %s" % ", ".join("0x%08X %s" % (s, nm(s)) for s in fc))
    r.c["flushpackets_reached"] = int(0x0052E320 in G)
    r.c["bad"] += r.c["flushpackets_reached"]
    send = 0x0052B330
    sc = calls_of(send)[0]
    r.c["send_calls"] = len(sc)
    for e, v in G.items():
        for s, t in v[3]:
            if t == send:
                r.c["contra_send_in_frame"] += 1
                ch, x = [], e
                while x is not None:
                    par = G[x][1]
                    site = [s2 for s2, t2 in G[par][3] if t2 == x][0] if par is not None else None
                    ch.append("0x%08X %s%s" % (x, nm(x), " @0x%08X" % site if site else ""))
                    x = par
                r.note("  direct send 0x%08X <- %s" % (s, " <- ".join(ch)))
    pk = [r2s(x) for x in (0x0053B22D, 0x0053B224)]
    r.c["send_one_byte_b0"] = int(pk == ["mov byte [ebp - 1], 0xb0", "push 1"])
    r.c["autosave_gate_883d50"] = int(r2s(0x0052D3D9) == "cmp dword [0x883d50], 0")
    bad += r.done()
    return bad


# ================================================================================================== main
CHECKS = collections.OrderedDict([("graphs", chk_graphs), ("xrefs", chk_xrefs), ("xrefs2", chk_xrefs2),
                                  ("reads", chk_reads), ("stores", chk_stores), ("masks", chk_masks),
                                  ("p2xrefs", chk_p2xrefs)])


def main(argv):
    secs = list(CHECKS) if argv[1:] == ["all"] else argv[1:]
    bad = 0
    for s in secs:
        bad += CHECKS[s]()
    print("S7a total bad=%d" % bad)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
