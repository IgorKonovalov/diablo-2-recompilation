#!/usr/bin/env python3
"""Horadric Cube transmute model (plan 0030 Phase 2), checked against tools/gdb/cube.gdb logs.

    python3 -I tools/cube.py check <log> [<log> ...] [--excel DIR] [-v]

Model of docs/findings/items/0008-cube.md, chained after tools/items_chain.py (tools/uniques.py, tools/affixes.py and
tools/props.py), from the cube's contents and the game seed at the transmute (CUB0) only:
  - CUBE_Transmute's row scan (section 1): enabled, version, ladder, min diff, class, numinputs = the cube's item count,
    the player ops; every row that reaches sub_005658C0_CubeMatchInputs is compared with the CMI lines, its result
    with CMIR, and the first match with CROW.
  - CUBE_MatchInput (section 2): per input, every unclaimed cube item in list order through the item test (base or
    type with upg, quality, unique/set row, nos/sock, noe/eth, bas/exc/eli, nru, op 28 on stat 356), the socketable
    first-input test, ops 15..27 on input 1; the count (= qty, or >= qty once a claimed item is stackable); the
    three output slots filled from input 1 with output A's kind and flags (CROW slots).
  - sub_00565AB0_RecipeOutputCreate (section 3), outputs A, B, C: the ilvl (lvl, else the player's level x plvl /
    100 + input 1's ilvl x ilvl / 100, clamped to [1, experience MaxLvl]); the special outputs (the cow portal's
    tests from the logged quest words and level, its spot search and portal object as ADR-0004 oracles (return
    values); the Pandemonium handlers return 0); a created item (fixed code, usetype, item type): the creation
    record (CREC), the game-seed draws of CubePickItemOfType, SUnitCreate and ItemSeedInit (unit seed, start seed,
    IIS0, IC0), sub_00557AB0_ItemInitStats (tools/props.py check_iis), sub_00557450_ItemCreateByQuality with the
    quality-0 creation roll (sub_00556F60_ItemRollQualityCreate, modelled here) and the crafted builder
    (sub_005C21D0_ItemBuildCrafted, tools/affixes.py Walk.crafted), through tools/props.py check_ic (every
    ItemApplyProps call, ethereal, sockets, the lists at LX) and tools/items_chain.py check_creation (the builders'
    picks from their entry seed, the cube's pre=/suf= as forced ids); useitem and mod: sub_0055A2A0_ItemCopy's two
    game-seed steps, the copy's start, item and unit seeds predicted (its class, quality, affixes and lists must
    equal the input's); mod:
    the class change and ItemInitStats on the copy's unit seed; then the mod lines (sub_00660240_CubeModApply:
    PROP_ApplyBlock through tools/props.py's Roller, slot by slot, CMOD/CMODX), the ethereal re-apply, rep, rch,
    qty and sock= (ITEMS_SetSockets with the cube's quality clamp).
  - The finish (section 3.5): the cube's items are destroyed only when something was produced (CDES), each output
    is placed identified (CPL, CUBX), and the game seed at CUBX is the model's.
Exit 0 only when every transmute reproduces. Stdlib only. Read-only.
"""
import argparse
import collections
import copy
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import affixes  # noqa: E402
import excel_bin  # noqa: E402
import items_chain  # noqa: E402
import props  # noqa: E402
import quality  # noqa: E402
import rng  # noqa: E402
import uniques  # noqa: E402

EXCEL = uniques.EXCEL
M32 = 0xFFFFFFFF
Mismatch = props.Mismatch
eq = props.eq
KIND = {0: "none", 1: "cow portal", 2: "pandemonium portal", 3: "pandemonium finale portal", 0xFC: "item",
        0xFD: "type", 0xFE: "useitem", 0xFF: "usetype"}
MISC = 52                     # itemtypes 52 `misc`: ItemRollQualityCreate's level term is 1


def s16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def s32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def seedpair(s):
    a, b = s.split(":")
    return int(a, 16), int(b, 16)


def fmt(seed):
    return "%08x:%08x" % seed


# ---------------------------------------------------------------- tables

class Tables:
    def __init__(self, excel):
        self.P = props.Tables(excel)
        self.A = affixes.Tables(excel)
        self.Q = quality.Tables(excel)
        self.rows = [self.row(r) for r in excel_bin.read_bin(excel_bin.find_file(excel, "cubemain", ".bin"))[0]]
        isc = props.recs(excel, "itemstatcost")
        self.isc_n = len(isc)
        exp = props.recs(excel, "experience")
        self.maxlvl = s32(exp[0], 0)              # sub_00611830_ExpMaxLevel(0): record 0, class 0 (MaxLvl)
        self.codes = {}
        for i, r in enumerate(self.P.items):
            c = r[0x80:0x84]
            self.codes.setdefault(c, i)

    @staticmethod
    def row(r):
        ins = []
        for k in range(7):
            o = 0x14 + 8 * k
            ins.append(dict(flags=u16(r, o), index=u16(r, o + 2), row1=u16(r, o + 4), q=r[o + 6], qty=r[o + 7]))
        outs = []
        for s in range(3):
            o = 0x4C + 0x54 * s
            mods = []
            for m in range(5):
                mo = o + 0x18 + 12 * m
                mods.append(dict(prop=s32(r, mo), par=s16(r, mo + 4), min=s16(r, mo + 6), max=s16(r, mo + 8),
                                 chance=r[mo + 10]))
            outs.append(dict(flags=u16(r, o), index=u16(r, o + 2), row1=u16(r, o + 4), q=r[o + 6], qty=r[o + 7],
                             kind=r[o + 8], lvl=r[o + 9], plvl=r[o + 10], ilvl=r[o + 11],
                             pre=[u16(r, o + 0xC + 2 * i) for i in range(3)],
                             suf=[u16(r, o + 0x12 + 2 * i) for i in range(3)], mods=mods))
        return dict(enabled=r[0], ladder=r[1], mindiff=r[2], cls=r[3], op=r[4], param=s32(r, 8), value=s32(r, 0xC),
                    n=r[0x10], ver=u16(r, 0x12), ins=ins, outs=outs)

    def raw(self, cls):
        return self.P.items[cls]

    def code(self, cls):
        return self.raw(cls)[0x80:0x84]

    def tiers(self, cls):
        r = self.raw(cls)
        return r[0x84:0x88], r[0x88:0x8C], r[0x8C:0x90]


