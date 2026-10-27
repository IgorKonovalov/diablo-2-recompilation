#!/usr/bin/env python3
"""Plan 0038 batch H6c (vendors): the checks over tools/gdb/h6c.gdb logs that tools/vendors.py check does not make,
for docs/findings/items/0009-vendors.md (run:2026-10-27-sweep-vendors), and the objdump anchors.

    python3 -I tools/sweep_h6c.py logs <log> [<log> ...] [--excel DIR] [-v]
    python3 -I tools/sweep_h6c.py pairs <log> [<log> ...]        # PIEND -> PLEAVE pairs in any vendors.py log
    python3 -I tools/sweep_h6c.py fails <log> [<log> ...]        # creations and failures per stock build
    python3 -I tools/sweep_h6c.py hb <log> [<log> ...]           # Asheara's first trade opens: the hireling byte
    python3 -I tools/sweep_h6c.py static [--exe workspace/install/app/game.exe]

`logs` (each check prints its counted cases; a "BAD" line is a mismatch; the SUMMARY line counts them):
  tll     every TLL line: its call site by return address (0x00538196 the per-frame room check, 0x0053AF45
          sub_0053AEC0_PlayerChangeLevel), the levels, and the STALE call that follows it (townEmpty, the records'
          built bytes before and after); a walk out of a town (old level a town, new level of the same act, the
          per-frame site) must give townEmpty 1 and reset or clear every built store of the act
  reopen  every trade open (TO, gamble 0) of a built, non-stale store: no BS0 before the next TO, and the stock
          inventory at the open (INVT) holds the same item ids as after the last build (INVB) less the ids bought
          since (NB1); the events since that build (TLL level changes, LUN level-ups, town entries) are listed
  build   every stock build: its failures (CSX 0), whether the count passed 32 and where (the perm creations made
          after it), the ilvl against clvl + 5 (VENDOR_StockLevel outside Normal)
  place   every stock item: the tab VPG against the item type's StorePage byte (itemtypes +0x22, the type
          weapons/armor/misc +0x11E), the placement calls (VPA/VPR: tab 2 only after tab 1 failed), the cell (VOK) inside
          the 10 x 10 grid and not overlapping an item already placed on that tab in that build (invwidth +0x10F,
          invheight +0x110); a first-fit search in column-major and in row-major order is scored against the cells
          (reported only)
  rec     every store creation (CF0 returning to VENDOR_CreateStockItem 0x005764DB or GAMBLE_BuildInv 0x005789FE): the
          ICR line of its record
          (+0x18 = 4, +0x28 = 1, +0x80 = 2)
  glv     every gamble lvl (GLV before the clamp, GPK after): below 5 -> 5, above 99 -> 99, else unchanged
  hire    every HIRE_BuildStock entry (HBR): its caller chain (HSL return address) and its place before the first
          menu action (MA) and trade open (TO) of that NPC
  buy     every purchase (NB0 .. NB1): the store's permanent test (SISP) and removal (SISR) or the gamble call (SISG),
          the copy (CPY0/CPY1: class, quality, flags, file index of the source and the copy), no creation (CF0, GB0,
          BS0) inside, and the stock or gamble inventory after = before less the bought id exactly when it is removed
  sell    every sale (NS0 .. NS1): the NSX decision lines in order (refusal reason, the permanent test, the copy)
  pie     every PIEND line and the PLEAVE that follows it from 0x00555562, with the interaction state of the
          player (the last ISET/ICLR for the unit)

Stdlib only. Read-only.
"""
import argparse
import collections
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402

EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
TOWNS = {1: 0, 40: 1, 75: 2, 103: 3, 109: 4}
ACT_OF_LEVEL = None          # filled from levels.bin (Act byte) when needed
NAME = {148: "Akara", 147: "Gheed", 154: "Charsi", 178: "Fara", 202: "Lysander", 177: "Drognan", 253: "Hratli",
        254: "Alkor", 255: "Ormus", 199: "Elzix", 252: "Asheara", 257: "Halbu", 405: "Jamella", 513: "Malah",
        511: "Larzuk", 512: "Anya", 514: "Nihlathak", 150: "Kashya", 198: "Greiz", 515: "Qual-Kehk"}


