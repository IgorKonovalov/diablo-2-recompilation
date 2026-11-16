#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S1ne (`lane/n66ne`), part 3: MonAiInit, MonAiPreChecks, AiHostileCandidate and
MonAiForcedTarget under Ghidra's p-code emulator (ADR-0015, ADR-0021, ADR-0029) with re/ghidra_scripts/EmuBoundary.java,
compared with the models below. Ruling R2 of the plan 0066 inventory: a callee runs whole on the declared image or is an
observed boundary at which the case ends (ADR-0021); the case claims the map from its inputs to that call's registers
and stack arguments, the memory written before it and the words dumped, and nothing after the call. MonAiInit's two
indirect calls are observed at the call instructions themselves (ADR-0029 (c)): 0x005B0F18 `call [row+4]` (the row's
init) and 0x005B0F30 `call [0x006CC34C]` (the KERNEL32 IsBadCodePtr import, the new think pushed).

    python3 -I tools/ai_s1ne3_emu.py cases [--dir D]    write D/s1ne3.cases, D/s1ne3.mem and the zeroed table images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s1ne3.cases D/s1ne3.mem > D/s1ne3.out
    python3 -I tools/ai_s1ne3_emu.py check [--dir D]    compare, account for every traced access, run the controls
    python3 -I tools/ai_s1ne3_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66ne/s1ne/run3. Every case draw comes from random.Random("n66ne3-<family>"); 200 cases a family, 400 for hcand.

The declared image is tools/ai_s1ne_emu.py's (tools/ai_s1e_emu.py's plus the DataTables +0x0D4 mask array). Image
constants read unwritten (traced reads accounted by range): g_BitMask32 0x006CE268; the AI class rows 0x0073CA18
(0x94 x 16 bytes) and state rows 0x0073D358 (18 x 16), read by MonAiEntryGet, transcribed by this tool from the pinned
game.exe's .data (PE section table, no other parse); LevelIsTown's jump table 0x006426C0 and index bytes 0x006426C8
(.text, 109 bytes; the town ids 1, 40, 75, 103, 109 as tools/combat_s5e3_emu.py); the forced-kind jump table
0x005DD7D8 (.text, 4 dwords).

Families (function; inventory rows, m = monsters-ai-machinery.md, r = monsters-ai-README.md):
  init    0x005B0E00 MonAiInit (r29, r31): MonAiEntryGet, the gate 0x00623470, AiCtlParamsFree 0x0058EDE0,
          MONSTATS_GetRecord, MonStats2Rec, UNIT_HasState run whole; observe 0x005B0F18 and 0x005B0F30
  prechk  0x005B10E0 MonAiPreChecks (r39): UNIT_HasState, MonAiOpenDoor 0x005B0F50 to its collision read,
          MonAiKeepNear 0x005B0FF0 (MonModeAllowed, GameFindUnit, UnitIsDead, AiDistUnits, MonAiPathOverride run whole);
          observe MonAiIdle 0x005DE080, 0x00648EB0, MonAiStepAway 0x005DEFE0, MonAiWanderNearUnit 0x005DF530
  hcand   0x005DC970 AiHostileCandidate (m16, m52): UnitIsDead, UnitGetRoom, RoomIsTown, 0x00451F30, UNIT_HasState,
          RNG_Range, UnitsHostile run whole; observe InMeleeRange 0x00622C40
  forced  0x005DD610 MonAiForcedTarget (m13, m51): the kind and guid getters, GameFindUnit, AiDistUnits, UnitAlignGet,
          RNG_RangePow2, UnitIsDead, MonForcedTargetClear, UnitGetSubX/Y, UnitGetRoom run whole; observe
          UnitLineBlocked 0x00622AA0, MonAlignSet 0x005543B0, AiUnitSearch 0x005DD0B0, LogicRegionIdAt 0x0061B130

Controls as tools/ai_s1ne_emu.py (every named test reversed alone, every ordered compare's strictness switched alone;
a control must separate some case and pass none). Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ai_s1e_emu as S  # noqa: E402
import ai_s1ne_emu as N  # noqa: E402
from ai_s1e_emu import DT, GAME, E, u32, s32, pick  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66ne", "s1ne", "run3")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
NCASES = 200
CLS_ROWS, ST_ROWS = 0x0073CA18, 0x0073D358
DEFAULT_THINK = 0x005B0CD0
TOWNS = (1, 40, 75, 103, 109)
CONST_READS = N.CONST_READS + ((CLS_ROWS, 0x94 * 16, "AI class rows 0x0073CA18"),
                               (ST_ROWS, 18 * 16, "AI state rows 0x0073D358"),
                               (0x006426C0, 8 + 0x6D, "LevelIsTown's jump table and index bytes"),
                               (0x005DD7D8, 0x10, "MonAiForcedTarget's kind jump table"))
