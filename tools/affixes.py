#!/usr/bin/env python3
"""Affix selection model (plan 0021 Phase 2), checked against tools/gdb/affixes.gdb logs; chained after tools/uniques.py.

    python3 -I tools/affixes.py check <log> [<log> ...] [--excel DIR] [-v]
    python3 -I tools/affixes.py survey [--excel DIR]

Model of the builders that sub_00557450_ItemCreateByQuality calls for qualities 1, 2, 3, 4 and 6 (directly or as a
fallback step) and of the post-switch automagic pick, as read in docs/findings/items/0005-affixes.md:
  - ITEMS_PickMagicAffix (0x005C1560): draw #1 (one step; bit 0 = 0 and no mustRoll -> no affix), alvl
    (max(ilvl, qlvl), then + magic lvl, or - qlvl/2 below 99 - qlvl/2, else 2*i - 99; clamp 1..99), the ordered
    filter (spawnable, version, level window, rare on qualities 6/8/9, ITEMS_MagicAffixTypeOk, the automagic group,
    frequency, classspecific, group already on the item), weights frequency (x level on a magic-lvl base), draw #2
    low % (W + 1), the subtract walk with a draw of W taking the last candidate;
  - ITEMS_BuildMagic (0x005565E0): prefix pick (mustRoll 0), suffix pick (mustRoll 1 when no prefix), properties
    inside each pick; fails when both are 0; the charm path of the normal builder (0x00556A60) is the same pair;
  - ITEMS_BuildRare (0x005C21A0): the item type's Rare = 0 -> fail at once; ITEMS_PickRareName (prefix side, then
    suffix side; uniform RNG_RangeOffset over the rows ITEMS_RareNameTypeOk keeps), the count (jewel type 58:
    3 + low % 2; else g_RareAffixCountTable[low & 7]), the slot loop (one side bit per slot while both sides are open,
    a failed pick closes its side and the slot is retried, each side closes at 3), properties after the loop in the
    order prefix k, suffix k;
  - ITEMS_BuildSuperiorPick (0x005C2970): rejection sampling over the QualityItems rows (4 for a throwable or
    nodurability base), the type test sub_0065E7D0_QualityItemTypeOk;
  - ITEMS_BuildLowPick (0x005C2D40): RNG_Range(seed, nLow); success only for a weapon (45) or armour (50);
  - the normal builder (0x00556E80): no draw of its own (charms: the magic pair);
  - after the switch: the automagic pick (expansion item, quality not 5 or 7, base `auto prefix` != 0): one pick
    over the automagic block with autoGroup = auto prefix, spawnable not tested.
Every fallback step starts from {S, 666} with the affix slots cleared (items/0004 section 5, tools/uniques.py).

ADR-0004 boundary oracles (architect ruling, plan 0021 Phase 1): sub_0065FEC0_ItemApplyProps (APR0/APR1) and
ITEMS_RollStaffMods (STF0/STF1): the model asserts the item seed at entry and takes the exit seed from the log.
The post-switch ethereal (ETB0/ETB1; ETH0/ETH1 in logs before plan 0027 Phase 3) and socket (SCK0/SCK1) rolls are
outside this plan (items/0004 section 8): their entry seed is asserted and their exit seed taken from the log. In a
log that also carries tools/gdb/props.py's lines (tools/gdb/items-chain.gdb), props.py's ETH0 (it has "rfl") is not
read here.
tools/items_chain.py sets PROPS_HOOK to tools/props.py's model of ItemApplyProps, which turns the APR0/APR1 oracle
into a check, and runs the builders with Walk(free=True) (no log lines) on the property logs.

The unique and set builders and the fallback chain stay with tools/uniques.py: every block is first checked by
uniques.check_block (on the uniques lines), then walked here with the unique and set builders' exit seed from BRET.

Asserted per creation: every builder's entry seed (BLD), every pick's arguments, quality, ilvl, version, the
item's prefixes and suffixes so far and seed (AF0), alvl, magic lvl, the candidate ids, count and W (AFC), the draw
and seed (AFX), the id and seed (AFR); rare names: the side, the candidate ids, n, r (RN), the id and seed (RNX);
the rare count and seed (RC); every superior draw (SUPD) and type test (SUPT); the low row and seed (LOWR); every
oracle entry seed and record (APR0, STF0); the seed at the join (ICJ), at the ethereal and socket entries, and at
the return (ICX).

Logs without the affix lines (the plan 0019 logs): uniques.check_block as before, and the join seed (ICJ) is asserted
only after a builder that needs no oracle: a low or normal build on a type without StaffMods (and not a charm).

Exit 0 only when every creation reproduces. Stdlib only. Read-only.
"""
import argparse
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402
import rng  # noqa: E402
import uniques  # noqa: E402

EXCEL = uniques.EXCEL
RARE_COUNT = (3, 4, 4, 5, 5, 5, 6, 6)          # data:g_RareAffixCountTable@0x006E3014
AFFIX_TAGS = ("AF0", "AFC", "AFX", "AFR", "RN0", "RN", "RNX", "RC", "APR0", "APR1", "STF0", "STF1", "SUPD", "SUPT",
              "LOWR", "ETH0", "ETH1", "ETB0", "ETB1", "SCK0", "SCK1", "AV0", "STFC")
ETB_LEGACY = {"ETB0": "ETH0", "ETB1": "ETH1"}   # the renamed ethereal boundary tags (plan 0027 Phase 3)
TAGS = uniques.TAGS + AFFIX_TAGS
FIRST_SKILL = {0: 6, 1: 36, 2: 66, 3: 96, 4: 126, 5: 221, 6: 251}   # docs/tables/Skills.md, Class blocks
RET_PICK = {0x005C190E: "magic", 0x005C1970: "auto", 0x005C1D01: "rare-s", 0x005C1D7E: "rare-p"}
Mismatch = uniques.Mismatch
eq = uniques.eq
fmt = uniques.fmt
seedpair = uniques.seedpair


def recs(excel, table):
    return uniques.recs(excel, table)


def s16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def s32(b, o):
    return struct.unpack_from("<i", b, o)[0]