class Tables:
    def __init__(self, excel):
        self.items = []
        for t in ("weapons", "armor", "misc"):
            r, _ = excel_bin.read_bin(excel_bin.find_file(excel, t, ".bin"))
            self.items.extend(r)
        self.types, _ = excel_bin.read_bin(excel_bin.find_file(excel, "itemtypes", ".bin"))
        lv, _ = excel_bin.read_bin(excel_bin.find_file(excel, "levels", ".bin"))
        self.levels = lv

    def code(self, i):
        return bytes(self.items[i][0x80:0x84]).decode("latin-1").strip()

    def size(self, i):
        return self.items[i][0x10F], self.items[i][0x110]

    def store_page(self, i):
        t = struct.unpack_from("<H", self.items[i], 0x11E)[0]
        return self.types[t][0x22] if t < len(self.types) else 0xFF


def read(path):
    out = []
    for line in open(path, errors="replace"):
        t, _, rest = line.rstrip("\n").partition(" ")
        if t == "GAME":
            out.append(("GAME", {}))
            continue
        if rest.startswith("{"):
            try:
                out.append((t, json.loads(rest)))
            except ValueError:
                pass
    return out


class Report:
    def __init__(self, verbose):
        self.c = collections.Counter()
        self.bad = 0
        self.v = verbose
        self.lines = collections.defaultdict(list)

    def count(self, k, n=1):
        self.c[k] += n

    def fail(self, where, msg):
        self.bad += 1
        print("BAD %s: %s" % (where, msg))

    def note(self, sec, msg):
        self.lines[sec].append(msg)


def close_item(b, R, where):
    """A stock item's placement outcome, from its VPR results (and VPK): the tab it went to, or None (parked)."""
    cur = b.pop("cur", None)
    if not cur:
        return
    res = cur["res"]
    if cur.get("parked"):
        R.count("place: no room (parked)")
        if not res or any(v for k, v in res):
            R.fail(cur["where"], "parked after results %s" % res)
        if cur["page"] == 1 and [k for k, v in res] != [1, 2]:
            R.fail(cur["where"], "a tab-1 item parked without its tab-2 try: %s" % res)
        if cur["page"] != 1 and [k for k, v in res] != [1]:
            R.fail(cur["where"], "a tab-%d item with tries %s" % (cur["page"], res))
        b["place"].append((cur["it"], None))
        return
    if res == [(1, 1)]:
        tab = cur["page"]
    elif res == [(1, 0), (2, 1)] and cur["page"] == 1:
        tab = 2
        R.count("place: placed on tab 2 after a tab-1 failure")
    else:
        R.fail(cur["where"], "placement results %s for a tab-%d item" % (res, cur["page"]))
        return
    R.count("place: items placed, tab %d" % tab)
    b["place"].append((cur["it"], tab))


def check_cells(T, R, where, place, items):
    """The cells of a build's stock (INVB: id, class, page, x, y) against the placements: each placed item on its tab,
    inside the 10 x 10 grid, no two overlapping; a first-fit search in creation order (column-major, row-major)
    scored against the cells (reported only)."""
    if place is None:
        return
    inv = {x[0]: x for x in items}
    placed = [(it, tab) for it, tab in place if tab is not None]
    ids = {it["id"] for it, tab in placed}
    if ids != set(inv):
        R.fail(where, "stock ids after the build %d, placed %d, in common %d" % (len(inv), len(ids), len(ids & set(inv))))
    occ = collections.defaultdict(set)
    taken = collections.defaultdict(set)
    for it, tab in placed:
        x = inv.get(it["id"])
        if not x:
            continue
        R.count("place: cells checked (INVB)")
        pg, cx, cy = x[2], x[3], x[4]
        if pg != tab:
            R.fail(where, "item %d on page %d, placed on tab %d" % (it["id"], pg, tab))
        w, h = T.size(it["c"])
        if not (0 <= cx and cx + w <= 10 and 0 <= cy and cy + h <= 10):
            R.fail(where, "item %d cell (%d, %d) size %dx%d outside the grid" % (it["id"], cx, cy, w, h))
        cells = {(cx + a, cy + b) for a in range(w) for b in range(h)}
        if cells & occ[pg]:
            R.fail(where, "item %d cell (%d, %d) overlaps" % (it["id"], cx, cy))
        for order in ("col", "row"):
            rng = [(a, b) for a in range(10) for b in range(10)] if order == "col" else \
                  [(a, b) for b in range(10) for a in range(10)]
            pred = None
            for a, b in rng:
                cs = {(a + p, b + q) for p in range(w) for q in range(h)}
                if a + w <= 10 and b + h <= 10 and not cs & taken[(order, pg)]:
                    pred = (a, b)
                    break
            R.count("place: first-fit %s-major %s" % (order, "agrees" if pred == (cx, cy) else "differs"))
            taken[(order, pg)] |= cells
        occ[pg] |= cells


