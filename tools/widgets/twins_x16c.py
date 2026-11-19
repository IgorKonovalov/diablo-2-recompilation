"""Python twins of the `seedtree` and `path` widgets (ADR-0037), registered by twins.py.

`seedtree`: the tree of tools/seedtree_anim.py's `trace`, which runs the DRLG model's Act and Seed classes of
tools/drlg.py (the seed tree of docs/specs/rng/seeds.md steps 1 to 5); the twin only reshapes its output into what
the widget's `compute` returns. `path`: tools/path_anim.py's `search`, the iterative-deepening walk of
docs/specs/path/search.md section L on the toy room; the twin only turns its records into strings (the cell store as
nine rows of text, points as `x,y`) and applies the widget's input rules (clamping, walls kept inside the room and
off the start and the target).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import path_anim  # noqa: E402
import seedtree_anim  # noqa: E402

M32 = 0xFFFFFFFF
SEED_LIMITS = {"seed": (1, 2147483647), "act": (0, 4), "level": (0, 255), "rooms": (1, 8)}
PATH_LIMITS = {"sx": (0, 15), "sy": (0, 8), "tx": (0, 15), "ty": (0, 8), "b1c": (0, 255)}


def clamp(v, lo, hi):
    return min(hi, max(lo, int(v)))


def twin_seedtree(inputs, data):
    seed = clamp(inputs["seed"], *SEED_LIMITS["seed"])
    act = clamp(inputs["act"], *SEED_LIMITS["act"])
    level = clamp(inputs["level"], *SEED_LIMITS["level"])
    rooms = clamp(inputs["rooms"], *SEED_LIMITS["rooms"])
    assert data["rule"]["initHigh"] == 666 and len(data["acts"]["items"]) == 5
    T = seedtree_anim.trace(seed, act, [level], rooms)
    acts = []
    for a in T["acts"]:
        tombs = list(a["tombs"]) if a["tombs"] != (0, 0) else None
        acts.append({"idx": a["idx"], "lead": a["base"], "draws": a["steps"], "tombs": tombs, "bit": a["bit"]})
    return {
        "seed": seed, "act": act, "level": level, "rooms": rooms,
        "game": {"low": T["game"][0], "high": T["game"][1]},
        "acts": acts,
        "levelSeed": {"lead": T["acts"][act]["base"], "id": level, "sum": T["levels"][0]["sum"], "high": 666},
        "roomRows": [{"k": r["n"], "levelLow": r["level"][0], "levelHigh": r["level"][1],
                      "roomLow": r["room"][0], "roomHigh": r["room"][1]} for r in T["rooms"]],
    }


def pt(p):
    return "%d,%d" % p


def wall_num(text):
    """A wall coordinate as the widget reads it: optional sign and ASCII digits only ("3.0", "1e0", "1_0" are not)."""
    t = text.strip()
    body = t[1:] if t[:1] in ("+", "-") else t
    if not body or any(c not in "0123456789" for c in body):
        raise ValueError(text)
    return int(t)


def parse_walls(items):
    out = set()
    for s in items:
        parts = str(s).split(",")
        try:
            if len(parts) != 2:
                raise ValueError(s)
            x, y = wall_num(parts[0]), wall_num(parts[1])
        except ValueError:
            continue
        if 0 <= x < path_anim.GW and 0 <= y < path_anim.GH:
            out.add((x, y))
    return out


def twin_path(inputs, data):
    assert (data["grid"]["wide"], data["grid"]["high"]) == (path_anim.GW, path_anim.GH)
    v = {k: clamp(inputs[k], *PATH_LIMITS[k]) for k in PATH_LIMITS}
    start, target = (v["sx"], v["sy"]), (v["tx"], v["ty"])
    walls = parse_walls(inputs["walls"]) - {start, target}
    R = path_anim.search(start, target, v["b1c"], walls)
    passes = []
    for p in R["passes"]:
        rows = []
        for y in range(path_anim.GH):
            cells = []
            for x in range(path_anim.GW):
                c = p["store"].get((x, y), 0)
                cells.append("." if c == 0 else "#" if c == 1 else str(c))
            rows.append(" ".join(cells))
        passes.append({
            "limit": p["bound"], "tries": p["tries"], "nodes": p["nodes"], "ending": p["end"],
            "descent": " ".join(pt(q) for q in p["first_descent"] or []),
            "chain": " ".join(pt(q) for q in p["chain"] or []),
            "grid": rows,
        })
    return {
        "start": pt(start), "target": pt(target), "b1c": v["b1c"], "walls": sorted(pt(w) for w in walls),
        "h0": R["h0"], "last": R["last"], "reached": R["found"], "passes": passes,
        "route": " ".join(pt(q) for q in R["points"]),
    }


TWINS = {"seedtree": twin_seedtree, "path": twin_path}

# seedtree: the illustrative seed 0xC0FFEE with each act and several levels; the ends of the seed range; seeds under
# which Act II's pair draw rejects at least once; clamped inputs.
# path: the toy room's wall with a gap (the spec's example), an open room, a sealed target, start next to target,
# bound at or below h0 (one pass), a wide bound, a diagonal line, walls typed over the start, clamped inputs.
_WALL = ["7,%d" % y for y in range(1, 9)]
CASES = {
    "seedtree": [
        {"seed": 12648430, "act": 0, "level": 1, "rooms": 3},
        {"seed": 12648430, "act": 1, "level": 66, "rooms": 3},
        {"seed": 12648430, "act": 2, "level": 80, "rooms": 2},
        {"seed": 12648430, "act": 3, "level": 255, "rooms": 8},
        {"seed": 12648430, "act": 4, "level": 0, "rooms": 1},
        {"seed": 12345, "act": 0, "level": 1, "rooms": 5},
        {"seed": 1, "act": 1, "level": 67, "rooms": 4},
        {"seed": 2147483647, "act": 2, "level": 255, "rooms": 8},
        {"seed": 4294967295, "act": 9, "level": -4, "rooms": 99},
        {"seed": 0, "act": -1, "level": 3, "rooms": 0},
    ],
    "path": [
        {"walls": _WALL, "sx": 2, "sy": 4, "tx": 13, "ty": 4, "b1c": 33},
        {"walls": _WALL, "sx": 2, "sy": 4, "tx": 13, "ty": 4, "b1c": 0},
        {"walls": _WALL, "sx": 2, "sy": 4, "tx": 13, "ty": 4, "b1c": 255},
        {"walls": [], "sx": 2, "sy": 4, "tx": 13, "ty": 4, "b1c": 33},
        {"walls": [], "sx": 1, "sy": 1, "tx": 8, "ty": 5, "b1c": 40},
        {"walls": [], "sx": 0, "sy": 0, "tx": 15, "ty": 8, "b1c": 80},
        {"walls": ["12,3", "12,4", "12,5", "13,3", "13,5", "14,3", "14,4", "14,5"], "sx": 2, "sy": 4, "tx": 13, "ty": 4, "b1c": 60},
        {"walls": ["3,4", "2,3", "2,5"], "sx": 2, "sy": 4, "tx": 4, "ty": 4, "b1c": 20},
        {"walls": _WALL, "sx": 5, "sy": 5, "tx": 5, "ty": 6, "b1c": 33},
        {"walls": _WALL + ["2,4", "13,4", "99,99", "x,y", "-1,3"], "sx": 2, "sy": 4, "tx": 13, "ty": 4, "b1c": 33},
        {"walls": [], "sx": 99, "sy": -3, "tx": 2, "ty": 100, "b1c": 9999},
        {"walls": ["7.0,4", "7,3.0", "1e0,4", "0x7,2", "1_0,4", "7,4,1", " 7 , 5 ", "+7,6", "-0,0"],
         "sx": 2, "sy": 4, "tx": 13, "ty": 4, "b1c": 33},
        {"walls": ["1,1", "2,2", "3,3", "4,4", "5,5", "6,6", "9,2", "9,3", "9,4", "9,5", "10,5", "11,5"],
         "sx": 0, "sy": 8, "tx": 15, "ty": 0, "b1c": 120},
    ],
}
