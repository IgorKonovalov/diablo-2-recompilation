#!/usr/bin/env python3
"""Plan 0052 Phase 1c, the Uber event (`lane/r52n`): the helpers and the class- and level-gated code around Uber Mephisto,
Uber Diablo and Uber Baal, run under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java and
compared with the models below. No game run, no slot. Same method as tools/ai_cat_emu11.py.

    python3 -I tools/ai_uber_emu.py cases [--dir D]     write D/<family>.cases and D/<family>.mem
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_uber_emu.py check [--dir D]     compare every D/<family>.out with its model, run the controls

Default D: workspace/logs/r52n/emu. Every case draw comes from random.Random("r52n-<family>"). `qdeath` reads its two byte
tables and two jump tables from the pinned image at run time (argument --exe), so no table bytes live in this file.

Families (function; what a case declares; where it ends):
  ucount  0x005DD140 the search callback: searcher and candidate (type, class, mode, +0xC6, path x/y; no MonStats2 row, so size
          0), the block's range +0x0C and counters. UnitIsDead, AiDistUnits, UNIT_GetSizeX, the path getters run on the image.
          Ends at its return; the block is compared.
  dhole   0x005E9DD0 stack argument unit or 0; ends at SpawnNearUnitNoBox or its return.
  umin    0x005F7F10 stack argument near-unit or 0; ends at SpawnNearUnitNoBox: class, mode, radius, flag, the unit seed.
  bmin    0x005FD0F0 ends at UnitGetRoom (0x005FD1AD): the frame's class and word tables, x, y, EDI = low & 1, the unit seed.
  drop    0x005E0070 class, the three Game flags, null unit; ends at DropItemAtUnit, the fatal line call 0x00408090 or its return.
  qdeath  0x005A3250 (g_UModEventFns mod 22, event 1) every class 0..733 in mode 0 and in another mode, and a null unit: ends at
          the arm's callee or the return.
  presets 0x005559A0 a level id and a preset list (id, next, type, flags): ends at the first PresetUnitSpawn or its return; the
          counter Game+0x1DE4 is compared. RoomGetLevelId, RoomLevelId and the list head getter run on the image.
  bact14  0x005FCB60 with k = 14 and a target: ends at MonAiUseSkill (class 709) or UnitGetRoom before SpawnPosPick (others), the
          point in the frame. UnitGetSubX/Y, UnitEdgeDistance with size 0 run on the image.
  aura    0x005A1650 (g_UModHandlers mod 30): unit with no stat list, so level 1; ends at UnitSkillAdd or its return. The claim is the
          class-704 arm; for another class only the call site is compared.
  postc   0x005B1CF0 a class and a BaseId: ends at the first ModAppendApply or QUESTS_HookMonster.

Controls (each must fail every case it separates): `cmp` strictness of the distance test, `cls` 705 and 709 swapped in the
counter map and the flag map, `lo3` the minion index from the seed's high word, `pass` level 136 taking the monster pass,
`cnt` the counter compared before its increment, `b709` class 709 taken as another class, `base` the class read where the BaseId is,
`site` each call site one byte later.

Not covered (ADR-0021): every callee at or after a boundary and every store after it. In particular `drop` ends before the `std`
copies, `postc` at the first mod, `presets` at the first spawn of a walk. Whether any of these runs in stock play is not covered:
a p-code run says nothing about reach. Stdlib only.
"""
import argparse
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52n", "emu")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")

MUL = 0x6AC690C5
GAME, UNIT, UPATH, TARGET, TPATH, MDATA, BLOCK, CTL, DTBL = (0x12000000, 0x12100000, 0x12200000, 0x12400000, 0x12B00000,
                                                             0x12500000, 0x12600000, 0x12800000, 0x12A00000)
ROOM, DROOM, LEVEL, PRE, MSBASE = 0x12300000, 0x12310000, 0x12320000, 0x12330000, 0x13000000
G_DATATABLES = 0x00744304
STK_LO, STK_LEN, EBP = 0x7FEFFC00, 1040, 0x7FEFFFFC
LINE, SPAWNNEAR, GETROOM, DROPITEM, PRESET, USESKILL, SKILLADD, MODAPP, QHOOK = (0x00408090, 0x005B23C0, 0x00620BB0, 0x00559A30,
                                                                                0x00555910, 0x005DEAD0, 0x0056DEB0, 0x005A4850, 0x005436B0)