EBP = 0x7FEFFFFC                            # EBP after `push ebp; mov ebp, esp` (entry ESP 0x7FF00000)
INIT_BLK = EBP - 0x28
FORCED_BLK = EBP - 0x2C
# observe address -> (registers compared, stack dwords compared, whether [ESP] is a return address)
OBS = {0x005B0F18: (("ecx", "edx"), 1, False), 0x005B0F30: ((), 1, False),
       0x005DE080: (("ecx", "edx"), 1, True), 0x00648EB0: ((), 1, True), 0x005DEFE0: (("ecx", "edx"), 3, True),
       0x005DF530: (("ecx", "edx"), 2, True), 0x00622C40: ((), 3, True), 0x00622AA0: ((), 3, True),
       0x005543B0: (("ecx", "dl"), 1, True), 0x005DD0B0: (("ecx", "edx"), 3, True), 0x0061B130: ((), 3, True)}
FNS = {"init": 0x005B0E00, "prechk": 0x005B10E0, "hcand": 0x005DC970, "forced": 0x005DD610}
FAMILIES = tuple(FNS)
NSTACK = {"init": 2, "prechk": 1, "hcand": 1, "forced": 4}
FATAL = "fatal"
POOLFREE = "pool free"
_SIZEX = N.sizex


def sizex3(m, u):                           # UNIT_GetSizeX with its type-3 case: the missile record 0x0046ACE0,
    if m.r32(u) == 3:                       # none while DataTables +0xB6C (the count) is 0 as declared: size 0
        if s32(m.r32(DT + 0xB6C)) > 0:
            raise ValueError("type 3 with a missile table")
        return 0
    return _SIZEX(m, u)


N.sizex = sizex3                            # this process only; tools/ai_s1ne_emu.py's file is unchanged


def exe_rows():
    """{address: dword} for the class and state rows, from game.exe's .data (section table: name, VA, raw pointer)."""
    with open(EXE, "rb") as f:
        b = f.read()
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    opt = struct.unpack_from("<H", b, pe + 20)[0]
    sec = pe + 24 + opt
    for i in range(nsec):
        name = b[sec + 40 * i:sec + 40 * i + 8].rstrip(b"\0")
        va, raw = struct.unpack_from("<I4xI", b, sec + 40 * i + 12)
        if name == b".data":
            def rd(a):
                return struct.unpack_from("<I", b, raw + a - (0x400000 + va))[0]
            return {a: rd(a) for a in range(CLS_ROWS, ST_ROWS + 18 * 16, 4)}
    raise SystemExit("no .data in " + EXE)


ROWS = exe_rows()


def row(addr):                              # (kind, init, think, alt)
    return tuple(ROWS[addr + 4 * i] for i in range(4))


# ---- callee maps ----

def entry(e, m, U, st):                     # MonAiEntryGet, tools/ai_s1ne_emu.py's map (its controls named "entry …")
    st = u32(st)
    md = m.r32(U + 0x14) if U and m.r32(U) == 1 else 0
    rec = m.r32(md) if md else 0
    if st != 0:
        if st in (10, 11, 12):
            if N.gate(E(m), s32(m.r32(U + 4)) if U else -1):
                return u32(ST_ROWS + 16 * st)
        else:
            return u32(ST_ROWS + 16 * s32(st))
    w = m.r16(rec + 0x1E)
    return CLS_ROWS + 16 * S.s16(w) if S.s16(w) >= 0 and w < 0x94 else CLS_ROWS


def obs(pc, regs, args, site=None, blk=None):
    return ("o", pc, regs, args, site, blk)


