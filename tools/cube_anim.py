"""Animate one Horadric Cube transmute (docs/specs/items/cube.md sections A, B, D, E, J, M): the cube's contents, the row
scan, the inputs of the matched row and the items they claim, the output's level, then every draw of the transmute in order,
and the cube after it. Schematic only (ADR-0036): boxes, text and cells in our own palette.

Usage:
  python3 -I tools/cube_anim.py <root> [--run NAME] [--n N] [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree (workspace/merged): the excel tables the cube model reads are in <root>/data/global/excel. The
transmute is a recorded one: --run NAME (default kinds2) names the run of workspace/logs/cube-NAME-*.log (exactly one file)
and --n N (default 4, 1 based) the transmute in it; the default is the Savage polearm of the spec's third worked example (row
19: a polearm of magic quality from a Kri, a gem, a staff and a belt, one scythe out of ten candidates). The run supplies only
the cube's contents, the player's facts and the game seed at the press; the match, the outputs and every draw are the model's
(tools/cube.py vector_data: the model's own check of that transmute, which must reproduce every logged value). --theme: dark or
light palette values. --schematic is accepted for the export builder and changes nothing. DIR defaults to
workspace/render/anim/cube-NAME-N-schematic/ and must stay under workspace/. Outputs: frame-NNN.png, cube.gif, index.html,
steps.json, schematic.json.

Steps: the cube; the row scan (which rows the header tests pass over and which reach the matcher); the matched row's inputs, each
with the items it claims; the output; one step per draw (the seed it is on, its range and its result); the cube after the
transmute. Seeds are shown by their low word in decimal. Not shown: the outputs' property lines beyond the draws, the placement
of the new item, the special outputs (the cow portal), the log's other transmutes. Stdlib only.
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import cube  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 424
QNAME = {1: "LOW", 2: "NORMAL", 3: "SUPERIOR", 4: "MAGIC", 5: "SET", 6: "RARE", 7: "UNIQUE", 8: "CRAFTED"}
WHY = {"numinputs": "BY THE ITEM COUNT", "disabled": "AS DISABLED", "version": "BY THE VERSION", "ladder": "BY THE LADDER FLAG",
       "min diff": "BY THE MINIMUM DIFFICULTY", "class": "BY THE CLASS"}
HELP = """<li>The cube holds the items on the left of the first frame. The scan tries the CubeMain rows from record 0 and the first row whose header tests and inputs all fit is the recipe.</li>
<li>Each input claims every cube item that fits it, not only its quantity; the count of claimed items must equal the quantity.</li>
<li>The draws are listed in the order the game makes them: first the game seed, then the new item's unit seed and item seed.</li>
<li>Every value is computed by our model from a recorded transmute's inputs, not observed in the game.</li>"""


def find_log(run):
    f = sorted(glob.glob(os.path.join(HERE, "..", "workspace", "logs", "cube-%s-*.log" % run)))
    if len(f) != 1:
        raise SystemExit("run %r: %d logs match workspace/logs/cube-%s-*.log, need exactly one" % (run, len(f), run))
    return f[0]


def code(T, cls):
    return T.code(cls).rstrip(b"\0 ").decode().upper()


def type_code(T, t):
    return T.P.itypes[t][:4].split(b"\0")[0].decode("latin1").upper()


def facts(D):
    """The model's data for the frames: the scan, the matched row's inputs with their claims, the output and the draws."""
    T, c = D["T"], D["c"]
    reached, row, slots = cube.match(T, c)
    assert row == D["res"]["row"] and [i for i, _ in reached] == D["res"]["reached"]
    reasons = {}                                       # rows passed over by the header tests, by the first test that failed
    n = len(c["items"])
    skipped = {}
    for i in range(row + 1):
        ok, why = cube.row_filter(T, T.rows[i], c, n)
        if not ok:
            reasons[why] = reasons.get(why, 0) + 1
            skipped[i] = why
    r = T.rows[row]
    ins = []
    claimed = [False] * 48
    sl = [[0, 0, 0] for _ in range(3)]
    for k in range(7):
        inp = r["ins"][k]
        if not inp["flags"] & 3:
            continue
        claims = []
        assert cube.match_input(T, r, k, c["items"], claimed, sl, c, claims)
        if inp["flags"] & 1:
            ask = code(T, inp["index"]) if inp["index"] != 0xFFFF else "ANY BASE"
            if inp["flags"] & 0x80:
                ask += " OR HIGHER"
        else:
            ask = "TYPE " + type_code(T, inp["index"])
        ins.append(dict(k=k, ask=ask, qty=inp["qty"] if inp["qty"] > 0 else 1, q=inp["q"], claims=claims))
    assert sl == slots
    o = r["outs"][0]
    return dict(reached=[i for i, _ in reached], row=row, skipped=skipped, reasons=reasons, ins=ins, o=o,
                ilvl=cube.out_ilvl(T, c, o, slots[0]), n=n)