class Tables(uniques.Tables):
    def __init__(self, excel):
        super().__init__(excel)
        self.magic = []
        blocks = {}
        for t in ("magicsuffix", "magicprefix", "automagic"):               # sub_00633730_LoadMagicAffixes
            start = len(self.magic)
            for r in recs(excel, t):
                self.magic.append(dict(
                    name=r[0:32].split(b"\0")[0].decode("latin1"), ver=u16(r, 0x22), mod1=s32(r, 0x24),
                    spawn=r[0x54], level=s32(r, 0x58), group=s32(r, 0x5C), maxlevel=s32(r, 0x60), rare=r[0x64],
                    cs=r[0x66], itype=[s16(r, 0x6A + 2 * k) for k in range(7)],
                    etype=[s16(r, 0x78 + 2 * k) for k in range(5)], freq=r[0x82]))
            blocks[t] = (start, len(self.magic))
        self.blk_s, self.blk_p, self.blk_a = blocks["magicsuffix"], blocks["magicprefix"], blocks["automagic"]
        self.rare = []
        rb = {}
        for t in ("raresuffix", "rareprefix"):                              # sub_00633F40_LoadRareAffixes
            start = len(self.rare)
            for r in recs(excel, t):
                self.rare.append(dict(name=r[0x26:0x26 + 32].split(b"\0")[0].decode("latin1"), ver=u16(r, 0x0E),
                                      itype=[s16(r, 0x10 + 2 * k) for k in range(7)],
                                      etype=[s16(r, 0x1E + 2 * k) for k in range(4)]))
            rb[t] = (start, len(self.rare))
        self.rblk_s, self.rblk_p = rb["raresuffix"], rb["rareprefix"]
        self.props = [u16(r, 0x20) for r in recs(excel, "properties")]
        self.qitems = [bytes(r[0:10]) for r in recs(excel, "qualityitems")]
        self.nlow = len(recs(excel, "lowqualityitems"))
        sk = recs(excel, "skills")                                          # staff mods (plan 0038 batch S2b)
        self.nskills = len(sk)                                              # DataTables+0xBA0
        self.skill_itype = [s16(r, 0x18) for r in sk]                      # itypea1, read as s16 at 0x005C1141
        self.skill_class = [r[0x0C] for r in sk]                           # charclass
        self._closure = {}
        self._base = {}

    def class_skill_count(self, c):
        """0x00646140(c): the number of skills of character class c."""
        return sum(1 for x in self.skill_class if x == c)

    def first_class_skill(self, c):
        """0x006460F0(c, 0): the first skill of class c (Skills.md, Class blocks)."""
        return next(i for i, x in enumerate(self.skill_class) if x == c)

    # -- bases and types
    def b(self, cls):
        if cls in self._base:
            return self._base[cls]
        r = self.items[cls]
        self._base[cls] = dict(qlvl=r[0xFD], mlvl=r[0x140], hasinv=r[0x137], gemsock=r[0x138], type=s16(r, 0x11E),
                    type2=s16(r, 0x120), stack=r[0x132], auto=u16(r, 0xF8), nodur=r[0x113],
                    code=r[0x80:0x84].decode("latin1").strip())
        return self._base[cls]

    def closure(self, t):
        if t not in self._closure:
            seen, stack = set(), [t]
            while stack:
                x = stack.pop()
                if x <= 0 or x in seen or x >= len(self.itypes):
                    continue
                seen.add(x)
                stack += [u16(self.itypes[x], 4), u16(self.itypes[x], 6)]
            self._closure[t] = seen
        return self._closure[t]

    def is_type(self, cls, t):
        """ITEMS_UnitIsType@0x00629BB0: t in the Equiv closure of the base's type or type2."""
        if t < 0 or t >= len(self.itypes):
            return False
        b = self.b(cls)
        return t in self.closure(b["type"]) or (b["type2"] > 0 and t in self.closure(b["type2"]))

    def tbyte(self, cls, off, missing=0):
        t = self.b(cls)["type"]
        return self.itypes[t][off] if 0 <= t < len(self.itypes) else missing

    def tclass(self, cls):
        c = self.tbyte(cls, 0x21, 7)
        return c if c < 7 else 7

    def maxsock(self, cls, ilvl):
        """sub_0062BC20_ItemMaxSockets: min(base gemsockets, the type's MaxSock1/25/40 by ilvl)."""
        col = 0x1A if ilvl <= 25 else 0x1B if ilvl <= 40 else 0x1C
        return min(self.b(cls)["gemsock"], self.tbyte(cls, col))


class Item:
    def __init__(self, T, ic):
        self.T, self.cls, self.ilvl, self.ver = T, ic["cls"], ic["ilvl"], ic["ver"]
        self.base = T.b(ic["cls"])
        self.q = None
        self.p = [0, 0, 0]
        self.s = [0, 0, 0]
        self.fp = [0, 0, 0]         # the creation record's forced prefixes (+0x68) and suffixes (+0x74): 0 on a drop,
        self.fs = [0, 0, 0]         # the cube's pre=/suf= (tools/cube.py)
        self.rfl = ic.get("rfl", 0) or 0   # the record's +0x80 flags (bit 0x20: the staff-mods bonus)

    def clear(self):
        self.p = [0, 0, 0]
        self.s = [0, 0, 0]


def type_ok(T, it, r, skip_sock=False):
    """ITEMS_MagicAffixTypeOk@0x0065E620 (skip_sock: without test (b), for the run's statistics only)."""
    b = it.base
    if it.ver < 100 and (b["stack"] or T.tbyte(it.cls, 0x10)):
        return False
    if not skip_sock and not (b["hasinv"] and T.maxsock(it.cls, it.ilvl) > 0):
        if r["mod1"] >= 0 and (r["mod1"] >= len(T.props) or T.props[r["mod1"]] == 194):
            return False
    for e in r["etype"]:
        if e <= 0:
            break
        if T.is_type(it.cls, e):
            return False
    for t in r["itype"]:
        if t <= 0:
            break
        if T.is_type(it.cls, t):
            return True
    return False


def rare_name_ok(T, it, r):
    """ITEMS_RareNameTypeOk@0x0065E710."""
    if it.ver < 100 and (it.base["stack"] or T.tbyte(it.cls, 0x10)):
        return False
    if r["ver"] >= 100 and it.ver < 100:
        return False
    for e in r["etype"]:
        if e <= 0:
            break
        if T.is_type(it.cls, e):
            return False
    for t in r["itype"]:
        if t <= 0:
            break
        if T.is_type(it.cls, t):
            return True
    return False


def group_taken(T, it, g):
    """sub_005C1500_AffixGroupTaken: prefixes 0..2 then suffixes 0..2, each list up to its first empty slot."""
    for lst in (it.p, it.s):
        for a in lst:
            if not a:
                break
            if T.magic[a - 1]["group"] == g:
                return True
    return False


def alvl_of(it):
    qlvl, m = it.base["qlvl"], it.base["mlvl"]
    a = it.ilvl if it.ilvl > qlvl else qlvl
    if m:
        a += m
    else:
        h = qlvl // 2
        a = a - h if a < 99 - h else 2 * a - h - (99 - h)
    if a <= 1:
        a = 1
    elif a >= 99:
        a = 99
    return a