def m_init(e, a):                           # MonAiInit(G, U; ctl, state)
    m, G, U, ctl, st = e.m, a["G"], a["U"], a["ctl"], a["state"]
    if e.t("state 54", S.hasstate(m, U, 0x36)):
        return FATAL
    if not e.t("G U ctl", G and U and ctl):
        return None
    if not e.c("state<18", s32(st), "<", 18):
        e.tag("state >= 18: return")
        return None
    if not e.t("monster", m.r32(U) == 1):
        return None
    cls = m.r32(U + 4)
    if not e.c("class<count", s32(cls), "<", S.ms_count(m)):
        e.tag("class past the count: state 1")
        st = 1
    if e.t("think!=0", m.r32(ctl + 4) != 0):
        cur = entry(e, m, U, m.r32(ctl))
        _, _, think, alt = row(cur)
        if e.t("think=row think", m.r32(ctl + 4) == think) and e.t("alt!=0", alt != 0):
            e.tag("alt bridge")
            m.w32(ctl, st)
            m.w32(ctl + 4, alt)
            return None
        e.tag("think set, no bridge")
    for off in (0x14, 0x18, 0x1C):
        m.w32(ctl + off, 0)
    md = m.r32(U + 0x14)                    # AiCtlParamsFree(G, U): MonsterData's own control, not ctl
    c2 = m.r32(md + 0x28) if md else 0
    if c2 and e.t("params", m.r32(c2 + 0x24) != 0):
        e.tag("a parameter record: the pool free")
        return POOLFREE
    r = entry(e, m, U, st)
    _, init, think, alt = row(r)
    if e.t("init!=0", init != 0):
        rec, r2 = S.ms_rec(m, cls), N.ms2rec(m, cls)
        if not e.t("records", rec != 0 and r2 != 0):
            e.tag("init row, a record missing: return")
            return None
        e.tag("init call")
        blk = struct.pack("<10I", ctl, 0, 0, 0, 0, 0, 0, rec, r2, 0)[:0x24]
        return obs(0x005B0F18, {"ecx": G, "edx": U}, [INIT_BLK], blk=blk)
    if not e.t("think from row", think != 0):
        think = DEFAULT_THINK
        e.tag("default think")
    m.w32(ctl, st)
    m.w32(ctl + 4, think)
    e.tag("IsBadCodePtr call")
    return obs(0x005B0F30, {}, [think])


def allowed(m, cls, mode):                  # 0x0046C140 MonModeAllowed(cls, mode)
    rec = S.ms_rec(m, cls)
    if rec == 0:
        return 0
    r2 = N.ms2rec(m, cls)
    if r2 == 0:
        return 0
    return m.r8(r2 + 0xF0 + (mode >> 3)) & (1 << (mode & 7))


def m_prechk(e, a):                         # MonAiPreChecks(G, U; ctx)
    m, G, U, ctx = e.m, a["G"], a["U"], a["ctx"]
    if e.t("state 21", S.hasstate(m, U, 0x15)):
        return obs(0x005DE080, {"ecx": G, "edx": U}, [3], site=0x005B1100)
    rec = m.r32(ctx + 0x1C)                 # MonAiOpenDoor
    if e.t("opendoors", m.r8(rec + 0x0C) & 8):
        return obs(0x00648EB0, {}, [m.r32(U + 0x2C)], site=0x005B0F77)
    ctl = m.r32(ctx)                        # MonAiKeepNear
    if not e.t("keep!=-1", m.r32(ctl + 0x0C) != 0xFFFFFFFF):
        e.tag("no unit to keep near")
        return 0
    if not e.t("mode 2 allowed", allowed(m, s32(m.r32(U + 4)), 2)):
        e.tag("mode 2 not allowed: cleared")
        m.w32(ctl + 0x0C, 0xFFFFFFFF)
        return 0
    o = S.findunit(m, G, m.r32(ctl + 0x10), m.r32(ctl + 0x0C))
    if not e.t("found", o != 0):
        e.tag("not found: cleared")
        m.w32(ctl + 0x0C, 0xFFFFFFFF)
        return 0
    if e.t("dead", S.isdead(m, o)):
        e.tag("dead: cleared")
        m.w32(ctl + 0x0C, 0xFFFFFFFF)
        return 0
    d = s32(N.m_adu(E(m), {"A": U, "B": o}))
    if not e.c("d>1", d, ">", 1):
        if e.t("player", m.r32(ctl + 0x10) == 0):
            e.tag("near a player: StepAway")
            return obs(0x005DEFE0, {"ecx": G, "edx": U}, [o, 0x13, 1], site=0x005B109C)
    if not e.c("d>20", d, ">", 20):
        e.tag("within 20: 0")
        return 0
    e.tag("past 20: override, WanderNearUnit")
    N.m_ovr(E(m), {"U": U, "type": 7, "param": 0, "byte": 0x28})
    return obs(0x005DF530, {"ecx": G, "edx": U}, [o, 0x13], site=0x005B10D1)


def room_town(m, room):                     # 0x0061AB00 RoomIsTown, RoomLevelId, LevelIsTown
    if room == 0:
        return 0
    lvl = m.r32(m.r32(m.r32(room + 0x10) + 0x58) + 0x1D0)
    return 1 if lvl in TOWNS else 0


