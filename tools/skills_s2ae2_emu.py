#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2ae part 2 (`lane/n66sa`): the mana checks and the missile collide filters under Ghidra's
p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared with the models below.

    python3 -I tools/skills_s2ae2_emu.py cases [--dir D] [--limit N]   write D/s2ae.cases, D/s2ae.mem and the tables
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s2ae.cases D/s2ae.mem > D/s2ae.out
    python3 -I tools/skills_s2ae2_emu.py check [--dir D] [--limit N]   compare, account for traced reads, controls
    python3 -I tools/skills_s2ae2_emu.py reach [--limit N]             model outcomes and branch reach per family
    python3 -I tools/skills_s2ae2_emu.py static                        objdump of every function the cases run
    python3 -I tools/skills_s2ae2_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66sa/s2ae/run2. Part 1's tool (tools/skills_s2ae_emu.py) and its run/ are unchanged; this
tool reuses its check machinery (build, predict, cmd_check) with its own families, tables and memory spec, and the
unit and stat-list builders of batch S5e part 1 (tools/combat_s5e_emu.py, unchanged). Every draw comes from
random.Random("n66sa-s2ae2-<family>"); the declared tables from random.Random("n66sa-s2ae2-tables").

Every callee runs whole on the declared image (no declared return) unless named as an observed boundary (ADR-0021):
the case ends at that call and its claim ends there. The allocator entries and the fatal path are guards.

Families (function, registers; inventory rows, d = skills/dispatch, m = skills/missiles):
  mana  0x00647540 SKILLS_ManaOk (EAX entry, ECX unit), whole, with sub_00644180_SkillLevelBonus,
        sub_00644150_ShrineSkillBonus, sub_004A89D0_SkillDescRec, sub_00611830_ExpMaxLevel, STATS_GetUnitStat,
        UNIT_HasState, 0x0063A400.                                                                  d36, d37
  srvm  0x0056C160 SKILLS_SrvManaCheck (ECX unit), whole, with UNIT_GetUsedSkill, 0x006439A0, 0x00643AD0,
        0x00644140, SKILLS_GetSkillLevel and the callees of mana.                                   d49
  filt  0x005A8730 sub_005A8730_CollideUnitFilter (ESI candidate, EDI owner, EBX Missiles record; game, missile),
        whole through UNIT_HasState, MISSDATA_IsLastHit, sub_00554200_UnitsHostile, sub_0058F0D0_MonsterOwner,
        sub_00650D70_AlignSame02, sub_006259B0_UnitAlignGet, UNIT_FindStatListByState,
        sub_00625650_StatListFindByState, sub_00625420_StatListGetStat, and for two players
        sub_0055B300_PlayerPairFlags with 0x006221A0 (the relation list at player data +0x38). Monster owners never
        resolve (MonsterOwner's +0x28 chain ends in 0) and no type-3 owner has +0xC8 bit 10, so 0x00552F60 (a
        guard) is not reached. No observed boundary in this part.                                     m47
  cpa   0x005A87F0 sub_005A87F0_CollidePlayerOrAlly (ECX candidate, EDX context), whole as filt.        m40
  cmon  0x005A87B0 sub_005A87B0_CollideMonster (ECX candidate, EDX context), whole as filt.          m41
  cun   0x005A8850 sub_005A8850_CollideUnit (ECX candidate, EDX context), whole as filt.             m42, m46
  cmis  0x005A8890 sub_005A8890_CollideMissile (ECX candidate), whole.                              m45

