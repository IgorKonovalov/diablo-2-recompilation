#!/usr/bin/env python3
"""Item use and inventory model (plan 0060, docs/findings/items/0012-use-inventory.md). P1.1: the use entries.

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


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "stock":
        stock(sys.argv[2])
    else:
        sys.exit(__doc__)
