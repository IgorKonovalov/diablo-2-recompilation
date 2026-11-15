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
            (party 14, 22), excel accessors in the frame's own code (frame 7), stores to fixed offsets (path README
            6, 38, 63, search 5, 14, 34; frame 20, 24, 63; lifecycle 11, 29, 36, 48), immediate move masks (path
            README 56, 76, 79), readers of unflatDead and SizeY (path README 17, 77)

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


# ================================================================================================== main
CHECKS = collections.OrderedDict([("graphs", chk_graphs), ("xrefs", chk_xrefs), ("xrefs2", chk_xrefs2),
                                  ("reads", chk_reads)])


def main(argv):
    secs = list(CHECKS) if argv[1:] == ["all"] else argv[1:]
    bad = 0
    for s in secs:
        bad += CHECKS[s]()
    print("S7a total bad=%d" % bad)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
