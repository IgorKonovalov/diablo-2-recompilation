#!/usr/bin/env python3
"""Plan 0067 Phase 2: the player-trade checker. It replays a host log of tools/gdb/two-trade.gdb through the rules of
docs/findings/multiplayer/0003-trade.md §§ 2-10 and checks each case of § 11 (T1-T13) against its prediction.

Usage:
  python3 -I tools/trade_check.py check <host.log> [--excel DIR] [--marks FILE] [--case T1] [-v]
  python3 -I tools/trade_check.py mark <host.log> <case> [start|end|fail] [--note TEXT]
  python3 -I tools/trade_check.py layout <excel-dir> [--seed N] [--trials N] [--show K]
  python3 -I tools/trade_check.py cases

check   every event line is checked against its rule (R-*), and each case (a segment of the log cut at the `start`
        marks of <log stem>.marks.tsv, or the whole log under --case) against its expectations (E-*). Prints one
        line per mismatch ("MISMATCH <case> <line> <rule>: ...") and per unmet expectation ("UNMET <case> <E-...>"),
        then "CASE <case>: ..." per case and a final "TRADE-CHECK events=... checks=... mismatches=... unmet=..."
        line. --excel gives the item sizes and codes (weapons, armor, misc) that the room test, the placements and
        the item tests need; without it those checks are skipped and counted as such. Exit 0 only with 0 mismatches
        and every expectation met.
mark    appends a case mark to <log stem>.marks.tsv (tools/harness_runner.py mark: the log's line count at that
        moment), so `check` cuts the host log per case. The harness lane marks `start` just before a case's first
        action.
layout  the T13 search (plan 0067 Phase 2 preparation): is there a page-0 layout and a page-2 offer where the
        commit's room test (FIRST, the scratch inventory's owner 0) and the real placement (BEST, a player's page)
        disagree? A seeded random search over layouts built from the item sizes of the three item tables, with every
        order of the offer tried; prints the counts per kind and the smallest examples with their grids.
cases   prints the case list with each case's expectations.

Models (pure, tested by tools/test_trade_check.py): the B1 search is tools/item_inventory.py's spot_find
(items/inventory B1-B4); place_seq() places an offer one item at a time and marks the cells as the scratch
(0x0063E1C0) and InvPlaceItem do. Stdlib only.
"""
import itertools
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import item_inventory as ii  # noqa: E402

INV_W, INV_H = 10, 4          # inventory.txt: the class rows and "Trade Page 1" are 10 x 4 (gridX, gridY)
GOLD_PER_LEVEL = 10000        # PLAYER_GoldCap 0x00622E70 (items/economy G2)
U32 = 0xFFFFFFFF

# The return addresses of TradeCommit's calls to TradeCancel (fn:sub_00567C70_TradeCommit), each one cancel reason.
CANCEL_SITES = {
    0x00567CA8: "gold A < offer A", 0x00567CE0: "B's cap passed by offer A",
    0x00567D51: "gold B < offer B", 0x00567D86: "A's cap passed by offer B",
    0x00567E41: "room test side 1", 0x00567E86: "room test side 0",
    0x00567F32: "move A to B failed", 0x00568050: "quest gate or move B to A failed",
}
TQX_EXIT = {0x00566ED8: "ev8", 0x00566F0D: "ev9-named", 0x00566F55: "ev9", 0x00567000: "open", 0x00567015: "none"}
TIT_MAIN = 0x00567826
TIT_LOCKED = 0x0056768E
# The tick (fn:sub_005689D0_TradeStateTick): state -> the next states it may write, and the frames to the next tick of
# that player it queues (None: none queued).
TICK = {5: ({6}, 1), 6: ({3}, None), 7: ({8}, 1), 9: ({10}, 1), 10: ({0}, None), 12: ({13}, 4), 13: ({0}, None),
        14: ({15}, 1), 15: ({16}, 5)}


# ---- the placement models -------------------------------------------------------------------------------------

def grid_from(rects, w=INV_W, h=INV_H):
    """A page from item rectangles [(col, row, iw, ih), ...]."""
    g = ii.InvGrid(w, h)
    for c, r, iw, ih in rects:
        for y in range(r, r + ih):
            for x in range(c, c + iw):
                g.cell[y][x] = 1
    return g


def copy_grid(g):
    n = ii.InvGrid(g.w, g.h)
    n.cell = [row[:] for row in g.cell]
    return n


def place_seq(g, sizes, player):
    """Place sizes [(w, h), ...] one after another into a copy of g, as InvScratchFitOffer (player False: the scratch's
    owner word is 0, FIRST) or TradeMoveItems' InvPlaceItem (player True: BEST) do. Returns (spots, grid): spots[k] is
    (col, row) or None; the first None stops the scratch (0x0063E34F) and fails the move (0x00567194), so later items
    are not placed."""
    g = copy_grid(g)
    spots = []
    for w, h in sizes:
        at = ii.spot_find(g, w, h, player)
        spots.append(at)
        if at is None:
            break
        c, r = at
        for y in range(r, r + h):
            for x in range(c, c + w):
                g.cell[y][x] = 1
    return spots, g


def fits_all(spots, n):
    return len(spots) == n and all(s is not None for s in spots)


def room_test(grid_a, offer_a, grid_b, offer_b):
    """TradeRoomTest(A, B): A's offer into a FIRST copy of B's page 0, then B's into A's. Returns (ok, side, spots_ab,
    spots_ba); side is 0 when A's offer failed, 1 when B's failed, None when both fit (0x0063E437, 0x0063E458)."""
    s_ab, _ = place_seq(grid_b, offer_a, False)
    if not fits_all(s_ab, len(offer_a)):
        return False, 0, s_ab, []
    s_ba, _ = place_seq(grid_a, offer_b, False)
    if not fits_all(s_ba, len(offer_b)):
        return False, 1, s_ab, s_ba
    return True, None, s_ab, s_ba


def gold_after(gold_a, gold_b, off_a, off_b):
    """The commit's gold moves (0x00567F4A-0x00567FCC): A's offer leaves A (only when A holds at least that much, `jl`)
    and reaches B (0x0055B060), then B's the same way."""
    if off_a:
        if gold_a >= off_a:
            gold_a -= off_a
        gold_b += off_a
    if off_b:
        if gold_b >= off_b:
            gold_b -= off_b
        gold_a += off_b
    return gold_a, gold_b


def clip_offer(amount, gold_q, lvl_q):
    """Button 8 (0x005683DC-0x00568497): the amount clipped to the partner's room under its cap (unsigned compare)."""
    cap = GOLD_PER_LEVEL * lvl_q
    if ((gold_q + amount) & U32) > cap:
        return (cap - gold_q) & U32
    return amount & U32


def s32(v):
    v &= U32
    return v - (1 << 32) if v & 0x80000000 else v


# ---- excel ------------------------------------------------------------------------------------------------------

