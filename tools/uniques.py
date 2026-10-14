#!/usr/bin/env python3
"""Unique and set selection model (plan 0019 Phase 2), checked against tools/gdb/uniques.gdb logs.

    python3 -I tools/uniques.py check <log> [<log> ...] [--excel DIR] [-v]
    python3 -I tools/uniques.py survey [--excel DIR]

Model of sub_00557450_ItemCreateByQuality as read in docs/findings/items/0004-uniques-sets.md, from its entry (IC0)
to the join after the builder chain (ICJ):
  - the quality: the record's quality (+0x30; a drop never reaches the creation-side roll's drawing body), then the
    four pre-switch overrides in their order (ItemTypes Magic: quest base -> 7, else 4 unless already 4..9;
    ItemTypes Rare = 0 and 6 -> 4; base `unique` -> 7; ItemTypes Normal (or no type record) -> 2), checked at ICQ;
  - quality 7, ITEMS_BuildUnique: the candidate filter in table order (version >= 100 needs item version >= 100;
    enabled; code; ladder only with Game+0x6A or +0x74 set; (int16) lvl <= max(1, ilvl)), weight max(1, rarity),
    the TC-named row (record +0x40 - 1) taken with no draw when it is a candidate, else one RNG_RangeOffset(0,
    total) draw on the item seed and the first candidate whose cumulative weight exceeds it; the made-uniques set of
    the game (tracked by the model from its own successful builds since the last GAME line, unless nolimit) tested
    after the pick (a quest base skips it); no candidate: success with no row if the base has `unique`, else fail;
  - quality 5, ITEMS_BuildSetPick: version (the set's, copied at load), (int16) lvl <= ilvl, code, set 29 only with
    record flag bit 0; weight rarity or 1 when 0; forced row; one RNG_RangeB(total) draw; subtract walk;
  - a failure: the durability step (ItemHasDurability from the base's nodurability/durability; the item version >= 1;
    stat 72 and 73 times 3 (unique) or 2 (set), each capped at 255; the two stat values are inputs, logged), then
    the fallback chain unique -> rare -> magic -> superior -> normal and set -> magic -> superior -> normal; every
    step reseeds the item seed to {S, 666} (S = the seed's low word before the failed builder) and writes the step's
    quality to the item and the record; the other qualities' chains (6, 4, 3, 1) the same way.
ADR-0004 boundary oracles (architect ruling, plan 0019 Phase 1): sub_0065FEC0_ItemApplyProps (unique mode 3, set
mode 4) and the rare, magic, superior, low and normal builders. At each oracle entry the model asserts the item seed
(PROPS, BLD), then takes the oracle's exit seed and result from the log: a builder's result is read from what follows
it (another FB step means it failed), its exit seed from BRET or ICJ. The ethereal, socket and automagic steps after
the join are outside the model (ICX is only compared on quality and file index).
Plan 0024 Phase 2: tools/props.py sets PROPS_MODEL (its model of ItemApplyProps' item-seed use), which replaces the
PROPS -> BRET seed oracle of a successful unique or set build with a predicted seed (`props.py check` / `rerun`).

Asserted per creation: ICQ quality; BLD entry seed of every builder; UMADE (the game's made bits at the unique
builder's entry) against the model's set; UPK/SPK candidate lists, totals and forced rows; UR/SR draw and seed; the
row (UPK/SROW) and the made bit; PROPS entry seed; BRET result and file index; every DUR value; every FB S value;
ICJ seed (= the last oracle's exit seed), quality, record quality and file index; ICX quality and file index. Also
the drop chain: IC0's record quality and row equal the CPRE line's q and uidx (the quality from tools/quality.py's
roll, or the TC's forced quality), and IC0's seed is {start, 666} (items/0004 section 1).

survey prints the stock rows behind the reachability statements of the Phase 2 record: the TreasureClassEx cells
that name a UniqueItems or SetItems row, the item types with Magic, Rare = 0 or Normal, the bases with `unique` or
`quest`, and the UniqueItems rows with the ladder bit.

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

EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
M32 = 0xFFFFFFFF
QN = {1: "low", 2: "normal", 3: "superior", 4: "magic", 5: "set", 6: "rare", 7: "unique", 8: "crafted", 9: "q9"}
CHAIN = {7: ["rare", "magic", "superior", "normal"], 5: ["magic", "superior", "normal"],
         6: ["magic", "superior", "normal"], 4: ["superior", "normal"], 3: ["normal"], 1: ["normal"]}
STEPQ = {"rare": 6, "magic": 4, "superior": 3, "normal": 2}
FIRST = {6: "rare", 4: "magic", 3: "superior", 1: "low", 2: "normalcase"}
# Optional model of ItemApplyProps' item-seed use (tools/props.py sets it): f(mode, file index, seed, IC0 dict) ->
# the seed after the call. When set, the PROPS -> BRET seed is predicted instead of read from the log.
PROPS_MODEL = None


def recs(excel, table):
    r, _ = excel_bin.read_bin(excel_bin.find_file(excel, table, ".bin"))
    return r


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


class Tables:
    def __init__(self, excel):
        self.items = []
        for t in ("weapons", "armor", "misc"):
            self.items.extend(recs(excel, t))
        self.itypes = recs(excel, "itemtypes")
        self.uniq = [dict(ver=u16(r, 0x24), code=r[0x28:0x2C], flags=r[0x2C], rarity=s32(r, 0x30), lvl=s16(r, 0x34),
                          name=r[2:34].split(b"\0")[0].decode("latin1")) for r in recs(excel, "uniqueitems")]
        sets = recs(excel, "sets")
        members = [0] * len(sets)
        self.setit = []
        for r in recs(excel, "setitems"):
            st = u16(r, 0x2C)
            sver = 0
            if 0 <= st < len(sets) and members[st] < 6:          # sub_00634DC0_LoadSetTables
                sver = u16(sets[st], 4)
                members[st] += 1
            self.setit.append(dict(code=r[0x28:0x2C], set=st, lvl=s16(r, 0x30), rarity=s32(r, 0x34), sver=sver,
                                   name=r[2:34].split(b"\0")[0].decode("latin1")))

    def base(self, cls):
        r = self.items[cls]
        return dict(code=r[0x80:0x84], type=s16(r, 0x11E), unique=r[0x129], quest=r[0x12A], dur=r[0x112],
                    nodur=r[0x113], name=r[0x80:0x84].decode("latin1").strip())

    def tflag(self, typ, off, missing):
        if typ < 0 or typ >= len(self.itypes):
            return missing
        return self.itypes[typ][off]


class Mismatch(Exception):
    pass


def overrides(T, cls, q):
    """The pre-switch overrides (items/0004 section 2): (quality, list of the rules that wrote it)."""
    b = T.base(cls)
    fired = []
    if T.tflag(b["type"], 0x14, 0):
        if b["quest"]:
            q = 7
            fired.append("magic-type-quest:7")
        elif not 4 <= q <= 9:
            q = 4
            fired.append("magic-type:4")
    if not T.tflag(b["type"], 0x15, 0) and q == 6:
        q = 4
        fired.append("not-rare-type:4")
    if b["unique"]:
        q = 7
        fired.append("base-unique:7")
    if T.tflag(b["type"], 0x16, 1):
        q = 2
        fired.append("normal-type:2")
    return q, fired


def unique_cands(T, b, ic):
    ilvl = max(1, ic["ilvl"])
    out, total = [], 0
    for row, u in enumerate(T.uniq):
        if u["ver"] >= 100 and ic["ver"] < 100:
            continue
        if not u["flags"] & 1:
            continue
        if u["code"] != b["code"]:
            continue
        if not ic["g6a"] and not ic["ladder"] and u["flags"] & 8:
            continue
        if u["lvl"] > ilvl:
            continue
        out.append([row, total])
        total += max(1, u["rarity"])
    return out, total


def set_cands(T, b, ic):
    ilvl = max(1, ic["ilvl"])
    out, total = [], 0
    for row, s in enumerate(T.setit):
        if s["sver"] >= 100 and ic["ver"] < 100:
            continue
        if s["lvl"] > ilvl:
            continue
        if s["code"] != b["code"]:
            continue
        if s["set"] == 29 and not ic["rfl"] & 1:
            continue
        w = s["rarity"] if s["rarity"] else 1
        out.append([row, w])
        total += w
    return out, total


def has_dur(b):
    return b["nodur"] == 0 and b["dur"] > 0


class Block:
    """The lines of one ItemCreateByQuality call (IC0 .. ICX), consumed in order."""

    def __init__(self, ev):
        self.ev, self.i = ev, 0

    def peek(self):
        return self.ev[self.i][0] if self.i < len(self.ev) else None

    def take(self, tag):
        if self.i >= len(self.ev):
            raise Mismatch("missing %s" % tag)
        t, d = self.ev[self.i]
        if t != tag:
            raise Mismatch("expected %s, log has %s %s" % (tag, t, d))
        self.i += 1
        return d


def eq(what, model, logged):
    if model != logged:
        raise Mismatch("%s: model %r, log %r" % (what, model, logged))


def check_block(T, ev, made, stats, cpre, verbose=False):
    """One creation. made: the model's made-uniques set for the current game (updated). Returns a summary dict."""
    B = Block(ev)
    ic = B.take("IC0")
    b = T.base(ic["cls"])
    res = dict(cls=ic["cls"], base=b["name"], ilvl=ic["ilvl"], ver=ic["ver"], diff=ic["diff"], exp=ic["exp"],
               rq=ic["rq"], steps=[], drop=cpre is not None)
    seed = seedpair(ic["seed"])
    if cpre is not None:
        eq("IC0 record quality vs CPRE q", int(cpre["q"]), ic["rq"])
        eq("IC0 record row vs CPRE uidx", int(cpre["uidx"]), ic["rrow"])
        if seed == (ic["start"], 666):
            stats["seed_is_start"] += 1
        else:
            stats["seed_not_start"] += 1
    if ic["rest"] or ic["ver"] == 0 or ic["rq"] == 0:
        stats["skipped"] += 1
        res["skip"] = "restore %d, version %d, record quality %d (not a drop path)" % (ic["rest"], ic["ver"], ic["rq"])
        return res
    q, fired = overrides(T, ic["cls"], ic["rq"])
    res["fired"] = ["%s (record quality %d%s)" % (f, ic["rq"], ", changed" if q != ic["rq"] else "")
                    for f in fired]
    d = B.take("ICQ")
    eq("quality after the overrides (ICQ)", q, d["q"])
    eq("item quality at the switch", q, d["iq"])
    res["q"] = q
    S = seed[0]
    cur = seed
    chain = []

    def builder_entry(kind, cur, qq, rqq, fi=None):
        d = B.take("BLD")
        eq("builder", kind, d["k"])
        eq("%s entry seed" % kind, fmt(cur), d["seed"])
        if qq is not None:
            eq("%s item quality" % kind, qq, d["q"])
        if rqq is not None:
            eq("%s record quality" % kind, rqq, d["rq"])
        if fi is not None:
            eq("%s file index at entry" % kind, fi, d["fi"])
        return d

    ok = None                  # result of the in-scope builder (unique / set); None for other qualities
    if q == 7:
        builder_entry("unique", cur, 7, ic["rq"], -1)
        d = B.take("UMADE")
        eq("made-uniques bits (UMADE)", sorted(made), d["rows"])
        cands, total = unique_cands(T, b, ic)
        forced = ic["rrow"] - 1 if ic["rrow"] and any(c[0] == ic["rrow"] - 1 for c in cands) else -1
        res.update(n=len(cands), total=total, cands=[c[0] for c in cands], forced=forced)
        if not cands:
            B.take("UNONE")
            ok = bool(b["unique"])
            row = -1
            res["exit"] = "no-candidate:" + ("base-unique" if ok else "fail")
        else:
            if forced < 0:
                lo, hi = rng.step(*cur)
                r = lo % total
                cur = (lo, hi)
                d = B.take("UR")
                eq("unique draw r", r, d["r"])
                eq("seed after the unique draw", fmt(cur), d["seed"])
                c = 1
                while c < len(cands) and r >= cands[c][1]:
                    c += 1
                row = cands[c - 1][0]
                res["r"] = r
            else:
                row = forced
            d = B.take("UPK")
            eq("unique candidates (row, cumBefore)", cands, d["cand"])
            eq("unique total", total, d["total"])
            eq("unique forced row", forced, d["forced"])
            eq("unique row", row, d["row"])
            eq("made bit of the row", 1 if row in made else 0, d["made"])
            eq("seed at the pick", fmt(cur), d["seed"])
            res["row"] = row
            if not b["quest"] and (row > 0x1000 or row in made):
                ok = False
                res["exit"] = "made"
            else:
                ok = True
                if not T.uniq[row]["flags"] & 2:
                    made.add(row)
                d = B.take("PROPS")
                eq("ItemApplyProps mode", 3, d["mode"])
                eq("ItemApplyProps entry seed (oracle)", fmt(cur), d["seed"])
                res["exit"] = "row"
                if PROPS_MODEL:
                    cur = PROPS_MODEL(3, row, cur, ic)
                    res["props_model"] = True
        d = B.take("BRET")
        eq("unique builder result", 1 if ok else 0, d["ret"])
        eq("file index after the unique builder", row if ok else -1, d["fi"])
        if ok and res.get("props_model"):
            eq("seed after ItemApplyProps (props model)", fmt(cur), d["seed"])
        if not ok:
            eq("seed after a failed unique build", fmt(cur), d["seed"])
        cur = seedpair(d["seed"])                         # PROPS oracle exit (or unchanged)
    elif q == 5:
        builder_entry("set", cur, 5, ic["rq"], -1)
        cands, total = set_cands(T, b, ic)
        forced = ic["rrow"] - 1 if ic["rrow"] and any(c[0] == ic["rrow"] - 1 for c in cands) else -1
        res.update(n=len(cands), total=total, cands=[c[0] for c in cands], forced=forced)
        row = -1
        if cands or B.peek() == "SPK":
            d = B.take("SPK")
            eq("set candidates (row, weight)", cands, d["cand"])
            eq("set total", total, d["total"])
            eq("set forced row", forced, d["forced"])
        if forced >= 0:
            row = forced
        elif total == 0:
            ok = False
            res["exit"] = "no-candidate"
        else:
            r, cur = rng_range_b(cur, total)
            d = B.take("SR")
            eq("set draw r", r, d["r"])
            eq("seed after the set draw", fmt(cur), d["seed"])
            res["r"] = r
            rr = r
            for c in cands:
                if rr < c[1]:
                    row = c[0]
                    break
                rr -= c[1]
            if row < 0:
                ok = False
                res["exit"] = "walk-off"
        if row >= 0:
            d = B.take("SROW")
            eq("set row", row, d["row"])
            ok = True
            res["row"] = row
            d = B.take("PROPS")
            eq("ItemApplyProps mode", 4, d["mode"])
            eq("ItemApplyProps entry seed (oracle)", fmt(cur), d["seed"])
            res["exit"] = "row"
            if PROPS_MODEL:
                cur = PROPS_MODEL(4, row, cur, ic)
                res["props_model"] = True
        d = B.take("BRET")
        eq("set builder result", 1 if ok else 0, d["ret"])
        eq("file index after the set builder", row if ok else -1, d["fi"])
        if ok and res.get("props_model"):
            eq("seed after ItemApplyProps (props model)", fmt(cur), d["seed"])
        if not ok:
            eq("seed after a failed set build", fmt(cur), d["seed"])
        cur = seedpair(d["seed"])
    elif q in FIRST:
        k = FIRST[q]
        builder_entry(k, cur, q, ic["rq"])
        if q == 2:
            builder_entry("normal", cur, 2, ic["rq"])
        chain.append(k)
    else:
        raise Mismatch("quality %d not modelled" % q)

    steps = list(CHAIN.get(q, []))
    if ok is False:
        k = 3 if q == 7 else 2
        hd = has_dur(b)
        d = B.take("DUR")
        eq("ItemHasDurability", 1 if hd else 0, d["has"])
        if hd:
            eq("item version (DUR)", ic["ver"], B.take("DUR")["ver"])
            if ic["ver"] >= 1:
                s72 = B.take("DUR")["s72"]
                s73 = B.take("DUR")["s73"]
                eq("stat 72 written", min(255, k * s72) if k * s72 < 255 else 255, B.take("DUR")["w72"])
                eq("stat 73 written", min(255, k * s73) if k * s73 < 255 else 255, B.take("DUR")["w73"])
                res["dur"] = [s72, s73]
    if ok is True:
        steps = []
    # the fallback chain: each step reseeds to {S, 666}; the previous builder failed iff an FB line follows it
    while B.peek() == "FB":
        if not steps:
            raise Mismatch("a fallback step the model does not expect")
        k = steps.pop(0)
        d = B.take("FB")
        eq("fallback step", k, d["k"])
        eq("fallback S (%s)" % k, S, d["S"])
        cur = (S, 666)
        res["steps"].append(k)
        if k == "rare" and not T.tflag(b["type"], 0x15, 0):
            # ITEMS_BuildRare returns 0 at once for a type that cannot be rare: no BLD of the rare body
            pass
        builder_entry(k, cur, STEPQ[k], STEPQ[k], -1)
    d = B.take("ICJ")
    final_q = STEPQ[res["steps"][-1]] if res["steps"] else q
    eq("quality at the join", final_q, d["q"])
    eq("record quality at the join", final_q if res["steps"] else ic["rq"], d["rq"])
    if ok:
        eq("seed at the join (after the builder)", fmt(cur), d["seed"])
        eq("file index at the join", res.get("row", -1) if q in (5, 7) else d["fi"], d["fi"])
    res["final"] = final_q
    res["join_seed"] = d["seed"]
    x = B.take("ICX")
    eq("ICX quality", d["q"], x["q"])
    eq("ICX file index", d["fi"], x["fi"])
    if B.i != len(ev):
        raise Mismatch("unconsumed lines: %s" % [t for t, _ in ev[B.i:]])
    return res