def m_hcand(e, a):                          # AiHostileCandidate(EDI searcher, ESI cand; G)
    m, A, C, G = e.m, a["A"], a["C"], a["G"]
    if not e.t("searcher 0/1", A and 0 <= s32(m.r32(A)) <= 1):
        return 0
    if not e.t("cand 0/1", C and 0 <= s32(m.r32(C)) <= 1):
        return 0
    if e.t("cand dead", S.isdead(m, C)) or e.t("searcher dead", S.isdead(m, A)):
        return 0
    if e.t("town", room_town(m, S.unit_room(m, C))):
        e.tag("candidate in town")
        return 0
    if not e.t("c4 bit 2", m.r32(C + 0xC4) & 4):
        e.tag("c4 bit 2 clear")
        return 0
    if e.t("state 146", S.hasstate(m, C, 0x92)):
        if e.t("cand player", m.r32(C) == 0):
            r = S.rng_range(m, C + 0x20, 100)
            e.names.add("draw<80")
            if e.c("draw<80", r, "<", 80):
                e.tag("player, draw below 80: melee test")
                return obs(0x00622C40, {}, [A, C, 0], site=0x005DCA0D)
            e.tag("player, draw 80 or more")
        else:
            e.tag("monster with state 146: melee test")
            return obs(0x00622C40, {}, [A, C, 0], site=0x005DC9E8)
    h = S.hostile(m, G, A, C)
    e.tag("hostile %d" % (1 if h else 0))
    return h


def m_forced(e, a):                         # MonAiForcedTarget(EAX G, ESI U; p8, flag, outU, outD)
    m, G, U = e.m, a["G"], a["U"]
    p8, flag, ou, od = a["s"]
    md = m.r32(U + 0x14) if U and m.r32(U) == 1 else 0
    if not e.t("monster", U and m.r32(U) == 1):
        return 0
    kind = m.r32(md + 0x38) if md else 0
    if not e.t("kind!=0", kind != 0):
        return 0

    def clear():
        if md:
            m.w32(md + 0x38, 0)
            m.w32(md + 0x34, 0)
        return 0

    if not e.t("kind 1-4", 1 <= kind <= 4):
        e.tag("kind past 4: cleared")
        return clear()
    if kind == 3:
        al = s32(S.align(m, U))
        r = S.step(m, U + 0x20) & 1         # RNG_RangePow2(seed, 2)
        e.tag("kind 3, alignment %s, draw %d" % (al if al in (0, 1, 2) else "other", r))
        new = None
        if e.t("align=1", al == 1):
            new = 2 if e.t("draw!=0", r != 0) else 0
        elif e.t("draw!=0", r != 0):
            if e.t("align=0", al == 0):
                new = 2
            elif e.t("align=2", al == 2):
                new = 0
        if new is not None:
            return obs(0x005543B0, {"ecx": U, "dl": new}, [1], site=0x005DD6FA)
        if e.t("flag", flag != 0):
            blk = struct.pack("<4I", 0, 0x7FFFFFFF, 0, 0x7FFFFFFF)
            return obs(0x005DD0B0, {"ecx": G, "edx": U}, [FORCED_BLK, 0, 6], site=0x005DD762, blk=blk)
        x, y = N.upos(m, U)
        room = S.unit_room(m, U)
        return obs(0x0061B130, {}, [room, x, y], site=0x005DD728)
    t = {1: 0, 2: 1, 4: 3}[kind]
    e.tag("kind %d" % kind)
    o = S.findunit(m, G, t, m.r32(md + 0x34))
    if not e.t("found", o != 0):
        e.tag("not found: cleared")
        return clear()
    d = N.m_adu(E(m), {"A": o, "B": U})
    if e.t("flag", flag != 0):
        e.tag("line test")
        return obs(0x00622AA0, {}, [o, U, 4], site=0x005DD67D)
    ty = s32(m.r32(o))
    if not e.t("type 0,1,3", 0 <= ty <= 1 or ty == 3):
        return clear()
    if 0 <= ty <= 1 and e.t("target dead", S.isdead(m, o)):
        e.tag("target dead: cleared")
        return clear()
    e.tag("taken")
    m.w32(ou, o)
    m.w32(od, d)
    return 1


MODELS = {"init": m_init, "prechk": m_prechk, "hcand": m_hcand, "forced": m_forced}


# ---- the case writer ----

def mon(w, rnd, states=(), al=0):
    U = w.unit(typ=1, al=al, states=states)
    return U


