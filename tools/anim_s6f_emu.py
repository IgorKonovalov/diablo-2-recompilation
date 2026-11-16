#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S6f (`lane/n66s`): the items-and-sequences family set and the room-walk attempt, under
Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared with the models below,
plus one recount of a kept emulation (no emulator). Parts 1-3 of S6e (tools/anim_s6e_emu.py, anim_s6e2_emu.py,
anim_s6e3_emu.py) stay unchanged; this file imports helpers only.

    python3 -I tools/anim_s6f_emu.py cases [--dir D]     write D/s6f.cases, D/s6f.mem and the region images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s6f.cases D/s6f.mem > D/s6f.out
    python3 -I tools/anim_s6f_emu.py check [--dir D]     compare, account for every traced read and write, controls
    python3 -I tools/anim_s6f_emu.py knock [--dir D]     recount the kept run:2026-11-03-path-emu-3 `knock` family
    python3 -I tools/anim_s6f_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66s/s6f/run. Every draw comes from random.Random("n66s-s6f-<family>"); the declared tables
from random.Random("n66s-s6f-image").

Families (function; inventory rows):
  wc     0x0064F060 COMPOSIT_WeaponClass(unit, 0, class, mode, inv, &index), a player, every callee run whole on a
         scratch inventory (page 0 declared, so sub_0063ADD0_InvPageGet allocates nothing; the allocator is a guard),
         scratch item units and Items records, the ItemTypes equivalence bits and g_ItemWeaponClassIndex declared.
         anim-timing 18 (the dual classes).
  seq    0x00663310 UnitSeqRecord (ESI unit), callees whole: UNIT_GetUsedSkill, SkillSeqIndex (a player's Skills byte
         +0x13; a monster's MonStats Skill<k> +0x170 / ordinal +0x188), g_PlrSeqTables (+ 12 x the column of
         PlrSeqColumn, which runs COMPOSIT_WeaponClass on the wc image), MonSeqRecord. anim-timing 45.
  sinit  0x00621260 UNIT_SeqInit(unit), callees whole (UnitSeqRecord three times, UNIT_SeqReadFrame, SEQ_ReadFrame).
         anim-timing 46's remainder (+0x3C, +0xC4).
  sadv   0x00623E00 UNIT_AnimAdvance(unit) with +0x30 set; +0x50 points at undeclared memory, so a read of the
         animdata record would be a traced access. anim-timing 49 (the advance half).
  pme    0x00581020 PlayerModeEnd (ECX game, EDX unit) to its first callee: observed boundaries (ADR-0021) at
         HandsRefresh 0x00580310, PlayerDeathModeEnd 0x0057FCA0, PlrModeStartNeutral 0x0057F020 and
         PlayerModeAllowed 0x0057EEC0; UNIT_GetUsedSkill and INV_GetCursorItem 0x0063C1E0 run whole. anim-timing 61.
  coll   0x00650150 PathStepCollide(dx, dy, &out, &n) (EAX path) over one declared room (path_emu2's DungeonRoom
         layout, its map written per case since the moves re-mark it); 0x0064FF90 and the COLL_* moves run whole.
         Two `trace` lines give each test's subtiles (0x0064FF90's entry) and result (0x00650215); the model takes the
         results as given and predicts every test's subtiles, the count +0x1D4, the list +0x1D8, flag 0x8, the out
         point, the count out and the return. anim-movement 22, 43.
  stop   0x006507B0 PathStop (ESI path), flag 0x40000 and the unit at +0x30 clear. anim-movement 23 (PathStop).
Check without an emulator:
  knock  the kept run:2026-11-03-path-emu-3 `knock` outputs (workspace/logs/r54c/emu, path_emu3's model and compare):
         how many matched cases the line test shortened, the +0x90 values met, and a `noline` control.
         anim-movement 2 and 31's remainders.

Controls as S6e: every named test reversed alone, every ordered compare's strictness switched alone; `sep` counts the
cases a control changes, `passed` those the emulator still matches (must be 0). Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from anim_s6e_emu import E, Fatal, s16, s32, u32, le32  # noqa: E402
import path_scan  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66s", "s6f", "run")
R54C = os.path.join(ROOT, "workspace", "logs", "r54c", "emu")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
PINNED = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"
G_DT = 0x00744304
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)
MAGIC = 0x01020304

U, INV, PAGES, LOCS = 0x20000000, 0x20001000, 0x20001100, 0x20001200
IT, IDATA, SL, SKO = 0x20002000, 0x20003000, 0x20004000, 0x20004100
PATH, OUTP, WOUT = 0x20008000, 0x20009000, 0x20009100
POISON = 0x2F000000
DT, DT_LEN = 0x21000000, 0x1000
MS, MS_N, MS_SZ = 0x21100000, 16, 0x1A8
SK, SK_N, SK_SZ = 0x21200000, 64, 0x23C
CS, CS_N, CS_SZ = 0x21300000, 7, 0xC4
TYB, TY_N, TY_W = 0x21400000, 64, 4
IREC, IREC_N, IREC_SZ = 0x21500000, 32, 0x1A8
MSQ, MSQ_N = 0x21600000, 20
SQR, FR = 0x21700000, 0x21800000
PST, PST_LEN, PCOL = 0x007483B8, 0x100, 0x00748418
IWC, IWC_N = 0x007446A0, 0x007446E0
DESC = 0x0074479C
MSQP, ITP = 0x0096C7B4, 0x0096CA58
WTOK, BM = 0x006EB748, 0x006CE268
CONST_READS = ((WTOK, 13 * 8, "g_WeaponClassTokens", ".rdata"), (BM, 32 * 4, "g_BitMask32", ".rdata"),
               (0x006EB7D4, 8, "PathStop's zero step pair", ".rdata"),
               (0x0064D8F0, 4, "COLL_PatternTest's jump table, pattern 0", ".text"),
               (0x0064EB88, 4, "COLL_PatternMark's jump table, pattern 0", ".text"),
               (0x0064ED00, 4, "COLL_PatternUnmark's jump table, pattern 0", ".text"))
STOPSTEP = 0x006EB7D4
OBS_REFRESH, OBS_DEATH, OBS_NEUTRAL, OBS_ALLOWED = 0x00580310, 0x0057FCA0, 0x0057F020, 0x0057EEC0
TR_TEST, TR_RES = 0x0064FF90, 0x00650215
FNS = {"wc": 0x0064F060, "seq": 0x00663310, "sinit": 0x00621260, "sadv": 0x00623E00, "pme": 0x00581020,
       "coll": 0x00650150, "stop": 0x006507B0}
FAMILIES = ("wc", "seq", "sinit", "sadv", "pme", "coll", "stop")
STOCK_IWC = ((b"bow ", 1), (b"1hs ", 2), (b"1ht ", 3), (b"stf ", 4), (b"2hs ", 5), (b"2ht ", 6), (b"xbw ", 7),
             (b"ht1 ", 12))
CODES = [struct.unpack("<I", c)[0] for c, _ in STOCK_IWC] + [struct.unpack("<I", b"hth ")[0],
                                                              struct.unpack("<I", b"zzz ")[0]]


def tok(s):
    return struct.unpack("<I", s)[0]