Controls as part 1: every named test reversed alone, every ordered compare's strictness switched alone; `sep`
counts the cases a control changes, `passed` those the emulator still matches (must be 0); `spec_*` controls are
the spec's own readings where they differ from the code. Stdlib only, plus objdump for `static`.
"""
import argparse
import os
import random
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import combat_s5e_emu as p1  # noqa: E402
import skills_s2ae_emu as B  # noqa: E402
from combat_s5e_emu import (u32, s32, le32, put_unit, has_state, ATT, DEF, G_DT, DT, MS, MS_N, ISC, ISC_N,  # noqa: E402
                            NSTATES, FATAL, ALLOC, SL_OFF, ARR_OFF, MD_OFF, BITMASK)

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sa", "s2ae", "run2")
FNS = {"mana": 0x00647540, "srvm": 0x0056C160, "filt": 0x005A8730, "cpa": 0x005A87F0, "cmon": 0x005A87B0,
       "cun": 0x005A8850, "cmis": 0x005A8890}
FAMILIES = ("mana", "srvm", "filt", "cpa", "cmon", "cun", "cmis")
NCASES = {"mana": 2500, "srvm": 1500, "filt": 3000, "cpa": 1200, "cmon": 800, "cun": 1200, "cmis": 800}
POP = {"mana": 0, "srvm": 0, "filt": 8, "cpa": 0, "cmon": 0, "cun": 0, "cmis": 0}
OBS_PAIR = 0x0055B300                 # sub_0055B300_PlayerPairFlags
SITE = {(f, OBS_PAIR): 0x00554297 for f in ("filt", "cpa", "cmon", "cun")}
p1.FNS.update(FNS)

OWN, MIS_U = 0x20002000, 0x20003000   # the owner unit, the missile unit
CTX, ENTRY, REC, XP, SKL = 0x20004000, 0x20004100, 0x20004200, 0x20004800, 0x20004900
SK2, SK2_N, SK2_SZ = 0x21300000, 24, 0x23C
SD, SD_N, SD_SZ = 0x21500000, 12, 0x120
MIS, MIS_N, MIS_SZ = 0x21600000, 16, 0x1A4
GCT = 0x0073C720                      # g_MissileCollideTypes: nine (filter, mask) pairs
G_XP = 0x0096C8A8                     # the pointer ExpMaxLevel reads (runtime data: declared in the memory spec)
ALIGN_STATE, ALIGN_STAT = 0x69, 0xAC

TABLES = None


def tables():
    global TABLES
    if TABLES is None:
        r = random.Random("n66sa-s2ae2-tables")
        sk = bytearray(r.getrandbits(8) for _ in range(SK2_N * SK2_SZ))
        for i in range(SK2_N):
            o = i * SK2_SZ
            struct.pack_into("<h", sk, o, r.choice([i, i, i, r.randrange(SK2_N), -1, SK2_N + 3]))
            sk[o + 0xC] = r.choice([0, 1, 2, 3, 4, 5, 6, 0xFF])
            struct.pack_into("<h", sk, o + 0x194, r.randrange(SD_N))
            sk[o + 0x1DC] = r.choice([0, 0, 1, 2, 3, 0x80, r.getrandbits(8)])
            struct.pack_into("<H", sk, o + 0x2E, r.choice([0x74, 0x74, 0, 0x73, 0x75, r.getrandbits(16)]))
            sk[o + 0x188] = r.choice([0, 8, 8, 8, 0, 3, 31, 33, r.getrandbits(8)])
            struct.pack_into("<h", sk, o + 0x18A, r.choice([0, 1, 5, 20, -3, r.randint(-0x8000, 0x7FFF)]))
            struct.pack_into("<h", sk, o + 0x18C, r.choice([0, 1, 2, 4, -1, r.randint(-0x8000, 0x7FFF)]))
        sd = bytearray(r.getrandbits(8) for _ in range(SD_N * SD_SZ))
        for i in range(SD_N):
            sd[i * SD_SZ + 2] = r.choice([0, 0, 1, 2, 3, r.getrandbits(8)])
        ms = bytearray(r.getrandbits(8) for _ in range(MIS_N * MIS_SZ))
        TABLES = (sk, sd, ms)
    return TABLES


class Case(p1.Case):
    pass


# ----------------------------------------------------------------------------------------------- stat lists
def relist(c, rnd, u, keys):
    """Rewrite the live stat array of a put_unit unit with {stat << 16 | layer: value}, sorted by key."""
    sl = u["base"] + SL_OFF
    live = 0x48 if u["listflag"] else 0x24
    arr = u["base"] + ARR_OFF
    ks = sorted(keys)
    for i, k in enumerate(ks):
        c.put(arr + 8 * i, le32(k) + le32(keys[k]))
    c.put(sl + live, le32(arr))
    c.put(sl + live + 4, struct.pack("<H", len(ks)) + bytes(2))
    u["keys"] = {k: s32(v) for k, v in keys.items()}


def gstat(u, s, layer=0):
    """STATS_GetUnitStat(u, s, layer): the layer's low 16 bits form the key."""
    if u is None or u.get("nolist"):
        return 0
    if s < 0 or s >= ISC_N:
        return 0
    return u["keys"].get((s << 16) | (layer & 0xFFFF), 0)


def chains(c, rnd, u, n_has):
    """The unit's state stat lists at +0x3C and +0x40 (chained by +0x2C); n_has of the elements carry state 0x69
    and a stat-172 value. -> [[(state, value)], [...]] in walk order."""
    sl = u["base"] + SL_OFF
    out, slot = [], 0
    for off in (0x3C, 0x40):
        n = rnd.choice([0, 0, 1, 2])
        els = []
        prev = sl + off
        for _ in range(n):
            el = u["base"] + 0x800 + 0x100 * slot
            slot += 1
            st = ALIGN_STATE if n_has > 0 and rnd.random() < 0.6 else rnd.choice([0x68, 0x6A, 0x69 + 0x100, 3])
            if st == ALIGN_STATE:
                n_has -= 1
            flag = rnd.random() < 0.5
            c.put(el, bytes(rnd.getrandbits(8) for _ in range(0x60)))
            c.put(el + 0x10, le32((0x80000000 if flag else 0) | rnd.getrandbits(31)))
            c.put(el + 0x14, le32(st))
            c.put(el + 0x44, le32(0))
            v = rnd.choice([0, 1, 2, 2, 2, 3, -1, rnd.getrandbits(32)])
            k = {(ALIGN_STAT << 16): v, (ALIGN_STAT << 16) | 1: rnd.getrandbits(32), (0x10 << 16): 5}
            if rnd.random() < 0.2:
                del k[ALIGN_STAT << 16]
                v = 0
            arr = el + 0x80
            ks = sorted(k)
            for i, kk in enumerate(ks):
                c.put(arr + 8 * i, le32(kk) + le32(k[kk]))
            live = 0x48 if flag else 0x24
            c.put(el + live, le32(arr))
            c.put(el + live + 4, struct.pack("<H", len(ks)) + bytes(2))
            c.put(prev, le32(el))
            prev = el + 0x2C
            els.append((st, s32(v)))
        c.put(prev, le32(0))
        out.append(els)
    u["chains"] = out
    return out