class Walk:
    """The affix lines of one creation, consumed in order, with the model's seed."""

    def __init__(self, T, ev, it, stats, notes, ctx, free=False):
        self.T, self.ev, self.i, self.it, self.stats, self.notes, self.ctx = T, ev, 0, it, stats, notes, ctx
        self.seed = None
        self.free = free            # no log lines: every take() returns values equal to anything (items_chain.py)
        self.apr = []               # the ItemApplyProps calls made: (mode, rec, entry seed, what)

    def peek(self):
        return self.ev[self.i][0] if self.i < len(self.ev) else None

    def take(self, tag):
        if self.free:
            return _AnyDict()
        if self.i >= len(self.ev):
            raise Mismatch("missing %s" % tag)
        t, d = self.ev[self.i]
        if t != tag:
            raise Mismatch("expected %s, log has %s %s" % (tag, t, json.dumps(d)[:300]))
        self.i += 1
        return d

    def skip_to(self, tag):
        while self.peek() is not None and self.peek() != tag:
            self.i += 1
        return self.take(tag)

    def step(self):
        self.seed = rng.step(*self.seed)
        return self.seed[0]

    def oracle(self, t0, t1, what, check=None, mode=0, rec=None):
        d = self.take(t0)
        eq("%s entry seed (oracle)" % what, fmt(self.seed), d["seed"])
        if check:
            check(d)
        if t0 == "APR0" and PROPS_HOOK is not None:
            self.apr.append((mode, rec, fmt(self.seed), what))
            new = PROPS_HOOK(mode, rec, self.seed, self.it)
            if not self.free:
                eq("%s exit seed (tools/props.py model)" % what, fmt(new), self.take(t1)["seed"])
                self.stats["ItemApplyProps exit seeds predicted by tools/props.py"] += 1
            self.seed = new
            return d
        if self.free:
            raise StaffModsUnmodelled(t0)
        self.seed = seedpair(self.take(t1)["seed"])
        return d

    # -- ITEMS_PickMagicAffix
    def pick(self, kind, spawn, must, apply, pre, forced=0, auto=0):
        T, it = self.T, self.it
        d = self.take("AF0")
        if not self.free:
            eq("pick caller", kind, RET_PICK.get(d["ret"], hex(d["ret"])) if kind != "charm" else
               ("charm" if d["ret"] == 0x005C190E else hex(d["ret"])))
        for k, v in (("spawn", spawn), ("must", must), ("apply", apply), ("pre", pre), ("forced", forced),
                     ("auto", auto), ("q", it.q), ("ilvl", it.ilvl), ("ver", it.ver), ("p", it.p), ("s", it.s)):
            eq("pick %s" % k, v, d[k])
        eq("pick entry seed", fmt(self.seed), d["seed"])
        lo = self.step()
        rec = dict(kind=kind, pre=pre, alvl=None, n=0, W=0, id=0, rolled=bool(lo & 1) or bool(must))
        if not (lo & 1) and not must:
            d = self.take("AFR")
            eq("pick id (no roll)", 0, d["id"])
            eq("seed after a pick with no roll", fmt(self.seed), d["seed"])
            rec["exit"] = "no-roll"
            self.stats["pick no-roll %s" % kind] += 1
            return 0, rec
        a0, a1 = T.blk_a if auto else T.blk_p if pre else T.blk_s
        alvl = alvl_of(it)
        if it.ver < 100 and (it.base["stack"] or T.tbyte(it.cls, 0x10)):
            self.stats["classic stackable/throwable base: picks"] += 1
        sockless = not (it.base["hasinv"] and T.maxsock(it.cls, it.ilvl) > 0)
        sockref = 0
        m = it.base["mlvl"]
        cands, W = [], 0
        naive = set()                   # contradiction 1: the rows a "level <= ilvl + 2" window would keep
        for i in range(a0, a1):
            r = T.magic[i]
            if spawn and r["spawn"] == 0:
                continue
            if r["ver"] >= 100 and it.ver < 100:
                continue
            isforced = forced > 0 and i - a0 == forced - 1
            if r["level"] <= it.ilvl + 2 and self.passes_rest(r, auto):
                naive.add(i + 1)
            if not isforced:
                if r["level"] > alvl:
                    continue
                if r["maxlevel"] != 0 and r["maxlevel"] < alvl:
                    continue
            if r["rare"] == 0 and it.q in (6, 8, 9):
                continue
            if not type_ok(T, it, r):
                if sockless and r["mod1"] >= 0 and type_ok(T, it, r, True):
                    sockref += 1
                continue
            if auto and r["group"] != auto:
                continue
            if r["freq"] == 0:
                continue
            if r["cs"] != 0xFF and T.tclass(it.cls) != 7 and r["cs"] != T.tclass(it.cls):
                continue
            if group_taken(T, it, r["group"]):
                continue
            if isforced:
                # the forced row passed every test but the level window: chosen with no weighted draw
                # (items/0005 section 3, 0x005C180B); reached by the cube's pre=/suf= (tools/cube.py)
                aid = i + 1
                rec.update(alvl=alvl, n=len(cands), W=W, m=m, id=aid, exit="forced")
                self.stats["pick forced row %s" % kind] += 1
                if apply:
                    self.oracle("APR0", "APR1", "ItemApplyProps (forced pick)",
                                lambda d: (eq("props caller", "auto" if auto else "pick", d["k"]),
                                           eq("props record", aid, d["rec"])), rec=aid)
                d = self.take("AFR")
                eq("pick id (forced)", aid, d["id"])
                eq("seed at the pick's return", fmt(self.seed), d["seed"])
                return aid, rec
            w = r["freq"] * r["level"] if m else r["freq"]
            cands.append((i + 1, w))
            W += w
        if sockref:
            self.stats["picks where the socket test (b) refused a row"] += 1
        d = self.take("AFC")
        eq("alvl", alvl, d["alvl"])
        eq("magic lvl", m, d["m"])
        eq("candidate count", len(cands), d["n"])
        eq("candidate W", W, d["W"])
        eq("candidate ids", [c[0] for c in cands], d["ids"])
        eq("seed after draw #1", fmt(self.seed), d["seed"])
        rec.update(alvl=alvl, n=len(cands), W=W, m=m)
        if naive != set(c[0] for c in cands):
            self.stats["c1: picks whose candidate set differs from level <= ilvl + 2"] += 1
        if not cands:
            d = self.take("AFR")
            eq("pick id (no candidate)", 0, d["id"])
            eq("seed after a pick with no candidate", fmt(self.seed), d["seed"])
            rec["exit"] = "no-candidate"
            self.stats["pick no-candidate %s" % kind] += 1
            self.notes["empty"].append("%s %s %s ilvl %d alvl %d q %d" % (self.ctx, kind, it.base["code"], it.ilvl,
                                                                          alvl, it.q))
            return 0, rec
        lo = self.step()
        x = (self.seed[1] if PICK_CF == "high-word" else lo) % (W + 1)
        d = self.take("AFX")
        eq("pick draw x", x, d["x"])
        eq("seed after draw #2", fmt(self.seed), d["seed"])
        k, xx = len(cands) - 1, x
        for j, (_, w) in enumerate(cands):
            xx -= w
            if xx < 0 and PICK_CF != "unsigned-walk":
                k = j
                break
        if x == W:
            self.stats["last-candidate rule (x = W)"] += 1
            self.notes["lastcand"].append("%s %s %s x=W=%d -> id %d (last of %d)" % (
                self.ctx, kind, it.base["code"], W, cands[-1][0], len(cands)))
        aid = cands[k][0]
        rec.update(x=x, id=aid, exit="row")
        if apply:
            self.oracle("APR0", "APR1", "ItemApplyProps (pick)",
                        lambda d: (eq("props caller", "auto" if auto else "pick", d["k"]),
                                   eq("props record", aid, d["rec"])), rec=aid)
        d = self.take("AFR")
        eq("pick id", aid, d["id"])
        eq("seed at the pick's return", fmt(self.seed), d["seed"])
        self.stats["pick row %s" % kind] += 1
        self.record_pick(rec, cands)
        return aid, rec

    def passes_rest(self, r, auto):
        """The filter tests after the level window, without the group test (for the c1 comparison only)."""
        T, it = self.T, self.it
        if r["rare"] == 0 and it.q in (6, 8, 9):
            return False
        if not type_ok(T, it, r) or (auto and r["group"] != auto) or r["freq"] == 0:
            return False
        if r["cs"] != 0xFF and T.tclass(it.cls) != 7 and r["cs"] != T.tclass(it.cls):
            return False
        return not group_taken(T, it, r["group"])

    def record_pick(self, rec, cands):
        T, it = self.T, self.it
        r = T.magic[rec["id"] - 1]
        # contradiction 1 (plan 0021 Phase 1b): the community rule "uniform over qlvl <= ilvl + 2"
        if rec["alvl"] != it.ilvl + 2:
            self.stats["c1: picks with alvl != ilvl + 2"] += 1
        if r["level"] > it.ilvl + 2:
            self.stats["c1: picked row level > ilvl + 2"] += 1
            self.notes["c1"].append("%s %s %s ilvl %d qlvl %d mlvl %d alvl %d: row id %d (%s) level %d" % (
                self.ctx, rec["kind"], it.base["code"], it.ilvl, it.base["qlvl"], it.base["mlvl"], rec["alvl"],
                rec["id"], r["name"], r["level"]))
        if len(set(w for _, w in cands)) > 1:
            self.stats["c1: picks over unequal weights"] += 1
        if r["cs"] != 0xFF:
            self.stats["classspecific row picked"] += 1
            self.notes["cs"].append("%s %s %s (type class %d): id %d %s classspecific %d" % (
                self.ctx, rec["kind"], it.base["code"], T.tclass(it.cls), rec["id"], r["name"], r["cs"]))
        if rec.get("m"):
            self.stats["picks on a magic-lvl base (weights x level)"] += 1

    # -- builders
    def magic(self, kind="magic"):
        """ITEMS_BuildMagic with the record's forced ids it.fp[0] / it.fs[0] (0 on a drop; items/0005 section 5)."""
        it = self.it
        fp, fs = it.fp[0], it.fs[0]
        p = s = 0
        prec = {}
        suf_must = 0
        done = False
        if fp < 0:
            suf_must = 1
        else:
            p, prec = self.pick(kind, 1, 1 if fp > 0 else 0, 1, 1, fp)
            it.p[0] = p
            if p == 0:
                suf_must = 1
            elif fs < 0:
                done = True
        if not done:
            if fs > 0:
                suf_must = 1
            s, srec = self.pick(kind, 1, suf_must, 1, 0, fs)
            it.s[0] = s
        ok = bool(p or s)
        shape = "both" if p and s else "prefix" if p else "suffix" if s else "none"
        if kind == "magic":
            self.stats["magic %s" % shape] += 1
            if not p and prec.get("exit") == "no-candidate":
                self.notes["magic-forced-suffix"].append("%s %s ilvl %d: no prefix candidate, suffix %s" % (
                    self.ctx, it.base["code"], it.ilvl, s))
        if ok and kind == "magic":
            self.staff("magic")
        return ok

    def staff_model(self, k):
        """ITEMS_RollStaffMods modelled (STAFF_MODEL): the STF0 entry seed asserted, STFC compared, the STF1 exit
        seed predicted and compared. The predicted (skill, level) writes are kept in self.staff_out."""
        T, it = self.T, self.it
        if not self.free:
            d = self.take("STF0")
            eq("ITEMS_RollStaffMods entry seed", fmt(self.seed), d["seed"])
            eq("staff mods caller", k, d["k"])
        new, out, info = staff_mods(T, it, self.seed)
        if not self.free:
            if info is not None and self.peek() == "STFC":
                d = self.take("STFC")
                eq("staff mods class (ItemTypes StaffMods)", info["cls"], d["cls"])
                eq("staff mods firstSkill(c)", info["first"], d["first"])
                self.stats["staff mods: class and firstSkill(c) compared (STFC)"] += 1
            elif info is not None:
                self.stats["staff mods: STFC not logged (seed 2101's logger had no STFC line)"] += 1
            elif self.peek() == "STFC":
                raise Mismatch("STFC logged on a type the model gives no staff-mods class")
            eq("ITEMS_RollStaffMods exit seed (model)", fmt(new), self.take("STF1")["seed"])
        key = "none" if info is None else "class %d" % info["cls"]
        self.stats["staff mods modelled: %s" % key] += 1
        if info is not None:
            self.stats["staff mods modelled: %d mods" % info["mods"]] += 1
            for x in ("fallback", "lowcap", "lownodraw", "typerefused"):
                if info.get(x):
                    self.stats["staff mods modelled: %s" % x] += info[x]
            if not self.free:
                self.stats["staff mods exit seeds predicted (STF1)"] += 1
        self.staff_out = out
        self.staff_info = info
        self.seed = new

    def staff(self, k):
        if STAFF_MODEL:
            return self.staff_model(k)
        if self.free:
            if self.T.tbyte(self.it.cls, 0x1F, 0xFF) >= 7:
                return                  # no StaffMods class: the oracle's seed does not move (legacy rule above)
            raise StaffModsUnmodelled(k)
        d = self.take("STF0")
        eq("ITEMS_RollStaffMods entry seed (oracle)", fmt(self.seed), d["seed"])
        eq("staff mods caller", k, d["k"])
        c = self.T.tbyte(self.it.cls, 0x1F, 0xFF)
        if self.peek() == "STFC":
            d = self.take("STFC")
            eq("staff mods class (ItemTypes StaffMods)", c, d["cls"])
            want = FIRST_SKILL.get(c)
            self.stats["staff mods: firstSkill logged"] += 1
            if d["first"] == want:
                self.stats["staff mods: firstSkill = first id of the class run"] += 1
            else:
                self.notes["firstskill"].append("class %d: firstSkill %d, class run starts at %s" % (
                    c, d["first"], want))
            self.notes["staffclass"].append("%s %s class %d first %d" % (self.ctx, self.it.base["code"], c,
                                                                          d["first"]))
        before = self.seed
        self.seed = seedpair(self.take("STF1")["seed"])
        if c >= 7:
            self.stats["staff mods on a type without StaffMods: seed %s" % (
                "unchanged" if self.seed == before else "MOVED")] += 1

    def rare_name(self, pre):
        T, it = self.T, self.it
        d = self.take("RN0")
        eq("rare name side", pre, d["pre"])
        eq("rare name entry seed", fmt(self.seed), d["seed"])
        a0, a1 = T.rblk_p if pre else T.rblk_s
        cands = [i + 1 for i in range(a0, a1) if rare_name_ok(T, it, T.rare[i])]
        nid = 0
        if cands:
            lo = self.step()
            r = lo % len(cands)
            d = self.take("RN")
            eq("rare name candidates", cands, d["ids"])
            eq("rare name n", len(cands), d["n"])
            eq("rare name draw", r, d["r"])
            eq("seed after the rare name draw", fmt(self.seed), d["seed"])
            nid = cands[r]
        d = self.take("RNX")
        eq("rare name id", nid, d["id"])
        eq("seed after the rare name pick", fmt(self.seed), d["seed"])
        return nid

    def rare(self):
        T, it = self.T, self.it
        if not T.tbyte(it.cls, 0x15):
            self.stats["rare: type cannot be rare"] += 1
            return False
        n1 = self.rare_name(1)
        n2 = self.rare_name(0)
        if not n1 or not n2:
            self.stats["rare: no name"] += 1
            return False
        jewel = it.base["type"] == 58
        lo = self.step()
        count = 3 + lo % 2 if jewel else RARE_COUNT[lo & 7]
        d = self.take("RC")
        eq("rare count", count, d["count"])
        eq("seed after the count draw", fmt(self.seed), d["seed"])
        np_ = ns = 0
        pre_done = suf_done = False
        i = 0
        closed = []
        sides = []
        while i < count:
            if pre_done:
                if suf_done:
                    break
                side = 0
            elif suf_done:
                side = 1
            else:
                lo = self.step()
                side = 0 if lo & 1 else 1
            if side == 0:
                a, _ = self.pick("rare-s", 1, 1, 0, 0)
                if not a:
                    suf_done = True
                    closed.append("suffix@%d" % i)
                    continue
                it.s[ns] = a
                ns += 1
                if ns >= 3:
                    suf_done = True
            else:
                a, _ = self.pick("rare-p", 1, 1, 0, 1)
                if not a:
                    pre_done = True
                    closed.append("prefix@%d" % i)
                    continue
                it.p[np_] = a
                np_ += 1
                if np_ >= 3:
                    pre_done = True
            sides.append("p" if side else "s")
            i += 1
        rec = dict(count=count, np=np_, ns=ns, closed=closed, jewel=jewel)
        if not np_ and not ns:
            self.stats["rare: no affix"] += 1
            return False
        for k in range(3):
            if it.p[k]:
                self.oracle("APR0", "APR1", "ItemApplyProps (rare prefix %d)" % k,
                            lambda d, k=k: (eq("props caller", "rare-p", d["k"]), eq("props record", it.p[k], d["rec"])),
                            rec=it.p[k])
            if it.s[k]:
                self.oracle("APR0", "APR1", "ItemApplyProps (rare suffix %d)" % k,
                            lambda d, k=k: (eq("props caller", "rare-s", d["k"]), eq("props record", it.s[k], d["rec"])),
                            rec=it.s[k])
        self.staff("rare")
        key = "jewel " if jewel else ""
        self.stats["rare %scount %d" % (key, count)] += 1
        self.stats["rare %saffixes %d" % (key, np_ + ns)] += 1
        if np_ + ns < count:
            self.stats["rare: short (fewer affixes than the count)"] += 1
        if closed:
            self.stats["rare: a side closed by a failed pick"] += 1
            self.notes["closed"].append("%s %s ilvl %d count %d -> %d prefixes %d suffixes, closed %s" % (
                self.ctx, it.base["code"], it.ilvl, count, np_, ns, ",".join(closed)))
        if np_ == 3 or ns == 3:
            self.stats["rare: a side full at 3"] += 1
        self.stats["rare: names drawn before the count and the affixes"] += 1
        self.rare_info = dict(rec, n1=n1, n2=n2, sides="".join(sides))
        return True

    def crafted(self):
        """sub_005C21D0_ItemBuildCrafted (items/0008 section 4, re-read from the disassembly for plan 0030 Phase 2):
        two rare names (prefix side, then suffix side; either 0 fails the build with nothing set), the count
        n = max(low % 5 (unsigned), tier) with tier 1..4 for ilvl <= 30, <= 50, <= 70, above; then per slot one side
        draw (suffix when the prefixes are full, else prefix when the suffixes are full, else suffix on bit 0 = 1) and
        picks (spawnable 1, mustRoll 1, applyProps 0, the record's forced id of that slot) until the id is neither
        an id nor of the group of a filled slot of that side, at most 252 picks, after which the slot is written 0 and
        its count not advanced; then the properties prefix 0, suffix 0, prefix 1, ... and the staff mods."""
        T, it = self.T, self.it
        n1 = self.rare_name(1)
        n2 = self.rare_name(0)
        if not n1 or not n2:
            self.stats["crafted: no name"] += 1
            return False
        il = it.ilvl
        tier = 4 if il > 70 else 3 if il > 50 else 2 if il > 30 else 1
        lo = self.step()
        n = lo % 5
        if tier > n:
            n = tier
        np_ = ns = 0
        sides = []
        for _ in range(n):
            lo = self.step()
            suffix = np_ == 3 or (ns != 3 and lo & 1)
            lst, k = (it.s, ns) if suffix else (it.p, np_)
            forced = (it.fs if suffix else it.fp)[k]
            t = 0
            while True:
                aid, _ = self.pick("crafted-%s" % ("s" if suffix else "p"), 1, 1, 0, 0 if suffix else 1, forced)
                grp = T.magic[aid - 1]["group"] if aid else None
                clash = False
                for x in lst:
                    if not x:
                        continue
                    if x == aid or (aid and T.magic[x - 1]["group"] == grp):
                        clash = True
                        break
                if not clash:
                    lst[k] = aid
                    if suffix:
                        ns += 1
                    else:
                        np_ += 1
                    break
                old_t = t
                t += 1
                self.stats["crafted: redraw (same id or group)"] += 1
                if old_t > 250:
                    lst[k] = 0
                    self.stats["crafted: slot left empty after 252 picks"] += 1
                    break
            sides.append("s" if suffix else "p")
        for k in range(3):
            if it.p[k]:
                self.oracle("APR0", "APR1", "ItemApplyProps (crafted prefix %d)" % k,
                            lambda d, k=k: eq("props record", it.p[k], d["rec"]), rec=it.p[k])
            if it.s[k]:
                self.oracle("APR0", "APR1", "ItemApplyProps (crafted suffix %d)" % k,
                            lambda d, k=k: eq("props record", it.s[k], d["rec"]), rec=it.s[k])
        self.staff("crafted")
        self.stats["crafted count %d (tier %d)" % (n, tier)] += 1
        self.crafted_info = dict(n1=n1, n2=n2, count=n, tier=tier, sides="".join(sides))
        return True

    def superior(self):
        T, it = self.T, self.it
        n = len(T.qitems)
        if T.tbyte(it.cls, 0x10) or it.base["nodur"]:
            n = 4
        tried = [0] * 10
        while True:
            while True:
                if n < 1:
                    row = 0
                else:
                    lo = self.step()
                    row = lo % n
                d = self.take("SUPD")
                eq("superior row draw", row, d["row"])
                eq("superior tried flag", tried[row], d["tried"])
                eq("seed after a superior draw", fmt(self.seed), d["seed"])
                if not tried[row]:
                    break
                self.stats["superior: redraw of a tried row"] += 1
            if row >= len(T.qitems):
                return False
            ok = self.quality_type_ok(T.qitems[row])
            eq("superior type test", 1 if ok else 0, self.take("SUPT")["ok"])
            if ok:
                self.oracle("APR0", "APR1", "ItemApplyProps (superior)",
                            lambda d: (eq("props caller", "superior", d["k"]), eq("props mode", 1, d["mode"]),
                                       eq("superior row", row, d["rec"])), mode=1, rec=row)
                self.staff("superior")
                self.stats["superior row %d" % row] += 1
                return True
            tried[row] = 1
            self.stats["superior: row refused by the type test"] += 1
            if all(tried[k] for k in range(n)):
                return False

    def quality_type_ok(self, q):
        """sub_0065E7D0_QualityItemTypeOk."""
        T, it = self.T, self.it
        t = it.base["type"]
        if q[1] and T.is_type(it.cls, 45) and t not in (26, 27, 35, 24, 25):
            return True
        if q[0] and T.is_type(it.cls, 50) and t not in (2, 15, 16, 19):
            return True
        for tt, k in ((2, 2), (24, 3), (25, 4), (26, 5), (27, 6), (35, 6), (15, 7), (16, 8), (19, 9)):
            if t == tt and q[k]:
                return True
        return False

    def low(self):
        T, it = self.T, self.it
        n = T.nlow
        if n < 1:
            row = 0
        else:
            lo = self.step()
            row = lo % n
        d = self.take("LOWR")
        eq("low row", row, d["row"])
        eq("low row count", n, d["n"])
        eq("seed after the low draw", fmt(self.seed), d["seed"])
        self.staff("low")
        ok = T.is_type(it.cls, 45) or T.is_type(it.cls, 50)
        self.stats["low row %d%s" % (row, "" if ok else " (not weapon/armour: fails)")] += 1
        return ok

    def normal(self):
        T, it = self.T, self.it
        if T.is_type(it.cls, 13):
            self.magic("charm")
            self.stats["normal: charm pair"] += 1
        self.staff("normal")
        return True

    def automagic(self):
        T, it = self.T, self.it
        g = it.base["auto"]
        aid, rec = self.pick("auto", 0, 1, 0, 1, 0, g)
        if aid:
            self.oracle("APR0", "APR1", "ItemApplyProps (automagic)",
                        lambda d: (eq("props caller", "auto", d["k"]), eq("props record", aid, d["rec"])), rec=aid)
            self.stats["automagic row"] += 1
            self.stats["automagic row on quality %d" % it.q] += 1
            if T.tclass(it.cls) != 7:
                self.stats["automagic on a class item"] += 1
                self.notes["auto-class"].append("%s %s q %d (type class %d, group %d): id %d %s" % (
                    self.ctx, it.base["code"], it.q, T.tclass(it.cls), g, aid, T.magic[aid - 1]["name"]))
        else:
            self.stats["automagic: no row (%s)" % rec.get("exit")] += 1
            self.notes["auto-none"].append("%s %s q %d group %d alvl %s: %s" % (
                self.ctx, it.base["code"], it.q, g, rec.get("alvl"), rec.get("exit")))
        return aid