ARMS = {0x005A329D: (0x005DFE00, 0x005A32A3), 0x005A32AB: (0x005DFE20, 0x005A32B1), 0x005A32B9: (0x005DFDB0, 0x005A32BF),
        0x005A32C7: (0x005E0020, 0x005A32CD), 0x005A32D5: (0x005DFD90, 0x005A32DB), 0x005A32E3: (0x005E0060, 0x005A32ED),
        0x005A32F5: (0x005E0040, 0x005A32FF), 0x005A3307: (0x005E0070, 0x005A3311)}
OBSERVE = sorted({LINE, SPAWNNEAR, DROPITEM, PRESET, USESKILL, SKILLADD, MODAPP, QHOOK} | {v[0] for v in ARMS.values()})
FNS = {"ucount": 0x005DD140, "dhole": 0x005E9DD0, "umin": 0x005F7F10, "bmin": 0x005FD0F0, "drop": 0x005E0070,
       "qdeath": 0x005A3250, "presets": 0x005559A0, "bact14": 0x005FCB60, "aura": 0x005A1650, "postc": 0x005B1CF0}
FAMILIES = tuple(FNS)
NCASES = 240
CONTROLS = {"ucount": ("cmp", "cls"), "dhole": (), "umin": ("lo3",), "bmin": ("lo3",), "drop": ("cls",), "qdeath": (),
            "presets": ("pass", "cnt"), "bact14": ("b709",), "aura": (), "postc": ("base",)}
RET = "ret"


def u32(v):
    return v & 0xFFFFFFFF


def hx32(v):
    return struct.pack("<I", u32(v)).hex()


def hx16(v):
    return struct.pack("<H", v & 0xFFFF).hex()


def mrec(c):
    return MSBASE + 0x1A8 * c


def C(a):
    return a + 5


def step(s):
    t = s[0] * MUL + s[1]
    s[0], s[1] = t & 0xFFFFFFFF, (t >> 32) & 0xFFFFFFFF


def want(fn=RET, site=0, args=(), ecx=None, edx=None, seed=None, frame=None, mem=None, regs=None):
    return dict(fn=fn, site=site, args=list(args), ecx=ecx, edx=edx, seed=seed, frame=frame or {}, mem=mem or {}, regs=regs or {})


def aidist(ax, ay, bx, by):                # size 0: (2 max + min) / 2, the sum never negative
    dx, dy = abs(ax - bx), abs(ay - by)
    return (2 * dx + dy if dx > dy else dx + 2 * dy) // 2


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


# ------------------------------------------------------------------------------------------------- models
def m_ucount(i, neg):
    b = list(i["block"])
    if i["cnull"] or i["ctype"] != 1 or i["cc6"] & 1 or i["cmode"] in (0, 12):
        return want(mem={BLOCK: b}, regs={"eax": 0})
    d = aidist(i["ux"], i["uy"], i["cx"], i["cy"])
    r = i["block"][3]
    far = d >= r if neg == "cmp" else d > r
    if not far:
        c = i["ccls"]
        if neg == "cls" and c in (705, 709):
            c = 1414 - c
        k = {704: 0, 705: 1, 709: 2, 711: 5, 712: 7, 731: 6, 732: 6, 733: 6}.get(c, 4)
        b[k] = u32(b[k] + 1)
    return want(mem={BLOCK: b}, regs={"eax": 0})


def m_dhole(i, neg):
    if not i["near"]:
        return want()
    return want(SPAWNNEAR, C(0x005E9DE5), [711, 1, 4, 0x40], ecx=GAME, edx=i["near"])


def m_umin(i, neg):
    s = list(i["seed"])
    step(s)
    k = (s[1] if neg == "lo3" else s[0]) & 7
    cls = (725, 725, 726, 726, 727, 728, 729, 730)[k]
    return want(SPAWNNEAR, C(0x005F7FE5), [cls, 8, 4, 0], ecx=GAME, edx=i["near"] or UNIT, seed=s)


def upos(i):
    if i["utype"] in (2, 4, 5):
        return i["usx"], i["usy"]
    return i["ux"], i["uy"]


