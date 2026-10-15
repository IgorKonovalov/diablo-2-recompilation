#!/usr/bin/env python3
"""New character, starting items, experience and level-up model (plan 0034 Phase 2), checked against
tools/gdb/player.gdb logs; the level-up save round trip.

    python3 -I tools/player.py check <log> [<log> ...] [--excel DIR] [--saves DIR] [-v]
    python3 -I tools/player.py loadcheck <built.d2s> <written.d2s> [...pairs] [--excel DIR]

Model of docs/findings/player/0001-creation.md (the architect's Phase 2 boundary, plan 0034 log 2026-10-15): the
player code is modelled here; each starting item's own creation is chained to the item model as tools/cube.py does
(tools/props.py check_iis and check_ic, tools/items_chain.py check_creation), with its exit seed compared.

check, per sub_00569F80_NewCharFromStub (NC0 .. NCX):
  - the game seed: one step for the player (sub_00552DF0_UnitSeedInit: Unit+0x28 = the step's low word, unit seed
    {low, 666}), nothing else up to the first item (NCU, NCP, NCS, NCB compared); after the items, nothing more
    (NCI, NCQ, NCX compared); every RNG-function call in the window is listed (RNG lines) and must be on an item seed
    inside an item creation;
  - PLAYER_InitBaseStats: strength, energy, dexterity, vitality from CharStats, 19 and 20 = 0, life
    (vit + hpadd) << 8, mana int << 8, stamina << 8 (current = max), level 1, nextexp = Experience[class][1],
    67/68/69 = 100; for act != 0 (-act N) PLAYER_GrantLevel(g_ActStartLevel[act]) through PLAYER_AddExperience and
    PLAYER_LevelUp (checked as below), compared at NCB;
  - PLAYER_GiveStartItems: item1..item10 x itemNcount in order (ITEMS_GetByCode), each copy: StartItemCreate (SIC0:
    slot, index), the creation record (CREC: source, ilvl = the player's level, index, +0x18 = 4, +0x28 = 1, item
    version, quality 2, flags 0x0A), two game-seed steps (unit seed init(step), start seed = next step), then
    ItemInitStats and ItemCreateByQuality through the item model (IIS0/IIS1, IC0 .. LX), CRECX (identified, the
    game seed); StartItemCreate's stat-list work (the 0x40 list removed, item_singleskill(StartSkill) = 1 on slot 0's
    copies, quantity = max stack when stackable; SICX); StartItemSlot (ISL): flag 0x20000, body location, placement
    (beltable type: the belt slot search of 0x0063C600 on the default belt; a body location: equipped there; else the
    inventory spot search of 0x0063B490 / 0x0063B620 with the 0x0063B340 score), durability = evaluated max
    durability (a quiver: quantity 250 / 100 instead);
  - the start skill: right skill = StartSkill when the unit has it and act = 0 (NCQ), the skill list (Attack +
    Skill 1..10 at level 1, item ref -1) and the item list at NCX;
  - the first save written after it (WDONE of tools/gdb/d2s-io.py, or the copied file in --saves): every header field,
    stat, skill byte and item predicted from the model, compared field by field.
check, experience (any XK0 / XC0 / XA0 / LU0 line): XP_Compute from (exp, player level, monster level, stat 85):
  the 0x7FFFFF clamp, the MaxLvl test, XP_LevelDiffPenalty (the /256 tables, or exp x clvl / mlvl from level 25),
  XP_ApplyExpRatio, the item_addexperience term (XCP, XCR, XCX compared); PLAYER_AddExperience (cap, lastexp, the new
  level); PLAYER_LevelUp: level, nextexp, maxhp/maxmana/maxstamina + per-level x d x 64, the refill, statpts +
  StatPerLevel x d, newskills + d; the game seed and the player's unit seed unchanged, and no RNG-function call between
  LU0 and LUX.
loadcheck: a built save and the file the game wrote back after loading it: every header field, stat, skill byte,
  item field, mercenary and golem field equal, except last_played, checksum, map_seed, the difficulty act bytes and
  an item's flag 0x2000 ("new") going from 1 to 0, which are listed and counted.
Exit 0 only if everything reproduces. Stdlib only. Read-only.
"""
import argparse
import collections
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import affixes  # noqa: E402
import d2s  # noqa: E402
import excel_bin as eb  # noqa: E402
import excel_layouts as L  # noqa: E402
import items_chain  # noqa: E402
import props  # noqa: E402
import rng  # noqa: E402
import uniques  # noqa: E402

EXCEL = uniques.EXCEL
M32 = 0xFFFFFFFF
CLASSES = ["Amazon", "Sorceress", "Necromancer", "Paladin", "Barbarian", "Druid", "Assassin"]
ACT_START_LEVEL = [1, 15, 20, 26, 32]          # data:g_ActStartLevel@0x006E1520
XP_BELOW = [256] * 6 + [207, 159, 110, 61, 13]  # data:g_XpPenaltyBelow@0x006E1668 (monster level <= player level)
XP_ABOVE = [256] * 6 + [225, 174, 92, 38, 5]    # data:g_XpPenaltyAbove@0x006E1694
Mismatch = props.Mismatch
eq = props.eq


def s8(v):
    return v - 256 if v & 0x80 else v


def i32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def seedpair(s):
    a, b = s.split(":")
    return int(a, 16), int(b, 16)


def fmt(seed):
    return "%08x:%08x" % seed


def decode(excel_dir, table):
    _, _, recs, _ = eb.load_table(excel_dir, table)
    fields = [f for f in L.LAYOUTS[table]["fields"] if "col" in f]
    return [{f["col"]: eb.decode_field(b, f) for f in fields} for b in recs]


# ---------------------------------------------------------------- tables