def gen_init(w, m, rnd):
    U = w.unit(typ=pick(rnd, 1, 1, 1, 1, 1, 1, 0, 3), states=(0x36,) if rnd.randrange(30) == 0 else ())
    if m.r32(U) == 1:
        md = m.r32(U + 0x14)
        p = m.alloc(0x40)
        m.w32(md, p)
        inits = [i for i in range(0x94) if row(CLS_ROWS + 16 * i)[1]]
        m.w16(p + 0x1E, pick(rnd, 0, 1, 0x93, 0x94, -1, rnd.randrange(0x94), pick(rnd, *inits), pick(rnd, *inits)))
        if rnd.randrange(8) == 0:
            m.w32(U + 4, pick(rnd, S.ms_count(m), S.ms_count(m) + 1, 0x300, 0xFFFFFFFF))
        N.gate_bits(w, m.r32(U + 4))
        c2 = m.r32(md + 0x28)
        if rnd.randrange(12) == 0:          # a two-record circular parameter list: the free reaches the pool
            r1, r2 = m.alloc(0x1C), m.alloc(0x1C)
            for x, y in ((r1, r2), (r2, r1)):
                m.w32(x, y)
                m.w32(x + 4, y)
            m.w32(c2 + 0x20, r1)
            m.w32(c2 + 0x24, pick(rnd, r1, r2))
        if rnd.randrange(10) == 0:
            m.w32(md + 0x28, 0)
        r2 = N.ms2rec(m, m.r32(U + 4))
        if r2 == 0 and rnd.randrange(2) and S.ms_rec(m, m.r32(U + 4)):
            m.w16(S.ms_rec(m, m.r32(U + 4)) + 0x18, 0)
    ctl = m.alloc(0x40)
    for off in range(0, 0x40, 4):
        m.w32(ctl + off, rnd.getrandbits(32))
    alts = [i for i in range(18) if row(ST_ROWS + 16 * i)[3]] + \
           [i - 0x94 for i in range(0x94) if row(CLS_ROWS + 16 * i)[3]]
    cur = pick(rnd, rnd.randrange(18), rnd.randrange(18), pick(rnd, *alts), pick(rnd, *alts), -rnd.randrange(1, 0x95))
    m.w32(ctl, u32(cur))
    k = rnd.randrange(4)
    if k == 0:
        m.w32(ctl + 4, 0)
    elif k in (1, 2) and m.r32(U) == 1:
        m.w32(ctl + 4, row(entry(E(m.copy()), m.copy(), U, cur))[2])
    st = pick(rnd, 0, 0, 0, 0, 1, 2, 3, 3, 4, 5, 6, 10, 11, 11, 12, 13, 16, 16, 17, 18, 19, 0x36, 0x7FFFFFFF,
              rnd.randrange(18), rnd.randrange(18), -rnd.randrange(1, 0x95))
    G = pick(rnd, GAME, GAME, GAME, GAME, GAME, GAME, GAME, 0)
    if rnd.randrange(20) == 0:
        ctl = 0
    if rnd.randrange(25) == 0:
        U = 0
    dumps = []
    if ctl:
        dumps.append((ctl, 0x20))
    if U and m.r32(U) == 1 and m.r32(m.r32(U + 0x14) + 0x28):
        dumps.append((m.r32(m.r32(U + 0x14) + 0x28) + 0x20, 8))
    return {"G": G, "U": U, "ctl": ctl, "state": u32(st)}, (G, U, [ctl, u32(st)], {}), dumps


def gen_prechk(w, m, rnd):
    U = w.unit(typ=1, states=(0x15,) if rnd.randrange(6) == 0 else ())
    pc = m.alloc(0x40)
    m.w32(m.r32(U + 0x14) + 0x2C, pc)
    N.gate_bits(w, m.r32(U + 4))
    ctl = m.alloc(0x40)
    rec = S.ms_rec(m, m.r32(U + 4)) or m.alloc(0x20)
    m.w8(rec + 0x0C, pick(rnd, 0, 0, 0, 0, 8, rnd.getrandbits(8) & 0xF7, rnd.getrandbits(8)))
    ctx = m.alloc(0x28)
    m.w32(ctx, ctl)
    m.w32(ctx + 0x1C, rec)
    k = rnd.randrange(8)
    o = None
    if k == 0:
        m.w32(ctl + 0x0C, 0xFFFFFFFF)
    else:
        typ = pick(rnd, 0, 0, 0, 1, 1, 3)
        ux, uy = N.upos(m, U)
        dd = pick(rnd, 0, 1, 2, 3, 20, 21, 22, rnd.randrange(60), rnd.randrange(30))
        o = w.unit(typ=typ, mode=pick(rnd, 1, 2, 3, 0, 12, 17), x=(ux + pick(rnd, dd, -dd, 0)) & 0xFFFF,
                   y=(uy + pick(rnd, dd, -dd, rnd.randrange(-dd - 1, dd + 1))) & 0xFFFF)
        N.ms2size(w, m.r32(U + 4))
        want = pick(rnd, None, None, 1, 20, 2, 21)
        if want is not None:                # an exact distance at a compare's edge, by the x offset alone
            for dx in range(-80, 81):
                N.place(w, o, typ, (ux + dx) & 0xFFFF, uy)
                if s32(N.m_adu(E(m.copy()), {"A": U, "B": o})) == want:
                    break
        m.w32(ctl + 0x10, typ)
        m.w32(ctl + 0x0C, m.r32(o + 0x0C) if rnd.randrange(8) else u32(m.r32(o + 0x0C) + 1))
        w.hash_in(o)
    dumps = [(ctl + 0x0C, 8), (pc + 0x18, 9)]
    return {"G": GAME, "U": U, "ctx": ctx}, (GAME, U, [ctx], {}), dumps