# ----------------------------------------------------------------------------------------------- mana, srvm
def sk_row(i, off, fmt):
    sk = tables()[0]
    return struct.unpack_from(fmt, sk, i * SK2_SZ + off)[0]


def rec_view(rec):
    """rec: ('row', i) for a Skills table row, ('blk', bytes) for the scratch record."""
    if rec[0] == "row":
        sk = tables()[0]
        return bytes(sk[rec[1] * SK2_SZ:(rec[1] + 1) * SK2_SZ])
    return rec[1]


def rv(rb, off, fmt):
    if off < 0:
        raise IndexError(off)
    try:
        return struct.unpack_from(fmt, rb, off)[0]
    except struct.error:
        raise IndexError(off)


def put_mana_unit(c, rnd, typ, sid_hint, cls_hint):
    cls = cls_hint if 0 <= cls_hint < 7 and rnd.random() < 0.6 else rnd.randrange(7)
    st = []
    if rnd.random() < 0.35:
        st.append(114)
    if rnd.random() < 0.3:
        st.append(134)
    u = put_unit(c, rnd, ATT, typ, cls, {}, st)
    v = lambda: rnd.choice([0, 0, 1, 2, 3, 4, 7, -2, rnd.randint(1, 40), rnd.getrandbits(32)])  # noqa: E731
    keys = {}
    for s, lay in ((127, 0), (83, cls), (83, (cls + 1) % 7), (97, sid_hint), (97, sid_hint + 1), (107, sid_hint),
                   (107, 0), (126, 1), (126, 2), (126, 3), (126, 0x80)):
        if rnd.random() < 0.55:
            keys[(s << 16) | (lay & 0xFFFF)] = u32(v())
    for t in range(1, 4):
        if rnd.random() < 0.4:
            keys[(188 << 16) | ((t + cls * 8 - 1) & 0xFFFF)] = u32(v())
    for s in (6, 8):
        if rnd.random() < 0.9:
            keys[s << 16] = u32(rnd.choice([0, rnd.randint(0, 3000), rnd.randint(0, 200) * 256,
                                            rnd.randint(0, 200) * 256 - 1, rnd.getrandbits(32)]))
    relist(c, rnd, u, keys)
    c8 = rnd.getrandbits(32)
    c.put(ATT + 0xC8, le32(c8))
    u["c8"] = c8
    return u


def put_mana_entry(c, rnd):
    if rnd.random() < 0.8:
        i = rnd.randrange(SK2_N)
        rec = ("row", i)
        addr = SK2 + i * SK2_SZ
    else:
        b = bytearray(rnd.getrandbits(8) for _ in range(SK2_SZ))
        struct.pack_into("<h", b, 0, rnd.choice([rnd.randrange(SK2_N), -2, SK2_N]))
        b[0x188] = rnd.choice([0, 8, 31])
        rec = ("blk", bytes(b))
        c.put(REC, bytes(b))
        addr = REC
    base = rnd.choice([0, 1, 2, 5, 20, 30, 99, 100, -3, rnd.randint(1, 60), rnd.getrandbits(32)])
    bon = rnd.choice([0, 0, 1, 3, -5, rnd.randint(0, 20)])
    item = rnd.choice([0xFFFFFFFF] * 6 + [0, rnd.getrandbits(32)])
    chg = rnd.choice([0, 1, 5, -1, rnd.getrandbits(32)])
    c.put(ENTRY, le32(addr) + bytes(rnd.getrandbits(8) for _ in range(0x24)) + le32(base) + le32(bon)
          + bytes(rnd.getrandbits(8) for _ in range(4)) + le32(item) + le32(chg))
    xp = rnd.choice([99, 99, 20, 1, 0, 50])
    c.put(XP, le32(xp))
    return dict(rec=rec, base=s32(base), bon=s32(bon), item=item, chg=s32(chg), xp=xp)


def target(c, rnd, u, ent, fam):
    """Set stats 6 and 8 at the model's cost, or one below or above it, so that a wrong level term or cost changes the
    returned bit (the compare is the only output)."""
    if u is None or rnd.random() < 0.35 or ent["item"] != 0xFFFFFFFF:
        return
    e = p1.E()
    try:
        lvl = s32(ent["base"] + bonus(e, u, ent))
    except IndexError:
        return
    lvl = min(max(lvl, 0), ent["xp"])
    lvl = max(s32(lvl - 1), 0)
    cst = cost(rec_view(ent["rec"]), lvl)
    keys = {k: u32(v) for k, v in u["keys"].items()}
    for st in (6, 8):
        keys[st << 16] = u32(cst + rnd.choice([0, 0, -1, -1, 1]))
    relist(c, rnd, u, keys)


def gen_mana(rnd):
    c = Case("mana")
    ent = put_mana_entry(c, rnd)
    sid = rv(rec_view(ent["rec"]), 0, "<h")
    chc = rv(rec_view(ent["rec"]), 0xC, "<b")
    k = rnd.random()
    if k < 0.06:
        u = None
        c.regs = {"EAX": ENTRY}
        c.ecx = 0
    else:
        typ = rnd.choice([0, 0, 0, 0, 1, 1, 2, 3])
        u = put_mana_unit(c, rnd, typ, sid, chc)
        target(c, rnd, u, ent, "mana")
        c.regs = {"EAX": ENTRY}
        c.ecx = ATT
    c.a = dict(u=u, ent=ent)
    return c