class Tables:
    def __init__(self, excel):
        self.excel = excel
        self.cs = decode(excel, "charstats")
        self.xp = decode(excel, "experience")
        self.P = props.Tables(excel)
        self.A = affixes.Tables(excel)
        sk = props.recs(excel, "skills")
        self.nskills = len(sk)
        self.skill_b10 = [s8(r[0x10]) for r in sk]
        self.codes = {}
        for i, r in enumerate(self.P.items):
            self.codes.setdefault(r[0x80:0x84].decode("latin1").strip(), i)
        self.compact_codes = set()
        for t in ("weapons", "armor", "misc"):
            rows = open(os.path.join(excel, t + ".txt"), encoding="latin1").read().splitlines()
            hd = rows[0].split("\t")
            ic, cc = hd.index("code"), hd.index("compactsave")
            for line in rows[1:]:
                c = line.split("\t")
                if len(c) > cc and c[cc] == "1":
                    self.compact_codes.add(c[ic])
        inv = {}
        for line in open(os.path.join(excel, "inventory.txt"), encoding="latin1").read().splitlines()[1:]:
            c = line.split("\t")
            if c[0]:
                inv[c[0]] = (int(c[5] or 0), int(c[6] or 0))
        self.grid = inv
        belts = open(os.path.join(excel, "belts.txt"), encoding="latin1").read().splitlines()[1:]
        self.belt_boxes = [int(line.split("\t")[1] or 0) for line in belts if line.split("\t")[0]]

    # Experience (fn:EXP_GetThreshold@0x00611800, fn:sub_00611830_ExpMaxLevel@0x00611830)
    def xcol(self, cls):
        return CLASSES[cls] if 0 <= cls <= 6 else None

    def threshold(self, cls, lvl):
        c = self.xcol(cls)
        return self.xp[lvl + 1][c] if c else 0

    def maxlvl(self, cls):
        c = self.xcol(cls)
        return self.xp[0][c] if c else 0

    def level_from_exp(self, cls, exp):
        n, cap = 0, self.maxlvl(cls)
        while n < cap and (exp & M32) >= self.threshold(cls, n):
            n += 1
        return n

    def ratio(self, lvl):
        """EXP_GetRatio (0x00613E60)."""
        if lvl <= 0:
            return self.xp[0]["ExpRatio"]
        if lvl > self.xp[0]["Amazon"]:
            return 0
        return self.xp[lvl + 1]["ExpRatio"]

    def compact(self, cls):
        """tbl:Misc.txt:compactsave (weapons/armor/misc .txt): the item is saved in the short form."""
        return self.item_raw(cls)[0x80:0x84].decode("latin1").strip() in self.compact_codes

    def item_raw(self, cls):
        return self.P.items[cls]

    def beltable(self, cls):
        t = props.s16(self.item_raw(cls), 0x11E)
        return bool(self.P.itypes[t][0x19]) if 0 <= t < len(self.P.itypes) else False

    def start_items(self, cls):
        r = self.cs[cls]
        out = []
        for k in range(1, 11):
            out.append((k - 1, r["item%d" % k], r["item%dloc" % k], r["item%dcount" % k]))
        return out


# ---------------------------------------------------------------- arithmetic

def muldiv(a, b, c):
    """sub_00483360_MulDiv (0x00483360): signed; 64-bit product only when a value is large."""
    a, b, c = i32(a), i32(b), i32(c)
    if c == 0:
        return 0

    def tdiv(x, y):
        q = abs(x) // abs(y)
        return q if (x >= 0) == (y > 0) else -q
    if a > 0x100000:
        if c > (a >> 4):
            return i32(tdiv(a * b, c))
        return i32(tdiv(a, c) * b)
    if b > 0x10000:
        if c > (b >> 4):
            return i32(tdiv(a * b, c))
        return i32(tdiv(b, c) * a)
    return i32(tdiv(i32(a * b), c))


def xp_compute(T, exp, clvl, mlvl, cls, s85, out=None):
    """XP_Compute (0x0057E480) for a player unit."""
    exp = i32(exp)
    if exp > 0x7FFFFF:
        exp = 0x7FFFFF
    elif exp <= 0:
        return 1
    if clvl >= T.maxlvl(cls if 0 <= cls <= 6 else 0):
        return 0
    # XP_LevelDiffPenalty (0x0057E2F0)
    if mlvl <= clvl:
        f = XP_BELOW[min(clvl - mlvl, 10)]
    elif clvl >= 25 and mlvl > 0:
        f = None
        exp = muldiv(exp, clvl, mlvl)
    else:
        f = XP_ABOVE[min(mlvl - clvl, 10)]
    if f is not None and f != 256:
        exp = muldiv(exp, f, 256)
    if out is not None:
        out["pen"] = exp
    # XP_ApplyExpRatio (0x0057E390)
    if exp > 0:
        r, s = T.ratio(clvl), T.ratio(0)
        if 1 <= s <= 31:
            sh = ((r >> s) + s) & 31
            lim = 0x7FFFFFFF >> sh
            exp = i32((exp >> s) * r) if exp > lim else i32(exp * r) >> s
    if out is not None:
        out["ratio"] = exp
    if s85:
        exp = i32(exp + muldiv(exp, s85, 100))
    return exp


# ---------------------------------------------------------------- stat dicts

def bdict(entries):
    return {(s, p): v for s, p, v in (entries or [])}


def bget(b, stat, param=0):
    return b.get((stat, param), 0)


def bset(b, stat, v, param=0):
    if v:
        b[(stat, param)] = v
    else:
        b.pop((stat, param), None)


def diff_b(model, logged, what):
    """Base entries compared as 32-bit values (the log prints the s32 entry; experience and nextexp pass 2^31 from
    level 93 on)."""
    model = {k: v & M32 for k, v in model.items()}
    logged = {k: v & M32 for k, v in logged.items()}
    if model != logged:
        keys = sorted(set(model) | set(logged))
        d = ["%s: model %s, log %s" % (k, model.get(k), logged.get(k)) for k in keys if model.get(k) != logged.get(k)]
        raise Mismatch("%s: %s" % (what, "; ".join(d)))


# ---------------------------------------------------------------- level-up

def level_up(T, cls, b, exp_total, maxima=None, S=None):
    """PLAYER_LevelUp (0x00570880) on the base entries b (dict, changed in place). Returns the levels gained.
    maxima: the logged UnitGetMaxHp/Mana/Stamina values (LUM); when one differs from the base maximum (item bonuses,
    not modelled here) it is taken as an input and counted."""
    maxima = maxima or {}

    def full(k, stat):
        v = bget(b, stat)
        if k in maxima and maxima[k] != v:
            if S is not None:
                S["level-up refill maximum with item bonuses (%s, LUM input)" % k] += 1
            return maxima[k]
        if S is not None and k in maxima:
            S["level-up refill maximum = base maximum (%s, predicted)" % k] += 1
        return v
    old = bget(b, 12)
    lvl = T.level_from_exp(cls, exp_total)
    bset(b, 12, lvl)
    bset(b, 30, T.threshold(cls, lvl))
    d = lvl - old
    if d <= 0:
        return d
    cs = T.cs[cls] if 0 <= cls < len(T.cs) else None
    bset(b, 7, bget(b, 7) + cs["LifePerLevel"] * d * 64)
    mh = full("hp", 7)
    if bget(b, 6) > 0:
        bset(b, 6, mh)
    bset(b, 9, bget(b, 9) + cs["ManaPerLevel"] * d * 64)
    bset(b, 8, full("mana", 9))
    bset(b, 11, bget(b, 11) + cs["StaminaPerLevel"] * d * 64)
    bset(b, 10, full("stamina", 11))
    bset(b, 4, bget(b, 4) + s8(cs["StatPerLevel"] & 0xFF) * d)
    bset(b, 5, bget(b, 5) + d)
    return d


