#!/usr/bin/env python3
"""Item use and inventory model (plan 0060, docs/findings/items/0012-use-inventory.md, 0013-grids-belts-stacks.md). P1.1: the
use entries; P1.2: grids, the placement search, belts, stacks.

Pure arithmetic over declared inputs; tools/use_emu.py compares it with Game.exe under the p-code emulator and
Phase 2's cases are predicted from it. No game data is held here: a row is passed in, or read by `stock` from the excel
directory given on the command line.

    python3 -I tools/item_inventory.py stock <excel-dir>     the stock potion rows and each class's amount

A boundary is (kind, args); `use_stat_entry` stops at the first one, as the emulator's observed boundary does.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng  # noqa: E402
from player import muldiv  # noqa: E402

M32 = 0xFFFFFFFF
LIFE, MAXLIFE, MANA, MAXMANA, MANAREC, HPREGEN = 6, 7, 8, 9, 26, 74
VIT, ENE = 3, 1
CLASS = ("ama", "sor", "nec", "pal", "bar", "dru", "ass")


def i32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def life_mul(unit_type, cls, v):
    """fn 0x0062A5D0: amazon, paladin, assassin v + (v >> 1); barbarian and any non-player 2v; others v."""
    if unit_type == 0:
        if cls in (0, 3, 6):
            return i32((v >> 1) + v)
        if cls != 4:
            return i32(v)
    return i32(v * 2)


def mana_mul(unit_type, cls, v):
    """fn 0x0062A620: amazon, paladin, assassin v + (v >> 1); sorceress, necromancer, druid 2v; others v."""
    if unit_type == 0:
        if cls in (0, 3, 6):
            return i32((v >> 1) + v)
        if cls in (1, 2, 5):
            return i32(v * 2)
    return i32(v)


class Unit:
    """type, cls, uid, low, high (seed), stats {stat: value}, slist None or {"end": frame, "base": {stat: value}},
    golem None or {"share": percent}."""

    def __init__(self, typ=0, cls=0, uid=1, low=1, high=0, stats=None, slist=None, golem=None):
        self.type, self.cls, self.uid, self.low, self.high = typ, cls, uid, low, high
        self.stats, self.slist, self.golem = dict(stats or {}), slist, golem

    def stat(self, s):
        return self.stats.get(s, 0)

    def range(self, n):
        """RNG_Range and RNG_RangeB: no step for n < 1, else one step and low mod n."""
        r, self.low, self.high = rng.rng_range(self.low, self.high, n & M32)
        return r


def potion_scale(u, stat, v):
    """Entry 3's switch (0x005BE4E0-0x005BE542). Its draws come for a zero amount too: they precede the amount test."""
    if stat in (MANAREC, HPREGEN):
        v = i32(v << 8)
    if stat in (MANA, MANAREC):
        v, src = mana_mul(u.type, u.cls, v), ENE
    elif stat in (LIFE, HPREGEN):
        v, src = life_mul(u.type, u.cls, v), VIT
    else:
        return v
    n = u.stat(src)
    if n > 0:
        r1 = u.range(n)
        r2 = u.range(100)
        if r2 < (r1 >> 1):
            v = i32(v * 2)
    return v


def golem_split(u, v):
    """fn 0x005C6870 for v > 0: a Blood Golem (pet type 3, class 0x122) takes v * share / 100, truncated."""
    if not u.golem:
        return v, None
    return v, tdiv(i32(v * u.golem["share"]), 100)


