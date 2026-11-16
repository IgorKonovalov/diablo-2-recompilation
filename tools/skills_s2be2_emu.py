#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2be part 2 (`lane/n66sb`): two catalogue routes under Ghidra's p-code emulator (ADR-0015,
ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared with the models below; plus `tail`, do 13's return read
with two tools (objdump over the whole .text and radare2), and `static`, the objdump listing of the functions run.

    python3 -I tools/skills_s2be2_emu.py cases [--dir D] [--limit N]   write D/s2ae.cases, D/s2ae.mem and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s2ae.cases D/s2ae.mem > D/s2ae.out
    python3 -I tools/skills_s2be2_emu.py check [--dir D] [--limit N]   compare, account for traced reads, controls
    python3 -I tools/skills_s2be2_emu.py tail                          do 13's single return: every way into it
    python3 -I tools/skills_s2be2_emu.py static                        objdump of the functions the cases run
    python3 -I tools/skills_s2be2_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66sb/s2be/run2. The case and check machinery is batch S2ae part 1's
(tools/skills_s2ae_emu.py: build, cmd_cases, cmd_check, cmd_manifest), pointed at this part's families in its module
state only, as S2ae parts 5-9 did; part 5's (tools/skills_s2ae5_emu.py) UNIT_GetTargetUnit model and bucket layout are
reused unchanged. Every draw comes from random.Random("n66sb-s2be2-<family>").

Declared inputs (S1e ruling 3): units, the path, the callback context and block are case memory; the Skills table
(64 rows of 0x23C) and the Missiles table (0x200 rows of 0x1A4) are spec memory: random bytes from
random.Random("n66sb-s2be2-tables") except Skills rows 44 and 48 and Missiles rows 90 and 119, which carry the shipped
.bin bytes (workspace/merged, read at case time, not copied into git). The random Skills rows keep the charge path
(+0x04 bit 2 with a state +0x80 and stat +0x54 in range) closed, so 0x006256B0 is never reached; their +0x138 calc is
at or past the declared pool size (DataTables +0x44), so SKILLS_EvalCalc returns at its bounds test.

Observed boundaries (ADR-0021; the case ends at the call, registers and stack arguments compared):
  STATE_ApplyTimed 0x0056E970 from 0x005DB1A6 (cb43), sub_0056D400_SkillNovaAtUnit 0x0056D400 from 0x005D4E53 (p36).