class Items:
    """Item class index -> (code, w, h, quest), weapons, armor and misc in file order (rows with a code)."""

    def __init__(self, excel):
        import excel_bin
        self.rows = []
        for t in ("weapons", "armor", "misc"):
            hd, rows = excel_bin.read_txt(excel_bin.find_file(excel, t, ".txt"))
            ci, wi, hi, qi = hd.index("code"), hd.index("invwidth"), hd.index("invheight"), hd.index("quest")
            for r in rows:
                if r[ci]:
                    self.rows.append((r[ci].strip(), int(r[wi] or 1), int(r[hi] or 1),
                                      int(r[qi]) if r[qi].strip() else 0))

    def size(self, cls):
        return self.rows[cls][1:3]

    def code(self, cls):
        return self.rows[cls][0]

    def quest(self, cls):
        return self.rows[cls][3]


# ---- the log ----------------------------------------------------------------------------------------------------

TAGS = {"TRQ", "TRQR", "TQT", "TQN", "TQX", "TRB", "TRBR", "TRA", "TRO", "TIT", "TITR", "TBL", "TBLR", "TSO", "TSOR",
        "TSP", "THO", "THOR", "TCM", "TCMR", "TRT", "SCP", "TMP", "TMV", "TCX", "TCXR", "TCL", "TCLR", "TAB", "TABR",
        "TRS", "TRSR", "TTK", "TTKR", "TSV", "TSC", "TMS", "TG9", "TEV", "CRM", "TRDY"}   # tools/gdb/two-trade.py


def parse(path):
    """The two-trade lines of a host log (the other loggers' lines, PLRS and the rest, are skipped unparsed)."""
    out = []
    with open(path, errors="replace") as f:
        for k, ln in enumerate(f):
            tag, _, rest = ln.partition(" ")
            if tag not in TAGS or not rest.startswith("{"):
                continue
            try:
                out.append((k, tag, json.loads(rest)))
            except ValueError:
                continue
    return out


def by_id(d):
    return {p["id"]: p for p in d.get("pl", [])}


def page_items(inv, page):
    return [it for it in inv if isinstance(it, list) and it[2] == page]


def rects(inv, page, items):
    out = []
    for it in page_items(inv, page):
        w, h = items.size(it[1])
        out.append((it[3], it[4], w, h))
    return out


def layout_key(inv):
    """An inventory list as a multiset of (class, page, x, y, loc): what a restore from the snapshot gives back."""
    return sorted((it[1], it[2], it[3], it[4], it[6]) for it in inv if isinstance(it, list))


class Check:
    def __init__(self, items=None, verbose=False):
        self.items = items
        self.verbose = verbose
        self.n_checks = 0
        self.skipped = 0
        self.mismatches = []        # (case, line, rule, msg)
        self.seen = []              # (case, kind, data): what expectations read
        self.opening = {}           # player id -> inventory list at its record's allocation (TRA ok 1)
        self.case = "all"
        self.last_tick = {}         # player id -> (frame, state before, queued delay)

    def ok(self, line, rule, cond, msg):
        self.n_checks += 1
        if not cond:
            self.mismatches.append((self.case, line, rule, msg))
        return cond

    def note(self, kind, **d):
        self.seen.append((self.case, kind, d))

    # -- helpers
    def partner(self, p, pl):
        if p and p.get("ia") and p["ia"][2] and p["ia"][1] == 0:
            return pl.get(p["ia"][0])
        return None

    def restored(self, line, rule, pid, before_inv, after_inv):
        """After TradeReturnItems: the live list equals the opening snapshot's layout, and no item id of the list
        before survives (every unit is read anew from the bytes, § 9)."""
        if pid not in self.opening:
            self.skipped += 1
            return
        self.ok(line, rule + "/layout", layout_key(after_inv) == layout_key(self.opening[pid]),
                "player %s: list after the restore is not the opening layout" % pid)
        old = {it[0] for it in before_inv if isinstance(it, list)}
        new = {it[0] for it in after_inv if isinstance(it, list)}
        self.ok(line, rule + "/newids", not (old & new), "player %s: ids kept through the restore: %s" %
                (pid, sorted(old & new)[:8]))
        self.note("restore", pid=pid, newids=not (old & new))


def segments(events, marks_path, case=None):
    if case:
        return [(case, events)]
    if marks_path and os.path.exists(marks_path):
        import harness_runner as hr
        rows = [r for r in hr.read_marks(marks_path) if r["event"] == "start"]
        out = []
        for k, r in enumerate(rows):
            hi = rows[k + 1]["line"] if k + 1 < len(rows) else 1 << 60
            out.append((r["case"], [e for e in events if r["line"] <= e[0] < hi]))
        return out
    return [("all", events)]


def pair_after(evs, k, tag, key):
    """The first `tag` line after evs[k] whose `key` fields equal evs[k]'s (an entry's after line)."""
    d0 = evs[k][2]
    for j in range(k + 1, len(evs)):
        t, d = evs[j][1], evs[j][2]
        if t == tag and all(d.get(x) == d0.get(x) for x in key):
            return j
    return None


def between(evs, k, j, tag):
    return [e for e in evs[k + 1:j] if e[1] == tag]


def check_events(chk, evs):
    for k, (line, tag, d) in enumerate(evs):
        if tag == "TRA" and d.get("ok") == 1:
            chk.opening[d["p"]] = (d.get("inv") or {}).get(str(d["p"]), [])
        elif tag == "TRQ":
            check_request(chk, evs, k)
        elif tag == "TRB":
            check_button(chk, evs, k)
        elif tag == "TIT":
            check_itemtest(chk, evs, k)
        elif tag == "TSO":
            check_show(chk, evs, k)
        elif tag == "THO":
            check_hide(chk, evs, k)
        elif tag == "TCM":
            check_commit(chk, evs, k)
        elif tag == "TCX":
            check_cancel(chk, evs, k)
        elif tag == "TCL":
            check_close(chk, evs, k)
        elif tag == "TAB":
            check_abort(chk, evs, k)
        elif tag == "TTK":
            check_tick(chk, evs, k)
        elif tag == "TSC":
            check_save(chk, evs, k)
        elif tag == "TBL":
            j = pair_after(evs, k, "TBLR", ("p",))
            if j is not None:
                chk.note("belt", p=d["p"], eax=evs[j][2].get("eax"))