def use_stat_entry(entry, u, rec, frame, memctx, nisc, nstates):
    """Entries 3 (0x005BE3F0), 4 (0x005BE7B0), 5 (0x005BEAC0), up to the first boundary or the return.
    rec: {"len", "state", "slots": [(stat, calc)]*3}; `isc[stat]`: (valshift, maxstat) inside rec["isc"].
    -> ("ret", eax) or (kind, args...)."""
    ln, state = rec["len"], rec["state"]
    sl, rem = None, 0
    if ln > 0:
        if state < 1 or state >= nstates:
            return ("ret", 0)
        sl = u.slist
        if sl is not None:
            rem = i32(sl["end"] - frame)
    done = 0
    for k, (s, calc) in enumerate(rec["slots"]):
        if s < 0 or s >= nisc:
            if entry == 5:
                continue
            break
        shift, maxstat = rec["isc"].get(s, (0, 0xFFFF))
        if entry == 5:
            if maxstat >= nisc or calc <= 0:
                continue
            top = u.stat(maxstat)
            v = muldiv(top, calc, 100)
            if calc == 100:
                v = top
        else:
            v = potion_scale(u, s, calc) if entry == 3 else (i32(calc << 8) if s in (MANAREC, HPREGEN) else calc)
            v = i32(v << (shift & 31))
            if v <= 0:
                continue
        if s in (LIFE, HPREGEN) and u.type == 0:
            v2, share = golem_split(u, v)
            if share is not None:
                return ("golem", share)
            v = v2
        if ln < 1:
            cur = u.stat(s)
            if entry == 5:
                if i32(cur + v) > top:
                    v = i32(top - cur)
            elif maxstat < nisc:
                top = u.stat(maxstat)
                if i32(cur + v) > top:
                    v = i32(top - cur)
            return ("addstat", s, v)
        end = i32(frame + rem + ln)
        if sl is None:
            return ("alloc", end)
        base = sl["base"].get(s, 0)
        if k == 0:
            return ("queue", end)
        d = i32(ln + rem)
        if d > 0:
            return ("setstat", s, tdiv(i32(i32(base * rem) + v), d), end)
        done = 1
    return ("ret", done)


def potion_total(cls, stat, calc, doubled=False):
    """A stock healing or mana potion's total for a player of class `cls`, in the stat's stored units."""
    v = i32(calc << 8)
    v = mana_mul(0, cls, v) if stat == MANAREC else life_mul(0, cls, v)
    return i32(v * 2) if doubled else v


def double_chance(n):
    """P(the doubling) = #{(r1, r2): r2 < r1 >> 1} / (n * 100), for vitality or energy n, as an exact fraction pair."""
    if n < 1:
        return (0, 1)
    return (sum(min(100, r1 >> 1) for r1 in range(n)), n * 100)


def stock(excel):
    rows = list(csv.reader(open(os.path.join(excel, "misc.txt"), encoding="latin1"), delimiter="\t"))
    h = rows[0]
    ix = {c: h.index(c) for c in ("code", "pSpell", "len", "stat1", "calc1", "stat2", "calc2")}
    for r in rows[1:]:
        if r[ix["pSpell"]] != "3":
            continue
        stat = MANAREC if r[ix["stat1"]] == "manarecovery" else HPREGEN
        calc = int(r[ix["calc1"]])
        ln = int(r[ix["len"]])
        print(r[ix["code"]], "len", ln, " ".join("%s=%d" % (c, potion_total(i, stat, calc)) for i, c in enumerate(CLASS)))


# ---- P1.2: grids, the placement search, belts, stacks (docs/findings/items/0013-grids-belts-stacks.md) --------------------

BODY_GRID, BELT_GRID = (13, 1), (16, 1)     # data 0x0074479C, 0x007447B4
POTION_GROUPS = (("hp1 ", "hp2 ", "hp3 ", "hp4 ", "hp5 "), ("mp1 ", "mp2 ", "mp3 ", "mp4 ", "mp5 "), ("rvl ", "rvs "))
CLASS_ROW = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 14, 6: 15}    # data 0x00744544, 7 pairs


class InvGrid:
    """One page's cells; `cell[row][col]` is 0 for free. Width and height are u8 in the page (+8, +9)."""

    def __init__(self, w, h, occupied=()):
        self.w, self.h = w, h
        self.cell = [[0] * w for _ in range(h)]
        for r, c in occupied:
            self.cell[r][c] = 1

    def free(self, col, row, w, h):
        """0x0063A8A0: no bounds test of its own; the callers test first."""
        return all(self.cell[r][c] == 0 for r in range(row, row + h) for c in range(col, col + w))

    def fits(self, col, row, w, h):
        return col + w <= self.w and row + h <= self.h and self.cell[row][col] == 0 and self.free(col, row, w, h)

    def score(self, col, row, w, h, edges=True):
        """0x0063B340: occupied cells along the four sides, an outside side counting its whole length; 255 when all are."""
        n = 0
        if col < 1:
            n += h if edges else 0
        else:
            n += sum(1 for r in range(row, row + h) if self.cell[r][col - 1])
        if col + w < self.w:
            n += sum(1 for r in range(row, row + h) if self.cell[r][col + w])
        else:
            n += h if edges else 0
        if row < 1:
            n += w if edges else 0
        else:
            n += sum(1 for c in range(col, col + w) if self.cell[row - 1][c])
        if row + h < self.h:
            n += sum(1 for c in range(col, col + w) if self.cell[row + h][c])
        else:
            n += w if edges else 0
        return 255 if 2 * (w + h) <= n else n