def town_room(w, m, rnd, u):
    p = m.r32(u + 0x2C)
    if p == 0 or rnd.randrange(6) == 0:
        return
    room = m.alloc(0x20)
    a1 = m.alloc(0x60)
    lv = m.alloc(0x1E0)
    m.w32(room + 0x10, a1)
    m.w32(a1 + 0x58, lv)
    m.w32(lv + 0x1D0, pick(rnd, 1, 40, 75, 103, 109, 2, 3, 39, 41, 74, 76, 102, 104, 108, 110, 0, rnd.randrange(140)))
    m.w32(p + 0x1C, room)


def gen_hcand(w, m, rnd):
    A = w.unit(typ=pick(rnd, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 4), mode=pick(rnd, 1, 2, 3, 4, 1, 2, 0, 12, 17),
               al=pick(rnd, 0, 0, 1, 2), dead=rnd.randrange(20) == 0)
    st = (0x92,) if rnd.randrange(5) < 3 else ()
    C = w.unit(typ=pick(rnd, 0, 0, 0, 0, 1, 1, 1, 1, 2, 3), mode=pick(rnd, 1, 2, 3, 4, 5, 6, 1, 2, 3, 0, 12, 17),
               al=pick(rnd, 0, 0, 1, 2), c4=pick(rnd, 4, 4, 4, 4, 4, 4, 0, 0xFB, rnd.getrandbits(32)),
               states=st, dead=rnd.randrange(20) == 0)
    town_room(w, m, rnd, C)
    if C and rnd.randrange(5) == 0:         # a step whose low word is 79 or 80 mod 100 (s0 = 0: low = s1)
        m.w32(C + 0x20, 0)
        m.w32(C + 0x24, pick(rnd, 80, 79, 180, 79 + 100 * rnd.randrange(1, 1000)))
    if rnd.randrange(30) == 0:
        A = 0
    if rnd.randrange(30) == 0:
        C = 0
    dumps = [(C + 0x20, 8)] if C else []
    return {"A": A, "C": C, "G": GAME}, (0, 0, [GAME], {"edi": A, "esi": C}), dumps


def gen_forced(w, m, rnd):
    U = w.unit(typ=pick(rnd, 1, 1, 1, 1, 1, 1, 1, 0), al=pick(rnd, 0, 1, 1, 2, 2, 0, 3))
    md = m.r32(U + 0x14) if m.r32(U) == 1 else 0
    if md:
        kind = pick(rnd, 1, 1, 2, 2, 3, 3, 3, 4, 4, 0, 5, 0xFFFFFFFF)
        m.w32(md + 0x38, kind)
        tt = {1: 0, 2: 1, 4: 3}.get(kind, pick(rnd, 0, 1, 3))
        o = w.unit(typ=tt, mode=pick(rnd, 1, 2, 3, 0, 12, 17), dead=rnd.randrange(10) == 0)
        w.hash_in(o)
        if rnd.randrange(6) == 0:           # a unit of type 4 or 5 under the same guid, first in the bucket
            o2 = w.unit(typ=pick(rnd, 4, 5))
            m.w32(o2 + 0x0C, m.r32(o + 0x0C))
            w.hash_in(o2, typ=tt)
        m.w32(md + 0x34, m.r32(o + 0x0C) if rnd.randrange(6) else u32(m.r32(o + 0x0C) + 1))
        N.ms2size(w, m.r32(o + 4))
    outs = m.alloc(8)
    m.w32(outs, 0xAAAAAAAA)
    m.w32(outs + 4, 0xBBBBBBBB)
    flag = pick(rnd, 0, 0, 1, 2, rnd.getrandbits(32))
    p8 = rnd.getrandbits(32)
    dumps = [(U + 0x20, 8), (outs, 8)]
    if md:
        dumps.append((md + 0x34, 8))
    s = [p8, flag, outs, outs + 4]
    return {"G": GAME, "U": U, "s": s}, (0, 0, s, {"eax": GAME, "esi": U}), dumps