class _Any:
    """A logged value that the free walk (tools/items_chain.py) does not have: equal to anything."""
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    __hash__ = object.__hash__


class _AnyDict(dict):
    def __missing__(self, key):
        return _Any()


class StaffModsUnmodelled(Exception):
    """The free walk reached ITEMS_RollStaffMods on a type with StaffMods (a seed oracle with no logged exit)."""


# Hook for tools/items_chain.py: props_hook(mode, rec, seed, it) -> the item seed after ItemApplyProps, predicted by
# tools/props.py. When set, the APR0/APR1 oracle becomes a check (the logged APR1 seed is compared, not taken).
PROPS_HOOK = None

# Plan 0038 batch S2b: when True, ITEMS_RollStaffMods is modelled (staff_mods below) instead of being the STF0/STF1
# seed oracle: the logged STF1 seed is compared, not taken, and the free walk (tools/items_chain.py) no longer stops
# at a StaffMods type. `check` sets it by default since plan 0048 Phase 1 (oracle 2 retired); `check --staff oracle`
# keeps the plan 0021 oracle (ADR-0004 switch). A caller whose namespace has no `staff` attribute keeps the oracle.
STAFF_MODEL = False
# Counterfactual variant of the pick (tools/items_sweep.py cf): "high-word" draws from the seed's high word,
# "unsigned-walk" compares the running x as unsigned (never below 0). Each must FAIL; never on by default.
PICK_CF = None
# Counterfactual variant of staff_mods (tools/items_sweep.py cf): each must FAIL on logs where its rule decides.
STAFF_CF = None


