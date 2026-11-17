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


TWINS = {"rng": twin_rng}

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
]}


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


FALLBACKS = {"rng": fallback_rng}


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