# ---------------------------------------------------------------- item helpers (logged UNIT dicts)

def base_of(it):
    return {(s, p): v for s, p, v in (it.get("b") or [])}


def subs_of(it):
    return [[st, fl, {(s, p): v for s, p, v in ent}] for st, fl, ent, *_ in it.get("sub", [])]


def stat_eval(it, stat):
    """STATS_GetUnitStat on an item: the base entry plus every attached list not flagged 0x2000."""
    v = base_of(it).get((stat, 0), 0)
    for st, fl, e in subs_of(it):
        if not fl & 0x2000:
            v += e.get((stat, 0), 0)
    return v


def norm(subs):
    return sorted((st, fl, tuple(sorted(e.items()))) for st, fl, e in subs)


def state_of(T, it):
    return props.Item.from_dump(T.P, it["cls"], it["q"], it["ilvl"], it["ver"], it["fl"], it, it["seed"])


# ---------------------------------------------------------------- the match

def row_filter(T, r, c, n):
    """CUBE_Transmute's tests before the matcher (0x00566653-0x00566A40); ops 1..14 are not used by stock rows."""
    if not r["enabled"]:
        return False, "disabled"
    if not c["exp"] and r["ver"] >= 100:
        return False, "version"
    if c["g6a"] == 0 and not c["ladder"] and r["ladder"]:
        return False, "ladder"
    if r["mindiff"] > c["diff"]:
        return False, "min diff"
    if r["cls"] != 0xFF and r["cls"] != c["pcls"]:
        return False, "class"
    if r["n"] != n:
        return False, "numinputs"
    if 1 <= r["op"] <= 14:
        raise Mismatch("player op %d not modelled (no stock row uses it)" % r["op"])
    return True, ""


def item_test(T, r, k, it, game):
    """CUBE_MatchInput's tests for input k against one cube item, up to the claimed test (0x005650D3-0x00565323)."""
    inp = r["ins"][k]
    cls = it["cls"]
    raw = T.raw(cls)
    code = raw[0x80:0x84]
    if inp["flags"] & 1:
        if inp["index"] != 0xFFFF:
            if inp["flags"] & 0x80:                                 # upg: the named base or a higher tier of it
                norm_, uber, ultra = T.tiers(cls)
                icode = T.code(inp["index"])
                if code == norm_:
                    ok = icode == norm_
                elif code == uber:
                    ok = icode in (norm_, uber)
                elif code == ultra:
                    ok = icode in (norm_, uber, ultra)
                else:
                    ok = False
                if not ok:
                    return False
            elif cls != inp["index"]:
                return False
    elif inp["flags"] & 2:
        if not T.A.is_type(cls, inp["index"]):
            return False
    if inp["q"] and it["q"] != inp["q"]:
        return False
    if inp["flags"] & 0x40 and it["fi"] != inp["row1"] - 1:
        return False
    socks = stat_eval(it, 194)
    if inp["flags"] & 4:
        if socks > 0:
            return False
    elif inp["flags"] & 8:
        if socks <= 0:
            return False
    eth = bool(it["fl"] & 0x400000)
    if inp["flags"] & 0x20:
        if eth:
            return False
    elif inp["flags"] & 0x10:
        if not eth:
            return False
    norm_, uber, ultra = T.tiers(cls)
    if inp["flags"] & 0x100:
        if code != norm_:
            return False
    elif inp["flags"] & 0x200:
        if code != uber:
            return False
    elif inp["flags"] & 0x400:
        if code != ultra:
            return False
    if inp["flags"] & 0x800 and it["fl"] & 0x4000000:
        return False
    if r["op"] == 28 and raw[0x12A] and raw[0x12B]:
        if stat_eval(it, 356) < game["diff"]:
            return False
    if k == 0:
        o = r["outs"][0]
        if o["kind"] in (0xFF, 0xFE) and o["flags"] & 2:
            if T.P.max_sockets(cls, it["ilvl"]) == 0:
                return False
    return True