def bonus(e, u, ent):
    rb = rec_view(ent["rec"])
    sid = rv(rb, 0, "<h")
    if not e.t("b_sid_ok", 0 <= sid < SK2_N):
        return 0
    x = ent["bon"]
    if e.t("b_shrine", has_state(u, 134)):
        x += 2
    x += gstat(u, 127)
    if e.t("b_player", u is not None and u["type"] == 0):
        if e.t("b_ownclass", rv(rb, 0xC, "<b") == u["cls"]):
            x += gstat(u, 83, u["cls"])
            d = rv(tables()[0], sid * SK2_SZ + 0x194, "<h")
            t = rv(tables()[1], d * SD_SZ + 2, "<b")     # movsx: a signed byte
            if e.t("b_tab", t != 0):
                x += gstat(u, 188, t + u["cls"] * 8 - 1)
            a = gstat(u, 97, sid)
            if e.c("b_cap3", a, ">", 3):
                a = 3
            x += a
        else:
            x += gstat(u, 97, sid)
    else:
        a = gstat(u, 97, sid)
        if e.c("b_base_gt0", ent["base"], ">", 0):
            if e.c("b_cap3n", a, ">", 3):
                a = 3
        x += a
    pg = rb[0x1DC]
    if e.t("b_elem", pg != 0):
        x += gstat(u, 126, pg)
    return s32(x + gstat(u, 107, sid))


def cost(rb, lvl):
    return s32((s32(rv(rb, 0x18C, "<h") * lvl) + rv(rb, 0x18A, "<h")) << (rb[0x188] & 31))


def m_mana(e, a):
    u, ent = a["u"], a["ent"]
    if e.t("item", ent["item"] != 0xFFFFFFFF):
        return ("ret", 1 if e.c("chg_gt0", ent["chg"], ">", 0) else 0)
    rb = rec_view(ent["rec"])
    if e.t("unit", u is not None):
        lvl = s32(ent["base"] + bonus(e, u, ent))
        if e.c("lvl_le0", lvl, "<=", 0):
            lvl = 0
        if not e.c("lvl_lt_max", lvl, "<", ent["xp"]):
            lvl = ent["xp"]
    else:
        lvl = 0
    lvl = s32(lvl - 1)
    if e.c("lvl_lt0", lvl, "<", 0):
        lvl = 0
    if e.flip == "spec_no_minus1":
        lvl += 1
    e.names.add("spec_no_minus1")
    cst = cost(rb, lvl)
    if e.t("st114", has_state(u, 114)):
        return ("ret", 1 if e.c("life_ge", gstat(u, 6), ">=", cst) else 0)
    if e.t("sdf116", rv(rb, 0x2E, "<H") == 0x74) and e.t("c8b3", u is not None and (u["c8"] >> 3) & 1):
        return ("ret", 1)
    return ("ret", 1 if e.c("mana_ge", gstat(u, 8), ">=", cst) else 0)


def gen_srvm(rnd):
    c = Case("srvm")
    ent = put_mana_entry(c, rnd)
    sid = rv(rec_view(ent["rec"]), 0, "<h")
    chc = rv(rec_view(ent["rec"]), 0xC, "<b")
    k = rnd.random()
    if k < 0.05:
        c.ecx = 0
        c.a = dict(u=None, ent=ent, used=False, nullrec=False)
        return c
    typ = rnd.choice([0, 0, 0, 0, 0, 1, 2, 3])
    u = put_mana_unit(c, rnd, typ, sid, chc)
    target(c, rnd, u, ent, "srvm")
    used = rnd.random() < 0.92
    nullrec = rnd.random() < 0.05
    if nullrec:
        c.put(ENTRY, le32(0))
    if rnd.random() < 0.04:
        c.put(ATT + 0xA8, le32(0))
        used = None
    else:
        c.put(ATT + 0xA8, le32(SKL))
        c.put(SKL, bytes(rnd.getrandbits(8) for _ in range(0x10)) + le32(ENTRY if used else 0))
    c.ecx = ATT
    c.a = dict(u=u, ent=ent, used=used, nullrec=nullrec)
    return c


def m_srvm(e, a):
    u, ent = a["u"], a["ent"]
    if not e.t("unit", u is not None) or not e.t("player", u["type"] == 0):
        return ("ret", 1)
    if not e.t("used", bool(a["used"])):
        return ("ret", 0)
    if e.t("item", ent["item"] != 0xFFFFFFFF):
        return ("ret", 1 if e.c("chg_gt0", ent["chg"], ">", 0) else 0)
    if not e.t("rec", not a["nullrec"]):
        return ("ret", 0)
    rb = rec_view(ent["rec"])
    lvl = s32(ent["base"] + bonus(e, u, ent))
    if e.c("lvl_le0", lvl, "<=", 0):
        lvl = 0
    if not e.c("lvl_lt_max", lvl, "<", ent["xp"]):
        lvl = ent["xp"]
    lvl = s32(lvl - 1)
    if e.c("lvl_lt0", lvl, "<", 0):
        lvl = 0
    cst = cost(rb, lvl)
    e.names.add("spec_st114")
    if e.flip == "spec_st114" and has_state(u, 114):
        return ("ret", 1 if gstat(u, 6) >= cst else 0)
    if e.t("sdf116", rv(rb, 0x2E, "<H") == 0x74) and e.t("c8b3", (u["c8"] >> 3) & 1):
        return ("ret", 1)
    return ("ret", 1 if e.c("mana_ge", gstat(u, 8), ">=", cst) else 0)


