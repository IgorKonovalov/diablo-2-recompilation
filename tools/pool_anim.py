"""Animate the region seed and one level's monster pool, pick by pick (docs/specs/monsters/pool.md sections A to C): the
game seed's first draw, the region seed made from it, the levels built before the one shown, the level's candidate
classes, and each pick (the draw over the remaining candidates, the class taken, whether it is kept). Schematic only
(ADR-0036): boxes, text and bars in our own palette.

Usage:
  python3 -I tools/pool_anim.py <root> <seed> [--level ID] [--difficulty 0|1|2|normal|nightmare|hell]
        [--theme dark|light] [--out DIR] [--schematic]

<root> is the merged data tree (workspace/merged). <seed> is the game seed's start value: the animation starts the game
seed with Init(seed) (a game run with -seed N does), draws once from it, and builds the regions of levels 1 up to the
shown level on the region seed made from that draw. Defaults: level 3, difficulty 0 (normal). --theme: dark or light
palette values. --schematic is accepted for the export builder and changes nothing. DIR defaults to
workspace/render/anim/pool-<level>-d<difficulty>-<seed hex>-schematic/ and must stay under workspace/. Outputs:
frame-NNN.png, pool.gif, index.html, steps.json, schematic.json (ADR-0036).

Every number is the model's of tools/monpool.py: first_draw_low (the game seed's first draw), build_all on a seed that
counts its steps (the levels before the shown one), and the pick records of build_pool (the draws of the shown level).
The levels are built in id order on the one region seed, so the number of draws the earlier levels made, appearance sets
included, is part of what decides this level's pool; the appearance sets are counted, not shown (pool D). The
candidate list is the level's slots up to the first blank, as the model counts it. A level with `rangedspawn` set has
its first pick redrawn up to 20 times (pool C6); the frames show every redraw. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import excel_bin  # noqa: E402
import monpool  # noqa: E402
import rng  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 424
DIFF = {"normal": 0, "nightmare": 1, "hell": 2, "0": 0, "1": 1, "2": 2}
DIFF_NAME = ("normal", "nightmare", "hell")
HELP = """<li>Top: the seeds. The game seed is started with Init and drawn once; the region seed is made from that draw, and every level's pool is drawn on it, one level after another.</li>
<li>Candidates: the level's monster slots up to the first blank. Each pick draws over the candidates that remain, takes one, and removes its slot, so a slot is never taken twice.</li>
<li>A taken class is kept only if it may spawn; its rarity is copied to the pool and used later, when a room picks from it.</li>
<li>Every value is computed by our model for the illustrative seed, not observed in the game.</li>"""


class Counting(monpool.Seed):
    """The model's region seed with a count of its steps."""
    def __init__(self, low):
        super().__init__(low)
        self.n = 0

    def step(self):
        self.n += 1
        return super().step()


def hx(lo, hi):
    return "%08X:%08X" % (lo, hi)


def load_names(excel):
    h, rows = excel_bin.read_txt(excel_bin.find_file(excel, "monstats", ".txt"))
    mon = [r[0].strip() for r in rows]
    h2, lrows = excel_bin.read_txt(excel_bin.find_file(excel, "levels", ".txt"))
    ci = {c: i for i, c in enumerate(h2)}
    lvl = [r[ci["Name"]].strip() for r in lrows]
    return mon, lvl


def trace(t, seed, diff, lid):
    """The model's build on the region seed of Init(seed)'s first draw, up to level lid: -> dict with the game seed
    after its draw, the region seed, the draw counts and seeds after of levels 1 .. lid, and the shown level's picks."""
    g = monpool.first_draw_low(seed, 1)
    sd = Counting(g.low)
    traces = {}
    per = []
    last = 0
    reg3 = None
    for lid_, reg, s in monpool.build_all(t, g.low, diff, 1, seed=sd, traces=traces):
        per.append({"lid": lid_, "draws": sd.n - last, "seed": (sd.low, sd.high), "npool": reg["n"]})
        last = sd.n
        if lid_ == lid:
            reg3 = reg
            break
    pk = traces[lid]
    npick = sum(len(p["draws"]) for p in pk)
    for p in pk:                                   # the draw's low word: the seed after the last draw of the pick
        lo = int(p["seed"].split(":")[0], 16)
        assert lo % p["count"] == p["i"], (lo, p)
    return dict(game=(g.low, g.high), region=(g.low, rng.INIT_HIGH), per=per, picks=pk, reg=reg3, npick=npick,
                varsdraws=per[-1]["draws"] - npick, total=sd.n)