def check_log(path, T, R):
    ev = read(path)
    name = os.path.basename(path)
    perm_of = {}                 # cls -> permanent item indices (from BS0 codes)
    after_build = {}             # cls -> set of stock ids after the last build / purchase
    since = collections.defaultdict(list)
    built = {}
    last_lvl = None
    cur_build = None
    istate = {}
    open_buy = None
    open_sell = None
    sold_id = None
    first = {}                   # (cls, what) -> event index
    last_place = {}
    for i, (t, d) in enumerate(ev):
        where = "%s #%d %s" % (name, i, t)
        if t == "GAME":
            after_build, built, since = {}, {}, collections.defaultdict(list)
            continue
        # ---------------------------------------------------------------- interaction state, PIEND
        if t == "ISET":
            istate[d["unit"]] = (d["type"], d["id"], 1)
        elif t == "ICLR":
            istate[d["unit"]] = (6, -1, 0)
        elif t == "PIEND":
            nxt = ev[i + 1] if i + 1 < len(ev) else (None, None)
            pl = nxt[0] == "PLEAVE" and nxt[1].get("ret") == 0x00555562
            R.count("pie: PIEND lines")
            R.count("pie: PIEND followed by PLEAVE from 0x00555562" if pl else "pie: PIEND with no PLEAVE")
            s = istate.get(d.get("a1") or d.get("ecx"))
            R.note("pie", "%s: player %s interaction %s -> %s" % (where, d.get("a1"), s, "PLEAVE" if pl else "none"))
            if s is not None and (s[2] == 1 and s[0] == 1) != pl:
                R.fail(where, "PLEAVE %s with the interaction state %s" % (pl, s))
        # ---------------------------------------------------------------- town leaves
        elif t == "TLL":
            site = {0x00538196: "per-frame room check", 0x0053AF45: "PlayerChangeLevel"}.get(d["ret"], hex(d["ret"]))
            j = i + 1
            while j < len(ev) and ev[j][0] not in ("STALE", "TLL", "GAME"):
                j += 1
            stl = ev[j][1] if j < len(ev) and ev[j][0] == "STALE" else None
            k = j + 1
            while k < len(ev) and ev[k][0] not in ("STALEX", "TLL", "GAME"):
                k += 1
            stx = ev[k][1] if k < len(ev) and ev[k][0] == "STALEX" else None
            old, new = d["old"], d["new"]
            kind = "town leave" if old in TOWNS else "not a town"
            R.count("tll: TLL from the %s, %s" % (site, kind))
            if old not in TOWNS:
                for c in built:
                    since[c].append("TLL %s->%s%s" % (old, new, " (town entry)" if new in TOWNS else ""))
                continue
            if stl is None:
                R.fail(where, "no STALE after a town leave")
                continue
            same = T.levels[new][0x3] == TOWNS[old] if new < len(T.levels) else None
            b0 = {r[0]: r for r in stl["recs"]}
            b1 = {r[0]: r for r in (stx or {}).get("recs", [])}
            res = []
            for c, r in b0.items():
                if r[2]:
                    a = b1.get(c)
                    res.append("%s %s" % (NAME.get(c, c), "reset" if a and not a[2] else ("stale" if a and a[3] else
                                                                                         "kept")))
            R.note("tll", "%s: %s -> %s (%s act), %s, townEmpty %d, ret %s: %s" % (
                where, old, new, "same" if same else "other", site, stl["empty"], hex(stl["ret"]), ", ".join(res)))
            if site == "per-frame room check" and same:
                R.count("tll: walk or in-act change from a town by the per-frame check")
                if stl["empty"] != 1:
                    R.fail(where, "townEmpty %d on an in-act leave" % stl["empty"])
                for c, r in b0.items():
                    if r[2] and b1.get(c, [0, 0, 1])[2]:
                        R.fail(where, "%s still built after an in-act leave" % NAME.get(c, c))
                R.count("tll: built stores destroyed by it", sum(1 for r in b0.values() if r[2]))
            for c in built:
                since[c].append("TLL %s->%s" % (old, new))
        elif t == "LUN":
            R.count("reopen: LUN (level-up notes)")
            for c in built:
                since[c].append("level-up to %s" % d["a1"])
        elif t == "PLR":
            pass
        # ---------------------------------------------------------------- builds
        elif t == "BS0":
            cur_build = {"cls": d["cls"], "fails": 0, "made": 0, "fail_at": None, "perm": d["perm"], "permmade": 0,
                         "diff": d["diff"], "occ": collections.defaultdict(list), "place": [], "ilvl": None}
            perm_of[d["cls"]] = d["perm"]
        elif t == "BSL" and cur_build:
            cur_build["ilvl"], cur_build["clvl"] = d["ilvl"], d["clvl"]
        elif t == "CS0" and cur_build:
            cur_build["code"] = d["code"]
            if cur_build["fail_at"] is not None and struct.unpack("<I", d["code"].encode("latin-1"))[0] in \
                    cur_build["perm"]:
                cur_build["permmade"] += 1
        elif t == "CSX" and cur_build:
            cur_build["made"] += 1
            if not d["it"]:
                cur_build["fails"] += 1
                if cur_build["fails"] == 33:
                    cur_build["fail_at"] = cur_build["made"]
        elif t == "VPG" and cur_build:
            close_item(cur_build, R, where)
            it = d["it"]
            want = T.store_page(it["c"])
            R.count("place: VPG tabs checked")
            if want != d["page"]:
                R.fail(where, "tab %d for %s, StorePage byte %d" % (d["page"], T.code(it["c"]), want))
            cur_build["cur"] = {"it": it, "page": d["page"], "res": [], "where": where}
        elif t == "VPR" and cur_build and cur_build.get("cur"):
            cur_build["cur"]["res"].append((d["k"], d["v"]))
        elif t == "VPK" and cur_build and cur_build.get("cur"):
            cur_build["cur"]["parked"] = True
            close_item(cur_build, R, where)
        elif t == "BSX" and cur_build:
            close_item(cur_build, R, where)
            b = cur_build
            cur_build = None
            last_place[b["cls"]] = b["place"]
            R.count("build: stock builds")
            nm = NAME.get(b["cls"], b["cls"])
            R.note("build", "%s: %s ilvl %s: %d creations, %d failed" % (where, nm, b["ilvl"], b["made"], b["fails"]))
            if b["fails"] > 32:
                R.count("build: builds whose failures passed 32")
                R.note("build", "%s: %s ilvl %s: %d failures, the 33rd at creation %d of %d; permanent items created "
                       "after it %d of %d" % (where, nm, b["ilvl"], b["fails"], b["fail_at"], b["made"], b["permmade"],
                                              len(b["perm"])))
            if b["diff"] > 0 and b.get("clvl") is not None:
                if b["ilvl"] != b["clvl"] + 5:
                    R.fail(where, "ilvl %s for clvl %s outside Normal" % (b["ilvl"], b["clvl"]))
                if b["ilvl"] > 99:
                    R.count("build: builds outside Normal at ilvl > 99")
                    R.note("build", "%s: %s difficulty %d clvl %d -> ilvl %d" % (where, nm, b["diff"], b["clvl"],
                                                                                 b["ilvl"]))
        elif t == "INVB":
            check_cells(T, R, where, last_place.pop(d["cls"], None), d["items"])
            after_build[d["cls"]] = {x[0] for x in d["items"]}
            built[d["cls"]] = True
            since[d["cls"]] = []
        elif t == "MA":
            pass
        elif t == "TO":
            cls = d["cls"]
            first.setdefault((cls, "TO"), i)
            if not d["gamble"] and d.get("store") == 1 and d["built"] and not d["stale"]:
                j = i + 1
                while j < len(ev) and ev[j][0] not in ("TO", "BS0", "GAME"):
                    j += 1
                built_again = j < len(ev) and ev[j][0] == "BS0"
                inv = [x for x in ev[i - 3:i + 3] if x[0] == "INVT" and x[1]["cls"] == cls and not x[1]["gamble"]]
                ids = {x[0] for x in inv[-1][1]["items"]} if inv else None
                R.count("reopen: trade opens of a built, non-stale store")
                if built_again:
                    R.fail(where, "a build at the reopen of %s" % NAME.get(cls, cls))
                if ids is None or cls not in after_build:
                    R.fail(where, "no INVT/INVB for the reopen of %s" % NAME.get(cls, cls))
                elif ids != after_build[cls]:
                    R.fail(where, "%s stock ids changed: %d before, %d now, %d in common" % (
                        NAME.get(cls, cls), len(after_build[cls]), len(ids), len(ids & after_build[cls])))
                else:
                    R.count("reopen: stock ids unchanged since the last build or purchase")
                R.note("reopen", "%s: %s, %d items kept; since the build: %s" % (
                    where, NAME.get(cls, cls), len(ids or ()), ", ".join(since[cls]) or "nothing"))
                since[cls].append("reopen")
        elif t in ("HBR",):
            first.setdefault(("hire", "HBR"), i)
            j = i + 1
            while j < len(ev) and ev[j][0] not in ("HBX", "GAME"):
                j += 1
            hs = [x for x in ev[max(0, i - 4):i] if x[0] == "HSL"]
            caller = hex(hs[-1][1]["ret"]) if hs else None
            R.count("hire: HIRE_BuildStock entries, return %s, HIRE_SendList called from %s" % (hex(d["ret"]), caller))
            R.note("hire", "%s: HBR ret %s, HSL ret %s" % (where, hex(d["ret"]), caller))
        # ---------------------------------------------------------------- creation record
        elif t == "CF0" and d["ret"] in (0x005764DB, 0x005789FE):     # VENDOR_CreateStockItem, GAMBLE_BuildInv
            j = i + 1
            while j < len(ev) and ev[j][0] not in ("ICR", "CF0", "GAME"):
                j += 1
            if j >= len(ev) or ev[j][0] != "ICR":
                R.fail(where, "no ICR after the store creation")
                continue
            r = ev[j][1]
            R.count("rec: store creation records")
            ok = r["k18"] == 4 and r["w28"] == 1 and r["f80"] == 2
            if not ok:
                R.fail(where, "record +0x18 %d +0x28 %d +0x80 %d" % (r["k18"], r["w28"], r["f80"]))
            else:
                R.count("rec: +0x18 = 4, +0x28 = 1, +0x80 = 2")
        # ---------------------------------------------------------------- gamble lvl
        elif t == "GLV":
            j = i + 1
            while j < len(ev) and ev[j][0] not in ("GPK", "GLV", "GAME"):
                j += 1
            if j < len(ev) and ev[j][0] == "GPK":
                v, c = d["lvl"], ev[j][1]["lvl"]
                exp = 5 if v <= 5 else (99 if v >= 99 else v)
                R.count("glv: gamble lvl draws")
                if v < 5:
                    R.count("glv: lvl below 5 clamped (to %s)" % c)
                    R.count("glv: lvl %+d before the clamp" % v)
                elif v > 99:
                    R.count("glv: lvl above 99 clamped (to %s)" % c)
                    R.count("glv: lvl %d before the clamp" % v)
                if c != exp:
                    R.fail(where, "lvl %d -> %d, expected %d" % (v, c, exp))
        elif t == "GFREE":
            R.count("sell: GambleInvFree calls returning to %s" % hex(d["ret"]))
        # ---------------------------------------------------------------- purchases
        elif t == "NB0":
            open_buy = {"i": i, "d": d, "ev": []}
        elif open_buy is not None and t in ("SIS", "SISP", "SISR", "SISG", "CPY0", "CPY1", "CF0", "GB0", "BS0"):
            open_buy["ev"].append((t, d))
        elif t == "NB1" and open_buy is not None:
            b0, evs = open_buy["d"], open_buy["ev"]
            open_buy = None
            R.count("buy: purchases (NB0 .. NB1)")
            tags = [x[0] for x in evs]
            if any(x in tags for x in ("CF0", "GB0", "BS0")):
                R.fail(where, "a creation inside a purchase: %s" % tags)
            sis = [x[1] for x in evs if x[0] == "SIS"]
            c0 = [x[1] for x in evs if x[0] == "CPY0"]
            c1 = [x[1] for x in evs if x[0] == "CPY1"]
            if not sis:
                R.note("buy", "%s: no sale handled (eax %s) %s" % (where, d["eax"], tags))
                R.count("buy: purchases refused or without StoreItemSold")
                continue
            s = sis[0]
            bid = s["it"]["id"]
            kind = "gamble" if "SISG" in tags else ("stock removed" if "SISR" in tags else "stock kept")
            perm = [x[1]["al"] for x in evs if x[0] == "SISP"]
            R.count("buy: %s" % kind)
            if c0 and c1:
                a, b = c0[0]["src"], c1[0]["copy"]
                same = all(a.get(k) == b.get(k) for k in ("c", "q", "fi"))
                R.count("buy: copy class, quality, file index equal to the source" if same else "buy: copy differs")
                if not same:
                    R.fail(where, "copy %s of %s" % (b, a))
                if a.get("u") != s["it"]["u"]:
                    R.fail(where, "copied unit %s, sold unit %s" % (a.get("u"), s["it"]["u"]))
            else:
                R.fail(where, "no ItemCopy in the purchase")
            if "stock" not in b0 or "stock" not in d:
                # the logger revision before the NB0 npc fix (the first session): no inventories at NB0/NB1; the
                # stock the reopen check expects follows the removal call
                R.count("buy: inventories not logged around the purchase (not compared)")
                if kind == "stock removed" and s["cls"] in after_build:
                    after_build[s["cls"]] = after_build[s["cls"]] - {bid}
            elif kind == "gamble":
                before = {x[0] for x in b0.get("ginv", [])}
                after = {x[0] for x in d.get("ginv", [])}
                if after != before - {bid}:
                    R.fail(where, "gamble inventory %d -> %d around the purchase of %s" % (len(before), len(after),
                                                                                            bid))
                else:
                    R.count("buy: gamble inventory = before less the bought item")
            else:
                before = {x[0] for x in b0.get("stock", [])}
                after = {x[0] for x in d.get("stock", [])}
                gone = after == before - {bid}
                stay = after == before
                if perm and perm[0] and not stay:
                    R.fail(where, "a permanent item %s left the stock" % bid)
                if perm and not perm[0] and not gone:
                    R.fail(where, "a non-permanent item %s stayed (or more changed)" % bid)
                if (perm and perm[0] and stay) or (perm and not perm[0] and gone):
                    R.count("buy: stock after = before %s" % ("(permanent)" if perm[0] else "less the bought item"))
                    if s["cls"] in after_build:
                        after_build[s["cls"]] = after
            R.note("buy", "%s: %s %s q %s: %s; permanent %s; stock %s -> %s, gamble inventory %s -> %s" % (
                where, NAME.get(s["cls"], s["cls"]), T.code(s["it"]["c"]), s["it"].get("q"), kind, perm,
                len(b0.get("stock", [])), len(d.get("stock", [])), len(b0.get("ginv", [])), len(d.get("ginv", []))))
        # ---------------------------------------------------------------- sales
        elif t == "NS0":
            open_sell = []
            sold_id = d["a"][1]
        elif t == "NSX" and open_sell is not None:
            open_sell.append(d)
        elif t == "CPY0" and open_sell is not None:
            if d["src"]["id"] != sold_id:
                R.fail(where, "the sale copies item %s, NS0 names %s" % (d["src"]["id"], sold_id))
            else:
                R.count("sell: the copy's source is the sold item (NS0's id)")
        elif t == "NS1" and open_sell is not None:
            R.count("sell: sales (NS0 .. NS1)")
            seq = [x["why"] for x in open_sell]
            cp = [x for x in open_sell if x["why"] == "after ItemCopy"]
            pt = [x.get("al") for x in open_sell if x["why"] == "permanent test"]
            ref = [w for w in seq if w not in ("tests done", "permanent test", "after ItemCopy", "store page") and
                   not w.startswith("placed") and not w.startswith("copy freed")]
            src = cp[0]["copy"] if cp else None
            R.count("sell: %s" % ("copied" if cp else "not copied (%s)" % (", ".join(ref) or "permanent" if pt and
                                                                            pt[0] else ", ".join(ref) or "?")))
            R.note("sell", "%s: item id %s: %s; VENDOR_IsPermanent %s -> %s" % (
                where, sold_id, seq, pt, ("copy %s" % T.code(src["c"])) if src else "no copy"))
            open_sell = None
    return