def fill_slots(T, r, it, slots, game):
    """The three output slots from input 1's item (0x005656EE-0x00565816), all from output A's kind and flags."""
    o = r["outs"][0]
    for s in range(3):
        sl = slots[s]
        sl[2] = it["ilvl"]
        if o["flags"] & 1:
            sl[0] = it["u"]
        if o["kind"] in (0xFF, 0xFE):
            sl[0] = it["u"]
            sl[1] = it["cls"] if o["kind"] == 0xFF else -1
            norm_, uber, ultra = T.tiers(it["cls"])
            tcode = uber if o["flags"] & 0x80 else ultra if o["flags"] & 0x100 else None
            if tcode is not None and tcode != b"    ":
                idx = T.codes.get(tcode)
                if idx is not None and (game["exp"] or u16(T.raw(idx), 0xF6) < 100):
                    sl[1] = idx


def match_input(T, r, k, items, claimed, slots, game):
    inp = r["ins"][k]
    if not inp["flags"] & 3:
        return True
    need = inp["qty"] if inp["qty"] > 0 else 1
    got, exact = 0, True
    for ordn, it in enumerate(items, 1):
        if not item_test(T, r, k, it, game):
            continue
        if ordn <= 48 and claimed[ordn - 1]:
            continue
        if k == 0:
            if 15 <= r["op"] <= 27:
                raise Mismatch("input op %d not modelled (no stock row uses it)" % r["op"])
            fill_slots(T, r, it, slots, game)
        if ordn <= 48:
            claimed[ordn - 1] = True
        got += 1
        if T.raw(it["cls"])[0x132]:
            exact = False
    return got == need if exact else got >= need


def match(T, c):
    """The row scan: [(row, matcher result)], the matched row or None, its slots."""
    items = c["items"]
    n = len(items)
    reached = []
    if n <= 0:
        return reached, None, None
    for i, r in enumerate(T.rows):
        ok, _ = row_filter(T, r, c, n)
        if not ok:
            continue
        claimed = [False] * 48
        slots = [[0, 0, 0] for _ in range(3)]
        res = all(match_input(T, r, k, items, claimed, slots, c) for k in range(7))
        reached.append((i, 1 if res else 0))
        if res:
            return reached, i, slots
    return reached, None, None


# ---------------------------------------------------------------- the creation-side quality roll

def create_roll(T, ic, seed):
    """sub_00556F60_ItemRollQualityCreate with a record of quality 0 and an item version >= 1 (0x00556F60-0x0055714C):
    a `quest` base returns 2 with no draw; else d = 1 for a `misc` item, else max(record ilvl - base level, 1); over
    the ItemRatio row of ITEMRATIO_Select(item, version 100) the codes 7, 6, 5, 4, 3, 2 in turn: c = base - d / divisor
    (signed, truncating); c <= 0 wins with no draw, else RNG_RangeB(item seed, c) = 0 wins; after the six, 3 when the
    record's flags have 0x40, else 1."""
    cls = ic["cls"]
    raw = T.raw(cls)
    if ic["ver"] < 1:
        raise Mismatch("creation roll of a version-0 item not modelled")
    if raw[0x12A]:
        return 2, seed
    if T.A.is_type(cls, MISC):
        d = 1
    else:
        d = ic["ilvl"] - raw[0xFD]
        if d < 1:
            d = 1
    ri = T.Q.select(cls, 100)
    if ri is None:
        raise Mismatch("no itemratio row for the creation roll")
    v = [quality.s32(x) for x in T.Q.ratio[ri]["v"]]
    for code, bi, di in ((7, 0, 1), (6, 3, 4), (5, 6, 7), (4, 9, 10), (3, 12, 13), (2, 14, 15)):
        c = v[bi] - quality.cdiv(d, v[di])
        if c <= 0:
            return code, seed
        r, seed = quality.range_b(seed, c)
        if r == 0:
            return code, seed
    return (3 if ic["rfl"] & 0x40 else 1), seed


# ---------------------------------------------------------------- log reading

class TX:
    def __init__(self, c):
        self.c, self.ev = c, []


def read_log(path):
    """Yield one TX per transmute: the CUB0 line and every line up to its CUBX, in order."""
    cur = None
    for line in open(path, errors="replace"):
        tag, _, rest = line.rstrip("\n").partition(" ")
        if not rest.startswith("{"):
            continue
        try:
            d = json.loads(rest)
        except ValueError:
            continue
        if tag == "CUB0":
            cur = TX(d)
            continue
        if cur is None or tag == "PDT":
            continue
        cur.ev.append((tag, d))
        if tag == "CUBX":
            yield cur
            cur = None


def split_until(ev, i, end_tags):
    out = []
    while i < len(ev):
        t, d = ev[i]
        out.append((t, d))
        i += 1
        if t in end_tags:
            break
    return out, i


# ---------------------------------------------------------------- the outputs

class Ctx:
    def __init__(self, T, tx, S, notes, pdt):
        self.T, self.tx, self.S, self.notes, self.pdt = T, tx, S, notes, pdt
        self.ev, self.i = tx.ev, 0
        self.gs = seedpair(tx.c["gs"])

    def peek(self):
        return self.ev[self.i][0] if self.i < len(self.ev) else None

    def take(self, tag):
        if self.i >= len(self.ev):
            raise Mismatch("missing %s" % tag)
        t, d = self.ev[self.i]
        if t != tag:
            raise Mismatch("expected %s, log has %s %s" % (tag, t, json.dumps(d)[:200]))
        self.i += 1
        return d

    def step(self):
        self.gs = rng.step(*self.gs)
        return self.gs[0]

    def range_b(self, n):
        r, self.gs = quality.range_b(self.gs, n)
        return r