def draw_label(T, seed, what, ngame):
    """Our own short label of a traced draw; ngame counts the game-seed draws of each kind before this one."""
    if what.startswith("RNG_RangeB (CubePickItemOfType)"):
        return "START IN THE ITEM LIST" if ngame["pick"] == 0 else "ONE OF THE CANDIDATES"
    if what.startswith("game-seed step"):
        return "UNIT SEED (CREATION STEP)" if ngame["step"] % 2 == 0 else "ITEM SEED (SEED-INIT STEP)"
    if what.startswith("ItemInitStats"):
        return "BASE STATS (UNIT SEED)"
    if what.startswith("PickMagicAffix") and "roll test" in what:
        return "AFFIX PICK: ROLL TEST"
    if what.startswith("property roll"):
        return "PROPERTY ROLL (PROP %s)" % what.split("prop ")[1].split(" ")[0]
    return what.upper()[:34]


def build(D, theme):
    T, c = D["T"], D["c"]
    F = facts(D)
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    items = c["items"]
    row = F["row"]
    codes = [code(T, it["cls"]) for it in items]

    def put(cap, text, calc):
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(text=text, calc=calc))

    def cube_row(y, marks=None, fills=None):
        cw = min(150, 900 // max(len(items), 1))
        for i, it in enumerate(items):
            fl = (fills or {}).get(i, "panel")
            k.box(20 + i * cw, y, cw - 10, 78, [(codes[i], "txt"), (QNAME.get(it["q"], "Q%d" % it["q"]), "dim"), ("ILVL %d" % it["ilvl"], "dim")],
                  fl, (marks or {}).get(i, "dim"), sc=2)
        return cw

    # ---- the cube
    k.text(20, 12, "THE CUBE: %d ITEMS" % len(items), "acc", 2, True)
    cube_row(60)
    k.text(20, 160, "THE TRANSMUTE SCANS THE CUBEMAIN ROWS FROM RECORD 0.", "dim", 2)
    k.text(20, 188, "THE FIRST ROW WHOSE HEADER TESTS AND INPUTS ALL FIT IS THE RECIPE.", "dim", 2)
    put("The cube holds %d items: %s. Pressing Transmute runs a scan over the CubeMain table in row order (cube A)." % (
        len(items), ", ".join(codes)),
        "The cube holds %d items." % len(items),
        ["cube A1: n = the number of cube items = %d; a stack counts 1." % len(items),
         "cube list order: %s." % ", ".join("%s (%s, ilvl %d)" % (codes[i], QNAME.get(it["q"], "q%d" % it["q"]).lower(), it["ilvl"])
                                          for i, it in enumerate(items))])
    # ---- the scan
    k.text(20, 12, "THE ROW SCAN: ROWS 0 TO %d" % row, "acc", 2, True)
    cols, cw_, ch_ = 20, 44, 26
    cells = {}
    for i in range(row + 1):
        if i == row:
            cells[(i % cols, i // cols)] = (str(i), "qd_set")
        elif i in F["reached"]:
            cells[(i % cols, i // cols)] = (str(i), "bad" if False else "qd_rare")
        else:
            cells[(i % cols, i // cols)] = (str(i), "panel")
    nrows = row // cols + 1
    k.cellgrid(20, 50, min(cols, row + 1), nrows, cw_, ch_, cells, sc=1)
    k.legend(20, 50 + nrows * ch_ + 14, [("panel", "PASSED OVER BY THE HEADER TESTS"), ("qd_rare", "REACHED THE MATCHER, NO FIT"),
                                          ("qd_set", "THE RECIPE")], sc=1)
    lines = ["%d OF %d ROWS PASSED OVER: %s" % (len(F["skipped"]), row + 1, ", ".join("%d %s" % (v, WHY.get(kx, kx.upper())) for kx, v in sorted(F["reasons"].items()))),
             "%d ROWS REACHED THE MATCHER AND FAILED AN INPUT%s" % (len(F["reached"]) - 1, (": " + ", ".join(str(i) for i in F["reached"][:-1])) if len(F["reached"]) <= 7 else ""),
             "ROW %d FITS: THE SCAN STOPS, ROWS AFTER IT ARE NEVER TESTED" % row]
    for j, s in enumerate(lines):
        k.text(20, 100 + nrows * ch_ + j * 28, s, "txt" if j == 2 else "dim", 2)
    put("The scan stops at the first row whose header tests and inputs pass: %d rows are passed over by the header tests, %d "
        "reach the matcher and fail an input, and row %d fits (cube A3)." % (len(F["skipped"]), len(F["reached"]) - 1, row),
        "The scan passes over %d rows, %d fail an input, and row %d is the recipe." % (len(F["skipped"]), len(F["reached"]) - 1, row),
        ["cube A3: for each row, the header tests (enabled, version, ladder, min diff, class, numinputs = n), then the seven inputs; "
         "first fit wins.",
         "passed over by the header tests: %d (%s). Reached the matcher: %s. Matched: %d." % (
             len(F["skipped"]), ", ".join("%d %s" % (v, WHY.get(kx, kx).lower()) for kx, v in sorted(F["reasons"].items())),
             ", ".join(str(i) for i in F["reached"]), row)])
    # ---- the inputs
    k.text(20, 12, "ROW %d: THE INPUTS" % row, "acc", 2, True)
    cw = cube_row(50, {i: "good" for inp in F["ins"] for i in [x - 1 for x in inp["claims"]]})
    k.text(20, 140, "EACH INPUT CLAIMS EVERY CUBE ITEM THAT FITS IT:", "dim", 2)
    for j, inp in enumerate(F["ins"]):
        y = 172 + j * 54
        k.box(20, y, 330, 46, [("INPUT %d: %s" % (inp["k"] + 1, inp["ask"]), "txt"),
                               ("COUNT %d, QTY %d" % (len(inp["claims"]), inp["qty"]), "dim")], "panel", "dim", sc=2, align="l")
        k.text(370, y + 15, "CLAIMS", "dim", 2)
        bw = min(110, 470 // max(len(inp["claims"]), 1) - 10)
        for m, o_ in enumerate(inp["claims"]):
            k.box(470 + m * (bw + 10), y, bw, 44, [(codes[o_ - 1], "good")], "qd_set", "good", sc=2)
    put("Row %d lists %d inputs; each claims every cube item that fits it, in column order, and its count must equal its quantity "
        "(cube B). The cube's %d items are claimed one to each input here." % (row, len(F["ins"]), len(items)),
        "Row %d: every input claims its items." % row,
        ["cube B3: for each cube item in list order: the item test, then unclaimed; claim it; got = got + 1.",
         "; ".join("input %d %s claims item(s) %s (count %d, qty %d)" % (
             i["k"] + 1, i["ask"].lower(), ",".join(codes[x - 1] for x in i["claims"]), len(i["claims"]), i["qty"]) for i in F["ins"])])
    # ---- the output
    o = F["o"]
    kind = cube.KIND.get(o["kind"], str(o["kind"]))
    k.text(20, 12, "ROW %d: OUTPUT A" % row, "acc", 2, True)
    rows_ = [("KIND: %s" % kind.upper(), "txt")]
    if o["kind"] in (0xFC, 0xFF, 0xFE):
        pass
    if o["kind"] in (0xFC, 0xFD):
        rows_.append(("ITEM %s: %s" % ("CODE" if o["kind"] == 0xFC else "TYPE",
                                       code(T, o["index"]) if o["kind"] == 0xFC else type_code(T, o["index"])), "txt"))
    rows_.append(("QUALITY: %s" % QNAME.get(o["q"], str(o["q"])), "txt"))
    forced = [p for p in o["pre"] if p] + [p for p in o["suf"] if p]
    if forced:
        rows_.append(("FORCED AFFIX ROW(S): %s" % ", ".join(str(p) for p in forced), "txt"))
    rows_.append(("LVL %d  PLVL %d  ILVL %d" % (o["lvl"], o["plvl"], o["ilvl"]), "dim"))
    rows_.append(("OUTPUT LEVEL V = %d%s" % (F["ilvl"], " (A FIXED LVL WINS)" if o["lvl"] else ""), "good"))
    for j, (s, col) in enumerate(rows_):
        k.text(20, 70 + j * 32, s, col, 2)
    put("Output A of row %d is %s with quality %s%s; its level v is %d%s (cube D, E)." % (
        row, ("an item of type " + type_code(T, o["index"]).lower()) if o["kind"] == 0xFD else "a " + kind,
        QNAME.get(o["q"], "?").lower(), (" and the forced affix row %s" % ", ".join(str(p) for p in forced)) if forced else "",
        F["ilvl"], ", the row's fixed lvl, which wins" if o["lvl"] else ""),
        "Output A of row %d, with its level v = %d." % (row, F["ilvl"]),
        ["cube D: a fixed lvl wins; otherwise v = player level x plvl / 100 + input 1's ilvl x ilvl / 100, truncated, at least 1.",
         "row %d output A: kind %s, quality %d, lvl %d, plvl %d, ilvl %d -> v = %d." % (
             row, kind if o["kind"] != 0xFD else "item type", o["q"], o["lvl"], o["plvl"], o["ilvl"], F["ilvl"])])
    # ---- the draws
    draws = [e for e in D["seq"] if e[0] == "draw"]
    shown = []
    ngame = {"pick": 0, "step": 0}
    low_seed = {"game": 0, "unit": 0, "item": 0}
    for e in draws:
        _, n, seed, bf, af, what, rg, r_ = e
        lab = draw_label(T, seed, what, ngame)
        if what.startswith("RNG_RangeB (CubePickItemOfType)"):
            ngame["pick"] += 1
        if what.startswith("game-seed step"):
            ngame["step"] += 1
        if r_.startswith("low "):                        # a step's result is its new low word (decimal, never hex)
            r_, rg = "LOW WORD %d" % af[0], "NO RANGE"
        shown.append((n, seed, lab, rg, r_, af))
    for i, (n, seed, lab, rg, r_, af) in enumerate(shown):
        k.text(20, 12, "DRAW %d OF %d: %s SEED" % (n, len(shown), seed.upper()), "acc", 2, True)
        hdr = ("#", "SEED", "DRAW", "RANGE", "RESULT")
        xs = (20, 60, 150, 560, 700)
        for x, t in zip(xs, hdr):
            k.text(x, 50, t, "dim", 2)
        k.hline(20, 940, 70, "grey", 1)
        first = max(0, i - 9)
        for j, (n2, s2, l2, rg2, r2, af2) in enumerate(shown[first:i + 1]):
            y = 80 + j * 30
            cur = first + j == i
            if cur:
                k.rect(14, y - 5, 932, 28, "cur")
            for x, t in zip(xs, (str(n2), s2.upper(), l2, rg2.upper().replace(" ", " "), r2.upper())):
                k.text(x, y, t, "txt" if cur else "dim", 2)
        put("%s" % draw_text(T, seed, lab, rg, r_, n, af),
            "Draw %d, on the %s seed: %s, %s, result %s." % (n, seed, lab.lower(), rg.lower(), r_.lower()),
            draw_calc(seed, lab, rg, r_, af))
    # ---- after
    k.text(20, 12, "THE CUBE AFTER THE TRANSMUTE", "acc", 2, True)
    cw = cube_row(60, {i: "bad" for i in range(len(items))})
    k.text(20, 150, "EVERY EARLIER CUBE ITEM IS DESTROYED WHEN SOMETHING WAS PRODUCED;", "dim", 2)
    k.text(20, 176, "THE OUTPUT TAKES THEIR PLACE, IDENTIFIED:", "dim", 2)
    for j, it in enumerate(D["final"]):
        pn = [T.A.magic[a - 1]["name"] for a in it["p"] if a]
        sn = [T.A.magic[a - 1]["name"] for a in it["s"] if a]
        lines = [(code(T, it["cls"]), "txt"), ("%s ILVL %d" % (QNAME.get(it["q"], "Q%d" % it["q"]), it["ilvl"]), "dim")]
        if pn or sn:
            lines.append((" ".join(x.upper() for x in pn + sn), "good"))
        k.box(20 + j * 240, 212, 230, 90, lines, "qd_magic" if it["q"] == 4 else "panel", "edge", sc=2)
    put("When the row produced an item the cube's earlier items are destroyed and the output is placed, identified (cube G). "
        "The first output here is %s." % ", ".join("%s of %s quality" % (code(T, it["cls"]).lower(), QNAME.get(it["q"], "?").lower())
                                                 for it in D["final"]),
        "The cube now holds the output.",
        ["cube G: the items are destroyed only when something was produced; each output is placed identified.",
         "output: %s." % ", ".join("%s q%d ilvl %d" % (code(T, it["cls"]), it["q"], it["ilvl"]) for it in D["final"])])
    return frames, caps, k.pal


def draw_text(T, seed, lab, rg, r_, n, af):
    if lab == "START IN THE ITEM LIST":
        return ("Draw %d, on the game seed: the pick of a base of the output's type starts at a random place in the item list, "
                "a draw with %s values, result %s (cube J)." % (n, rg.replace("n ", ""), r_))
    if lab == "ONE OF THE CANDIDATES":
        return ("Draw %d, on the game seed: one of the candidate bases, a draw with %s values, result %s (cube J)." % (
            n, rg.replace("n ", ""), r_))
    if lab.startswith("UNIT SEED"):
        return "Draw %d, on the game seed: the step that makes the new item's unit (cube M)." % n
    if lab.startswith("ITEM SEED"):
        return "Draw %d, on the game seed: the step that starts the new item's own seed (cube M)." % n
    if lab.startswith("BASE STATS"):
        return "Draw %d, on the unit seed: the new item's base stats, range %s, result %s (cube M, properties A)." % (n, rg, r_)
    if lab.startswith("AFFIX PICK"):
        return "Draw %d, on the item seed: the roll test of an affix pick, the low bit of the draw, %s (cube M, affixes C)." % (n, r_)
    if lab.startswith("PROPERTY ROLL"):
        return "Draw %d, on the item seed: a property of the item rolled in its range %s, %s (cube M)." % (n, rg, r_)
    return "Draw %d, on the %s seed: %s, %s, %s." % (n, seed, lab.lower(), rg, r_)


def draw_calc(seed, lab, rg, r_, af):
    return ["the %s seed after the step: low word %d, high word %d." % (seed, af[0], af[1]),
            "%s: %s -> %s." % (lab.lower(), rg.lower(), r_.lower())]


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--run": "kinds2", "--n": "4", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            if i + 1 >= len(argv):
                print(__doc__.strip(), file=sys.stderr)
                return 2
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1 or opts["--theme"] not in K.THEMES or not opts["--n"].isdigit() or int(opts["--n"]) < 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    excel = os.path.join(argv[0], "data", "global", "excel")
    if not os.path.isdir(excel):
        print("no excel tables under %s" % excel, file=sys.stderr)
        return 2
    n = int(opts["--n"])
    D = cube.vector_data(excel, find_log(opts["--run"]), n)
    if D is None or D["res"].get("row") is None or not D["res"].get("produced") or not D["final"]:
        print("transmute %d of run %s matched no row or produced no item" % (n, opts["--run"]), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "cube-%s-%d-schematic" % (opts["--run"], n))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal = build(D, opts["--theme"])
    K.write_illustration(out, "cube", frames, caps, W, H, K.palette(opts["--theme"])[1], "cube transmute animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