def cmd_logs(ns):
    T = Tables(ns.excel)
    R = Report(ns.verbose)
    for p in ns.logs:
        check_log(p, T, R)
    print("== tools/sweep_h6c.py logs: %d logs ==" % len(ns.logs))
    for sec in ("tll", "reopen", "build", "place", "rec", "glv", "hire", "buy", "sell", "pie"):
        ks = sorted(k for k in R.c if k.startswith(sec + ":"))
        if not ks and not R.lines[sec]:
            continue
        print("[%s]" % sec)
        for k in ks:
            print("  %-78s %d" % (k, R.c[k]))
        for n in R.lines[sec][: None if ns.verbose else 40]:
            print("    " + n)
    print("SUMMARY logs=%d checks=%d bad=%d" % (len(ns.logs), sum(R.c.values()), R.bad))
    return 1 if R.bad else 0


def cmd_pairs(ns):
    n = collections.Counter()
    for p in ns.logs:
        ev = read(p)
        for i, (t, d) in enumerate(ev):
            if t == "PIEND":
                nxt = ev[i + 1] if i + 1 < len(ev) else (None, {})
                pl = nxt[0] == "PLEAVE" and nxt[1].get("ret") == 0x00555562
                n["PIEND"] += 1
                n["PIEND then PLEAVE (ret 0x00555562)" if pl else "PIEND alone"] += 1
                print("%s #%d PIEND ret %s -> %s" % (os.path.basename(p), i, hex(d["ret"]),
                                                     "PLEAVE ret %s npc %s" % (hex(nxt[1]["ret"]), nxt[1]["a1"])
                                                     if pl else "no PLEAVE"))
    for k in sorted(n):
        print("  %-50s %d" % (k, n[k]))
    return 0


