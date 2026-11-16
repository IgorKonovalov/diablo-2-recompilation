#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S5e (`lane/n66t`), part 1: the combat reduction and to-hit leaf functions under Ghidra's
p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared with the models below.

    python3 -I tools/combat_s5e_emu.py cases [--dir D]     write D/s5e.cases, D/s5e.mem and the table images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s5e.cases D/s5e.mem > D/s5e.out
    python3 -I tools/combat_s5e_emu.py check [--dir D]     compare, account for every traced read and write, controls
    python3 -I tools/combat_s5e_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66t/s5e/run. Every draw comes from random.Random("n66t-s5e-<family>"); the declared tables
from random.Random("n66t-s5e-image").

Every callee runs whole on the declared image (R2: no declared return) unless named as an observed boundary
(ADR-0021): the case ends at that call and its claim ends there. Callees run whole: STATS_GetUnitStat 0x00625480,
sub_00625500_UnitGetStat, sub_00625420_StatListGetStat, sub_00624F60_StatListGetValue, STATLIST_FindIndex 0x00624B90,
UNIT_HasState 0x00639DF0, UNIT_TestStateBit 0x00625B70, MONSTATS_IsUndead/IsDemon/IsBoss/IsPrimeEvil,
sub_0063EE90_HirelingType, 0x00451F30 (the +0xC4 mask test), sub_005A0180_MonTypeFlag, sub_00483360_MulDiv,
sub_0057DCA0_WeaponBlockChance, sub_006261D0_StatListGetEntries and 0x00626110, RNG_Range 0x0045C390,
sub_00554010_UnitGetGame, DEBUG_DefenceRollStub 0x005347C0, sub_00554650_PacketHitClassSet.

Families (function, registers; inventory rows):
  resist 0x0057BE00 COMBAT_ResistFor (EBX row, EDI ctx).            reductions 2, 14-16, 18, 22, 23
  absorb 0x0057BF10 COMBAT_Absorb (EAX d, ECX ctx, EBX row).        reductions 19, 21
  pct    0x0057C060 COMBAT_DamagePercent (EAX ctx).                 reductions 3, 4, 8, 9; README 12's P = 25
  len    0x0057C140 COMBAT_LengthImmunities (ESI ctx).              reductions 12, 13
  thm    0x0057D8A0 COMBAT_ToHitTargetMods (EBX att, EDI def, &AR, &DEF).   to-hit 6, 11, 12
  phh    0x0057D810 sub_0057D810_PreventHealHook (EDI att, ESI def); observed boundary STATE_ApplyTimed 0x0056E970.
                                                                    to-hit 9, 10's remainder
  mode   0x00621190 (unit).                                         to-hit 24
  avoid  0x0057DD60 COMBAT_AvoidRoll (ESI def, EDI att, isMissile); observed boundary 0x0064F380 (the weapon-block
         skill check, which runs COMPOSIT_WeaponClass).             to-hit 25, 27
  crit   0x005A5560 sub_005A5560_MonCritDouble (ECX att, EDX def, pkt); observed boundary
         sub_00621E40_UnitSetOverlayStat.                           damage 20

Controls as S6e/S6f: every named test reversed alone, every ordered compare's strictness switched alone; `sep` counts
the cases a control changes, `passed` those the emulator still matches (must be 0). Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66t", "s5e", "run")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
PINNED = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"
M32 = 0xFFFFFFFF
A_LCG = 0x6AC690C5

G_DT = 0x00744304
BITMASK = 0x006CE268
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)
OBS_STATE, OBS_WCHECK, OBS_OVERLAY = 0x0056E970, 0x0064F380, 0x00621E40
FNS = {"resist": 0x0057BE00, "absorb": 0x0057BF10, "pct": 0x0057C060, "len": 0x0057C140, "thm": 0x0057D8A0,
       "phh": 0x0057D810, "mode": 0x00621190, "avoid": 0x0057DD60, "crit": 0x005A5560}
FAMILIES = ("resist", "absorb", "pct", "len", "thm", "phh", "mode", "avoid", "crit")
NCASES = {"resist": 3000, "absorb": 2000, "pct": 2500, "len": 1500, "thm": 2500, "phh": 1200, "mode": 600,
          "avoid": 2500, "crit": 1500}
CALL_SITE = {"phh": 0x0057D896, "crit": 0x005A5641}
AVOID_SITE = {True: (0x0057DDB0, -4), False: (0x0057DEEF, -8)}   # player branch, other branch

# declared memory
DT = 0x21000000
ISC, ISC_N, ISC_SZ = 0x21100000, 0x200, 0x144
MS, MS_N, MS_SZ = 0x21200000, 0x240, 0x1A8
NSTATES = 0xC0
ATT, DEF = 0x20000000, 0x20001000
UNIT_SZ = 0x100
SL_OFF, ARR_OFF, BITS_OFF, MD_OFF = 0x200, 0x300, 0x700, 0x780
CTX, PKT, ROW, GAME, DREC, OUT = 0x20004000, 0x20004100, 0x20004200, 0x20004300, 0x20004400, 0x20004500
PKT_SZ = 0x70
HIRE = {0x10F: 1, 0x152: 2, 0x167: 3, 0x230: 4, 0x231: 4}


def u32(v):
    return v & M32


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def le32(v):
    return struct.pack("<I", v & M32)