def staff_mods(T, it, seed, cf=None):
    """ITEMS_RollStaffMods@0x005C1260 and its expansion body sub_005C0F90_StaffModsRoll@0x005C0F90, as read in
    docs/findings/items/0005-affixes.md section 9 and re-read in the disassembly (plan 0038 batch S2b).
    it: the affix model's Item (cls, ilvl = the record's +0x0C, ver, q = the item's quality at the call, rfl = the
    record's +0x80). Returns (seed after, [(skill, level)] in write order, info); raises Mismatch for the version-0
    body, which is not modelled. Every `low % k` is on the unsigned low word of the item seed after one step."""
    cf = cf or STAFF_CF
    c = T.tbyte(it.cls, 0x1F, 7)                         # sub_0062BBD0_ItemTypeStaffMods: 7 = none
    if c >= 7 or T.class_skill_count(c) <= 0:
        return seed, [], None
    if it.ver == 0:
        raise Mismatch("staff mods: version-0 body sub_005C0D70_StaffModsRollV0 not modelled")
    first = T.first_class_skill(c)                       # 0x006460F0(c, 0)
    ilvl = it.ilvl
    bonus = ilvl if (getattr(it, "rfl", 0) & 0x20) else 0
    info = {"cls": c, "first": first, "bonus": bonus}
    state = [seed]

    def step():
        state[0] = rng.step(*state[0])
        return state[0][0]
    t = step() % 100 + bonus                             # 0x005C0FB0-0x005C0FDB
    if t > 90:
        n = 3
    elif t > 70:
        n = 2
    elif t > 30 or (cf == "count-ge" and t >= 30):
        n = 1
    elif bonus == 0:
        info["mods"] = 0
        return state[0], [], info                        # 0x005C0FFC: no mod
    else:
        n = 1
    if ilvl > 36 and (it.ver >= 100 or cf == "tier-noexp"):
        tier = 5                                         # 0x005C100A-0x005C102C
    elif ilvl > 24:
        tier = 4
    elif ilvl > 18:
        tier = 3
    elif ilvl > 11:
        tier = 2
    else:
        tier = 1
    used = [-1, -1, -1]
    out = []
    info.update(mods=n, tier=tier, fallback=0, lowcap=0, lownodraw=0, typerefused=0)
    for i in range(n):
        u = step() % 100                                 # 0x005C1065-0x005C10B4
        if u > 80:
            tt = tier + 1
        elif u > 30:
            tt = tier
        elif u > 10:
            tt = tier - 1
        else:
            tt = tier - 2
        if tt < 1:
            tt = 1
        if it.q == 1 and tt >= 4 and cf != "nolowcap":   # 0x005C10C4-0x005C10D4
            if tt > 4:
                info["lowcap"] += 1
            tt = 4
        tries = 6
        while True:                                      # 0x005C10E2-0x005C1174
            lo = step()
            if cf == "signed-low":
                slo = lo - (1 << 32) if lo & 0x80000000 else lo
                skill = _cmod(slo, 5) + 5 * (tt - 1) + first
            else:
                skill = lo % 5 + 5 * (tt - 1) + first
            if skill < 0 or skill >= T.nskills:
                type_ok = True
            else:
                req = T.skill_itype[skill]
                type_ok = req < 1 or T.is_type(it.cls, req) or cf == "notype"
                if not type_ok:
                    info["typerefused"] += 1
            if type_ok and skill not in used:
                used[i] = skill
                break
            tries -= 1
            if tries <= 0:
                info["fallback"] += 1                    # 0x005C1174: the last skill drawn, not stored in used[]
                break
        level = 1
        if it.ver < 100 or it.q != 1 or cf == "lowdraw":  # 0x005C117D-0x005C11EC
            v = step() % 100 + int(bonus / 2)
            level = 3 if v >= 90 else 2 if v >= 60 else 1
        else:
            info["lownodraw"] += 1
        out.append((skill, level))                       # 0x005C1232 STATLIST_SetStat(list, 107, level, skill)
    return state[0], out, info