def check_request(chk, evs, k):
    line, _, d = evs[k]
    j = None
    for m in range(k + 1, len(evs)):
        if evs[m][1] == "TQX":
            j = m
            break
    if j is None:
        return
    exit_ = TQX_EXIT.get(evs[j][2]["pc"])
    a = pair_after(evs, k, "TRQR", ("req", "tgt"))
    tq = between(evs, k, j, "TQT")
    tqn = between(evs, k, j, "TQN")
    pb, pa = by_id(d), by_id(evs[a][2]) if a is not None else {}
    r0, g0 = pb.get(d["req"]), pb.get(d["tgt"])
    r1, g1 = pa.get(d["req"]), pa.get(d["tgt"])
    chk.note("request", exit=exit_ if not tqn else "town", t=tq[0][2]["t"] if tq else None)
    if not (r0 and g0 and r1 and g1):
        chk.skipped += 1
        return
    t = tq[0][2]["t"] if tq else None
    rule = "R-request"
    if exit_ == "open":
        chk.ok(line, rule + "/gates", r0["st"] == 0 and g0["st"] == 0 and t is not None and
               (t - g0["t58"]) & U32 >= 5000 and (t - r0["t58"]) & U32 >= 5000,
               "opened with states %s/%s or inside a 5 s end window" % (r0["st"], g0["st"]))
        chk.ok(line, rule + "/states", (r1["st"], g1["st"]) == (1, 2), "after the open: %s/%s, not 1/2" %
               (r1["st"], g1["st"]))
        chk.ok(line, rule + "/interact", r1["ia"][:2] == [g1["id"], 0] and g1["ia"][:2] == [r1["id"], 0],
               "interactions after the open: %s / %s" % (r1["ia"], g1["ia"]))
    elif exit_ in ("ev8", "ev9-named", "ev9"):
        ev = between(evs, k, j, "TEV")
        chk.ok(line, rule + "/event", any(e[2]["ev"] == (8 if exit_ == "ev8" else 9) for e in ev),
               "exit %s without its event message" % exit_)
        chk.ok(line, rule + "/rate", t is not None and r1["t54"] == t, "+0x54 after %s is %s, not t %s" %
               (exit_, r1["t54"], t))
        if exit_ == "ev8":
            chk.ok(line, rule + "/ev8", (t - r0["t54"]) & U32 > 1000, "event 8 inside the 1 s rate")
        elif exit_ == "ev9-named":
            chk.ok(line, rule + "/ev9n", (t - g0["t58"]) & U32 < 5000 and (r0["t54"] + 1000) & U32 < t,
                   "event 9 (named) outside the target's 5 s window or inside the rate")
        else:
            chk.ok(line, rule + "/ev9", r0["st"] == 0 and g0["st"] == 0 and (t - r0["t58"]) & U32 < 5000,
                   "event 9 (unnamed) with states %s/%s or outside the requester's window" % (r0["st"], g0["st"]))
        chk.ok(line, rule + "/nostate", (r1["st"], g1["st"]) == (r0["st"], g0["st"]), "a refused request moved a state")
    elif tqn:
        chk.ok(line, rule + "/town", r1["ia"][2] == 0 and g1["ia"][2] == 0 and (r1["st"], g1["st"]) == (0, 0),
               "out of town: interactions %s/%s, states %s/%s" % (r1["ia"], g1["ia"], r1["st"], g1["st"]))
    else:
        chk.ok(line, rule + "/nothing", (r1["st"], g1["st"], r1["t54"]) == (r0["st"], g0["st"], r0["t54"]),
               "the silent exit changed a state or the rate tick")


def blocked(p):
    return bool(p["b22"] or p["b23"])


def find_close(evs, k, j):
    return [e for e in between(evs, k, j, "TCL")]


def check_button(chk, evs, k):
    line, _, d = evs[k]
    j = pair_after(evs, k, "TRBR", ("p", "button", "param"))
    if j is None:
        return
    b, param = d["button"], d["param"]
    pb, pa = by_id(d), by_id(evs[j][2])
    p0 = pb.get(d["p"])
    q0 = chk.partner(p0, pb)
    if not p0 or not q0:
        return
    if b not in (2, 3, 4, 7, 8):
        if b in (5, 6) or (b > 8 and b not in (0x12, 0x13, 0x14, 0x17, 0x18)):   # stash and cube buttons apart
            p1, q1 = pa.get(p0["id"]), pa.get(q0["id"])
            chk.ok(line, "R-button/none", p1 and q1 and (p1["st"], q1["st"]) == (p0["st"], q0["st"]),
                   "button %d moved a state" % b)
        return
    p1, q1 = pa.get(p0["id"]), pa.get(q0["id"])
    if not p1 or not q1:
        chk.skipped += 1
        return
    closes = find_close(evs, k, j)
    rule = "R-button%d" % b
    chk.note("button", b=b, param=param, p=p0["id"], st=(p0["st"], q0["st"]), after=(p1["st"], q1["st"]),
             off=p1.get("off"), closes=[c[2]["code"] for c in closes], cur=p0["cur"])
    if b == 2:
        want = (p0["st"] in (1, 2) and q0["st"] in (1, 2)) or not (blocked(p0) or blocked(q0))
        chk.ok(line, rule + "/close", bool(closes) == want and (not closes or closes[0][2]["code"] == 9),
               "button 2: close %s, expected %s (code 9)" % ([c[2]["code"] for c in closes], want))
        if want:
            chk.ok(line, rule + "/t58", p1["t58"] == q1["t58"] and p1["t58"] != p0["t58"], "both +0x58 not set to t")
    elif b == 3:
        if blocked(p0) or blocked(q0):
            exp = {7: 14, 8: 15}.get(p0["st"])
            if exp:
                chk.ok(line, rule + "/blocked", p1["st"] == exp, "blocked press at %d: %d, not %d" %
                       (p0["st"], p1["st"], exp))
            else:
                chk.ok(line, rule + "/blocked", closes and closes[0][2]["code"] == 12, "blocked press: no close 12")
        elif p0["st"] == 2 and q0["st"] == 1:
            chk.ok(line, rule + "/open", (p1["st"], q1["st"]) == (3, 3) and p1["rec"] and q1["rec"],
                   "open: states %s/%s, records %s/%s" % (p1["st"], q1["st"], p1["rec"], q1["rec"]))
            for x0, x1 in ((p0, p1), (q0, q1)):
                if x1.get("rec"):
                    chk.ok(line, rule + "/record", (x1["g10"], x1["off"], x1["lk"]) == (x0["gold"], 0, 0) and
                           x1["r0"] > 0, "player %s record: g10 %s off %s lk %s r0 %s (gold %s)" %
                           (x0["id"], x1["g10"], x1["off"], x1["lk"], x1["r0"], x0["gold"]))
        else:
            chk.ok(line, rule + "/close12", closes and closes[0][2]["code"] == 12,
                   "button 3 at %d/%d: no close 12" % (p0["st"], q0["st"]))
    elif b == 4:
        if blocked(p0) or blocked(q0) or p0["st"] != 3 or p0["cur"]:
            chk.ok(line, rule + "/refusedmsg", any(e[2]["code"] == 6 for e in between(evs, k, j, "TMS")),
                   "refused accept without a 0x77 code 6")
            chk.ok(line, rule + "/refused", (p1["st"], q1["st"]) == (p0["st"], q0["st"]),
                   "refused accept (blocked %s, state %d, cursor %s) moved a state" % (
                       blocked(p0) or blocked(q0), p0["st"], p0["cur"]))
        elif q0["st"] == 4:
            chk.ok(line, rule + "/commit", any(e[1] == "TCM" and e[2]["a"] == p0["id"] and e[2]["b"] == q0["id"]
                                               for e in evs[k + 1:j]), "both at 4 and no commit with A = presser")
        else:
            chk.ok(line, rule + "/accept", (p1["st"], q1["st"]) == (4, q0["st"]), "accept: %s/%s" %
                   (p1["st"], q1["st"]))
    elif b == 7:
        exp = (3 if p0["st"] == 4 else p0["st"], 3 if q0["st"] == 4 else q0["st"])
        chk.ok(line, rule, (p1["st"], q1["st"]) == exp, "button 7: %s/%s, not %s" % (p1["st"], q1["st"], exp))
    elif b == 8:
        if p0["gold"] is not None and p0["gold"] < param and not (blocked(p0) or blocked(q0)):
            chk.ok(line, rule + "/overspend", closes and closes[0][2]["code"] == 9, "overspend without a close 9")
            chk.note("overspend", p=p0["id"])
        else:
            chk.ok(line, rule + "/nostate", (p1["st"], q1["st"]) == (p0["st"], q0["st"]),
                   "a gold offer moved a state: %s/%s -> %s/%s" % (p0["st"], q0["st"], p1["st"], q1["st"]))
            if p0.get("rec") and q0["gold"] is not None and q0["lvl"]:
                want = s32(clip_offer(param, q0["gold"], q0["lvl"]))
                chk.ok(line, rule + "/clip", p1.get("off") == want, "offer stored %s, clip model %s (param %d)" %
                       (p1.get("off"), want, param))
                chk.note("offer", p=p0["id"], param=param, off=p1.get("off"), clipped=want != param,
                         partner_st=q0["st"])