def tdiv(a, b):
    """C signed division, truncating toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def muldiv(a, b, c):
    """sub_00483360_MulDiv(ecx a, edx b, c), signed; the same model as tools/monstats.py muldiv."""
    a, b, c = s32(a), s32(b), s32(c)
    if c == 0:
        return 0
    if a > 0x100000:
        if c > (a >> 4):
            return s32(tdiv(a * b, c))
        return s32(tdiv(a, c) * b)
    if b > 0x10000:
        if c > (b >> 4):
            return s32(tdiv(a * b, c))
        return s32(tdiv(b, c) * a)
    return tdiv(s32(a * b), c)


class E:
    """One model run: the named tests and the reversal or strictness control (as tools/anim_s6e_emu.py)."""

    def __init__(self, flip=None):
        self.flip = flip
        self.names = set()

    def t(self, name, cond):
        self.names.add(name)
        return (not cond) if self.flip == name else bool(cond)

    def c(self, name, a, op, b):
        self.names.add(name)
        self.names.add(name + "~")
        if self.flip == name + "~":
            op = {"<": "<=", "<=": "<", ">": ">=", ">=": ">"}[op]
        r = {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
        return (not r) if self.flip == name else r


class Image:
    """The declared MonStats table (seeded random bytes) and the zero ItemStatCost records."""

    def __init__(self):
        data = open(EXE, "rb").read()
        if hashlib.sha256(data).hexdigest() != PINNED:
            raise SystemExit("combat_s5e_emu: not the pinned Game.exe")
        r = random.Random("n66t-s5e-image")
        self.ms = bytearray(r.getrandbits(8) for _ in range(MS_N * MS_SZ))
        self.bitmask = [1 << i for i in range(32)]


IMG = None


def img():
    global IMG
    if IMG is None:
        IMG = Image()
    return IMG


class Case:
    def __init__(self, fam):
        self.fam = fam
        self.w = {}
        self.dumps = []
        self.regs = {}
        self.args = []
        self.ecx = self.edx = 0
        self.a = {}           # the model's inputs

    def put(self, addr, b):
        for i, x in enumerate(b):
            self.w[addr + i] = x

    def lines(self):
        out, run = [], []
        for addr in sorted(self.w):
            if run and addr == run[0] + len(run[1]):
                run[1].append(self.w[addr])
            else:
                if run:
                    out.append("w %08x %s" % (run[0], bytes(run[1]).hex()))
                run = [addr, [self.w[addr]]]
        if run:
            out.append("w %08x %s" % (run[0], bytes(run[1]).hex()))
        for a, n in self.dumps:
            out.append("d %08x %d" % (a, n))
        for k, v in self.regs.items():
            out.append("r %s %08x" % (k, v))
        out.append("call %08x %08x %08x %s" % (FNS[self.fam], self.ecx, self.edx,
                                               " ".join("%08x" % u32(x) for x in self.args)))
        return out


# ----------------------------------------------------------------------------------------------- units
def rnd_val(rnd):
    return rnd.choice([0, 0, rnd.randint(1, 40), rnd.randint(1, 150), rnd.randint(-150, -1), rnd.randint(95, 105),
                       rnd.getrandbits(32), rnd.randint(1, 3), 0x7FFFFFFF, 0x80000000, rnd.randint(-120, -90)])


def put_unit(c, rnd, base, typ, cls, stats, states, mode=None, listflag=None, nolist=False, md_flags=None,
             f30=None, f40=None, seed=None, game=GAME, fc4=None):
    """A scratch unit at base: random bytes, then the fields the code reads. Its stat list at base+SL_OFF holds
    {stat: value} at layer 0 (plus decoys at layer 1 and other stats), sorted by key (stat << 16 | layer); the live
    array at +0x48/+0x4C when +0x10 bit 31 is set, else +0x24/+0x28; the state bits at +0x58 (read only when bit 31
    is set). -> the unit's model view."""
    c.put(base, bytes(rnd.getrandbits(8) for _ in range(UNIT_SZ)))
    c.put(base, le32(typ))
    c.put(base + 4, le32(cls))
    mode = rnd.randrange(20) if mode is None else mode
    c.put(base + 0x10, le32(mode))
    md = base + MD_OFF
    mdf = rnd.getrandbits(16) if md_flags is None else md_flags
    if md_flags == -1:
        c.put(base + 0x14, le32(0))
    else:
        c.put(base + 0x14, le32(md))
        c.put(md, bytes(rnd.getrandbits(8) for _ in range(0x20)))
        c.put(md + 0x16, struct.pack("<H", mdf & 0xFFFF))
    seed = (rnd.getrandbits(32), rnd.getrandbits(32)) if seed is None else seed
    c.put(base + 0x20, le32(seed[0]) + le32(seed[1]))
    f30 = rnd.choice([0, rnd.getrandbits(32)]) if f30 is None else f30
    f40 = rnd.randrange(20) if f40 is None else f40
    c.put(base + 0x30, le32(f30))
    c.put(base + 0x40, le32(f40))
    c.put(base + 0x60, le32(0))
    c.put(base + 0x80, le32(game))
    fc4 = rnd.getrandbits(32) if fc4 is None else fc4
    c.put(base + 0xC4, le32(fc4))
    view = {"type": typ, "cls": cls, "mode": mode, "md": None if md_flags == -1 else mdf & 0xFFFF, "f30": f30,
            "f40": f40, "seed": list(seed), "fc4": fc4, "stats": {}, "states": set(), "base": base}
    if nolist:
        c.put(base + 0x5C, le32(0))
        return view
    sl = base + SL_OFF
    c.put(base + 0x5C, le32(sl))
    c.put(sl, bytes(rnd.getrandbits(8) for _ in range(0x60)))
    flag = rnd.random() < 0.85 if listflag is None else listflag
    lf = (0x80000000 if flag else 0) | rnd.getrandbits(31)
    c.put(sl + 0x10, le32(lf))
    c.put(sl + 0x44, le32(0))
    live, other = (0x48, 0x24) if flag else (0x24, 0x48)
    keys = {}
    for s, v in stats.items():
        if v is None:
            continue
        keys[s << 16] = u32(v)
        if rnd.random() < 0.15:
            keys[(s << 16) | 1] = rnd.getrandbits(32)
    extra = {}
    for _ in range(rnd.randrange(4)):
        k = rnd.randrange(1, ISC_N) << 16
        if k >> 16 not in stats and k >> 16 != 348:
            keys[k] = extra[k >> 16] = rnd.getrandbits(32)
    ks = sorted(keys)
    arr = base + ARR_OFF
    for i, k in enumerate(ks):
        c.put(arr + 8 * i, le32(k) + le32(keys[k]))
    c.put(sl + live, le32(arr))
    c.put(sl + live + 4, struct.pack("<H", len(ks)) + bytes(2))
    decoy = arr + 8 * 64
    dk = sorted({(s << 16): rnd.getrandbits(32) for s in list(stats)[:3]})
    for i, k in enumerate(dk):
        c.put(decoy + 8 * i, le32(k) + le32(rnd.getrandbits(32)))
    c.put(sl + other, le32(decoy))
    c.put(sl + other + 4, struct.pack("<H", len(dk)) + bytes(2))
    bits = base + BITS_OFF
    words = [rnd.getrandbits(32) & rnd.getrandbits(32) & rnd.getrandbits(32) for _ in range(NSTATES // 32)]
    for s in range(NSTATES):
        words[s >> 5] &= ~(1 << (s & 31))
    for s in states:
        words[s >> 5] |= 1 << (s & 31)
    c.put(sl + 0x58, le32(bits))
    for i, w in enumerate(words):
        c.put(bits + 4 * i, le32(w))
    view["stats"] = {s: s32(v) for s, v in stats.items() if v is not None}
    view["stats"].update({s: s32(v) for s, v in extra.items()})
    view["states"] = set(states) if flag else set()
    view["listflag"] = flag
    return view


def stat(u, s):
    """STATS_GetUnitStat / UnitGetStat(u, s, 0): 0 for no unit, no list, or an id outside the table."""
    if u is None or "stats" not in u or u.get("nolist"):
        return 0
    if s < 0 or s >= ISC_N:
        return 0
    return u["stats"].get(s, 0)


def has_state(u, st):
    if u is None or u["type"] not in (0, 1, 3) or st < 0 or st >= NSTATES:
        return False
    return st in u["states"]


def ms_byte(cls, off):
    return img().ms[cls * MS_SZ + off]


def ms_rec(u):
    if u is None or u["type"] != 1 or not 0 <= u["cls"] < MS_N:
        return None
    return u["cls"]


def is_undead(u):
    k = ms_rec(u)
    return k is not None and bool(ms_byte(k, 0xD) & 0x18)


def is_demon(u):
    k = ms_rec(u)
    return k is not None and bool(ms_byte(k, 0xD) & 0x20)


def is_boss(u):
    k = ms_rec(u)
    return k is not None and bool(ms_byte(k, 0xC) & 0x40)


def is_prime(u):
    k = ms_rec(u)
    return k is not None and bool(ms_byte(k, 0xC) & 0x80)


def hire(u):
    if u is None or u["type"] != 1:
        return 0
    return HIRE.get(u32(u["cls"]), 0)


def mon_type_flag(u, mask):
    return u is not None and u["type"] == 1 and u["md"] is not None and bool(u["md"] & mask)


def put_ms(c, rnd, cls, **bytes_at):
    """Overwrite chosen bytes of MonStats record cls for this case (the model reads img().ms, patched back after)."""
    if not 0 <= cls < MS_N:
        return {}
    patch = {}
    for off, v in bytes_at.items():
        o = int(off[1:], 16)
        c.put(MS + cls * MS_SZ + o, bytes([v]))
        patch[cls * MS_SZ + o] = v
    return patch


def rnd_cls(rnd, hire_p=0.25):
    x = rnd.random()
    if x < hire_p:
        return rnd.choice(list(HIRE))
    if x < hire_p + 0.05:
        return rnd.choice([-1, MS_N, 0x1000, -0x100])
    return rnd.randrange(MS_N)


def rnd_type(rnd):
    return rnd.choice([0, 0, 1, 1, 1, 2, 3, 4])


def rnd_ms_bytes(rnd):
    return {"o0c": rnd.choice([0, 0x40, 0x80, 0xC0, rnd.getrandbits(8)]),
            "o0d": rnd.choice([0, 0x08, 0x10, 0x18, 0x20, 0x28, rnd.getrandbits(8)])}


# ----------------------------------------------------------------------------------------------- families
def gen_resist(rnd):
    c = Case("resist")
    res = rnd.choice([-1, 36, 37, 39, 41, 43, 45, rnd.randrange(ISC_N)])
    mx = rnd.choice([-1, -1, 40, 42, 44, 46, rnd.randrange(ISC_N)])
    pierce = rnd.choice([-1, -1, 333, 334, 335, 336, rnd.randrange(ISC_N)])
    defmon = rnd.choice([0, 0, 1, rnd.getrandbits(32)])
    big = rnd.random() < 0.1
    sv = {}
    for s in {res, mx, pierce} - {-1}:
        sv[s] = rnd.getrandbits(32) if big else rnd.choice([0, rnd.randint(-150, 150), rnd.randint(90, 110),
                                                            rnd.randint(-110, -90), rnd.randint(1, 30)])
    dcls = rnd_cls(rnd, 0.05)
    dtyp = rnd_type(rnd)
    dms = rnd_ms_bytes(rnd)
    att = put_unit(c, rnd, ATT, rnd_type(rnd), rnd_cls(rnd), {s: sv[s] for s in sv if rnd.random() < 0.8},
                   [47] if rnd.random() < 0.4 else [])
    dfn = put_unit(c, rnd, DEF, dtyp, dcls, {s: sv[s] for s in sv if rnd.random() < 0.8}, [])
    patch = put_ms(c, rnd, dcls, **dms) if dtyp == 1 else {}
    exp = rnd.choice([0, 0, 1, rnd.getrandbits(32)])
    diff = rnd.choice([0, 1, 2, 3, rnd.getrandbits(8)])
    pen = rnd.choice([0, -40, -100, rnd.randint(-200, 50), rnd.getrandbits(32)])
    c.put(GAME + 0x6C, bytes([rnd.getrandbits(8), diff, rnd.getrandbits(8), rnd.getrandbits(8)]))
    c.put(GAME + 0x70, le32(exp))
    c.put(GAME + 0x80, le32(rnd.getrandbits(32)))
    c.put(DREC, le32(pen))
    c.put(CTX, le32(GAME) + le32(DREC) + le32(ATT) + le32(DEF) + le32(rnd.getrandbits(32)) + le32(defmon)
          + le32(PKT))
    c.put(ROW, le32(rnd.getrandbits(32)) + le32(res) + le32(mx) + le32(pierce) + le32(rnd.getrandbits(32)) * 2)
    c.regs = {"EBX": ROW, "EDI": CTX}
    c.a = dict(att=att, dfn=dfn, res=res, mx=mx, pierce=pierce, defmon=defmon, exp=exp, diff=diff, pen=pen,
               patch=patch)
    return c


def with_patch(a, f):
    im = img()
    saved = {o: im.ms[o] for o in a.get("patch", {})}
    for o, v in a.get("patch", {}).items():
        im.ms[o] = v
    try:
        return f()
    finally:
        for o, v in saved.items():
            im.ms[o] = v


def m_resist(e, a):
    att, dfn = a["att"], a["dfn"]
    r = stat(dfn, a["res"]) if e.t("res_set", a["res"] != -1) else 0
    if e.t("pierce_set", a["pierce"] != -1) and (e.c("r_lt100", r, "<", 100) or e.t("pierce_defmon0", a["defmon"] == 0)):
        p = stat(att, a["pierce"])
        if e.t("p_nz", p != 0):
            r = s32(r - p)
    if e.t("pen_defmon0", a["defmon"] == 0) and e.t("res_not36", a["res"] != 36) and e.t("res_not37", a["res"] != 37):
        if e.t("classic", a["exp"] == 0):
            if e.t("diff1", a["diff"] == 1):
                r = s32(r - 20)
            elif e.t("diff2", a["diff"] == 2):
                r = s32(r - 50)
        else:
            r = s32(r + s32(a["pen"]))
    if e.c("r_lt1", r, "<", 1):
        out = -100 if e.c("r_ltm99", r, "<", -99) else r
        e.names.add("spec_sanct_any_r")     # control: B2's text, the sanctuary test at the top level (any r)
        if e.flip == "spec_sanct_any_r" and a["res"] == 36 and has_state(att, 47) and is_undead(dfn):
            out = 0
        return out
    out = r
    if e.t("cap_defmon0", a["defmon"] == 0):
        if e.t("max_none", a["mx"] == -1):
            cap = 50 if e.t("cap_res36", a["res"] == 36) else 75
        else:
            cap = s32(stat(dfn, a["mx"]) + 75)
            if e.c("cap_gt94", cap, ">", 94):
                cap = 95
        out = r if e.c("r_ltcap", r, "<", cap) else cap
    if e.t("sanct_res36", a["res"] == 36) and e.t("sanct_state", has_state(att, 47)) and e.t("sanct_undead",
                                                                                              is_undead(dfn)):
        out = 0
    return out


def gen_absorb(rnd):
    c = Case("absorb")
    pct = rnd.choice([-1, 142, 144, 146, 148, rnd.randrange(ISC_N)])
    flat = rnd.choice([143, 145, 147, 149, rnd.randrange(ISC_N)])
    sv = {}
    if pct != -1:
        sv[pct] = rnd.choice([0, rnd.randint(1, 39), 40, 41, rnd.randint(41, 200), rnd.randint(-50, -1),
                              rnd.getrandbits(32)])
    sv[flat] = rnd.choice([0, rnd.randint(1, 30), rnd.randint(-20, -1), rnd.getrandbits(32),
                           rnd.choice([0x7FFFFF, 0x800000, 0x1000000])])
    if flat == pct:
        sv[flat] = sv[pct] if pct in sv else sv[flat]
    dfn = put_unit(c, rnd, DEF, rnd_type(rnd), rnd_cls(rnd), {s: v for s, v in sv.items() if rnd.random() < 0.9}, [])
    d = rnd.choice([0, rnd.randint(1, 10000), rnd.randint(1, 1 << 20), rnd.randint(-5000, -1), rnd.getrandbits(32),
                    rnd.randint(0x100000, 0x7FFFFFFF)])
    heal = rnd.choice([0, rnd.getrandbits(32), rnd.randint(1, 1000)])
    c.put(PKT, bytes(rnd.getrandbits(8) for _ in range(PKT_SZ)))
    c.put(PKT + 0x48, le32(heal))
    c.put(CTX, le32(GAME) + le32(DREC) + le32(ATT) + le32(DEF) + le32(rnd.getrandbits(32)) * 2 + le32(PKT))
    c.put(ROW, le32(rnd.getrandbits(32)) * 4 + le32(pct) + le32(flat))
    c.regs = {"EAX": u32(d), "EBX": ROW}
    c.ecx = CTX
    c.dumps = [(PKT + 0x48, 4)]
    c.a = dict(dfn=dfn, pct=pct, flat=flat, d=s32(d), heal=heal)
    return c


def m_absorb(e, a):
    d, heal = a["d"], a["heal"]
    if not e.t("pct_set", a["pct"] != -1):
        return ("ret", u32(d), u32(heal))
    p = stat(a["dfn"], a["pct"])
    if e.c("p_ge40", p, ">=", 40):
        p = 40
        go = True
    else:
        go = e.c("p_gt0", p, ">", 0)
    if go:
        x = muldiv(d, p, 100)
        heal = u32(heal + x)
        d = s32(d - x)
    f = s32(stat(a["dfn"], a["flat"]) << 8)
    if e.c("f_gt0", f, ">", 0):
        x = d if e.c("d_le_f", d, "<=", f) else f
        heal = u32(heal + x)
        d = s32(d - x)
    return ("ret", u32(d), u32(heal))


def gen_pct(rnd):
    c = Case("pct")
    shape = rnd.random()
    at, dt = rnd_type(rnd), rnd_type(rnd)
    acls, dcls = rnd_cls(rnd, 0.35), rnd_cls(rnd, 0.35)
    att = put_unit(c, rnd, ATT, at, acls, {}, [], fc4=rnd.choice([0, 0x80000000, rnd.getrandbits(32)]))
    dfn = put_unit(c, rnd, DEF, dt, dcls, {}, [], fc4=rnd.choice([0, 0x80000000, rnd.getrandbits(32)]))
    patch = {}
    if at == 1:
        patch.update(put_ms(c, rnd, acls, o0c=rnd.choice([0, 0x80, 0xC0, 0x40, rnd.getrandbits(8)])))
    if dt == 1:
        patch.update(put_ms(c, rnd, dcls, o0c=rnd.choice([0, 0x40, 0xC0, 0x80, rnd.getrandbits(8)])))
    pa, pd = ATT, DEF
    if shape < 0.03:
        pa = 0
    elif shape < 0.06:
        pd = 0
    elif shape < 0.09:
        pd = pa
    hbp = rnd.choice([25, 35, 50, rnd.getrandbits(32)])
    drec = 0 if rnd.random() < 0.05 else DREC
    c.put(DREC + 0x38, le32(hbp))
    c.put(CTX, le32(GAME) + le32(drec) + le32(pa) + le32(pd))
    c.regs = {"EAX": CTX}
    c.a = dict(att=att if pa else None, dfn=(att if pd == ATT else dfn) if pd else None, same=pa == pd and pa != 0,
               drec=drec, hbp=hbp, patch=patch)
    return c


def m_pct(e, a):
    att, dfn = a["att"], a["dfn"]
    if not e.t("att_set", att is not None) or not e.t("def_set", dfn is not None) or e.t("same", a["same"]):
        return 100
    if e.t("def_player", dfn["type"] == 0):
        if e.t("att_nonplayer", att["type"] != 0) and e.t("att_nohire1", hire(att) == 0):
            if e.t("att_noflag", not att["fc4"] & 0x80000000) and e.t("att_nohire2", hire(att) == 0):
                return 100
        return 17
    if e.t("def_hire", hire(dfn) != 0) and e.t("att_hire", hire(att) != 0):
        return 25
    if e.t("att_hire2", hire(att) != 0) and e.t("def_boss", is_boss(dfn)):
        if not e.t("drec_set", a["drec"] != 0):
            return 100
        return a["hbp"]
    if e.t("att_prime", is_prime(att)) and e.t("def_flag", bool(dfn["fc4"] & 0x80000000)):
        return 200 if e.t("def_hire3", hire(dfn) != 0) else 400
    return 100


def gen_len(rnd):
    c = Case("len")
    sv = {153: rnd.choice([0, 0, 1, rnd.getrandbits(32)]), 118: rnd.choice([0, 0, 1, rnd.getrandbits(32)])}
    st = [s for s in (131, 133) if rnd.random() < 0.5]
    dfn = put_unit(c, rnd, DEF, rnd.choice([0, 1, 1, 3, 2]), rnd_cls(rnd), {s: v for s, v in sv.items() if v}, st)
    f = {}
    for off in (0x18, 0x2C, 0x30, 0x34):
        f[off] = rnd.choice([0, rnd.randint(1, 500), rnd.randint(-500, -1), rnd.getrandbits(32), 1])
    c.put(PKT, bytes(rnd.getrandbits(8) for _ in range(PKT_SZ)))
    for off, v in f.items():
        c.put(PKT + off, le32(v))
    c.put(CTX, le32(GAME) + le32(DREC) + le32(ATT) + le32(DEF) + le32(rnd.getrandbits(32)) * 2 + le32(PKT))
    c.regs = {"ESI": CTX}
    c.dumps = [(PKT + 0x18, 4), (PKT + 0x2C, 12)]
    c.a = dict(dfn=dfn, f={k: s32(v) for k, v in f.items()})
    return c


def m_len(e, a):
    f, dfn = dict(a["f"]), a["dfn"]
    if e.c("cold_gt0", f[0x30], ">", 0) or e.c("frz_gt0", f[0x34], ">", 0):
        if e.t("s153", stat(dfn, 153) != 0):
            f[0x30] = f[0x34] = 0
        elif e.t("s118", stat(dfn, 118) != 0):
            f[0x30] = tdiv(f[0x30], 2)
            f[0x34] = tdiv(f[0x34], 2)
    if e.c("pois_gt0", f[0x2C], ">", 0) and e.t("st133", has_state(dfn, 133)):
        f[0x2C] = 0
    if e.c("burn_gt0", f[0x18], ">", 0) and e.t("st131", has_state(dfn, 131)):
        f[0x18] = 0
    return ("pkt", tuple(u32(f[k]) for k in (0x18, 0x2C, 0x30, 0x34)))


def gen_thm(rnd):
    c = Case("thm")
    sv = {115: rnd.choice([0, 0, 1, rnd.getrandbits(32)]),
          116: rnd.choice([0, rnd.randint(1, 50), rnd.randint(50, 250), rnd.randint(-50, 0), 1, 2, 3, 200, 201,
                           rnd.getrandbits(32)]),
          123: rnd.choice([0, rnd.randint(1, 500), rnd.getrandbits(32)]),
          124: rnd.choice([0, rnd.randint(1, 500), rnd.getrandbits(32)])}
    att = put_unit(c, rnd, ATT, 0, rnd.randrange(7), {s: v for s, v in sv.items() if rnd.random() < 0.85}, [])
    dt = rnd.choice([0, 1, 1, 1, 1, 2, 3, 4])
    dcls = rnd_cls(rnd, 0.2)
    dfn = put_unit(c, rnd, DEF, dt, dcls, {}, [], md_flags=rnd.choice([-1, 0, 2, 8, 0xA, rnd.getrandbits(16)]))
    patch = put_ms(c, rnd, dcls, **rnd_ms_bytes(rnd)) if dt == 1 else {}
    pd = 0 if rnd.random() < 0.05 else DEF
    ar = rnd.choice([rnd.randint(0, 5000), rnd.getrandbits(32)])
    df = rnd.choice([rnd.randint(0, 5000), rnd.randint(-100, 0), rnd.getrandbits(32), rnd.randint(0x100001, 1 << 30)])
    c.put(OUT, le32(ar) + le32(df))
    c.regs = {"EBX": ATT, "EDI": pd}
    c.args = [OUT, OUT + 4]
    c.dumps = [(OUT, 8)]
    c.a = dict(att=att, dfn=dfn if pd else None, ar=ar, df=df, patch=patch)
    return c


def m_thm(e, a):
    att, dfn = a["att"], a["dfn"]
    ar, df = s32(a["ar"]), s32(a["df"])
    if e.t("s115", stat(att, 115) != 0) and e.t("d1_set", dfn is not None) and e.t("d1_mon", dfn["type"] == 1) \
            and e.t("d1_not_0a", not mon_type_flag(dfn, 0xA)) and e.t("d1_not_boss", not is_boss(dfn)) \
            and e.t("d1_not_hire", hire(dfn) == 0):
        df = 0
    p = stat(att, 116)
    if e.c("p_gt0", p, ">", 0):
        if e.t("d2_set", dfn is not None):
            if e.t("d2_player", dfn["type"] == 0):
                half = True
            elif e.t("d2_mon", dfn["type"] == 1):
                half = e.t("d2_boss", is_boss(dfn)) or e.t("d2_02", mon_type_flag(dfn, 2)) \
                    or e.t("d2_hire", hire(dfn) != 0)
            else:
                half = False
            if half:
                p = tdiv(p, 2)
        p = 0 if e.c("p_le0", p, "<=", 0) else p
        if e.c("p_ge100", p, ">=", 100):
            p = 100
        df = s32(df - muldiv(df, p, 100))
    v = stat(att, 123)
    if e.t("s123", v != 0) and e.t("demon", is_demon(dfn)):
        ar = s32(ar + v)
    v = stat(att, 124)
    if e.t("s124", v != 0) and e.t("undead", is_undead(dfn)):
        ar = s32(ar + v)
    return ("out", u32(ar), u32(df))


def gen_phh(rnd):
    c = Case("phh")
    at = rnd.choice([0, 0, 0, 1, 2])
    att = put_unit(c, rnd, ATT, at, rnd.randrange(7), {117: rnd.choice([0, 1, rnd.getrandbits(32)])}
                   if rnd.random() < 0.9 else {}, [])
    dcls = rnd.choice([0x2BF, 0x2C0, 0x2C2, 0x2C5, 0x2C6, rnd.randrange(MS_N), rnd.choice(list(HIRE)), -1])
    dfn = put_unit(c, rnd, DEF, rnd.choice([1, 1, 1, 0, 3]), dcls, {}, [])
    pa = 0 if rnd.random() < 0.04 else ATT
    pd = 0 if rnd.random() < 0.04 else DEF
    c.regs = {"EDI": pa, "ESI": pd}
    c.a = dict(att=att if pa else None, dfn=dfn if pd else None, pa=pa, pd=pd)
    return c


def m_phh(e, a):
    att, dfn = a["att"], a["dfn"]
    if e.t("att_set", att is not None) and e.t("att_player", att["type"] == 0) and e.t("def_set", dfn is not None) \
            and e.t("def_mon", dfn["type"] == 1) and e.t("s117", stat(att, 117) != 0):
        cl = s32(dfn["cls"])
        if e.c("cls_lt2c0", cl, "<", 0x2C0) or e.c("cls_gt2c5", cl, ">", 0x2C5):
            return ("obs", OBS_STATE, (a["pa"], a["pd"], 0, 1, 120000, 31, 0, 52, 0))
    return ("ret",)


def gen_mode(rnd):
    c = Case("mode")
    t = rnd.choice([0, 1, 2, 3, 4, 5, rnd.getrandbits(32)])
    u = put_unit(c, rnd, DEF, t, 0, {}, [], nolist=True, f30=rnd.choice([0, 0, 1, rnd.getrandbits(32)]),
                 f40=rnd.getrandbits(32), mode=rnd.getrandbits(32))
    p = 0 if rnd.random() < 0.05 else DEF
    c.args = [p]
    c.a = dict(u=u if p else None)
    return c


def m_mode(e, a):
    u = a["u"]
    if not e.t("u_set", u is not None):
        return ("ret", 0)
    if (e.t("t0", u["type"] == 0) or e.t("t1", u["type"] == 1)) and e.t("f30", u["f30"] != 0):
        return ("ret", u32(u["f40"]))
    return ("ret", u32(u["mode"]))


def lcg(seed):
    v = seed[0] * A_LCG + seed[1]
    seed[0], seed[1] = v & M32, (v >> 32) & M32
    return seed[0]


def rng_range(seed, n):
    if n < 1:
        return 0
    lo = lcg(seed)
    return lo % n if n & (n - 1) else lo & (n - 1)


def gen_avoid(rnd):
    c = Case("avoid")
    dt = rnd.choice([0, 0, 0, 1, 1, 1, 2, 3, 4, 5])
    mode = rnd.choice([2, 3, 15, 2, 15, 0, 1, 4, 7, rnd.randrange(20)])
    sv = {}
    for s in (340, 338, 339):
        sv[s] = rnd.choice([0, rnd.randint(1, 99), rnd.randint(-20, 0), 100, rnd.getrandbits(32)])
    wb = rnd.random() < 0.08
    dfn = put_unit(c, rnd, DEF, dt, rnd_cls(rnd), {s: v for s, v in sv.items() if rnd.random() < 0.85}, [],
                   mode=mode, listflag=True if wb else None)
    if wb:     # one stat-348 entry of item type 0 (matches with no item): WeaponBlockChance > 0 if its value is
        val = rnd.choice([rnd.randint(1, 60), 0, -5])
        sl = DEF + SL_OFF
        arr = DEF + ARR_OFF
        keys = {(s << 16): u32(v) for s, v in dfn["stats"].items()}
        keys.update({(s << 16) | 1: rnd.getrandbits(32) for s in list(dfn["stats"])[:2]})
        keys[348 << 16] = u32(val)
        ks = sorted(keys)
        for i, k in enumerate(ks):
            c.put(arr + 8 * i, le32(k) + le32(keys[k]))
        c.put(sl + 0x4C, struct.pack("<H", len(ks)) + bytes(2))
        dfn["wb"] = val
    att = put_unit(c, rnd, ATT, rnd_type(rnd), 0, {}, [], nolist=True)
    pd = 0 if rnd.random() < 0.04 else DEF
    miss = rnd.choice([0, 1, rnd.getrandbits(32)])
    c.regs = {"ESI": pd, "EDI": ATT}
    c.args = [miss]
    c.dumps = [(DEF + 0x20, 8)]
    c.a = dict(dfn=dfn if pd else None, miss=miss)
    return c


def m_avoid(e, a):
    dfn = a["dfn"]
    seed = list(dfn["seed"]) if dfn else None

    def done(v):
        return ("ret", v, tuple(seed) if seed else None)

    def evade():
        ev = stat(dfn, 340)
        if not e.c("e_gt0", ev, ">", 0):
            return done(0)
        lo = lcg(seed)
        r = lo % 100
        return done(8 if e.c("r_lt_e", r, "<", ev) else 0)

    if e.t("def_set", dfn is not None):
        m = dfn["mode"]
        if e.t("def_player", dfn["type"] == 0):
            if e.t("p_m3", m == 3) or e.t("p_m2", m == 2):
                return evade()
        elif (e.t("o_m15", m == 15) or e.t("o_m2", m == 2)) and not (e.flip == "spec_monster_only"
                                                                      and dfn["type"] != 1):
            return evade()
        e.names.add("spec_monster_only")    # control: C3's text, the moving modes for a monster (type 1) only
        wbv = dfn.get("wb", 0) if dfn.get("listflag") else 0
        if e.c("wb_gt0", wbv, ">", 0):
            return ("obs", OBS_WCHECK, (DEF, 0, 0xFFFFFFFF, 1), dfn["type"] == 0)
    if e.t("melee", a["miss"] == 0):
        ch = stat(dfn, 338)
        if e.c("dodge_gt0", ch, ">", 0):
            r = rng_range(seed, 100)
            if e.c("r_lt_dodge", r, "<", ch):
                return done(4)
    else:
        ch = stat(dfn, 339)
        if e.c("avoid_gt0", ch, ">", 0):
            r = rng_range(seed, 100)
            if e.c("r_lt_avoid", r, "<", ch):
                return done(2)
    return done(0)


def gen_crit(rnd):
    c = Case("crit")
    at = rnd.choice([1, 1, 1, 1, 0, 2])
    acls = rnd_cls(rnd, 0.05)
    att = put_unit(c, rnd, ATT, at, acls, {}, [], nolist=True)
    cb = rnd.choice([0, rnd.randint(1, 99), 100, 255, rnd.randint(1, 30), rnd.getrandbits(8)])
    patch = put_ms(c, rnd, acls, oa6=cb) if at == 1 else {}
    pa = 0 if rnd.random() < 0.04 else ATT
    pd = 0 if rnd.random() < 0.2 else DEF
    if pd:
        put_unit(c, rnd, DEF, 1, 0, {}, [], nolist=True)
    flags = rnd.choice([0, 0x10, 0x20, 0xF0, 0x80, 0x100, 0x0F, rnd.getrandbits(32)])
    pk = [rnd.choice([0, rnd.randint(1, 1 << 20), rnd.getrandbits(32)]) for _ in range(PKT_SZ // 4)]
    pk[0x60 // 4] = flags
    c.put(PKT, b"".join(le32(x) for x in pk))
    c.ecx, c.edx = pa, pd
    c.args = [PKT]
    c.dumps = [(PKT, PKT_SZ), (ATT + 0x20, 8)]
    c.a = dict(att=att if pa else None, pd=pd, pk=pk, patch=patch)
    return c


def m_crit(e, a):
    att, pk = a["att"], list(a["pk"])
    seed = list(att["seed"]) if att else None
    k = ms_rec(att)
    if e.t("att_mon", k is not None) and e.t("cb_nz", ms_byte(k, 0xA6) != 0):
        lo = lcg(seed)
        r = (lo % 100) & 0xFF
        if e.c("r_lt_cb", r, "<", ms_byte(k, 0xA6)):
            for off in (0x08, 0x10, 0x1C, 0x20, 0x24, 0x28):
                pk[off // 4] = u32(pk[off // 4] * 2)
            if e.t("def_set", a["pd"] != 0):
                if e.t("class_taken", bool(pk[0x60 // 4] & 0xF0)):
                    return ("obs", OBS_OVERLAY, (a["pd"], 0x36, 0), tuple(pk), tuple(seed))
                pk[0x60 // 4] |= 0x10
    return ("ret", tuple(pk), tuple(seed) if seed else None)


GEN = {"resist": gen_resist, "absorb": gen_absorb, "pct": gen_pct, "len": gen_len, "thm": gen_thm, "phh": gen_phh,
       "mode": gen_mode, "avoid": gen_avoid, "crit": gen_crit}
MODEL = {"resist": m_resist, "absorb": m_absorb, "pct": m_pct, "len": m_len, "thm": m_thm, "phh": m_phh,
         "mode": m_mode, "avoid": m_avoid, "crit": m_crit}
POP = {"resist": 0, "absorb": 0, "pct": 0, "len": 0, "thm": 8, "phh": 0, "mode": 4, "avoid": 4, "crit": 4}


def predict(fam, a, flip=None):
    e = E(flip)
    try:
        out = with_patch(a, lambda: MODEL[fam](e, a))
    except TypeError:               # a reversed null test dereferences no unit: an outcome no case can match
        return ("model-null",), e.names
    if fam in ("resist", "pct"):
        out = ("ret", u32(out))
    return out, e.names


# ----------------------------------------------------------------------------------------------- files
def write_spec(d):
    im = img()
    with open(os.path.join(d, "monstats.bin"), "wb") as f:
        f.write(bytes(im.ms))
    with open(os.path.join(d, "isc.bin"), "wb") as f:
        f.write(bytes(ISC_N * ISC_SZ))
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0xA78, MS), (0xA80, MS_N), (0xBCC, ISC), (0xBD4, ISC_N)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    lines = ["# plan 0066 S5e part 1 (tools/combat_s5e_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (MS, os.path.join(d, "monstats.bin")),
             "load %08x %s" % (ISC, os.path.join(d, "isc.bin"))]
    lines += ["guard %08x" % x for x in FATAL + ALLOC]
    lines += ["observe %08x" % x for x in (OBS_STATE, OBS_WCHECK, OBS_OVERLAY)]
    with open(os.path.join(d, "s5e.mem"), "w") as f:
        f.write("\n".join(lines) + "\n")


def build(limit=None):
    """every family's cases; --limit N keeps the first N of each (development runs only, never a kept run)."""
    cases = []
    for fam in FAMILIES:
        rnd = random.Random("n66t-s5e-" + fam)
        for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
            cases.append(GEN[fam](rnd))
    return cases


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    write_spec(d)
    cases = build(limit)
    with open(os.path.join(d, "s5e.cases"), "w") as f:
        for c in cases:
            f.write("\n".join(c.lines()) + "\n")
    print("cases %d -> %s" % (len(cases), os.path.join(d, "s5e.cases")))


def read_out(path):
    calls, reads, writes = [], [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "fn": int(p[2], 16), "dumps": {}}
            if p[3] == "STOP":
                c["stop"] = int(p[4], 16)
                c["msg"] = " ".join(p[5:])
            elif p[3] == "OBS":
                c["obs"] = int(p[4], 16)
                c["regs"] = dict(x.split("=") for x in p[6:])
            else:
                kv = dict(x.split("=") for x in p[3:])
                c.update(eax=int(kv["eax"], 16), pop=int(kv["pop"]))
            calls.append(c)
        elif p[0] == "A":
            calls[-1]["stack"] = bytes.fromhex(p[1])
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            (reads if p[0] == "R" else writes).append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
    return calls, reads, writes


def observed(fam, c):
    """-> the emulator's outcome in the model's shape, or None when it is not comparable."""
    if "stop" in c:
        return ("stop", c["stop"], c["msg"])
    dw = lambda addr, n: struct.unpack("<%dI" % (n // 4), c["dumps"][addr])  # noqa: E731
    if "obs" in c:
        st = c["stack"]
        ret = struct.unpack_from("<I", st, 0)[0]
        if fam == "phh":
            ecx = int(c["regs"]["ecx"], 16)
            esp = int(c["regs"]["esp"], 16)
            off = ecx - esp
            args = struct.unpack_from("<9I", st, off) if 0 <= off <= 64 - 36 else None
            return ("obs", c["obs"], args), ret
        if fam == "avoid":
            a = struct.unpack_from("<5I", st, 4)
            local = a[2] - int(c["regs"]["ebp"], 16)
            return ("obs", c["obs"], (a[0], a[1], u32(a[3]), a[4])), (ret, local)
        if fam == "crit":
            a = struct.unpack_from("<3I", st, 4)
            return ("obs", c["obs"], a, dw(PKT, PKT_SZ), dw(ATT + 0x20, 8)), ret
    if c["pop"] != POP[fam]:
        return ("pop", c["pop"]), None
    if fam in ("resist", "pct"):
        return ("ret", c["eax"]), None
    if fam == "absorb":
        return ("ret", c["eax"], dw(PKT + 0x48, 4)[0]), None
    if fam == "len":
        return ("pkt", dw(PKT + 0x18, 4) [:1] + dw(PKT + 0x2C, 12)), None
    if fam == "thm":
        return ("out",) + dw(OUT, 8), None
    if fam == "phh":
        return ("ret",), None
    if fam == "mode":
        return ("ret", c["eax"]), None
    if fam == "avoid":
        return ("ret", c["eax"], dw(DEF + 0x20, 8)), None
    if fam == "crit":
        s = dw(ATT + 0x20, 8)
        return ("ret", dw(PKT, PKT_SZ), s), None
    raise ValueError(fam)


def norm(fam, want, a):
    """the model's outcome with the parts the dumps cannot show filled in."""
    if fam == "avoid" and want[0] == "ret":
        seed = want[2] if want[2] is not None else tuple(a["dfn"]["seed"]) if a["dfn"] else None
        return ("ret", want[1], seed)
    if fam == "crit" and want[0] == "ret":
        return ("ret", want[1], want[2] if want[2] is not None else None)
    return want


def same(fam, want, got, a):
    if want[0] != got[0]:
        return False
    if fam == "avoid" and want[0] == "ret":
        return want[1] == got[1] and (want[2] is None or tuple(want[2]) == tuple(got[2]))
    if fam == "crit" and want[0] == "ret":
        return tuple(want[1]) == tuple(got[1]) and (want[2] is None or tuple(want[2]) == tuple(got[2]))
    if fam == "crit" and want[0] == "obs":
        return want[1] == got[1] and tuple(want[2]) == tuple(got[2]) and tuple(want[3]) == tuple(got[3]) \
            and tuple(want[4]) == tuple(got[4])
    if want[0] == "obs":
        return want[1] == got[1] and got[2] is not None and tuple(want[2]) == tuple(got[2])
    if want[0] == "model-null":
        return False
    return tuple(want) == tuple(got)


# reads the image holds as constants, and the tables of the memory spec (traced only when outside a declared range)
CONST_READS = ((BITMASK, BITMASK + 128, "g_BitMask32 0x006CE268 (.rdata), read by UNIT_TestStateBit"),
               (G_DT, G_DT + 4, "g_pDataTables 0x00744304 (.data), written by the spec's dword line"))


def account(reads, writes):
    bad = []
    for pc, addr, n, cnt in reads:
        if not any(lo <= addr and addr + n <= hi for lo, hi, _ in CONST_READS):
            bad.append(("R", pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        bad.append(("W", pc, addr, n, cnt))
    return bad


def cmd_check(d, limit=None):
    cases = build(limit)
    calls, reads, writes = read_out(os.path.join(d, "s5e.out"))
    if len(calls) != len(cases):
        print("CASES %d emulated %d: mismatch" % (len(cases), len(calls)))
        return 1
    bad = 0
    per = {f: [0, 0, {}] for f in FAMILIES}
    names_by_fam = {f: set() for f in FAMILIES}
    got_all = []
    for i, (c, k) in enumerate(zip(cases, calls)):
        fam = c.fam
        want, names = predict(fam, c.a)
        names_by_fam[fam] |= names
        got, site = observed(fam, k)
        want = norm(fam, want, c.a)
        ok = same(fam, want, got, c.a)
        if ok and want[0] == "obs":
            if fam == "avoid":
                ok = site == AVOID_SITE[want[3]]
            else:
                ok = site == CALL_SITE[fam]
        per[fam][0] += 1
        out_kind = want[0] + (":%x" % want[1] if want[0] == "obs" else "")
        if fam in ("resist", "pct", "mode"):
            out_kind = "%s=%d" % (want[0], s32(want[1])) if fam == "pct" else out_kind
        per[fam][2][out_kind] = per[fam][2].get(out_kind, 0) + 1
        if not ok:
            per[fam][1] += 1
            bad += 1
            if bad <= 20:
                print("MISMATCH %d %s want=%r got=%r site=%r" % (i, fam, want, got, site))
        got_all.append(got)
    for f in FAMILIES:
        n, b, kinds = per[f]
        print("FAMILY %s cases=%d mismatches=%d outcomes %s" % (f, n, b, " ".join(
            "%s:%d" % kv for kv in sorted(kinds.items()))))
    # controls
    ctl_bad, ctl_lines = 0, []
    for f in FAMILIES:
        for nm in sorted(names_by_fam[f]):
            sep = passed = 0
            for c, got in zip(cases, got_all):
                if c.fam != f:
                    continue
                base, _ = predict(f, c.a)
                alt, _ = predict(f, c.a, flip=nm)
                base, alt = norm(f, base, c.a), norm(f, alt, c.a)
                if not same(f, base, alt, c.a):
                    sep += 1
                    if same(f, alt, got, c.a):
                        passed += 1
            ctl_lines.append("CONTROL %s %s sep=%d passed=%d" % (f, nm, sep, passed))
            if passed:
                ctl_bad += 1
    print("\n".join(ctl_lines))
    nsep0 = sum(1 for x in ctl_lines if " sep=0 " in x)
    acc = account(reads, writes)
    for x in acc:
        print("UNACCOUNTED %s pc=%08x addr=%08x n=%d count=%d" % x)
    stops = sum(1 for k in calls if "stop" in k)
    print("S5E total cases=%d mismatches=%d stops=%d controls=%d unseparated=%d controls_passed=%d unaccounted=%d"
          % (len(cases), bad, stops, len(ctl_lines), nsep0, ctl_bad, len(acc)))
    return 1 if bad or ctl_bad or acc else 0


def cmd_manifest(d, write):
    names = sorted(x for x in os.listdir(d) if os.path.isfile(os.path.join(d, x)) and x != "manifest.sha256")
    out = []
    for n in names:
        with open(os.path.join(d, n), "rb") as f:
            out.append("%s  %s" % (hashlib.sha256(f.read()).hexdigest(), n))
    text = "\n".join(out) + "\n"
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as f:
            f.write(text)
    print(text, end="")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    o = ap.parse_args(argv)
    if o.cmd == "cases":
        cmd_cases(o.dir, o.limit)
        return 0
    if o.cmd == "check":
        return cmd_check(o.dir, o.limit)
    cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