class XpState:
    """The open experience calls of one log (thread-local)."""

    def __init__(self):
        self.xc = {}
        self.xa = {}
        self.lu = {}


def check_xp_line(T, tag, d, st, S, gs_of=None):
    th = d.get("th")
    if tag == "XK0":
        S["kills credited (XP_OnMonsterKill)"] += 1
        return
    if tag == "XC0":
        st.xc[th] = {"in": d, "parts": {}}
        return
    if tag in ("XCP", "XCR", "XC85"):
        if th in st.xc:
            st.xc[th]["parts"][tag] = d["v"]
        return
    if tag == "XCX":
        c = st.xc.pop(th, None)
        if c is None:
            return
        a = c["in"]
        unit_cls = a.get("cls")
        out = {}
        s85 = c["parts"].get("XC85", 0)
        cls = st.cls_of.get(a["unit"], 0) if unit_cls is None else unit_cls
        v = xp_compute(T, a["exp"], a["clvl"], a["mlvl"], cls, s85, out)
        if "XCP" in c["parts"]:
            eq("XP_LevelDiffPenalty (exp %d, clvl %d, mlvl %d)" % (a["exp"], a["clvl"], a["mlvl"]), out.get("pen"),
               c["parts"]["XCP"])
            S["XP_LevelDiffPenalty predicted"] += 1
            if a["mlvl"] <= a["clvl"]:
                S["  level difference: monster at or below (g_XpPenaltyBelow[%d])" % min(a["clvl"] - a["mlvl"], 10)] += 1
            elif a["clvl"] >= 25:
                S["  level difference: monster above, clvl >= 25 (exp x clvl / mlvl)"] += 1
            else:
                S["  level difference: monster above (g_XpPenaltyAbove[%d])" % min(a["mlvl"] - a["clvl"], 10)] += 1
        if "XCR" in c["parts"]:
            eq("XP_ApplyExpRatio (clvl %d)" % a["clvl"], out.get("ratio"), c["parts"]["XCR"])
            S["XP_ApplyExpRatio predicted"] += 1
            S["  ExpRatio of level %d: %d" % (a["clvl"], T.ratio(a["clvl"]))] += 1
        eq("XP_Compute (exp %d, clvl %d, mlvl %d)" % (a["exp"], a["clvl"], a["mlvl"]), v, d["v"])
        S["XP_Compute predicted"] += 1
        st.last_xc[th] = v
        return
    if tag == "XA0":
        st.cls_of[d["unit"]] = d["cls"]
        b = bdict(d["b"])
        cls = d["cls"]
        exp = bget(b, 13) & M32
        cap = T.threshold(cls, T.maxlvl(cls) - 1)
        new = (exp + d["add"]) & M32
        if new > cap:
            new = cap
        bset(b, 29, i32(new - exp))
        bset(b, 13, i32(new))
        newlvl = T.level_from_exp(cls, new)
        st.xa[th] = {"b": b, "lu": newlvl != d["old"], "old": d["old"], "exp": new, "cls": cls, "in": d,
                     "unit": d["unit"]}
        if th in st.last_xc:
            eq("PLAYER_AddExperience amount = XP_Compute's result", st.last_xc.pop(th) & M32, d["add"])
            S["AddExperience amounts from XP_Compute"] += 1
        S["PLAYER_AddExperience calls"] += 1
        return
    if tag == "LU0":
        a = st.xa.get(th)
        b = bdict(d["b"])
        if a is not None:
            m = dict(a["b"])
            # the base entries at LU0 are AddExperience's writes (experience, lastexp) on the entry state
            eq("LU0 experience = AddExperience's", bget(m, 13), bget(b, 13))
            eq("LU0 lastexp = AddExperience's", bget(m, 29), bget(b, 29))
            a["lu_seen"] = True
        st.lu[th] = {"in": d, "b": b, "max": {}}
        return
    if tag == "LUM":
        if th in st.lu:
            st.lu[th]["max"][d["k"]] = d["v"]
        return
    if tag == "LUX":
        c = st.lu.pop(th, None)
        if c is None:
            return
        a = c["in"]
        cls = a["cls"]
        b = dict(c["b"])
        gained = level_up(T, cls, b, bget(b, 13) & M32, c["max"], S)
        diff_b(b, bdict(d["b"]), "PLAYER_LevelUp base entries (class %d, level %d -> %d)" % (
            cls, bget(c["b"], 12), bget(b, 12)))
        eq("game seed unchanged by PLAYER_LevelUp", a["gs"], d["gs"])
        eq("player unit seed unchanged by PLAYER_LevelUp", a["useed"], d["useed"])
        S["PLAYER_LevelUp reproduced"] += 1
        S["  level-ups: %d level(s) at once" % gained] += 1
        S["  level-up to level %d" % bget(b, 12)] += 1
        st.leveled.append((cls, bget(c["b"], 12), bget(b, 12)))
        x = st.xa.get(th)
        if x is not None:
            x["after"] = b
        return
    if tag == "XAX":
        a = st.xa.pop(th, None)
        if a is None:
            return
        b = a.get("after", a["b"])
        eq("PLAYER_LevelUp called (the level changed)", a["lu"], "after" in a)
        diff_b(b, bdict(d["b"]), "base entries after PLAYER_AddExperience")
        S["PLAYER_AddExperience reproduced"] += 1
        return
    if tag in ("RNG", "LCG") and d.get("in") == "lu":
        raise Mismatch("RNG step inside PLAYER_LevelUp: %s %s" % (tag, json.dumps(d)))
    if tag == "LCG":
        S["LCG multiplier executions inside NewCharFromStub (control: the item creations)"] += 1


# ---------------------------------------------------------------- the new character

def start_stats(T, cls):
    cs = T.cs[cls]
    b = {}
    bset(b, 0, cs["str"])
    bset(b, 1, cs["int"])
    bset(b, 2, cs["dex"])
    bset(b, 3, cs["vit"])
    hp = (cs["hpadd"] + cs["vit"]) << 8
    mp = cs["int"] << 8
    sta = cs["stamina"] << 8
    for s, v in ((6, hp), (7, hp), (8, mp), (9, mp), (10, sta), (11, sta)):
        bset(b, s, v)
    bset(b, 12, 1)
    bset(b, 30, T.threshold(cls, 1))
    for s in (68, 67, 69):
        bset(b, s, 100)
    return b