def out_ilvl(T, c, o, slot):
    if o["lvl"]:
        v = o["lvl"]
    else:
        v = 0
        if o["plvl"]:
            lv = base_of({"b": c["pb"]}).get((12, 0), 0)
            v = props.trunc_div(lv * o["plvl"], 100)
        if o["ilvl"]:
            v += props.trunc_div(slot[2] * o["ilvl"], 100)
    v1 = max(v, 1)
    return v1 if v1 < T.maxlvl else T.maxlvl


def check_cow(X, res):
    """CUBE_CowPortalOpen's tests (items/0008 section 5.1) from the logged quest words and level; the spot search and
    the portal object are oracles (their return values)."""
    c = X.tx.c
    eq("COW0 game seed", fmt(X.gs), X.take("COW0")["gs"])
    t = {}
    want = None
    while X.peek() == "COWT":
        d = X.take("COWT")
        t[d["t"]] = d["v"]
        eq("COWT %s game seed" % d["t"], fmt(X.gs), d["gs"]) if d["t"] not in ("spot", "portal", "ret") else None
        if d["t"] in ("spot", "portal"):
            X.gs = seedpair(d["gs"])                   # the oracles' draws, if any
            res.setdefault("cow_oracle_gs", []).append(d["gs"])
        if d["t"] == "ret":
            break
    # the model's verdict from the inputs
    order = ["q4_11", "p4_10"] + (["p40_0"] if c["exp"] else ["p26_0"]) + ["room", "level", "spot", "portal", "ret"]
    if t.get("q4_11"):
        want = ("game quest word 4 bit 11 set (one cow portal per game)", 0, ["q4_11"])
    elif t.get("p4_10"):
        want = ("player quest word 4 bit 10 set", 0, ["q4_11", "p4_10"])
    elif not t.get("p40_0" if c["exp"] else "p26_0"):
        want = ("player quest word %s bit 0 clear" % ("40" if c["exp"] else "26"), 0, order[:3])
    elif not t.get("room"):
        want = ("no room", 0, order[:4])
    elif t.get("level") != 1:
        want = ("not in level 1 (level %s)" % t.get("level"), 0, order[:5])
    elif not t["spot"][0]:
        want = ("no free spot (oracle)", 0, order[:6])
    elif not t.get("portal"):
        want = ("portal object not created (oracle)", 0, order[:7])
    else:
        want = ("opened", 1, order[:7])
    eq("cow portal tests reached", want[2] + ["ret"], [k for k in order if k in t])
    eq("cow portal result", want[1], t["ret"])
    res["cow"] = want[0]
    return want[1]


def check_created(X, r, s, o, slot, res, made):
    T, S = X.T, X.S
    c = X.tx.c
    il = out_ilvl(T, c, o, slot)
    q = o["q"]
    row1 = o["row1"]
    if o["kind"] == 0xFF:
        cls = slot[1]
        if o["flags"] & 0x40:
            raise Mismatch("reg not modelled (no stock row)")
    elif o["kind"] == 0xFC:
        cls = o["index"]
    else:
        cls = pick_type(X, il, o["index"])
    rfl = (0x10 if (o["flags"] & 2 and o["qty"] == 0) else 0x08) | (0x04 if o["flags"] & 4 else 0x02)
    d = X.take("CREC")
    for k, v in (("s", s), ("ilvl", il), ("idx", cls), ("k18", 4), ("w28", 1), ("ver", c["iver"]), ("q", q),
                 ("row1", row1), ("pre", o["pre"]), ("suf", o["suf"]), ("rfl", rfl), ("src", c["player"])):
        eq("creation record %s" % k, v, d[k])
    eq("game seed at ItemCreate", fmt(X.gs), d["gs"])
    lo = X.step()
    useed = (lo, 666)
    start = X.step()
    # ItemInitStats and ItemCreateByQuality
    iis0 = X.take("IIS0")
    eq("unit seed (SUnitCreate: init(step(game seed)))", fmt(useed), iis0["useed"])
    eq("start seed (ItemSeedInit: the next game-seed step)", start, iis0["start"])
    eq("item seed at ItemInitStats", fmt((start, 666)), iis0["iseed"])
    iis1 = X.take("IIS1")
    props.check_iis(T.P, iis0, iis1, S)
    S["ItemInitStats (created)"] += 1
    blk, X.i = split_until(X.ev, X.i, ("LX",))
    if blk[0][0] != "IC0":
        raise Mismatch("expected IC0 after ItemInitStats, log has %s" % blk[0][0])
    ic = blk[0][1]
    eq("IC0 item seed = {start, 666}", fmt((start, 666)), ic["seed"])
    uniques.CREATE_ROLL = lambda ic_, seed: create_roll(T, ic_, seed)
    uniques.CRAFTED = True
    r_ic = props.check_ic(T.P, blk, made, collections.Counter(), None, X.pdt, S, iis1=iis1)
    if "skip" in r_ic:
        raise Mismatch("ItemCreateByQuality skipped: %s" % r_ic["skip"])
    items_chain.check_creation(T.A, blk, S, forced=(o["pre"], o["suf"]))
    res["q"] = r_ic.get("final")
    if "create_roll" in r_ic:
        S["creation roll (record quality 0) -> %d" % r_ic["create_roll"]] += 1
    st = r_ic.get("state")
    if st is None and r_ic.get("steps") == ["normal"] and not r_ic.get("segs") and r_ic.get("final") == 2:
        # a failed low (or magic/rare without an ItemApplyProps call) then the normal fallback: no stat was written
        # since ItemInitStats, so the state is its base entries (props.py tracks only fallback-free builds)
        st = props.Item(T.P, cls, 2, ic["ilvl"], ic["ver"], ic["fl"],
                        {(x[0], x[1]): x[2] for x in (iis1.get("b") or [])}, [], ic["seed"])
        X.S["state after a fallback to normal with no property call"] += 1
    if st is None:
        raise Mismatch("the item state after ItemCreateByQuality is not tracked (%s)" % r_ic.get("final"))
    x = X.take("CRECX")
    it = x["it"]
    eq("game seed after ItemCreate (two steps)", fmt(X.gs), x["gs"])
    eq("created class", cls, it["cls"])
    icx = [d_ for t_, d_ in blk if t_ == "ICX"][-1]
    eq("created item seed (ICX)", icx["seed"], it["seed"])
    eq("created base entries", sorted(st.base.items()), sorted(base_of(it).items()))
    eq("created lists", props.norm_subs(st), norm(subs_of(it)))
    st.seed = props.Seed(it["seed"])
    st.flags = it["fl"]
    res["created"] = dict(cls=cls, q=it["q"], ilvl=il, p=it["p"], s=it["s"], rn=it["rn"], fl=it["fl"])
    return st, it