class Image:
    """The declared tables (seeded) and the two .rdata constants the code reads."""

    def __init__(self):
        data = open(EXE, "rb").read()
        if hashlib.sha256(data).hexdigest() != PINNED:
            raise SystemExit("anim_s6f_emu: not the pinned Game.exe")
        raw = path_scan.va_bytes(data, WTOK, 13 * 8)
        self.wtok = [struct.unpack_from("<II", raw, 8 * i) for i in range(13)]
        self.bm = struct.unpack("<32I", path_scan.va_bytes(data, BM, 128))
        self.sect = {n: (va, vs) for n, va, vs, _, _ in path_scan.sections(data)}
        self.stopstep = struct.unpack("<II", path_scan.va_bytes(data, STOPSTEP, 8))
        r = random.Random("n66s-s6f-image")
        self.irec = []
        for i in range(IREC_N):
            self.irec.append(dict(comp=r.choice([5, 6, 5, 6, 1, 2, 0]), twoh=r.choice([0, 0, 1]),
                                  ty=r.randrange(TY_N), ty2=r.choice([0, 0, -1, r.randrange(TY_N), 70]),
                                  b13d=r.choice([0, 0, 1]), c0=r.choice(CODES), c4=r.choice(CODES)))
        self.tyb = []
        for t in range(TY_N):
            w = [r.getrandbits(32) for _ in range(TY_W)]
            if r.random() < 0.5:
                w[1] |= 1 << 13                                     # type 45 (0x2D): word 1, bit 13
            else:
                w[1] &= ~(1 << 13)
            self.tyb.append(w)
        self.iwc = [(tok(c), i) for c, i in STOCK_IWC]
        self.cs = [r.choice(CODES) for _ in range(CS_N)]
        self.sk = []
        for i in range(SK_N):
            self.sk.append(dict(id=r.choice([r.randrange(SK_N), r.randrange(SK_N), 70, -3, 0, SK_N, SK_N - 1, -1, 199]),
                                b6=r.getrandbits(8),
                                seq=r.choice([0, 0, r.randrange(1, 24), r.randrange(1, 24), r.randrange(24, 40)])))
        self.ms = []
        for i in range(MS_N):
            sk = [r.choice([r.choice(self.sk)["id"], r.choice(self.sk)["id"], r.choice(self.sk)["id"], r.randrange(80),
                            199, -1]) for _ in range(8)]
            od = [r.choice([0, -1, 1, r.randrange(1, MSQ_N), r.randrange(1, MSQ_N), MSQ_N - 1, MSQ_N, MSQ_N + 3])
                  for _ in range(8)]
            self.ms.append(dict(sk=sk, od=od))
        self.pst = bytearray(PST_LEN)
        for i in range(24):
            struct.pack_into("<I", self.pst, 4 * i, SQR + 0x100 * i)
        keys = list(range(14))
        r.shuffle(keys)
        self.cols = [(r.randrange(14), k) for k in keys]           # (column, weapon-class token index)
        for i, (c, k) in enumerate(self.cols):
            struct.pack_into("<II", self.pst, PCOL - PST + 8 * i, c, k)
        for o in range(PCOL - PST + 0x70, PST_LEN, 4):
            struct.pack_into("<I", self.pst, o, r.getrandbits(32))
        self.seqrec = {}                                           # address -> (frames, length, count)
        self.frames = bytearray(0x10000)
        fo = 0
        for i in range(24):
            for c in range(14):
                n = r.randrange(1, 24)
                rows = bytearray()
                for j in range(n):
                    rows += struct.pack("<HBBBB", r.getrandbits(16), r.randrange(21), r.randrange(40), r.randrange(32),
                                        r.choice([0, 0, 0, 1, 2, 3, 4, 7]))
                self.frames[fo:fo + len(rows)] = rows
                self.seqrec[SQR + 0x100 * i + 12 * c] = (FR + fo, n, r.choice([n, n, r.randrange(1, 40)]))
                fo += len(rows)
        self.msq = []
        for i in range(MSQ_N):
            n = r.randrange(1, 24)
            rows = bytearray()
            for j in range(n):
                rows += struct.pack("<HBBBB", 0, r.randrange(21), r.randrange(40), r.randrange(32),
                                    r.choice([0, 0, 1, 2, 3, 4]))
            self.frames[fo:fo + len(rows)] = rows
            self.msq.append((FR + fo, n, r.choice([n, r.randrange(1, 40)])))
            fo += len(rows)

    def tokidx(self, code):
        for k, v in self.wtok:
            if k == code:
                return v
        return 0

    def frame_row(self, frames, i):
        o = frames - FR + 6 * i
        return self.frames[o:o + 6]


IMG = None


def img():
    global IMG
    if IMG is None:
        IMG = Image()
    return IMG


# ------------------------------------------------------------------------------------------------ the item model
class Inv:
    """A case's inventory and hands: magic, page count, page sizes, primary id, cursor, loc 4 and 5 items."""

    def __init__(self, a):
        self.a = a

    def page_ok(self, e):
        a = self.a
        if not e.t("magic", a["magic"] == MAGIC):
            return False
        return e.t("pagesz", a["pagesz"] == (0x0D, 0x01))


def rec(cid):
    return img().irec[cid] if u32(cid) < IREC_N else None


def need_rec(cid):
    r = rec(cid)
    if r is None:
        raise Fatal()
    return r


def is_type(e, it, t):
    if it is None:
        return 0
    I = img()
    r = need_rec(it["cls"])                                     # ITEMS_GetType: fatal without a record
    if I.tyb[r["ty"]][t >> 5] & I.bm[t & 31]:
        return 1
    if 0 < r["ty2"] < TY_N:
        return 1 if I.tyb[r["ty2"]][t >> 5] & I.bm[t & 31] else 0
    return 0


def notdis(e, it):
    if it is None:
        return False
    if it["type"] != 4:
        return True
    d = it["d"]
    return e.t("d100", d is None or not d["f"] & 0x100) and e.t("d4000", d is None or not d["f"] & 0x4000)


def comp(it):
    if it["type"] != 4:
        raise Fatal()
    return need_rec(it["cls"])["comp"]


def loc(e, inv, k):
    if inv is None or not inv.page_ok(e):
        return None
    return inv.a["hands"][k - 4]


def primary(e, inv):
    a = inv.a
    if a["magic"] != MAGIC or a["prim"] == 0xFFFFFFFF:
        return None
    for k in (5, 4):
        it = loc(e, inv, k)
        if it is not None and is_type(e, it, 45) and e.t("primid", it["id"] == a["prim"]):
            return it
    return None


def set_primary(e, inv, it):
    """0x0063D1D0, on the path where no primary is found and `it` is enabled."""
    if it is None or it["type"] != 4 or not is_type(e, it, 45):
        return
    lb = it["d"]["loc"] if it["d"] is not None else 0
    if e.t("lb45", lb in (4, 5)):
        if primary(e, inv) is None:
            inv.a["prim"] = it["id"]


def wci(e, it):
    """0x00629FE0 ItemWeaponClassIndex: the low half of g_ItemWeaponClassIndex's entry for Items +0xC0, else 0."""
    r = need_rec(it["cls"] if it is not None else -1)
    for k, v in img().iwc:
        if r["c0"] == k:
            return v
    return 0


def f62a1e0(e, unit, it):
    if unit["type"] == 0 and unit["ucls"] == 4:
        return need_rec(it["cls"])["b13d"] != 0
    return False


def twoh(it):
    if it is None or it["type"] != 4:
        return 0
    return need_rec(it["cls"])["twoh"]


def f63d340(e, unit, inv):
    a = inv.a if inv is not None else None
    if a is None:
        return -1
    ok = a["magic"] == MAGIC and a["pagesz"] == (0x0D, 0x01)
    r5 = a["hands"][1] if ok else None
    r4 = a["hands"][0] if ok else None
    if r5 is None:
        if r4 is None:
            return -1
        i1, itm = twoh(r4), r4
    elif r4 is not None:
        if e.t("f62", f62a1e0(e, unit, r5) or f62a1e0(e, unit, r4)):
            return 1
        if twoh(r5) or twoh(r4):
            return 2
        return -1
    else:
        i1, itm = twoh(r5), r5
    if e.t("twoh", i1 != 0):
        return 2
    if f62a1e0(e, unit, itm):
        return 2
    return -1