def cmd_hb(ns):
    """Asheara's first trade opens (TO class 252, gamble 0, built 0) in any vendors.py log: the record's
    hirelingsBuilt byte at the open, and the HB0 (HIRE_BuildStock) and MA lines before it in that game."""
    n = collections.Counter()
    for p in ns.logs:
        ev = read(p)
        hb0 = None
        for i, (t, d) in enumerate(ev):
            if t == "GAME":
                hb0 = None
            elif t == "HB0":
                hb0 = i
            elif t == "TO" and d["cls"] == 252 and not d["gamble"] and not d["built"]:
                mas = [x[1]["action"] for x in ev[hb0 or 0:i] if x[0] == "MA" and x[1]["npc"] == d["id"]]
                n["first trade opens"] += 1
                n["hirelingsBuilt %d at the open" % d["hb"]] += 1
                n["an HB0 before it in the game" if hb0 is not None else "no HB0 before it"] += 1
                print("%s #%d: hb %d; HB0 at #%s; Asheara's menu actions between: %s" % (
                    os.path.basename(p), i, d["hb"], hb0, mas))
    for k in sorted(n):
        print("  %-50s %d" % (k, n[k]))
    return 0


def cmd_fails(ns):
    """Each stock build of any vendors.py log (BS0 .. BSX): the NPC, its stock level, its creations and failed creations
    (CSX with no item), and the largest failure count."""
    worst = 0
    n = 0
    for p in ns.logs:
        cur = None
        for t, d in read(p):
            if t == "BS0":
                cur = [d["cls"], None, 0, 0]
            elif t == "BSL" and cur:
                cur[1] = d["ilvl"]
            elif t == "CSX" and cur:
                cur[2] += 1
                cur[3] += 0 if d["it"] else 1
            elif t == "BSX" and cur:
                n += 1
                worst = max(worst, cur[3])
                print("%s: %s ilvl %s: %d creations, %d failed" % (os.path.basename(p), NAME.get(cur[0], cur[0]),
                                                                   cur[1], cur[2], cur[3]))
                cur = None
    print("builds %d, most failures in one build %d" % (n, worst))
    return 0


