"""Animate one magic-affix pick (docs/specs/items/affixes.md sections B and C): the affix level, draw 1, the filter that
leaves the candidates, their weights, draw 2 and the walk that picks one. Schematic only (ADR-0036): boxes, text and a
weight strip in our own palette.

Usage:
  python3 -I tools/affix_anim.py <root> <item code> <ilvl> <seed> [--side prefix|suffix] [--theme dark|light] [--out DIR]
        [--schematic]

<root> is the merged data tree (workspace/merged); the tables read are weapons, armor, misc, itemtypes, magicprefix,
magicsuffix and properties. <item code> is a base item code of those tables (for example lsd). <ilvl>: the item level.
<seed>: an illustrative input, the item's seed is {seed, 666} (not a seed the game derives). --side: the pick shown
(default prefix; the item is a magic item of an expansion game with no affix yet, so the pick has no must-roll and no
forced row). --theme: the palette's dark or light values (default dark). --schematic is accepted for the export builder
and changes nothing. DIR defaults to workspace/render/anim/affix-<item>-<ilvl>-<seed hex>-<side>-schematic/ and must stay
under workspace/. Outputs:
  frame-NNN.png  one frame per step; affix.gif the frames as an animated GIF; index.html the step-through page;
  steps.json the captions and calculations; schematic.json the marker's file list (ADR-0036).

Data shown (ADR-0009 risk 3: the affix tables are game data): the filter frame shows counts only; the weights frame shows
at most five candidates, each as its affix id and weight, and the weight strip as bars with no text; the one affix name
shown is the winner's, on the last frame. Steps: the inputs, the affix level, draw 1, the filter, the weights, draw 2 and
the walk, the result; a pick that does not roll or finds no candidate ends early. Every number is computed by the pick of
tools/affixes.py (Walk.pick, run with no log lines and a trace dict) and the affix level by its alvl_of; the affix level's
arithmetic shown is recomputed from the base's two columns and asserted equal to the model's. Stdlib only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import affixes  # noqa: E402
import anim_common  # noqa: E402
import rng  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 436
MAX_LISTED = 5          # candidates a frame lists (id and weight); the strip carries the rest as bars with no text
STEPS = ("ALVL", "DRAW 1", "FILTER", "WEIGHTS", "DRAW 2")
TESTS = (("spawnable", "C4A", "SPAWNABLE FLAG IS 0"),
         ("version", "C4B", "ROW NEEDS VERSION 100 AND ITEM IS BELOW IT"),
         ("level", "C4C", "ROW LEVEL ABOVE ALVL OR MAXLEVEL BELOW IT"),
         ("rare", "C4D", "RARE FLAG 0 ON A RARE ITEM"),
         ("type", "C4E", "ITEM TYPE TEST FAILS"),
         ("frequency", "C4G", "FREQUENCY IS 0"),
         ("class", "C4H", "CLASS-SPECIFIC ROW OF ANOTHER CLASS"),
         ("taken", "C4I", "GROUP ALREADY ON THE ITEM"))
HELP = """<li>The top row names the steps of one pick: the affix level (alvl), draw 1, the filter, the weights and draw 2.</li>
<li>Draw 1: the low bit of the first step of the item seed decides whether the pick rolls at all.</li>
<li>Filter: counts only, one line per test in the game's order, with the rows each test refused and the rows left. No row of the table is listed.</li>
<li>Weights and draw 2: the strip is one bar per candidate, as wide as its weight; draw 2 picks a point along it, and the candidate under the point wins. At most five candidates are listed, by affix id and weight.</li>
<li>Every value is computed by our model of the pick for the illustrative inputs given, not observed in the game.</li>"""


def code_index(T):
    codes = {}
    for i in range(len(T.items)):
        codes.setdefault(T.b(i)["code"], i)
    return codes


def model_pick(T, cls, ilvl, seed, pre):
    """The model's pick (affixes.Walk.pick, no log lines) with its trace: a magic item (quality 4) of an expansion game
    (item version 101) with no affixes, no must-roll, no forced row and no properties applied."""
    it = affixes.Item(T, dict(cls=cls, ilvl=ilvl, ver=101))
    it.q = 4
    wk = affixes.Walk(T, [], it, collections.Counter(), collections.defaultdict(list), "anim", free=True)
    wk.seed = (seed, rng.INIT_HIGH)
    tr = {}
    aid, rec = wk.pick("magic", 1, 0, 0, 1 if pre else 0, trace=tr)
    tr.update(aid=aid, rec=rec, seed_end=wk.seed, it=it, alvl_model=affixes.alvl_of(it))
    return tr


def alvl_parts(base, ilvl):
    """The arithmetic of B1-B4 from the base's level and magic lvl, for the frame; the model's alvl_of is the value."""
    q, m = base["qlvl"], base["mlvl"]
    i = ilvl if ilvl > q else q
    if m:
        raw, how = i + m, "M"
        h = None
    else:
        h = q // 2
        raw, how = (i - h, "H") if i < 99 - h else (2 * i - 99, "D")
    return dict(q=q, m=m, i=i, h=h, raw=raw, how=how, a=max(1, min(99, raw)))


def build(T, codes, code, ilvl, seed, pre, theme):
    cls = codes[code]
    tr = model_pick(T, cls, ilvl, seed, pre)
    base = T.b(cls)
    side = "PREFIX" if pre else "SUFFIX"
    side_l = side.lower()
    par = alvl_parts(base, ilvl)
    alvl = par["a"]
    assert alvl == tr["alvl_model"], (alvl, tr["alvl_model"])
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    ended = None

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def stepper(cur):
        for i, n in enumerate(STEPS):
            k.box(20 + i * 186, 40, 176, 30, [n], "cur" if i == cur else "panel", "acc" if i == cur else "dim",
                  "txt" if i <= cur else "dim", 2, bold=(i == cur))

    # ---- inputs
    header("AFFIX PICK: ITEM %s, ITEM LEVEL %d, %s" % (code.upper(), ilvl, side))
    stepper(-1)
    lines = [("BASE ITEM", code.upper()), ("ITEM LEVEL", str(ilvl)), ("BASE LEVEL (QLVL)", str(par["q"])),
             ("MAGIC LVL OF THE BASE", str(par["m"])), ("QUALITY", "MAGIC, NO AFFIX YET"),
             ("GAME", "EXPANSION, ITEM VERSION 100 OR MORE"), ("ITEM SEED", "%08X : %08X" % (seed, rng.INIT_HIGH))]
    y = 90
    for lab, val in lines:
        k.text(40, y, lab, "dim", 2)
        k.text(380, y, val, "txt", 2, True)
        y += 34
    k.text(40, y + 10, "A %s PICK: NO MUST-ROLL, NO FORCED ROW, PROPERTIES NOT SHOWN" % side, "dim", 2)
    k.caption("One %s pick on a magic %s of item level %d: draw 1, the filter over the %s table, the weights, then draw 2 "
              "(affixes C)." % (side_l, code, ilvl, side_l), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="One %s pick for a magic item, base %s, item level %d, on the item seed {%d:%d} (illustrative)." % (
            side_l, code, ilvl, seed, rng.INIT_HIGH),
        calc=["affixes.md C: PickMagicAffix(item, needSpawnable = 1, mustRoll = 0, applyProps = 0, isPrefix = %d, "
              "forcedId = 0, autoGroup = 0)." % (1 if pre else 0),
              "base %s: qlvl = %d, magic lvl = %d; item version 101 (expansion), quality 4, no affix on the item." % (
                  code, par["q"], par["m"])]))

    # ---- alvl
    header("THE AFFIX LEVEL (ALVL)")
    stepper(0)
    k.text(40, 96, "I = MAX(ILVL, QLVL) = MAX(%d, %d) = %d" % (ilvl, par["q"], par["i"]), "txt", 2, True)
    if par["m"]:
        k.text(40, 140, "MAGIC LVL M = %d IS NOT 0: ALVL = I + M = %d + %d = %d" % (par["m"], par["i"], par["m"], par["raw"]),
               "txt", 2, True)
        k.text(40, 174, "(NO SUBTRACTION OF QLVL / 2 FOR SUCH A BASE)", "dim", 2)
    else:
        h = par["h"]
        k.text(40, 140, "MAGIC LVL IS 0: H = QLVL / 2 = %d / 2 = %d (ROUNDED DOWN)" % (par["q"], h), "txt", 2, True)
        if par["how"] == "H":
            k.text(40, 174, "I = %d IS BELOW 99 - H = %d: ALVL = I - H = %d" % (par["i"], 99 - h, par["raw"]), "txt", 2, True)
        else:
            k.text(40, 174, "I = %d IS NOT BELOW 99 - H = %d: ALVL = 2 * I - 99 = %d" % (par["i"], 99 - h, par["raw"]),
                   "txt", 2, True)
    k.text(40, 218, "CLAMPED TO 1..99", "dim", 2)
    k.box(40, 250, 400, 90, [("ALVL", "dim"), (str(alvl), "acc")], "cur", "acc", "txt", 3, bold=True)
    k.text(470, 280, "THE LEVEL WINDOW OF THE FILTER", "dim", 2)
    k.text(470, 306, "USES ALVL, NOT THE ITEM LEVEL", "dim", 2)
    k.caption("The affix level is the greater of item level and base level, less half the base level (or plus its magic "
              "lvl), kept to 1..99: here %d (affixes B)." % alvl, CAP_Y, 76)
    frames.append(k.done())
    if par["m"]:
        calc_b = "B2: magic lvl %d is not 0, so alvl = i + m = %d + %d = %d." % (par["m"], par["i"], par["m"], par["raw"])
    elif par["how"] == "H":
        calc_b = "B3: magic lvl 0, h = qlvl / 2 = %d; i = %d < 99 - h = %d, so alvl = i - h = %d." % (
            par["h"], par["i"], 99 - par["h"], par["raw"])
    else:
        calc_b = "B3: magic lvl 0, h = qlvl / 2 = %d; i = %d is not below 99 - h = %d, so alvl = 2 * i - 99 = %d." % (
            par["h"], par["i"], 99 - par["h"], par["raw"])
    caps.append(dict(
        text="The affix level of base %s at item level %d is %d." % (code, ilvl, alvl),
        calc=["B1: i = max(ilvl, qlvl) = max(%d, %d) = %d." % (ilvl, par["q"], par["i"]), calc_b,
              "B4: clamped to 1..99, alvl = %d." % alvl]))

    # ---- draw 1
    lo1 = tr["lo1"]
    rolled = bool(lo1 & 1)
    header("DRAW 1: STEP THE ITEM SEED")
    stepper(1)
    k.box(40, 96, 420, 100, [("LOW WORD", "dim"), ("%08X" % lo1, "acc")], "panel", "dim", "txt", 3, bold=True)
    k.text(490, 106, "BIT 0 = %d" % (lo1 & 1), "txt", 3, True)
    if rolled:
        k.text(490, 150, "BIT 0 IS 1: THE PICK ROLLS", "good", 2, True)
    else:
        k.text(490, 150, "BIT 0 IS 0 AND NO MUST-ROLL: NO AFFIX", "bad", 2, True)
    k.text(40, 230, "DRAW 1 IS MADE ON EVERY PICK, BEFORE THE FILTER", "dim", 2)
    k.text(40, 262, "A PICK COSTS 1 STEP (NO ROLL OR NO CANDIDATE) OR 2", "dim", 2)
    k.caption("Draw 1 is one step of the item seed; its low bit is %d, so the pick %s (affixes C2)." % (
        lo1 & 1, "rolls" if rolled else "ends here with no affix"), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="Draw 1: the low word is %d, bit 0 is %d, so the pick %s." % (lo1, lo1 & 1, "rolls" if rolled else "ends with no affix"),
        calc=["C2: Step(item.seed); low = %d; seed = {%d:%d}." % (lo1, tr["seed1"][0], tr["seed1"][1]),
              "C2: (low & 1) = %d%s." % (lo1 & 1, "" if rolled else " and mustRoll is 0: return 0, no affix")]))
    cands, Wt = tr.get("cands", []), tr.get("W", 0)
    if not rolled:
        ended = "noroll"
    else:
        # ---- filter
        refused = tr["refused"]
        rows = tr["rows"]
        header("THE FILTER: COUNTS ONLY")
        stepper(2)
        k.text(40, 84, "ROWS IN THE %s TABLE: %d" % (side, rows), "txt", 2, True)
        refmap = dict(refused)
        left = rows
        y = 114
        for key, tag, lab in TESTS:
            n = refmap[key]
            left -= n
            k.rect(40, y, 880, 30, "panel")
            k.outline(40, y, 880, 30, "dim")
            k.text(50, y + 8, tag, "dim", 2)
            k.text(120, y + 8, lab, "txt" if n else "dim", 2, bool(n))
            k.text(660, y + 8, "REFUSED %d" % n, "txt" if n else "dim", 2, bool(n))
            k.text(800, y + 8, "LEFT %d" % left, "acc" if n else "dim", 2, True)
            y += 34
        assert left == len(cands)
        k.text(40, y + 10, "CANDIDATES: %d    TOTAL WEIGHT W: %d" % (len(cands), Wt), "txt", 3, True)
        k.caption("Each row of the %s table meets the tests in order; a row refused by one is out. %d of %d rows are left "
                  "as candidates (affixes C4)." % (side_l, len(cands), rows), CAP_Y, 76)
        frames.append(k.done())
        left = rows
        calc = ["C4: the %s block has %d rows; alvl = %d." % (side_l, rows, alvl)]
        for (key, tag, lab) in TESTS:
            left -= refmap[key]
            calc.append("%s: %s: %d refused, %d left." % (tag, lab.lower(), refmap[key], left))
        calc.append("C4: n = %d candidates, W = %d (the weight is the row's frequency; frequency * level on a base with a "
                    "magic lvl)." % (len(cands), Wt))
        caps.append(dict(text="The filter leaves %d of %d rows as candidates, with total weight %d." % (len(cands), rows, Wt),
                         calc=calc))
        if not cands:
            ended = "nocand"
        else:
            # ---- weights
            header("THE CANDIDATES AND THEIR WEIGHTS")
            stepper(3)
            rule = "WEIGHT = FREQUENCY * LEVEL (MAGIC LVL BASE)" if par["m"] else "WEIGHT = FREQUENCY OF THE ROW"
            k.text(40, 84, "%d CANDIDATES, W = %d.  %s" % (len(cands), Wt, rule), "txt", 2, True)
            shown = cands[:MAX_LISTED]
            k.text(40, 118, "THE FIRST %d IN TABLE ORDER (AFFIX ID, WEIGHT)" % len(shown) if len(cands) > len(shown)
                   else "THE %d CANDIDATES (AFFIX ID, WEIGHT)" % len(shown), "dim", 2)
            for j, (aid, w) in enumerate(shown):
                k.rect(40, 146 + j * 36, 420, 30, "panel")
                k.outline(40, 146 + j * 36, 420, 30, "dim")
                k.text(52, 154 + j * 36, "ID %d" % aid, "txt", 2, True)
                k.text(300, 154 + j * 36, "WEIGHT %d" % w, "txt", 2)
            strip(k, 40, 360, 880, cands, Wt, None, None)
            k.text(40, 392, "THE STRIP: ONE BAR PER CANDIDATE, AS WIDE AS ITS WEIGHT", "dim", 2)
            k.caption("%d candidates with total weight %d; the strip gives each as wide as its weight, in table order "
                      "(affixes C4)." % (len(cands), Wt), CAP_Y, 76)
            frames.append(k.done())
            caps.append(dict(
                text="%d candidates, total weight %d." % (len(cands), Wt),
                calc=["C4: the weight is %s." % ("frequency * level, the base has a magic lvl" if par["m"] else "the row's frequency"),
                      "the first %d candidates (merged affix id: weight): %s." % (
                          len(shown), ", ".join("%d: %d" % (a, w) for a, w in shown)),
                      "C4: n = %d, W = %d, the sum of the %d weights." % (len(cands), Wt, len(cands))]))
            # ---- draw 2
            x, kk, aid = tr["x"], tr["k"], tr["aid"]
            before = sum(w for _a, w in cands[:kk])
            wk_ = cands[kk][1]
            header("DRAW 2: RANGE(W + 1), THEN THE WALK")
            stepper(4)
            k.box(40, 84, 380, 90, [("DRAW X = RANGE(%d)" % (Wt + 1), "dim"), (str(x), "acc")], "panel", "dim", "txt", 3,
                  bold=True)
            if x == Wt:
                k.text(430, 96, "X = W: THE LAST CANDIDATE WINS", "txt", 2, True)
            else:
                k.text(430, 96, "SUBTRACT EACH WEIGHT FROM X:", "txt", 2, True)
            k.text(430, 126, "THE FIRST TO GO BELOW 0 WINS", "dim", 2)
            k.text(430, 152, "CANDIDATE %d OF %d: %d TO %d" % (kk + 1, len(cands), before, before + wk_ - 1), "txt", 2, True)
            strip(k, 40, 250, 880, cands, Wt, x, kk)
            k.text(40, 296, "0", "dim", 2)
            k.text(40 + 880 - K.text_w(str(Wt), 2), 296, str(Wt), "dim", 2)
            k.box(40, 330, 880, 56, [("AFFIX ID %d, WEIGHT %d" % (aid, wk_), "good")], "cur", "good", "txt", 3, bold=True)
            k.caption("Draw 2 is %d of 0..%d; the walk stops at candidate %d of %d, whose weights span %d to %d "
                      "(affixes C7)." % (x, Wt, kk + 1, len(cands), before, before + wk_ - 1), CAP_Y, 76)
            frames.append(k.done())
            caps.append(dict(
                text="Draw 2 is %d; the walk stops at candidate %d of %d, affix id %d." % (x, kk + 1, len(cands), aid),
                calc=["C7: x = Range(item.seed, W + 1) = Range(%d) = %d; seed = {%d:%d}." % (
                    Wt + 1, x, tr["seed2"][0], tr["seed2"][1]),
                      "C7: the running subtraction first goes below 0 at candidate %d (weights before it: %d, its own: %d)%s." % (
                          kk + 1, before, wk_, "; x = W takes the last candidate" if x == Wt else ""),
                      "C7: the id returned is %d." % aid]))
    # ---- the result
    if ended is None:
        aid = tr["aid"]
        name = T.magic[aid - 1]["name"].upper()
        header("THE PICK: %s" % side)
        k.box(40, 90, 880, 80, [(name, "good")], "cur", "good", "txt", 4, bold=True)
        k.text(40, 184, "AFFIX ID %d" % aid, "txt", 2, True)
        k.text(40, 230, "2 STEPS OF THE ITEM SEED", "txt", 2, True)
        k.text(40, 262, "THE PROPERTIES OF THE AFFIX ARE APPLIED AFTER THE PICK (NOT SHOWN)", "dim", 2)
        k.caption("The pick returns affix id %d after two steps of the item seed; its properties are applied next "
                  "(affixes C8)." % aid, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="The pick returns affix id %d after two draws on the item seed." % aid,
            calc=["C8: return id + 1 = %d; item seed after = {%d:%d}." % (aid, tr["seed_end"][0], tr["seed_end"][1])]))
    else:
        header("THE PICK: NO AFFIX")
        why = ("DRAW 1 HAD BIT 0 AT 0" if ended == "noroll" else "NO ROW PASSED THE FILTER")
        k.box(40, 90, 880, 80, [("NO AFFIX", "bad")], "panel", "bad", "txt", 4, bold=True)
        k.text(40, 184, why, "dim", 2)
        k.text(40, 230, "1 STEP OF THE ITEM SEED", "txt", 2, True)
        k.caption("The pick returns 0, no affix, after one step of the item seed (affixes C2, C7).", CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="The pick returns 0, no affix, after one draw on the item seed.",
            calc=["%s: return 0; item seed after = {%d:%d}." % ("C2" if ended == "noroll" else "C7",
                                                                    tr["seed_end"][0], tr["seed_end"][1])]))
    return frames, caps, k.pal, tr


def strip(k, x, y, bw, cands, Wt, xdraw, win):
    """The weight strip: one bar per candidate in table order, as wide as its weight; the winner's in the highlight."""
    k.rect(x, y, bw, 22, "grey")
    cum = 0
    for j, (_a, w) in enumerate(cands):
        a, b = x + cum * bw // Wt, x + (cum + w) * bw // Wt
        cum += w
        fill = "cur" if j == win else ("panel" if j % 2 == 0 else "grey")
        k.rect(a, y, max(1, b - a), 22, fill)
        k.vline(a, y, y + 21, "dim", 1)
    k.outline(x, y, bw, 22, "dim")
    if win is not None:
        cum = sum(w for _a, w in cands[:win])
        a, b = x + cum * bw // Wt, x + (cum + cands[win][1]) * bw // Wt
        k.outline(a, y - 2, max(2, b - a), 26, "good", 2)
    if xdraw is not None:
        mx = x + min(bw - 2, xdraw * bw // Wt)
        k.rect(mx - 1, y - 12, 3, 46, "txt")


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--side": "prefix", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 4:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        code, ilvl, seed = argv[1], int(argv[2]), int(argv[3], 0)
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (0 <= ilvl <= 255 and 0 < seed <= 0xFFFFFFFF and opts["--theme"] in K.THEMES
            and opts["--side"] in ("prefix", "suffix")):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    T = affixes.Tables(os.path.join(argv[0], "data", "global", "excel"))
    codes = code_index(T)
    if code not in codes:
        print("no item code %r in weapons, armor, misc" % code, file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim",
                                        "affix-%s-%d-%x-%s-schematic" % (code, ilvl, seed, opts["--side"]))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _tr = build(T, codes, code, ilvl, seed, opts["--side"] == "prefix", opts["--theme"])
    K.write_illustration(out, "affix", frames, caps, W, H, K.palette(opts["--theme"])[1], "affix pick animation", HELP,
                         targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
