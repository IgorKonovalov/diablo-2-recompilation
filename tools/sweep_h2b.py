#!/usr/bin/env python3
"""Plan 0038 batch H2b checks (run:2026-10-20-sweep-items-chain; items/tc, affixes, uniques-sets, properties and
sockets-runewords rows).

    python3 -I tools/sweep_h2b.py logs <log> [<log> ...]     # the H2b lines of tools/gdb/items-h2b.gdb
    python3 -I tools/sweep_h2b.py static [--excel DIR]       # full-table checks behind the reclassified rows
    python3 -I tools/sweep_h2b.py rareboth [--excel DIR]     # where a rare build can fail with both sides empty

`logs` reads the lines tools/gdb/h2b.py adds, with the IC0/ICJ/ICX, CPRE/CPOST, SLOT, ROLLR, LX and BLD/FB lines of
the other loggers, and checks, per log, in order:
  seeds    each GS0 (sub_00558D90_ItemCreate entry) is followed on its thread by exactly one GS1 (after
           sub_00552E90_ItemSeedInit in SUnitCreate) and one GS2 (SUnitCreate's return): with g the game seed at GS0,
           g1 = Step(g), g2 = Step(g1): GS1 game seed = g2, unit seed = Init(g1.low) = {g1.low, 666}, Unit+0x28 =
           g1.low, item seed = {g2.low, 666}, start = g2.low; GS2 equal to GS1 in every field; GS3 (the record-seed
           branch) absent unless GS0's arg or record +0x2C is non-zero; GS4 equal to GS2 without GS3;
  create   the GQ0 of the same unit (sub_00557450_ItemCreateByQuality) carries the game seed of GS4 (no game-seed
           draw between, ItemInitStats included); GQJ (the join) and GQX (the return) carry GQ0's game seed and unit
           seed (neither is stepped in ItemCreateByQuality), except that after the low builder (BLD low) the unit
           seed may be one step on (its durability draw, items/affixes G2, an oracle of items/uniques-sets);
  drops    each CPRE..CPOST pair (sub_0055A550_DropCreateItem around the TC resolver's creation call) holds exactly
           one GS0, with return address 0x0055A6B4, arg 0, record +0x2C 0 and the record's item index = CPRE's item,
           when CPOST names a unit, and CPOST's source seed equal to CPRE's;
  sockets  each ITEMS_SetSockets call (SS0 .. SSR): p = invwidth x invheight of the item's record (> 0 unless the
           call returns at once), cap = min(p, 6) at SSP; SSQ: quality 4 -> min(cap, 4), 6 -> min(cap, 2), 8 and 9 ->
           min(cap, 3), 1-3 (and no item data) -> unchanged with n unchanged, 5 and 7 not modelled (reported);
           SSM's ItemMaxSockets = the items/properties F5 value (gemsockets, MaxSock1/25/40 by ilvl from the open
           IC0 of the item); SSN cap = min(cap, maxs); SSW v = min(max(n, 1), cap), absent when that is < 1;
           counts which clamp decided the written value;
  builders MB0/MBF: ITEMS_BuildMagic fails (MBF) exactly when both slot ids are 0; RNE: a name scan with n = 0
           draws nothing (the next RNE of the same build, the second name scan, carries the same item seed); RBF counted per cause;
  classic  per classic creation of a stackable or Throwable weapon base (items/affixes C5a, R1), the builders entered
           (BLD) and the fallback helpers (FB) in order, and the quality at the join;
  tors     classic body armour (type 3) at qualities 2-3: SOK0 followed by no SOKR draw, and whether the case
           reached the tors test (SOKM with ItemMaxSockets > 0); control: expansion body armour past SOKM > 0 draws;
  dur      superior ethereal creations with a func-13 slot: stat 73 h, the dur% roll d, stat 72; the code's order
           h + floor(h d / 100) and the other order floor((h - 1)(100 + d) / 100) + 1, and whether they differ;
  carriers the func 12, 23 and 24 slots of stock creations (plan 0038 inventory § 6, H2c).
`rareboth`: the rare-able bases, item versions and ilvls where both rare names exist and both affix sides are empty
  (the only way to items/affixes E5), by tools/affixes.py survey's loop.
`static`: the elixir type (11) against every way a stock item is made (TreasureClassEx cells and type groups,
  cubemain outputs, the vendor columns of misc.txt, the item's spawnable and quest cells), and the bases whose
  ItemMaxSockets can exceed min(6, invwidth x invheight) at some ilvl (the only clamp the drop roll can meet).
Exit 0 only when no check fails. Stdlib only. Read-only.
"""
import argparse
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng  # noqa: E402

EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")


def sp(s):
    a, b = s.split(":")
    return int(a, 16), int(b, 16)


def fmt(t):
    return "%08x:%08x" % t


def table(excel, name):
    with open(os.path.join(excel, name + ".txt"), errors="replace", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


class Items:
    """Item records in the game's order (weapons, armor, misc) and item types in .bin order (Expansion row out)."""

    def __init__(self, excel):
        self.recs = []
        for t in ("weapons", "armor", "misc"):
            for r in table(excel, t):
                if r.get("code") and r["code"] != "":
                    if r.get("name", "").lower() == "expansion" and not r.get("code"):
                        continue
                    r["_table"] = t
                    self.recs.append(r)
        self.types = [r for r in table(excel, "itemtypes") if r.get("ItemType", "") != "Expansion"]
        self.type_idx = {r["Code"]: i for i, r in enumerate(self.types) if r.get("Code")}

    def rec(self, cls):
        return self.recs[cls] if 0 <= cls < len(self.recs) else None

    def tidx(self, cls):
        return self.type_idx.get(self.rec(cls)["type"])

    def maxsock(self, cls, ilvl):
        r = self.rec(cls)
        ty = self.types[self.tidx(cls)]
        gs = int(r.get("gemsockets") or 0)
        k = "MaxSock1" if ilvl <= 25 else "MaxSock25" if ilvl <= 40 else "MaxSock40"
        return min(gs, int(ty.get(k) or 0))

    def area(self, cls):
        r = self.rec(cls)
        return int(r.get("invwidth") or 0) * int(r.get("invheight") or 0)

    def throwable(self, cls):
        r = self.rec(cls)
        ty = self.types[self.tidx(cls)]
        return r.get("stackable") == "1" or ty.get("Throwable") == "1"


def read(path):
    """(tag, data) per line: JSON lines as dicts, printf lines as key=value dicts, other lines as {"raw": text}."""
    out = []
    with open(path, errors="replace") as f:
        text = f.read().splitlines()
    for ln in text:
        if not ln or " " not in ln:
            continue
        tag, rest = ln.split(" ", 1)
        if rest.startswith("{"):
            try:
                out.append((tag, json.loads(rest)))
                continue
            except ValueError:
                pass
        d = {}
        for w in rest.split():
            if "=" in w:
                k, v = w.split("=", 1)
                d[k] = v
        out.append((tag, d))
    return out


def stat(lst, s):
    for e in lst or []:
        if e[0] == s:
            return e[2]
    return None


def cmd_logs(ns):
    I = Items(ns.excel)
    S = collections.Counter()
    bad = []
    lists = collections.defaultdict(list)

    def fail(path, k, msg):
        bad.append("%s:%d: %s" % (os.path.basename(path), k, msg))

    for path in ns.logs:
        L = read(path)
        pend = {}          # thread -> (k, GS0) waiting for GS1/GS2
        made = {}          # unit -> game seed at GS4 (or GS2)
        gq = {}            # thread -> GQ0
        ic = {}            # thread -> open IC0
        cpre = None        # (k, gs0 count) inside CPRE..CPOST
        ss = None          # open SetSockets
        rne_last = {}      # thread -> last RNE
        blocks = {}        # thread -> creation lines (IC0 .. ICX)
        bld = {}           # thread -> builders entered since GQ0
        for k, (tag, d) in enumerate(L, 1):
            th = d.get("th", 1) if isinstance(d, dict) else 1
            if tag in ("IC0", "ICJ", "ICX", "BLD", "FB", "SLOT", "ROLLR", "LX", "SOK0", "SOKM", "SOKR", "SOKX", "ETHX",
                       "MB0", "MBF", "RNE", "RBF", "APE", "APX"):
                if tag == "IC0":
                    ic[th] = d
                    blocks[th] = []
                if th in blocks:
                    blocks[th].append((tag, d))
                if tag == "ICX" and th in blocks:
                    lists[path].append((blocks.pop(th), ic.get(th)))
            if tag == "GS0":
                S["GS0 ItemCreate calls"] += 1
                if th in pend:
                    fail(path, k, "GS0 without GS2 before it")
                pend[th] = {"k": k, "gs0": d, "gs1": None, "gs3": None}
                if cpre is not None:
                    cpre[1].append(d)
            elif tag == "GS1":
                p = pend.get(th)
                if not p:
                    S["GS1 outside ItemCreate (other SUnitCreate callers)"] += 1
                    continue
                g = sp(p["gs0"]["gseed"])
                g1 = rng.step(*g)
                g2 = rng.step(*g1)
                want = {"gseed": fmt(g2), "useed": fmt((g1[0], 666)), "u28": g1[0], "iseed": fmt((g2[0], 666)),
                        "start": g2[0]}
                for f, v in want.items():
                    if d.get(f) != v:
                        fail(path, k, "GS1 %s %s, model %s" % (f, d.get(f), v))
                S["GS1 seeds = two game-seed steps (unit {g1.low, 666}, item {g2.low, 666})"] += 1
                p["gs1"] = d
            elif tag == "GS2":
                p = pend.get(th)
                if not p or not p["gs1"]:
                    fail(path, k, "GS2 without GS0/GS1")
                    continue
                for f in ("gseed", "useed", "u28", "iseed", "start", "unit"):
                    if d.get(f) != p["gs1"].get(f):
                        fail(path, k, "GS2 %s %s != GS1 %s" % (f, d.get(f), p["gs1"].get(f)))
                p["gs2"] = d
                S["GS2 = GS1 (nothing drew after ItemSeedInit in SUnitCreate)"] += 1
            elif tag == "GS3":
                p = pend.get(th)
                if p:
                    p["gs3"] = d
                    if not (p["gs0"]["arg"] or p["gs0"]["r2c"]):
                        fail(path, k, "GS3 with arg 0 and record +0x2C 0")
                    S["GS3 record-seed branch (arg %s, +0x2C %s)" % (p["gs0"]["arg"], p["gs0"]["r2c"])] += 1
            elif tag == "GS4":
                p = pend.pop(th, None)
                if not p or "gs2" not in p:
                    fail(path, k, "GS4 without GS2")
                    continue
                if not p["gs3"]:
                    for f in ("gseed", "useed", "iseed", "start"):
                        if d.get(f) != p["gs2"].get(f):
                            fail(path, k, "GS4 %s %s != GS2 %s" % (f, d.get(f), p["gs2"].get(f)))
                    S["GS4 = GS2 (no record seed)"] += 1
                made[d["unit"]] = d["gseed"]
            elif tag == "BLD":
                bld.setdefault(th, []).append(d["k"])
                rne_last.pop(th, None)
            elif tag == "GQ0":
                gq[th] = d
                bld[th] = []
                g = made.pop(d.get("unit"), None)
                if g is None:
                    S["GQ0 of a unit with no GS4 (not an ItemCreate creation)"] += 1
                elif g != d["gseed"]:
                    fail(path, k, "GQ0 game seed %s != GS4 %s" % (d["gseed"], g))
                else:
                    S["GQ0 game seed = GS4 (ItemInitStats drew no game seed)"] += 1
            elif tag in ("GQJ", "GQX"):
                q0 = gq.get(th)
                if not q0:
                    continue
                if d.get("gseed") != q0.get("gseed"):
                    fail(path, k, "%s game seed %s != GQ0 %s" % (tag, d.get("gseed"), q0.get("gseed")))
                low = "low" in bld.get(th, ())
                if d.get("useed") == q0.get("useed"):
                    S["%s game and unit seed = GQ0%s" % (tag, " (low builder)" if low else "")] += 1
                elif low and d.get("useed") == fmt(rng.step(*sp(q0["useed"]))):
                    S["%s game seed = GQ0, unit seed one step on (the low builder's durability draw)" % tag] += 1
                else:
                    fail(path, k, "%s unit seed %s, GQ0 %s (builders %s)" % (tag, d.get("useed"), q0.get("useed"),
                                                                         bld.get(th)))
                if tag == "GQX":
                    gq.pop(th, None)
            elif tag == "CPRE":
                cpre = (k, [], int(d.get("item", "-1")), d.get("seed"))
            elif tag == "CPOST":
                if cpre is None:
                    continue
                unit = int(d.get("unit", "0"), 16)
                gs = cpre[1]
                if unit:
                    if len(gs) != 1:
                        fail(path, k, "CPOST unit with %d GS0 lines" % len(gs))
                    else:
                        g = gs[0]
                        if g["ret"] != 0x0055A6B4 or g["arg"] != 0 or g["r2c"] != 0:
                            fail(path, k, "drop GS0 ret %08x arg %d r2c %d" % (g["ret"], g["arg"], g["r2c"]))
                        if g["idx"] != cpre[2]:
                            fail(path, k, "drop GS0 record index %d != CPRE item %d" % (g["idx"], cpre[2]))
                        S["drop creations: one ItemCreate call (ret 0x0055A6B4, no record seed)"] += 1
                        if d.get("seed") != cpre[3]:
                            fail(path, k, "the source seed moved during the creation (%s -> %s)" % (cpre[3], d.get("seed")))
                        else:
                            S["drop creations: source seed at CPOST = at CPRE"] += 1
                else:
                    S["drop creation calls with no unit: GS0 lines %d" % len(gs)] += 1
                cpre = None
            elif tag == "SS0":
                ss = {"k": k, "s0": d}
                S["SetSockets calls (ret %08x)" % d["ret"]] += 1
            elif tag in ("SSP", "SSQ", "SSM", "SSN", "SSW") and ss is not None:
                ss[tag] = d
            elif tag == "SSR" and ss is not None:
                check_ss(I, ss, ic.get(ss["s0"]["th"]), S, lambda m, ss=ss: fail(path, ss["k"], m))
                ss = None
            elif tag == "MB0":
                S["magic builder after its picks"] += 1
                nxt = L[k][0] if k < len(L) else None
                if (d["p"] == 0 and d["s"] == 0) != (nxt == "MBF"):
                    fail(path, k, "MB0 p %d s %d, next %s" % (d["p"], d["s"], nxt))
                if nxt == "MBF":
                    S["magic builder failed: both slots 0 (MBF)"] += 1
                else:
                    S["magic builder ok: %s" % ("both" if d["p"] and d["s"] else "prefix" if d["p"] else "suffix")] += 1
            elif tag == "RNE":
                S["rare name scans: %s" % ("none" if d["n"] == 0 else "candidates")] += 1
                prev = rne_last.get(th)
                if prev is not None and prev[1]["n"] == 0:
                    if prev[1].get("iseed") != d.get("iseed"):
                        fail(path, k, "an empty name scan drew (%s -> %s)" % (prev[1].get("iseed"), d.get("iseed")))
                    else:
                        S["empty name scan followed by the second scan with the same item seed (no draw)"] += 1
                rne_last[th] = (k, d)
            elif tag == "RBF":
                S["rare build failures (0x005C1E71)"] += 1
    # per creation: classic throwables, tors, dur%, carriers
    for path, blks in lists.items():
        for blk, ic0 in blks:
            if not ic0:
                continue
            cls = ic0["cls"]
            r = I.rec(cls)
            if r is None:
                continue
            classic = ic0.get("exp") == 0
            tags = [t for t, _ in blk]
            if classic and I.throwable(cls) and r["_table"] == "weapons":
                chain = []
                for t, d in blk:
                    if t == "BLD":
                        chain.append("BLD:%s" % d["k"])
                    elif t == "FB":
                        chain.append("FB:%s" % d.get("k", d.get("q")))
                    elif t in ("MBF", "RBF"):
                        chain.append(t)
                q = next((d.get("q") for t, d in blk if t == "ICJ"), None)
                S["classic throwable %s (ICQ %s): %s -> q %s" % (r["code"], ic0.get("q"), " ".join(chain), q)] += 1
            if classic and I.tidx(cls) == 3:
                q = next((d.get("q") for t, d in blk if t == "ICJ"), None)
                if q in (2, 3):
                    n0 = tags.count("SOK0")
                    nr = tags.count("SOKR")
                    S["classic tors q%s: SOK0 %d, SOKR %d" % (q, n0, nr)] += 1
                    # the tors test (0x00556BEC-0x00556BFC) is reached only past ItemMaxSockets > 0 (0x00556B96):
                    # SOKM (0x00556BA3) with ms > 0 marks a case where a roll without the test would have drawn
                    ms = [d.get("ms") for t, d in blk if t == "SOKM"]
                    S["classic tors q%s reaching the tors test (SOKM ms > 0): %s, SOKR %d" % (
                        q, "yes" if any(m and m > 0 for m in ms) else "no", nr)] += 1
                    if nr:
                        bad.append("%s: classic tors %s drew a socket roll" % (os.path.basename(path), r["code"]))
            elif not classic and I.tidx(cls) == 3:
                # control: an expansion body armour past ItemMaxSockets > 0 draws the roll (SOKR)
                q = next((d.get("q") for t, d in blk if t == "ICJ"), None)
                if q in (2, 3):
                    ms = [d.get("ms") for t, d in blk if t == "SOKM"]
                    if any(m and m > 0 for m in ms):
                        S["control: expansion tors q%s past SOKM ms > 0, SOKR %d" % (q, tags.count("SOKR"))] += 1
            q = next((d.get("q") for t, d in blk if t == "ICJ"), None)
            eth = any(t == "ETHX" and d["fl"] & 0x400000 for t, d in blk)
            mode = None
            dd = None
            in13 = False
            for t, d in blk:
                if t == "APE":
                    mode = d.get("mode")
                elif t == "APX":
                    mode = None
                elif t == "SLOT":
                    in13 = mode == 1 and d.get("func") == 13
                    if d.get("func") in (12, 23, 24):
                        S["carrier: func %d slot (class %d, q %s)" % (d["func"], cls, q)] += 1
                elif t == "ROLLR" and in13:
                    dd = d["v"]
                    in13 = False
            if q == 3 and eth and dd is not None:
                lx = [d for t, d in blk if t == "LX"]
                b = lx[-1].get("b") if lx else None
                h, s72 = stat(b, 73), stat(b, 72)
                a = h + h * dd // 100
                o = (h - 1) * (100 + dd) // 100 + 1
                S["superior ethereal dur%%: %s h %d d %d stat72 %d code %d other %d %s" % (
                    r["code"], h, dd, s72, a, o, "DIFFER" if a != o else "same")] += 1
                if s72 != a:
                    bad.append("%s: dur%% stat 72 %d != code order %d" % (os.path.basename(path), s72, a))
    for k in sorted(S):
        print("  %-100s %d" % (k, S[k]))
    for b in bad[:50]:
        print("BAD " + b)
    print("%d bad" % len(bad))
    return 1 if bad else 0


def check_ss(I, ss, ic0, S, fail):
    s0 = ss["s0"]
    cls, q, n = s0.get("cls"), s0.get("q"), s0["n"]
    if "SSP" not in ss:
        S["SetSockets: returned before the cap"] += 1
        return
    p, cap = ss["SSP"]["p"], ss["SSP"]["cap"]
    if cls is not None and I.rec(cls) is not None and p != I.area(cls):
        fail("SSP p %d != invwidth x invheight %d" % (p, I.area(cls)))
    if p == 0:
        S["SetSockets: p = 0, return"] += 1
        return
    if cap != min(p, 6):
        fail("SSP cap %d != min(p %d, 6)" % (cap, p))
    if p > 6:
        S["SetSockets: the 6 clamp lowered the cap (p > 6)"] += 1
    qq = ss.get("SSQ")
    if not qq:
        fail("no SSQ")
        return
    if q in (1, 2, 3, None):
        want, wn = cap, n
    elif q == 4:
        want, wn = min(cap, 4), n
    elif q == 6:
        want, wn = min(cap, 2), n
    elif q in (8, 9):
        want, wn = min(cap, 3), n
    else:
        want, wn = qq["cap"], qq["n"]
        S["SetSockets: quality %d (not modelled here)" % q] += 1
    if qq["cap"] != want or (qq["n"] & 0xFFFFFFFF) != (wn & 0xFFFFFFFF):
        fail("SSQ q %s cap %d n %d, model %d %d" % (q, qq["cap"], qq["n"], want, wn))
    S["SetSockets: quality %s, quality clamp %s" % (q, "acted" if want < cap else "none")] += 1
    if qq["cap"] > 3:
        S["SetSockets: quality %s with a cap above 3 after the quality step" % q] += 1
    if n >= 4:
        S["SetSockets: quality %s with a request of 4 or more" % q] += 1
    m = ss.get("SSM")
    if m and ic0 and ic0.get("it") == s0.get("it") and cls is not None:
        ms = I.maxsock(cls, ic0["ilvl"])
        if m["maxs"] != ms:
            fail("SSM maxs %d != F5 model %d (cls %d ilvl %d)" % (m["maxs"], ms, cls, ic0["ilvl"]))
        else:
            S["SetSockets: ItemMaxSockets = F5 model"] += 1
    nn = ss.get("SSN")
    if not nn or not m:
        fail("no SSM/SSN")
        return
    if nn["cap"] != min(qq["cap"], m["maxs"]):
        fail("SSN cap %d != min(%d, %d)" % (nn["cap"], qq["cap"], m["maxs"]))
    if m["maxs"] < qq["cap"]:
        S["SetSockets: ItemMaxSockets lowered the cap"] += 1
    nv = nn["n"] if nn["n"] < 0x80000000 else nn["n"] - (1 << 32)
    r = min(max(nv, 1), nn["cap"])
    w = ss.get("SSW")
    if r < 1:
        if w:
            fail("SSW with r < 1")
        S["SetSockets: nothing written (cap < 1)"] += 1
        return
    if not w or w["v"] != r:
        fail("SSW %s, model %d" % (w and w["v"], r))
        return
    S["SetSockets: written = min(max(n, 1), cap)"] += 1
    if nv > nn["cap"]:
        who = ("inventory" if p < min(6, qq["cap"], m["maxs"]) + 0 and p == nn["cap"] else
               "6" if nn["cap"] == 6 and p > 6 else
               "quality" if qq["cap"] < cap and qq["cap"] == nn["cap"] else
               "ItemMaxSockets" if m["maxs"] == nn["cap"] else "?")
        S["SetSockets: n %d clamped to %d (%s)" % (nv, nn["cap"], who)] += 1


def cmd_static(ns):
    I = Items(ns.excel)
    elix = [r["code"] for r in I.recs if r.get("type") == "elix" or r.get("type2") == "elix"]
    print("type 11 (%s) records: %s" % (I.types[11]["Code"], elix))
    ty = I.types[11]
    print("  ItemTypes TreasureClass %s (no weapN/armoN-style group)" % ty.get("TreasureClass"))
    tc = table(ns.excel, "treasureclassex")
    cells = [r[c] for r in tc for c in r if c and c.startswith("Item") and r[c]]
    hits = [c for c in cells if any(c == e or c.startswith(e + ",") for e in elix)]
    print("  TreasureClassEx: %d item cells, naming an elixir: %d" % (len(cells), len(hits)))
    cm = table(ns.excel, "cubemain")
    outs = [r[c] for r in cm for c in ("output", "output b", "output c") if r.get(c)]
    oh = [o for o in outs if any(o.split(",")[0].strip('"') == e for e in elix) or "elix" in o.split(",")[0]]
    print("  cubemain outputs: %d, naming an elixir or its type: %d" % (len(outs), len(oh)))
    misc = {r["code"]: r for r in table(ns.excel, "misc")}
    for e in elix:
        r = misc[e]
        vend = {k: v for k, v in r.items() if k and (k.endswith("Min") or k.endswith("Max")) and v not in ("", "0")}
        print("  %s: spawnable %s, quest %s, vendor Min/Max cells set: %s" % (e, r.get("spawnable"), r.get("quest"), vend or "none"))
    other = []
    for t in ("monstats", "superuniques", "levels", "objects", "uniqueitems", "setitems", "runes", "gamble"):
        try:
            rows = table(ns.excel, t)
        except OSError:
            continue
        for r in rows:
            for k, v in r.items():
                if v and any(v == e for e in elix):
                    other.append((t, k))
    print("  other tables naming an elixir code: %s" % (other or "none"))
    over = []
    for cls, r in enumerate(I.recs):
        if r.get("hasinv") != "1" or I.tidx(cls) is None:
            continue
        a = I.area(cls)
        for il in (1, 26, 41):
            m = I.maxsock(cls, il)
            if m > min(6, a):
                over.append((r["code"], il, m, a))
    print("bases whose ItemMaxSockets exceeds min(6, invwidth x invheight): %d %s" % (len(over), over))
    return 0


def cmd_rareboth(ns):
    """items/affixes E5: the rare builder fails with no prefix and no suffix only when, after both names are found,
    both sides have no candidate row. tools/affixes.py survey's loop (its Tables, side_rows, alvl_of and
    rare_name_ok), per rare-able base, item version (1 classic, 101 expansion) and ilvl 1..99: the cases with both
    names and both sides empty, and the least candidate count of the larger side."""
    import affixes
    T = affixes.Tables(ns.excel)
    both = []
    n = 0
    for cls in range(len(T.items)):
        b = T.b(cls)
        if T.tbyte(cls, 0x16, 1) or not T.tbyte(cls, 0x15):
            continue
        for ver in (1, 101):
            rows = {}
            for ilvl in range(1, 100):
                it = affixes.Item(T, dict(cls=cls, ilvl=ilvl, ver=ver))
                it.q = 6
                names = [any(affixes.rare_name_ok(T, it, T.rare[i]) for i in range(*blk))
                         for blk in (T.rblk_p, T.rblk_s)]
                if not all(names):
                    continue
                key = T.maxsock(cls, ilvl) > 0
                if key not in rows:
                    rows[key] = [affixes.side_rows(T, it, T.blk_p), affixes.side_rows(T, it, T.blk_s)]
                a = affixes.alvl_of(it)
                live = [[r for r in rs if r["level"] <= a and (r["maxlevel"] == 0 or r["maxlevel"] >= a)]
                        for rs in rows[key]]
                n += 1
                if not live[0] and not live[1]:
                    both.append((b["code"], ver, ilvl))
    print("rare-able bases x versions x ilvls with both names: %d" % n)
    print("of them with no prefix and no suffix candidate (items/affixes E5 reachable): %d %s" % (len(both), both[:40]))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(prog="sweep_h2b.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("logs")
    p.add_argument("logs", nargs="+")
    p.add_argument("--excel", default=EXCEL)
    p = sub.add_parser("static")
    p.add_argument("--excel", default=EXCEL)
    p = sub.add_parser("rareboth")
    p.add_argument("--excel", default=EXCEL)
    ns = ap.parse_args(argv[1:])
    return {"logs": cmd_logs, "static": cmd_static, "rareboth": cmd_rareboth}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