def m_bmin(i, neg):
    s = list(i["seed"])
    step(s)
    x, y = upos(i)
    k = (s[1] if neg == "lo3" else s[0]) & 1
    f = {EBP - 0x20 + 4 * n: v for n, v in enumerate((732, 731, 733, 1, 7, 8))}
    f[EBP - 8], f[EBP - 4] = x, y
    return want(GETROOM, C(0x005FD1AD), [UNIT, EBP - 8, 2, 0x100, 0], seed=s, frame=f, regs={"edi": k})


def m_drop(i, neg):
    c = -1 if i["unull"] else i["cls"]
    f = list(i["flags"])                    # +0x1DE8, +0x1DEC, +0x1DF0
    if neg == "cls" and c in (705, 709):
        c = 1414 - c
    if c == 704:
        f[2] = 1
    elif c == 705:
        f[1] = 1
    elif c == 709:
        f[0] = 1
    else:
        return want(LINE, C(0x005E00A0), [0xE6], mem={GAME + 0x1DE8: list(i["flags"])})
    if f[0] and f[1] and f[2]:
        return want(DROPITEM, C(0x005E0108), [7, EBP - 4, 0, 0xFFFFFFFF, 0], ecx=GAME, edx=UNIT,
                    mem={GAME + 0x1DE8: f, UNIT + 0xB8: [0x20326D63]})
    return want(mem={GAME + 0x1DE8: f})


TABLES = {}


def load_tables(exe):
    if not TABLES:
        b = open(exe, "rb").read()
        at = lambda va, n: b[va - 0x400000:va - 0x400000 + n]        # .text raw = rva for this image
        TABLES["j1"] = struct.unpack("<4I", at(0x005A331C, 16))
        TABLES["i1"] = at(0x005A332C, 0xE7)
        TABLES["j2"] = struct.unpack("<5I", at(0x005A3414, 20))
        TABLES["i2"] = at(0x005A3428, 0x65)
    return TABLES


def arm_of(c):
    t = TABLES
    if c is None:
        return None
    if c == 0x10B:
        return 0x005A32D5
    if c < 0x10B:
        x = c - 0x9C
        return t["j2"][t["i2"][x]] if 0 <= x <= 0x64 else None
    x = c - 0x1DF
    return t["j1"][t["i1"][x]] if 0 <= x <= 0xE6 else None


def m_qdeath(i, neg):
    a = arm_of(None if i["unull"] else i["cls"])
    if a is None or a not in ARMS:
        return want()
    if not i["unull"] and i["mode"] != 0:
        return want()
    fn, site = ARMS[a]
    return want(fn, C(site), [], ecx=GAME, edx=0 if i["unull"] else UNIT)


def m_presets(i, neg):
    lv, cnt = i["level"], i["g1de4"]
    lim = i["g7c"] % 3 + 3
    for n, (pid, typ, fl) in enumerate(i["list"]):
        if typ == 1 or fl & 1:
            continue
        spawn = True
        if lv == 136:
            spawn = not (typ == 2 and pid in (0x10C, 0x1A, 0x10D))
        elif lv in (133, 135):
            spawn = not (typ == 2 and pid == 0x18D)
        elif lv == 134 and typ == 2 and pid != 0x192:
            before = cnt
            cnt = u32(cnt + 1)
            spawn = (before if neg == "cnt" else cnt) != lim
        elif lv == 134 and typ == 2:
            spawn = False
        if spawn:
            site = 0x00555A1E if lv == 136 else 0x00555A8C
            return want(PRESET, C(site), [PRE + 0x20 * n], ecx=GAME, edx=ROOM, mem={GAME + 0x1DE4: [cnt]})
    if lv != 136 or neg == "pass":
        for n, (pid, typ, fl) in enumerate(i["list"]):
            if typ == 1 and not fl & 1:
                return want(PRESET, C(0x00555AC1), [PRE + 0x20 * n], ecx=GAME, edx=ROOM, mem={GAME + 0x1DE4: [cnt]})
    return want(mem={GAME + 0x1DE4: [cnt]})


def m_bact14(i, neg):
    c = i["cls"]
    ux, uy, tx, ty = i["ux"], i["uy"], i["tx"], i["ty"]
    if c == 709 and neg != "b709":
        sk = i["sk5"] - 0x10000 if i["sk5"] & 0x8000 else i["sk5"]
        return want(USESKILL, C(0x005FCE15), [i["m5"], u32(sk), 0, tx, ty], ecx=GAME, edx=UNIT)
    e = aidist(ux, uy, tx, ty) or 1
    return want(GETROOM, C(0x005FCE31), [UNIT], frame={EBP - 0x14: u32(tdiv((ux - tx) * 25, e) + ux),
                                                       EBP - 0x10: u32(tdiv((uy - ty) * 25, e) + uy)})


