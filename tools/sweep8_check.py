"""Checks and predictions of plan 0065 (harness sweep 8), the single-client cases. Stdlib only; reads the logs and the
excel tables named, writes nothing.

  python3 -I tools/sweep8_check.py predict [--excel DIR]          every prediction written before the runs
  python3 -I tools/sweep8_check.py pick <log> [--lid L] [--near-player]
  python3 -I tools/sweep8_check.py p12 <log> [...]
  python3 -I tools/sweep8_check.py c2 <log> [...] [--excel DIR]
  python3 -I tools/sweep8_check.py h2 <log> [...]
  python3 -I tools/sweep8_check.py h3 <log> [...] [--excel DIR]
  python3 -I tools/sweep8_check.py b8 <log> [...] [--room | --full]
  python3 -I tools/sweep8_check.py xs <log> [...]

pick  P12's cell: from the room grids (CB lines of tools/gdb/pilot.py, the activation snapshot COLL_MapBuild builds)
      of level L (default 2, the Blood Moor), every cell whose word has bit 0 and not bit 2 (`c & 5 == 1`, the case the
      backlog names; a word of exactly 0x0001 is taken before one with other bits), and for the one nearest the first PLR line in that level (or the last PLR line, --near-player) a
      stand cell 2..5 sub-tiles away whose 3x3 square has none of the player's blocking bits 0x1C09 (harness-play.md
      § Teleport only to standable cells), on one of the eight directions from the cell, the cells between them and as
      many cells past it on that line in the grid and all with c & 5 == 0, so a Nova missile from the stand cell crosses
      the cell towards free ground (an obstacle inside the level, not its edge). Prints the pick as JSON.
p12   skills/missiles D3 against src:pk-walkable-flags-overview's floor flag 01 (backlog 0054-p12), from the MMC/MMR
      lines of tools/gdb/p12.py. Each MMC is one MissileMoveCollide own-cell test of a followed missile: c & 5 != 0
      predicts the next line of that missile is MMR r 2 and that it never steps again (freed, no hit function: D3);
      c & 5 == 0 predicts it goes on (the control). A bit-0-only word (c & 5 == 1) is the separating case: the lead
      ("allow missiles pass") predicts a later MMC of the same missile. Counts the cases whose word came from a fresh
      CollisionTest (path +0x7C 0) apart from the cached ones, and whether the session's own CB grid has bit 0 at
      the tested point. The logged word has been through CollisionTest over the missile's size (or is the path's cached
      word of another point), so it is not the grid's own cell word: the lead's observable is counted apart, a missile
      at a point the CB grid marks bit-0-only (c & 5 == 1) whose word is 0 and that steps again (fresh = verdict
      "against the grid reading", cached = counted only). SEPARATING needs a fresh freed word and the grid's own cell
      bit-0-only. Prints the verdict; exit 1 when any case goes against D3 or the grid reading.
c2    skills/0002 § 12 C2 (backlog plan-0045-c2), from tools/gdb/skills.py's MC0/MC1 lines: every spike1 (Missiles
      row 7, Vel 10, VelLev 8) created without the caller's velocity (flags bit 2 clear) is predicted at
      tdiv(((VelLev · lvl) / 8 + Vel) << 8 · 75, 100) and checked; each one separates the read from the lead's
      `VelLev · (lvl − 1) + Vel`. tools/skills.py check is the full check of the same log.
h2    items/use F1f (items/0017 H2): every potion use (URM after UNIT_FindStatListByState) with a live list (list ≠
      0, rem > 0) is a blend: the UBL numerator must be old · rem + v (old the rate the previous USS set on that list
      and stat, v the UDV amount) and its denominator len + rem, and the USS rate trunc(num / den). It separates from
      `v ÷ len` when the two differ (counted). A use with no list sets trunc(v ÷ len) (tools/inventory_check.py's
      model checks the draws and that rate). Each UFL/UFM free is counted with the next use of that state, which must
      find no list.
h3    items/use D3, D5 (items/0017 H3), from T26.., T61.., IU0: for each flagged 0x26 (T26 flag ≠ 0 in an expansion
      game) the three ITEMS_UnitIsType results for 0x4C (hpot), 0x51 (wpot), 0x50 (apot) are predicted from
      ItemTypes' Equiv closure of the item's type, in that order, stopping at the first pass; a pass must be followed by
      an IU0 with the hireling (unit type 1) as user for that item, a refusal by none. The lead (The Arreat Summit) gives
      a mana potion to the hireling: an mp1 line separates. The same three results for each 0x61 (T61A..C).
b8    items/inventory F6 (items/0017 B8), from CCR, CMB, BOV0/BOV1 (tools/gdb/use-sweep8.py) and IPG
      (tools/gdb/inventory.py): at the corpse's BeltOverflow (BOV0 return 0x0057F47F, belt word 0, so belts row 2's
      numboxes 4), every belt item (mode 2) in box 4 or above leaves the belt: to page 0 at the cell the search gives
      (tools/item_inventory.py spot_find, a player's page, 1x1 items in box order) when page 0 has room, else to the
      ground (an IPG line for its id before BOV1); boxes 0..3 stay. --room / --full state which recipe the log is.
xs    player/0002 § 4 (backlog a68-review exp-state kill), from XK0 (kxs, vxs) and the XS lines of tools/gdb/player.py:
      for a monster killer, the credit is the MonsterOwner result (XSO), replaced by the owner GameFindUnit returns
      (XSF) for the 0x800 list of the killer (XSK ≠ 0) and then of the victim (XSV ≠ 0, which wins, even a none); the
      return (XSR) is that unit if it is a player, else none. XSK ≠ 0 must equal a non-empty kxs, XSV ≠ 0 a non-empty
      vxs. Tags counted: state-killer, state-victim, state-both, none.
Prints SURVEY lines; exit 1 on a mismatch.
"""
import base64
import collections
import csv
import json
import math
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
PLAYER_BLOCK = 0x1C09
TYPES_TESTED = (0x4C, 0x51, 0x50)          # the order of 0x00562464..0x00562486 and 0x0054D28C..0x0054D2B6
BELT_NULL_BOXES = 4                         # belts.txt row 2 (default) numboxes, F6's null belt
CORPSE_BOV_RET = 0x0057F47F