class Grid:
    """A player's inventory page (10 x 4 for every class, inventory.txt gridX/gridY)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.cell = [[0] * w for _ in range(h)]

    def free(self, row, col, w, h):
        """0x0063A8A0."""
        return all(self.cell[r][c] == 0 for r in range(row, row + h) for c in range(col, col + w))

    def score(self, row, col, w, h):
        """0x0063B340: occupied or outside cells along the four sides; 255 when enclosed."""
        n = 0
        if col > 0:
            n += sum(1 for r in range(row, row + h) if self.cell[r][col - 1])
        else:
            n = h
        if col + w < self.w:
            n += sum(1 for r in range(row, row + h) if self.cell[r][col + w])
        else:
            n += h
        if row > 0:
            n += sum(1 for c in range(col, col + w) if self.cell[row - 1][c])
        else:
            n += w
        if row + h < self.h:
            n += sum(1 for c in range(col, col + w) if self.cell[row + h][c])
        else:
            n += w
        return 255 if n >= 2 * (w + h) else n

    def find(self, w, h):
        """0x0063B490 (one-row items: columns from the right, rows from the bottom) and 0x0063B620 (rows from the top,
        columns from the left) for a player's page; the best score wins (strictly greater), 255 ends the search."""
        best, at = 0, None
        if h == 1:
            order = [(r, c) for c in range(self.w - 1, -1, -1) for r in range(self.h - 1, -1, -1)]
        else:
            order = [(r, c) for r in range(self.h) for c in range(self.w)]
        for r, c in order:
            if self.cell[r][c] or c + w > self.w or r + h > self.h or not self.free(r, c, w, h):
                continue
            s = self.score(r, c, w, h)
            if s > best:
                best, at = s, (c, r)
                if s == 255:
                    break
        return at

    def put(self, x, y, w, h, u):
        for r in range(y, y + h):
            for c in range(x, x + w):
                self.cell[r][c] = u


class Ctx:
    def __init__(self, ev, i=0):
        self.ev, self.i = ev, i

    def peek(self):
        return self.ev[self.i][0] if self.i < len(self.ev) else None

    def take(self, tag):
        while self.i < len(self.ev) and self.ev[self.i][0] in SKIP:
            self.i += 1
        if self.i >= len(self.ev):
            raise Mismatch("missing %s" % tag)
        t, d = self.ev[self.i]
        if t != tag:
            raise Mismatch("expected %s, log has %s %s" % (tag, t, json.dumps(d)[:300]))
        self.i += 1
        return d


SKIP = {"RNG", "XK0", "XC0", "XCP", "XCR", "XC85", "XCX", "XA0", "XAX", "LU0", "LUX", "LUM", "GL0", "LCG"}


def check_item_copy(T, X, ctx, slot, idx, cs, player, gs, ilvl, S, made, pdt):
    """One starting item copy: SIC0 .. ISL. Returns (gs, item state dict for the save)."""
    d = ctx.take("SIC0")
    eq("StartItemCreate slot", slot, d["slot"])
    eq("StartItemCreate item index (ITEMS_GetByCode)", idx, d["idx"])
    eq("game seed at StartItemCreate", fmt(gs), d["gs"])
    d = ctx.take("CREC")
    for k, v in (("src", player), ("ilvl", ilvl), ("idx", idx), ("k18", 4), ("w28", 1), ("ver", X["iver"]),
                 ("q", 2), ("row1", 0), ("pre", [0, 0, 0]), ("suf", [0, 0, 0]), ("rfl", 0x08 | 0x02)):
        eq("creation record %s" % k, v, d[k])
    eq("game seed at ItemCreate", fmt(gs), d["gs"])
    gs = rng.step(*gs)
    lo = gs[0]
    gs = rng.step(*gs)
    start = gs[0]
    iis0 = ctx.take("IIS0")
    eq("item unit seed (SUnitCreate: init(step(game seed)))", fmt((lo, 666)), iis0["useed"])
    eq("start seed (ItemSeedInit: the next game-seed step)", start, iis0["start"])
    eq("item seed {start, 666}", fmt((start, 666)), iis0["iseed"])
    iis1 = ctx.take("IIS1")
    props.check_iis(T.P, iis0, iis1, S)
    S["ItemInitStats predicted"] += 1
    blk = []
    while True:
        if ctx.i >= len(ctx.ev):
            raise Mismatch("ItemCreateByQuality block not closed")
        t, dd = ctx.ev[ctx.i]
        ctx.i += 1
        if t in SKIP:
            continue
        blk.append((t, dd))
        if t == "LX":
            break
    if blk[0][0] != "IC0":
        raise Mismatch("expected IC0 after ItemInitStats, log has %s" % blk[0][0])
    ic = blk[0][1]
    eq("IC0 item seed", fmt((start, 666)), ic["seed"])
    r_ic = props.check_ic(T.P, blk, made, collections.Counter(), None, pdt, S, iis1=iis1)
    if "skip" in r_ic:
        raise Mismatch("ItemCreateByQuality skipped: %s" % r_ic["skip"])
    boundary = None
    n0 = S["staff mods: exit not checkable"]
    items_chain.check_creation(T.A, blk, S)
    if S["staff mods: exit not checkable"] > n0:
        # the normal builder ends in ITEMS_RollStaffMods on a StaffMods type (items/0005 boundary): its exit seed
        # (the join, ICJ) is the log's, not the model's
        boundary = "ITEMS_RollStaffMods (normal builder exit seed taken from the log)"
    st = r_ic.get("state")
    if st is None and r_ic.get("final") == 2:
        st = props.Item(T.P, ic["cls"], 2, ic["ilvl"], ic["ver"], ic["fl"], bdict(iis1.get("b")), [], ic["seed"])
    if st is None:
        raise Mismatch("item state after ItemCreateByQuality not tracked (%s)" % r_ic.get("final"))
    if r_ic.get("staffmods"):
        boundary = "ITEMS_RollStaffMods (staff-mod entries taken from the log)"
    x = ctx.take("CRECX")
    it = x["it"]
    eq("game seed after ItemCreate (two steps)", fmt(gs), x["gs"])
    eq("created class", idx, it["cls"])
    icx = [d_ for t_, d_ in blk if t_ == "ICX"][-1]
    eq("created item seed (ICX)", icx["seed"], it["seed"])
    eq("created item: Unit+0x28 = the first step's low word", lo, it["seed28"])
    eq("created item quality", 2, it["q"])
    eq("created item ilvl", ilvl, it["ilvl"])
    base = dict(st.base)
    subs = [[s_, f_, dict(e_)] for s_, f_, e_ in st.subs]
    if boundary:
        # the staff-mod entries come from the log (counted oracle); the rest must be the model's
        lb = bdict(it["b"])
        for k in list(lb):
            if k[0] == 107:
                base[k] = lb[k]
        subs = [[s_, f_, {(a, b_): v for a, b_, v in e_}] for s_, f_, e_ in it["sub"]]
    eq("created base entries", sorted(base.items()), sorted(bdict(it["b"]).items()))
    fl = st.flags | 0x10
    eq("created item flags (identified set by ITEMS_CreateForStore)", fl, it["fl"])
    # StartItemCreate: the 0x40 list removed, item_singleskill on slot 0, quantity
    subs = [s_ for s_ in subs if not s_[1] & 0x40]
    if slot == 0 and 0 <= cs["StartSkill"] < T.nskills and cs["StartSkill"] != 0xFFFF:
        subs.append([0, 0x40, {(107, cs["StartSkill"]): 1}])
    b = T.P.base(idx)
    if b["stackable"]:
        bset(base, 70, b["maxstack"])
    y = ctx.take("SICX")["it"]
    eq("StartItemCreate: base entries", sorted(base.items()), sorted(bdict(y["b"]).items()))
    lsub = sorted((s_, f_ & ~0x80000000 if False else f_, tuple(sorted(bdict(e_).items()))) for s_, f_, e_ in y["sub"])
    msub = sorted((s_, f_, tuple(sorted(e_.items()))) for s_, f_, e_ in subs)
    eq("StartItemCreate: attached lists (state, flags, entries)", [(a, c) for a, _, c in msub],
       [(a, c) for a, _, c in lsub])
    for (a1, f1, _), (a2, f2, _) in zip(msub, lsub):
        eq("StartItemCreate: attached list flag 0x40", f1 & 0x40, f2 & 0x40)
    S["StartItemCreate stat lists predicted"] += 1
    return gs, dict(it=it, base=base, subs=subs, st=st, lo=lo, start=start, fl=fl, idx=idx, boundary=boundary,
                    ic=ic, icx=icx)