def rng_range_b(seed, n):
    if n & 0x80000000 or n == 0:
        return 0, seed
    lo, hi = rng.step(*seed)
    return (lo & (n - 1) if n & (n - 1) == 0 else lo % n), (lo, hi)


TAGS = ("IC0", "ICQ", "BLD", "UMADE", "UR", "UPK", "UNONE", "SR", "SPK", "SROW", "PROPS", "BRET", "DUR", "FB", "ICJ",
        "ICX")


def read_log(path):
    """Yield ('GAME', None) at each game, and (block, cpre) per ItemCreateByQuality call (per thread)."""
    open_ = {}
    cpre = None
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
        if tag == "IC0":
            th = d.get("th", 0)
            open_[th] = [[("IC0", d)], cpre]
            last = th
            continue
        if not open_:
            continue
        cur = open_[last]
        cur[0].append((tag, d))
        if tag == "ICX":
            yield cur[0], cur[1]
            del open_[last]


def cmd_check(ns):
    T = Tables(ns.excel)
    ok = bad = 0
    stats = collections.Counter()
    table = collections.Counter()
    notes = collections.defaultdict(list)
    for path in ns.logs:
        made = set()
        game = 0
        for blk, cpre in read_log(path):
            if blk == "GAME":
                made = set()
                game += 1
                continue
            try:
                r = check_block(T, blk, made, stats, cpre, ns.verbose)
            except (Mismatch, KeyError, IndexError) as e:
                bad += 1
                print("FAIL %s game %d IC0 %s: %s" % (os.path.basename(path), game, json.dumps(blk[0][1]), e))
                continue
            ok += 1
            if "skip" in r:
                continue
            mode = "exp" if r["ver"] >= 100 else "classic"
            dn = ("normal", "nightmare", "hell")[r["diff"]] if r["diff"] is not None else "?"
            src = "drop" if r["drop"] else "other"
            table[(r["q"], mode, dn, src, r.get("exit", "-"), "+".join(r["steps"]) or "-")] += 1
            for f in r["fired"]:
                stats["override " + f] += 1
            if r["q"] in (5, 7):
                tag = "U" if r["q"] == 7 else "S"
                if r.get("n", 0) > 1:
                    stats["%s multi-candidate builds" % tag] += 1
                    if r.get("forced", -1) < 0:
                        notes["multi"].append("%s %s %s ilvl %d %s rows %s -> %s (r %s of %s)" % (
                            tag, mode, r["base"], r["ilvl"], dn, r["cands"], r.get("row"), r.get("r"), r.get("total")))
                if r["q"] == 7:
                    lad = [c for c in r.get("cands", []) if T.uniq[c]["flags"] & 8]
                    if lad:
                        stats["U builds with a ladder row among the candidates"] += 1
                        notes["ladder"].append("%s %s ilvl %d: ladder rows %s among %s, picked %s" % (
                            dn, r["base"], r["ilvl"], lad, r["cands"], r.get("row")))
                    if r.get("exit") == "made":
                        notes["made"].append("%s %s %s: row %s already made -> %s" % (
                            mode, dn, r["base"], r.get("row"), "+".join(r["steps"])))
                    if r.get("forced", -1) >= 0 or blk[0][1]["rrow"]:
                        notes["named"].append("%s row+1 %d forced %d" % (r["base"], blk[0][1]["rrow"], r["forced"]))
                    if mode == "classic" and r["base"] in ("rin", "amu"):
                        notes["classic-jewel"].append("%s %s ilvl %d rows %s total %s r %s -> %s" % (
                            dn, r["base"], r["ilvl"], r["cands"], r.get("total"), r.get("r"), r.get("row")))
                if r.get("exit") not in ("row",):
                    notes["fail"].append("%s %s %s %s ilvl %d: %s -> %s%s" % (
                        tag, mode, dn, r["base"], r["ilvl"], r.get("exit"), "+".join(r["steps"]) or "-",
                        " dur %s" % r["dur"] if "dur" in r else ""))
    print("%d creations reproduced, %d failed" % (ok, bad))
    print("drop seeds {start, 666} at IC0: %d, not: %d; skipped (restore / version 0 / no record quality): %d" % (
        stats["seed_is_start"], stats["seed_not_start"], stats["skipped"]))
    print("builds by switch quality, mode, difficulty, source, exit, fallback steps:")
    for k, v in sorted(table.items(), key=lambda kv: (-kv[0][0], kv[0][1:])):
        print("  %-8s %-7s %-9s %-5s %-24s %-28s %d" % (QN[k[0]], k[1], k[2], k[3], k[4], k[5], v))
    for k in sorted(s for s in stats if not s.startswith("seed_") and s != "skipped"):
        print("%s: %d" % (k, stats[k]))
    for k in ("fail", "made", "multi", "ladder", "classic-jewel", "named"):
        if notes[k]:
            print("-- %s (%d)" % (k, len(notes[k])))
            for n in notes[k][: (None if ns.verbose else 40)]:
                print("   " + n)
    return 0 if bad == 0 else 1