def m_wc(e, unit, cls, mode, inv):
    """-> (eax, index written or None); inv.a['prim'] may change."""
    R, cmpv = None, 0
    if inv is not None:
        it4 = loc(e, inv, 4)
        got = False
        if it4 is not None and notdis(e, it4):
            if e.t("t4", it4["type"] != 4):
                return 0, None
            cmpv = comp(it4)
            if e.t("c56a", cmpv in (5, 6)):
                R, got = it4, True
        if not got:
            it5 = loc(e, inv, 5)
            R = None
            if it5 is not None:
                if notdis(e, it5):
                    R = it5
                    cmpv = comp(it5)
    if e.t("dual", mode not in (0, 17) and R is not None and cmpv in (5, 6)):
        a = loc(e, inv, 4)
        a = a if notdis(e, a) else None
        b = loc(e, inv, 5)
        b = b if notdis(e, b) else None
        if e.t("cls4", cls == 4):
            if is_type(e, a, 45) and is_type(e, b, 45):
                p = primary(e, inv)
                if p is None:
                    set_primary(e, inv, a)
                    p = a
                s1 = wci(e, p)
                o = b if e.t("swap", a is p) else a
                s2 = wci(e, o)
                if e.t("s1is2", s1 == 2):
                    code = tok(b"1js ") if s2 != 2 and e.t("s2is3", s2 == 3) else tok(b"1ss ")
                elif e.t("s1is3", s1 == 3):
                    if e.t("s2is3b", s2 == 3):
                        code = tok(b"1jt ")
                    elif e.t("s2is2", s2 == 2):
                        code = tok(b"1st ")
                    else:
                        code = tok(b"1ss ")
                else:
                    code = tok(b"1ss ")
                return code, img().tokidx(code)
        elif e.t("cls6", cls == 6) and is_type(e, a, 45) and is_type(e, b, 45):
            code = tok(b"ht2 ")
            return code, img().tokidx(code)
        r = f63d340(e, unit, inv)
        if e.t("r2", r == 2):
            if R is None or R["type"] != 4:
                raise Fatal()
            code = need_rec(R["cls"])["c4"]
        else:
            code = need_rec(R["cls"])["c0"] if R is not None and R["type"] == 4 else 0
        return code, img().tokidx(code)
    code = img().cs[cls]
    return code, img().tokidx(code)


def gen_item(r):
    d = None
    if r.random() < 0.9:
        d = dict(f=r.choice([0, 0, 0, 0, 0x100, 0x4000, 0x10]), loc=r.choice([4, 5, 4, 5, 0, 1]))
    return dict(type=r.choice([4] * 15 + [2]), cls=r.choice([r.randrange(IREC_N)] * 12 + [40]),
                id=r.getrandbits(16), d=d)


def gen_inv(r):
    hands = [gen_item(r) if r.random() < 0.85 else None, gen_item(r) if r.random() < 0.85 else None]
    a = dict(magic=MAGIC if r.random() < 0.95 else 0x11111111,
             pagesz=(0x0D, 0x01) if r.random() < 0.95 else (0x0A, 0x04), hands=hands, cursor=0)
    ids = [h["id"] for h in hands if h is not None]
    a["prim"] = r.choice([0xFFFFFFFF, r.getrandbits(16)] + ids * 2)
    return a


def wc_lines(a, inv_at=INV):
    """Lines writing a case's unit-independent inventory and items."""
    ln = []
    if a is None:
        return ln
    ln.append("w %08x %s" % (inv_at, le32(a["magic"]).hex()))
    ln.append("w %08x %s" % (inv_at + 0x14, (le32(PAGES) + le32(1)).hex()))
    ln.append("w %08x %s" % (inv_at + 0x1C, (le32(a["prim"]) + le32(a["cursor"])).hex()))
    ln.append("w %08x %s" % (PAGES + 8, (bytes(a["pagesz"]) + b"\0\0" + le32(LOCS)).hex()))
    for k, h in enumerate(a["hands"]):
        if h is None:
            continue
        iu, idd = IT + 0x40 * k, IDATA + 0x80 * k
        ln.append("w %08x %s" % (LOCS + 4 * (4 + k), le32(iu).hex()))
        ln.append("w %08x %s" % (iu, (le32(h["type"]) + le32(h["cls"]) + le32(0) + le32(h["id"]) + le32(0) +
                                      le32(idd if h["d"] is not None else 0)).hex()))
        if h["d"] is not None:
            ln.append("w %08x %s" % (idd + 0x18, le32(h["d"]["f"]).hex()))
            ln.append("w %08x %02x" % (idd + 0x44, h["d"]["loc"]))
    return ln


def gen_wc(rnd):
    out = []
    for k in range(4000):
        cls = rnd.choice([4, 4, 4, 6, 6, rnd.randrange(CS_N)])
        mode = rnd.choice([rnd.randrange(21), 7, 8, 1, 0, 17])
        a = gen_inv(rnd) if rnd.random() < 0.95 else None
        if a is not None and k % 2 == 0 and cls == 4:              # bias: two enabled weapons, component 5/6
            for h in a["hands"]:
                if h is not None:
                    h["type"], h["cls"] = 4, rnd.randrange(IREC_N)
                    if h["d"] is not None:
                        h["d"]["f"] = 0
        out.append(dict(cls=cls, mode=mode, ucls=rnd.choice([cls, cls, 4, 1]), inv=a))
    I = img()
    elig = [i for i, r in enumerate(I.irec) if r["comp"] in (5, 6) and (I.tyb[r["ty"]][1] & (1 << 13) or (
        0 < r["ty2"] < TY_N and I.tyb[r["ty2"]][1] & (1 << 13)))]
    by = {}
    for i in elig:
        by.setdefault(dict(I.iwc).get(I.irec[i]["c0"], 0), []).append(i)
    for k in range(2400):                                          # two enabled weapons, classes 4 and 6
        cls = rnd.choice([4, 4, 4, 6])
        a = gen_inv(rnd)
        a["magic"], a["pagesz"] = MAGIC, (0x0D, 0x01)
        for j in range(2):
            h = gen_item(rnd)
            h["type"] = 4
            ix = rnd.choice([2, 3, 2, 3, rnd.choice(sorted(by))])
            h["cls"] = rnd.choice(by.get(ix, elig))
            if h["d"] is None or rnd.random() < 0.8:
                h["d"] = dict(f=0, loc=rnd.choice([4, 5, 4, 5, 1]))
            a["hands"][j] = h
        ids = [h["id"] for h in a["hands"]]
        a["prim"] = rnd.choice([0xFFFFFFFF, rnd.getrandbits(16)] + ids * 2)
        out.append(dict(cls=cls, mode=rnd.choice([1, 2, 7, 8, 11, 0, 17, rnd.randrange(21)]), ucls=cls, inv=a))
    return out


def unit_of(a):
    return dict(type=0, ucls=a["ucls"])


def p_wc(e, a):
    inv = Inv(dict(a["inv"], hands=list(a["inv"]["hands"]))) if a["inv"] is not None else None
    code, idx = m_wc(e, unit_of(a), a["cls"], a["mode"], inv)
    return ("ret", u32(code), idx, inv.a["prim"] if inv is not None else None)


def case_wc(a):
    ln = ["w %08x %s" % (U, (le32(0) + le32(a["ucls"])).hex()), "w %08x eeeeeeee" % WOUT]
    ln += wc_lines(a["inv"])
    ln += ["d %08x 4" % WOUT, "d %08x 4" % (INV + 0x1C),
           "call %08x 00000000 00000000 %08x 00000000 %08x %08x %08x %08x" % (
               FNS["wc"], U, a["cls"], a["mode"], INV if a["inv"] is not None else 0, WOUT)]
    return ln