def order_cols_right(g):
    """0x0063B490 and 0x0063B540's column order: the right column first."""
    return range(g.w - 1, -1, -1)


def search_best(g, w, h, order, ctl=None):
    """0x0063B490, 0x0063B620: the first spot of the highest score in `order`, stopping at 255; a best of 0 fails."""
    best, at = 0, None
    for col, row in order:
        if not g.fits(col, row, w, h):
            continue
        s = g.score(col, row, w, h, edges=ctl != "noedge")
        if s > best or (ctl == "geq" and s == best and s > 0):
            best, at = s, (col, row)
            if s == 255 and ctl != "no255":
                return at
    return at


def search_first(g, w, h, order):
    """0x0063B540, 0x0063B6E0: the first spot that fits in `order`."""
    for col, row in order:
        if g.fits(col, row, w, h):
            return col, row
    return None


def order_best_row(g):
    """0x0063B490: columns from the right, in each rows from the bottom."""
    return [(c, r) for c in range(g.w - 1, -1, -1) for r in range(g.h - 1, -1, -1)]


def order_best(g):
    """0x0063B620: rows from the top, in each columns from the left."""
    return [(c, r) for r in range(g.h) for c in range(g.w)]


def order_first_row(g):
    """0x0063B540: columns from the right, in each rows from the top."""
    return [(c, r) for c in range(g.w - 1, -1, -1) for r in range(g.h)]


def order_first(g):
    """0x0063B6E0: columns from the left, in each rows from the top."""
    return [(c, r) for c in range(g.w) for r in range(g.h)]


def spot_find(g, w, h, is_player, ctl=None):
    """0x0063B850 past its tests: the spot, or None. A height of 1 takes the row searches; the three other branches at
    0x0063B8F1..0x0063B938 call bodies that do the same thing. A player's page takes the score, any other the first fit."""
    if ctl == "firstall":
        is_player = False
    if ctl == "bestall":
        is_player = True
    one = h == 1 and ctl != "h1general"
    if is_player:
        if ctl == "rowfirst" and one:
            order = [(c, r) for r in range(g.h - 1, -1, -1) for c in range(g.w - 1, -1, -1)]
        elif ctl == "colright" and not one:
            order = [(c, r) for r in range(g.h) for c in range(g.w - 1, -1, -1)]
        else:
            order = order_best_row(g) if one else order_best(g)
        return search_best(g, w, h, order, ctl)
    return search_first(g, w, h, order_first_row(g) if one else order_first(g))


def inv_row(unit_type, cls, page, expansion, ctl=None):
    """0x00621050: the inventory.txt row for a unit and page; -1 for none. A stash is row 12 in an expansion game, else 8."""
    if unit_type == 0:
        if page == 1:
            return 6
        if page == 2:
            return 7
        if page == 3:
            return 9
        if page == 4:
            big = expansion != 0 if ctl != "stashsmall" else False
            return 12 if big else 8
        return CLASS_ROW.get(cls, -1)
    if unit_type == 1:
        return 5
    if unit_type == 2:
        return {0x152: 10, 0x153: 11}.get(cls, -1)
    return -1


def same_potion_group(a, b):
    """0x00628A40 on codes, past its equal-class test: both in one of the three lists."""
    return any(a in g and b in g for g in POTION_GROUPS)


def belt_slot(numboxes, boxes, code, same_class_at, autobelt, ctl=None):
    """0x0063C600 past its tests: the box, or None. Each of the bottom four boxes that holds a matching potion starts a walk
    up its column; then, with `autobelt`, the first free box of the bottom row. `boxes[i]` is None or the held code;
    `same_class_at` the boxes whose item has the same class as this one."""
    for col in range(4):
        held = boxes[col]
        if held is None:
            continue
        match = col in same_class_at or (same_potion_group(code, held) if ctl != "nogroup" else False)
        if match and col < numboxes:
            step = 1 if ctl == "walk1" else 4
            for b in range(col, numboxes, step):
                if boxes[b] is None:
                    return b
    if autobelt or ctl == "noauto":
        for b in range(4):
            if boxes[b] is None:
                return b
    return None