def _cmod(a, n):
    """C remainder (sign of the dividend), for the signed-low counterfactual."""
    r = abs(a) % n
    return -r if a < 0 else r

BUILDERS = {"magic": "magic", "rare": "rare", "superior": "superior", "low": "low", "normal": "normal",
            "crafted": "crafted"}


def check_affixes(T, ev, stats, notes, legacy, res):
    """Walk one creation's lines (all tags) after uniques.check_block accepted it. res: its summary."""
    ic = ev[0][1]
    it = Item(T, ic)
    mode = "exp" if ic["ver"] >= 100 else "classic"
    dn = ("normal", "nightmare", "hell")[ic["diff"]] if ic["diff"] is not None else "?"
    ctx = "%s/%s" % (mode, dn)
    W = Walk(T, ev, it, stats, notes, ctx)
    W.take("IC0")
    W.seed = seedpair(ic["seed"])
    S = W.seed[0]
    it.q = W.take("ICQ")["q"]
    built = []
    ok = None
    first = True
    while True:
        t = W.peek()
        if t == "BLD":
            d = W.take("BLD")
            k = d["k"]
            if k == "normalcase":
                continue
            eq("%s entry seed" % k, fmt(W.seed), d["seed"])
            if not first:
                it.clear()
            first = False
            it.q = d["q"]
            if k in ("unique", "set"):
                d = W.skip_to("BRET")
                ok = bool(d["ret"])
                W.seed = seedpair(d["seed"])
                built.append(k if ok else k + "(fail)")
                continue
            if legacy:
                ok = None
                if k in ("low", "normal") and T.tbyte(it.cls, 0x1F, 0xFF) >= 7 and not T.is_type(it.cls, 13):
                    if k == "low":
                        W.step()
                    ok = True
                    built.append(k)
                    W.seed_known = True
                else:
                    W.seed_known = False
                    built.append(k + "?")
                continue
            W.rare_info = None
            ok = getattr(W, BUILDERS[k])()
            built.append(k if ok else k + "(fail)")
            if ok and k in ("magic", "rare"):
                W.stats["built %s %s %s" % (k, mode, dn)] += 1
                if k == "rare":
                    notes["rares"].append("%s %s ilvl %d: names %d/%d count %d sides %s -> %dp %ds%s" % (
                        ctx, it.base["code"], it.ilvl, W.rare_info["n1"], W.rare_info["n2"], W.rare_info["count"],
                        W.rare_info["sides"], W.rare_info["np"], W.rare_info["ns"],
                        " closed " + ",".join(W.rare_info["closed"]) if W.rare_info["closed"] else ""))
            elif ok:
                W.stats["built %s" % k] += 1
            continue
        if t == "FB":
            d = W.take("FB")
            if ok:
                raise Mismatch("fallback after a builder the model says succeeded")
            W.seed = (S, 666)
            W.seed_known = True
            continue
        if t in uniques.TAGS and t not in ("ICJ", "ICX"):
            W.i += 1                          # DUR, PROPS, UMADE ...: checked by uniques.check_block
            continue
        break
    d = W.take("ICJ")
    if legacy and not getattr(W, "seed_known", True):
        res["legacy_unchecked"] = built
        return built
    eq("seed at the join (after the builder chain)", fmt(W.seed), d["seed"])
    it.q = d["q"]
    if legacy:
        res["legacy_checked"] = built
        return built
    if it.ver >= 100:
        W.oracle("ETH0", "ETH1", "ethereal roll (boundary)")
    if 1 <= it.q <= 3:
        W.oracle("SCK0", "SCK1", "socket roll (boundary)")
    if it.ver >= 100 and it.q not in (5, 7) and it.base["auto"]:
        W.automagic()
        built.append("auto")
    elif it.ver >= 100 and it.base["auto"]:
        stats["automagic skipped: quality %d with an auto prefix base" % it.q] += 1
    elif it.ver < 100 and it.base["auto"]:
        stats["automagic skipped: classic item with an auto prefix base"] += 1
    x = W.take("ICX")
    eq("seed at the return (ICX)", fmt(W.seed), x["seed"])
    if W.i != len(ev):
        raise Mismatch("unconsumed lines: %s" % [t for t, _ in ev[W.i:]])
    return built