def obs_wc(c, a):
    w = struct.unpack("<I", c["dumps"][WOUT])[0]
    p = struct.unpack("<I", c["dumps"][INV + 0x1C])[0] if a["inv"] is not None else None
    return ("ret", c["eax"], None if w == 0xEEEEEEEE else w, p)


# ------------------------------------------------------------------------------------------------ sequences
def used_skill(a):
    return a["sk"]                                                # None or a Skills row index


def m_seqrec(e, a, st):
    """UnitSeqRecord on unit state st (mode, +0x30, +0x40); -> address or 0."""
    I = img()
    if used_skill(a) is None:
        return 0
    row = I.sk[a["sk"]]
    if a["type"] == 0:
        idx = row["seq"]
    else:
        sid = row["id"]
        if e.t("s199", sid == 199):
            idx = 0
        else:
            m = I.ms[a["cls"]]
            idx = 0
            for k in range(8):
                if e.t("skmatch", m["sk"][k] == sid):
                    idx = m["od"][k]
                    break
    if e.c("idx1", idx, "<", 1):
        return 0
    if a["type"] == 0:
        base = struct.unpack_from("<I", I.pst, 4 * idx)[0]
        mode = st["m40"] if st["s30"] != 0 else st["mode"]
        inv = Inv(a["inv"]) if a["inv"] is not None else None
        _, w = m_wc(e, dict(type=0, ucls=a["cls"]), a["cls"], mode, inv)
        for c, k in I.cols:
            if k == w:
                return u32(base + 12 * c)
        raise Fatal()
    if a["type"] == 1:
        if e.c("msq", idx, "<", MSQ_N):
            return MSQ + 12 * idx
        return 0
    return 0


def gen_seq(rnd, sinit=False):
    out = []
    n = 900 if sinit else 2500
    for k in range(n):
        typ = rnd.choice([0, 0, 1, 1]) if not sinit else rnd.choice([0, 1])
        sk = rnd.randrange(SK_N) if rnd.random() < 0.93 else None
        if sinit and sk is not None and img().sk[sk]["seq"] >= 24:
            sk = None if rnd.random() < 0.3 else rnd.choice([i for i in range(SK_N) if img().sk[i]["seq"] < 24])
        a = dict(type=typ, cls=rnd.randrange(MS_N) if typ == 1 else rnd.randrange(CS_N), sk=sk,
                 mode=rnd.choice([rnd.randrange(21), 0, 17, 7]), m40=rnd.choice([0, 17, 3, rnd.randrange(21)]),
                 s30=rnd.choice([0, 0, rnd.getrandbits(32) | 1]), c4=rnd.getrandbits(32))
        a["inv"] = gen_inv(rnd) if typ == 0 and rnd.random() < 0.8 else None
        if a["inv"] is not None:                                   # body locations hold items: a non-item in the
            a["inv"]["magic"] = MAGIC                              # right hand leaves COMPOSIT's index unwritten and
            for h in a["inv"]["hands"]:                            # PlrSeqColumn reads its own uninitialised local
                if h is not None:                                  # (development run, `seq` case 4015)
                    h["type"] = 4
        if typ == 0 and sk is not None and img().sk[sk]["seq"] >= 24 and not sinit:
            pass                                                   # idx past the 24 tables: no bound test
        out.append(a)
    return out


def seq_unit_lines(a):
    ln = ["w %08x %s" % (U, (le32(a["type"]) + le32(a["cls"])).hex()),
          "w %08x %s" % (U + 0x10, le32(a["mode"]).hex()),
          "w %08x %s" % (U + 0x30, le32(a["s30"]).hex()),
          "w %08x %s" % (U + 0x40, le32(a["m40"]).hex()),
          "w %08x %s" % (U + 0x60, le32(INV if a["inv"] is not None else 0).hex()),
          "w %08x %s" % (U + 0xA8, le32(SL).hex()),
          "w %08x %s" % (U + 0xC4, le32(a["c4"]).hex())]
    if a["sk"] is not None:
        ln += ["w %08x %s" % (SL + 0x10, le32(SKO).hex()), "w %08x %s" % (SKO, le32(SK + SK_SZ * a["sk"]).hex())]
    return ln + wc_lines(a["inv"])


def p_seq(e, a):
    st = dict(mode=a["mode"], m40=a["m40"], s30=a["s30"])
    return ("ret", m_seqrec(e, dict(a, inv=dict(a["inv"]) if a["inv"] is not None else None), st))


def case_seq(a):
    return seq_unit_lines(a) + ["r esi %08x" % U, "call %08x 00000000 00000000" % FNS["seq"]]


def obs_seq(c, a):
    return ("ret", c["eax"])