def item_code(chk, it):
    return chk.items.code(it[1]) if chk.items and it else None


def check_itemtest(chk, evs, k):
    line, _, d = evs[k]
    j = None
    for m in range(k + 1, len(evs)):
        if evs[m][1] == "TITR":
            j = m
            break
    if j is None:
        return
    r = evs[j][2]
    pb, pa = by_id(d), by_id(r)
    p0 = pb.get(d["p"])
    q0 = chk.partner(p0, pb)
    chk.note("itemtest", pc=r["pc"], eax=r["eax"], p=d["p"], code=item_code(chk, d.get("item")),
             st=(p0 or {}).get("st"), pst=(q0 or {}).get("st"))
    if not p0 or not q0:
        return
    p1, q1 = pa.get(p0["id"]), pa.get(q0["id"])
    rule = "R-itemtest"
    if r["pc"] == TIT_LOCKED:
        chk.ok(line, rule + "/locked", r["eax"] == 0 and (not q0["rec"] or p0["b23"] or q0["b23"]),
               "early refusal with eax %s, partner record %s, bits23 %s/%s" % (r["eax"], q0["rec"], p0["b23"],
                                                                            q0["b23"]))
        return
    if r["pc"] != TIT_MAIN:
        return
    chk.ok(line, rule + "/states", p1 and q1 and (p1["st"], q1["st"]) == (7, 7) and p1["b22"] == 1,
           "after the change lock: %s/%s, bit 22 %s" % (p1 and p1["st"], q1 and q1["st"], p1 and p1["b22"]))
    it = d.get("item")
    if chk.items is None or not it:
        chk.skipped += 1
        return
    want = 1 if p0["st"] != 4 else 0
    code, quest = chk.items.code(it[1]), chk.items.quest(it[1])
    if quest:
        inv = d.get("inv", {})
        if code == "box" and page_items(inv.get(str(p0["id"]), []), 3):
            want = 0
            chk.ok(line, rule + "/cubeevent", any(e[2]["ev"] == 0x0A for e in between(evs, k, j, "TEV")),
                   "cube with contents: no event 0x0A")
        if any(isinstance(x, list) and chk.items.code(x[1]) == code for x in inv.get(str(q0["id"]), [])):
            want = 0
    chk.ok(line, rule + "/eax", r["eax"] == want, "item %s (quest %s) at state %d: eax %s, model %s" %
           (code, quest, p0["st"], r["eax"], want))


def check_show(chk, evs, k):
    line, _, d = evs[k]
    j = pair_after(evs, k, "TSOR", ("p",))
    if j is None:
        return
    tsp = between(evs, k, j, "TSP")
    pb, pa = by_id(d), by_id(evs[j][2])
    p0 = pb.get(d["p"])
    q0 = chk.partner(p0, pb)
    if not p0 or not q0 or not tsp:
        return
    s = tsp[0][2]
    p1, q1 = pa.get(p0["id"]), pa.get(q0["id"])
    rule = "R-show"
    chk.note("show", p=p0["id"], ok=s["ok"], st=(p0["st"], q0["st"]), after=(p1["st"], q1["st"]),
             reopen=bool(between(evs, k, j, "TRO")))
    if not s["ok"]:
        chk.ok(line, rule + "/fail", any(c[2]["code"] == 9 for c in find_close(evs, k, j)), "failed copy: no close 9")
        return
    orig = d.get("item") or []
    ci = s.get("copy_item") or []
    chk.ok(line, rule + "/cell", ci and (ci[2], ci[3], ci[4]) == (1, orig[3], orig[4]) and (s["x"], s["y"]) ==
           (orig[3], orig[4]), "copy %s at page %s (%s, %s), original at (%s, %s)" %
           (s["copy"], ci and ci[2], ci and ci[3], ci and ci[4], orig and orig[3], orig and orig[4]))
    chk.ok(line, rule + "/newid", s["copy"] != s["orig"], "the copy kept the original's id")
    chk.ok(line, rule + "/map", [s["orig"], s["copy"]] in (p1.get("map") or []), "the map lacks (%s, %s)" %
           (s["orig"], s["copy"]))
    if 4 in (p0["st"], q0["st"]):
        chk.ok(line, rule + "/reopen", (p1["st"], q1["st"]) == (3, 3), "a 4 was not returned to 3")
    else:
        chk.ok(line, rule + "/nostate", (p1["st"], q1["st"]) == (p0["st"], q0["st"]), "states moved without a 4")


def check_hide(chk, evs, k):
    line, _, d = evs[k]
    j = pair_after(evs, k, "THOR", ("p",))
    if j is None:
        return
    pb, pa = by_id(d), by_id(evs[j][2])
    p0 = pb.get(d["p"])
    q0 = chk.partner(p0, pb)
    if not p0 or not q0 or not p0.get("rec"):
        return
    p1, q1 = pa.get(p0["id"]), pa.get(q0["id"])
    rule = "R-hide"
    orig = (d.get("item") or [None])[0]
    copy = [c for o, c in (p0.get("map") or []) if o == orig]
    chk.note("hide", p=p0["id"], lk=(p1.get("lk"), q1.get("lk")), st=(p0["st"], q0["st"]), after=(p1["st"], q1["st"]))
    chk.ok(line, rule + "/lock", p1.get("lk") and p1.get("lk") == q1.get("lk") and p1["lk"] != p0.get("lk"),
           "lock times %s/%s (before %s)" % (p1.get("lk"), q1.get("lk"), p0.get("lk")))
    if copy:
        qinv = (evs[j][2].get("inv") or {}).get(str(q0["id"]), [])
        chk.ok(line, rule + "/copyoff", not any(isinstance(x, list) and x[0] == copy[0] and x[2] == 1 for x in qinv),
               "copy %s still on the partner's page 1" % copy[0])
    chk.ok(line, rule + "/mapkept", any(o == orig for o, _ in (p1.get("map") or [])), "the map entry was removed")
    if 4 in (p0["st"], q0["st"]):
        chk.ok(line, rule + "/reopen", (p1["st"], q1["st"]) == (3, 3), "a 4 was not returned to 3")


def offer_of(inv, items):
    """A player's page-2 items in list order, with their sizes."""
    its = page_items(inv, 2)
    return its, [items.size(it[1]) for it in its]