def pick_type(X, ilvl, typ):
    """sub_00565930_CubePickItemOfType (0x00565930, re-read for plan 0030 Phase 2): start = RNG_RangeB(game seed, the
    item count); scan upward from start with wrap-around, stopping at start - 1 (or at the last record when start is
    0), which is never examined, collecting at most 256 records that are of the type (ITEMS_IsType), `spawnable`, of
    `version` < 100 or in a game of item version >= 100, and of `level` <= ilvl; none: record 0 with no second draw;
    else RNG_RangeB(game seed, count) picks one."""
    T, c = X.T, X.tx.c
    d = X.take("CPT0")
    eq("CubePickItemOfType ilvl", ilvl, d["ilvl"])
    eq("CubePickItemOfType type", typ, d["type"])
    eq("game seed at CubePickItemOfType", fmt(X.gs), d["gs"])
    n = len(T.P.items)
    start = X.range_b(n)
    stop = start - 1 if start - 1 >= 0 else n - 1
    cands = []
    i = start
    while i != stop and len(cands) < 256:
        raw = T.raw(i)
        if (T.A.is_type(i, typ) and raw[0x133] and (u16(raw, 0xF6) < 100 or c["iver"] >= 100)
                and raw[0xFD] <= ilvl):
            cands.append(i)
        i += 1
        if i >= n:
            i = 0
    cls = cands[X.range_b(len(cands))] if cands else 0
    x = X.take("CPTX")
    eq("CubePickItemOfType class", cls, x["cls"])
    eq("game seed after CubePickItemOfType", fmt(X.gs), x["gs"])
    X.S["CubePickItemOfType: candidates %d" % len(cands)] += 1
    return cls


def check_copy(X, slot, at, res):
    """sub_0055A2A0_ItemCopy (serialise, then sub_00558CB0_ItemCreateFromSave): its seeds predicted, its contents compared.
    Its game-seed use is SUnitCreate's and ItemSeedInit's two steps, as a created item's: the copy's start seed and
    item seed {start, 666} are the second step's low word; its unit seed comes back from the stream (the source's
    Unit+0x28, re-initialised: init(seed28)); its class, quality, file index, ilvl, affixes, rare names, flags and
    lists are the source's."""
    c = X.tx.c
    src = {it["u"]: it for it in c["items"]}.get(slot[0])
    if src is None:
        raise Mismatch("ItemCopy source %s not a cube item" % slot[0])
    d = X.take("CCP0")
    eq("ItemCopy call", at, d["at"])
    eq("ItemCopy source (slot unit)", slot[0], d["src"])
    eq("game seed at ItemCopy", fmt(X.gs), d["gs"])
    X.step()
    start = X.step()
    x = X.take("CCPX")
    cp = x["it"]
    eq("game seed after ItemCopy (two steps)", fmt(X.gs), x["gs"])
    eq("copy start seed (the second game-seed step)", start, cp["start"])
    eq("copy item seed {start, 666}", fmt((start, 666)), cp["seed"])
    s28 = src.get("seed28")
    if s28 is None:
        if seedpair(src["useed"])[1] != 666:
            raise Mismatch("source unit seed stepped and no seed28 logged")
        s28 = seedpair(src["useed"])[0]
    eq("copy unit seed init(source Unit+0x28)", fmt((s28, 666)), cp["useed"])
    for key in ("cls", "q", "fi", "ilvl", "ver", "p", "s", "rn", "auto"):
        eq("copy %s = input's" % key, src[key], cp[key])
    eq("copy flags = input's", src["fl"], cp["fl"])
    eq("copy base entries = input's", sorted(base_of(src).items()), sorted(base_of(cp).items()))
    eq("copy lists = input's", norm(subs_of(src)), norm(subs_of(cp)))
    X.S["ItemCopy (%s)" % at] += 1
    return src, cp