Families (rows: c = skills/catalogue):
  cb43  0x005DB150, do 12's per-unit callback (ECX the walker's context, EDX the unit), to STATE_ApplyTimed: the
        nine-dword block it builds on its frame and passes in ECX.                                         c43
  p36   sub_005D4DB0_SkillPrgDo36NovaAtTarget (ECX game, EDX caster; id, lvl), whole to SkillNovaAtUnit:
        UNIT_GetTargetUnit 0x00553540 (part 5's model), sub_005D3CF0_SkillSrvMissileByCharge,
        sub_00663270_MissileSpeedAtLevel (Missiles at 0x0096C794, count 0x0096C79C), SKILLS_EvalCalc 0x00646CA0;
        Skills rows 44 and 48 with their shipped bytes.                                                   c73

Controls as S2ae: every named test reversed alone, every ordered compare's strictness switched alone; `sep` counts the
cases a control changes, `passed` those the emulator still matches (must be 0); `spec_*` controls are readings the
spec states or rules out. Stdlib only, plus objdump (and r2 for `tail`).
"""
import argparse
import os
import random
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import combat_s5e_emu as p1  # noqa: E402
import skills_s2ae_emu as B  # noqa: E402
import skills_s2ae5_emu as P5  # noqa: E402
from combat_s5e_emu import u32, s32, le32, tdiv, G_DT, DT, FATAL, ALLOC, BITMASK, EXE  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sb", "s2be", "run2")
FNS = {"cb43": 0x005DB150, "p36": 0x005D4DB0}
FAMILIES = ("cb43", "p36")
NCASES = {"cb43": 1500, "p36": 5000}
POP = {"cb43": 0, "p36": 8}
OBS_TIMED, OBS_NOVA = 0x0056E970, 0x0056D400
SITE = {("cb43", OBS_TIMED): 0x005DB1AB, ("p36", OBS_NOVA): 0x005D4E58}
p1.FNS.update(FNS)

SHIPPED = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
CTX, BLK = 0x22000000, 0x22000100            # cb43: the walker's context and the caller's block
GAME, U, T, X = P5.GAME, P5.U, P5.T, P5.X      # p36: part 5's game and units (its bucket layout)
PATH_OFF = P5.PATH_OFF
SK, SK_N, SK_SZ = 0x21300000, 64, 0x23C
MI, MI_N, MI_SZ = 0x21800000, 0x200, 0x1A4
G_MIS, G_MIS_N = 0x0096C794, 0x0096C79C
CALC, CALC_N = 0x21900000, 0x40               # the calc pool (DataTables +0x40, size +0x44); never entered
NSTATES, NSTATS = 0xC0, 0x200
SHIP_SK, SHIP_MI = (44, 48), (90, 119)

TABLES = None


def shipped(name, sz, rows):
    with open(os.path.join(SHIPPED, name), "rb") as f:
        b = f.read()
    return {r: b[4 + r * sz:4 + (r + 1) * sz] for r in rows}


def tables():
    """(skills, missiles): the declared images; the shipped rows overwrite the random ones."""
    global TABLES
    if TABLES is None:
        r = random.Random("n66sb-s2be2-tables")
        sk = bytearray(r.getrandbits(8) for _ in range(SK_N * SK_SZ))
        for i in range(SK_N):
            o = i * SK_SZ
            charge = r.random() < 0.4
            sk[o + 4] = (sk[o + 4] | 4) if charge else (sk[o + 4] & ~4)
            if charge:                       # the charge path stays closed: a state or a stat out of range
                if r.random() < 0.5:
                    struct.pack_into("<h", sk, o + 0x80, r.choice([-1, NSTATES, NSTATES + 7, -300]))
                else:
                    struct.pack_into("<h", sk, o + 0x80, r.randrange(NSTATES))
                    struct.pack_into("<h", sk, o + 0x54, r.choice([-1, NSTATS, 0x7FFF]))
            struct.pack_into("<h", sk, o + 0x48, r.choice([r.randrange(MI_N), r.randrange(MI_N), 0, -1, -5,
                                                           MI_N, MI_N + 40, r.randrange(1, MI_N)]))
            struct.pack_into("<I", sk, o + 0x138, r.choice([0xFFFFFFFF, CALC_N, CALC_N + r.randrange(1 << 20)]))
        for row, b in shipped("skills.bin", SK_SZ, SHIP_SK).items():
            sk[row * SK_SZ:(row + 1) * SK_SZ] = b
        mi = bytearray(r.getrandbits(8) for _ in range(MI_N * MI_SZ))
        for row, b in shipped("missiles.bin", MI_SZ, SHIP_MI).items():
            mi[row * MI_SZ:(row + 1) * MI_SZ] = b
        TABLES = (bytes(sk), bytes(mi))
    return TABLES


def skw(row, off):
    return struct.unpack_from("<h", tables()[0], row * SK_SZ + off)[0]


def skd(row, off):
    return struct.unpack_from("<I", tables()[0], row * SK_SZ + off)[0]


def skb(row, off):
    return tables()[0][row * SK_SZ + off]


def mib(row, off):
    return tables()[1][row * MI_SZ + off]


class Case(p1.Case):
    pass


Mem = P5.Mem
rbytes = P5.rbytes


# ----------------------------------------------------------------------------------------------- cb43
def gen_cb43(rnd):
    c = Case("cb43")
    c.put(CTX, rbytes(rnd, 0x20))
    c.put(CTX + 0xC, le32(BLK))
    c.put(BLK, rbytes(rnd, 0x20))
    unit = rnd.choice([rnd.getrandbits(32), 0x20000000 + rnd.randrange(1 << 20), 0])
    c.ecx, c.edx = CTX, unit
    c.a = dict(w=dict(c.w), unit=unit)
    return c


def m_cb43(e, a):
    M = Mem(a["w"])
    blk = [M.d(BLK + 4 * k) for k in range(6)]
    e.names.update(("spec_block_order", "spec_unit_first"))
    if e.flip == "spec_block_order":          # the spec's list order {id, lvl, len, state, stat, calc} copied as is
        words = [M.d(CTX + 4), a["unit"]] + blk + [0]
    elif e.flip == "spec_unit_first":
        words = [a["unit"], M.d(CTX + 4), blk[0], blk[1], blk[2], blk[4], blk[5], blk[3], 0]
    else:
        words = [M.d(CTX + 4), a["unit"], blk[0], blk[1], blk[2], blk[4], blk[5], blk[3], 0]
    return ("obs", OBS_TIMED, tuple(words))


# ----------------------------------------------------------------------------------------------- p36
def gen_p36(rnd):
    c = Case("p36")
    guids = set()

    def gid():
        while True:
            g = rnd.choice([rnd.getrandbits(32), rnd.randrange(0x100)])
            if g not in guids and g != 0xFFFFFFFF:
                guids.add(g)
                return g
    units = {}

    def mk(base, typ, mode):
        c.put(base, rbytes(rnd, 0x100))
        g = gid()
        for off, v in ((0, typ), (0xC, g), (0x10, mode), (0xE4, 0)):
            c.put(base + off, le32(v))
        units[base] = (typ, g)
        return g
    ut = rnd.choice([0, 0, 1, 1, 3])
    ug = mk(U, ut, rnd.randrange(20))
    tt = rnd.choice([1, 1, 1, 0, 0, 4, 2, 3, 5])
    tg = mk(T, tt, rnd.choice([1, 2, 12, rnd.randrange(20)]))
    mk(X, rnd.choice([0, 1, 4]), rnd.randrange(20))
    pth = U + PATH_OFF
    c.put(U + 0x2C, le32(pth))
    c.put(pth, rbytes(rnd, 0x70))
    lookups = set()
    k = rnd.random()
    if k < 0.75:
        st, sty, sg = T, tt, tg
        if rnd.random() < 0.05:
            sg = gid()                                    # a stale guid: not found, cleared
    elif k < 0.85:
        st, sty, sg = 0, rnd.choice([0, 1]), rnd.getrandbits(32)
    elif k < 0.92:
        st, sty, sg = U, ut, ug                           # the unit itself
    else:
        st, sty, sg = X, units[X][0], units[X][1]
        if rnd.random() < 0.5:
            sty, sg = tt, tg                              # found as T, stored as X: cleared
    if st:
        lookups.add((sty, sg))
    c.put(pth + 0x58, le32(st) + le32(sty) + le32(sg))
    heads = {}
    order = list(units.items())
    rnd.shuffle(order)
    for base, (t, g) in order:
        heads.setdefault(P5.head_addr(t, g), []).append(base)
    for t, g in lookups:
        heads.setdefault(P5.head_addr(t, g), [])
    for ha, lst in heads.items():
        c.put(ha, le32(lst[0] if lst else 0))
        for i, base in enumerate(lst):
            c.put(base + 0xE4, le32(lst[i + 1] if i + 1 < len(lst) else 0))
    sid = rnd.choice([44] * 8 + [48] * 8 + [rnd.randrange(SK_N)] * 6 + [-1, SK_N, rnd.getrandbits(32)])
    lvl = rnd.choice([rnd.randint(1, 20), rnd.randint(1, 60), rnd.randint(1, 3), 0, -1, rnd.randint(-40, -2),
                      rnd.getrandbits(32), 0x7FFFFFFF, rnd.randint(1, 1 << 24)])
    c.ecx, c.edx = GAME, U
    c.args = [u32(sid), u32(lvl)]
    c.dumps = [(pth + 0x58, 12)]
    c.a = dict(w=dict(c.w), sid=s32(u32(sid)), lvl=s32(u32(lvl)), dumps=list(c.dumps))
    return c


def by_charge(e, row):
    """sub_005D3CF0_SkillSrvMissileByCharge for a row whose charge path is closed: srvmissilea (+0x48)."""
    if e.t("charge_flag", skb(row, 4) & 4) and e.c("cst_ge0", skw(row, 0x80), ">=", 0) and \
            e.c("cst_lt", skw(row, 0x80), "<", NSTATES) and e.c("cstat_ge0", skw(row, 0x54), ">=", 0) and \
            e.c("cstat_lt", skw(row, 0x54), "<", NSTATS):
        raise KeyError("the charge path is not declared")
    return skw(row, 0x48)


def speed(e, m, lvl):
    """sub_00663270_MissileSpeedAtLevel: (VelLev * lvl) / 8 (truncating) + Vel; 0 for a bad class."""
    if not e.c("m_ge0", m, ">=", 0) or not e.c("m_lt", m, "<", MI_N):
        return 0
    e.names.add("spec_floor")
    q = (mib(m, 0x9B) * lvl) >> 3 if e.flip == "spec_floor" else tdiv(s32(u32(mib(m, 0x9B) * lvl)), 8)
    return u32(q + mib(m, 0x9A))


def evalcalc(e, calc):
    """SKILLS_EvalCalc: 0 at its bounds test (unsigned) on the declared pool."""
    if e.c("calc_in", calc, "<", CALC_N):
        raise KeyError("a calc inside the pool is not declared")
    return 0


def m_p36(e, a):
    M = Mem(a["w"])
    sid, lvl = a["sid"], a["lvl"]
    out = lambda r: ("ret", r, P5.P4.dumped(M, a["dumps"]))  # noqa: E731
    try:
        t = P5.get_target(e, M, GAME, U)
    except P5.Stop:
        return ("stop", 0x00408090, None)
    if not e.t("t_nz", t != 0):
        return out(0)
    if not e.c("lvl_gt0", lvl, ">", 0):
        return out(0)
    if not e.c("sid_ge0", sid, ">=", 0) or not e.c("sid_lt", sid, "<", SK_N):
        return out(0)
    m = s32(u32(by_charge(e, sid)))
    if not e.c("m_gt0", m, ">", 0):
        return out(0)
    v = u32(speed(e, m, lvl) + evalcalc(e, skd(sid, 0x138)))
    e.names.add("spec_caster_centre")
    centre = U if e.flip == "spec_caster_centre" else t
    return ("obs", OBS_NOVA, (GAME, U), (centre, u32(m), u32(sid), u32(lvl), v), P5.P4.dumped(M, a["dumps"]))


GEN = {"cb43": gen_cb43, "p36": gen_p36}
MODEL = {"cb43": m_cb43, "p36": m_p36}


# ----------------------------------------------------------------------------------------------- check plumbing
def write_spec(d):
    sk, mi = tables()
    for name, data in (("skills.bin", sk), ("missiles.bin", mi)):
        with open(os.path.join(d, name), "wb") as f:
            f.write(data)
    dt = bytearray(0x1000)
    for off, v in ((0x40, CALC), (0x44, CALC_N), (0xC4, NSTATES), (0xB98, SK), (0xBA0, SK_N), (0xBD4, NSTATS)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    lines = ["# plan 0066 S2be part 2 (tools/skills_s2be2_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (SK, os.path.join(d, "skills.bin")),
             "load %08x %s" % (MI, os.path.join(d, "missiles.bin")),
             "dword %08x %08x" % (G_MIS, MI),
             "dword %08x %08x" % (G_MIS_N, MI_N)]
    lines += ["guard %08x" % x for x in FATAL + ALLOC]
    lines += ["observe %08x" % x for x in (OBS_TIMED, OBS_NOVA)]
    with open(os.path.join(d, "s2ae.mem"), "w") as f:
        f.write("\n".join(lines) + "\n")


def observed(fam, k):
    if "stop" in k:
        return ("stop", k["stop"], None), None
    dumps = k["dumps"]
    if "obs" in k:
        st = k["stack"]
        ret = struct.unpack_from("<I", st, 0)[0]
        regs = {r: int(k["regs"][r], 16) for r in ("ecx", "edx", "esp")}
        if fam == "cb43":
            words = struct.unpack_from("<9I", st, 8)
            if regs["ecx"] != regs["esp"] + 8:       # the block passed is the one on the frame
                return ("obs-ecx", k["obs"], regs["ecx"], regs["esp"]), ret
            return ("obs", k["obs"], words), ret
        return ("obs", k["obs"], (regs["ecx"], regs["edx"]), struct.unpack_from("<5I", st, 4),
                tuple(dumps[va] for va in sorted(dumps))), ret
    if k["pop"] != POP[fam]:
        return ("pop", k["pop"]), None
    return ("ret", k["eax"], tuple(dumps[va] for va in sorted(dumps))), None


def norm(fam, want):
    return want


READS = ((BITMASK, BITMASK + 128, "g_BitMask32 0x006CE268 (.rdata)"),
         (P5.BUCKET_TBL, P5.BUCKET_TBL + 20, "GameFindUnit's per-type bucket offsets 0x006E10E0 (.rdata)"))


def account(reads, writes):
    bad = []
    for pc, addr, n, cnt in reads:
        if not any(lo <= addr and addr + n <= hi for lo, hi, _ in READS):
            bad.append(("R", pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        bad.append(("W", pc, addr, n, cnt))
    return bad


def predict(fam, a, flip=None):
    e = p1.E(flip)
    try:
        out = MODEL[fam](e, a)
    except (TypeError, KeyError, IndexError, AttributeError, ZeroDivisionError):
        return ("model-null",), e.names
    return out, e.names


def install():
    """Point part 1's check machinery at this part's families (its module state only; part 1's file is unchanged)."""
    B.FNS, B.FAMILIES, B.NCASES, B.POP, B.SITE = FNS, FAMILIES, NCASES, POP, SITE
    B.GEN, B.MODEL = GEN, MODEL
    B.observed, B.norm, B.account, B.write_spec, B.predict = observed, norm, account, write_spec, predict
    B.Case = Case

    def build(limit=None):
        cases = []
        for fam in FAMILIES:
            rnd = random.Random("n66sb-s2be2-" + fam)
            for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
                cases.append(GEN[fam](rnd))
        return cases
    B.build = build


def cmd_rows(limit=None):
    """Per family: the model outcome per case kind; p36: per Skills row 44/48, the class and speed reached."""
    install()
    seen = {}
    for c in B.build(limit):
        want, _ = predict(c.fam, c.a)
        key = c.fam + ":" + want[0]
        if c.fam == "p36" and c.a["sid"] in SHIP_SK and want[0] == "obs":
            key += ":row%d:m%d:v%d" % (c.a["sid"], want[3][1], want[3][4])
        elif c.fam == "p36" and c.a["sid"] in SHIP_SK:
            notarget = predict(c.fam, c.a, flip="t_nz")[0][0] == "obs"
            key += ":row%d:%s" % (c.a["sid"], "no-target-only" if notarget else "lvl-le0")
        seen[key] = seen.get(key, 0) + 1
    for k in sorted(seen):
        print("ROWS %s %d" % (k, seen[k]))
    for row in SHIP_SK:
        print("SHIPPED skills %d +0x04=%02x +0x48=%d +0x80=%d +0x54=%d +0x138=%08x" % (
            row, skb(row, 4), skw(row, 0x48), skw(row, 0x80), skw(row, 0x54), skd(row, 0x138)))
    for row in SHIP_MI:
        print("SHIPPED missiles %d Vel(+0x9A)=%d VelLev(+0x9B)=%d" % (row, mib(row, 0x9A), mib(row, 0x9B)))
    return 0


# ----------------------------------------------------------------------------------------------- do 13's return
DO13, DO13_END = 0x005DBC60, 0x005DBE48
DO13_XOR, DO13_RET = 0x005DBE3F, 0x005DBE45


def objdump(lo, hi):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % lo,
                          "--stop-address=0x%x" % hi, EXE], capture_output=True, text=True, check=True).stdout
    ins = []
    for ln in out.splitlines():
        m = re.match(r"\s+([0-9a-f]+):\s+(\S+)\s*(.*)$", ln)
        if m:
            ins.append((int(m.group(1), 16), m.group(2), m.group(3).strip()))
    return ins