def check_commit(chk, evs, k):
    line, _, d = evs[k]
    j = pair_after(evs, k, "TCMR", ("a", "b"))
    if j is None:
        return
    pb, pa = by_id(d), by_id(evs[j][2])
    A0, B0 = pb.get(d["a"]), pb.get(d["b"])
    A1, B1 = pa.get(d["a"]), pa.get(d["b"])
    if not (A0 and B0 and A1 and B1):
        chk.skipped += 1
        return
    rule = "R-commit"
    cx = between(evs, k, j, "TCX")
    site = cx[0][2]["site"] if cx else None
    trt = between(evs, k, j, "TRT")
    tmv = between(evs, k, j, "TMV")
    offA, offB = A0.get("off") or 0, B0.get("off") or 0
    gA, gB = A0["gold"], B0["gold"]
    capA, capB = GOLD_PER_LEVEL * (A0["lvl"] or 0), GOLD_PER_LEVEL * (B0["lvl"] or 0)
    want = None
    if offA and gA < offA:
        want = 0x00567CA8
    elif offA and (gB + offA) & U32 > capB:
        want = 0x00567CE0
    elif offB and gB < offB:
        want = 0x00567D51
    elif offB and (gA + offB) & U32 > capA:
        want = 0x00567D86
    note = {"site": site, "trt": [t[2]["eax"] for t in trt], "side": [t[2]["side"] for t in trt],
            "tmv": [(t[2]["dir"], t[2]["al"]) for t in tmv], "a": d["a"], "b": d["b"], "offA": offA, "offB": offB}
    if want is not None:
        chk.ok(line, rule + "/gold", site == want, "gold tests predict %s (%s), logged %s" %
               (hex(want), CANCEL_SITES[want], site and hex(site)))
        chk.note("commit", **note)
        return
    chk.ok(line, rule + "/goldpass", bool(trt), "the gold tests passed but no room test was logged")
    inv = d.get("inv") or {}
    invA, invB = inv.get(str(d["a"]), []), inv.get(str(d["b"]), [])
    pred = None
    if chk.items is not None:
        itA, offerA = offer_of(invA, chk.items)
        itB, offerB = offer_of(invB, chk.items)
        gridA, gridB = grid_from(rects(invA, 0, chk.items)), grid_from(rects(invB, 0, chk.items))
        rt_ok, side, s_ab, s_ba = room_test(gridA, offerA, gridB, offerB)
        scp = [e[2] for e in between(evs, k, j, "SCP")]
        want_scp = [(it[0], 1 if s else 0, s) for it, s in zip(itA, s_ab)] + \
                   [(it[0], 1 if s else 0, s) for it, s in zip(itB, s_ba)]
        got_scp = [((e.get("item") or [None])[0], 1 if e["ok"] else 0,
                    (e["x"], e["y"]) if e["ok"] else None) for e in scp]
        chk.ok(line, rule + "/scratch", got_scp == [(a, b, tuple(c) if c else None) for a, b, c in want_scp],
               "scratch placements %s, FIRST model %s" % (got_scp, want_scp))
        chk.ok(line, rule + "/owner0", all(e["own"] == 0 for e in scp), "a scratch owner word is not 0")
        if trt:
            chk.ok(line, rule + "/roomtest", (trt[0][2]["eax"] == 1) == rt_ok and
                   (rt_ok or trt[0][2]["side"] == side), "room test eax %s side %s, model %s side %s" %
                   (trt[0][2]["eax"], trt[0][2]["side"], rt_ok, side))
        mv_ab, _ = place_seq(gridB, offerA, True)
        mv_ba, _ = place_seq(gridA, offerB, True)
        tmp = [e[2] for e in between(evs, k, j, "TMP")]
        want_tmp = [(it[0], s) for it, s in zip(itA, mv_ab)] + [(it[0], s) for it, s in zip(itB, mv_ba)]
        got_tmp = [(e["orig"], (e["copy"][3], e["copy"][4]) if e["ok"] and e.get("copy") else None) for e in tmp]
        if rt_ok and not (site == 0x00568050 and not tmv):
            n = len(got_tmp)
            chk.ok(line, rule + "/placement", got_tmp == [(a, tuple(c) if c else None) for a, c in want_tmp][:n],
                   "placements %s, BEST model %s" % (got_tmp, want_tmp))
        pred = (rt_ok, side, fits_all(mv_ab, len(offerA)), fits_all(mv_ba, len(offerB)))
        note.update(model=pred, first_ab=s_ab, best_ab=mv_ab, first_ba=s_ba, best_ba=mv_ba)
    else:
        chk.skipped += 1
    msgs = [e[2]["code"] for e in between(evs, k, j, "TMS")]
    if trt and trt[0][2]["eax"] == 0:
        # 0x77 to A, then B: 9 to the side without room, 0x0A to the offerer (0x00567E05-0x00567E72)
        chk.ok(line, rule + "/roommsgs", msgs[:2] == ([9, 0x0A] if trt[0][2]["side"] == 1 else [0x0A, 9]),
               "room failure side %s: 0x77 codes %s" % (trt[0][2]["side"], msgs))
        chk.ok(line, rule + "/roomcancel", site == (0x00567E41 if trt[0][2]["side"] == 1 else 0x00567E86) and
               A1.get("off") == 0 and B1.get("off") == 0, "room failure: site %s, offers %s/%s" %
               (site and hex(site), A1.get("off"), B1.get("off")))
    elif tmv and tmv[-1][2]["al"] == 0:
        # TradeMoveItems' failed placement: 0x0A to the giver, 9 to the receiver (0x00567268-0x00567294)
        chk.ok(line, rule + "/movemsgs", msgs[:2] == [0x0A, 9], "failed move: 0x77 codes %s" % msgs)
    if tmv and tmv[0][2]["al"] == 0:
        chk.ok(line, rule + "/movecancel", site == 0x00567F32, "A to B failed, cancel site %s" % (site and hex(site)))
    elif len(tmv) == 2 and tmv[1][2]["al"] == 0:
        chk.ok(line, rule + "/movecancel", site == 0x00568050, "B to A failed, cancel site %s" % (site and hex(site)))
    elif not cx:
        chk.ok(line, rule + "/donemsgs", msgs[-2:] == [0x0D, 0x0D], "after the exchange: 0x77 codes %s" % msgs)
        chk.ok(line, rule + "/done", (A1["st"], B1["st"]) == (9, 9) and not A1["rec"] and not B1["rec"] and
               A1["ia"][2] == 0 and B1["ia"][2] == 0, "after the exchange: states %s/%s, records %s/%s, ia %s/%s" %
               (A1["st"], B1["st"], A1["rec"], B1["rec"], A1["ia"], B1["ia"]))
        ga, gb = gold_after(gA, gB, offA, offB)
        chk.ok(line, rule + "/goldmove", (A1["gold"], B1["gold"]) == (ga, gb), "gold after %s/%s, model %s/%s" %
               (A1["gold"], B1["gold"], ga, gb))
        after = evs[j][2].get("inv") or {}
        old = {it[0] for x in (invA, invB) for it in x if isinstance(it, list)}
        for pid, src in ((d["a"], invA), (d["b"], invB)):
            gone = {it[0] for it in src if isinstance(it, list) and it[2] in (1, 2)}
            now = {it[0] for it in after.get(str(pid), []) if isinstance(it, list)}
            chk.ok(line, rule + "/pages", not (gone & now), "player %s still holds page 1/2 items %s" %
                   (pid, sorted(gone & now)))
        for e in between(evs, k, j, "TMP"):
            c = e[2].get("copy")
            if e[2]["ok"] and c:
                chk.ok(line, rule + "/newcopy", c[0] not in old and c[2] == 0, "copy %s: id seen before or page %s" %
                       (c[0], c[2]))
        if pred is not None:
            chk.ok(line, rule + "/predicted", pred[0] and pred[2] and pred[3], "the exchange went through where the"
                   " model predicts a failure %s" % (pred,))
    chk.note("commit", **note)