# ----------------------------------------------------------------------------------------------- collide
def put_coll_unit(c, rnd, base, typ, role):
    """A candidate or owner: +0xC4 bits, +0x0C id, MonsterOwner's chain ending in 0, the alignment chains."""
    nolist = rnd.random() < 0.06
    mdf = -1 if rnd.random() < 0.15 and typ != 0 else None
    u = put_unit(c, rnd, base, typ, rnd.randrange(7), {}, [86] if rnd.random() < 0.4 else [], nolist=nolist,
                 md_flags=mdf, fc4=rnd.getrandbits(32) | (0xC if rnd.random() < 0.6 else 0))
    u["nolist"] = nolist
    uid = rnd.getrandbits(32)
    c.put(base + 0xC, le32(uid))
    u["id"] = uid
    c.put(base + 0xC8, le32(rnd.getrandbits(32) & ~0x400))
    if typ == 0:                       # a player's data block holds the relation list PlayerPairFlags walks
        md = base + MD_OFF
        c.put(base + 0x14, le32(md))
        rel = []
        prev = md + 0x38
        for j in range(rnd.choice([0, 1, 1, 2, 3])):
            node = base + 0xC00 + 0x20 * j
            rid = rnd.choice(["cand", "own", "rnd"])
            fl = rnd.choice([8, 8, 0, 0xFFFFFFFF, 0xFFFFFFF7, rnd.getrandbits(32)])
            c.put(node, le32(0) + le32(fl) + bytes(rnd.getrandbits(8) for _ in range(8)))
            c.put(prev, le32(node))
            prev = node + 0x10
            rel.append([node, rid, fl])
        c.put(prev, le32(0))
        u["rel"] = rel
        mdf = None
    if mdf != -1:
        md = base + MD_OFF
        if rnd.random() < 0.5:
            c.put(md + 0x28, le32(0))
        else:
            c.put(md + 0x28, le32(md + 0x40))
            c.put(md + 0x40 + 0x28, le32(0))
    if not nolist:
        relist(c, rnd, u, {(0x10 << 16): 3})
        chains(c, rnd, u, rnd.choice([0, 1, 1, 2]))
    return u


def align(e, u):
    if u is None or u.get("nolist"):
        return 0
    if u32(u["type"]) > 1:
        return 2
    if not u["listflag"]:
        return 0
    for ch in u["chains"]:
        for st, v in ch:
            if st == ALIGN_STATE:
                return v
    return 0


def same02(e, a, b):
    if a is None or b is None:
        return 0
    if a is b:
        return 1
    x, y = align(e, a), align(e, b)
    if x == 0:
        return 1 if y == 0 else 0
    if x == 2:
        return 1 if y == 2 else 0
    return 0


def hostile(e, o, cand):
    """sub_00554200_UnitsHostile(owner, cand) -> ('val', v) or the observed pair boundary."""
    if e.t("h_same", o is cand):
        return ("val", 0)
    if o is not None and o["type"] == 0 and cand is not None and cand["type"] == 0:
        for node, rid, fl in o["rel"]:          # sub_0055B300_PlayerPairFlags(o, cand, 8), whole
            if e.t("p_id", rid == cand["id"]):
                e.names.add("spec_any_flag")
                return ("val", (fl != 0) if e.flip == "spec_any_flag" else fl & 8)
        return ("val", 0)
    return ("val", 0 if e.t("h_align", same02(e, o, cand)) else 1)


def gen_coll_ctx(c, rnd, cand_base):
    """The filter's inputs beside the candidate: the owner (none, the candidate, another unit), the missile unit,
    the Missiles record (+0x187 CollideFriend, +0x188 NextHit)."""
    rec = bytearray(rnd.getrandbits(8) for _ in range(MIS_SZ))
    rec[0x187] = rnd.choice([0, 0, 1, rnd.getrandbits(8)])
    rec[0x188] = rnd.choice([0, 0, 1, rnd.getrandbits(8)])
    c.put(REC, bytes(rec))
    ok = rnd.random()
    if ok < 0.15:
        owner = None
    elif ok < 0.25:
        owner = "cand"
    else:
        owner = put_coll_unit(c, rnd, OWN, rnd.choice([0, 0, 1, 1, 1, 2, 3, 4]), "owner")
    mt = rnd.random()
    mis = None
    if mt < 0.1:
        maddr = 0
    else:
        maddr = MIS_U
        mtype = 3 if rnd.random() < 0.85 else rnd.choice([0, 1, 4])
        mcls = rnd.choice([rnd.randrange(MIS_N)] * 6 + [-1, MIS_N, MIS_N + 7])
        c.put(MIS_U, le32(mtype) + le32(mcls) + bytes(rnd.getrandbits(8) for _ in range(0xC)))
        mdat = rnd.random() < 0.9
        c.put(MIS_U + 0x14, le32(MIS_U + 0x100 if mdat else 0))
        mis = dict(type=mtype, cls=mcls, md=mdat)
        if mdat:
            mis["t"], mis["id"] = None, None
            c.put(MIS_U + 0x100, bytes(rnd.getrandbits(8) for _ in range(0x18)))
            mis["hit"] = rnd.random() < 0.5
        game = rnd.getrandbits(32)
    game = rnd.getrandbits(32)
    return dict(rec=bytes(rec), owner=owner, maddr=maddr, mis=mis, game=game)