def cmd_tail():
    """do 13 returns 0 on every path: its only `ret` is reached from `xor eax, eax` with no instruction between them
    that writes EAX, and no branch anywhere in .text lands between the xor and the ret."""
    ins = objdump(DO13, DO13_END)
    rets = [a for a, mn, _ in ins if mn.startswith("ret")]
    indirect = [(a, mn, op) for a, mn, op in ins if mn.startswith("j") and not re.match(r"0x[0-9a-f]+$", op)]
    targets = sorted({int(op, 16) for a, mn, op in ins if mn.startswith("j") and re.match(r"0x[0-9a-f]+$", op)})
    outside = [x for x in targets if not DO13 <= x < DO13_END]
    tail = [(a, mn, op) for a, mn, op in ins if DO13_XOR <= a <= DO13_RET]
    print("TAIL objdump function 0x%08x-0x%08x: instructions=%d rets=%s indirect_jumps=%d" % (
        DO13, DO13_END, len(ins), ",".join("%08x" % r for r in rets), len(indirect)))
    print("TAIL branch targets inside=%s outside=%d" % (",".join("%08x" % x for x in targets), len(outside)))
    for a, mn, op in tail:
        print("TAIL %08x %s %s" % (a, mn, op))
    # every direct branch or call in .text whose target lies in (xor, ret]
    text = objdump(0x00401000, 0x006D0000)
    hits = []
    for a, mn, op in text:
        if (mn.startswith("j") or mn.startswith("call")) and re.match(r"0x[0-9a-f]+$", op):
            x = int(op, 16)
            if DO13_XOR < x <= DO13_RET:
                hits.append((a, mn, x))
            if x == DO13_XOR or DO13_XOR - 2 <= x < DO13_XOR:
                print("TAIL into-or-before-xor %08x %s %08x" % (a, mn, x))
    print("TAIL text instructions=%d branches_into_xor_ret=%d" % (len(text), len(hits)))
    for h in hits:
        print("TAIL HIT %08x %s %08x" % h)
    # the second tool: radare2's own analysis of the function and its cross-references into the tail
    r2 = subprocess.run(["r2", "-q", "-e", "scr.color=0", "-e", "bin.relocs.apply=true", "-c",
                         "af @ 0x%x; afb @ 0x%x; aar; " % (DO13, DO13) +
                         "; ".join("axt @ 0x%x" % x for x in range(DO13_XOR - 2, DO13_RET + 1)),
                         EXE], capture_output=True, text=True)
    for ln in r2.stdout.splitlines():
        print("R2 " + ln.rstrip())
    ok = rets == [DO13_RET] and not indirect and not outside and not hits and \
        [mn for _, mn, _ in tail] == ["xor", "pop", "mov", "pop", "ret"]
    print("TAIL verdict %s" % ("single-ret-after-xor" if ok else "NOT-SHOWN"))
    return 0 if ok else 1


STATIC = (("cb43", 0x005DB150, 0x005DB1B5), ("p36", 0x005D4DB0, 0x005D4E64), ("bycharge", 0x005D3CF0, 0x005D3D92),
          ("speed", 0x00663270, 0x006632B7), ("evalcalc", 0x00646CA0, 0x00646CFF),
          ("gettarget", 0x00553540, 0x00553567))


def cmd_static():
    for name, lo, hi in STATIC:
        for a, mn, op in objdump(lo, hi):
            print("STATIC %s %08x %s %s" % (name, a, mn, op))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "rows", "tail", "static", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    o = ap.parse_args(argv)
    install()
    if o.cmd == "cases":
        B.cmd_cases(o.dir, o.limit)
        return 0
    if o.cmd == "check":
        return B.cmd_check(o.dir, o.limit)
    if o.cmd == "rows":
        return cmd_rows(o.limit)
    if o.cmd == "tail":
        return cmd_tail()
    if o.cmd == "static":
        return cmd_static()
    B.cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