def stack_ok(a, b):
    """0x0062C850 on two dicts: class, quality (ItemData+0, `d0`), file index, stackable, ethereal, the quality rule, six stats, sockets."""
    if a["cls"] != b["cls"] or a["d0"] != b["d0"] or a["file"] != b["file"] or not a["stackable"]:
        return False
    if bool(a["eth"]) != bool(b["eth"]):
        return False
    for x in (a, b):
        q = x["d0"]
        if q == 0 or 3 < q <= 9:
            return False
    if any(a["stats"].get(s, 0) != b["stats"].get(s, 0) for s in (21, 22, 23, 24, 159, 160)):
        return False
    return (a["stats"].get(194, 0) & 0xFF) == 0 and (b["stats"].get(194, 0) & 0xFF) == 0


def max_stack(rec_max, stat254):
    """ITEMS_GetMaxStack 0x006295B0: the record's +0xE8 plus stat 254, 511 above 510."""
    v = i32(rec_max + stat254)
    return 0x1FF if v > 0x1FE else v


def merge_first_set(src_q, tgt_q, mx, src_dur=None, tgt_dur=None):
    """0x0055E590's first UnitSetStat, as (on the target, stat, value). Above the maximum the target takes the maximum and
    (read, after the boundary) the source keeps the rest; else a durable source lowers the target's stat 72, then the sum."""
    total = i32(src_q + tgt_q)
    if mx < total:
        return (70, mx)
    if src_dur is not None and src_dur < tgt_dur:
        return (72, src_dur)
    return (70, total)


# ---- plan 0060 P1.3 (lane/r60c, items/0014): the ground drop's cell search, ground expiry, pickup's distance and line ends

BLOCKED = 0x27                  # COLL_CellTest and COLL_CellTestAt's return with no room, no map or no cells
DROP_MASK_CELL, DROP_MASK_LINE = 0x3E01, 0x801
DIR_DX = (0, 1, 1, 1, 0, -1, -1, -1, 0)     # data:0x00749780
DIR_DY = (-1, -1, 0, 1, 1, 1, 0, -1, 0)     # data:0x007497A4


class Room:
    """A room as the search reads it: subtile rectangle, near list in order, cells or None (no map or no cells)."""

    def __init__(self, x, y, w, h, cells=None, near=()):
        self.x, self.y, self.w, self.h, self.cells, self.near = x, y, w, h, cells, list(near)

    def holds(self, x, y):
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h


def room_at(room, x, y):
    """0x00463740: the room itself, else the first of its near list (in list order) holding the subtile."""
    if room is None:
        return None
    if room.holds(x, y):
        return room
    for r in room.near:
        if r is not None and r.holds(x, y):
            return r
    return None


def cell_test(room, x, y, mask):
    """COLL_CellTest 0x0064D450 and COLL_CellTestAt 0x0064CB30: mask & cell, 0x27 without a room, map or cells."""
    r = room_at(room, x, y)
    if r is None or r.cells is None:
        return BLOCKED
    return r.cells.get((x, y), 0) & mask


def field_dir(field, ox, oy, x, y):
    """The direction byte for (x, y) with the origin (ox, oy): row 128 + dy, column 128 + dx of the 256 x 256 file."""
    return field[(y - oy + 128) * 256 + (x - ox) + 128]


def line_cells(field, ox, oy, x, y):
    """The cells 0x0066A670 tests from (x, y) walking the field to the origin: the start, then each step whose byte is not 8,
    so the origin itself is tested only when it is the start."""
    out = [(x, y)]
    while True:
        d = field_dir(field, ox, oy, x, y)
        x, y = x + DIR_DX[d], y + DIR_DY[d]
        if field_dir(field, ox, oy, x, y) == 8:
            return out
        out.append((x, y))


def diag_cells(ox, oy, x, y):
    """A wrong reading, the control `linediag`: diagonal first, then straight, ignoring the file."""
    out = [(x, y)]
    while (x, y) != (ox, oy):
        x += (ox > x) - (ox < x)
        y += (oy > y) - (oy < y)
        if (x, y) != (ox, oy):
            out.append((x, y))
    return out


