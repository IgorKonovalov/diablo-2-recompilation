"""Animate the drop quality roll (docs/specs/items/quality.md): the ladder of tests, unique first, each test's chance
step by step (base term, magic find's diminished factor, the row's minimum, the ratio word), its draw, and the
outcome. Schematic only (ADR-0036): boxes, text and bars in our own palette.

Usage:
  python3 -I tools/quality_anim.py <root> <item code> <ilvl> <seed> [--mf N] [--ratio a,b,c,d] [--theme dark|light]
        [--out DIR] [--schematic]

<root> is the merged data tree (workspace/merged); the tables read are weapons, armor, misc, itemtypes and itemratio.
<item code> is a base item code of those tables (for example lsd). <ilvl>: the item level. <seed>: an illustrative
input, the source unit's seed is {seed, 666} (not a seed the game derives). --mf: the killer's magic find (default 0).
--ratio: the TC frame's first four ratio words in the order magic, rare, set, unique (default 0,0,0,0). --theme: the
palette's dark or light values (default dark). --schematic is accepted for the export builder and changes nothing.
DIR defaults to workspace/render/anim/quality-<item>-<ilvl>-<seed hex>-schematic/ and must stay under workspace/. Outputs:
  frame-NNN.png  one frame per step; quality.gif the frames as an animated GIF; index.html the step-through page;
  steps.json the captions and calculations; schematic.json the marker's file list (ADR-0036).

Steps: the inputs (the item, ilvl, the itemratio row and d); one step per test the roll reaches (unique, set, rare,
magic, superior, normal), each with its chance chain and its draw; a last step with the outcome. Every number is
computed by the model of tools/quality.py (roll, with its trace and its per-test record of the chance before the
minimum; diminish for the factor): the base term and the factor shown are recomputed from the itemratio row with
the model's helpers and asserted equal to the model's chance. Not shown: the early returns' tables beyond a note, the
classic-version row choice and the item creation after the quality. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import quality  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 436
LADDER = ("unique", "set", "rare", "magic", "superior", "normal")
QCODE = {"unique": 7, "set": 5, "rare": 6, "magic": 4, "superior": 3, "normal": 2}
QCOL = {"unique": "q_unique", "set": "q_set", "rare": "q_rare", "magic": "q_magic", "superior": "q_superior",
        "normal": "q_normal", "low": "q_low"}
QFILL = {k: "qd_" + k for k in QCOL}
# per test: (row column of base, divisor, min, factor k, ratio word index); D table of quality.md
COLS = {"unique": (0, 1, 2, 250, 3), "set": (6, 7, 8, 500, 2), "rare": (3, 4, 5, 600, 1), "magic": (9, 10, 11, 0, 0),
        "superior": (12, 13, None, 0, None), "normal": (14, 15, None, 0, None)}
SECT = {"unique": "D", "set": "D", "rare": "D", "magic": "D", "superior": "E1-E2", "normal": "E3-E4"}
HELP = """<li>Left: the tests in the order the game runs them. The current test is outlined; a won test ends the roll, a lost one passes to the next.</li>
<li>Right: the chance c of the current test, in four steps (base term, magic find, the row's minimum, the ratio word), then the draw. A draw below 128 wins; a c below 1 wins with no draw.</li>
<li>The superior and normal tests use only the base term. A test with no draw changes nothing on the seed.</li>
<li>Every value is computed by our model of the roll for the illustrative inputs given, not observed in the game.</li>"""


def code_index(T):
    codes = {}
    for i, r in enumerate(T.items):
        codes.setdefault(bytes(r[0x80:0x84]).decode("latin-1").strip(), i)
    return codes


def trace(T, item, ilvl, ratio, seed, mf):
    """The model's roll with its trace, and one record per test: the base term, the factor, the chance after magic
    find, the minimum, the ratio word, the chance, the draw, the win and the seed after, recomputed from the row with the
    model's helpers and asserted equal to the model's values."""
    tr, pre = [], []
    code, seed_out, why, ndraw, ri = quality.roll(T, item, ilvl, ratio, seed, mf, trace=tr, cf={"pre": pre})
    info = dict(code=code, seed_out=seed_out, why=why, ndraw=ndraw, ri=ri, tests=[], mf=mf)
    if ri is None:
        return info
    v = T.ratio[ri]["v"]
    d = quality.s32(ilvl - T.items[item][0xFD])
    info["d"] = d
    m100 = mf + 100
    use_mf = mf != 0 and mf > -100
    pi = {p[0]: p for p in pre}
    cur = seed
    for name, c, x, won in tr:
        b, dv, mn, k, w = COLS[name]
        base = quality.s32((v[b] - quality.cdiv(d, quality.s32(v[dv]))) << 7)
        t = dict(name=name, base=base, bterm=v[b], div=quality.s32(v[dv]), d=d, c=c, x=x, won=won, factor=None,
                 c_mf=base, minimum=None, word=None, c_min=base)
        if mn is not None:
            t["minimum"] = quality.s32(v[mn])
            t["word"] = ratio[w]
            c1 = base
            if use_mf:
                f = m100 if name == "magic" else quality.diminish(m100, k)
                t["factor"] = f
                if f != 0:
                    c1 = quality.cdiv(quality.s32(base * 100), f)
            assert pi[name][1] == c1 and pi[name][2] == t["minimum"] and pi[name][3] == t["word"], (name, pi[name], c1)
            t["c_mf"] = c1
            t["c_min"] = max(c1, t["minimum"]) if c1 <= t["minimum"] else c1
        else:
            assert c == base, (name, c, base)
        if x is not None:
            xv, cur = quality.range_b(cur, c)
            assert xv == x
        t["seed_after"] = cur
        info["tests"].append(t)
    assert cur == seed_out
    return info


def build(T, codes, code, ilvl, ratio, seed, mf, theme):
    item = codes[code]
    info = trace(T, item, ilvl, ratio, (seed, 666), mf)
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    tests = info["tests"]
    names = [t["name"] for t in tests]
    final = info["code"]
    fname = {7: "unique", 5: "set", 6: "rare", 4: "magic", 3: "superior", 2: "normal", 1: "low", 0: "none"}[final]
    d = info.get("d")

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def ladder(cur):
        """cur: the test being shown (None: the outcome). A test before or at cur shows its result, a later one nothing;
        on the outcome frame a test the roll never reached shows NOT RUN."""
        y = 44
        for name in LADDER + ("low",):
            state = ""
            if name in names:
                if cur is None or names.index(name) <= names.index(cur):
                    state = "WIN" if tests[names.index(name)]["won"] else "LOSE"
            elif cur is None:
                state = "WIN" if (name == "low" and final == 1) else "NOT RUN"
            is_cur = cur == name
            won_name = cur is None and name == fname
            fill = QFILL[name] if (won_name or is_cur) else "panel"
            edge = "acc" if is_cur else ("txt" if won_name else "dim")
            k.rect(20, y, 280, 44, fill)
            k.outline(20, y, 280, 44, edge, 2 if is_cur else 1)
            k.text(34, y + 15, name.upper(), QCOL[name], 2, True)
            if state:
                k.text(300 - 14 - K.text_w(state, 2), y + 15, state, "good" if state == "WIN" else "dim", 2, True)
            y += 48

    # ---- inputs
    header("QUALITY ROLL: ITEM %s, ILVL %d, MAGIC FIND %d" % (code.upper(), ilvl, mf))
    k.text(20, 44, "TESTS IN ORDER, FIRST WIN ENDS IT", "dim", 2)
    y = 74
    for name in LADDER:
        k.box(20, y, 150, 36, [name.upper()], QFILL[name], "dim", QCOL[name], 2, bold=True)
        y += 42
    k.box(20, y, 150, 36, ["LOW"], QFILL["low"], "dim", QCOL["low"], 2, bold=True)
    for i, name in enumerate(LADDER):
        k.text(190, 74 + i * 42 + 10, {"unique": "ALWAYS", "set": "ALWAYS", "rare": "IF THE TYPE ALLOWS RARE",
                                       "magic": "A TEST; AN ALWAYS-MAGIC TYPE IS MAGIC AT ONCE",
                                       "superior": "NO MAGIC FIND, MINIMUM OR RATIO", "normal": "LOSING IT GIVES LOW"}[name],
               "dim", 2)
    k.text(190, 74 + 6 * 42 + 10, "ONLY BY LOSING THE NORMAL TEST", "dim", 2)
    if info["ri"] is not None:
        k.text(580, 44, "ITEMRATIO ROW %d" % info["ri"], "txt", 2, True)
        k.text(580, 70, "D = ILVL - QLVL = %d - %d = %d" % (ilvl, ilvl - d, d), "txt", 2)
        k.text(580, 96, "RATIO WORDS %s" % ",".join(str(w) for w in ratio[:4]), "dim", 2)
        k.text(580, 122, "SOURCE SEED {%d, 666}" % seed, "dim", 2)
    k.caption("Item %s at item level %d, magic find %d. The tests run in order; each has a chance c and a draw from 0 "
              "to c - 1 that wins below 128 (quality D, E)." % (code, ilvl, mf), CAP_Y, 76)
    frames.append(k.done())
    row_txt = ("itemratio row %d (version argument 100); d = ilvl - rec.level = %d - %d = %d."
               % (info["ri"], ilvl, ilvl - d, d)) if info["ri"] is not None else "no itemratio row is read."
    caps.append(dict(
        text="The quality roll for item %s, item level %d, magic find %d: the tests run in order and the first win ends "
             "the roll." % (code, ilvl, mf),
        calc=["quality.md Inputs: item %s, ilvl %d, magic find %d, ratio words (magic, rare, set, unique) %s, source seed "
              "{%08x, 666} (illustrative)." % (code, ilvl, mf, ",".join(str(w) for w in ratio[:4]), seed),
              "quality.md B: " + row_txt,
              "quality.md Test order: unique, set, rare (if the type allows), magic (or magic with no test for an "
              "always-magic type), superior, normal; losing the normal test is low."]))

    # ---- one frame per test
    for t in tests:
        name = t["name"]
        cur = name
        header("QUALITY ROLL: %s TEST" % name.upper())
        ladder(cur)
        X0 = 330
        c = t["c"]
        rows = []
        b = "(%d - %d / %d) X 128 = %d" % (t["bterm"], t["d"], t["div"], t["base"])
        rows.append(("BASE", b, "txt"))
        if t["minimum"] is not None:
            if t["factor"] is not None:
                rows.append(("MAGIC FIND", "X 100 / F, F = %d: %d" % (t["factor"], t["c_mf"]), "txt"))
            elif mf == 0:
                rows.append(("MAGIC FIND", "NONE (MAGIC FIND 0): %d" % t["c_mf"], "dim"))
            else:
                rows.append(("MAGIC FIND", "NOT USED: %d" % t["c_mf"], "dim"))
            if t["c_mf"] <= t["minimum"]:
                rows.append(("MINIMUM", "%d <= %d: RAISED TO %d" % (t["c_mf"], t["minimum"], t["minimum"]), "acc"))
            else:
                rows.append(("MINIMUM", "%d ABOVE %d: KEPT" % (t["c_mf"], t["minimum"]), "txt"))
            rows.append(("RATIO WORD", "W = %d: C - W X C / 1024 = %d" % (t["word"], c), "txt"))
        else:
            rows.append(("MAGIC FIND", "NOT USED IN THIS TEST", "dim"))
            rows.append(("MINIMUM", "NOT USED IN THIS TEST", "dim"))
            rows.append(("RATIO WORD", "NOT USED IN THIS TEST", "dim"))
        y = 44
        for lab, s, col in rows:
            k.rect(X0, y, 610, 40, "panel")
            k.outline(X0, y, 610, 40, "dim")
            k.text(X0 + 10, y + 13, lab, "dim", 2)
            k.text(X0 + 170, y + 13, s, col, 2, col != "dim")
            y += 46
        # the chance and the draw
        k.rect(X0, y + 4, 610, 150, "cur")
        k.outline(X0, y + 4, 610, 150, "acc", 2)
        k.text(X0 + 12, y + 14, "CHANCE C = %d" % c, "txt", 3, True)
        if t["x"] is None:
            k.text(X0 + 12, y + 56, "C BELOW 1: WIN, NO DRAW", "good", 3, True)
        else:
            k.text(X0 + 12, y + 56, "DRAW X = %d" % t["x"], "txt", 3, True)
            k.text(X0 + 12, y + 92, "WINS BELOW 128: %s" % ("WIN" if t["won"] else "LOSE"),
                   "good" if t["won"] else "bad", 2, True)
            bw = 580
            k.bar(X0 + 12, y + 118, bw, 18, min(128, c), max(c, 1), "good", "grey")
            mx = X0 + 12 + min(bw - 2, t["x"] * bw // max(c, 1))
            k.rect(mx - 1, y + 112, 3, 30, "txt")
            k.text(X0 + 12 + bw - K.text_w("0 TO %d" % (c - 1), 1), y + 98, "0 TO %d" % (c - 1), "dim", 1)
        tail = "A WIN ENDS THE ROLL: %s." % name.upper() if t["won"] else "LOST: THE NEXT TEST RUNS."
        k.text(X0, 392, tail, "good" if t["won"] else "dim", 2, True)
        if t["x"] is None:
            cap = ("The %s test: c = %d is below 1, so it wins with no draw (quality %s)." % (name, c, SECT[name]))
        else:
            cap = ("The %s test: c = %d, draw %d, %s (a draw below 128 wins)." % (
                name, c, t["x"], "a win" if t["won"] else "a loss, so the next test runs"))
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        calc = ["quality.md %s: base term = (%d - %d / %d) << 7 = %d." % (
            "D4" if name in ("unique", "set", "rare", "magic") else ("E1" if name == "superior" else "E3"),
            t["bterm"], t["d"], t["div"], t["base"])]
        if t["minimum"] is not None:
            if t["factor"] is not None:
                calc.append("D5: magic find on: c = c x 100 / F with F = %s = %d, so c = %d." % (
                    "m100 = %d (no diminishing)" % (mf + 100) if name == "magic" else
                    "Diminish(%d, %d)" % (mf + 100, COLS[name][3]), t["factor"], t["c_mf"]))
            else:
                calc.append("D5: no magic find applied, c = %d." % t["c_mf"])
            calc.append("D6: c <= the row's minimum %d is raised to it: c = %d." % (t["minimum"], t["c_min"]))
            calc.append("D7: ratio word %d: c = c - w x c / 1024 = %d." % (t["word"], c))
        if t["x"] is None:
            calc.append("%s: c = %d < 1, so the test is won with no draw; the seed is unchanged." % (
                "D8" if t["minimum"] is not None else "E", c))
        else:
            calc.append("%s: draw RangeB(c = %d): the seed steps once, x = new low mod %d = %d; seed = {%08x:%08x}." % (
                "D9" if t["minimum"] is not None else "E", c, c, t["x"], t["seed_after"][0], t["seed_after"][1]))
            calc.append("x = %d %s 128: %s." % (t["x"], "<" if t["won"] else ">=", "won" if t["won"] else "lost"))
        caps.append(dict(
            text="The %s test: chance c = %d, %s." % (name, c, "won with no draw" if t["x"] is None else
                                                    "draw %d, %s" % (t["x"], "won" if t["won"] else "lost")),
            calc=calc))

    # ---- the outcome
    header("THE ROLL ENDS: %s" % fname.upper())
    ladder(None)
    k.box(330, 60, 610, 120, [(fname.upper(), QCOL[fname])], QFILL.get(fname, "panel"), "txt", QCOL.get(fname, "txt"), 4,
          bold=True)
    k.text(330, 200, "%d DRAWS, QUALITY CODE %d" % (info["ndraw"], final), "txt", 2, True)
    k.text(330, 228, "THE SEED KEEPS THE DRAWS FOR THE NEXT ROLL", "dim", 2)
    k.caption("The roll ends with %s after %d draws. Every test that was reached has run in order; the seed carries "
              "the draws on to the next roll." % (fname, info["ndraw"]), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The roll ends with %s (quality code %d) after %d draws on the source seed." % (fname, final, info["ndraw"]),
        calc=["result code = %d (%s); draws = %d; tests reached = %s." % (final, fname, info["ndraw"],
                                                                         ", ".join(names) if names else "none"),
              "source seed after the roll = {%08x:%08x}." % info["seed_out"]]))
    return frames, caps, k.pal, info


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--mf": "0", "--ratio": "0,0,0,0", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 4:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        code, ilvl, seed, mf = argv[1], int(argv[2]), int(argv[3], 0), int(opts["--mf"])
        ratio = [int(x) for x in opts["--ratio"].split(",")]
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (len(ratio) == 4 and all(0 <= w <= 1024 for w in ratio) and 0 <= ilvl <= 255 and 0 < seed <= 0xFFFFFFFF
            and -1000 <= mf <= 10000 and opts["--theme"] in K.THEMES):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    excel = os.path.join(argv[0], "data", "global", "excel")
    T = quality.Tables(excel)
    codes = code_index(T)
    if code not in codes:
        print("no item code %r in weapons, armor, misc" % code, file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim",
                                        "quality-%s-%d-%x-schematic" % (code, ilvl, seed))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _info = build(T, codes, code, ilvl, ratio, seed, mf, opts["--theme"])
    K.write_illustration(out, "quality", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "quality roll animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