def check_cancel(chk, evs, k):
    line, _, d = evs[k]
    j = pair_after(evs, k, "TCXR", ("a", "b"))
    if j is None:
        return
    pb, pa = by_id(d), by_id(evs[j][2])
    rule = "R-cancel"
    for pid in (d["a"], d["b"]):
        x0, x1 = pb.get(pid), pa.get(pid)
        if not x0 or not x1:
            continue
        chk.ok(line, rule + "/state", x1["st"] == 5 and x1["rec"] == x0["rec"] and x1["rec"] and x1.get("off") == 0
               and x1["b23"] == 1, "player %s after the cancel: state %s rec %s/%s off %s bit23 %s" %
               (pid, x1["st"], x0["rec"], x1["rec"], x1.get("off"), x1["b23"]))
        if x0["gold"] and x0["mode"] not in (0, 17) and x0.get("g10") is not None:
            chk.ok(line, rule + "/gold", x1["gold"] == x0["g10"], "player %s gold %s, opening %s" %
                   (pid, x1["gold"], x0["g10"]))
        chk.restored(line, rule, pid, (d.get("inv") or {}).get(str(pid), []),
                     (evs[j][2].get("inv") or {}).get(str(pid), []))
    chk.note("cancel", site=d["site"], why=CANCEL_SITES.get(d["site"]))


def check_close(chk, evs, k):
    line, _, d = evs[k]
    j = pair_after(evs, k, "TCLR", ("p", "q", "code"))
    if j is None:
        return
    pb, pa = by_id(d), by_id(evs[j][2])
    p0, q0, p1, q1 = pb.get(d["p"]), pb.get(d["q"]), pa.get(d["p"]), pa.get(d["q"])
    chk.note("close", code=d["code"], p=d["p"], site=d["site"])
    if not (p0 and q0 and p1 and q1):
        return
    rule = "R-close"
    chk.ok(line, rule + "/states", (p1["st"], q1["st"]) == (d["code"], 9) and not p1["rec"] and not q1["rec"] and
           p1["ia"][2] == 0 and q1["ia"][2] == 0 and p1["b23"] == 1 and q1["b23"] == 1,
           "after the close %d: states %s/%s rec %s/%s ia %s/%s" % (d["code"], p1["st"], q1["st"], p1["rec"],
                                                                     q1["rec"], p1["ia"], q1["ia"]))
    for x0, x1 in ((p0, p1), (q0, q1)):
        if x0.get("rec"):
            if x0["gold"] and x0["mode"] not in (0, 17):
                chk.ok(line, rule + "/gold", x1["gold"] == x0["g10"], "player %s gold %s, opening %s" %
                       (x0["id"], x1["gold"], x0["g10"]))
            chk.restored(line, rule, x0["id"], (d.get("inv") or {}).get(str(x0["id"]), []),
                         (evs[j][2].get("inv") or {}).get(str(x0["id"]), []))


def check_abort(chk, evs, k):
    line, _, d = evs[k]
    j = pair_after(evs, k, "TABR", ("p",))
    if j is None:
        return
    pb, pa = by_id(d), by_id(evs[j][2])
    p0 = pb.get(d["p"])
    q0 = chk.partner(p0, pb)
    back = bool(q0 and q0["ia"][2] and q0["ia"][1] == 0 and q0["ia"][0] == p0["id"])
    chk.note("abort", p=d["p"], back=back)
    if not p0:
        return
    rule = "R-abort"
    p1 = pa.get(p0["id"])
    if back:
        q1 = pa.get(q0["id"])
        chk.ok(line, rule + "/states", q1 and q1["st"] == 9 and not q1["rec"] and (p1 is None or (p1["st"] == 9 and
               not p1["rec"])), "after the abort: %s / %s" % (p1 and (p1["st"], p1["rec"]),
                                                              q1 and (q1["st"], q1["rec"])))
        if q0.get("rec") and q1:
            chk.restored(line, rule, q0["id"], (d.get("inv") or {}).get(str(q0["id"]), []),
                         (evs[j][2].get("inv") or {}).get(str(q0["id"]), []))
    elif p1:
        chk.ok(line, rule + "/oneway", p1["ia"][2] == 0 and p1["st"] == p0["st"] and p1["rec"] == p0["rec"],
               "no back-pointer, yet more than the interaction changed")


def check_tick(chk, evs, k):
    line, _, d = evs[k]
    j = pair_after(evs, k, "TTKR", ("p",))
    if j is None:
        return
    p0, p1 = by_id(d).get(d["p"]), by_id(evs[j][2]).get(d["p"])
    if not p0 or not p1:
        return
    s, s1 = p0["st"], p1["st"]
    rule = "R-tick"
    prev = chk.last_tick.get(d["p"])
    if prev and prev[2] is not None:
        quiet = not any(e[1] in ("TIT", "TCX", "TCL", "TCM", "TAB", "TSO", "THO", "TRB") for e in evs
                        if prev[3] < e[0] < line)
        if quiet:
            chk.ok(line, rule + "/delay", d["f"] - prev[0] == prev[2], "tick at %d queued +%d, came +%d" %
                   (prev[1], prev[2], d["f"] - prev[0]))
    delay = None
    if s <= 4:
        chk.ok(line, rule + "/low", s1 == s, "the tick moved state %d to %d" % (s, s1))
    elif s in TICK:
        nxt, delay = TICK[s]
        chk.ok(line, rule + "/step", s1 in nxt, "tick at %d wrote %d, not %s" % (s, s1, sorted(nxt)))
        if s in (6, 10, 13) or s == 15:
            chk.ok(line, rule + "/bits", p1["b22"] == 0 and (s == 15 or p1["b23"] == 0),
                   "tick at %d left bits 22/23 at %d/%d" % (s, p1["b22"], p1["b23"]))
    elif s == 8:
        lk = p0.get("lk") or 0
        want = 11 if lk else 3
        chk.ok(line, rule + "/eight", s1 == want and p1["b22"] == 0, "tick at 8 (lock %s): %d, bit 22 %d" %
               (lk, s1, p1["b22"]))
        delay = 125 if lk else None
    elif s == 11:
        chk.ok(line, rule + "/eleven", s1 in (11, 3) and (s1 == 11 or (p1.get("lk") == 0 and p1["b22"] == 0 and
               p1["b23"] == 0)), "tick at 11: %d, lock %s" % (s1, p1.get("lk")))
        delay = 25 if s1 == 11 else None
    elif s == 16:
        chk.ok(line, rule + "/sixteen", s1 in (16, 12), "tick at 16: %d" % s1)
        delay = 5 if s1 == 16 else None
    chk.last_tick[d["p"]] = (d["f"], s, delay, line)
    chk.note("tick", p=d["p"], st=s, after=s1, lk=p0.get("lk"))