def build(root, seed, lid, diff, theme):
    excel = os.path.join(root, "data", "global", "excel")
    t = monpool.Tables(excel)
    mon, lvl = load_names(excel)
    tr = trace(t, seed, diff, lid)
    dn = DIFF_NAME[diff]
    off = 0x68 if diff else 0x36
    cand0 = t.slots(lid, off)
    numon = t.lvl_u8(lid, 0x32)
    ranged = t.lvl_u8(lid, 0x31) != 0
    bound = min(numon, 13, len(cand0))
    assert bound == len(tr["picks"]) or len(cand0) == 0, (bound, len(tr["picks"]))
    nm = lambda c: mon[c].upper()                           # noqa: E731
    lname = lvl[lid]
    k = K.Kit(W, H, theme)
    frames, caps = [], []

    def header(s):
        k.text(14, 12, s, "acc", 2, True)

    def seedrow(label, lo, hi, y=46):
        k.text(14, y, "%s %s" % (label, hx(lo, hi)), "dim", 2)

    def cands(remaining, cur=None, taken=None, y=216):
        """The candidate slots as boxes in a row (at most 13 shown per row, the model's pick bound)."""
        n = len(remaining)
        cw = min(200, 930 // max(n, 1))
        sc = 2 if all(K.text_w(nm(c), 2) <= cw - 14 for c in remaining) else 1
        for i, c in enumerate(remaining):
            hot = i == cur
            k.box(14 + i * cw, y, cw - 4, 56, [(nm(c), "txt"), ("SLOT %d" % i, "dim")], "cur" if hot else "panel",
                  "acc" if hot else "dim", "txt", sc, bold=hot)

    # ---- 1: the inputs
    header("REGION SEED AND POOL: %s, %s" % (lname.upper(), dn.upper()))
    k.text(14, 50, "GAME SEED = INIT(%d)" % seed, "txt", 2)
    seedrow("GAME SEED", seed, rng.INIT_HIGH, 82)
    k.text(14, 120, "EVERY LEVEL'S POOL IS DRAWN ON ONE REGION SEED, LEVEL 1 UP", "dim", 2)
    k.text(14, 146, "IN ID ORDER. THE POOL DEPENDS ON THE GAME SEED AND THE", "dim", 2)
    k.text(14, 172, "DIFFICULTY ONLY, NOT ON THE MAP SEED OR THE VISIT ORDER.", "dim", 2)
    k.text(14, 216, "SHOWN: LEVEL %d, %s" % (lid, lname.upper()), "txt", 3, True)
    k.caption("The pool of %s in %s for an illustrative game seed: the region seed first, then the levels built before "
              "it, then the level's picks one by one (pool A to C)." % (lname, dn), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The monster pool of %s in %s for an illustrative game seed." % (lname, dn),
        calc=["pool.md A: the game seed starts as Init(%d) = {%08x:%08x} (illustrative); the pool is a function of that seed and the difficulty only." % (
                  seed, seed, rng.INIT_HIGH),
              "pool.md B, C: level %d (%s), difficulty %s, candidates from the %s slots." % (
                  lid, lname, dn, "nmon" if diff else "mon")]))

    # ---- 2: the region seed
    g, r = tr["game"], tr["region"]
    header("THE REGION SEED")
    k.text(14, 50, "A2: THE GAME SEED STEPS ONCE", "txt", 2)
    seedrow("BEFORE", seed, rng.INIT_HIGH, 82)
    seedrow("AFTER ", g[0], g[1], 108)
    k.text(14, 150, "A3: R = INIT(LOW WORD OF THE DRAW)", "txt", 2)
    k.box(14, 182, 560, 64, [("REGION SEED R", "dim"), (hx(*r), "acc")], "cur", "acc", "txt", 2, bold=True)
    k.text(14, 270, "R IS A LOCAL OF THE BUILD: NOTHING ELSE DRAWS FROM IT,", "dim", 2)
    k.text(14, 296, "AND IT IS THROWN AWAY WHEN THE LAST LEVEL IS DONE.", "dim", 2)
    k.caption("The game seed steps once, to {%08x:%08x}; the region seed is Init of its low word, %d, which is "
              "{%08x:%08x} (pool A). It is used for the pools only." % (g[0], g[1], g[0], r[0], r[1]), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The game seed steps once and the region seed is made from its low word.",
        calc=["A2: Step(game.seed): {%08x:%08x} -> {%08x:%08x} (the first draw after the seeds are initialised)." % (
                  seed, rng.INIT_HIGH, g[0], g[1]),
              "A3: R = Init(game.seed.low) = {%08x:%08x}." % r,
              "A: R is a local of the region init; nothing else draws from it."]))

    # ---- 3: the levels before
    before = [p for p in tr["per"] if p["lid"] < lid]
    header("LEVELS BUILT BEFORE LEVEL %d" % lid)
    k.text(14, 50, "ID ORDER, ALL ON R; A LEVEL'S PICKS AND ITS APPEARANCE", "dim", 2)
    k.text(14, 76, "SETS ARE DONE BEFORE THE NEXT LEVEL'S FIRST DRAW", "dim", 2)
    y = 118
    shown = before[-3:]
    early = before[:-3]
    rows = ([("LEVELS 1 TO %d: %d DRAWS IN ALL" % (early[-1]["lid"], sum(p["draws"] for p in early)), None)] if early else []) + \
           [("LEVEL %d %s: %d DRAWS, POOL OF %d" % (p["lid"], lvl[p["lid"]].upper(), p["draws"], p["npool"]), p) for p in shown]
    for lab, p in rows:
        k.box(14, y, 920, 44, [(lab, "txt")], "panel", "dim", "txt", 2, align="l")
        if p is not None:
            k.text(560, y + 15, "R AFTER %s" % hx(*p["seed"]), "dim", 2)
        y += 52
    r0 = before[-1]["seed"] if before else r
    k.box(14, y + 10, 920, 56, [("R AT THE FIRST DRAW OF LEVEL %d" % lid, "dim"), (hx(*r0), "acc")], "cur", "acc", "txt", 2,
          bold=True)
    k.caption("Levels 1 to %d are built first on the region seed and take %d draws in all, the appearance sets included; "
              "those draws decide the seed this level's pool starts from (pool B3, D)." % (
                  lid - 1, sum(p["draws"] for p in before)), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="Levels 1 to %d are built first on the same region seed." % (lid - 1),
        calc=["B3: for id in 1 ..< levelCount: the pool of the level, then its appearance sets, all from R."] +
             ["level %d: %d draws, seed after {%08x:%08x}." % ((p["lid"], p["draws"]) + p["seed"]) for p in shown]))

    # ---- 4: the candidates
    npr = len(cand0)
    header("LEVEL %d: THE CANDIDATES" % lid)
    k.text(14, 46, "%s SLOTS, UP TO THE FIRST BLANK: COUNT = %d" % ("NMON" if diff else "MON", npr), "txt", 2)
    cands(cand0, y=84)
    k.text(14, 160, "NUMMON = %d, SO THE PICKS = MIN(%d, 13, %d) = %d" % (numon, numon, npr, bound), "txt", 2)
    k.text(14, 188, "RANGEDSPAWN = %d: %s" % (1 if ranged else 0, "THE FIRST PICK IS REDRAWN UNTIL RANGED, UP TO 20 TIMES"
                                              if ranged else "NO REDRAW FOR THE FIRST PICK"), "txt", 2)
    k.text(14, 216, "A CLASS KEPT ONLY IF ITS ISSPAWN IS SET; THE PICK COUNTS ANYWAY", "dim", 2)
    k.text(14, 244, "THE COUNT IS NOT IN THE FILE: THE MODEL COUNTS THE SLOTS", "dim", 2)
    seedrow("R", *r0, 300)
    k.caption("%s has %d candidates (the %s slots up to the first blank) and NumMon %d, so it makes min(%d, 13, %d) = %d "
              "picks; rangedspawn is %d (pool C1 to C3, C6)." % (
                  lname, npr, "nmon" if diff else "mon", numon, numon, npr, bound, 1 if ranged else 0), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="%s: %d candidates and %d picks." % (lname, npr, bound),
        calc=["C1: count = the number of leading filled %s slots = %d; candidates = %s." % (
                  "nmon" if diff else "mon", npr, ", ".join("%d %s" % (c, mon[c]) for c in cand0)),
              "C2: bound = min(NumMon, 13, count) = min(%d, 13, %d) = %d." % (numon, npr, bound),
              "C6: rangedspawn = %d." % (1 if ranged else 0)]))

    # ---- 5..: each pick
    remaining = list(cand0)
    held = []
    for pk in tr["picks"]:
        p = pk["p"]
        header("PICK %d OF %d" % (p + 1, bound))
        lo = int(pk["seed"].split(":")[0], 16)
        sh = [int(x, 16) for x in pk["seed"].split(":")]
        cands(remaining, cur=pk["i"], y=84)
        k.text(14, 160, "COUNT = %d REMAINING" % pk["count"], "txt", 2)
        multi = len(pk["draws"]) > 1
        if multi:
            k.text(14, 188, "RANGEDSPAWN: %d DRAWS OVER THE SAME %d, THE LAST IS TAKEN" % (len(pk["draws"]), pk["count"]), "txt", 2, True)
            k.text(14, 206, "SLOTS DRAWN: %s" % " ".join(str(d[0]) for d in pk["draws"][:24]), "dim", 1)
        else:
            k.text(14, 188, "DRAW = LOW WORD MOD COUNT = %d MOD %d = %d" % (lo, pk["count"], pk["i"]), "txt", 2, True)
        c = pk["c"]
        k.box(14, 226, 920, 80, [(("TAKEN: %s" % nm(c)), "good" if pk["kept"] else "bad"),
                                 ("RARITY %d, %s" % (t.ms[c][0x2E], "KEPT: ISSPAWN IS SET" if pk["kept"]
                                                     else "DROPPED: ISSPAWN IS 0, THE PICK STILL COUNTS"), "dim")],
              "cur", "good" if pk["kept"] else "bad", "txt", 2, bold=True)
        left = [x for j, x in enumerate(remaining) if j != pk["i"]]
        k.text(14, 326, "SLOT %d REMOVED: %d LEFT FOR THE NEXT PICK" % (pk["i"], len(left)), "dim", 2)
        k.text(14, 352, "R AFTER %s" % pk["seed"].upper(), "dim", 2)
        if multi:
            k.caption("Pick %d, rangedspawn set: redrawn until a ranged class, up to 20 redraws; %d draws over the same %d "
                      "candidates, the last, slot %d, %s, is taken, rarity %d, %s (pool C6, C8)." % (
                          p + 1, len(pk["draws"]), pk["count"], pk["i"], mon[c], t.ms[c][0x2E],
                          "kept" if pk["kept"] else "dropped, and the pick still counts"), CAP_Y, 76)
        else:
            k.caption("Pick %d: Range(R, %d) = %d takes slot %d, %s, rarity %d, %s (pool C5 to C8)." % (
                p + 1, pk["count"], pk["i"], pk["i"], mon[c], t.ms[c][0x2E],
                "kept" if pk["kept"] else "dropped, and the pick still counts"), CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="Pick %d takes %s from %d candidates." % (p + 1, mon[c], pk["count"]),
            calc=[("C5: i = Range(R, %d) = %d (the draw's low word %d mod %d)." % (pk["count"], pk["i"], lo, pk["count"])) if not multi
                  else ("C6: %d draws Range(R, %d), the slots %s; the last is taken (a ranged class, or the 20th redraw)." % (
                      len(pk["draws"]), pk["count"], ", ".join(str(d[0]) for d in pk["draws"]))),
                  "C5: c = cand[%d] = %d %s; C7: slot %d removed, count = %d." % (pk["i"], c, mon[c], pk["i"], len(left)),
                  "C8: isSpawn %s: %s; R after = {%08x:%08x}." % (
                      "set" if pk["kept"] else "clear",
                      "entry appended, rarity %d" % t.ms[c][0x2E] if pk["kept"] else "dropped, the pick still counts", *sh)]))
        remaining = left
        if pk["kept"]:
            held.append(c)

    # ---- the pool
    header("THE POOL OF LEVEL %d" % lid)
    reg = tr["reg"]
    ents = reg["ents"]
    for i, e in enumerate(ents):
        k.box(14 + i * 232, 60, 224, 70, [(nm(e[0]), "txt"), ("RARITY %d" % e[1], "dim")], "cur", "good", "txt", 2, bold=True)
    k.text(14, 150, "POOL OF %d CLASSES, RARITY SUM %d" % (len(ents), reg["rsum"]), "txt", 3, True)
    if remaining:
        k.text(14, 196, "LEFT OUT: %s%s" % (", ".join(nm(c) for c in remaining[:3]), ", ..." if len(remaining) > 3 else ""), "dim", 2)
    k.text(14, 226, "%d DRAWS FOR THE PICKS, %d FOR THE APPEARANCE SETS (NOT SHOWN)" % (tr["npick"], tr["varsdraws"]), "dim", 2)
    seedrow("R AFTER LEVEL %d" % lid, *tr["per"][-1]["seed"], 258)
    k.text(14, 284, "THE NEXT LEVEL'S FIRST DRAW CONTINUES FROM THIS SEED", "dim", 2)
    k.text(14, 310, "RARITY IS ONLY COPIED NOW; A ROOM USES IT WHEN IT PICKS", "dim", 2)
    k.caption("The pool of %s: %s; the rarities add to %d. Its %d picks took %d draws and its appearance sets %d more, "
              "after which the region seed is {%08x:%08x} (pool C8, D)." % (
                  lname, ", ".join(mon[e[0]] for e in ents), reg["rsum"], bound, tr["npick"], tr["varsdraws"],
                  *tr["per"][-1]["seed"]), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The pool of %s: %s." % (lname, ", ".join(mon[e[0]] for e in ents)),
        calc=["C8: entries %s; raritySum = %d (u8)." % (", ".join("%d %s (rarity %d)" % (e[0], mon[e[0]], e[1]) for e in ents),
                                                         reg["rsum"]),
              "level %d: %d draws in all, %d for the picks and %d for the appearance sets (pool D, not shown)." % (
                  lid, tr["per"][-1]["draws"], tr["npick"], tr["varsdraws"]),
              "seed after level %d = {%08x:%08x}; the next level's first draw continues from it." % ((lid,) + tr["per"][-1]["seed"])]))
    return frames, caps, k.pal, tr


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--level": "3", "--difficulty": "0", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 2 or opts["--difficulty"].lower() not in DIFF or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        seed, lid = int(argv[1], 0), int(opts["--level"], 0)
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not 0 < seed <= 0xFFFFFFFF or not 2 <= lid <= 136:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    diff = DIFF[opts["--difficulty"].lower()]
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim",
                                        "pool-%d-d%d-%x-schematic" % (lid, diff, seed))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _tr = build(argv[0], seed, lid, diff, opts["--theme"])
    K.write_illustration(out, "pool", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "monster pool animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