def rd_seqrec(addr):
    I = img()
    if addr == 0:
        return None
    if addr in I.seqrec:
        return I.seqrec[addr]
    if MSQ <= addr < MSQ + 12 * MSQ_N:
        return I.msq[(addr - MSQ) // 12]
    raise Fatal()                                                  # not met: generators keep idx < 24 here


def seq_read(frames, pos, prev):
    """SEQ_ReadFrame: (mode, frame, event)."""
    I = img()
    i = s32(pos) >> 8
    row = I.frame_row(frames, i)
    mode, frame = row[2], row[3]
    if pos == prev:
        return mode, frame, row[5]
    ev = 0
    for j in range((s32(prev) >> 8) + 1, i + 1):
        x = I.frame_row(frames, j)[5]
        if x:
            ev = x
    return mode, frame, ev


def p_sinit(e, a):
    st = dict(mode=a["mode"], m40=a["m40"], s30=a["s30"])
    inv0 = dict(a["inv"]) if a["inv"] is not None else None
    a2 = dict(a, inv=inv0)
    ad1 = m_seqrec(e, a2, st)
    r1 = rd_seqrec(ad1)
    out = dict(s30=u32(r1[0]) if r1 else 0)
    st["s30"] = out["s30"]
    if out["s30"] == 0:
        return ("sinit", out["s30"], None, None, None, None, None, None, a["c4"], inv0 and inv0["prim"])
    ad2 = m_seqrec(e, a2, st)
    r2 = rd_seqrec(ad2)
    length = u32(r2[1] << 8) if r2 else 0
    ad3 = m_seqrec(e, a2, st)
    r3 = rd_seqrec(ad3)
    if e.flip is None:
        a["_later_record_differs"] = ad2 != ad1 or ad3 != ad1
    cnt = u32(r3[2] << 8) if r3 else 0
    mode, frame, ev = seq_read(out["s30"], 0, 0)
    c4 = a["c4"] | 0x4000 if e.t("c4bit", True) else a["c4"]
    m3c = 0x100 if e.t("r100", True) else 0
    return ("sinit", out["s30"], length, 0, m3c, cnt, frame << 8, (mode, ev), c4, inv0 and inv0["prim"])


def case_sinit(a):
    return seq_unit_lines(a) + ["w %08x %s" % (U + 0x34, (le32(0xAAAAAAAA) * 3).hex()),
                                "w %08x %s" % (U + 0x44, le32(0xBBBBBBBB).hex()),
                                "w %08x %s" % (U + 0x48, le32(0xCCCCCCCC).hex()),
                                "d %08x 32" % (U + 0x30), "d %08x 4" % (U + 0x48), "d %08x 1" % (U + 0x4E),
                                "d %08x 4" % (U + 0xC4), "d %08x 4" % (INV + 0x1C),
                                "call %08x 00000000 00000000 %08x" % (FNS["sinit"], U)]


def obs_sinit(c, a):
    d = c["dumps"][U + 0x30]
    s30, s34, s38, s3c = struct.unpack_from("<4I", d, 0)
    m40, s44 = struct.unpack_from("<II", d, 0x10)
    c4 = struct.unpack("<I", c["dumps"][U + 0xC4])[0]
    p = struct.unpack("<I", c["dumps"][INV + 0x1C])[0] if a["inv"] is not None else None
    if s30 == 0:
        return ("sinit", 0, None, None, None, None, None, None, c4, p)
    s48 = struct.unpack("<I", c["dumps"][U + 0x48])[0]
    return ("sinit", s30, s34, s38, s3c, s48, s44, (m40, c["dumps"][U + 0x4E][0]), c4, p)


def gen_sadv(rnd):
    I = img()
    out = []
    recs = list(I.seqrec.values()) + I.msq
    for k in range(1500):
        frames, n, _ = rnd.choice(recs)
        L = n << 8
        prev = rnd.randrange(0, L)
        r = rnd.choice([0, 1, 0x80, 0x100, 0x100, 0x180, 0x200, rnd.randrange(0, L + 1), L - prev, L - prev - 1])
        out.append(dict(frames=frames, L=L, prev=prev, r=r, m40=rnd.randrange(21), s48=rnd.getrandbits(16),
                        c4=rnd.getrandbits(32), e4e=rnd.getrandbits(8)))
    return out


def p_sadv(e, a):
    prev, L, r = a["prev"], a["L"], a["r"]
    pos = s32(prev + r)
    if e.c("wrap", pos, ">=", L):
        pos -= L
    mode, frame, ev = seq_read(a["frames"], pos, prev)
    c4 = a["c4"] & ~0x4000
    if e.t("chg", mode != a["m40"]):
        c4 |= 0x4000
    return ("sadv", u32(pos), u32(a["s48"] - r), u32(frame << 8), mode, ev, u32(c4))


def case_sadv(a):
    return ["w %08x %s" % (U, (le32(1) + le32(3)).hex()),
            "w %08x %s" % (U + 0x30, (le32(a["frames"]) + le32(a["L"]) + le32(a["prev"]) + le32(a["r"]) +
                                     le32(a["m40"]) + le32(0xDDDDDDDD) + le32(a["s48"])).hex()),
            "w %08x %s" % (U + 0x4C, (struct.pack("<H", 0x1234) + bytes([a["e4e"]])).hex()),
            "w %08x %s" % (U + 0x50, le32(POISON).hex()),
            "w %08x %s" % (U + 0xC4, le32(a["c4"]).hex()),
            "d %08x 32" % (U + 0x30), "d %08x 1" % (U + 0x4E), "d %08x 4" % (U + 0xC4),
            "call %08x 00000000 00000000 %08x" % (FNS["sadv"], U)]


def obs_sadv(c, a):
    d = c["dumps"][U + 0x30]
    s38 = struct.unpack_from("<I", d, 8)[0]
    m40, s44, s48 = struct.unpack_from("<III", d, 0x10)
    return ("sadv", s38, s48, s44, m40, c["dumps"][U + 0x4E][0], struct.unpack("<I", c["dumps"][U + 0xC4])[0])


# ------------------------------------------------------------------------------------------------ PlayerModeEnd
def p_pme(e, a):
    I = img()
    mode = a["mode"]
    refresh = False
    if e.t("m7811", mode in (7, 8, 11)):
        refresh = True
    elif a["sk"] is not None:
        sid = I.sk[a["sk"]]["id"]
        if e.c("sid0", sid, ">=", 0) and e.c("sidn", sid, "<", SK_N) and e.t("dur", I.sk[sid]["b6"] & 4):
            refresh = True
    if refresh:
        return ("obs", OBS_REFRESH, (), U, 0x00581091)
    if e.t("m0", mode == 0):
        return ("obs", OBS_DEATH, (0x11, 0, 0), U, 0x0058118F)
    if e.t("m19", mode != 19):
        return ("obs", OBS_NEUTRAL, (1, 0, 0), U, 0x005810B6)
    if a["game"] == 0:
        raise Fatal()
    if a["inv"] and e.t("cmagic", a["magic"] == MAGIC) and e.t("cursor", a["cursor"] != 0):
        return ("ret",)
    return ("obs", OBS_ALLOWED, (4, 1, 0), U, 0x0058114C)


def gen_pme(rnd):
    out = []
    for k in range(1600):
        out.append(dict(mode=rnd.choice([rnd.randrange(21), 19, 19, 0, 7, 8, 11]),
                        sk=rnd.randrange(SK_N) if rnd.random() < 0.9 else None,
                        game=rnd.choice([0x20007000, 0x20007000, 0x20007000, 0]),
                        inv=rnd.random() < 0.8, magic=rnd.choice([MAGIC, MAGIC, MAGIC, 0x5]),
                        cursor=rnd.choice([0, 0, 0x20007800])))
    return out


def case_pme(a):
    ln = ["w %08x %s" % (U, le32(0).hex()), "w %08x %s" % (U + 0x10, le32(a["mode"]).hex()),
          "w %08x %s" % (U + 0x60, le32(INV if a["inv"] else 0).hex()), "w %08x %s" % (U + 0xA8, le32(SL).hex())]
    if a["sk"] is not None:
        ln += ["w %08x %s" % (SL + 0x10, le32(SKO).hex()), "w %08x %s" % (SKO, le32(SK + SK_SZ * a["sk"]).hex())]
    if a["inv"]:
        ln += ["w %08x %s" % (INV, le32(a["magic"]).hex()), "w %08x %s" % (INV + 0x20, le32(a["cursor"]).hex())]
    return ln + ["call %08x %08x %08x" % (FNS["pme"], a["game"], U)]


def obs_pme(c, a):
    if "obs" not in c:
        return ("ret",)
    n = 0 if c["obs"] == OBS_REFRESH else 3
    args = tuple(c["args"][1:1 + n])
    edx = c["regs"]["edx"]
    return ("obs", c["obs"], args, edx, c["args"][0])


# ------------------------------------------------------------------------------------------------ PathStepCollide
ROOM_RECT = (1000, 1000, 100, 100)


def room_cells():
    r = random.Random("n66s-s6f-room")
    cells = []
    for i in range(ROOM_RECT[2] * ROOM_RECT[3]):
        cells.append(r.choice([0x0001, 0x0004, 0x0400, 0x0800, 0x0080]) if r.random() < 0.05 else 0)
    return cells


def room_lines():
    import path_emu2 as P2
    rm = P2.Room(0, ROOM_RECT, room_cells())
    P2.link([rm])
    return [ln.replace("const bytes", "bytes") for ln in P2.room_spec([rm])], rm.addr


def halve(dx, dy):
    """0x00678F00: arithmetic shifts of both until each is within one subtile."""
    if dx >= 0:
        while dx > 0x10000:
            dx >>= 1
            dy >>= 1
    else:
        while dx < -0x10000:
            dx >>= 1
            dy >>= 1
    if dy >= 0:
        while dy > 0x10000:
            dx >>= 1
            dy >>= 1
    else:
        while dy < -0x10000:
            dx >>= 1
            dy >>= 1
    return dx, dy


def p_coll(e, a, results):
    """-> ('coll', tests [(new, cur)], ret, out, n, flags, list). `results`: the traced test results, in order."""
    x0, y0, dx, dy = a["x"], a["y"], s32(a["dx"]), s32(a["dy"])
    if e.t("halve", True):
        hx, hy = halve(dx, dy)
    else:
        hx, hy = dx, dy
    tx, ty = u32(x0 + dx), u32(y0 + dy)
    tgt = ((tx >> 16) & 0xFFFF, (ty >> 16) & 0xFFFF)
    cur = ((x0 >> 16) & 0xFFFF, (y0 >> 16) & 0xFFFF)
    xa, ya = x0, y0
    n, tests, lst = 0, [], []
    flags = a["flags"]
    it = 0
    while not e.t("atgt", cur == tgt):
        it += 1
        if it > 200000:
            raise Fatal()
        nx, ny = u32(xa + hx), u32(ya + hy)
        new = ((nx >> 16) & 0xFFFF, (ny >> 16) & 0xFFFF)
        if e.t("chg", new != cur):
            tests.append((new[0] | new[1] << 16, cur[0] | cur[1] << 16))
            r = results[len(tests) - 1] if len(tests) <= len(results) else 1
            if e.t("blk", r == 0):
                out = (u32((xa & 0xFFFF0000) + 0x8000), u32((ya & 0xFFFF0000) + 0x8000))
                return ("coll", tuple(tests), 1, out, n, flags, tuple(lst))
            if e.t("lst", flags & 0x20000):
                lst.append(new[0] | new[1] << 16)
            n += 1
            if e.c("ten", n, ">=", 10):
                break
        xa, ya, cur = nx, ny, new
    if e.t("f8", n != 0):
        flags |= 8
    return ("coll", tuple(tests), 0, (tx, ty), n, flags, tuple(lst))


def gen_coll(rnd):
    out = []
    for k in range(3000):
        x = (rnd.randrange(1030, 1070) << 16) | rnd.getrandbits(16)
        y = (rnd.randrange(1030, 1070) << 16) | rnd.getrandbits(16)
        sc = rnd.choice([0x8000, 0x10000, 0x18000, 0x30000, 0x80000, 0xC0000, 0x180000])
        dx = rnd.randrange(-sc, sc + 1)
        dy = rnd.randrange(-sc, sc + 1)
        if rnd.random() < 0.05:
            dx = rnd.choice([0, dx])
            dy = 0 if dx else dy
        flags = rnd.choice([0, 0x20000, 0x20000, 0x10, 0x20]) | rnd.choice([0, 0x1000])
        out.append(dict(x=x, y=y, dx=u32(dx), dy=u32(dy), flags=flags, mask=rnd.choice([0x1C09, 0x3401, 0x0C01, 0xFFFF]),
                        mark=rnd.choice([0, 0, 0, 0x80]), s54=0))
    return out


def case_coll(a, room):
    return ["w %08x %s" % (PATH, (le32(a["x"]) + le32(a["y"])).hex()),
            "w %08x %s" % (PATH + 0x1C, le32(room).hex()),
            "w %08x %s" % (PATH + 0x30, (le32(0) + le32(a["flags"])).hex()),
            "w %08x %s" % (PATH + 0x48, (le32(0) + le32(a["mark"]) + le32(a["mask"]) + le32(0)).hex()),
            "w %08x %s" % (PATH + 0x1D4, "cc" * 44),
            "w %08x %s" % (OUTP, "dd" * 12),
            "d %08x 4" % (PATH + 0x34), "d %08x 4" % (PATH + 0x1D4), "d %08x 40" % (PATH + 0x1D8),
            "d %08x 12" % OUTP, "r eax %08x" % PATH,
            "call %08x 00000000 00000000 %08x %08x %08x %08x" % (FNS["coll"], a["dx"], a["dy"], OUTP, OUTP + 8)]


def obs_coll(c, a):
    tests = []
    res = []
    for t in c["trace"]:
        if t["pc"] == TR_TEST:
            tests.append(struct.unpack_from("<II", t["stack"], 4))
        elif t["pc"] == TR_RES:
            res.append(t["eax"])
    n = struct.unpack("<I", c["dumps"][PATH + 0x1D4])[0]
    lstb = c["dumps"][PATH + 0x1D8]
    lst = tuple(struct.unpack_from("<I", lstb, 4 * i)[0] for i in range(min(n, 10))) if a["flags"] & 0x20000 else ()
    o = c["dumps"][OUTP]
    out = struct.unpack_from("<II", o, 0)
    cnt = struct.unpack_from("<I", o, 8)[0]
    if cnt != n:
        return ("coll-bad-count", cnt, n), res
    return ("coll", tuple(tests), c["eax"], out, n, struct.unpack("<I", c["dumps"][PATH + 0x34])[0], lst), res


# ------------------------------------------------------------------------------------------------ PathStop
def p_stop(e, a):
    b = bytearray(a["path"])
    x, y = struct.unpack_from("<II", b, 0)
    struct.pack_into("<II", b, 0, u32((x & 0xFFFF0000) + 0x8000), u32((y & 0xFFFF0000) + 0x8000))
    f = struct.unpack_from("<I", b, 0x34)[0]
    struct.pack_into("<I", b, 0x34, f & ~0x20 if e.t("f20", True) else f)
    struct.pack_into("<II", b, 0x24, 0, 0)
    struct.pack_into("<II", b, 0x72, *img().stopstep)
    return ("pstop", bytes(b[0:8]), bytes(b[0x10:0x80]))


def gen_stop(rnd):
    out = []
    for k in range(200):
        b = bytearray(rnd.getrandbits(8) for _ in range(0x80))
        struct.pack_into("<I", b, 0x30, 0)
        f = rnd.getrandbits(32) & ~0x40000
        struct.pack_into("<I", b, 0x34, f | (0x20 if k % 3 else 0))
        out.append(dict(path=bytes(b)))
    return out


def case_stop(a):
    return ["w %08x %s" % (PATH, a["path"].hex()), "d %08x 128" % PATH, "r esi %08x" % PATH,
            "call %08x 00000000 00000000" % FNS["stop"]]


def obs_stop(c, a):
    d = c["dumps"][PATH]
    return ("pstop", d[0:8], d[0x10:0x80])


# ------------------------------------------------------------------------------------------------ build
GEN = {"wc": gen_wc, "seq": gen_seq, "sinit": lambda r: gen_seq(r, True), "sadv": gen_sadv, "pme": gen_pme,
       "coll": gen_coll, "stop": gen_stop}


def build():
    allc = []
    for fam in FAMILIES:
        allc += [(fam, a) for a in GEN[fam](random.Random("n66s-s6f-" + fam))]
    return allc


def predict(fam, a, flip=None, results=()):
    e = E(flip)
    try:
        if fam == "wc":
            out = p_wc(e, a)
        elif fam == "seq":
            out = p_seq(e, a)
        elif fam == "sinit":
            out = p_sinit(e, a)
        elif fam == "sadv":
            out = p_sadv(e, a)
        elif fam == "pme":
            out = p_pme(e, a)
        elif fam == "coll":
            out = p_coll(e, a, results)
        else:
            out = p_stop(e, a)
    except Fatal:
        out = ("fatal",)
    return out, e.names


def write_images(d):
    I = img()
    dt = bytearray(DT_LEN)
    for off, v in ((0xA78, MS), (0xA80, MS_N), (0xB98, SK), (0xBA0, SK_N), (0xBC4, CS), (0xBC8, CS_N),
                   (0xBFC, TY_N), (0xC00, TY_W), (0xC04, TYB)):
        struct.pack_into("<I", dt, off, v)
    ms = bytearray(MS_N * MS_SZ)
    for i, m in enumerate(I.ms):
        struct.pack_into("<8h", ms, i * MS_SZ + 0x170, *m["sk"])
        struct.pack_into("<8h", ms, i * MS_SZ + 0x188, *m["od"])
    sk = bytearray(SK_N * SK_SZ)
    for i, s in enumerate(I.sk):
        struct.pack_into("<h", sk, i * SK_SZ, s["id"])
        sk[i * SK_SZ + 6] = s["b6"]
        sk[i * SK_SZ + 0x13] = s["seq"]
    cs = bytearray(CS_N * CS_SZ)
    for i, c in enumerate(I.cs):
        struct.pack_into("<I", cs, i * CS_SZ + 0x4C, c)
    tyb = b"".join(struct.pack("<4I", *w) for w in I.tyb)
    ir = bytearray(IREC_N * IREC_SZ)
    for i, r in enumerate(I.irec):
        o = i * IREC_SZ
        struct.pack_into("<II", ir, o + 0xC0, r["c0"], r["c4"])
        ir[o + 0x115] = r["comp"]
        ir[o + 0x11C] = r["twoh"]
        struct.pack_into("<hh", ir, o + 0x11E, r["ty"], r["ty2"])
        ir[o + 0x13D] = r["b13d"]
    msq = b"".join(struct.pack("<III", *m) for m in I.msq)
    sqr = bytearray(0x100 * 24)
    for adr, v in I.seqrec.items():
        struct.pack_into("<III", sqr, adr - SQR, *v)
    iwc = bytearray(0x44)
    for i, (k, v) in enumerate(I.iwc):
        struct.pack_into("<II", iwc, 8 * i, k, v)
    struct.pack_into("<I", iwc, 0x40, len(I.iwc))
    files = {"dt": dt, "ms": ms, "sk": sk, "cs": cs, "tyb": tyb, "irec": ir, "msq": msq, "sqr": sqr, "fr": I.frames,
             "pst": I.pst, "iwc": iwc}
    for k, v in files.items():
        open(os.path.join(d, "s6f-%s.bin" % k), "wb").write(bytes(v))
    at = {"dt": DT, "ms": MS, "sk": SK, "cs": CS, "tyb": TYB, "irec": IREC, "msq": MSQ, "sqr": SQR, "fr": FR,
          "pst": PST, "iwc": IWC}
    return ["load %08x %s" % (at[k], os.path.join(d, "s6f-%s.bin" % k)) for k in files]


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    rl, room = room_lines()
    mem = ["# plan 0066 S6f declared image (tools/anim_s6f_emu.py)", "dword %08x %08x" % (G_DT, DT)]
    mem += write_images(d)
    mem += ["dword %08x %08x" % (MSQP, MSQ), "dword %08x %08x" % (MSQP + 4, MSQ_N),
            "dword %08x %08x" % (ITP, IREC_N), "dword %08x %08x" % (ITP + 4, IREC),
            "bytes %08x 0d01" % DESC,
            "bytes %08x %s" % (U, "00" * 0x100), "bytes %08x %s" % (INV, "00" * 0x40),
            "bytes %08x %s" % (PAGES, "00" * 0x10), "bytes %08x %s" % (LOCS, "00" * 0x34),
            "bytes %08x %s" % (IT, "00" * 0x80), "bytes %08x %s" % (IDATA, "00" * 0x100),
            "bytes %08x %s" % (SL, "00" * 0x20), "bytes %08x %s" % (SKO, "00" * 0x10),
            "bytes %08x %s" % (PATH, "00" * 0x200), "bytes %08x %s" % (OUTP, "00" * 0x10),
            "bytes %08x %s" % (WOUT, "00" * 4)]
    mem += rl
    mem += ["guard %08x" % x for x in FATAL + ALLOC]
    mem += ["observe %08x" % x for x in (OBS_REFRESH, OBS_DEATH, OBS_NEUTRAL, OBS_ALLOWED)]
    mem += ["trace %08x" % x for x in (TR_TEST, TR_RES)]
    open(os.path.join(d, "s6f.mem"), "w").write("\n".join(mem) + "\n")
    allc = build()
    lines = []
    for fam, a in allc:
        lines += case_coll(a, room) if fam == "coll" else CASE[fam](a)
    open(os.path.join(d, "s6f.cases"), "w").write("\n".join(lines) + "\n")
    n = {}
    for fam, _ in allc:
        n[fam] = n.get(fam, 0) + 1
    print("CASES total=%d %s" % (len(allc), " ".join("%s=%d" % kv for kv in sorted(n.items()))))


CASE = {"wc": case_wc, "seq": case_seq, "sinit": case_sinit, "sadv": case_sadv, "pme": case_pme, "stop": case_stop}
OBS = {"wc": obs_wc, "seq": obs_seq, "sinit": obs_sinit, "sadv": obs_sadv, "pme": obs_pme, "stop": obs_stop}


def read_out(path):
    calls, reads, writes, pend = [], [], [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "T":
            kv = dict(x.split("=") for x in p[3:11])
            pend.append(dict(pc=int(p[2], 16), eax=int(kv["eax"], 16), stack=bytes.fromhex(p[11])))
        elif p[0] == "C":
            c = {"n": int(p[1]), "fn": int(p[2], 16), "dumps": {}, "trace": pend}
            pend = []
            if p[3] == "STOP":
                c["stop"] = int(p[4], 16)
                c["msg"] = " ".join(p[5:])
            elif p[3] == "OBS":
                c["obs"] = int(p[4], 16)
                c["regs"] = {k: int(v, 16) for k, v in (x.split("=") for x in p[6:] if "=" in x)}
            else:
                kv = dict(x.split("=") for x in p[3:])
                c.update(eax=int(kv["eax"], 16), pop=int(kv["pop"]))
            calls.append(c)
        elif p[0] == "A":
            calls[-1]["args"] = struct.unpack("<16I", bytes.fromhex(p[1]))
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            (reads if p[0] == "R" else writes).append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
    return calls, reads, writes


def observed(fam, c, a):
    if c.get("stop") == FATAL[0]:
        return ("fatal",), ()
    if "stop" in c:
        return ("stop", c["stop"], c.get("msg")), ()
    if fam == "coll":
        return obs_coll(c, a)
    return OBS[fam](c, a), ()


def cmd_check(d):
    allc = build()
    calls, reads, writes = read_out(os.path.join(d, "s6f.out"))
    out, bad = [], 0
    if len(calls) != len(allc):
        out.append("BAD count out=%d cases=%d" % (len(calls), len(allc)))
        bad += 1
    stats, rows = {}, []
    for (fam, a), c in zip(allc, calls):
        got, res = observed(fam, c, a)
        want, names = predict(fam, a, results=res)
        s = stats.setdefault(fam, {"cases": 0, "bad": 0, "stops": 0, "fatal": 0})
        s["cases"] += 1
        s["stops"] += got[0] == "stop"
        s["fatal"] += want[0] == "fatal"
        if tuple(want) != tuple(got):
            s["bad"] += 1
            if s["bad"] <= 5:
                out.append("BAD %s case=%d want=%s got=%s" % (fam, c["n"], want, got))
        rows.append((fam, a, got, res, want, names))
    for fam in FAMILIES:
        s = stats.get(fam, {})
        out.append("FAMILY %s %s" % (fam, " ".join("%s=%d" % kv for kv in s.items())))
        bad += s.get("bad", 0) + s.get("stops", 0)
    # tallies
    t = {}

    def inc(k):
        t[k] = t.get(k, 0) + 1
    for fam, a, got, res, want, _ in rows:
        if fam == "wc" and want[0] == "ret":
            nm = struct.pack("<I", want[1]).decode("latin-1").strip()
            if nm in ("1js", "1jt", "1st", "1ss", "ht2"):
                inc("wc-%s" % nm)
            if a["inv"] is not None and want[3] != a["inv"]["prim"]:
                inc("wc-primary-set")
        if fam == "wc" and want[0] == "fatal":
            inc("wc-fatal")
        if fam == "seq":
            k = "seq-t%d-%s" % (a["type"], "0" if want[0] == "ret" and want[1] == 0 else want[0])
            inc(k)
            if a["type"] == 0 and a["sk"] is not None and img().sk[a["sk"]]["seq"] >= 24 and want[0] == "ret":
                inc("seq-t0-idx-past-24")
        if fam == "sinit" and want[0] == "sinit":
            inc("sinit-t%d-%s" % (a["type"], "set" if want[1] else "none"))
            if a.get("_later_record_differs"):
                inc("sinit-later-lookups-other-record")
        if fam == "sadv" and want[0] == "sadv":
            w = s32(a["prev"] + a["r"]) >= a["L"]
            inc("sadv-%s" % ("wrap" if w else "nowrap"))
            if want[5]:
                inc("sadv-event")
        if fam == "pme":
            inc("pme-%s" % ("%08x" % want[1] if want[0] == "obs" else want[0]))
        if fam == "coll" and want[0] == "coll":
            n = want[4]
            inc("coll-%s" % ("blocked" if want[2] else ("ten" if n >= 10 else "end")))
            if n >= 10 and a["mark"] == 0:
                cells = room_cells()
                x, y = a["x"], a["y"]
                tx, ty = u32(x + s32(a["dx"])), u32(y + s32(a["dy"]))
                hx, hy = halve(s32(a["dx"]), s32(a["dy"]))
                xa, ya, cur, k, past = x, y, ((x >> 16), (y >> 16)), 0, False
                while cur != ((tx >> 16), (ty >> 16)) and k < 100000:
                    k += 1
                    xa, ya = u32(xa + hx), u32(ya + hy)
                    nw = ((xa >> 16), (ya >> 16))
                    if nw != cur:
                        X, Y = nw[0] - ROOM_RECT[0], nw[1] - ROOM_RECT[1]
                        if 0 <= X < ROOM_RECT[2] and 0 <= Y < ROOM_RECT[3] and cells[Y * ROOM_RECT[2] + X] & \
                                (0x3C01 if a["mask"] == 0x3401 else a["mask"]):
                            past = True
                    cur = nw
                if past:
                    inc("coll-ten-past-a-blocked-cell")
            if a["flags"] & 0x20000 and want[4]:
                inc("coll-list")
    out += ["TALLY %s %d" % kv for kv in sorted(t.items())]
    # controls
    names = {}
    for fam, a, got, res, want, nm in rows:
        names.setdefault(fam, set()).update(nm)
    unsep = []
    for fam in FAMILIES:
        for nm in sorted(names.get(fam, ())):
            sep = passed = 0
            for f, a, got, res, want, _ in rows:
                if f != fam:
                    continue
                try:
                    alt, _ = predict(f, a, nm, res)
                except Exception:                                   # a control that runs off its own model separates
                    alt = ("model-error",)
                if alt != want:
                    sep += 1
                    if alt[0] != "fatal" and tuple(alt) == tuple(got):
                        passed += 1
            out.append("CTRL %s %s sep=%d passed=%d" % (fam, nm, sep, passed))
            bad += passed
            if sep == 0:
                unsep.append("%s:%s" % (fam, nm))
    out.append("UNSEPARATED %s" % (" ".join(unsep) or "none"))
    # traced accesses
    un = 0
    for lo, n, nm, sn in CONST_READS:
        sect = img().sect[sn]
        ok = sect[0] <= lo and lo + n <= sect[0] + sect[1]
        out.append("CONST %08x %d %s in %s [%08x, %08x): %d" % (lo, n, nm, sn, sect[0], sect[0] + sect[1], int(ok)))
        bad += 0 if ok else 1
    for pc, addr, size, cnt in reads:
        if not any(lo <= addr and addr + size <= lo + n for lo, n, _, _ in CONST_READS):
            un += 1
            out.append("READ pc=%08x addr=%08x size=%d n=%d" % (pc, addr, size, cnt))
    for pc, addr, size, cnt in writes:
        un += 1
        out.append("WRITE pc=%08x addr=%08x size=%d n=%d" % (pc, addr, size, cnt))
    out.append("ACCESS reads=%d writes=%d unaccounted=%d" % (len(reads), len(writes), un))
    bad += un
    out.append("SCAN check bad=%d" % bad)
    txt = "\n".join(out) + "\n"
    open(os.path.join(d, "check.txt"), "w").write(txt)
    sys.stdout.write(txt)
    return 0 if bad == 0 else 1


def cmd_knock(d):
    """Recount run:2026-11-03-path-emu-3's kept `knock` family: line-shortened plans, +0x90 values, `noline`."""
    import path_emu3 as P3
    rooms, cases = P3.family("knock", R54C)
    R = {r.addr: r for r in rooms}
    calls, _ = P3.read_out(os.path.join(R54C, "knock.out"))
    seen = {}
    orig_los, orig_knock = P3.line_of_sight, P3.PLANNERS[P3.KNOCK]

    def los(c, s, t):
        r, q = orig_los(c, s, t)
        if seen.get("mode") == "noline":
            return 1, None
        seen["line"] = (r, s, t, q)
        return r, q

    def kn(c):
        seen["b90"] = c.path(0x90, 1)
        return orig_knock(c)
    P3.line_of_sight = los
    P3.PLANNERS[P3.KNOCK] = kn
    n = match = short = refused_line = 0
    b90 = {}
    sep = passed = 0
    for c, case in zip(calls, cases):
        if "stop" in c:
            continue
        seen.clear()
        kind, val, M, st = P3.predict(case, R)
        ok = P3.compare(c, case, kind, val, M)
        n += 1
        match += ok
        if not ok:
            continue
        b = seen.get("b90")
        b90[b] = b90.get(b, 0) + 1
        ln = seen.get("line")
        if ln and not ln[0]:
            short += 1
            if kind == "ret" and val == 0:
                refused_line += 1
        seen.clear()
        seen["mode"] = "noline"
        k2, v2, M2, _ = P3.predict(case, R)
        if (k2, v2) != (kind, val) or M2.snap(P3.UPATH, 0x200) != M.snap(P3.UPATH, 0x200):
            sep += 1
            if P3.compare(c, case, k2, v2, M2):
                passed += 1
    P3.line_of_sight, P3.PLANNERS[P3.KNOCK] = orig_los, orig_knock
    h = hashlib.sha256(open(os.path.join(R54C, "knock.out"), "rb").read()).hexdigest()
    six = sum(v for k, v in b90.items() if k is not None and (k >> 1) + 1 == 6)
    lines = ["KNOCK kept=knock.out sha256=%s cases=%d match=%d line_blocked=%d line_blocked_to_start=%d" % (
                 h, n, match, short, refused_line),
             "KNOCK b90_values=%d with_n6=%d (b90 10 or 11) histogram=%s" % (len(b90), six,
                                                                              ",".join("%s:%d" % kv for kv in sorted(b90.items()))),
             "CTRL knock noline sep=%d passed=%d" % (sep, passed)]
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "knock.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if match == n and passed == 0 else 1


def cmd_manifest(d, write):
    names = ["s6f.cases", "s6f.mem", "s6f.out", "s6f.err", "check.txt", "knock.txt"] + sorted(
        x for x in os.listdir(d) if x.startswith("s6f-") and x.endswith(".bin"))
    lines = ["%s  %s" % (hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest(), n) for n in names]
    if write:
        open(os.path.join(d, "manifest.sha256"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["cases", "check", "knock", "manifest"])
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        return cmd_cases(a.dir) or 0
    if a.cmd == "check":
        return cmd_check(a.dir)
    if a.cmd == "knock":
        return cmd_knock(a.dir)
    return cmd_manifest(a.dir, a.write) or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