def read_log(path):
    """As uniques.read_log, keeping the affix lines too."""
    open_ = {}
    cpre = None
    last = None
    for line in open(path, errors="replace"):
        line = line.rstrip("\n")
        tag, _, rest = line.partition(" ")
        if tag == "GAME":
            yield "GAME", None
            continue
        if tag == "CPRE":
            cpre = dict(x.split("=", 1) for x in rest.split() if "=" in x)
            continue
        if tag == "CPOST":
            cpre = None
            continue
        if tag not in TAGS or not rest.startswith("{"):
            continue
        try:
            d = json.loads(rest)
        except ValueError:
            continue
        if tag == "ETH0" and "rfl" in d:
            continue                          # tools/gdb/props.py's ETH0, not the affix logger's boundary
        tag = ETB_LEGACY.get(tag, tag)
        if tag == "IC0":
            last = d.get("th", 0)
            open_[last] = [[("IC0", d)], cpre]
            continue
        if not open_ or last not in open_:
            continue
        cur = open_[last]
        cur[0].append((tag, d))
        if tag == "ICX":
            yield cur[0], cur[1]
            del open_[last]


def has_affix_lines(path):
    with open(path, errors="replace") as f:
        for line in f:
            if line.startswith(("AF0 ", "STF0 ", "ETB0 ", "RC ")):
                return True
            if line.startswith("ETH0 ") and '"rfl"' not in line:
                return True
    return False


