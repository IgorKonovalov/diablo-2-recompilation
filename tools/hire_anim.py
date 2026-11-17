"""Animate one seller's hire list (docs/specs/hirelings/README.md sections B, D and E): the store seed's draws, one seed
per name of the seller's range, the ten picks that list names, and each listed entry rolled from its own seed into a
hireling id, a level and a price. Schematic only (ADR-0036): boxes, a cell grid and text in our own palette.

Usage:
  python3 -I tools/hire_anim.py <root> <seller> <player level> <seed> [--difficulty normal|nightmare|hell] [--classic]
        [--theme dark|light] [--out DIR] [--schematic]

<root> is the merged data tree (workspace/merged); the tables read are hireling (the seller's name range and the rows
of the act and difficulty) and their string-index columns. <seller> is kashya, greiz, asheara or qualkehk (Qual-Kehk has
rows in an expansion game only). <player level>: the level the list is rolled for. <seed>: an illustrative input, the
store seed is {seed, 666} (a real game's is the vendors' shared seed; this one is not derived). --difficulty: the
game's difficulty (default normal; the name range is the Normal row's in every difficulty). --classic: the classic rows
(default: expansion). --theme: the palette's dark or light values (default dark). --schematic is accepted for the export
builder and changes nothing. DIR defaults to workspace/render/anim/hire-<seller>-<level>-<seed hex>-schematic/ and must
stay under workspace/. Outputs:
  frame-NNN.png  one frame per step; hire.gif the frames as an animated GIF; index.html the step-through page;
  steps.json the captions and calculations; schematic.json the marker's file list (ADR-0036).

Data shown: the number of names in the range, the name indices (numbers, not strings), the type id, level and price of
each of the ten entries that result; no row of the hireling table, no stat of a type and no name string. Steps: the
inputs; one step for the n seeds; one step per pick (10); one step per listed entry (10); the finished list. Every number
is computed by the model of tools/hirelings.py: build_stock with its trace list for the seeds and the picks, roll_entry
with its trace dict for each entry; this tool recomputes nothing. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import hirelings  # noqa: E402
import rng  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 436
SELLERS = {"kashya": (150, "KASHYA"), "greiz": (198, "GREIZ"), "asheara": (252, "ASHEARA"), "qualkehk": (515, "QUAL-KEHK")}
DIFF = {"normal": 0, "nightmare": 1, "hell": 2}
ACT = {0: "I", 1: "II", 2: "III", 3: "IV", 4: "V"}
HELP = """<li>Step 2: every name of the seller's range gets a seed, one step of the store seed per name, in name order, before any pick.</li>
<li>Picks: ten draws over the range; a pick that lands on a name already listed moves on to the next free name, with no further draw. The grid has one cell per name, in range order.</li>
<li>Entries: each listed name's own seed picks a hireling type among the rows of the seller's act and difficulty, then a level offset; the price follows from the level.</li>
<li>Names are shown as string indices (numbers). Every value is computed by our model for the illustrative inputs given, not observed in the game.</li>"""


def model(t, seller, vf, diff, plvl, seed):
    """The model's list: build_stock with its pick trace, then roll_entry with its trace for every listed name."""
    S = hirelings.Seed(seed, rng.INIT_HIGH)
    picks = []
    tab, n = hirelings.build_stock(t, S, seller, vf, trace=picks)
    row = t.rows[t.seller_row(vf, seller)]
    act = row["Act"] - 1
    entries = []
    for pos in range(n):
        name, eseed, _h, listed = tab[pos]
        if listed:
            tr = {}
            ok, o = hirelings.roll_entry(t, vf, plvl, eseed, act, diff, trace=tr)
            assert ok == 1
            entries.append(dict(pos=pos, name=name, seed=eseed, hid=o[0], level=o[1], price=o[5], tr=tr))
    return dict(tab=tab, n=n, picks=picks, entries=entries, act=act, S_end=(S.low, S.high), first=row["first"],
                last=row["last"])