def line_blocked(field, ox, oy, room, x, y, mask, ctl=None):
    """0x0066A670: 0 with no room; else 1 at the first cell of the walk whose test is non-zero, tested from the candidate's room."""
    if room is None:
        return 0
    cells = diag_cells(ox, oy, x, y) if ctl == "linediag" else line_cells(field, ox, oy, x, y)
    if ctl == "lineorigin" and (ox, oy) not in cells:
        cells = cells + [(ox, oy)]
    for cx, cy in cells:
        if cell_test(room, cx, cy, mask):
            return 1
    return 0


def ring_cells(x, y, r, ctl=None):
    """Ring r in the code's order: for each row y - r..y + r the columns x - r, x + r; then for each column x - r + 1..x + r - 1
    the rows y - r, y + r."""
    sides = [(cx, cy) for cy in range(y - r, y + r + 1) for cx in (x - r, x + r)]
    caps = [(cx, cy) for cx in range(x - r + 1, x + r) for cy in (y - r, y + r)]
    return caps + sides if ctl == "capsfirst" else sides + caps


def find_free_near(room0, x, y, origin, field, mask_a, mask_b, fallback, radius=50, ctl=None):
    """COLL_FindFreeNear 0x0064DEA0 with size 1 and step 1. -> (room or None, x, y). The base room is a variable: each lookup is from the
    last non-null room a lookup returned, the first lookup's result kept even when null (so a lookup's reach is that room and its near
    list, not the first room's), and the final lookup too, so a fallback can return None though the given cell lies in the first room. The first ring holding a free cell gives
    the lowest |dx| + |dy| of that ring, the earliest of equals."""
    cur = [room0]

    def ok(cx, cy, first=False):
        r = room_at(room0 if ctl == "fixedbase" else cur[0], cx, cy)
        if first:
            cur[0] = r          # the first lookup's result is kept even when null, and from null every later lookup is null
        if r is None:
            return False
        cur[0] = r
        if cell_test(r, cx, cy, mask_a):
            return False
        if ctl == "noline" or origin is None:
            return True
        lr = room0 if ctl == "lineroom0" else r
        return not line_blocked(field, origin[0], origin[1], lr, cx, cy, mask_b, ctl)

    if ok(x, y, True):
        return cur[0], x, y
    top = {"r48": 48, "r50": 50}.get(ctl, radius - 1)
    for r in range(1, top + 1):
        best, at = -1, None
        for cx, cy in ring_cells(x, y, r, ctl):
            if not ok(cx, cy):
                continue
            d = abs(cx - x) + abs(cy - y)
            if best == -1 or d < best or (ctl == "leq" and d == best):
                best, at = d, (cx, cy)
            if ctl == "first":
                break
        if at:
            return room_at(room0 if ctl == "fixedbase" else cur[0], at[0], at[1]), at[0], at[1]
    if fallback or ctl == "alwaysfallback":
        return room_at(room0 if ctl == "fixedbase" else cur[0], x, y), x, y
    return None, x, y


def ground_drop_cell(room, px, py, field, fallback=1, ctl=None):
    """0x00555DA0: start at (px + 2, py + 3) when a room holds it, else at the position; the line runs to the position.
    -> (room or None, x, y)."""
    dx, dy = {"offset32": (3, 2)}.get(ctl, (2, 3))
    sx, sy = px + dx, py + dy
    if ctl == "nooffset" or room_at(room, sx, sy) is None:
        sx, sy = px, py
    mask_a = 0x3C01 if ctl == "noitembit" else DROP_MASK_CELL
    mask_b = DROP_MASK_CELL if ctl == "linecellmask" else DROP_MASK_LINE
    return find_free_near(room, sx, sy, (px, py), field, mask_a, mask_b, fallback, 50, ctl)


def ground_expiry(frame, quest, quality, base_type, gold, filler):
    """sub_00558A10_ItemGroundExpiry: 0 for a quest base, else the frame plus 30000 (quality 4), 45000 (5..9), for base type 4
    45000 above 10000 gold else 15000, for a socket filler 30000, else 15000. Wraps as i32."""
    if quest:
        return 0
    if quality == 4:
        add = 30000
    elif 5 <= quality <= 9:
        add = 45000
    elif base_type == 4:
        add = 45000 if gold > 10000 else 15000
    elif filler:
        add = 30000
    else:
        add = 15000
    return i32(frame + add)


def sweep_first(items, frame, ctl=None):
    """0x00558B90 in list order: the first unit of type 4 with expiry non-zero and <= frame (signed), or None."""
    for i, (typ, exp) in enumerate(items):
        if typ != 4 or (exp == 0 and ctl != "zerofrees"):
            continue
        if exp < frame or (exp == frame and ctl != "ltframe"):
            return i
    return None


