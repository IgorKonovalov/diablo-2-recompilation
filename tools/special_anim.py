"""Animate the champion-or-unique roll and the weighted mod picks of a special monster (docs/specs/monsters/special.md
sections A and B): the champion chance draw, then either one champion mod pick or the unique group's picks, each with
its candidates, total and draw. Schematic only (ADR-0036): boxes, text and bars in our own palette.

Usage:
  python3 -I tools/special_anim.py <root> <monster id> <seed> [--difficulty 0|1|2|normal|nightmare|hell] [--classic]
        [--theme dark|light] [--out DIR] [--schematic]

<root> is the merged data tree (workspace/merged). <monster id> is a MonStats Id (default use: zombie1); its class
decides which mods can be picked. <seed> is an illustrative input: the unit's seed is {seed, 666}, not a seed the game
derives. Defaults: difficulty 0 (normal), the expansion game (--classic: a classic game); the pass's random boss
(champion allowed). --theme: dark or light palette values. --schematic is accepted for the export builder and changes
nothing. DIR defaults to workspace/render/anim/special-<id>-d<difficulty>-<seed hex>-schematic/ and must stay under
workspace/. Outputs: frame-NNN.png, special.gif, index.html, steps.json, schematic.json (ADR-0036).

Steps: the inputs; the champion draw (Range(seed, 100) against the chance of the table's first row); then, on a champion,
the one mod pick, or, on a unique, the Range(seed, 1) draw (it returns 0 but steps the seed) and one pick per mod
(1 + difficulty of them), each with the candidates that passed the row tests, their total, the draw and the winner;
a last step with the mod list. Every number is the model's of tools/monspecial.py (Data.mods_roll and the records of its
picks); the number of steps the seed took is asserted equal to the draw count of special.md A1.

What a frame shows of the MonUMod table (a per-mod weight table is not shown, in this tool or anywhere in the export):
only the winner's name and weight of each pick, the number of rows that carry a weight of the pick's kind, the number
of candidates after the class and version tests and the ones already held, and their total. Not shown: the mod
handlers (special.md C, D), minions (E), the name (I) and the pass's other draws. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import excel_bin  # noqa: E402
import monspecial  # noqa: E402
import rng  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 436
DIFF = {"normal": 0, "nightmare": 1, "hell": 2, "0": 0, "1": 1, "2": 2}
DIFF_NAME = ("normal", "nightmare", "hell")
HELP = """<li>Top: the mods of the unit so far, in the order they are written. A champion gets one mod and no more; a unique gets 1 + difficulty of them.</li>
<li>Champion chance: a draw from 0 to 99 below the chance of the first MonUMod row (20) makes a champion, and then no draw is made for the unique group.</li>
<li>A pick: the rows with a weight of the pick's kind are tested against the class and version; the ones left are the candidates, one draw from 0 to the total picks the first whose running weight passes it.</li>
<li>Only the winner's weight is shown, not the table. Every value is computed by our model for the illustrative inputs given, not observed in the game.</li>"""


def mod_names(excel):
    h, rows = excel_bin.read_txt(excel_bin.find_file(excel, "monumod", ".txt"))
    return [r[0].strip() for r in rows]


def class_index(excel, mid):
    h, rows = excel_bin.read_txt(excel_bin.find_file(excel, "monstats", ".txt"))
    for i, r in enumerate(rows):
        if r[0].strip() == mid:
            return i
    return None


def trace(d, cls, diff, exp, seed):
    """The model's SpecialModsRoll with the unit's seed {seed, 666}, its records and the check that the seed stepped
    as special.md A1 counts: Range(100), then Range(1) and one draw per pick for a unique, or one pick for a champion."""
    s = monspecial.Seed((seed, rng.INIT_HIGH))
    mods = [0] * 9
    out = d.mods_roll(s, mods, diff, exp, cls, 1)
    steps = 1 + (len(out["picks"]) if out["champion"] else 1 + len(out["picks"]))
    lo, hi = seed, rng.INIT_HIGH
    for _ in range(steps):
        lo, hi = rng.step(lo, hi)
    assert (lo, hi) == s.t(), (steps, s.t())
    for p in out["picks"]:
        if p["total"] >= 1:
            assert p["x"] < p["total"]
    return out, mods, steps