def build(t, who, sid, vf, diff, plvl, seed, theme):
    m = model(t, sid, vf, diff, plvl, seed)
    n, picks, entries, tab = m["n"], m["picks"], m["entries"], m["tab"]
    assert len(picks) == 10 and len(entries) == 10 and m["S_end"] == _chain(seed, n + 10)
    dn = {v: k for k, v in DIFF.items()}[diff]
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    cols = 17
    cw, ch = 52, 30

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def grid(listed, cur=None, probe=None):
        cells = {}
        for pos in range(n):
            if pos in listed:
                cells[(pos % cols, pos // cols)] = (str(pos), "cur" if pos == cur else "qd_set")
            else:
                cells[(pos % cols, pos // cols)] = (str(pos), "panel")
        rows = (n + cols - 1) // cols
        k.cellgrid(20, 70, cols, rows, cw, ch, cells, sc=2)
        for pos in range(n):
            if pos == probe:
                k.outline(20 + (pos % cols) * cw - 1, 70 + (pos // cols) * ch - 1, cw + 3, ch + 3, "acc", 3)
        return 70 + rows * ch + 14

    # ---- inputs
    header("HIRE LIST: %s, ACT %s, %s, PLAYER LEVEL %d" % (who, ACT[m["act"]], dn.upper(), plvl))
    lines = [("SELLER", "%s, ACT %s" % (who, ACT[m["act"]])), ("GAME", "CLASSIC" if not vf else "EXPANSION"),
             ("DIFFICULTY", dn.upper()), ("PLAYER LEVEL", str(plvl)),
             ("STORE SEED", "%08X : %08X" % (seed, rng.INIT_HIGH)), ("NAMES IN THE SELLER'S RANGE", str(n)),
             ("DRAWS ON THE STORE SEED", "%d + 10 = %d" % (n, n + 10))]
    y = 60
    for lab, val in lines:
        k.text(40, y, lab, "dim", 2)
        k.text(470, y, val, "txt", 2, True)
        y += 32
    k.text(40, y + 14, "ONE SEED PER NAME FIRST, THEN TEN PICKS, THEN EACH PICKED NAME ROLLS ITSELF", "dim", 2)
    k.text(40, y + 44, "NAMES ARE STRING INDICES, SHOWN AS NUMBERS", "dim", 2)
    k.caption("The hire list of %s for a level %d player: a seed per name, ten picks, then each listed name "
              "rolls itself (hirelings D, E)." % (who.title(), plvl), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The hire list of %s in %s for player level %d, from the store seed {%d:%d} (illustrative)." % (
            who.title(), dn, plvl, seed, rng.INIT_HIGH),
        calc=["D3: the seller's Normal row gives the name range %d..%d, n = %d names." % (m["first"], m["last"], n),
              "D4, D5: one build is n + 10 = %d draws on the store seed S (n seeds, then 10 picks)." % (n + 10),
              "E2: the entries roll on the act's rows (act %d) and the game's difficulty (%s)." % (m["act"] + 1, dn)]))

    # ---- the seeds
    header("EVERY NAME GETS A SEED: %d STEPS OF THE STORE SEED" % n)
    show = [0, 1, 2]
    k.text(40, 66, "ONE STEP PER NAME, IN NAME ORDER, BEFORE ANY PICK", "txt", 2, True)
    y = 100
    for pos in show:
        k.rect(40, y, 880, 30, "panel")
        k.outline(40, y, 880, 30, "dim")
        k.text(52, y + 8, "DRAW %d" % (pos + 1), "dim", 2)
        k.text(220, y + 8, "NAME INDEX %d" % tab[pos][0], "txt", 2, True)
        k.text(520, y + 8, "ITS SEED %08X" % tab[pos][1], "acc", 2, True)
        y += 36
    k.text(52, y + 6, "...", "dim", 2)
    y += 36
    pos = n - 1
    k.rect(40, y, 880, 30, "panel")
    k.outline(40, y, 880, 30, "dim")
    k.text(52, y + 8, "DRAW %d" % n, "dim", 2)
    k.text(220, y + 8, "NAME INDEX %d" % tab[pos][0], "txt", 2, True)
    k.text(520, y + 8, "ITS SEED %08X" % tab[pos][1], "acc", 2, True)
    k.text(40, y + 52, "THE FIRST THREE AND THE LAST OF %d" % n, "dim", 2)
    k.caption("Each name takes one step of the store seed, in name order, and keeps the low word as its own seed, "
              "before any pick (hirelings D4).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="Every one of the %d names takes one step of the store seed and keeps the low word as its own seed." % n,
        calc=["D4: for i in 0..%d: Step(S); t[i].seed = S.low (draw i + 1 on S)." % (n - 1),
              "name %d gets seed %d, name %d gets %d, name %d gets %d; the last, name %d, gets %d." % (
                  tab[0][0], tab[0][1], tab[1][0], tab[1][1], tab[2][0], tab[2][1], tab[n - 1][0], tab[n - 1][1])]))

    # ---- the picks
    listed = set()
    for kk, u, v, probes, sd in picks:
        header("PICK %d OF 10: DRAW %d ON THE STORE SEED" % (kk + 1, n + kk + 1))
        listed.add(v)
        ybot = grid(listed, v, u)
        k.text(40, ybot + 4, "DRAW %d = RANGE(%d) = %d" % (n + kk + 1, n, u), "txt", 3, True)
        if probes == 0:
            k.text(40, ybot + 44, "SLOT %d IS FREE: LISTED" % u, "good", 2, True)
        else:
            k.text(40, ybot + 44, "SLOT %d IS LISTED: NEXT FREE IS %d, NO DRAW" % (u, v), "txt", 2, True)
        k.text(40, ybot + 74, "LISTED SO FAR: %d" % len(listed), "dim", 2)
        k.legend(40, ybot + 104, [("qd_set", "LISTED"), ("cur", "THIS PICK"), ("panel", "NOT LISTED")], 2)
        k.caption("Pick %d draws %d from 0 to %d; %s (hirelings D5)." % (
            kk + 1, u, n - 1, "that slot is free, so it is listed" if probes == 0 else
            "that slot is already listed, so the pick steps on to slot %d with no further draw" % v), CAP_Y, 76)
        # the picked cell is drawn highlighted
        frames.append(k.done())
        caps.append(dict(
            text="Pick %d: draw %d gives %d, %s." % (kk + 1, n + kk + 1, u, "listed" if probes == 0 else "taken, so slot %d is listed" % v),
            calc=["D5: u = Range(S, %d) = %d (draw %d on S); S = {%d:%d}." % (n, u, n + kk + 1, sd[0], sd[1]),
                  "D5: %s." % ("t[%d] is not listed or hired: listed = 1." % u if probes == 0 else
                               "t[%d] is listed: the probe steps %d time%s with wrap, to t[%d]: listed = 1, no draw." % (
                                   u, probes, "" if probes == 1 else "s", v))]))

    # ---- the entries
    for j, e in enumerate(entries):
        tr = e["tr"]
        header("ENTRY %d OF 10: NAME INDEX %d" % (j + 1, e["name"]))
        k.text(20, 46, "ROLLED FROM ITS OWN SEED, NOT THE STORE SEED", "dim", 2)
        x0, y = 20, 76
        card = [("OWN SEED", "%08X" % e["seed"], "txt"),
                ("DRAW 1: RANGE(%d)" % tr["k"], "%d" % tr["pick"], "txt"),
                ("HIRELING ID", "%d" % e["hid"], "acc"),
                ("DRAW 2: LOW WORD MOD 5", "%d" % tr["mod"], "txt"),
                ("LEVEL = %d - 5 + %d" % (plvl, tr["mod"]), "%d%s" % (tr["raw"], "  RAISED TO 2" if tr["raw"] < 2 else ""),
                 "txt"),
                ("LEVEL", "%d" % e["level"], "acc"),
                ("PRICE IN GOLD", "%d" % e["price"], "acc")]
        for lab, val, col in card:
            k.rect(x0, y, 470, 34, "panel")
            k.outline(x0, y, 470, 34, "dim")
            k.text(x0 + 10, y + 10, lab, "dim", 2)
            k.text(x0 + 470 - 10 - K.text_w(val, 2), y + 10, val, col, 2, True)
            y += 40
        # the list so far
        lx = 520
        k.text(lx, 76, "THE LIST SO FAR", "dim", 2)
        k.text(lx + 6, 104, "NAME", "dim", 2)
        k.text(lx + 100, 104, "ID", "dim", 2)
        k.text(lx + 150, 104, "LEVEL", "dim", 2)
        k.text(lx + 250, 104, "PRICE", "dim", 2)
        for i in range(j + 1):
            q = entries[i]
            cur = i == j
            k.rect(lx, 126 + i * 28, 420, 24, "cur" if cur else "panel")
            col = "txt"
            k.text(lx + 6, 132 + i * 28, str(q["name"]), col, 2, cur)
            k.text(lx + 100, 132 + i * 28, str(q["hid"]), col, 2, cur)
            k.text(lx + 156, 132 + i * 28, str(q["level"]), col, 2, cur)
            k.text(lx + 250, 132 + i * 28, str(q["price"]), col, 2, cur)
        k.caption("Name %d rolls from its own seed: draw 1 picks hireling id %d among %d, draw 2 gives level %d, and "
                  "the price is %d gold (hirelings E)." % (e["name"], e["hid"], tr["k"], e["level"], e["price"]),
                  CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="Entry %d, name %d: hireling id %d, level %d, price %d gold." % (j + 1, e["name"], e["hid"], e["level"], e["price"]),
            calc=["E1: s = Init(%d) = {%d:%d}; E2: %d rows share the act and difficulty." % (
                e["seed"], e["seed"], rng.INIT_HIGH, tr["k"]),
                  "E3: draw 1 = Range(s, %d) = %d, the row's id is %d." % (tr["k"], tr["pick"], e["hid"]),
                  "E4: draw 2, low word %d, mod 5 = %d; L = %d - 5 + %d = %d%s." % (
                      tr["low"], tr["mod"], plvl, tr["mod"], tr["raw"], ", raised to 2" if tr["raw"] < 2 else ""),
                  "E5: level %d, price %d gold." % (e["level"], e["price"])]))

    # ---- the list
    header("THE HIRE LIST: 10 NAMES")
    k.text(40, 50, "NAME", "dim", 2)
    k.text(200, 50, "ID", "dim", 2)
    k.text(300, 50, "LEVEL", "dim", 2)
    k.text(440, 50, "PRICE", "dim", 2)
    for i, q in enumerate(entries):
        y = 78 + i * 32
        k.rect(40, y, 560, 28, "panel")
        k.outline(40, y, 560, 28, "dim")
        k.text(50, y + 7, str(q["name"]), "txt", 2, True)
        k.text(210, y + 7, str(q["hid"]), "txt", 2)
        k.text(310, y + 7, str(q["level"]), "txt", 2)
        k.text(450, y + 7, str(q["price"]), "txt", 2)
    k.text(630, 90, "%d DRAWS ON THE STORE SEED" % (n + 10), "txt", 2, True)
    k.text(630, 124, "10 ENTRIES, EACH ROLLED", "dim", 2)
    k.text(630, 150, "FROM ITS OWN SEED", "dim", 2)
    k.text(630, 190, "ROLLED AGAIN AT A HIRE", "dim", 2)
    k.text(630, 216, "AT THE PLAYER'S LEVEL THEN", "dim", 2)
    k.caption("The finished list: ten names, each with a hireling id, a level and a price; the build took %d draws "
              "on the store seed (hirelings D4, E4)." % (n + 10), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The finished list of %d names took %d draws on the store seed; the store seed ends at {%d:%d}." % (
            10, n + 10, m["S_end"][0], m["S_end"][1]),
        calc=["D4: n + 10 = %d draws; S = {%d:%d}." % (n + 10, m["S_end"][0], m["S_end"][1]),
              "E: entries (name, id, level, price): %s." % "; ".join(
                  "%d, %d, %d, %d" % (q["name"], q["hid"], q["level"], q["price"]) for q in entries)]))
    return frames, caps, k.pal, m


def _chain(seed, draws):
    lo, hi = seed, rng.INIT_HIGH
    for _ in range(draws):
        lo, hi = rng.step(lo, hi)
    return lo, hi


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    classic = "--classic" in argv
    if classic:
        argv.remove("--classic")
    opts = {"--difficulty": "normal", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 4 or argv[1] not in SELLERS or opts["--difficulty"] not in DIFF or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        plvl, seed = int(argv[2]), int(argv[3], 0)
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (1 <= plvl <= 99 and 0 < seed <= 0xFFFFFFFF):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    t = hirelings.Tables(os.path.join(argv[0], "data", "global", "excel"))
    vf = 0 if classic else 1
    sid, who = SELLERS[argv[1]]
    if t.seller_row(vf, sid) is None:
        print("no %s rows for %s" % ("classic" if classic else "expansion", argv[1]), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim",
                                        "hire-%s-%d-%x-schematic" % (argv[1], plvl, seed))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _m = build(t, who, sid, vf, DIFF[opts["--difficulty"]], plvl, seed, opts["--theme"])
    K.write_illustration(out, "hire", frames, caps, W, H, K.palette(opts["--theme"])[1], "hire list animation", HELP,
                         targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