def place(T, X, slot, loc, idx, cpy, grid, belt, pcls):
    """StartItemSlot's placement for one copy. Returns (page, x, y, body, where)."""
    raw = T.item_raw(idx)
    b = T.P.base(idx)
    w, h = b["invw"], b["invh"]
    if T.beltable(idx):
        # sub_0055E9B0_ItemToBelt(.., 1) -> 0x0063C790 -> 0x0063C600 on the default belt (no belt equipped)
        n = T.belt_boxes[2]
        at = None
        if w == 1 and h == 1:
            for i in range(4):
                if belt.get(i) is not None and belt[i] == idx:
                    j = i
                    while j < n:
                        if belt.get(j) is None:
                            at = j
                            break
                        j += 4
                    if at is not None:
                        break
            if at is None and raw[0x131]:
                for i in range(4):
                    if belt.get(i) is None:
                        at = i
                        break
        if at is not None:
            belt[at] = idx
            return ("belt", at, 0, 0)
    elif loc:
        return ("equip", loc, 0, loc)
    at = grid.find(w, h)
    if at is None:
        raise Mismatch("no inventory spot for item %d" % idx)
    grid.put(at[0], at[1], w, h, idx + 1)
    return ("inv", at[0], at[1], 0)


def check_nc(T, blk, S, made, pdt, saved, res):
    ev = blk
    for t, d in ev:
        if t == "RNG":
            if d["game"] or d["unit"]:
                raise Mismatch("RNG-function call on the %s seed inside NewCharFromStub: %s" % (
                    "game" if d["game"] else "player unit", json.dumps(d)))
            S["RNG-function calls inside NewCharFromStub on other seeds (item creation): %s" % d["fn"]] += 1
    ctx = Ctx(ev)
    c = ctx.take("NC0")
    gs = seedpair(c["gs"])
    cls = c["cls"]
    X = {"iver": c["iver"], "exp": c["exp"]}
    res.update(cls=cls, name=c["name"], status=c["status"], act=c["act"], exp=c["exp"], diff=c["diff"])
    u = ctx.take("NCU")
    eq("SUnitCreate(player) draws nothing on the game seed", fmt(gs), u["gs"])
    player = u["u"]
    d = ctx.take("NCP")
    gs = rng.step(*gs)
    eq("PlayerUnitInit: one game-seed step", fmt(gs), d["gs"])
    eq("player Unit+0x28 = the step's low word", gs[0], d["seed28"])
    eq("player unit seed {low, 666}", fmt((gs[0], 666)), d["useed"])
    eq("player mode", 1, d["mode"])
    res["player_seed28"] = gs[0]
    d = ctx.take("NCS")
    eq("game seed after the unit is sent to the client (no draw)", fmt(gs), d["gs"])
    # PLAYER_InitBaseStats; under -act N, PLAYER_GrantLevel's AddExperience/LevelUp lines come in between
    if cls >= len(T.cs):
        b = {}
        S["class without a CharStats record (no stats, items or start skill)"] += 1
    else:
        b = start_stats(T, cls)
        act = min(c["act"], 4)
        if act:
            lvl = ACT_START_LEVEL[act]
            exp = T.threshold(cls, lvl)
            add = exp - bget(b, 13)
            bset(b, 29, add)
            bset(b, 13, exp)
            level_up(T, cls, b, exp)
            S["-act start: PLAYER_GrantLevel(%d) -> level %d" % (lvl, bget(b, 12))] += 1
    d = ctx.take("NCB")
    eq("game seed after PLAYER_InitBaseStats", fmt(gs), d["gs"])
    diff_b(b, bdict(d["b"]), "PLAYER_InitBaseStats base entries")
    S["PLAYER_InitBaseStats predicted"] += 1
    ilvl = max(bget(b, 12), 1)
    res["level"] = bget(b, 12)
    # PLAYER_GiveStartItems
    gw, gh = T.grid.get(CLASSES[cls] if cls < 7 else "Amazon", (10, 4))
    grid = Grid(gw, gh)
    belt = {}
    items = []
    if cls < len(T.cs):
        cs = T.cs[cls]
        for slot, code, loc, cnt in T.start_items(cls):
            idx = T.codes.get(code)
            if idx is None:
                continue
            for k in range(cnt):
                gs, itm = check_item_copy(T, X, ctx, slot, idx, cs, player, gs, ilvl, S, made, pdt)
                if itm["boundary"]:
                    S["ItemCreate boundary oracle: %s (%s)" % (itm["boundary"], code)] += 1
                    res.setdefault("boundary", []).append(code)
                else:
                    S["starting item creations reproduced through the item model (%s)" % code] += 1
                pl = place(T, X, slot, loc, idx, k, grid, belt, cls)
                d = ctx.take("ISL")
                it = d["it"]
                eq("ISL slot", slot, d["slot"])
                eq("ISL copy", k, d["copy"])
                eq("game seed after the copy", fmt(gs), d["gs"])
                fl = itm["fl"] | 0x20000
                base = itm["base"]
                st = itm["st"]
                if not T.beltable(idx) or pl[0] != "belt":
                    pass
                q5 = T.P.is_type(idx, 5)
                if not T.beltable(idx):
                    st2 = props.Item(T.P, idx, 2, ilvl, X["iver"], fl, base,
                                     [[a, f_, e_] for a, f_, e_ in itm["subs"]], itm["icx"]["seed"])
                    if q5:
                        bset(base, 70, 250)
                        if not loc:
                            bset(base, 70, 100)
                    else:
                        bset(base, 72, st2.eval_maxdur())
                if pl[0] == "equip":
                    fl |= 1                 # 0x005606B0: ITEMS_SetFlag(item, 1, 1) when equipped
                eq("starting item flags (0x20000 starter, 0x1 when equipped)", fl, it["fl"])
                eq("item mode (0 inventory, 1 equipped, 2 belt)", {"inv": 0, "equip": 1, "belt": 2}[pl[0]], it["mode"])
                eq("body location (ItemData+0x44)", loc, it["body"])
                diff_b(base, bdict(it["b"]), "starting item %s base entries after placement" % code)
                where = {"belt": 2, "equip": 1, "inv": 0}[pl[0]]
                if pl[0] == "inv":
                    eq("inventory page (ItemData+0x45)", 0, it["page"])
                    eq("inventory cell (x, y)", [pl[1], pl[2]], it["xy"])
                elif pl[0] == "belt":
                    eq("belt slot (x, 0)", [pl[1], 0], it["xy"])
                    eq("page of a belt item", 255, it["page"])
                else:
                    eq("equipped: (body location, 0)", [loc, 0], it["xy"])
                    eq("page of an equipped item", 255, it["page"])
                S["placements predicted: %s" % pl[0]] += 1
                items.append(dict(slot=slot, code=code, idx=idx, pl=pl, where=where, fl=fl, base=base, subs=itm["subs"],
                                  seed28=itm["lo"], ilvl=ilvl, it=it))
    d = ctx.take("NCI")
    eq("game seed after PLAYER_GiveStartItems", fmt(gs), d["gs"])
    d = ctx.take("NCQ")
    eq("game seed before QuestsPlayerJoin", fmt(gs), d["gs"])
    right = 0
    if cls < len(T.cs) and c["act"] == 0:
        ss = T.cs[cls]["StartSkill"]
        if ss not in (0, 0xFFFF) and 0 <= ss < T.nskills:
            right = ss
    eq("right skill (player data +0x70)", right, d["pd70"])
    eq("left skill (player data +0x74)", 0, d["pd74"])
    d = ctx.take("NCX")
    eq("game seed after QuestsPlayerJoin (no draw)", fmt(gs), d["gs"])
    p = d["p"]
    # the skill list: Attack, then Skill 1..10 (valid ids, column order), level 1, item ref -1; then the skill item1
    # grants through item_singleskill once it is equipped: an entry of base level 0 (SKILLS_AddSkill's entry +0x08 =
    # the skills record's byte +0x10; Assassin's Left Hand Swing 16)
    want = [(0, 1)]
    if cls < len(T.cs):
        for k in range(1, 11):
            s_ = T.cs[cls]["Skill %d" % k]
            if 0 <= s_ < T.nskills and s_ != 0xFFFF and s_ not in [w[0] for w in want]:
                want.append((s_, 1))
    ss = T.cs[cls]["StartSkill"] if cls < len(T.cs) else 0xFFFF
    if 0 <= ss < T.nskills and ss != 0xFFFF and any(x["slot"] == 0 and x["pl"][0] == "equip" for x in items) \
            and ss not in [w[0] for w in want]:
        want.append((ss, 0))
    eq("skill list (id, level) in list order", want, [(e[0], e[1]) for e in p["skills"]])
    for sid, lvl, iref, e8 in p["skills"]:
        eq("skill %d item ref" % sid, -1, iref)
        e8m = 16 if (cls == 6 and sid == 5) else T.skill_b10[sid]
        eq("skill %d entry +0x08" % sid, e8m, e8)
    eq("skill list right skill", right, p["right"])
    eq("skill list left skill", 0, p["left"])
    S["skill lists predicted"] += 1
    eq("item count on the player", len(items), len(p["items"]))
    res["items"] = items
    res["gs_exit"] = fmt(gs)
    res["right"] = right
    res["map"] = c["map"]
    res["b"] = b
    return ctx.i