def check_save(chk, evs, k):
    line, _, d = evs[k]
    tsv = None
    for m in range(k - 1, -1, -1):
        if evs[m][1] == "TSV":
            tsv = evs[m][2]
            break
    rec = None
    for m in range(k - 1, -1, -1):
        pl = by_id(evs[m][2])
        if d["p"] in pl:
            rec = pl[d["p"]]
            break
    chk.note("save", p=d["p"], eax=d["eax"], flag=tsv and tsv["flag"], sha=d.get("sha"),
             rec_sha=rec and rec.get("sha"))
    if not rec:
        return
    rule = "R-save"
    if rec.get("rec") and tsv and tsv["flag"] and rec["r0"] <= tsv["room"]:
        chk.ok(line, rule + "/snapshot", d["eax"] == rec["r0"] and d.get("sha") == rec.get("sha"),
               "saved %s bytes sha %s, the record holds %s sha %s" % (d["eax"], d.get("sha"), rec["r0"],
                                                                      rec.get("sha")))
    elif not rec.get("rec"):
        chk.ok(line, rule + "/live", d["eax"] == 0, "no record, yet the snapshot copy returned %s" % d["eax"])


# ---- the cases ----------------------------------------------------------------------------------------------------

def _any(seen, kind, pred=lambda x: True):
    return any(k == kind and pred(d) for k, d in seen)


CASES = {
    "T1": ("MP31: an item and gold", [
        ("E-open", lambda s: _any(s, "button", lambda d: d["b"] == 3 and d["after"] == (3, 3))),
        ("E-show", lambda s: _any(s, "show", lambda d: d["ok"])),
        ("E-gold", lambda s: _any(s, "offer")),
        ("E-exchange", lambda s: _any(s, "commit", lambda d: d["site"] is None and
                                      d["tmv"] == [("ab", 1), ("ba", 1)]))]),
    "T2": ("a close by the stock control, the snapshot restore", [
        ("E-close", lambda s: _any(s, "close", lambda d: d["code"] in (9, 12))),
        ("E-newids", lambda s: _any(s, "restore", lambda d: d["newids"]))]),
    "T3": ("the request gates", [
        ("E-busy", lambda s: _any(s, "request", lambda d: d["exit"] == "ev8")),
        ("E-window", lambda s: _any(s, "request", lambda d: d["exit"] in ("ev9-named", "ev9"))),
        ("E-town", lambda s: _any(s, "request", lambda d: d["exit"] == "town"))]),
    "T4": ("a commit with no room", [
        ("E-room", lambda s: _any(s, "commit", lambda d: d["trt"] == [0] and d["site"] in (0x00567E41, 0x00567E86))),
        ("E-cancel", lambda s: _any(s, "cancel", lambda d: d["site"] in (0x00567E41, 0x00567E86)))]),
    "T5": ("a gold offer past the receiver's cap, then an overspend", [
        ("E-clip", lambda s: _any(s, "offer", lambda d: d["clipped"])),
        ("E-exchange", lambda s: _any(s, "commit", lambda d: d["site"] is None and d["tmv"])),
        ("E-overspend", lambda s: _any(s, "overspend"))]),
    "T6": ("gold does not un-accept", [
        ("E-offer-at-4", lambda s: _any(s, "offer", lambda d: d["partner_st"] == 4)),
        ("E-exchange", lambda s: _any(s, "commit", lambda d: d["site"] is None and d["tmv"]))]),
    "T7": ("the 10 s lock on a removal", [
        ("E-hide", lambda s: _any(s, "hide")),
        ("E-eleven", lambda s: _any(s, "tick", lambda d: d["st"] == 8 and d["after"] == 11)),
        ("E-refused", lambda s: _any(s, "button", lambda d: d["b"] == 4 and d["st"][0] in (7, 8, 11) and
                                     d["after"][0] == d["st"][0])),
        ("E-unlock", lambda s: _any(s, "tick", lambda d: d["st"] == 11 and d["after"] == 3))]),
    "T8": ("the joiner leaves mid-trade", [
        ("E-saved", lambda s: _any(s, "save", lambda d: d["flag"] and d["eax"] and d["sha"] == d["rec_sha"])),
        ("E-abort", lambda s: _any(s, "abort", lambda d: d["back"]))]),
    "T9": ("the belt lock", [
        ("E-lock", lambda s: _any(s, "itemtest", lambda d: d["pc"] == TIT_MAIN)),
        ("E-belt", lambda s: _any(s, "belt", lambda d: d["eax"] == 0))]),
    "T10": ("a cube holding an item", [
        ("E-cube", lambda s: _any(s, "itemtest", lambda d: d["pc"] == TIT_MAIN and d["eax"] == 0 and
                                  d["code"] in (None, "box")))]),
    "T11": ("a quest code the partner holds", [
        ("E-quest", lambda s: _any(s, "itemtest", lambda d: d["pc"] == TIT_MAIN and d["eax"] == 0))]),
    "T12": ("an addition un-accepts, without the lock", [
        ("E-lock", lambda s: _any(s, "itemtest", lambda d: d["pc"] == TIT_MAIN and 4 in (d["st"], d["pst"]))),
        ("E-noreopen", lambda s: _any(s, "show", lambda d: d["ok"] and not d["reopen"])),
        ("E-three", lambda s: _any(s, "tick", lambda d: d["st"] == 8 and d["after"] == 3 and not d["lk"]))]),
    "T13": ("FIRST fits, BEST does not", [
        ("E-roompass", lambda s: _any(s, "commit", lambda d: d["trt"] == [1])),
        ("E-movefail", lambda s: _any(s, "commit", lambda d: any(al == 0 for _, al in d["tmv"]))),
        ("E-cancel", lambda s: _any(s, "cancel", lambda d: d["site"] in (0x00567F32, 0x00568050)))]),
}


def run_check(log, items=None, marks=None, case=None, verbose=False, out=print):
    evs = parse(log)
    if marks is None:
        stem = log[:-4] if log.endswith(".log") else log
        marks = stem + ".marks.tsv"
    chk = Check(items, verbose)
    unmet = []
    for name, seg in segments(evs, marks, case):
        chk.case = name
        nm0, nc0 = len(chk.mismatches), chk.n_checks
        check_events(chk, seg)
        seen = [(kd, d) for c, kd, d in chk.seen if c == name]
        exp = CASES.get(name.split("-")[0])
        met = []
        if exp:
            for ename, fn in exp[1]:
                if fn(seen):
                    met.append(ename)
                else:
                    unmet.append((name, ename))
                    out("UNMET %s %s" % (name, ename))
        for c, ln, rule, msg in chk.mismatches[nm0:]:
            out("MISMATCH %s %d %s: %s" % (c, ln + 1, rule, msg))
        out("CASE %s: events=%d checks=%d mismatches=%d expectations=%s" % (
            name, len(seg), chk.n_checks - nc0, len(chk.mismatches) - nm0,
            ("%d/%d met" % (len(met), len(exp[1]))) if exp else "none"))
        if verbose:
            for kd, d in seen:
                out("  %s %s" % (kd, json.dumps(d, default=str)))
    out("TRADE-CHECK events=%d checks=%d mismatches=%d unmet=%d skipped=%d" % (
        len(evs), chk.n_checks, len(chk.mismatches), len(unmet), chk.skipped))
    return chk, unmet