GENS = {"init": gen_init, "prechk": gen_prechk, "hcand": gen_hcand, "forced": gen_forced}


def gen_case(fam, rnd):
    w, m = N.world(rnd)
    a, call, dumps = GENS[fam](w, m, rnd)
    if fam in ("init", "forced"):
        dumps.append((STK_LO, STK_LEN))
    return m, a, call, dumps


STK_LO, STK_LEN = 0x7FEFFE00, 0x200


def all_cases():
    out = []
    for fam in FAMILIES:
        rnd = random.Random("n66ne3-" + fam)
        for k in range(NCASES * (2 if fam == "hcand" else 1)):
            m, a, call, dumps = gen_case(fam, rnd)
            out.append((fam, k, m, a, call, dumps))
    return out


def predict(fam, m, a, flip=None):
    mm = m.copy()
    e = E(mm, flip)
    r = MODELS[fam](e, a)
    return r, mm, e.names, e.tags


def outputs(fam, r, mm, dumps):
    ds = tuple(bytes(mm.r8(lo + i) for i in range(n)) for lo, n in dumps if lo != STK_LO)
    if r == FATAL:
        return ("fatal",)
    if r == POOLFREE:
        return ("stop", 0x0040B480)
    if isinstance(r, tuple):
        _, pc, regs, args, site, blk = r
        rr = tuple(u32(regs[k]) for k in OBS[pc][0])
        return ("obs", pc, site, rr, tuple(u32(x) for x in args), blk) + ds
    return ("ret", u32(r if r is not None else 0) if fam not in ("init",) else None) + ds


def observed(fam, g, dumps):
    p = g["line"].split()
    stk, ds = None, []
    for (lo, n), (_, b) in zip(dumps, g["d"]):
        if lo == STK_LO:
            stk = b
        else:
            ds.append(b)
    ds = tuple(ds)
    if p[3] == "STOP":
        pc = int(p[4], 16)
        return (("fatal",) if pc == 0x00408090 else ("stop", pc)), None
    if p[3] == "OBS":
        pc = int(p[4], 16)
        kv = dict(x.split("=") for x in p[6:])
        regs, nargs, hasret = OBS[pc]
        A = bytes.fromhex(g["a"])
        words = struct.unpack_from("<%dI" % (nargs + 1), A, 0)
        site = words[0] if hasret else None
        args = words[1:] if hasret else words[:nargs]
        rr = tuple((int(kv["edx"], 16) & 0xFF) if r == "dl" else int(kv[r], 16) for r in regs)
        blk = None
        if pc in (0x005B0F18, 0x005DD0B0) and stk is not None:
            lo = (INIT_BLK if pc == 0x005B0F18 else FORCED_BLK) - STK_LO
            blk = stk[lo:lo + (0x24 if pc == 0x005B0F18 else 0x10)]
        return ("obs", pc, site, rr, tuple(args), blk) + ds, None
    kv = dict(x.split("=") for x in p[3:])
    return ("ret", int(kv["eax"], 16) if fam != "init" else None) + ds, int(kv["pop"])


def mem_spec(d):
    base = N.mem_spec(d).splitlines()
    out = ["# plan 0066 batch S1ne part 3: tools/ai_s1ne_emu.py's declared image and guards, the observes below"]
    out += [x for x in base if not x.startswith("#") and not x.startswith("observe")]
    out += ["observe %08x" % a for a in sorted(OBS)]
    return "\n".join(out) + "\n"


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "s1ne3.mem"), "w") as f:
        f.write(mem_spec(d))
    with open(os.path.join(d, "s1ne3.cases"), "w") as f:
        for fam, k, m, a, call, dumps in all_cases():
            f.write("# %s %d\n" % (fam, k))
            for lo, b in m.runs():
                if S.G_DT <= lo < S.G_DT + 4:
                    continue
                f.write("w %08x %s\n" % (lo, b.hex()))
            for lo, n in dumps:
                f.write("d %08x %d\n" % (lo, n))
            ecx, edx, stack, regs = call
            for r in sorted(regs):
                f.write("r %s %08x\n" % (r, u32(regs[r])))
            f.write("call %08x %08x %08x%s\n" % (FNS[fam], u32(ecx), u32(edx), "".join(" %08x" % u32(x) for x in stack)))
    print("cases written to", d)