# ---------------------------------------------------------------- the stub

GAME_EXE = os.path.join(os.path.dirname(HERE), "workspace", "install", "app", "game.exe")


def default_gfx():
    """The 16 bytes sub_0043C540_StubBuild copies from data 0x0070CCC8 (.data: file offset 0x305000 + VA - 0x705000)."""
    with open(GAME_EXE, "rb") as fh:
        fh.seek(0x305000 + 0x0070CCC8 - 0x00705000)
        return fh.read(16)


def check_stub(T, rh, ret, nc0, S):
    """The 335-byte stub the server read (RHDR) against sub_0043C540_StubBuild's layout, and D2S_ReadHeader's 2."""
    b = bytes.fromhex(rh["hex"])
    eq("stub length", 0x14F, rh["len"])
    eq("stub magic", 0xAA55AA55, struct.unpack_from("<I", b, 0)[0])
    eq("stub version", 96, struct.unpack_from("<I", b, 4)[0])
    eq("stub size field", 0x14F, struct.unpack_from("<I", b, 8)[0])
    eq("stub checksum", d2s.checksum(b), struct.unpack_from("<I", b, 0x0C)[0])
    eq("stub name", nc0["name"], b[0x14:0x24].split(b"\0")[0].decode("latin1"))
    st = b[0x24]
    eq("stub status bit 0 (new)", 1, st & 1)
    eq("stub status = the client's status | 1 (bit 0 cleared by D2S_ReadHeader)", nc0["status"] | 1, st)
    if nc0["cls"] in (5, 6):
        eq("stub status bit 0x20 for class 5 or 6", 0x20, st & 0x20)
    eq("stub class", nc0["cls"], b[0x28])
    eq("stub 0x29, 0x2A, level", (16, 30, 1), (b[0x29], b[0x2A], b[0x2B]))
    eq("stub 0x2C = 0x30 (time(NULL) twice)", b[0x2C:0x30], b[0x30:0x34])
    eq("stub 0x88..0x97 = the default graphics (0x0070CCC8)", default_gfx(), b[0x88:0x98])
    eq("stub 0x98..0xA7 = 0xFF", b"\xff" * 16, b[0x98:0xA8])
    rest = b[0x10:0x14] + b[0x25:0x28] + b[0x34:0x88] + b[0xA8:]
    eq("stub: every other byte 0", bytes(len(rest)), rest)
    eq("D2S_ReadHeader return for a stub", 2, ret["code"])
    S["stubs checked (RHDR: StubBuild layout, ReadHeader 2)"] += 1


# ---------------------------------------------------------------- the first save

