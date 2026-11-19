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