def cmd_check(d):
    cases = all_cases()
    got, reads, writes = N.read_out(os.path.join(d, "s1ne3.out"))
    lines, ok = [], True
    if len(got) != len(cases):
        print("S1NE3 cases=%d outputs=%d result=FAIL" % (len(cases), len(got)))
        return 1
    per = {f: {"cases": 0, "match": 0, "bad": 0, "ctl": {}, "tags": {}, "obs": {}, "ret": 0, "stop": 0}
           for f in FAMILIES}
    for (fam, k, m, a, call, dumps), g in zip(cases, got):
        P = per[fam]
        P["cases"] += 1
        r, mm, names, tags = predict(fam, m, a)
        want = outputs(fam, r, mm, dumps)
        have, pop = observed(fam, g, dumps)
        for tg in tags:
            P["tags"][tg] = P["tags"].get(tg, 0) + 1
        good = have == want
        if have[0] == "ret" and pop != 4 * NSTACK[fam]:
            good = False
        if have[0] == "obs":
            P["obs"]["%08x" % have[1]] = P["obs"].get("%08x" % have[1], 0) + 1
        P["ret"] += have[0] == "ret"
        P["stop"] += have[0] in ("fatal", "stop")
        if good:
            P["match"] += 1
        else:
            P["bad"] += 1
            if P["bad"] <= 6:
                lines.append("BAD %s %d want=%s have=%s pop=%s" % (fam, k, N._fmt(want), N._fmt(have), pop))
        for nm in names:
            try:
                r2, mm2, _, _ = predict(fam, m, a, flip=nm)
                alt = outputs(fam, r2, mm2, dumps)
            except (KeyError, ValueError, IndexError, ZeroDivisionError):
                alt = None
            c = P["ctl"].setdefault(nm, [0, 0])
            if alt != want:
                c[0] += 1
                if alt == have:
                    c[1] += 1
    for fam in FAMILIES:
        P = per[fam]
        unsep = sorted(n for n, c in P["ctl"].items() if c[0] == 0)
        passed = sorted(n for n, c in P["ctl"].items() if c[1] > 0)
        lines.append("S1NE3 %s fn=%08x cases=%d match=%d bad=%d ret=%d stop=%d controls=%d separated=%d passed=%d"
                     % (fam, FNS[fam], P["cases"], P["match"], P["bad"], P["ret"], P["stop"], len(P["ctl"]),
                        len(P["ctl"]) - len(unsep), len(passed)))
        lines.append("  OBS " + (" ".join("%s:%d" % kv for kv in sorted(P["obs"].items())) or "-"))
        lines.append("  CTL " + (" ".join("%s:%d/%d" % (n, c[0], c[1]) for n, c in sorted(P["ctl"].items())) or "-"))
        lines.append("  UNSEPARATED " + (" ".join(unsep) if unsep else "-"))
        lines.append("  TAGS " + ("; ".join("%s %d" % kv for kv in sorted(P["tags"].items())) or "-"))
        if passed:
            ok = False
            lines.append("  PASSED " + " ".join(passed))
        if P["bad"]:
            ok = False
    acc, unacc = {}, []
    for pc, addr, n, cnt in reads:
        hit = [nm for lo, ln, nm in CONST_READS if lo <= addr and addr + n <= lo + ln]
        if hit:
            acc[hit[0]] = acc.get(hit[0], 0) + cnt
        else:
            unacc.append("R %08x %08x %d %d" % (pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        unacc.append("W %08x %08x %d %d" % (pc, addr, n, cnt))
    lines.append("S1NE3 traced reads accounted: " + (", ".join("%s %d" % kv for kv in sorted(acc.items())) or "-"))
    lines.append("S1NE3 traced unaccounted: %d" % len(unacc))
    lines += ["  " + x for x in unacc[:40]]
    if unacc:
        ok = False
    lines.append("S1NE3 total cases=%d match=%d" % (sum(P["cases"] for P in per.values()),
                                                    sum(P["match"] for P in per.values())))
    lines.append("S1NE3 result=%s" % ("ok" if ok else "FAIL"))
    print("\n".join(lines))
    return 0 if ok else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir)
        return 0
    if a.cmd == "check":
        return cmd_check(a.dir)
    N.cmd_manifest(a.dir, a.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