def predict_save(T, res):
    """The parsed .d2s fields the first save of a new character must have (tools/d2s.py parse names)."""
    cls = res["cls"]
    hd = {"name": res["name"], "cls": cls, "level": res["level"], "map_seed": res["map"], "progression": 0,
          "status": (res["status"] & ~1) & 0xFFFF, "version": 96, "weapon_set": 0, "unk_29": 16 | 30 << 8,
          "unk_2c": 0, "unk_34": 0xFFFFFFFF, "hotkeys": [0xFFFF] * 16, "mouse": [0, res["right"], 0, 0],
          "difficulty": bytes([0x80 | res["act"], 0, 0]), "unk_af": 0, "merc_dead": 0, "merc_seed": 0,
          "merc_name": 0, "merc_type": 0, "merc_exp": 0}
    stats = []
    b = res["b"]
    for sid in range(16):
        v = bget(b, sid)
        if v:
            stats.append((sid, None, v))
    items = []
    for it in res["items"]:
        raw = T.item_raw(it["idx"])
        pl = it["pl"]
        d = {"code": it["code"].ljust(4), "identified": 1, "starter": 1, "ethereal": 0, "socketed": 0}
        if pl[0] == "belt":
            d.update(location=2, body=0, x=pl[1], y=0, store=0)
        elif pl[0] == "equip":
            d.update(location=1, body=pl[3], x=pl[3], y=0, store=0)
        else:
            d.update(location=0, body=0, x=pl[1], y=pl[2], store=1)
        items.append(d)
    return hd, stats, items


SECTIONS = {}


def compare_save(T, res, data, S, what):
    isc, kinds = d2s.load_isc(T.excel), d2s.load_kinds(T.excel)
    f = d2s.parse(data, isc, kinds)
    hd, stats, items = predict_save(T, res)
    h = f["header"]
    for k, v in hd.items():
        if k == "status":
            eq("%s header status" % what, v, h[k])
        else:
            eq("%s header %s" % (what, k), v, h[k])
    sec = bytes(data[0x14F:data.index(b"gf", 0x14F)])
    key = "expansion" if res["exp"] else "classic"
    ref = SECTIONS.setdefault(key, sec)
    eq("%s quest, waypoint and npc sections = every other new %s character's" % (what, key), ref, sec)
    S["quest/waypoint/npc sections identical across new characters (%s)" % key] += 1
    eq("%s no corpse, no golem" % what, (0, False), (len(f.get("corpses") or []), bool(f.get("golem"))))
    eq("%s character stats" % what, stats, [tuple(x) for x in f["stats"]])
    eq("%s class skill bytes (all 0)" % what, [0] * len(f["skills"]), f["skills"])
    fit = f["items"]["items"]
    eq("%s item count" % what, len(items), len(fit))
    # order: the save writes the player's item list; match by (code, location, x, y)
    for m, it in zip(items, res["items"]):
        cand = [x for x in fit if x["code"] == m["code"] and x["location"] == m["location"]
                and x.get("body") == m["body"] and (m["location"] == 1 or (x["x"], x["y"]) == (m["x"], m["y"]))]
        if not cand:
            raise Mismatch("%s: no saved item %s at %s" % (what, m["code"], m))
        x = cand[0]
        fit.remove(x)
        for k, v in m.items():
            eq("%s item %s %s" % (what, m["code"], k), v, x[k])
        # the file flags: the runtime flags with bit 19 cleared and bit 23 set, bit 21 for a compact (simple) item
        # (save/0001, as tools/d2sio.py checks them)
        # (save/0001, as tools/d2sio.py checks them); bit 0, set by the equip at creation, is clear again by the save
        # (cleared after NewCharFromStub; not followed here, counted)
        want_fl = (it["fl"] & ~0x80001) | 0x800000 | (0x200000 if x["simple"] else 0)
        if it["fl"] & 1:
            S["saved equipped items: flag 0x1 of the equip cleared by the save"] += 1
        eq("%s item %s flags" % (what, m["code"]), want_fl, x["flags"])
        eq("%s item %s simple = misc compactsave" % (what, m["code"]), T.compact(it["idx"]), bool(x["simple"]))
        if not x["simple"]:
            eq("%s item %s seed (Unit+0x28)" % (what, m["code"]), it["seed28"], x["seed"])
            eq("%s item %s ilvl" % (what, m["code"]), it["ilvl"], x["ilvl"])
            eq("%s item %s quality" % (what, m["code"]), 2, x["quality"])
            base = it["base"]
            if x.get("maxdur") is not None and x.get("maxdur"):
                eq("%s item %s max durability" % (what, m["code"]), bget(base, 73), x["maxdur"])
                eq("%s item %s durability" % (what, m["code"]), bget(base, 72), x["dur"])
            if "defense" in x:
                eq("%s item %s defense" % (what, m["code"]), bget(base, 31), x["defense"])
            if "quantity" in x:
                eq("%s item %s quantity" % (what, m["code"]), bget(base, 70), x["quantity"])
            want = sorted([[s_, p_, [v_]] for st_, fl_, e_ in it["subs"] for (s_, p_), v_ in e_.items()])
            eq("%s item %s property list" % (what, m["code"]), want,
               sorted([list(p_[:2]) + [list(p_[2])] for p_ in (x.get("props") or [])]))
        S["saved items predicted field by field"] += 1
    S["first saves predicted field by field"] += 1


# ---------------------------------------------------------------- log driver

def events(path):
    out = []
    for line in open(path, errors="replace"):
        tag, _, rest = line.rstrip("\n").partition(" ")
        if rest.startswith("{"):
            try:
                out.append((tag, json.loads(rest)))
            except ValueError:
                pass
    return out


ITEM_TAGS = set(uniques.TAGS) | props.PTAGS | {"IIS0", "IIS1"}
NC_TAGS = {"NC0", "NCU", "NCP", "NCS", "NCB", "NCI", "NCQ", "NCX", "SIC0", "CREC", "CRECX", "SICX", "ISL"}
XP_TAGS = {"XK0", "XC0", "XCP", "XCR", "XC85", "XCX", "XA0", "XAX", "LU0", "LUX", "LUM", "GL0", "RNG", "LCG"}