def lines(path, tags):
    with open(path, errors="replace") as f:
        for n, line in enumerate(f, 1):
            tag, _, rest = line.rstrip("\n").partition(" ")
            if tag in tags:
                try:
                    yield n, tag, json.loads(rest)
                except ValueError:
                    continue


def table(excel, name):
    with open(os.path.join(excel, name), encoding="latin1") as fh:
        rows = list(csv.reader(fh, delimiter="\t"))
    return rows[0], rows[1:]


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


# ------------------------------------------------------------------------------------------------------------ P12 pick
def grid(path, lid):
    cells = {}
    for _n, _t, d in lines(path, ("CB",)):
        if d.get("lid") != lid or not d.get("z"):
            continue
        c = json.loads(zlib.decompress(base64.b64decode(d["z"])))["cells"]
        if not c or not c[4]:
            continue
        x0, y0, w, h, hx = c
        raw = bytes.fromhex(hx)
        for i in range(w * h):
            cells[(x0 + i % w, y0 + i // w)] = raw[2 * i] | raw[2 * i + 1] << 8
    return cells


def last_pos(path, lid=None):
    pos = None
    for _n, _t, d in lines(path, ("PLR",)):
        if lid is None or d.get("lid") == lid:
            pos = (d["x"], d["y"], d["lid"])
    return pos


def first_pos(path, lid):
    for _n, _t, d in lines(path, ("PLR",)):
        if d.get("lid") == lid:
            return (d["x"], d["y"], lid)
    return None


def standable(cells, x, y):
    return all((x + dx, y + dy) in cells and cells[(x + dx, y + dy)] & PLAYER_BLOCK == 0
               for dx in (-1, 0, 1) for dy in (-1, 0, 1))


def beyond_free(cells, x, y, s, r):
    """The cells between the stand cell s and (x, y), and the r cells past (x, y) on that line, are in the grid with
    c & 5 == 0: the missile reaches the cell over free ground and, crossing it, would land on free ground (an obstacle
    inside the level, not its edge)."""
    ux, uy = (x - s[0]) // r, (y - s[1]) // r
    return all(cells.get((x + k * ux, y + k * uy), 5) & 5 == 0 for k in range(-r + 1, r + 1) if k)


def pick(path, lid=2, near_player=False, cells=None):
    cells = grid(path, lid) if cells is None else cells
    origin = last_pos(path, lid) if near_player else first_pos(path, lid)
    if not cells or not origin:
        return None
    b1 = [k for k, v in cells.items() if v & 5 == 1]
    # a word of exactly 0x0001 first (bit 0 alone), then any c & 5 == 1, each nearest first
    for (x, y) in sorted(b1, key=lambda k: (cells[k] != 1, math.hypot(k[0] - origin[0], k[1] - origin[1]), k)):
        for r in range(2, 6):
            ring = [(x + dx, y + dy) for dy in (-r, 0, r) for dx in (-r, 0, r) if (dx, dy) != (0, 0)]
            ok = [s for s in ring if standable(cells, *s) and beyond_free(cells, x, y, s, r)]
            if ok:
                s = min(ok, key=lambda s: (math.hypot(s[0] - origin[0], s[1] - origin[1]), s))
                return {"cell": [x, y], "v": cells[(x, y)], "stand": list(s), "r": r, "from": list(origin[:2]),
                        "lid": lid, "bit0only": len(b1), "cells": len(cells)}
    return None


# ------------------------------------------------------------------------------------------------------------ P12 check
def check_p12(paths):
    S = collections.Counter()
    bad = []
    for path in paths:
        cells = {}
        for lid in {d.get("lid") for _n, _t, d in lines(path, ("PLR",))}:
            cells.update(grid(path, lid))
        evs = list(lines(path, ("MMC", "MMR")))
        later = collections.defaultdict(list)       # mid -> MMC indexes
        for k, (_n, t, d) in enumerate(evs):
            if t == "MMC":
                later[d["mid"]].append(k)
        for k, (n, t, d) in enumerate(evs):
            if t != "MMC":
                continue
            mid, c = d["mid"], d["c"]
            nxt = next((e for e in evs[k + 1:] if e[2].get("mid") == mid), None)
            again = any(j > k for j in later[mid])
            kind = "bit0only" if c & 5 == 1 else "bit2" if c & 4 else "free"
            fresh = "fresh" if not d.get("cached") else "cached"
            S["MMC %s (%s)" % (kind, fresh)] += 1
            where = "%s:%d" % (path, n)
            g = cells.get((d["x"], d["y"]))
            if g is not None and g & 5 == 1 and c & 5 == 0:
                # The lead's observable: the missile is at a point whose grid word is bit-0-only. The logged c has been
                # through CollisionTest over size sz (the cell word & 0x7FFF, or the plus / square of it: always
                # including the own cell) or came from the path's cache (another point's word), so it is not the grid's
                # own word (review of plan 0065 P0, fix 1). A fresh 0 contradicts the grid (or the grid is stale there);
                # a cached 0 never tested this cell and separates nothing.
                S["LEAD-OUTCOME at a grid bit-0-only point, word c&5=0 (%s), %s" %
                  (fresh, "the missile steps again" if again else "no later step")] += 1
                if fresh == "fresh" and again:
                    S["LEAD-OUTCOME fresh: carried on over a grid bit-0-only cell"] += 1
            if kind == "free":
                if nxt and nxt[1] == "MMR" and nxt[2]["r"] == 2:
                    S["free word, then MMR 2 by another exit (no room/path, no filter or a wall hit)"] += 1
                elif again:
                    S["free word, the missile steps again (control)"] += 1
                continue
            freed = nxt is not None and nxt[1] == "MMR" and nxt[2]["r"] == 2 and not again
            if not freed:
                bad.append("%s %s word 0x%04x of missile %d: %s" % (where, kind, c, mid,
                                                                  "steps again" if again else "no MMR 2 after it"))
                continue
            S["%s word: freed at its own cell (D3)" % kind] += 1
            if kind == "bit0only":
                S["bit0only freed, the session's CB grid at (x, y): %s" %
                  ("absent" if g is None else "bit 0 set" if g & 1 else "bit 0 clear")] += 1
                # separating only when the grid's own cell is bit-0-only too: with size 2 or 3 the word also holds
                # the neighbours' bits, so a clear own cell leaves the bit to a neighbour
                if fresh == "fresh" and g is not None and g & 5 == 1:
                    S["SEPARATING: bit0only fresh word freed"] += 1
    sep = S["SEPARATING: bit0only fresh word freed"]
    lead = S["LEAD-OUTCOME fresh: carried on over a grid bit-0-only cell"]
    for b in bad:
        print("MISMATCH " + b)
    verdict = ("against D3" if bad else "against the grid reading (lead outcome seen)" if lead else
               "D3 holds" if sep else "not separated (no fresh bit-0-only word)")
    print("SURVEY sweep8 p12 logs=%d mmc=%d separating=%d lead=%d mismatches=%d verdict=%s" %
          (len(paths), sum(v for k, v in S.items() if k.startswith("MMC ")), sep, lead, len(bad), verdict))
    for k, v in sorted(S.items()):
        print("  %-90s %d" % (k, v))
    return 1 if bad or lead else 0


# ------------------------------------------------------------------------------------------------------------ C2
def missile_row(excel, name):
    h, rows = table(excel, "missiles.txt")
    r = next(r for r in rows if r[h.index("Missile")] == name)
    return {"id": int(r[h.index("Id")]), "vel": int(r[h.index("Vel")]), "vellev": int(r[h.index("VelLev")])}


def c2_vel(row, lvl):
    v = (tdiv(row["vellev"] * lvl, 8) + row["vel"]) << 8
    return tdiv(v * 75, 100) if v else 0


def c2_lead(row, lvl):
    v = (row["vellev"] * (lvl - 1) + row["vel"]) << 8
    return tdiv(v * 75, 100) if v else 0


def check_c2(paths, excel):
    import struct
    row = missile_row(excel, "spike1")
    S = collections.Counter()
    bad = []
    for path in paths:
        open0 = {}
        for n, t, d in lines(path, ("MC0", "MC1")):
            if t == "MC0":
                blk = bytes.fromhex(d["p"])
                f = struct.unpack_from("<I", blk, 0)[0]
                cls = struct.unpack_from("<i", blk, 0x10)[0]
                lvl = struct.unpack_from("<i", blk, 0x30)[0]
                if cls == row["id"]:
                    open0[d["n"]] = (f, lvl, n)
                continue
            got = open0.pop(d.get("k"), None)
            if not got or not d.get("m"):
                continue
            f, lvl, n0 = got
            if f & 4:
                S["spike1 with the caller's velocity (flags bit 2): not a C2 case"] += 1
                continue
            v = ((d["m"].get("path") or {}).get("v"))
            want, lead = c2_vel(row, lvl), c2_lead(row, lvl)
            S["spike1 at level %d" % lvl] += 1
            if v != want:
                bad.append("%s:%d spike1 level %d velocity %s, predicted %d (lead %d)" % (path, n0, lvl, v, want, lead))
            elif want != lead:
                S["SEPARATING: spike1 velocity as read, not the lead's"] += 1
    sep = S["SEPARATING: spike1 velocity as read, not the lead's"]
    for b in bad:
        print("MISMATCH " + b)
    print("SURVEY sweep8 c2 logs=%d spike1=%d separating=%d mismatches=%d" %
          (len(paths), sum(v for k, v in S.items() if k.startswith("spike1 at")), sep, len(bad)))
    for k, v in sorted(S.items()):
        print("  %-90s %d" % (k, v))
    return 1 if bad else 0


# ------------------------------------------------------------------------------------------------------------ H2
def check_h2(paths):
    S = collections.Counter()
    bad = []
    for path in paths:
        rate = {}            # (list, stat) -> the rate the last USS set
        freed = set()        # states whose list was freed since the last use
        cur = None           # the open use: URM line, the last UDV v
        for n, t, d in lines(path, ("URM", "UDV", "UBL", "USS", "UFL", "UFM")):
            where = "%s:%d" % (path, n)
            if t == "URM":
                cur = {"urm": d, "v": None, "n": n}
                if d["state"] in freed:
                    freed.discard(d["state"])
                    S["use after a free"] += 1
                    if d["list"]:
                        bad.append("%s state %d: a list found after its free" % (where, d["state"]))
                S["use, list %s" % ("alive (blend)" if d["list"] and d["rem"] > 0 else "none (fresh)")] += 1
            elif t == "UDV" and cur:
                cur["v"] = d["v"]
            elif t == "UBL" and cur:
                u = cur["urm"]
                old = rate.get((d["list"], d["stat"]))
                if not u["list"]:
                    # a use with no list: the blend step runs on the list the use just made (UBL's list is that new
                    # one), numerator v, denominator len, rate trunc(v / len) (smoke session, plan 0065 Phase 1)
                    if cur["v"] is None or d["num"] != cur["v"] or d["den"] != u["len"]:
                        bad.append("%s fresh UBL num %d den %d, predicted %s, %d" % (where, d["num"], d["den"],
                                                                                   cur["v"], u["len"]))
                    else:
                        cur["fresh"] = tdiv(cur["v"], u["len"])
                    continue
                if d["list"] != u["list"]:
                    bad.append("%s UBL on list %d, the use found %d" % (where, d["list"], u["list"]))
                    continue
                if old is None or cur["v"] is None:
                    S["UBL with no earlier rate or no UDV (not predicted)"] += 1
                    continue
                if d["num"] != old * u["rem"] + cur["v"] or d["den"] != u["len"] + u["rem"]:
                    bad.append("%s UBL num %d den %d, predicted %d, %d" % (where, d["num"], d["den"],
                                                                         old * u["rem"] + cur["v"], u["len"] + u["rem"]))
                    continue
                cur["blend"] = (tdiv(d["num"], d["den"]), tdiv(cur["v"], u["len"]))
            elif t == "USS":
                if cur and cur.get("fresh") is not None:
                    want = cur.pop("fresh")
                    if d["rate"] != want:
                        bad.append("%s USS rate %d, fresh trunc(v / len) %d" % (where, d["rate"], want))
                    else:
                        S["fresh rate as predicted"] += 1
                if cur and cur.get("blend") is not None:
                    want, alt = cur.pop("blend")
                    if d["rate"] != want:
                        bad.append("%s USS rate %d, blend predicted %d" % (where, d["rate"], want))
                    else:
                        S["blend rate as predicted"] += 1
                        if want != alt:
                            S["SEPARATING: blend differs from v / len"] += 1
                rate[(d["list"], d["stat"])] = d["rate"]
            elif t in ("UFL", "UFM"):
                freed.add(100 if t == "UFL" else 106)
                S["%s free at the maximum" % t] += 1
    sep = S["SEPARATING: blend differs from v / len"]
    for b in bad:
        print("MISMATCH " + b)
    print("SURVEY sweep8 h2 logs=%d blends=%d separating=%d frees=%d mismatches=%d" %
          (len(paths), S["blend rate as predicted"], sep, S["UFL free at the maximum"] + S["UFM free at the maximum"],
           len(bad)))
    for k, v in sorted(S.items()):
        print("  %-90s %d" % (k, v))
    return 1 if bad else 0


# ------------------------------------------------------------------------------------------------------------ H3
def item_codes(excel):
    out = []
    for n in ("weapons", "armor", "misc"):
        h, rows = table(excel, n + ".txt")
        for r in rows:
            code = r[h.index("code")]
            if code and code != "Expansion":
                out.append((code, r[h.index("type")]))
    return out


def type_closure(excel):
    """item type code -> the set of ItemTypes row indices ITEMS_UnitIsType passes (the type and its Equiv closure),
    rows counted without the 'Expansion' marker (items/0017 H3)."""
    h, rows = table(excel, "itemtypes.txt")
    rows = [r for r in rows if r[0] != "Expansion"]
    idx = {r[h.index("Code")]: k for k, r in enumerate(rows) if r[h.index("Code")]}
    eq = {r[h.index("Code")]: [r[h.index("Equiv1")], r[h.index("Equiv2")]] for r in rows if r[h.index("Code")]}

    def close(c, seen):
        if c in seen or c not in idx:
            return seen
        seen.add(c)
        for e in eq[c]:
            close(e, seen)
        return seen
    return {c: {idx[x] for x in close(c, set())} for c in idx}


def h3_expect(code_type, closure):
    """[(type, result)] in test order, stopping at the first pass; and whether the item passes."""
    out = []
    for ty in TYPES_TESTED:
        r = ty in closure.get(code_type, set())
        out.append((ty, r))
        if r:
            return out, True
    return out, False


def check_h3(paths, excel):
    codes = item_codes(excel)
    closure = type_closure(excel)
    S = collections.Counter()
    bad = []
    for path in paths:
        ev = list(lines(path, ("T26", "T26A", "T26B", "T26C", "T26P", "T61", "T61A", "T61B", "T61C", "IU0")))
        for k, (n, t, d) in enumerate(ev):
            where = "%s:%d" % (path, n)
            if t == "T26":
                it = d.get("item") or {}
                code, ty = codes[it["c"]] if 0 <= it.get("c", -1) < len(codes) else ("?", "?")
                if not d["flag"] or d["pt"] != 0 or not d["exp"]:
                    S["0x26 without the flag (or not expansion): %s" % code] += 1
                    continue
                want, passes = h3_expect(ty, closure)
                tail = []
                for e in ev[k + 1:]:
                    if e[1] == "T26":
                        break
                    tail.append(e)
                got = [(e[2]["type"], bool(e[2]["r"])) for e in tail if e[1] in ("T26A", "T26B", "T26C")]
                iu = [e for e in tail if e[1] == "IU0" and (e[2].get("item") or {}).get("id") == it["id"]]
                merc = [e for e in iu if (e[2].get("user") or {}).get("t") == 1]
                if got != want:
                    bad.append("%s 0x26 %s: tests %s, predicted %s" % (where, code, got, want))
                elif passes and not merc:
                    bad.append("%s 0x26 %s passes but no ItemUse with the hireling as user" % (where, code))
                elif not passes and iu:
                    bad.append("%s 0x26 %s refused but ItemUse reached" % (where, code))
                else:
                    S["0x26 flagged %s: %s, as predicted" % (code, "to the hireling" if passes else "refused")] += 1
                    if code == "mp1" and not passes:
                        S["SEPARATING: mp1 refused (the lead gives it)"] += 1
            elif t == "T61A":
                grp = [e for e in ev[k:k + 3] if e[1] in ("T61A", "T61B", "T61C") and e[2]["iid"] == d["iid"]]
                S["0x61 tests %s" % [(e[2]["type"], bool(e[2]["r"])) for e in grp]] += 1
    sep = S["SEPARATING: mp1 refused (the lead gives it)"]
    for b in bad:
        print("MISMATCH " + b)
    print("SURVEY sweep8 h3 logs=%d flagged=%d separating=%d mismatches=%d" %
          (len(paths), sum(v for k, v in S.items() if k.startswith("0x26 flagged")), sep, len(bad)))
    for k, v in sorted(S.items()):
        print("  %-90s %d" % (k, v))
    return 1 if bad else 0


# ------------------------------------------------------------------------------------------------------------ B8
def b8_expect(inv, room):
    """The predicted moves of F6 for a BOV0 item list: {item id: (page, x, y) or 'ground'} for boxes >= 4, in box order;
    and the ids of boxes 0..3 that stay."""
    import item_inventory as ii
    belt = sorted((r for r in inv if isinstance(r, list) and r[5] == 2), key=lambda r: r[3])
    g = ii.InvGrid(10, 4, [(r[4], r[3]) for r in inv if isinstance(r, list) and r[2] == 0 and r[5] == 0])
    moves, stay = {}, []
    for r in belt:
        if r[3] < BELT_NULL_BOXES:
            stay.append(r[0])
            continue
        at = ii.spot_find(g, 1, 1, True) if room else None
        if at:
            g.cell[at[1]][at[0]] = 1
            moves[r[0]] = (0, at[0], at[1])
        else:
            moves[r[0]] = "ground"
    return moves, stay


def check_b8(paths, room):
    S = collections.Counter()
    bad = []
    for path in paths:
        ev = list(lines(path, ("CCR", "CCN", "CMB", "BOV0", "BOV1", "IPG")))
        for k, (n, t, d) in enumerate(ev):
            if t == "CCN":
                S["corpse path: %s" % ("CorpseOverflowDrop (count > 15)" if d["n"] > 15 else "the slot loop")] += 1
            if t != "BOV0" or d["ret"] != CORPSE_BOV_RET:
                if t == "BOV0":
                    S["BOV0 from another caller (ret 0x%08X)" % d["ret"]] += 1
                continue
            where = "%s:%d" % (path, n)
            if d["belt"] != 0:
                bad.append("%s corpse BeltOverflow with a belt word %d" % (where, d["belt"]))
            moves, stay = b8_expect(d["inv"], room)
            after = next((e for e in ev[k + 1:] if e[1] == "BOV1"), None)
            if not after:
                bad.append("%s no BOV1" % where)
                continue
            ground = {e[2]["item"]["id"] for e in ev[k + 1:ev.index(after)] if e[1] == "IPG" and e[2].get("item")}
            inv1 = {r[0]: r for r in after[2]["inv"] if isinstance(r, list)}
            for iid, m in moves.items():
                if m == "ground":
                    ok = iid in ground and (iid not in inv1 or inv1[iid][5] != 2)
                else:
                    r = inv1.get(iid)
                    ok = r is not None and (r[2], r[3], r[4]) == m and r[5] == 0
                if not ok:
                    bad.append("%s item %d predicted %s, after: %s%s" % (where, iid, m, inv1.get(iid),
                                                                       " (IPG)" if iid in ground else ""))
                else:
                    S["box >= 4 item %s, as predicted" % ("to the ground" if m == "ground" else "to page 0")] += 1
            for iid in stay:
                r = inv1.get(iid)
                S["box 0..3 item %s after BOV1" % ("still in the belt" if r and r[5] == 2 else "moved")] += 1
            S["corpse BeltOverflow calls"] += 1
    for b in bad:
        print("MISMATCH " + b)
    print("SURVEY sweep8 b8 logs=%d calls=%d moved=%d mismatches=%d" %
          (len(paths), S["corpse BeltOverflow calls"],
           sum(v for k, v in S.items() if k.startswith("box >= 4")), len(bad)))
    for k, v in sorted(S.items()):
        print("  %-90s %d" % (k, v))
    return 1 if bad else 0


# ------------------------------------------------------------------------------------------------------------ XS
def check_xs(paths):
    S = collections.Counter()
    bad = []
    tags = ("XK0", "XSO", "XSK", "XSKL", "XSV", "XSVL", "XSL", "XSG", "XSF", "XSR")
    for path in paths:
        ev = list(lines(path, tags))
        for k, (n, t, d) in enumerate(ev):
            if t != "XK0" or d.get("ktype") != 1:
                continue
            where = "%s:%d" % (path, n)
            steps = {}
            for e in ev[k + 1:]:
                if e[1] == "XK0" or (e[1] == "XSR" and "XSR" in steps):
                    break
                if e[2].get("th") == d.get("th"):
                    steps[e[1]] = e[2]["r"]
                if e[1] == "XSR":
                    break
            if "XSR" not in steps:
                S["monster kill with no XpCreditPlayer steps (not credited through G0)"] += 1
                continue
            kxs, vxs = d.get("kxs"), d.get("vxs")
            if bool(steps.get("XSK")) != bool(kxs):
                bad.append("%s XSK %s against kxs %s" % (where, steps.get("XSK"), kxs))
            if "XSV" in steps and bool(steps["XSV"]) != bool(vxs):
                bad.append("%s XSV %s against vxs %s" % (where, steps.get("XSV"), vxs))
            s = None
            if steps.get("XSK"):
                s = steps.get("XSKL")
            if steps.get("XSV"):
                s = steps.get("XSVL")
            owner = steps.get("XSF") if s else steps.get("XSO")
            want = owner if owner and owner[0] == 0 else None
            if steps["XSR"] != want:
                bad.append("%s credit %s, predicted %s" % (where, steps["XSR"], want))
                continue
            tag = ("state-both" if kxs and vxs else "state-killer" if kxs else "state-victim" if vxs else "no state")
            S["%s: credit %s" % (tag, "a player" if want else "none")] += 1
            if tag != "no state" and want and not (steps.get("XSO") and steps["XSO"][0] == 0):
                S["SEPARATING: credited through the 0x800 list, MonsterOwner gave no player"] += 1
    sep = S["SEPARATING: credited through the 0x800 list, MonsterOwner gave no player"]
    for b in bad:
        print("MISMATCH " + b)
    print("SURVEY sweep8 xs logs=%d state_kills=%d separating=%d mismatches=%d" %
          (len(paths), sum(v for k, v in S.items() if k.startswith("state-")), sep, len(bad)))
    for k, v in sorted(S.items()):
        print("  %-90s %d" % (k, v))
    return 1 if bad else 0


# ------------------------------------------------------------------------------------------------------------ predict
def predict(excel):
    import item_inventory as ii
    out = []
    row = missile_row(excel, "spike1")
    out.append("C2 spike1 (Missiles row %d, Vel %d, VelLev %d): velocity as read / the lead's, by level" %
               (row["id"], row["vel"], row["vellev"]))
    for lvl in range(1, 6):
        out.append("  level %d: %d / %d" % (lvl, c2_vel(row, lvl), c2_lead(row, lvl)))
    codes = item_codes(excel)
    closure = type_closure(excel)
    types = dict(codes)
    out.append("H3 flagged 0x26 (and 0x61), ITEMS_UnitIsType for 0x4C, 0x51, 0x50 in order:")
    for c in ("mp1", "hp1", "rvs", "yps", "wms"):
        want, passes = h3_expect(types[c], closure)
        out.append("  %s (type %s): %s -> %s" % (c, types[c], want, "the hireling uses it" if passes else "refused"))
    h, rows = table(excel, "misc.txt")
    misc = {r[h.index("code")]: r for r in rows}
    out.append("H2 fresh rates for a Sorceress (class 1), not doubled / doubled: total and trunc(total / len)")
    for c in ("hp1", "hp2", "hp4", "hp5", "mp1", "mp2", "mp3", "mp4", "mp5"):
        r = misc[c]
        stat, calc, ln = r[h.index("stat1")], int(r[h.index("calc1")]), int(r[h.index("len")])
        st = ii.MANAREC if stat == "manarecovery" else None
        t0, t1 = ii.potion_total(1, st, calc), ii.potion_total(1, st, calc, True)
        out.append("  %s %s calc %d len %d: %d -> %d / %d -> %d" % (c, stat, calc, ln, t0, tdiv(t0, ln), t1, tdiv(t1, ln)))
    out.append("H2 blend (second use with the first list alive): trunc((old * rem + v) / (len + rem)); the wrong reading "
               "trunc(v / len); rem is logged (URM)")
    for room, label in ((True, "b8room"), (False, "b8full")):
        inv = [[100 + b, 0, None, b, 0, 2, None] for b in range(16)]
        if not room:
            inv += [[200 + k, 0, 0, k % 10, k // 10, 0, None] for k in range(40)]
        moves, stay = b8_expect(inv, room)
        out.append("B8 %s: boxes 0..3 stay; boxes 4..15 -> %s" %
                   (label, [moves[100 + b] for b in range(4, 16)]))
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, rest = argv[1], argv[2:]
    excel = EXCEL
    if "--excel" in rest:
        k = rest.index("--excel")
        excel = rest[k + 1]
        rest = rest[:k] + rest[k + 2:]
    if cmd == "predict":
        print("\n".join(predict(excel)))
        return 0
    if cmd == "pick":
        lid = 2
        if "--lid" in rest:
            k = rest.index("--lid")
            lid = int(rest[k + 1])
            rest = rest[:k] + rest[k + 2:]
        near = "--near-player" in rest
        paths = [a for a in rest if a != "--near-player"]
        print(json.dumps(pick(paths[0], lid, near)))
        return 0
    paths = [a for a in rest if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 2
    if cmd == "p12":
        return check_p12(paths)
    if cmd == "c2":
        return check_c2(paths, excel)
    if cmd == "h2":
        return check_h2(paths)
    if cmd == "h3":
        return check_h3(paths, excel)
    if cmd == "b8":
        if ("--room" in rest) == ("--full" in rest):
            print("b8 needs --room or --full")
            return 2
        return check_b8(paths, "--room" in rest)
    if cmd == "xs":
        return check_xs(paths)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