def check_mod(X, o, sl, cp, res):
    """A `mod` output (0x00565DC4-0x00565E3F): the copy's class becomes the slot's (upgraded) class, or 0 when that is
    -1, then sub_00557AB0_ItemInitStats(game, &copy, 0, 0) re-runs the base stats on the copy's unit seed."""
    T = X.T
    k = o["kind"]
    if k == 0xFE:
        cls = max(sl[1], 0)
    elif k == 0xFF:
        cls = sl[1]
    elif k == 0xFC:
        cls = o["index"]
    elif k == 0xFD:
        cls = pick_type(X, out_ilvl(T, X.tx.c, o, sl), o["index"])
    else:
        cls = 0
    a = X.take("IIS0")
    eq("ItemInitStats on the copy: class", cls, a["cls"])
    eq("ItemInitStats on the copy: unit seed", cp["useed"], a["useed"])
    eq("ItemInitStats on the copy: no record", 0, a["rec"])
    b = X.take("IIS1")
    stats, gfx, kind, useed = props.init_stats(T.P, cls, cp["useed"], 0, 0, False)
    eq("unit seed after ItemInitStats (copy)", str(useed), b["useed"])
    base = dict(base_of(cp))
    for key in list(base):
        pass
    want = dict(base)
    # the stats ItemInitStats writes replace the copy's, the others stay
    written = {(21, 0), (22, 0), (23, 0), (24, 0), (159, 0), (160, 0), (72, 0), (73, 0), (31, 0), (20, 0), (67, 0),
               (68, 0), (70, 0), (14, 0)}
    for key in written:
        want.pop(key, None)
    want.update(stats)
    got = {(x[0], x[1]): x[2] for x in (b["b"] or [])}
    eq("base entries after ItemInitStats (copy)", sorted(want.items()), sorted(got.items()))
    if gfx is not None:
        eq("picture after ItemInitStats (copy)", gfx, b["gfx"])
    X.S["mod: ItemInitStats on the copy (%s)" % kind] += 1
    it = dict(cp, cls=cls, useed=b["useed"], b=b["b"])
    st = state_of(X.T, it)
    res["mod"] = dict(src_cls=cp["cls"], cls=cls)
    return st, it


def apply_mods(X, o, st, it, res):
    """The mod lines (0x005661C8-0x00566283): chance 1..99 draws on the unit seed (no stock row), then CubeModApply:
    PROP_ApplyBlockByVersion(7, item, line, state 0, flags 0x40), then ITEMS_MakeEthereal again on an ethereal item."""
    T = X.T
    lines = []
    for m in o["mods"]:
        if m["prop"] < 0:
            continue
        if 1 <= m["chance"] <= 99:
            raise Mismatch("mod chance not modelled (no stock row)")
        blk = [m["prop"], m["par"], m["min"], m["max"]]
        d = X.take("CMOD")
        eq("mod line", blk, d["line"])
        eq("item seed at CubeModApply", str(st.seed), d["it"]["seed"])
        eq("base entries at CubeModApply", sorted(st.base.items()), sorted(base_of(d["it"]).items()))
        eq("lists at CubeModApply", props.norm_subs(st), norm(subs_of(d["it"])))
        ev = []
        while X.peek() in ("SLOT", "SLOTR", "ROLL", "ROLLR", "WR", "EVD"):
            ev.append((X.peek(), X.take(X.peek())))
        R = props.Roller(T.P, st, 7, [e["v"] for t_, e in ev if t_ == "EVD"], X.pdt)
        R.run([(blk, 0, 0x40, False)])
        props.compare_events(R.ev, ev, "mod line %s" % blk)
        if st.flags & 0x400000:
            props.make_ethereal(st)
            X.S["mod line on an ethereal item: MakeEthereal again"] += 1
        x = X.take("CMODX")
        eq("item seed after CubeModApply", str(st.seed), x["it"]["seed"])
        eq("base entries after CubeModApply", sorted(st.base.items()), sorted(base_of(x["it"]).items()))
        eq("lists after CubeModApply", props.norm_subs(st), norm(subs_of(x["it"])))
        eq("flags after CubeModApply", st.flags, x["it"]["fl"])
        lines.append((blk, [e["v"] for t_, e in R.ev if t_ == "ROLLR"]))
        if any(t_ == "SLOT" and e["func"] == 14 for t_, e in R.ev):
            b_ = T.P.base(st.cls)
            rolled = [e["v"] for t_, e in R.ev if t_ == "ROLLR"]
            X.notes["sock mod line: base, ilvl, roll min..max -> value, sockets, ItemMaxSockets, size cap"].append(
                "%s ilvl %d %d..%d -> %s, %d, %d, %d" % (b_["code"], st.ilvl, blk[2], blk[3], rolled[0] if rolled else "-",
                                                        st.get_base(194), T.P.max_sockets(st.cls, st.ilvl),
                                                        min(6, b_["invw"] * b_["invh"])))
        X.S["mod lines"] += 1
        X.S["mod line func %s" % ",".join(str(e["func"]) for t_, e in R.ev if t_ == "SLOT")] += 1
    res["mods"] = lines