def finish_rel(c, rnd, units):
    """Write each relation node's id: the candidate's, the owner's, or another; ids resolved once both exist."""
    ids = {k: u["id"] for k, u in units.items() if u is not None}
    for u in units.values():
        if u is None or "rel" not in u:
            continue
        for r in u["rel"]:
            if r[1] in ids and rnd.random() < 0.85:
                v = ids[r[1]]
            else:
                v = rnd.getrandbits(32)
            c.put(r[0], le32(v))
            r[1] = v


def finish_mis(c, rnd, x, cand):
    """Write the missile data's last-hit type and id: the candidate's (a hit) or near misses."""
    m = x["mis"]
    if m is None or not m["md"]:
        return
    if cand is not None and m["hit"]:
        t, i = cand["type"], cand["id"]
        k = rnd.random()
        if k < 0.15:
            t ^= 1
        elif k < 0.3:
            i ^= 1 << rnd.randrange(32)
    else:
        t, i = rnd.choice([0, 1, 3]), rnd.getrandbits(32)
    c.put(MIS_U + 0x100 + 0x18, le32(t) + le32(i))
    m["t"], m["id"] = u32(t), u32(i)


def last_hit(e, x, cand):
    m = x["mis"]
    if m is None or cand is None:
        return False
    if m["type"] != 3 or not 0 <= m["cls"] < MIS_N:
        return False
    if not tables()[2][m["cls"] * MIS_SZ + 4] & 1:
        return False
    if not m["md"]:
        return False
    return e.t("lh_match", m["t"] == u32(cand["type"]) and m["id"] == cand["id"])


def filt(e, x, cand):
    if not e.t("f_cand", cand is not None):
        return ("val", 0)
    if not e.t("f_bit3", (cand["fc4"] >> 3) & 1) or not e.t("f_bit2", (cand["fc4"] >> 2) & 1):
        return ("val", 0)
    if e.t("f_nexthit", x["rec"][0x188] != 0) and e.t("f_st86", has_state(cand, 86)):
        return ("val", 0)
    if e.t("f_lasthit", last_hit(e, x, cand)):
        return ("val", 0)
    o = cand if x["owner"] == "cand" else x["owner"]
    if e.t("f_owner", o is not None):
        h = hostile(e, o, cand)
        if h[0] == "obs":
            return h
        if not e.t("f_hostile", h[1] != 0) and not e.t("f_friend", x["rec"][0x187] != 0):
            return ("val", 0)
    return ("val", 1)


def gen_cand(c, rnd, fam):
    if rnd.random() < 0.06:
        return None
    if fam == "cpa":
        typ = rnd.choice([0, 0, 1, 1, 1, 2, 3, 4])
    else:
        typ = rnd.choice([0, 0, 1, 1, 2, 3, 4, 5, -1])
    return put_coll_unit(c, rnd, DEF, typ, "cand")


def gen_filt(rnd):
    c = Case("filt")
    cand = gen_cand(c, rnd, "filt")
    x = gen_coll_ctx(c, rnd, DEF)
    finish_rel(c, rnd, {"cand": cand, "own": x["owner"] if isinstance(x["owner"], dict) else None})
    finish_mis(c, rnd, x, cand)
    own = DEF if x["owner"] == "cand" else (0 if x["owner"] is None else OWN)
    c.regs = {"ESI": 0 if cand is None else DEF, "EDI": own, "EBX": REC}
    c.args = [x["game"], x["maddr"]]
    c.a = dict(cand=cand, x=x)
    return c


def m_filt(e, a):
    r = filt(e, a["x"], a["cand"])
    return r if r[0] == "obs" else ("ret", r[1])


def gen_wrap(fam):
    def gen(rnd):
        c = Case(fam)
        cand = gen_cand(c, rnd, fam)
        x = gen_coll_ctx(c, rnd, DEF)
        finish_rel(c, rnd, {"cand": cand, "own": x["owner"] if isinstance(x["owner"], dict) else None})
        finish_mis(c, rnd, x, cand)
        own = DEF if x["owner"] == "cand" else (0 if x["owner"] is None else OWN)
        k = rnd.random()
        ctx = "ok"
        if k < 0.05:
            ctx = "null"
        elif k < 0.1:
            ctx = "norec"
        c.put(CTX, le32(x["game"]) + le32(x["maddr"]) + le32(own) + le32(0 if ctx == "norec" else REC))
        c.ecx = 0 if cand is None else DEF
        c.edx = 0 if ctx == "null" else CTX
        c.a = dict(cand=cand, x=x, ctx=ctx)
        return c
    return gen