def m_aura(i, neg):
    if not i["flag"]:
        return want()
    if i["cls"] == 704:
        return want(SKILLADD, C(0x005A175C), [20, 1], ecx=UNIT, edx=123)
    return want("other")


POSTC = {  # (BaseId, class is the uber) -> (fn, site, args)
    (242, 704): (MODAPP, 0x005B1EA0, [22, 1]), (243, 705): (MODAPP, 0x005B1EBA, [22, 1]),
    (544, 709): (MODAPP, 0x005B2027, [22, 1]), (156, 707): (MODAPP, 0x005B1F07, [23, 1]),
    (211, 708): (MODAPP, 0x005B1D95, [6, 1]), (256, 706): (MODAPP, 0x005B1D95, [6, 1]),
    (242, None): (QHOOK, 0x005B2046, [20]), (243, None): (MODAPP, 0x005B1E2B, [22, 1]),
    (544, None): (QHOOK, 0x005B2046, [36]), (156, None): (MODAPP, 0x005B1EEF, [22, 1]),
    (211, None): (QHOOK, 0x005B1D7B, [13]), (256, None): (MODAPP, 0x005B1F51, [22, 1]),
}


def m_postc(i, neg):
    base, c = i["base"], i["cls"]
    if neg == "base":
        base = c
    k = (base, c) if (base, c) in POSTC else (base, None)
    fn, site, args = POSTC.get(k, (RET, 0, []))
    if fn == RET:
        return want()
    return want(fn, C(site), args, ecx=GAME, edx=UNIT)


MODELS = {k: globals()["m_" + k] for k in FAMILIES}


# ------------------------------------------------------------------------------------------------- cases
def common(i):
    c = i.get("cls", 0)
    L = ["w %08x %s" % (G_DATATABLES, hx32(DTBL)), "w %08x %s" % (DTBL + 0xA78, hx32(MSBASE)),
         "w %08x %s" % (DTBL + 0xA80, hx32(734))]
    return L


def rec_lines(classes):
    return ["w %08x %s" % (mrec(c) + 0x18, hx16(0xFFFF)) for c in classes]