def cmd_check(ns):
    global STAFF_MODEL
    if getattr(ns, "staff", "oracle") == "model":
        STAFF_MODEL = True
    T = Tables(ns.excel)
    ok = bad = 0
    stats = collections.Counter()
    ustats = collections.Counter()
    notes = collections.defaultdict(list)
    table = collections.Counter()
    for path in ns.logs:
        legacy = not has_affix_lines(path)
        stats["logs %s" % ("without affix lines" if legacy else "with affix lines")] += 1
        made = set()
        game = 0
        for blk, cpre in read_log(path):
            if blk == "GAME":
                made = set()
                game += 1
                continue
            ublk = [(t, d) for t, d in blk if t in uniques.TAGS]
            try:
                res = uniques.check_block(T, ublk, made, ustats, cpre)
                if "skip" in res:
                    ok += 1
                    stats["skipped (not a drop path)"] += 1
                    continue
                built = check_affixes(T, blk, stats, notes, legacy, res)
            except (Mismatch, KeyError, IndexError, TypeError) as e:
                bad += 1
                print("FAIL %s game %d IC0 %s: %s" % (os.path.basename(path), game, json.dumps(blk[0][1]), e))
                continue
            ok += 1
            mode = "exp" if res["ver"] >= 100 else "classic"
            dn = ("normal", "nightmare", "hell")[res["diff"]] if res["diff"] is not None else "?"
            if legacy:
                stats["legacy: join seed asserted"] += 1 if "legacy_checked" in res else 0
                stats["legacy: join seed not checkable (oracle inside)"] += 1 if "legacy_unchecked" in res else 0
            table[(mode, dn, "drop" if res["drop"] else "other", "+".join(built))] += 1
    print("%d creations reproduced, %d failed" % (ok, bad))
    print("chains by mode, difficulty, source:")
    for k, v in sorted(table.items()):
        print("  %-7s %-9s %-5s %-40s %d" % (k[0], k[1], k[2], k[3], v))
    for k in sorted(stats):
        print("%s: %d" % (k, stats[k]))
    for k in ("firstskill", "staffclass", "c1", "cs", "auto-class", "auto-none", "empty", "closed", "lastcand", "magic-forced-suffix", "rares"):
        if notes[k]:
            print("-- %s (%d)" % (k, len(notes[k])))
            for n in notes[k][: (None if ns.verbose else 25)]:
                print("   " + n)
    return 0 if bad == 0 else 1


def side_rows(T, it, blk, spawn=True, auto=0):
    """The rows of a block that pass every filter test that does not depend on the level window or on the
    affixes already on the item (in their order of ITEMS_PickMagicAffix)."""
    out = []
    for i in range(*blk):
        r = T.magic[i]
        if spawn and r["spawn"] == 0:
            continue
        if r["ver"] >= 100 and it.ver < 100:
            continue
        if r["rare"] == 0 and it.q in (6, 8, 9):
            continue
        if not type_ok(T, it, r):
            continue
        if auto and r["group"] != auto:
            continue
        if r["freq"] == 0:
            continue
        if r["cs"] != 0xFF and T.tclass(it.cls) != 7 and r["cs"] != T.tclass(it.cls):
            continue
        out.append(r)
    return out


def cmd_survey(ns):
    """Reachability on stock data, per base, item version (1 classic, 101 expansion) and ilvl 1..99:
    for every base whose type is not `Normal` (those are always built as quality 2): the magic sides with no candidate, the automagic groups with no candidate, and for rare-able types the least
    number of distinct groups on a rare side (a rare pick can fail only when a side has fewer groups than picks)."""
    T = Tables(ns.excel)
    empty = collections.defaultdict(list)
    mingroups = []
    for cls in range(len(T.items)):
        b = T.b(cls)
        if T.tbyte(cls, 0x16, 1):                        # ItemTypes Normal: always quality 2 (items/0004 section 2)
            continue
        for ver in (1, 101):
            rows = {}                                    # the socket test depends on ilvl through max sockets
            for ilvl in range(1, 100):
                for q in (4, 6):
                    it = Item(T, dict(cls=cls, ilvl=ilvl, ver=ver))
                    it.q = q
                    key = (q, T.maxsock(cls, ilvl) > 0)
                    if key not in rows:
                        rows[key] = [side_rows(T, it, T.blk_p), side_rows(T, it, T.blk_s),
                                     side_rows(T, it, T.blk_a, False, b["auto"]) if b["auto"] and ver >= 100 else None]
                    a = alvl_of(it)
                    live = [None if rs is None else [r for r in rs if r["level"] <= a and
                                                     (r["maxlevel"] == 0 or r["maxlevel"] >= a)]
                            for rs in rows[key]]
                    if q == 4:
                        if not live[0]:
                            empty[(b["code"], ver, "magic: no prefix candidate")].append(ilvl)
                        if not live[1]:
                            empty[(b["code"], ver, "magic: no suffix candidate")].append(ilvl)
                    if live[2] is not None and not live[2]:
                        empty[(b["code"], ver, "automagic (q %d): no candidate, group %d" % (q, b["auto"]))].append(ilvl)
                    if q == 6 and T.tbyte(cls, 0x15):
                        names = [any(rare_name_ok(T, it, T.rare[i]) for i in range(*blk))
                                 for blk in (T.rblk_p, T.rblk_s)]
                        if all(names):
                            g = min(len(set(r["group"] for r in live[0])), len(set(r["group"] for r in live[1])))
                            mingroups.append((g, b["code"], ver, ilvl))
                        else:
                            empty[(b["code"], ver, "rare: no name candidate")].append(ilvl)
    print("== sides with no candidate (base, item version, what: ilvl range and count) ==")
    for k, v in sorted(empty.items(), key=lambda kv: (kv[0][2], kv[0][1], kv[0][0])):
        print("  %-5s %3d  %-48s ilvl %d..%d (%d)" % (k[0], k[1], k[2], min(v), max(v), len(v)))
    g = min(mingroups)
    print("== rare sides: least number of distinct groups over every rare-able base with both names, ilvl 1..99 ==")
    print("  %d (%s, version %d, ilvl %d); bases x versions x ilvls checked: %d" % (g[0], g[1], g[2], g[3],
                                                                                   len(mingroups)))
    print("  under 3 (a third pick on that side could fail): %d" % sum(1 for m in mingroups if m[0] < 3))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("logs", nargs="+")
    c.add_argument("--excel", default=EXCEL)
    c.add_argument("-v", "--verbose", action="store_true")
    c.add_argument("--staff", choices=("oracle", "model"), default="model",
                   help="ITEMS_RollStaffMods: the staff_mods model (default since plan 0048 Phase 1) or the STF0/STF1 "
                        "seed oracle")
    v = sub.add_parser("survey")
    v.add_argument("--excel", default=EXCEL)
    ns = ap.parse_args(argv)
    return {"check": cmd_check, "survey": cmd_survey}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