def m_wrap(fam):
    def m(e, a):
        cand = a["cand"]
        if not e.t("w_ctx", a["ctx"] == "ok"):
            return ("ret", 0)
        if not e.t("w_cand", cand is not None):
            return ("ret", 0)
        t = s32(cand["type"])
        if fam == "cmon":
            if not e.t("w_mon", t == 1):
                return ("ret", 0)
        elif fam == "cun":
            if not (e.c("w_ge0", t, ">=", 0) and e.c("w_le1", t, "<=", 1)):
                return ("ret", 0)
        else:
            if e.t("w_player", t == 0):
                pass
            elif e.t("w_mon", t == 1):
                if not e.t("w_align2", align(e, cand) == 2):
                    return ("ret", 0)
            else:
                return ("ret", 0)
        r = filt(e, a["x"], cand)
        return r if r[0] == "obs" else ("ret", 1 if r[1] else 0)
    return m


def gen_cmis(rnd):
    c = Case("cmis")
    if rnd.random() < 0.06:
        c.ecx = 0
        c.a = dict(m=None)
        return c
    t = rnd.choice([3, 3, 3, 3, 0, 1, 2, 4])
    cls = rnd.choice([rnd.randrange(MIS_N)] * 6 + [-1, -5, MIS_N, MIS_N + 2])
    c.put(MIS_U, le32(t) + le32(cls))
    c.ecx = MIS_U
    c.a = dict(m=dict(type=t, cls=cls))
    return c


def m_cmis(e, a):
    m = a["m"]
    if not e.t("m_unit", m is not None) or not e.t("m_type3", m["type"] == 3):
        return ("ret", 0)
    if not e.c("m_ge0", m["cls"], ">=", 0) or not e.c("m_lt_n", m["cls"], "<", MIS_N):
        return ("ret", 0)
    return ("ret", 1 if e.t("m_candestroy", tables()[2][m["cls"] * MIS_SZ + 4] & 0x10) else 0)


GEN = {"mana": gen_mana, "srvm": gen_srvm, "filt": gen_filt, "cpa": gen_wrap("cpa"), "cmon": gen_wrap("cmon"),
       "cun": gen_wrap("cun"), "cmis": gen_cmis}
MODEL = {"mana": m_mana, "srvm": m_srvm, "filt": m_filt, "cpa": m_wrap("cpa"), "cmon": m_wrap("cmon"),
         "cun": m_wrap("cun"), "cmis": m_cmis}


# ----------------------------------------------------------------------------------------------- spec, check
def write_spec(d):
    sk, sd, ms = tables()
    for name, b in (("isc.bin", bytes(ISC_N * p1.ISC_SZ)), ("skills.bin", bytes(sk)), ("skilldesc.bin", bytes(sd)),
                    ("missiles.bin", bytes(ms))):
        with open(os.path.join(d, name), "wb") as f:
            f.write(b)
    dt = bytearray(0x1000)
    for off, v in ((0xC4, NSTATES), (0xB64, MIS), (0xB6C, MIS_N), (0xB8C, SD), (0xB94, SD_N), (0xB98, SK2),
                   (0xBA0, SK2_N), (0xBCC, ISC), (0xBD4, ISC_N)):
        struct.pack_into("<I", dt, off, v)
    with open(os.path.join(d, "dt.bin"), "wb") as f:
        f.write(bytes(dt))
    lines = ["# plan 0066 S2ae part 2 (tools/skills_s2ae2_emu.py): declared tables",
             "dword %08x %08x" % (G_DT, DT),
             "dword %08x %08x" % (G_XP, XP),
             "load %08x %s" % (DT, os.path.join(d, "dt.bin")),
             "load %08x %s" % (ISC, os.path.join(d, "isc.bin")),
             "load %08x %s" % (SK2, os.path.join(d, "skills.bin")),
             "load %08x %s" % (SD, os.path.join(d, "skilldesc.bin")),
             "load %08x %s" % (MIS, os.path.join(d, "missiles.bin"))]
    lines += ["guard %08x" % x for x in FATAL + ALLOC + (0x00552F60,)]
    with open(os.path.join(d, "s2ae.mem"), "w") as f:
        f.write("\n".join(lines) + "\n")


def observed(fam, k):
    if "stop" in k:
        return ("stop", k["stop"], k["msg"]), None
    if "obs" in k:
        st = k["stack"]
        ret = struct.unpack_from("<I", st, 0)[0]
        regs = (int(k["regs"]["ecx"], 16), int(k["regs"]["edx"], 16), struct.unpack_from("<I", st, 4)[0])
        return ("obs", k["obs"], regs), ret
    if k["pop"] != POP[fam]:
        return ("pop", k["pop"]), None
    if fam == "mana" or fam == "srvm":
        return ("ret", k["eax"]), None
    return ("ret", k["eax"]), None


def norm(fam, want):
    return want


def account(reads, writes):
    bad = []
    for pc, addr, n, cnt in reads:
        if not (BITMASK <= addr and addr + n <= BITMASK + 128):
            bad.append(("R", pc, addr, n, cnt))
    for pc, addr, n, cnt in writes:
        bad.append(("W", pc, addr, n, cnt))
    return bad