STATIC = [
    ("TownLevelLeave call sites", 0x00538191, 0x00538196, "call   0x537340"),
    ("TownLevelLeave call sites", 0x0053AF40, 0x0053AF45, "call   0x537340"),
    ("PlayerInteractEnd -> NpcStorePlayerLeave", 0x0055555D, 0x00555562, "call   0x536b50"),
    ("UnitFree's player case -> PlayerInteractEnd", 0x005555C6, 0x005555CB, "call   0x555500"),
    ("NpcInteractRemove: free only when the list is empty", 0x00572FAC, 0x00572FC0, None),
    ("BuildStock: the 32-failure test after a normal copy", 0x00576AA3, 0x00576AAD, None),
    ("BuildStock: no test in the magic loop", 0x00576B3C, 0x00576B4F, None),
    ("BuildStock: the 32-failure test after a permanent item", 0x00576BE1, 0x00576BEB, None),
    ("CreateStockItem: tab, placement, tab 2, park", 0x00576569, 0x00576633, None),
    ("StoreItemSold: gamble branch, permanent test, removal", 0x00576F6C, 0x00576FE9, None),
    ("GambleEnsure: build only without an inventory", 0x00578AFC, 0x00578B24, None),
    ("GAMBLE_BuildInv: the lvl clamp", 0x005788A3, 0x005788D8, None),
    ("StockLevel: no clamp outside Normal", 0x00576890, 0x005768F0, None),
    ("NpcInteractStart -> HIRE_SendList", 0x00572CFF, 0x00572D04, "call   0x576770"),
    ("NPC_MenuAction action 3 -> HIRE_SendList", 0x00579F28, 0x00579F2D, "call   0x576770"),
    ("HIRE_SendList -> HIRE_BuildStock", 0x005767EB, 0x005767F0, "call   0x576070"),
    ("NPC_OpenStore -> HIRE_BuildStock (after the stock)", 0x00578BCB, 0x00578C04, "call   0x576070"),
]