def finish_output(X, o, st, it, res):
    """rep, rch, qty and sock= (0x00566289-0x005663E3)."""
    T = X.T
    cls = it["cls"]
    raw = T.raw(cls)
    if o["flags"] & 0x200:
        # rep: a stackable base's quantity, then a broken item's repair, else base stat 72 raised to the evaluated 73
        if raw[0x132] and o["qty"]:
            raise Mismatch("rep on a stackable output not modelled (no session)")
        if st.flags & 0x100:
            raise Mismatch("rep of a broken item (sub_0055F900_ItemRepairBroken) not modelled (no session)")
        e73 = st.eval_maxdur()
        if st.get_base(72) < e73:
            st.set_base(72, e73)
            X.S["rep: durability raised"] += 1
        else:
            X.S["rep: durability already full"] += 1
    if o["flags"] & 0x400:
        # rch: sub_0055FE80_ItemRefillCharges, every stat 204 entry's charges raised to its maximum
        n = 0
        for L in [st.base] + [e for _, _, e in st.subs]:
            for (stat, par), v in list(L.items()):
                if stat == 204 and (v & 0xFF) < (v >> 8):         # as tools/sockets.py's refill
                    L[(stat, par)] = (v & ~0xFF) | (v >> 8)
                    n += 1
        X.S["rch: charge entries refilled %d" % n] += 1
    if o["flags"] & 2:
        if o["qty"]:
            if st.get_base(194) == 0 and not st.flags & 0x800:
                n = T.P.max_sockets(cls, it["ilvl"])
                n = min(n, o["qty"])
                qq = it["q"]
                if qq in (4, 9):
                    n = min(n, 3)
                elif qq in (5, 6, 7, 8):
                    n = min(n, 1)
                if n > 0:
                    d = X.take("CSOCK")
                    eq("sock= count", n, d["n"])
                    st.flags |= 0x800                         # ITEMS_SetFlag(0x800) before the call
                    final = set_sockets(T, st, cls, it, n)
                    res["sock="] = (o["qty"], n, final)
                    X.S["sock= sockets set"] += 1
    elif o["qty"] and raw[0x132]:
        raise Mismatch("qty= on a stackable output not modelled yet")


def set_sockets(T, st, cls, it, n):
    """ITEMS_SetSockets (items/0007 section 7): the cap is min(invwidth x invheight, 6), then the quality clamp (magic 4,
    rare 2, crafted and 9 3; set and unique: a current count replaces the request, else 1), then ItemMaxSockets; the
    count max(n, 1) below the cap, else the cap; nothing when the cap is 0. Returns the count written (0: none)."""
    b = T.P.base(cls)
    cap = min(b["invw"] * b["invh"], 6)
    if cap == 0:
        return 0
    q = it["q"]
    if q == 4:
        cap = min(cap, 4)
    elif q in (5, 7):
        cur = st.eval_stat(194)
        if cur >= 1:
            n = cur
        elif cap:
            cap = 1
    elif q == 6:
        cap = min(cap, 2)
    elif q in (8, 9):
        cap = min(cap, 3)
    cap = min(cap, T.P.max_sockets(cls, it["ilvl"]))
    r = max(n, 1) if max(n, 1) < cap else cap
    if r < 1:
        return 0
    st.flags |= 0x800
    st.set_base(194, r)
    return r