def cmd_survey(ns):
    T = Tables(ns.excel)
    names_u = {u["name"].lower(): i for i, u in reversed(list(enumerate(T.uniq))) if u["name"]}
    names_s = {s["name"].lower(): i for i, s in reversed(list(enumerate(T.setit))) if s["name"]}
    print("== TreasureClassEx cells naming a UniqueItems or SetItems row ==")
    n = 0
    for r in recs(ns.excel, "treasureclassex"):
        tc = r[0:32].split(b"\0")[0].decode("latin1")
        if not tc:
            break
        for k in range(10):
            cell = r[0x38 + 64 * k: 0x78 + 64 * k].split(b"\0")[0].decode("latin1").replace('"', "")
            nm = cell.split(",")[0].lower()
            if nm in names_u and names_u[nm] >= 1:
                u = names_u[nm]
                print("  %-20s %-16s unique row %d (lvl %d, enabled %d)" % (tc, cell, u, T.uniq[u]["lvl"],
                                                                           T.uniq[u]["flags"] & 1))
                n += 1
            elif nm in names_s and len(nm) > 4:
                print("  %-20s %-16s set row %d" % (tc, cell, names_s[nm]))
                n += 1
    print("  cells: %d" % n)
    print("== ItemTypes overrides (records with Magic, Rare 0, Normal) ==")
    for flag, off in (("Magic", 0x14), ("Normal", 0x16)):
        print("  %s: %s" % (flag, " ".join(t[0:4].decode("latin1").strip() for t in T.itypes if t[off])))
    print("  Rare = 0 (6 -> 4 on such a type): %d types" % sum(1 for t in T.itypes if not t[0x15]))
    print("== bases with `unique` or `quest` ==")
    for i in range(len(T.items)):
        b = T.base(i)
        if b["unique"] or b["quest"]:
            print("  %4d %-4s unique %d quest %d type %d" % (i, b["name"], b["unique"], b["quest"], b["type"]))
    print("== UniqueItems rows with the ladder bit ==")
    print("  " + ", ".join("%d %s (%s, lvl %d)" % (i, u["name"], u["code"].decode("latin1").strip(), u["lvl"])
                           for i, u in enumerate(T.uniq) if u["flags"] & 8))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("logs", nargs="+")
    c.add_argument("--excel", default=EXCEL)
    c.add_argument("-v", "--verbose", action="store_true")
    s = sub.add_parser("survey")
    s.add_argument("--excel", default=EXCEL)
    ns = ap.parse_args(argv)
    return {"check": cmd_check, "survey": cmd_survey}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