def build(root, mid, diff, exp, seed, theme):
    excel = os.path.join(root, "data", "global", "excel")
    d = monspecial.Data(excel)
    cls = class_index(excel, mid)
    names = mod_names(excel)
    out, mods, nsteps = trace(d, cls, diff, exp, seed)
    chance = d.constants(0)
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    held = []
    champion = out["champion"]
    r100 = out["r100"]
    dn = DIFF_NAME[diff]

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def modrow(n_shown, cur=None):
        k.text(20, 46, "MODS OF THE UNIT" + ("" if n_shown else ": NONE YET"), "dim", 2)
        cells = [names[m].upper() for m in held[:n_shown]]
        cw = 210
        for i in range(3):
            lab = cells[i] if i < len(cells) else None
            k.box(20 + i * (cw + 8), 68, cw, 38, [lab] if lab else [], "cur" if i == cur else "panel",
                  "acc" if i == cur else "dim", "txt", 2, bold=bool(lab))

    # ---- inputs
    header("SPECIAL MONSTER: %s, %s%s" % (mid.upper(), dn.upper(), "" if exp else ", CLASSIC"))
    modrow(0)
    k.text(20, 130, "THE PASS ROLLS ITS RANDOM BOSS: A CHAMPION IS ALLOWED", "txt", 2)
    k.text(20, 160, "UNIT SEED {%d, 666}" % seed, "dim", 2)
    k.text(20, 190, "CHAMPION: ONE DRAW, THEN ONE MOD PICK", "dim", 2)
    k.text(20, 216, "UNIQUE: ONE DRAW, THEN 1 + DIFFICULTY = %d MOD PICKS" % (1 + diff), "dim", 2)
    k.caption("A random boss of class %s in %s: the champion chance is drawn first; a champion gets one mod, a "
              "unique %d (special A)." % (mid, dn, 1 + diff), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="A special monster roll for class %s in %s: a champion or a unique, then the weighted mod picks." % (mid, dn),
        calc=["special.md A1: SpecialModsRoll(unit, allowChampion = 1) on the unit seed {%08x, 666} (illustrative)." % seed,
              "class %s (MonStats row %d), %s, %s game; the unit has no mods yet." % (
                  mid, cls, dn, "expansion" if exp else "classic"),
              "A1: a champion costs one pick, a unique costs Range(1) and 1 + difficulty picks = %d." % (1 + diff)]))

    # ---- the champion roll
    header("CHAMPION DRAW: RANGE(SEED, 100)")
    modrow(0)
    k.box(20, 130, 300, 90, [("DRAW", "dim"), ("%d" % r100, "acc")], "panel", "dim", "txt", 3, bold=True)
    k.text(340, 140, "BELOW %d: A CHAMPION" % chance, "txt", 2, True)
    k.text(340, 170, "%d %s %d: %s" % (r100, "<" if champion else ">=", chance,
                                       "A CHAMPION" if champion else "NOT A CHAMPION, A UNIQUE"),
           "good" if champion else "txt", 2, True)
    bw = 900
    k.bar(20, 250, bw, 22, chance, 100, "acc", "grey")
    mx = 20 + r100 * bw // 100
    k.rect(mx - 1, 242, 3, 38, "txt")
    k.text(20, 284, "0", "dim", 2)
    k.text(20 + bw - K.text_w("99", 2), 284, "99", "dim", 2)
    k.caption("Range(seed, 100) = %d; below %d is a champion with one mod. %s (special A1)." % (
                  r100, chance, "This one is a champion" if champion else "This one is not, so a unique group follows"),
              CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The champion draw is %d, %s %d: %s." % (r100, "below" if champion else "not below", chance,
                                                    "a champion" if champion else "a unique"),
        calc=["A1: r = Range(unit.seed, 100) = %d (draw 1)." % r100,
              "A1: (i32) r %s c = MonUMod[0].constants = %d: %s." % ("<" if champion else ">=", chance,
                                                                      "champion (flag 0x04), ChampionModPick follows"
                                                                      if champion else "not a champion")]))
    if not champion:
        n = 1 + diff
        header("UNIQUE: RANGE(SEED, 1), THEN %d PICKS" % n)
        modrow(0)
        k.text(20, 130, "RANGE(SEED, 1) STEPS THE SEED ONCE AND RETURNS 0", "txt", 2)
        k.text(20, 160, "N = 0 + 1 + DIFFICULTY = %d MODS" % n, "txt", 3, True)
        k.text(20, 200, "EACH PICK DRAWS ONCE AND CANNOT TAKE A MOD THE UNIT ALREADY HAS", "dim", 2)
        k.caption("A unique: Range(seed, 1) is drawn for the step it takes (it returns 0), so the group gets "
                  "1 + difficulty = %d mods, one pick each (special A1, B2)." % n, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="A unique: one more draw, Range(1), then %d picks." % n,
            calc=["A1: n = Range(unit.seed, 1) + 1 + difficulty = 0 + 1 + %d = %d (draw 2)." % (diff, n),
                  "A1: have = the unit's mods so far = none; each pick is UniqueModPick (B2), one draw each."]))
    # ---- the picks
    for i, p in enumerate(out["picks"]):
        res, total, x, cands = p["res"], p["total"], p["x"], p["cands"]
        champ = p["kind"] == "champion"
        wins = dict(cands)
        off = (0x0E if champ else 0x14) + 2 * diff
        rows_kind = sum(1 for r in range(len(d.mu)) if d.mu_s16(r, off) > 0 and (d.mu[r][8] != 0) == champ)
        assert all(r_ in range(len(d.mu)) for r_, _w in cands) and len(cands) <= rows_kind
        held_before = list(held)
        held.append(res)
        header("%s MOD PICK %d OF %d" % ("CHAMPION" if champ else "UNIQUE", i + 1, len(out["picks"])))
        modrow(len(held_before), cur=len(held_before))
        refused = rows_kind - len(cands)
        k.rect(20, 124, 920, 150, "panel")
        k.outline(20, 124, 920, 150, "dim")
        k.text(34, 134, "ROWS WITH A WEIGHT OF THIS KIND: %d" % rows_kind, "dim", 2)
        k.text(34, 160, "NOT CANDIDATES (CLASS, VERSION, HELD): %d" % refused, "dim", 2)
        k.text(34, 190, "CANDIDATES: %d   TOTAL: %d" % (len(cands), total), "txt", 3, True)
        k.text(34, 228, "DRAW X = RANGE(SEED, %d) = %d" % (total, x), "txt", 2, True)
        k.bar(34, 252, 890, 12, 1, 1, "grey", "grey")
        k.rect(34 + x * 890 // max(total, 1) - 1, 246, 3, 24, "acc")
        k.box(20, 290, 920, 86, [(names[res].upper(), "good"), ("ITS WEIGHT %d" % wins[res], "dim")], "cur", "good", "txt", 3,
              bold=True)
        k.text(20, 392, "THE FIRST CANDIDATE WHOSE RUNNING WEIGHT PASSES X WINS", "dim", 2)
        k.caption("%s pick %d: %d candidates, total %d, draw %d: row %d, %s, with weight %d (special B%d)." % (
            "Champion" if champ else "Unique", i + 1, len(cands), total, x, res, names[res], wins[res], 1 if champ else 2),
            CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="%s pick %d: %d candidates, total %d, draw %d, so %s." % (
                "Champion" if champ else "Unique", i + 1, len(cands), total, x, names[res]),
            calc=["B%d: %d rows carry a weight of this kind; %d are candidates after ModEligible (class, version, fPick)%s." % (
                      1 if champ else 2, rows_kind, len(cands), "" if champ else " and the mods the unit has"),
                  "B%d: total = %d; x = Range(unit.seed, %d) = %d; seed = {%08x:%08x}." % (
                      1 if champ else 2, total, total, x, p["us"][0], p["us"][1]),
                  "B%d: the first candidate whose running weight exceeds x is row %d, %s (weight %d)." % (
                      1 if champ else 2, res, names[res], wins[res])]))
    # ---- the end
    header("THE MOD LIST")
    modrow(len(held))
    k.text(20, 130, "%s" % ("A CHAMPION: ONE MOD" if champion else "A UNIQUE: %d MODS" % len(held)), "txt", 3, True)
    k.text(20, 172, "%d STEPS OF THE UNIT SEED IN ALL" % nsteps, "dim", 2)
    k.text(20, 198, "THE MOD HANDLERS RUN AFTER THIS (NOT SHOWN)", "dim", 2)
    k.caption("The roll is done: %s, after %d steps of the unit seed (special A1). Handlers apply the mods afterwards." % (", ".join(names[m] for m in held), nsteps), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The mod list: %s; the unit seed stepped %d times." % (", ".join(names[m] for m in held), nsteps),
        calc=["mods = %s." % ", ".join("%d %s" % (m, names[m]) for m in held),
              "steps of the unit seed = %d (A1: the champion draw, then %s)." % (
                  nsteps, "one pick" if champion else "Range(1) and one per pick"),
              "unit seed after = {%08x:%08x}." % tuple(rng_final(seed, nsteps))]))
    assert held == [m for m in mods if m]
    return frames, caps, k.pal, out


def rng_final(seed, n):
    lo, hi = seed, rng.INIT_HIGH
    for _ in range(n):
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
    opts = {"--difficulty": "0", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 3 or opts["--difficulty"].lower() not in DIFF or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        seed = int(argv[2], 0)
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not 0 < seed <= 0xFFFFFFFF:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    excel = os.path.join(argv[0], "data", "global", "excel")
    if class_index(excel, argv[1]) is None:
        print("no MonStats Id %r" % argv[1], file=sys.stderr)
        return 2
    diff = DIFF[opts["--difficulty"].lower()]
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim",
                                        "special-%s-d%d-%x-schematic" % (argv[1], diff, seed))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _o = build(argv[0], argv[1], diff, 0 if classic else 1, seed, opts["--theme"])
    K.write_illustration(out, "special", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "special monster roll animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