def check_tx(T, tx, S, notes, pdt, made):
    X = Ctx(T, tx, S, notes, pdt)
    c = tx.c
    res = dict(n=len(c["items"]), items=[it["cls"] for it in c["items"]], game="exp" if c["exp"] else "classic",
               diff=c["diff"])
    reached, row, slots = match(T, c)
    logged = []
    while X.peek() in ("CMI", "CMIR"):
        d = X.take("CMI")
        logged.append((d["row"], X.take("CMIR")["r"]))
    eq("rows reaching the matcher (row, result)", reached, logged)
    res["row"] = row
    res["reached"] = [i for i, _ in reached]
    if row is None:
        x = X.take("CUBX")
        eq("game seed unchanged (no row)", fmt(X.gs), x["gs"])
        eq("cube unchanged (no row)", [(it["u"], it["cls"], it["seed"]) for it in c["items"]],
           [(it["u"], it["cls"], it["seed"]) for it in x["items"]])
        return res
    d = X.take("CROW")
    eq("matched row", row, d["row"])
    eq("slots", [v for sl in slots for v in sl], d["slots"])
    r = T.rows[row]
    produced = False
    outs = []
    for s in range(3):
        o = r["outs"][s]
        sl = slots[s]
        ores = dict(kind=KIND.get(o["kind"], o["kind"]))
        strip = bool(o["flags"] & 0x30)
        if 1 <= o["kind"] <= 3:
            d = X.take("CPORT")
            eq("special output index", s, d["s"])
            eq("special output kind", o["kind"], d["kind"])
            eq("game seed at the special output", fmt(X.gs), d["gs"])
            if o["kind"] == 1:
                rv = check_cow(X, ores)
            else:
                d = X.take("PAN")
                eq("Pandemonium handler", o["kind"], d["k"])
                rv = 0
            d = X.take("CPORTR")
            eq("special output result", rv, d["r"])
            X.gs = seedpair(d["gs"]) if o["kind"] == 1 else X.gs
            eq("game seed after the special output", fmt(X.gs), d["gs"])
            produced |= bool(rv)
            ores["result"] = rv
            outs.append(ores)
            continue
        if o["kind"] == 0:
            continue
        if strip:
            raise Mismatch("uns/rem not modelled yet")
        if not o["flags"] & 1:
            if o["kind"] == 0xFE:
                src, cp = check_copy(X, sl, "useitem", ores)
                if o["q"] == 9:
                    raise Mismatch("tmp output not modelled (disabled rows only)")
                st, it = state_of(T, cp), cp
            else:
                st, it = check_created(X, r, s, o, sl, ores, made)
        else:
            src, cp = check_copy(X, sl, "mod", ores)
            st, it = check_mod(X, o, sl, cp, ores)
        apply_mods(X, o, st, it, ores)
        finish_output(X, o, st, it, ores)
        outs.append((ores, st, it))
        produced = True
    res["outs"] = [x if isinstance(x, dict) else x[0] for x in outs]
    if not produced:
        x = X.take("ROCX")
        eq("game seed at the return (nothing produced)", fmt(X.gs), x["gs"])
        x = X.take("CUBX")
        eq("cube unchanged (nothing produced)", [(it["u"], it["cls"]) for it in c["items"]],
           [(it["u"], it["cls"]) for it in x["items"]])
        res["produced"] = False
        return res
    d = X.take("CDES")
    eq("game seed at the destroy", fmt(X.gs), d["gs"])
    placed = []
    for x in outs:
        if isinstance(x, dict):
            continue
        ores, st, it = x
        d = X.take("CPL")
        p = d["it"]
        eq("placed unit", it["u"], p["u"])
        eq("placed item seed", str(st.seed), p["seed"])
        eq("placed base entries", sorted(st.base.items()), sorted(base_of(p).items()))
        eq("placed lists", props.norm_subs(st), norm(subs_of(p)))
        eq("placed flags", st.flags, p["fl"])
        r_ = X.take("CPLR")
        if not r_["r"]:
            raise Mismatch("placement failed (InvPlaceItem oracle 0)")
        placed.append((p, st.flags | 0x10))
    x = X.take("ROCX")
    eq("game seed at the return", fmt(X.gs), x["gs"])
    x = X.take("CUBX")
    eq("game seed at CUBX", fmt(X.gs), x["gs"])
    eq("cube after: the outputs only", [(p["u"], p["cls"], fl) for p, fl in placed],
       [(it["u"], it["cls"], it["fl"]) for it in x["items"]])
    res["produced"] = True
    return res


# ---------------------------------------------------------------- driver

def cmd_check(ns):
    T = Tables(ns.excel)
    affixes.PROPS_HOOK = items_chain.make_hook(T.P)     # the affix model's ItemApplyProps seeds from tools/props.py
    S = collections.Counter()
    notes = collections.defaultdict(list)
    ok = bad = 0
    by_row = collections.Counter()
    by_kind = collections.Counter()
    for path in ns.logs:
        made = set()
        pdt = (0, 0)
        for line in open(path, errors="replace"):
            if line.startswith("PDT "):
                d = json.loads(line.split(" ", 1)[1])
                pdt = (d["c6c"], d["c70"])
                break
        n = 0
        for tx in read_log(path):
            n += 1
            try:
                r = check_tx(T, tx, S, notes, pdt, made)
            except (Mismatch, affixes.Mismatch, KeyError, IndexError, TypeError, ValueError) as e:
                bad += 1
                print("FAIL %s transmute %d (items %s): %s" % (os.path.basename(path), n,
                                                              [it["cls"] for it in tx.c["items"]], e))
                continue
            ok += 1
            by_row["none" if r["row"] is None else r["row"]] += 1
            for o in r.get("outs", []):
                by_kind["%s%s" % (o["kind"], " q%s" % o["q"] if o.get("q") else "")] += 1
            if ns.verbose:
                print("ok   %s %d: %s" % (os.path.basename(path), n, json.dumps(r)[:400]))
    print("%d transmutes reproduced, %d failed" % (ok, bad))
    print("rows: %s" % ", ".join("%s:%d" % kv for kv in sorted(by_row.items(), key=lambda kv: str(kv[0]))))
    print("outputs: %s" % ", ".join("%s %d" % kv for kv in sorted(by_kind.items())))
    for k in sorted(S):
        print("  %-66s %d" % (k, S[k]))
    for k in sorted(notes):
        vals = collections.Counter(notes[k])
        print("-- %s:" % k)
        for v, n in sorted(vals.items()):
            print("     %s%s" % (v, " (x%d)" % n if n > 1 else ""))
    return 0 if bad == 0 and ok else 1


def main(argv):
    ap = argparse.ArgumentParser(prog="cube.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("logs", nargs="+")
    p.add_argument("--excel", default=EXCEL)
    p.add_argument("-v", "--verbose", action="store_true")
    ns = ap.parse_args(argv[1:])
    return cmd_check(ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