def gen_family(fam, rnd):
    cases, meta = [], []
    n = 2 * 734 + 1 if fam == "qdeath" else NCASES
    for k in range(n):
        seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
        i = {"seed": seed}
        L = common(i)
        d = ["d %08x %d" % (STK_LO, STK_LEN), "d %08x 8" % (UNIT + 0x20)]
        f = FNS[fam]
        L += ["w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1]))]
        if fam == "ucount":
            i.update(ux=rnd.randrange(1 << 16), uy=rnd.randrange(1 << 16), cnull=int(rnd.randrange(12) == 0),
                     ctype=rnd.choice([1, 1, 1, 1, 1, 0, 2]), cc6=rnd.choice([0, 0, 0, 0, 1, 2]), cmode=rnd.choice([1, 1, 1, 2, 4, 0, 12, 17]),
                     ccls=rnd.choice([704, 705, 709, 711, 712, 731, 732, 733, 706, 710, 734 - 1, 0, rnd.randrange(734)]))
            ctype_path = i["ctype"] in (0, 1)
            near = rnd.randrange(4)
            r = rnd.randrange(1, 80)
            dx, dy = rnd.randrange(0, 60), rnd.randrange(0, 60)
            if near == 0:                   # at the range's edge
                dy = 0
                dx = r
            i["cx"], i["cy"] = i["ux"] + dx, i["uy"] + dy
            if i["cx"] > 0xFFFF or i["cy"] > 0xFFFF:
                i["cx"], i["cy"] = i["ux"] - dx, i["uy"] - dy
            i["block"] = [rnd.randrange(50) for _ in range(3)] + [r] + [rnd.randrange(50) for _ in range(4)]
            L += rec_lines([i["ccls"], 709])
            L += ["w %08x %s" % (UNIT, hx32(1) + hx32(709)), "w %08x %s" % (UNIT + 0x2C, hx32(UPATH)),
                  "w %08x %s" % (UPATH + 2, hx16(i["ux"])), "w %08x %s" % (UPATH + 6, hx16(i["uy"])),
                  "w %08x %s" % (TARGET, hx32(i["ctype"]) + hx32(i["ccls"])), "w %08x %s" % (TARGET + 0x10, hx32(i["cmode"])),
                  "w %08x %s" % (TARGET + 0xC6, "%02x" % i["cc6"]), "w %08x %s" % (TARGET + 0x2C, hx32(TPATH)),
                  "w %08x %s" % (TPATH + 2, hx16(i["cx"])), "w %08x %s" % (TPATH + 6, hx16(i["cy"])),
                  "w %08x %s" % (BLOCK, "".join(hx32(x) for x in i["block"]))]
            d.append("d %08x 32" % BLOCK)
            call = "call %08x %08x %08x %08x %08x" % (f, GAME, UNIT, 0 if i["cnull"] else TARGET, BLOCK)
        elif fam == "dhole":
            i["near"] = rnd.choice([0, UNIT, TARGET, rnd.randrange(1, 1 << 31)])
            call = "call %08x %08x %08x %08x" % (f, GAME, 0x11111111, i["near"])
        elif fam in ("umin", "bmin"):
            i.update(utype=rnd.choice([1, 1, 1, 0, 2, 3, 4, 5]), ux=rnd.randrange(1 << 16), uy=rnd.randrange(1 << 16),
                     usx=rnd.randrange(1 << 32), usy=rnd.randrange(1 << 32), near=rnd.choice([0, 0, TARGET]))
            L += ["w %08x %s" % (UNIT, hx32(i["utype"])), "w %08x %s" % (UNIT + 0x2C, hx32(UPATH)),
                  "w %08x %s" % (UPATH + 2, hx16(i["ux"])), "w %08x %s" % (UPATH + 6, hx16(i["uy"])),
                  "w %08x %s%s" % (UPATH + 0xC, hx32(i["usx"]), hx32(i["usy"]))]
            call = ("call %08x %08x %08x %08x" % (f, GAME, UNIT, i["near"])) if fam == "umin" else "call %08x %08x %08x" % (f, GAME, UNIT)
        elif fam == "drop":
            i.update(cls=rnd.choice([704, 705, 709, 704, 705, 709, 706, 707, 708, 243, rnd.randrange(734)]), unull=int(rnd.randrange(16) == 0),
                     flags=[rnd.choice([0, 1, 1, 1, 5]) for _ in range(3)])
            if i["unull"]:
                i["cls"] = -1
            L += ["w %08x %s" % (UNIT, hx32(1) + hx32(i["cls"])), "w %08x %s" % (UNIT + 0xB8, hx32(0x20647473)),
                  "w %08x %s" % (GAME + 0x1DE8, "".join(hx32(x) for x in i["flags"]))]
            d += ["d %08x 12" % (GAME + 0x1DE8), "d %08x 4" % (UNIT + 0xB8)]
            call = "call %08x %08x %08x" % (f, GAME, 0 if i["unull"] else UNIT)
        elif fam == "qdeath":
            i.update(unull=int(k == 2 * 734), cls=k // 2 if k < 2 * 734 else 0, mode=0 if k % 2 == 0 else rnd.choice([1, 2, 4, 12]))
            L += ["w %08x %s" % (UNIT, hx32(1) + hx32(i["cls"])), "w %08x %s" % (UNIT + 0x10, hx32(i["mode"]))]
            call = "call %08x %08x %08x %08x %08x" % (f, GAME, 0 if i["unull"] else UNIT, 0, 0)
        elif fam == "presets":
            lv = rnd.choice([133, 134, 135, 136, 133, 134, 135, 136, 134, 136, 17, 39, 100])
            cnt = rnd.choice([0, 0, 1, 2, 3, 4, 5])
            lst = []
            for _ in range(rnd.randrange(0, 8)):
                r = rnd.randrange(8)
                if r < 3:
                    lst.append((rnd.choice({136: [0x10C, 0x1A, 0x10D], 133: [0x18D], 135: [0x18D], 134: [0x192]}.get(lv, [5])), 2, 0))
                elif r == 3:
                    lst.append((rnd.randrange(1, 500), 1, 0))
                elif r == 4:
                    lst.append((rnd.randrange(1, 500), rnd.choice([0, 2, 5]), 1))
                elif r == 5 and lv == 134:
                    lst.append((rnd.randrange(1, 400), 2, 0))
                elif r == 6:
                    lst.append((rnd.randrange(1, 500), rnd.choice([0, 2, 5]), 0))
                else:
                    lst.append((rnd.choice([0x10C, 0x1A, 0x10D, 0x18D, 0x192]), rnd.choice([2, 2, 0, 5]), 0))
            g7c = rnd.randrange(1 << 32)
            if lv == 136 and rnd.randrange(3) == 0:     # monsters and skipped objects only: the second pass decides
                lst = [(rnd.randrange(1, 500), 1, 0)] + [(rnd.choice([0x10C, 0x1A, 0x10D]), 2, 0) for _ in range(rnd.randrange(3))]
            if lv == 134 and rnd.randrange(2):          # the counter one short of its limit, then objects
                cnt = g7c % 3 + 3 - rnd.choice([1, 1, 2])
                lst = [(rnd.randrange(1, 400), 2, 0) for _ in range(rnd.randrange(1, 4))]
            i.update(level=lv, list=lst, g1de4=cnt, g7c=g7c)
            L += ["w %08x %s" % (ROOM + 0x10, hx32(DROOM)), "w %08x %s" % (DROOM + 0x58, hx32(LEVEL)),
                  "w %08x %s" % (DROOM + 0x28, hx32(0)), "w %08x %s" % (DROOM + 0x5C, hx32(PRE if lst else 0)),
                  "w %08x %s" % (LEVEL + 0x1D0, hx32(lv)), "w %08x %s" % (GAME + 0x7C, hx32(i["g7c"])),
                  "w %08x %s" % (GAME + 0x1DE4, hx32(cnt))]
            for n2, (pid, typ, fl) in enumerate(lst):
                a = PRE + 0x20 * n2
                nx = a + 0x20 if n2 + 1 < len(lst) else 0
                L += ["w %08x %s" % (a + 4, hx32(pid)), "w %08x %s" % (a + 0xC, hx32(nx)), "w %08x %s" % (a + 0x14, hx32(typ)),
                      "w %08x %s" % (a + 0x1C, hx32(fl))]
            d.append("d %08x 4" % (GAME + 0x1DE4))
            call = "call %08x %08x %08x" % (f, GAME, ROOM)
        elif fam == "bact14":
            cl = rnd.choice([709, 709, 709, 544, 570, 559, 243, rnd.randrange(734)])
            i.update(cls=cl, ux=rnd.randrange(1 << 16), uy=rnd.randrange(1 << 16), sk5=rnd.choice([0xFFFF, 0x8000, 0, 1, 277, rnd.randrange(1 << 16)]),
                     m5=rnd.randrange(16))
            dx, dy = rnd.choice([(0, 0), (1, 0), (rnd.randrange(80), rnd.randrange(80))])
            i["tx"], i["ty"] = (i["ux"] + dx) & 0xFFFF, (i["uy"] + rnd.choice([dy, -dy])) & 0xFFFF
            if abs(i["ux"] - i["tx"]) > 200:
                i["tx"] = i["ux"]
            if abs(i["uy"] - i["ty"]) > 200:
                i["ty"] = i["uy"]
            L += rec_lines([cl, 243])
            L += ["w %08x %s" % (UNIT, hx32(1) + hx32(cl)), "w %08x %s" % (UNIT + 0x2C, hx32(UPATH)),
                  "w %08x %s" % (UPATH + 2, hx16(i["ux"])), "w %08x %s" % (UPATH + 6, hx16(i["uy"])),
                  "w %08x %s" % (TARGET, hx32(1) + hx32(243)), "w %08x %s" % (TARGET + 0x2C, hx32(TPATH)),
                  "w %08x %s" % (TPATH + 2, hx16(i["tx"])), "w %08x %s" % (TPATH + 6, hx16(i["ty"])),
                  "w %08x %s" % (mrec(cl) + 0x178, hx16(i["sk5"])), "w %08x %s" % (mrec(cl) + 0x184, "%02x" % i["m5"])]
            call = "call %08x %08x %08x %08x %08x %08x %08x" % (f, GAME, UNIT, CTL, TARGET, 14, 0)
        elif fam == "aura":
            i.update(cls=rnd.choice([704, 704, 704, 705, 709, 242, rnd.randrange(734)]), flag=rnd.choice([1, 1, 1, 0, 7]))
            L += ["w %08x %s" % (UNIT, hx32(1) + hx32(i["cls"])), "w %08x %s" % (UNIT + 0x14, hx32(MDATA)), "w %08x %s" % (UNIT + 0x5C, hx32(0)),
                  "w %08x %s" % (MDATA + 0x14, hx16(rnd.randrange(1 << 16))), "w %08x %s" % (MDATA + 0x26, hx16(rnd.choice([0, 0x25, 5])))]
            call = "call %08x %08x %08x %08x" % (f, UNIT, 0, i["flag"])
        elif fam == "postc":
            base, cl = rnd.choice([(242, 704), (243, 705), (544, 709), (156, 707), (211, 708), (256, 706), (242, 242), (243, 243), (243, 333),
                                   (544, 544), (544, 570), (156, 156), (211, 211), (256, 256)])
            i.update(cls=cl, base=base)
            L += ["w %08x %s" % (mrec(cl) + 2, hx16(base)), "w %08x %s" % (BLOCK, hx32(GAME) + hx32(rnd.randrange(1 << 16)) + hx32(0) + hx32(cl))]
            L.append("r eax %08x" % BLOCK)
            call = "call %08x %08x %08x" % (f, UNIT, 0x11111111)
        lines = L + d + [call]
        cases.append(lines)
        meta.append(i)
    mem = ["observe %08x" % a for a in OBSERVE if a != FNS[fam]] + ["guard %08x" % a for a in (0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480)]
    if fam in ("bmin", "bact14"):
        mem.append("observe %08x" % GETROOM)
    return cases, meta, mem


def seedrnd(fam):
    return random.Random("r52n-" + fam)


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        cases, meta, mem = gen_family(fam, seedrnd(fam))
        with open(os.path.join(d, fam + ".cases"), "w") as f:
            for c in cases:
                f.write("\n".join(c) + "\n")
        with open(os.path.join(d, fam + ".mem"), "w") as f:
            f.write("\n".join(mem) + "\n")
        print("CASES %s %d" % (fam, len(cases)))


# ------------------------------------------------------------------------------------------------- check
def read_out(path):
    calls, traced = [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "dumps": {}}
            if p[3] == "STOP":
                c["stop"] = " ".join(p[4:])
            elif p[3] == "OBS":
                c["obs"] = int(p[4], 16)
                c["regs"] = {k: int(v, 16) for k, v in (x.split("=") for x in p[5:]) if k != "steps"}
            else:
                c["obs"] = RET
                c["regs"] = {k: int(v, 16) for k, v in (x.split("=") for x in p[3:]) if k != "steps"}
            calls.append(c)
        elif p[0] == "A":
            calls[-1]["args"] = bytes.fromhex(p[1])
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            traced.append(ln.strip())
    return calls, traced


def matches(c, w, inp, fam, shift=0):
    if w["fn"] == "other":                  # aura: another class, the call site only
        if c.get("obs") == RET:
            return shift == 0
        ret = struct.unpack_from("<I", c.get("args", b"\0\0\0\0"), 0)[0]
        return c.get("obs") == SKILLADD and ret == C(0x005A17AF) + shift
    if c.get("obs") != w["fn"]:
        return False
    if w["seed"] is not None and list(struct.unpack("<II", c["dumps"][UNIT + 0x20])) != w["seed"]:
        return False
    if w["seed"] is None and list(struct.unpack("<II", c["dumps"][UNIT + 0x20])) != list(inp["seed"]):
        return False
    for addr, words in w["mem"].items():
        got = c["dumps"][addr]
        if list(struct.unpack("<%dI" % (len(got) // 4), got))[:len(words)] != [u32(x) for x in words]:
            return False
    for addr, v in w["frame"].items():
        if struct.unpack_from("<I", c["dumps"][STK_LO], addr - STK_LO)[0] != u32(v):
            return False
    for r, v in w["regs"].items():
        if c["regs"][r] != u32(v):
            return False
    if w["fn"] == RET:
        return shift == 0
    a = c.get("args", b"")
    if struct.unpack_from("<I", a, 0)[0] != w["site"] + shift:
        return False
    if [struct.unpack_from("<I", a, 4 + 4 * k)[0] for k in range(len(w["args"]))] != [u32(x) for x in w["args"]]:
        return False
    if w["ecx"] is not None and c["regs"]["ecx"] != u32(w["ecx"]):
        return False
    if w["edx"] is not None and c["regs"]["edx"] != u32(w["edx"]):
        return False
    return True


# static reads the image serves: (pc lo, pc hi, addr lo, addr hi), each named in the finding
ACCOUNT = {"qdeath": [(0x005A3250, 0x005A3320, 0x005A331C, 0x005A348D)], "bact14": [(0x005FCBC0, 0x005FCBC8, 0x005FCEF0, 0x005FCF2C), (0x00620521, 0x00620528, 0x0062057C, 0x00620594)],
           "ucount": [(0x00620521, 0x00620528, 0x0062057C, 0x00620594)],
           "aura": [(0x005A1690, 0x005A17B8, 0x0073BF68, 0x0073C008)], "postc": [(0x005B1D5F, 0x005B1D70, 0x005B2060, 0x005B21A2)]}


def account(fam, line):
    p = line.split()
    pc, addr = int(p[1], 16), int(p[2], 16)
    return any(a <= pc < b and c <= addr < d for a, b, c, d in ACCOUNT.get(fam, ()))


def cmd_check(d, exe):
    load_tables(exe)
    allok = True
    tot = [0, 0]
    for fam in FAMILIES:
        _, meta, _ = gen_family(fam, seedrnd(fam))
        calls, traced = read_out(os.path.join(d, fam + ".out"))
        bad, match, stops, spass = [], 0, 0, 0
        ctl = {n: [0, 0] for n in CONTROLS[fam]}
        sites = {}
        ndraw = 0
        if len(calls) != len(meta):
            bad.append("case count %d != %d" % (len(calls), len(meta)))
        for c, inp in zip(calls, meta):
            if "stop" in c:
                stops += 1
                bad.append("case %d STOP %s" % (c["n"], c["stop"]))
                continue
            w = MODELS[fam](inp, None)
            ok = matches(c, w, inp, fam)
            match += ok
            if not ok:
                bad.append("case %d want=%s@%x obs=%s args=%s regs=%s inp=%s" % (
                    c["n"], w["fn"] if w["fn"] in (RET, "other") else hex(w["fn"]), w["site"],
                    c.get("obs") if c.get("obs") == RET else hex(c.get("obs", 0)), c.get("args", b"")[:24].hex(),
                    {k: hex(v) for k, v in c.get("regs", {}).items() if k in ("eax", "ecx", "edx", "edi")}, str(inp)[:200]))
            key = str(w["fn"]) if w["fn"] in (RET, "other") else "%x@%x" % (w["fn"], w["site"])
            sites[key] = sites.get(key, 0) + 1
            ndraw += w["seed"] is not None
            if w["fn"] != RET:
                spass += matches(c, w, inp, fam, 1)
            for n in ctl:
                nw = MODELS[fam](inp, n)
                if nw != w:
                    ctl[n][0] += 1
                    ctl[n][1] += matches(c, nw, inp, fam)
        rest = [t for t in traced if not (t.startswith("R") and account(fam, t))]
        acc = len(traced) - len(rest)
        print("AI52N %s cases=%d match=%d bad=%d stopped=%d traced=%d accounted=%d drew=%d %s site_control_passed=%d boundaries=%d" % (
            fam, len(meta), match, len(bad), stops, len(rest), acc, ndraw,
            " ".join("%s_separating=%d %s_passed=%d" % (n, ctl[n][0], n, ctl[n][1]) for n in ctl), spass, len(sites)))
        print("  SITES " + " ".join("%s:%d" % kv for kv in sorted(sites.items())))
        if fam == "qdeath":
            arms = {}
            for c0 in range(734):
                a = arm_of(c0)
                if a in ARMS:
                    arms.setdefault(ARMS[a][0], []).append(c0)
            for fn, cs in sorted(arms.items()):
                print("  ARM %08x classes %s" % (fn, ",".join(map(str, cs))))
        for b in bad[:20]:
            print("  BAD", b)
        for t in rest[:20]:
            print("  TRACED", t)
        if bad or rest or spass or any(ctl[n][1] for n in ctl):
            allok = False
        tot[0] += len(meta)
        tot[1] += match
    print("AI52N total cases=%d match=%d" % tuple(tot))
    print("AI52N result=%s" % ("ok" if allok else "FAIL"))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["cases", "check"])
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--exe", default=EXE)
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir)
    else:
        cmd_check(a.dir, a.exe)


if __name__ == "__main__":
    main(sys.argv[1:])