def interact_distance(table, ax, ay, sa, bx, by, sb):
    """0x00641530 with table = the 64 i32 at 0x006EB180, sa and sb UNIT_GetSizeX of the two units."""
    dx, dy = abs(bx - ax), abs(by - ay)
    if dx < 8 and dy < 8 and sa < 4 and sb < 4:
        v = table[dx + dy * 8]
        if v < 0:
            return 0
        if sa == 3 or sb == 3:
            v -= 1
        v = max(v, 0)
        return v + 1 if sa < 2 or sb < 2 else v
    half = abs((sb >> 1) + (sa >> 1))
    dx, dy = max(dx - half, 0), max(dy - half, 0)
    return dy + dx * 2 if dy < dx else dx + dy * 2


def line_ends(ax, ay, sa, bx, by, sb):
    """0x00622920's clamp and shortening before COLL_LineTest, a at (ax, ay) with size sa, b likewise. -> None when the units touch
    (|dx| + |dy| < min(sa, 2) + min(sb, 2): return 0 with no test), else ((ax', ay'), (bx', by'))."""
    sa, sb = min(sa, 2), min(sb, 2)
    dx, dy = abs(bx - ax), abs(by - ay)
    if dx + dy < sa + sb:
        return None
    if sa == 0 and sb == 0:
        return (ax, ay), (bx, by)
    if dy <= dx:
        if ax < bx:
            ax, bx = ax + sa, bx - sb
        else:
            ax, bx = ax - sa, bx + sb
        if dy < dx:
            return (ax, ay), (bx, by)
    if ay < by:
        ay, by = ay + sa, by - sb
    else:
        ay, by = ay - sa, by + sb
    return (ax, ay), (bx, by)


def dispatch_gate(op, table_nonzero, mode, state54):
    """0x0054D750 as far as the handler's pointer: 'bad' (returns 3), 'gate' (returns 0), else 'handler'."""
    if op == 0 or op > 0x66 or not table_nonzero:
        return "bad"
    if op in (0x14, 0x15, 0x3C, 0x43, 0x66):
        return "handler"
    if op == 0x41:
        return "handler" if mode == 0x11 else "gate"
    return "handler" if (not state54 and mode not in (0, 0x11)) else "gate"


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "stock":
        stock(sys.argv[2])
    else:
        sys.exit(__doc__)


# ---- plan 0060 Phase 2 (lane/p60, items/0013 § 5 and § 6): the two crafted requests' expected outcomes --------------------

TOWN_LEVELS = (1, 40, 75, 103, 109)
STASH_EXPANSION, STASH_CLASSIC = (6, 8), (6, 4)


def pkt18_expect(page, in_town, x, y, w, h, expansion, occupied=(), ctl=None):
    """items/0013 § 5: `0x18` with a cursor item for a player. -> (handler return, page the item ends on, cell or None).
    Page >= 5 returns 2; page 4 in town only (else 3); no stash-open test (`ctl` 'stashopen' is the wrong reading that
    refuses page 4 with no stash open); a placed item takes (x, y) when it fits and no occupied cell is covered, else the
    handler returns 3 with the page byte already set (`ItemSetPage` runs before the placement)."""
    if page >= 5:
        return 2, None, None
    if page == 4 and not in_town:
        return 3, 4, None
    if page == 4 and ctl == "stashopen":
        return 3, 4, None
    gw, gh = (STASH_EXPANSION if expansion else STASH_CLASSIC) if page == 4 else (10, 4)
    if x < 0 or y < 0 or x + w > gw or y + h > gh:
        return 3, page, None
    cells = {(x + i, y + j) for i in range(w) for j in range(h)}
    if cells & set(occupied):
        return 3, page, None
    return 0, page, (x, y)


def belt23_expect(box, occupied=(), numboxes=12, beltable=True, ctl=None):
    """items/0013 § 6: `0x23` to a box: `BeltPutItem` needs a 1 x 1 beltable item and `box < 16`, and an empty box; it does
    not read `numboxes` (`ctl` 'numboxes' is the wrong reading that does). -> True when the item stays in the box."""
    if not beltable or box >= 16 or box in occupied:
        return False
    if ctl == "numboxes" and box >= numboxes:
        return False
    return True