# ---- T13: the layout search -----------------------------------------------------------------------------------------

def outcomes(grid, offer):
    """Over every order of the offer: the set of (FIRST fits, BEST fits) pairs."""
    seen = set()
    for perm in set(itertools.permutations(offer)):
        f, _ = place_seq(grid, list(perm), False)
        b, _ = place_seq(grid, list(perm), True)
        seen.add((fits_all(f, len(perm)), fits_all(b, len(perm))))
    return seen


def random_layout(rng, sizes, n):
    g = ii.InvGrid(INV_W, INV_H)
    placed = []
    for _ in range(n):
        w, h = rng.choice(sizes)
        spots = [(c, r) for r in range(INV_H) for c in range(INV_W) if g.fits(c, r, w, h)]
        if not spots:
            continue
        c, r = rng.choice(spots)
        for y in range(r, r + h):
            for x in range(c, c + w):
                g.cell[y][x] = 1
        placed.append((c, r, w, h))
    return placed


def offer_fits_page(offer):
    """Whether the offer has some arrangement on the 10 x 4 trade page (any order's FIRST packing is a witness)."""
    empty = ii.InvGrid(INV_W, INV_H)
    return any(fits_all(place_seq(empty, list(p), False)[0], len(offer)) for p in set(itertools.permutations(offer)))


def show_grid(placed, spots=(), sizes=()):
    cells = [["." for _ in range(INV_W)] for _ in range(INV_H)]
    for c, r, w, h in placed:
        for y in range(r, r + h):
            for x in range(c, c + w):
                cells[y][x] = "#"
    for k, (s, (w, h)) in enumerate(zip(spots, sizes)):
        if s is None:
            continue
        for y in range(s[1], s[1] + h):
            for x in range(s[0], s[0] + w):
                cells[y][x] = "abcdefghij"[k]
    return ["".join(row) for row in cells]


def layout_search(sizes, seed=67, trials=20000, max_items=10, max_offer=4):
    """Returns {kind: [(cost, placed, offer, robust), ...]} for kind 'D1' (FIRST fits, BEST does not: the test passes,
    the move fails) and 'D2' (BEST fits, FIRST does not: a trade that fits is refused); robust when every order of the
    offer gives the same disagreement. Seeded and deterministic."""
    rng = random.Random(seed)
    found = {"D1": [], "D2": []}
    counts = {"trials": 0, "D1": 0, "D2": 0, "D1_robust": 0, "D2_robust": 0}
    for _ in range(trials):
        n0 = rng.randint(0, max_items)
        placed = random_layout(rng, sizes, n0)
        k = rng.randint(2, max_offer)
        if rng.random() < 0.5:
            offer = [rng.choice(sizes)] * k
        else:
            offer = [rng.choice(sizes) for _ in range(k)]
        if not offer_fits_page(offer):
            continue
        counts["trials"] += 1
        res = outcomes(grid_from(placed), offer)
        for kind, pair in (("D1", (True, False)), ("D2", (False, True))):
            if pair in res:
                robust = res == {pair}
                counts[kind] += 1
                counts[kind + "_robust"] += robust
                found[kind].append((len(placed) + len(offer), sum(w * h for _, _, w, h in placed), placed, offer,
                                    robust))
    for kind in found:
        found[kind].sort(key=lambda t: (not t[4], t[0], t[1], t[2], t[3]))
    return counts, found


def describe(placed, offer):
    g = grid_from(placed)
    f, _ = place_seq(g, offer, False)
    b, _ = place_seq(g, offer, True)
    lines = ["page 0 items (col, row, w, h): %s" % placed, "offer in list order (w, h): %s" % offer,
             "FIRST (room test) spots: %s" % f, "BEST (real placement) spots: %s" % b,
             "%-12s %-12s %-12s" % ("page 0", "FIRST", "BEST")]
    for a, x, y in zip(show_grid(placed), show_grid(placed, f, offer), show_grid(placed, b, offer)):
        lines.append("%-12s %-12s %-12s" % (a, x, y))
    return lines


def main(argv):
    if not argv or argv[0] not in ("check", "mark", "layout", "cases"):
        print(__doc__)
        return 2
    cmd, a = argv[0], argv[1:]
    opt, pos, k = {}, [], 0
    while k < len(a):
        if a[k] in ("--excel", "--marks", "--case", "--seed", "--trials", "--show", "--note"):
            opt[a[k][2:]] = a[k + 1]
            k += 2
        elif a[k] == "-v":
            opt["v"] = True
            k += 1
        else:
            pos.append(a[k])
            k += 1
    if cmd == "cases":
        for name, (what, exps) in CASES.items():
            print("%-4s %s: %s" % (name, what, ", ".join(e for e, _ in exps)))
        return 0
    if cmd == "mark":
        import harness_runner as hr
        if len(pos) < 2:
            print(__doc__)
            return 2
        log, case = pos[0], pos[1]
        ev = pos[2] if len(pos) > 2 else "start"
        stem = log[:-4] if log.endswith(".log") else log
        r = hr.mark(stem, case, ev, log=log, note=opt.get("note", ""))
        print("mark %s %s line %s" % (case, ev, r["line"]))
        return 0
    if cmd == "layout":
        if len(pos) != 1:
            print(__doc__)
            return 2
        items = Items(pos[0])
        sizes = sorted({(w, h) for _, w, h, _ in items.rows})
        seed, trials, show = int(opt.get("seed", 67)), int(opt.get("trials", 20000)), int(opt.get("show", 2))
        counts, found = layout_search(sizes, seed, trials)
        print("item sizes (w, h) in weapons/armor/misc: %s" % sizes)
        print("seed %d, trials %d, offers that fit the trade page %d" % (seed, trials, counts["trials"]))
        for kind, what in (("D1", "FIRST fits, BEST does not (the test passes, the move fails)"),
                           ("D2", "BEST fits, FIRST does not (a trade that fits is refused)")):
            print("%s %s: %d layouts, %d for every order of the offer" % (kind, what, counts[kind],
                                                                           counts[kind + "_robust"]))
            for cost, area, placed, offer, robust in found[kind][:show]:
                print("  example (%d items, %s):" % (cost, "every order" if robust else "some orders"))
                for ln in describe(placed, offer):
                    print("    " + ln)
        print("LAYOUT D1=%d D1_robust=%d D2=%d D2_robust=%d" % (counts["D1"], counts["D1_robust"], counts["D2"],
                                                               counts["D2_robust"]))
        return 0
    if len(pos) != 1:
        print(__doc__)
        return 2
    items = Items(opt["excel"]) if opt.get("excel") else None
    chk, unmet = run_check(pos[0], items, opt.get("marks"), opt.get("case"), opt.get("v", False))
    return 0 if not chk.mismatches and not unmet else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
