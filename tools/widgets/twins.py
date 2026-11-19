#!/usr/bin/env python3
"""Python twins of the scripted widgets (ADR-0037) and their fixture writer.

Usage:
  python3 -I tools/widgets/twins.py write      # rewrite tools/widgets/<name>/fixture.json from the twins
  python3 -I tools/widgets/twins.py check      # exit 1 when a fixture.json differs from its twin

A twin is a function of an existing model in tools/ (never a second copy of a rule). `rng`: tools/rng.py's
`rng_range` and `INIT_HIGH`; the draw stepper's inputs are a seed, a range n and a number of draws, and its output
is the seed after Init(seed) and after each of the draws (Range(n) on one seed). fixture.json holds
{"cases": [{"inputs": {...}, "expect": {...}}]}; tools/test_widgets.py compares widget.js's `compute` with it.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import rng  # noqa: E402
import struct  # noqa: E402
import monstats  # noqa: E402
import hirelings  # noqa: E402
import quality  # noqa: E402
import d2s  # noqa: E402
from fractions import Fraction  # noqa: E402

LIMITS = {"seed": (0, 0xFFFFFFFF), "n": (-5, 0x7FFFFFFF), "draws": (1, 12)}


def clamp(v, lo, hi):
    return min(hi, max(lo, int(v)))


def twin_rng(inputs, data):
    """Seed after Init(seed) and after each of `draws` Range(n) calls, with the results."""
    seed = clamp(inputs["seed"], *LIMITS["seed"])
    n = clamp(inputs["n"], *LIMITS["n"])
    draws = clamp(inputs["draws"], *LIMITS["draws"])
    low, high = seed, rng.INIT_HIGH
    rows = []
    for k in range(1, draws + 1):
        # rng_range takes the u32 pattern of n; a negative n is its two's complement
        result, low, high = rng.rng_range(low, high, n & 0xFFFFFFFF)
        rows.append({"k": k, "drew": n >= 1, "result": result, "low": low, "high": high})
    return {"seed": seed, "n": n, "draws": draws, "start": {"low": seed, "high": rng.INIT_HIGH}, "rows": rows}


# ---- monstat: tools/monstats.py's `monlvl_stats` (MonLvlStats mask 7) over a toy MonLvl and MonStats --------------------
def _mon_tables(data):
    """A monstats.Tables with no game data: the toy level rows and monsters packed at the offsets the model reads."""
    T = object.__new__(monstats.Tables)
    T.ml = []
    for r in data["levels"]["items"]:
        b = bytearray(0x78)
        for off, key in ((0x00, "ac"), (0x30, "hp"), (0x60, "xp")):
            for d in range(3):  # the column set single player reads (L = 1)
                struct.pack_into("<i", b, off + 0xC + 4 * d, r[f"{key}{d}"])
        T.ml.append(bytes(b))
    T.ms = []
    for m in data["monsters"]["items"]:
        b = bytearray(0x1A8)
        b[0x0C] = 4 if m["plain"] else 0
        for d in range(3):
            for off, key in ((0xB0, "mnhp"), (0xB6, "mxhp"), (0xBC, "ac"), (0xD4, "ex")):
                struct.pack_into("<h", b, off + 2 * d, m[f"{key}{d}"])
        T.ms.append(bytes(b))
    return T


def twin_monstat(inputs, data):
    lim = data["inputs"]
    monster = clamp(inputs["monster"], lim["monster"]["min"], lim["monster"]["max"])
    level = clamp(inputs["level"], lim["level"]["min"], lim["level"]["max"])
    asked = clamp(inputs["difficulty"], lim["difficulty"]["min"], lim["difficulty"]["max"])
    T = _mon_tables(data)
    stats = monstats.Model(T).monlvl_stats(monster, True, asked, level)
    row = -1 if level < 0 else min(level, len(T.ml) - 1)
    d = 0 if asked < 1 else min(asked, 2)
    base = [0, 0, 0, 0] if row < 0 else [T.ml32(T.ml[row], 0x30 + 0xC + 4 * d), T.ml32(T.ml[row], 0x30 + 0xC + 4 * d),
                                         T.ml32(T.ml[row], 0x00 + 0xC + 4 * d), T.ml32(T.ml[row], 0x60 + 0xC + 4 * d)]
    cell = [0, 0, 0, 0] if row < 0 else [T.m16(monster, 0xB0 + 2 * d), T.m16(monster, 0xB6 + 2 * d),
                                         T.m16(monster, 0xBC + 2 * d), T.m16(monster, 0xD4 + 2 * d)]
    return {"monster": monster, "level": level, "diff": d, "row": row, "scaled": not T.noratio(monster),
            "rowVals": base, "cell": cell, "result": stats}


# ---- merc: tools/hirelings.py's `set_level` (MERC_SetLevel) over toy hire-table rows ------------------------------------
def twin_merc(inputs, data):
    lim = data["inputs"]["level"]
    lvl = clamp(inputs["level"], lim["min"], lim["max"])
    T = object.__new__(hirelings.Tables)  # no game data: the toy band rows, no skills
    T.max_lvl = data["rule"]["maxLevel"]
    T.nskills = 0
    T.reqlevel = []
    T.rows = []
    for b in data["bands"]["items"]:
        row = {"Id": 1, "Version": 100, "Level": b["lv"], "Exp/Lvl": b["expl"], "Str": b["st"], "Str/Lvl": b["stl"],
               "Dex": b["dexb"], "Dex/Lvl": b["dxl"], "HP": b["hp"], "HP/Lvl": b["hpl"], "Defense": b["df"],
               "Def/Lvl": b["dfl"], "AR": b["ar"], "AR/Lvl": b["arl"], "Dmg-Min": b["dmin"], "Dmg-Max": b["dmax"],
               "Dmg/Lvl": b["dml"], "Resist": b["rs"], "Resist/Lvl": b["rsl"]}
        for i in range(1, 7):
            row.update({f"Skill{i}": 0, f"Mode{i}": 0, f"LvlPerLvl{i}": 0, f"Level{i}": 0})
        T.rows.append(row)
    band, st, _sk = hirelings.set_level(T, True, 1, lvl)
    d = lvl - T.rows[band]["Level"]
    # the names of stats 12, 30, 13 (minimum), 0, 2, 7, 31, 19, 23, 24, the shared resistance and 74
    stats = [st[12], st[30], st["13min"], st[0], st[2], st[7], st[31], st[19], st[23], st[24], st[39], st[74]]
    return {"level": lvl, "band": band, "dlt": d, "result": stats}


# ---- quality: tools/quality.py's `roll` over a toy item and the page's ItemRatio record ---------------------------------
class _QualityToy(quality.Tables):
    """quality.Tables with one item, one item type and the chosen ratio record; no game data."""

    def __init__(self, level, flags, record):
        item = bytearray(0x140)
        item[0xFD] = level
        self.items = [bytes(item)]
        ty = bytearray(0x30)
        ty[0x14], ty[0x15], ty[0x16] = flags  # Magic, Rare, Normal
        self.itypes = [bytes(ty)]
        self.ratio = [{"v": record, "ver": 1, "uber": 0, "cls": 0}]

    def select(self, item, version=100):
        return 0


# item kinds of the widget: ordinary, never rare, always magic, always normal -> the (Magic, Rare, Normal) type bytes
_KIND_FLAGS = [(0, 1, 0), (0, 0, 0), (1, 1, 0), (0, 1, 1)]


def twin_quality(inputs, data):
    lim = data["inputs"]
    ilvl = clamp(inputs["ilvl"], lim["ilvl"]["min"], lim["ilvl"]["max"])
    qlvl = clamp(inputs["qlvl"], lim["qlvl"]["min"], lim["qlvl"]["max"])
    mf = clamp(inputs["mf"], lim["mf"]["min"], lim["mf"]["max"])
    rec = clamp(inputs["record"], lim["record"]["min"], lim["record"]["max"])
    kind = clamp(inputs["kind"], lim["kind"]["min"], lim["kind"]["max"])
    w = [clamp(inputs[f"w{i}"], lim["word"]["min"], lim["word"]["max"]) for i in range(4)]
    row = next(r for r in data["records"]["items"] if r["rec"] == rec)
    rl = data["rule"]
    v = [row["uni"], row["uniDiv"], rl["uniqueMin"], row["rare"], row["rareDiv"], rl["rareMin"], row["set"], row["setDiv"],
         rl["setMin"], row["mag"], row["magDiv"], rl["magicMin"], row["hi"], row["hiDiv"], row["nor"], row["norDiv"]]
    T = _QualityToy(qlvl, _KIND_FLAGS[kind], v)
    trace, pre = [], []
    saved = quality.range_b
    quality.range_b = lambda seed, n: (0x80000000, seed)  # every draw loses, so every test the roll reaches is traced
    try:
        code, _seed, _why, _draws, _ri = quality.roll(T, 0, ilvl, w[:], (1, 666), mf, trace=trace, cf={"pre": pre})
    finally:
        quality.range_b = saved
    after_mf = {name: c for name, c, _mn, _w in pre}
    mins = {name: mn for name, _c, mn, _w in pre}
    codes = {"unique": 7, "set": 5, "rare": 6, "magic": 4, "superior": 3, "normal": 2}
    steps, outcomes = [], []
    reach = Fraction(1)
    for name, c, _x, _won in trace:
        num, den = (1, 1) if c < 1 else (min(128, c), c)
        win = Fraction(num, den)
        steps.append({"name": name, "rc": codes[name], "afterMf": after_mf.get(name), "min": mins.get(name),
                      "word": None if name in ("superior", "normal") else w[{"unique": 3, "set": 2, "rare": 1, "magic": 0}[name]],
                      "chance": c, "noDraw": c < 1, "winPpm": int(win * 1000000)})
        outcomes.append({"name": name, "rc": codes[name], "ppm": int(reach * win * 1000000)})
        reach *= 1 - win
        if reach == 0:
            break
    if not trace:
        outcomes.append({"name": "normal", "rc": 2, "ppm": 1000000})   # an always-normal type: no test
    elif reach > 0:
        outcomes.append({"name": "magic" if code == 4 else "low", "rc": code, "ppm": int(reach * 1000000)})
    return {"ilvl": ilvl, "qlvl": qlvl, "mf": mf, "record": rec, "kind": kind, "words": w, "gap": ilvl - qlvl,
            "steps": steps, "outcomes": outcomes}


# ---- checksum: tools/d2s.py's `checksum` on each prefix of the typed bytes ------------------------------------------------
def twin_checksum(inputs, data):
    rule = data["rule"]
    text = str(inputs["typed"])
    toks, bad, cur = [], False, ""
    for ch in text.lower():
        if ch in " ,":
            if cur:
                toks.append(cur)
            cur = ""
        elif ch in "0123456789abcdef":
            cur += ch
        else:
            bad, cur = True, ""
    if cur:
        toks.append(cur)
    bad = bad or any(len(t) > 2 for t in toks)
    bytes_ = [] if bad else [int(t, 16) for t in toks]
    error = 1 if bad else (2 if len(bytes_) > rule["maxBytes"] else 0)
    if error:
        bytes_ = []
    steps = []
    for i, b in enumerate(bytes_):
        s = d2s.checksum(bytes(bytes_[:i + 1]))
        used = 0 if rule["skipFrom"] <= i < rule["skipTo"] else b
        steps.append({"i": i, "byte": b, "used": used, "rot": (s - used) & 0xFFFFFFFF, "sum": s})
    return {"fault": error, "tally": len(bytes_), "steps": steps, "whole": d2s.checksum(bytes(bytes_))}


TWINS = {"rng": twin_rng, "monstat": twin_monstat, "merc": twin_merc, "quality": twin_quality,
         "checksum": twin_checksum}

# inputs of each widget's fixture: the page's worked example first (seed 12345, range 100: 87, low 015B2E77, high
# 0000141D), then n below 1 (no draw), n = 1, a power of two, the largest n, seeds at the ends of u32, a carry-heavy
# seed, and out-of-range inputs that are clamped.
CASES = {"rng": [
    {"seed": 12345, "n": 100, "draws": 1},
    {"seed": 12345, "n": 100, "draws": 5},
    {"seed": 12345, "n": 0, "draws": 3},
    {"seed": 12345, "n": -5, "draws": 3},
    {"seed": 12345, "n": 8, "draws": 4},
    {"seed": 12345, "n": 7, "draws": 4},
    {"seed": 0, "n": 1, "draws": 12},
    {"seed": 1, "n": 2147483647, "draws": 12},
    {"seed": 4294967295, "n": 7, "draws": 12},
    {"seed": 4294967295, "n": 4294967295, "draws": 2},
    {"seed": 2863311530, "n": 256, "draws": 6},
    {"seed": -3, "n": 99999999999, "draws": 40},
    {"seed": 12345, "n": -99, "draws": 0},
],
    "monstat": [
        {"monster": 0, "level": 7, "difficulty": 0},
        {"monster": 0, "level": 7, "difficulty": 1},
        {"monster": 0, "level": 7, "difficulty": 2},
        {"monster": 1, "level": 7, "difficulty": 0},
        {"monster": 1, "level": 19, "difficulty": 2},
        {"monster": 0, "level": 0, "difficulty": 0},
        {"monster": 0, "level": 19, "difficulty": 2},
        {"monster": 0, "level": 99, "difficulty": 1},
        {"monster": 0, "level": -1, "difficulty": 0},
        {"monster": 0, "level": -5, "difficulty": 2},
        {"monster": 0, "level": 12, "difficulty": -1},
        {"monster": 1, "level": 12, "difficulty": 5},
        {"monster": 0, "level": 3, "difficulty": 4},
        {"monster": 9, "level": 500, "difficulty": 0},
    ],
    "merc": [{"level": lv} for lv in (30, 1, 5, 6, 7, 20, 21, 44, 45, 97, 98, 99, 0, 500)],
    "quality": [
        {"ilvl": 28, "qlvl": 10, "mf": 100, "record": 2, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 28, "qlvl": 10, "mf": 0, "record": 2, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 28, "qlvl": 10, "mf": 10, "record": 3, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 28, "qlvl": 10, "mf": 11, "record": 4, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 49, "qlvl": 10, "mf": 100, "record": 2, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 22, "qlvl": 19, "mf": 0, "record": 2, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 30, "qlvl": 10, "mf": 300, "record": 5, "kind": 1, "w0": 200, "w1": 300, "w2": 400, "w3": 500},
        {"ilvl": 30, "qlvl": 10, "mf": 300, "record": 5, "kind": 2, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 30, "qlvl": 10, "mf": 100, "record": 2, "kind": 3, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 30, "qlvl": 10, "mf": -50, "record": 2, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 30, "qlvl": 10, "mf": -99, "record": 3, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 30, "qlvl": 10, "mf": -100, "record": 2, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 30, "qlvl": 10, "mf": -150, "record": 2, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 255, "qlvl": 0, "mf": 0, "record": 2, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 0, "qlvl": 255, "mf": 1000, "record": 4, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 28, "qlvl": 10, "mf": 100, "record": 2, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 1024},
        {"ilvl": 28, "qlvl": 10, "mf": 100, "record": 2, "kind": 0, "w0": 1024, "w1": 512, "w2": 0, "w3": 0},
        {"ilvl": 100, "qlvl": 1, "mf": 0, "record": 3, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0},
        {"ilvl": 400, "qlvl": -3, "mf": 5000, "record": 9, "kind": 7, "w0": 5000, "w1": -1, "w2": 0, "w3": 0},
    ],
    "checksum": [{"typed": b} for b in (
        "01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12", "01 02 03", "FF FF FF FF", "80 00 00 00 00", "",
        "0,1,2", "00 00 00 00 00 00 00 00 00 00 00 00 FF FF FF FF 01", "FF " * 32, "FF " * 33, "0102", "zz 01", "1 2 3 a b c")],
}

sys.path.insert(0, HERE)
import twins_x16c  # noqa: E402  (the seedtree and path twins)
TWINS.update(twins_x16c.TWINS)
CASES.update(twins_x16c.CASES)


# ---- tohit, damage, breakpoints (plan 0070 Phase 11 batch 3, lane x16a) ----
import anim_rates as AR  # noqa: E402
import combat  # noqa: E402
import monstats  # noqa: E402


def twin_tohit(inputs, data):
    """combat.tohit_chance (to-hit A3-A5), the function the log checker calls."""
    lim = data["inputs"]
    v = {k: clamp(inputs[k], lim[k]["min"], lim[k]["max"]) for k in ("ar", "pct", "def", "alvl", "dlvl")}
    t = combat.tohit_chance(v["ar"], v["def"], v["pct"], v["alvl"], v["dlvl"])
    after_def = t["ar3"] - v["def"] if v["def"] < 0 else t["ar3"]  # A4's first swap, then the second's test
    swap = {(True, True): "both", (True, False): "def", (False, True): "ar"}.get((v["def"] < 0, after_def < 0), "none")
    clamp_kind = "low" if t["c2"] <= 5 else ("high" if t["c2"] >= 95 else "none")
    return {"ar": v["ar"], "pct": v["pct"], "def": v["def"], "alvl": v["alvl"], "dlvl": v["dlvl"], "ar3": t["ar3"],
            "swap": swap, "arAfter": t["ar"], "defAfter": t["df"], "c1": t["c1"], "c2": t["c2"], "chance": t["c"],
            "clamp": clamp_kind}


DAMAGE_KEYS = ("wmin", "wmax", "add", "ed", "str", "strBonus", "dex", "dexBonus", "seed", "flat", "resist", "pct")


def twin_damage(inputs, data):
    """combat.phys_ed, phys_bounds, rng_range (the draw), percent_scale, resist_final and reduce_value."""
    lim = data["inputs"]
    v = {k: clamp(inputs[k], lim[k]["min"], lim[k]["max"]) for k in DAMAGE_KEYS}
    kind = inputs["kind"] if inputs["kind"] in lim["kind"]["items"] else lim["kind"]["default"]
    ed = combat.phys_ed(0, v["ed"], True, v["str"], v["dex"], v["strBonus"], v["dexBonus"], 0)
    mn, mx, lo, hi = combat.phys_bounds(v["wmin"] << 8, v["wmax"] << 8, v["add"] << 8, ed, 0, 0)
    phys, draw, drew = lo, 0, hi > lo
    seed = (v["seed"], rng.INIT_HIGH)
    if drew:
        draw, seed = combat.rng_range(seed, hi - lo)
        phys += draw
    phys = max(phys, 0)
    scaled = combat.percent_scale(phys, v["pct"])
    flat8 = v["flat"] << 8
    res, _cap = combat.resist_final(v["resist"], kind == "monster", combat.resist_cap_default(36))
    after_flat, final = 0, 0
    if scaled > 0:
        after_flat = scaled - flat8
        final = combat.reduce_value(scaled, flat8, res, False)
    return {"inputs": v, "kind": kind, "mn": mn, "mx": mx, "ed": ed, "lo": lo, "hi": hi, "gapLen": hi - lo,
            "drew": drew, "draw": draw, "low": seed[0], "high": seed[1], "phys": phys, "scaled": scaled,
            "flat8": flat8, "afterFlat": after_flat, "res": res, "final": final}


# the kinds of the breakpoints widget: the animation_rates bonus index, and the rate function of a factor
BP_BONUS = {"attack": 0, "cast": 2, "gethit": 1, "block": 3, "blockhs": 3}


def bp_rate(kind, spd, x):
    if kind == "attack":
        return AR.rate_attack(spd, x)
    if kind == "cast":
        return AR.rate_cast(spd, x - 100)
    if kind == "gethit":
        return AR.rate_gethit(spd, x - 50)
    return AR.rate_block(spd, x - (100 if kind == "blockhs" else 50), kind == "blockhs")


def bp_len(F, S, r):
    return AR.sched_len(F, S, 0)[0] if r == 0 else AR.closed_len(F, S, r)


def twin_breakpoints(inputs, data):
    """tools/anim_rates.py: bonus, the rate functions, closed_len, least_x and least_stat (timing J1, J2, K1-K3)."""
    lim, rule = data["inputs"], data["rule"]
    kind = inputs["kind"] if inputs["kind"] in lim["kind"]["items"] else lim["kind"]["default"]
    spec = next(q for q in rule["kinds"]["items"] if q["id"] == kind)
    F = clamp(inputs["nfr"], lim["nfr"]["min"], lim["nfr"]["max"])
    S = min(clamp(inputs["start"], lim["start"]["min"], lim["start"]["max"]), F - 1)
    spd = clamp(inputs["spd"], lim["spd"]["min"], lim["spd"]["max"])
    stat = clamp(inputs["stat"], lim["stat"]["min"], lim["stat"]["max"])
    term = clamp(inputs["term"], lim["term"]["min"], lim["term"]["max"])
    ev = clamp(inputs["evt"], lim["evt"]["min"], lim["evt"]["max"])
    t = term if kind == "attack" else 0
    assert rule["k"] == AR.BONUS[BP_BONUS[kind]][1] and rule["ticks"] == 256
    B = AR.bonus(BP_BONUS[kind], stat)
    x = spec["plus"] + B + t
    if kind == "attack":
        x = max(spec["lo"], min(spec["hi"], x))
    if kind == "cast":
        x = min(x, spec["hi"])
    r = bp_rate(kind, spd, x)
    n = bp_len(F, S, r)
    fire = AR.sched_len(F, S, r)[1].get(ev)  # E1's loop, not the closed form: frame ev's step, or none
    lens = {bp_len(F, S, bp_rate(kind, spd, xx)) for xx in range(spec["lo"], spec["hi"] + 1)
            if bp_rate(kind, spd, xx) != 0}
    rows = []
    for m in sorted((m for m in lens if m <= n), reverse=True):
        xm = AR.least_x(spd, F, S, m, spec["lo"], spec["hi"])
        least = None
        if xm is not None:
            if kind == "attack" and xm == spec["lo"]:
                least = 0
            else:
                y = xm - spec["plus"] - t
                least = 0 if y <= 0 else AR.least_stat(rule["k"], y)
        rows.append({"m": m, "fac": xm, "stat": least})
    return {"kind": kind, "nfr": F, "start": S, "spd": spd, "stat": stat, "term": t, "evt": ev, "bonus": B,
            "fac": x, "rt": r, "n": n, "fireAt": fire, "rows": rows[:rule["maxRows"]], "capped": len(rows) > rule["maxRows"]}


TWINS.update({"tohit": twin_tohit, "damage": twin_damage, "breakpoints": twin_breakpoints})

# tohit: an even match, weak and strong attackers, a negative defence, a negative attack rating (from a percent of -100
# and a negative input), both sides 0, the clamp at both ends, the big attack rating that takes the guarded product's
# other branch, level 0 for the defender, and out-of-range inputs that are clamped.
CASES["tohit"] = [
    {"ar": 500, "pct": 0, "def": 300, "alvl": 30, "dlvl": 30},
    {"ar": 500, "pct": 0, "def": 500, "alvl": 30, "dlvl": 30},
    {"ar": 100, "pct": 0, "def": 900, "alvl": 20, "dlvl": 60},
    {"ar": 6000, "pct": 50, "def": 800, "alvl": 85, "dlvl": 40},
    {"ar": 400, "pct": 0, "def": -250, "alvl": 30, "dlvl": 30},
    {"ar": -300, "pct": 0, "def": 200, "alvl": 30, "dlvl": 30},
    {"ar": 500, "pct": -100, "def": 200, "alvl": 30, "dlvl": 30},
    {"ar": -300, "pct": 0, "def": -100, "alvl": 30, "dlvl": 30},
    {"ar": 0, "pct": 0, "def": 0, "alvl": 1, "dlvl": 0},
    {"ar": 100000, "pct": 0, "def": 10, "alvl": 99, "dlvl": 1},
    {"ar": 10, "pct": 0, "def": 100000, "alvl": 1, "dlvl": 99},
    {"ar": 1500000, "pct": 1000, "def": 0, "alvl": 99, "dlvl": 99},
    {"ar": 1200000, "pct": 100, "def": 1500000, "alvl": 255, "dlvl": 255},
    {"ar": 1200000, "pct": 7, "def": 99999, "alvl": 50, "dlvl": 0},
    {"ar": 301, "pct": 33, "def": 77, "alvl": 12, "dlvl": 29},
    {"ar": -5000000, "pct": 5000, "def": 9999999999, "alvl": 0, "dlvl": -4},
]

DAMAGE_BASE = {"wmin": 10, "wmax": 25, "add": 0, "ed": 0, "str": 100, "strBonus": 100, "dex": 50, "dexBonus": 0,
               "seed": 12345, "flat": 0, "resist": 0, "pct": 100, "kind": "monster"}


def dcase(**kw):
    return dict(DAMAGE_BASE, **kw)


# damage: a plain weapon, enhanced damage with both shares, the -90 floor, a weapon with min 0 (the floors), max not
# above min (no draw), the pair's percent, a flat reduction beyond the damage (negative), resistances: partial,
# immune, negative, the player's cap and a monster's none; the seed at both ends; clamped inputs.
CASES["damage"] = [
    dcase(),
    dcase(wmin=20, wmax=40, add=5, ed=120, str=200, dex=80),
    dcase(wmin=20, wmax=40, ed=50, resist=60),
    dcase(wmin=20, wmax=40, ed=50, flat=8, resist=70, pct=17, kind="player"),
    dcase(wmin=20, wmax=40, ed=50, resist=70, kind="monster"),
    dcase(wmin=0, wmax=0),
    dcase(wmin=30, wmax=30),
    dcase(wmin=30, wmax=10, ed=-100, str=0, dex=0),
    dcase(ed=-100, strBonus=0, dexBonus=0),
    dcase(flat=2000),
    dcase(resist=100),
    dcase(resist=250, kind="player"),
    dcase(resist=-60),
    dcase(resist=-200, kind="player"),
    dcase(wmin=500, wmax=2000, add=2000, ed=1000, str=1000, dex=1000, dexBonus=200, strBonus=200, pct=1000),
    dcase(pct=1, flat=1),
    # the damage page's worked example: strength 405 with a weapon of strength bonus 100, damage 32 to 87
    dcase(wmin=32, wmax=87, str=405, dex=0, dexBonus=0, seed=17),
    dcase(seed=0),
    dcase(seed=4294967295, wmin=1, wmax=2),
    dcase(wmin=-9, wmax=99999, seed=-5, kind="nobody", pct=0),
]

BP_BASE = {"kind": "attack", "nfr": 16, "start": 0, "spd": 256, "stat": 0, "term": 100, "evt": 7}


def bcase(**kw):
    return dict(BP_BASE, **kw)


# breakpoints: each kind at no stat and at a stat that crosses breakpoints; the spec's illustrations (a 14-frame cast at
# speed 256 with an event at 7, a 5-frame get-hit), a weapon term, a start frame, an event that does not fire, a slow
# speed that gives a rate of 0, a stat 68 below 100, the largest stat, a long list of breakpoints, clamped inputs.
CASES["breakpoints"] = [
    bcase(),
    bcase(stat=50),
    bcase(kind="cast", nfr=14),
    bcase(kind="cast", nfr=14, stat=20),
    bcase(kind="cast", nfr=14, stat=200),
    bcase(kind="gethit", nfr=5, evt=0),
    bcase(kind="gethit", nfr=5, stat=24, evt=0),
    bcase(kind="block", nfr=6, evt=0, stat=10),
    bcase(kind="blockhs", nfr=6, evt=3, stat=40),
    bcase(nfr=14, start=2, spd=200, term=70, stat=40, evt=2),
    bcase(nfr=14, term=160, evt=13),
    # the spec's illustrations of K3: a 14-frame cast at speed 256 with the cast rates 9, 37, 63 and 105, and a 5-frame
    # get-hit at the hit recovery rates 7, 15, 27, 48, 86 and 200
    *[bcase(kind="cast", nfr=14, stat=x) for x in (9, 37, 63, 105)],
    *[bcase(kind="gethit", nfr=5, stat=x, evt=0) for x in (7, 15, 27, 48, 86, 200)],
    bcase(nfr=40, start=1, evt=39, stat=15),
    bcase(nfr=3, start=2, spd=1, evt=2),
    bcase(nfr=1, start=0, spd=1, term=0, evt=0),
    # the factor's floor 15 with stat 68 at 0, and one-step actions (the rate covers the frames whole): no event fires
    bcase(term=0),
    bcase(nfr=1, evt=0),
    bcase(kind="cast", nfr=2, start=1, spd=512, evt=1),
    bcase(nfr=144, start=0, spd=1024, stat=2000, evt=100),
    bcase(nfr=100, spd=300),
    bcase(nfr=-4, start=999, spd=0, stat=-8, term=900, evt=-1, kind="nothing"),
]


def fixture(name, data):
    return {"cases": [{"inputs": c, "expect": TWINS[name](c, data)} for c in CASES[name]]}


def fallback_rng(fx):
    """The text fallback of the draw stepper: the fixture case of seed 12345, range 100 and five draws, in decimal."""
    case = next(c for c in fx["cases"] if c["inputs"] == {"seed": 12345, "n": 100, "draws": 5})["expect"]
    rows = [["0", "Init(seed)", "-", case["start"]["low"], case["start"]["high"]]]
    rows += [[r["k"], "Range(n)", r["result"], r["low"], r["high"]] for r in case["rows"]]
    note = ("The first draws of the illustrative seed 12345 with Range(100), computed by our model "
            "(decimal; the seed's two words are low and high).")
    return ["Draw", "Operation", "Result", "low after", "high after"], rows, note


def _find(fx, inputs):
    return next(c for c in fx["cases"] if c["inputs"] == inputs)["expect"]


def fallback_monstat(fx):
    e = _find(fx, {"monster": 0, "level": 7, "difficulty": 1})
    names = ["Minimum hit points", "Maximum hit points", "Defence", "Experience"]
    rows = [[n, e["rowVals"][i], e["cell"][i], e["result"][i]] for i, n in enumerate(names)]
    return ["Stat", "Level row value", "Monster cell", "Result"], rows, (
        "The invented scaled monster at monster level 7 on difficulty 1, computed by our model: MulDiv(row value, cell, 100).")


def fallback_merc(fx):
    e = _find(fx, {"level": 30})
    names = ["Level", "Experience for the next level", "Experience at this level", "Strength", "Dexterity",
             "Life (in 1/256)", "Defence", "Attack rating", "Minimum damage", "Maximum damage", "Resistances (each of four)",
             "Life regeneration"]
    return ["Stat", "Value"], [[n, e["result"][i]] for i, n in enumerate(names)], (
        f"An invented three-band hire table at level 30 (band {e['band']}, d = {e['dlt']}), computed by our model.")


def fallback_quality(fx):
    e = _find(fx, {"ilvl": 28, "qlvl": 10, "mf": 100, "record": 2, "kind": 0, "w0": 0, "w1": 0, "w2": 0, "w3": 0})
    out = {o["name"]: o["ppm"] for o in e["outcomes"]}
    rows = [[s["name"], s["chance"], f"{s['winPpm'] / 10000:.2f}", f"{out[s['name']] / 10000:.2f}"] for s in e["steps"]]
    return ["Test", "c", "Chance to win when reached (percent)", "Chance of this result (percent)"], rows, (
        "Item level 28, quality level 10, magic find 100, record 2, ratio words 0, computed by our model.")


def fallback_checksum(fx):
    e = _find(fx, {"typed": "01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12"})
    rows = [[s["i"], s["byte"], s["used"], s["rot"], s["sum"]] for s in e["steps"]]
    return ["Offset", "Byte typed", "Byte counted", "Sum rotated left by 1", "Sum after adding the byte"], rows, (
        "Toy bytes typed by hand, all numbers in decimal; the bytes at offsets 12 to 15 count as 0. Computed by our model.")


FALLBACKS = {"rng": fallback_rng, "monstat": fallback_monstat, "merc": fallback_merc, "quality": fallback_quality,
             "checksum": fallback_checksum}

def fallback_tohit(fx):
    """The text fallback of the to-hit widget: the first case, step by step, in decimal."""
    c = fx["cases"][0]["expect"]
    rows = [["Attack rating after the percent", c["ar3"]], ["Chance before the levels", str(c["c1"]) + "%"],
            ["Chance after the level factor", str(c["c2"]) + "%"], ["Chance after the clamp", str(c["chance"]) + "%"]]
    note = ("The first case of the illustrative inputs: attack rating %d, percent %d, defence %d, levels %d and %d "
            "(computed by our model)." % (c["ar"], c["pct"], c["def"], c["alvl"], c["dlvl"]))
    return ["Step", "Value"], rows, note


FALLBACKS["tohit"] = fallback_tohit



def fallback_table(name, fx):
    """(header, rows, one-line note) for `fallback: text`, or None when the widget has none."""
    return FALLBACKS[name](fx) if name in FALLBACKS else None


def widget_dirs():
    return sorted(d for d in os.listdir(HERE) if os.path.isfile(os.path.join(HERE, d, "widget.js")))


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode not in ("write", "check"):
        print(__doc__)
        return 2
    bad = 0
    for name in widget_dirs():
        data = json.load(open(os.path.join(HERE, name, "widget.json"), encoding="utf-8"))
        text = json.dumps(fixture(name, data), indent=1) + "\n"
        path = os.path.join(HERE, name, "fixture.json")
        if mode == "write":
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        elif not os.path.isfile(path) or open(path, encoding="utf-8").read() != text:
            print(f"{name}: fixture.json differs from its twin")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