def cmd_check(ns):
    T = Tables(ns.excel)
    affixes.PROPS_HOOK = items_chain.make_hook(T.P)
    S = collections.Counter()
    ok = bad = 0
    lu_ok = lu_bad = 0
    cases = collections.Counter()
    for path in ns.logs:
        ev = events(path)
        pdt = (0, 0)
        for t, d in ev:
            if t == "PDT":
                pdt = (d["c6c"], d["c70"])
                break
        made = set()
        xs = XpState()
        xs.cls_of, xs.last_xc, xs.leveled = {}, {}, []
        i = 0
        pending = []
        while i < len(ev):
            t, d = ev[i]
            if t == "NC0":
                th = d["th"]
                rh = ret = None
                for k in range(i - 1, -1, -1):
                    if ev[k][0] == "RHRET" and ret is None:
                        ret = ev[k][1]
                    if ev[k][0] == "RHDR":
                        rh = ev[k][1]
                        break
                try:
                    if rh is None or ret is None:
                        raise Mismatch("no RHDR/RHRET before NC0")
                    check_stub(T, rh, ret, d, S)
                except Mismatch as e:
                    bad += 1
                    print("FAIL %s stub of %s: %s" % (os.path.basename(path), d.get("name"), e))
                j = i
                blk = []
                while j < len(ev):
                    tj, dj = ev[j]
                    if tj in NC_TAGS | XP_TAGS or tj in props.PTAGS or tj in ("IIS0", "IIS1", "IC0"):
                        if dj.get("th", th) == th:
                            blk.append((tj, dj))
                    elif tj in uniques.TAGS:
                        blk.append((tj, dj))
                    j += 1
                    if tj == "NCX" and dj.get("th") == th:
                        break
                res = {}
                try:
                    # experience lines inside (the -act grant) go through the experience checker too
                    for tx, dx in blk:
                        if tx in XP_TAGS:
                            check_xp_line(T, tx, dx, xs, S)
                    check_nc(T, blk, S, made, pdt, None, res)
                    ok += 1
                    kind = "%s %s%s%s" % (CLASSES[res["cls"]] if res["cls"] < 7 else res["cls"],
                                         "expansion" if res["exp"] else "classic",
                                         " hardcore" if res["status"] & 4 else "",
                                         " act %d" % (res["act"] + 1) if res["act"] else "")
                    cases[kind] += 1
                    if ns.verbose:
                        print("ok   %s %s: %s, level %d, %d items, game seed %s -> %s" % (
                            os.path.basename(path), res["name"], kind, res["level"], len(res["items"]),
                            d["gs"], res["gs_exit"]))
                    pending.append(res)
                except (Mismatch, affixes.Mismatch, KeyError, IndexError, TypeError, ValueError) as e:
                    bad += 1
                    print("FAIL %s new character %s (class %s): %s" % (os.path.basename(path), d.get("name"),
                                                                       d.get("cls"), e))
                i = j
                continue
            if t in XP_TAGS:
                try:
                    n0 = S["PLAYER_LevelUp reproduced"]
                    check_xp_line(T, t, d, xs, S)
                    if S["PLAYER_LevelUp reproduced"] > n0:
                        lu_ok += 1
                except (Mismatch, KeyError, IndexError, TypeError) as e:
                    lu_bad += 1
                    print("FAIL %s %s: %s" % (os.path.basename(path), t, e))
            if t == "WDONE" and pending:
                data = bytes.fromhex(d["hex"]) if "hex" in d else None
                name = os.path.basename(d.get("path", "")).rsplit(".", 1)[0].replace("\\", "/").split("/")[-1]
                for res in list(pending):
                    if res["name"].lower() == name.lower().split("\\")[-1] and data is not None:
                        try:
                            compare_save(T, res, data, S, "first save of %s" % res["name"])
                        except (Mismatch, KeyError, IndexError, TypeError, d2s.D2sError) as e:
                            bad += 1
                            print("FAIL %s first save of %s: %s" % (os.path.basename(path), res["name"], e))
                        pending.remove(res)
            i += 1
        for res in pending:
            S["new characters with no save logged after them"] += 1
        for cls, a, b in xs.leveled:
            cases["level-up %s %d -> %d" % (CLASSES[cls] if 0 <= cls < 7 else cls, a, b)] += 1
    print("== tools/player.py check ==")
    print("%d new characters reproduced, %d failed; %d level-ups reproduced, %d experience lines failed" % (
        ok, bad, S["PLAYER_LevelUp reproduced"], lu_bad))
    for k in sorted(cases):
        print("  case %-60s %d" % (k, cases[k]))
    for k in sorted(S):
        print("  %-78s %d" % (k, S[k]))
    return 0 if not bad and not lu_bad and (ok or S["PLAYER_LevelUp reproduced"]) else 1


# ---------------------------------------------------------------- loadcheck

CHANGED = ("last_played", "checksum", "map_seed", "difficulty")


def cmd_loadcheck(ns):
    isc, kinds = d2s.load_isc(ns.excel), d2s.load_kinds(ns.excel)
    if len(ns.files) % 2:
        print("pairs of files expected")
        return 2
    n = bad = 0
    changed = collections.Counter()
    for a, b in zip(ns.files[::2], ns.files[1::2]):
        da, db = open(a, "rb").read(), open(b, "rb").read()
        fa, fb = d2s.parse(da, isc, kinds), d2s.parse(db, isc, kinds)
        errs = []
        cmp = 0
        for k in sorted(set(fa["header"]) | set(fb["header"])):
            va, vb = fa["header"].get(k), fb["header"].get(k)
            cmp += 1
            if va != vb:
                if k in CHANGED:
                    changed[k] += 1
                else:
                    errs.append("header %s: built %r, written %r" % (k, va, vb))
        for part in ("stats", "skills", "golem"):
            cmp += 1
            if fa.get(part) != fb.get(part):
                errs.append("%s differ" % part)
        ia, ib = fa["items"]["items"], fb["items"]["items"]
        if len(ia) != len(ib):
            errs.append("item count %d vs %d" % (len(ia), len(ib)))
        for x, y in zip(ia, ib):
            for k in sorted(set(x) | set(y)):
                if k in ("off", "end"):
                    continue
                cmp += 1
                if x.get(k) != y.get(k):
                    if (k == "new" and (x[k], y[k]) == (1, 0)) or (k == "flags" and x[k] ^ y[k] == 0x2000
                                                                    and x[k] & 0x2000):
                        if k == "new":
                            changed["items whose flag 0x2000 (new) was cleared"] += 1
                        continue
                    errs.append("item %s %s: built %r, written %r" % (x.get("code"), k, x.get(k), y.get(k)))
        n += 1
        ha, hb = hashlib.sha256(da).hexdigest(), hashlib.sha256(db).hexdigest()
        st = "ok  " if not errs else "FAIL"
        print("%s %-10s built %s written %s  %d fields compared%s" % (
            st, os.path.basename(a), ha[:16], hb[:16], cmp, "" if not errs else ": " + "; ".join(errs[:6])))
        if errs:
            bad += 1
    print("%d saves loaded and written back, %d with differences outside %s; changed: %s" % (
        n, bad, "/".join(CHANGED), ", ".join("%s %d" % kv for kv in sorted(changed.items()))))
    return 0 if not bad and n else 1


def main(argv):
    ap = argparse.ArgumentParser(prog="player.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("logs", nargs="+")
    p.add_argument("--excel", default=EXCEL)
    p.add_argument("-v", "--verbose", action="store_true")
    q = sub.add_parser("loadcheck")
    q.add_argument("files", nargs="+")
    q.add_argument("--excel", default=EXCEL)
    ns = ap.parse_args(argv[1:])
    return cmd_check(ns) if ns.cmd == "check" else cmd_loadcheck(ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