def install():
    """Point part 1's check machinery at this part's families (its module state only; part 1's file is unchanged)."""
    B.FNS, B.FAMILIES, B.NCASES, B.POP, B.SITE = FNS, FAMILIES, NCASES, POP, SITE
    B.GEN, B.MODEL = GEN, MODEL
    B.observed, B.norm, B.account, B.write_spec = observed, norm, account, write_spec
    B.Case = Case
    _build = B.build

    def build(limit=None):
        cases = []
        for fam in FAMILIES:
            rnd = random.Random("n66sa-s2ae2-" + fam)
            for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
                cases.append(GEN[fam](rnd))
        return cases
    B.build = build
    return _build


STATIC = (
    ("mana", 0x00647540, 0x00647634),
    ("srvm", 0x0056C160, 0x0056C207),
    ("bonus", 0x00644180, 0x00644296),
    ("shrine", 0x00644150, 0x00644170),
    ("getlvl", 0x006442A0, 0x006442FC),
    ("explvl", 0x00611830, 0x00611859),
    ("descrec", 0x004A89D0, 0x004A8A15),
    ("used", 0x00620250, 0x00620286),
    ("used2", 0x006439A0, 0x006439AB),
    ("item", 0x00643AD0, 0x00643AFE),
    ("recget", 0x00644140, 0x0064414A),
    ("bit3", 0x0063A400, 0x0063A41C),
    ("filt", 0x005A8730, 0x005A87A1),
    ("cmon", 0x005A87B0, 0x005A87E6),
    ("cpa", 0x005A87F0, 0x005A8842),
    ("cun", 0x005A8850, 0x005A888C),
    ("cmis", 0x005A8890, 0x005A88D2),
    ("lasthit", 0x0064A470, 0x0064A4DC),
    ("hostile", 0x00554200, 0x005542B3),
    ("monowner", 0x0058F0D0, 0x0058F100),
    ("same02", 0x00650D70, 0x00650DC9),
    ("align", 0x006259B0, 0x006259EF),
    ("findbystate", 0x006256B0, 0x006256D8),
    ("findbystate2", 0x00625650, 0x006256A8),
    ("getstat", 0x00625420, 0x00625473),
    ("unitgetstat", 0x00625480, 0x006254DE),
    ("pair", 0x0055B300, 0x0055B34B),
    ("pdata", 0x006221A0, 0x006221DA),
    ("hasstate", 0x00639DF0, 0x00639E2E),
)


def cmd_static():
    if p1.img() is None:
        return 1
    for label, lo, hi in STATIC:
        out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-M", "intel", "--start-address=0x%x" % lo,
                              "--stop-address=0x%x" % hi, p1.EXE], capture_output=True, text=True, check=True).stdout
        for ln in out.splitlines():
            ln = ln.strip()
            if ln and ln[0] in "0123456789abcdef" and ":\t" in ln:
                print("%s %s" % (label, " ".join(ln.split())))
    # g_MissileCollideTypes 0x0073C720: nine (filter, mask) pairs in the image, and every .text operand that names an
    # address inside them (the reference scan of ADR-0015 (2) for a .data table: a store would show here)
    import sweep_s4b as W
    raw = B.img_bytes(GCT, 9 * 8)
    for i in range(9):
        fn, mask = struct.unpack_from("<2I", raw, 8 * i)
        print("GCT type=%d filter=%08x mask=%04x" % (i, fn, mask))
    print("SECTION %08x %s" % (GCT, W.section_of(GCT)))
    A = W.asm()
    hits = []
    for va in sorted(A.ins):
        mn, ops = A.ins[va]
        for tok in ops.replace(",", " ").replace("[", " ").replace("]", " ").replace("+", " ").replace("*", " ").split():
            if tok.startswith("0x"):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                if GCT <= v < GCT + 9 * 8:
                    hits.append("%08x %s %s" % (va, mn, ops))
    for h in hits:
        print("GCT-REF " + h)
    print("GCT-REF count=%d" % len(hits))
    return 0


class RE(p1.E):
    """The unflipped model, recording each named test's outcome: the branches reached and not reached."""

    def __init__(self):
        super().__init__(None)
        self.seen = []

    def t(self, name, cond):
        r = super().t(name, cond)
        self.seen.append((name, r))
        return r

    def c(self, name, a, op, b):
        r = super().c(name, a, op, b)
        self.seen.append((name, r))
        return r


def cmd_reach(limit=None):
    """Per family: the return values and observed boundaries the model predicts, and each test's true/false count
    (from the same cases as check)."""
    cases = B.build(limit)
    outs, reach = {}, {}
    for c in cases:
        e = RE()
        w = MODEL[c.fam](e, c.a)
        k = "%s:%s" % (w[0], ("%x" % w[1]) if w[0] == "obs" else w[1])
        outs.setdefault(c.fam, {}).setdefault(k, 0)
        outs[c.fam][k] += 1
        for name, r in e.seen:
            d = reach.setdefault(c.fam, {}).setdefault(name, [0, 0])
            d[0 if r else 1] += 1
    for f in FAMILIES:
        print("OUTCOMES %s %s" % (f, " ".join("%s=%d" % kv for kv in sorted(outs.get(f, {}).items()))))
        for name, (tt, ff) in sorted(reach.get(f, {}).items()):
            print("REACH %s %s true=%d false=%d" % (f, name, tt, ff))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "reach", "static", "manifest"))
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
    if o.cmd == "reach":
        return cmd_reach(o.limit)
    if o.cmd == "static":
        return cmd_static()
    B.cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