def cmd_static(ns):
    print("== tools/sweep_h6c.py static: %s ==" % ns.exe)
    for what, a, b, want in STATIC:
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % a,
                              "--stop-address=0x%x" % b, ns.exe], capture_output=True, text=True).stdout
        ins = [ln.strip() for ln in out.splitlines() if ln[:2] == "  " and ":" in ln]
        print("[%s] 0x%08X..0x%08X" % (what, a, b))
        for ln in ins:
            print("    " + ln)
        if want and not any(want in ln for ln in ins):
            print("BAD %s: %r not found" % (what, want))
            return 1
    return 0


def main(argv):
    ap = argparse.ArgumentParser(prog="sweep_h6c.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("logs")
    p.add_argument("logs", nargs="+")
    p.add_argument("--excel", default=EXCEL)
    p.add_argument("-v", "--verbose", action="store_true")
    p = sub.add_parser("pairs")
    p.add_argument("logs", nargs="+")
    p = sub.add_parser("fails")
    p.add_argument("logs", nargs="+")
    p = sub.add_parser("hb")
    p.add_argument("logs", nargs="+")
    p = sub.add_parser("static")
    p.add_argument("--exe", default=os.path.join(os.path.dirname(HERE), "workspace", "install", "app", "game.exe"))
    ns = ap.parse_args(argv[1:])
    return {"logs": cmd_logs, "pairs": cmd_pairs, "hb": cmd_hb, "fails": cmd_fails, "static": cmd_static}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
