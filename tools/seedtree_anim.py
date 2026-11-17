"""Animate the seed tree (docs/specs/rng/seeds.md steps 1 to 5): the game's seeds, the five acts' seeds, a level's seed
as a sum, and each room's seed as one draw on its level. Schematic only (ADR-0036): boxes, text and lines in our own
palette.

Usage:
  python3 -I tools/seedtree_anim.py <root> <seed> [--act N] [--levels a,b,c] [--rooms N] [--theme dark|light]
                                    [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); this tool reads no game file and ignores
it. <seed> is the game's seed override N, decimal or 0x hex (an illustrative input, never a seed a game derives).
--act: the act (0 to 4, 0 = Act I; default 0) whose levels are shown. --levels: up to three level ids (default 1,2,3).
--rooms: the rooms of the first level shown (1 to 5; default 3). --theme: dark or light palette values (default dark).
--schematic is accepted for the export builder and changes nothing. DIR defaults to
workspace/render/anim/seedtree-<seed hex>-schematic/ and must stay under workspace/. Outputs:
  frame-NNN.png one frame per step; seedtree.gif the animated GIF; index.html the step-through page with each step's
  arithmetic; steps.json the captions and calculations; schematic.json the marker's file list.

Steps: the map seed and game seed from N (step 1); one step per act (3a-3c: Init on the map seed, one step for the level
seed base, Act II's tomb pair draws, Act III's one draw); one step with the chosen levels' seeds (step 4: base + level
id, no draw); one step per room of the first level (step 5: one draw on the level seed, then the room's own seed is
initialised from it and steps once); the whole tree. Every value comes from the DRLG model's Act and Seed classes
(tools/drlg.py), the spec's step list as the model implements it; the act link builder's later draws on the act seed
(step 3d) are not shown. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import drlg  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 520
CAP_Y = 436
ACTN = ["ACT I", "ACT II", "ACT III", "ACT IV", "ACT V"]
ACTR = ["I", "II", "III", "IV", "V"]
HELP = """<li>Top: the map seed (it builds the world) and the game seed (it seeds the units); both start from the same number N when the game is made with an override.</li>
<li>Second row: one box per act. Every act starts from the map seed, steps once, and keeps that low word as its level seed base.</li>
<li>Third row: each level's seed is the act's base plus the level id, a sum with no draw.</li>
<li>Bottom row: each room takes one draw from its level's seed, starts its own seed from the result and steps once.</li>
<li>Every value is computed by our model for the illustrative seed given, not observed in the game.</li>"""


def trace(n, act, levels, rooms):
    """The tree from the DRLG model. -> dict with the map and game seeds, the five acts, the shown levels' seeds and the
    first level's rooms. Seeds are (low, high)."""
    acts = []
    for i in range(5):
        a = drlg.Act(i, n, 0)
        f = drlg.Seed(n & drlg.M32)                              # step 3a, 3b: Init(map seed), one step
        f.step()
        assert f.lo == a.base
        acts.append(dict(idx=i, base=a.base, first=(f.lo, f.hi), seed=(a.seed.lo, a.seed.hi), tombs=a.tombs,
                         bit=getattr(a, "bit474", None), steps=a.seed.n))
    base = acts[act]["base"]
    lvls = []
    for lid in levels:
        lv = drlg.Seed((base + lid) & drlg.M32)                  # step 4: Init(base + id), a u32 sum, no draw
        lvls.append(dict(id=lid, sum=lv.lo, seed=(lv.lo, lv.hi)))
    rms = []
    lv = drlg.Seed((base + levels[0]) & drlg.M32)
    for r in range(rooms):                                       # step 5, per room
        lv.step()                                                # one level draw
        rs = drlg.Seed(lv.lo)                                    # Init(room.seed, level.seed.low)
        rs.step()                                                # room draw 1
        rms.append(dict(n=r + 1, level=(lv.lo, lv.hi), room=(rs.lo, rs.hi), r04=rs.lo))
    gseed = drlg.Seed(n & drlg.M32)
    return dict(n=n & drlg.M32, game=(gseed.lo, gseed.hi), acts=acts, levels=lvls, rooms=rms, act=act)


def fs(s):
    return "{%08x:%08x}" % s


def build(n, act, levels, rooms, theme):
    T = trace(n, act, levels, rooms)
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    AX = [20 + 188 * i for i in range(5)]
    aw, ah, ay = 176, 76, 132
    ly, lh = 244, 62
    ry, rh = 346, 62
    lw = 288
    rw = 920 // max(rooms, 1) - 10 if rooms > 3 else 288

    def hdr(s):
        k.text(20, 10, s, "acc", 2, True)

    def top(stage):
        k.box(20, 34, 380, 56, [("MAP SEED", "dim"), ("N = %d" % T["n"], "txt")], "panel", "acc", sc=2)
        k.box(560, 34, 380, 56, [("GAME SEED", "dim"), ("%08X:%08X" % T["game"], "txt")], "panel", "dim", sc=2)
        k.text(420, 52, "SAME N", "dim", 2)
        k.text(420, 68, "UNDER AN OVERRIDE", "dim", 1)
        k.text(560, 96, "SEEDS THE UNITS, NOT THE MAP", "dim", 1)

    def act_row(upto, hl=None):
        for i in range(upto):
            a = T["acts"][i]
            lines = [(ACTN[i], "txt"), ("BASE %08X" % a["base"], "good")]
            if a["tombs"] != (0, 0):
                lines.append(("TOMBS %d,%d" % a["tombs"], "dim"))
            elif a["bit"] is not None:
                lines.append(("GATE BIT %d" % a["bit"], "dim"))
            else:
                lines.append(("NO EXTRA DRAW", "dim"))
            if a["tombs"] != (0, 0) or a["bit"] is not None:
                lines[-1] = (lines[-1][0], "dim")
            edge = "acc" if i == hl else "dim"
            fill = "cur" if i == hl else "panel"
            k.box(AX[i], ay, aw, ah, lines, fill, edge, sc=2)
            cx = AX[i] + aw // 2
            k.vline(cx, 116, ay - 1, "dim", 2)
        if upto:
            k.hline(AX[0] + aw // 2, AX[upto - 1] + aw // 2, 116, "dim", 2)
            k.vline(210, 90, 116, "dim", 2)

    def lvl_row(upto, hl=0):
        a = T["acts"][act]
        ax = AX[act] + aw // 2
        k.vline(ax, ay + ah, ly - 12, "acc", 2)
        for i in range(upto):
            L = T["levels"][i]
            x = 20 + i * (lw + 28)
            k.box(x, ly, lw, lh, [("LEVEL %d" % L["id"], "txt"), ("%08X + %d" % (a["base"], L["id"]), "dim"),
                                  ("= %08X" % L["sum"], "good")], "cur" if i == hl else "panel",
                  "acc" if i == hl else "dim", sc=2)
            k.vline(x + lw // 2, ly - 12, ly - 1, "acc", 2)
        k.hline(20 + lw // 2, 20 + (upto - 1) * (lw + 28) + lw // 2, ly - 12, "acc", 2)
        k.hline(min(ax, 20 + lw // 2), max(ax, 20 + lw // 2), ly - 12, "acc", 2)

    def room_row(upto, hl=None):
        L0 = 20 + lw // 2
        k.vline(L0, ly + lh, ry - 12, "acc", 2)
        for i in range(upto):
            R = T["rooms"][i]
            x = 20 + i * (rw + 10)
            k.box(x, ry, rw, rh, [("ROOM %d" % R["n"], "txt"), ("DRAW %08X" % R["level"][0], "dim"),
                                  ("ROOM %08X" % R["room"][0], "good")], "cur" if i == hl else "panel",
                  "acc" if i == hl else "dim", sc=2)
            k.vline(x + rw // 2, ry - 12, ry - 1, "acc", 2)
        if upto:
            k.hline(min(L0, 20 + rw // 2), max(L0, 20 + (upto - 1) * (rw + 10) + rw // 2), ry - 12, "acc", 2)

    def cap(s):
        k.caption(s, CAP_Y, 76)

    # ---- step 1
    hdr("SEED TREE FOR N = %d" % T["n"])
    top(0)
    cap("The game made with seed N has two roots. The map seed is N and builds the world; the game seed starts from "
        "N too and seeds the units.")
    frames.append(k.done())
    caps.append(dict(
        text="The game has two roots: the map seed, which builds acts, levels and rooms, and the game seed, which seeds the units.",
        calc=["N = %d (illustrative), an override of the seed." % T["n"],
              "map seed = N = %d; game seed = Init(N) = %s (low:high)." % (T["n"], fs(T["game"])),
              "Under an override the two start from the same number; they stay two separate seeds."]))
    # ---- steps 3: acts
    for i in range(5):
        a = T["acts"][i]
        hdr("EACH ACT: INIT ON THE MAP SEED, STEP ONCE")
        top(0)
        act_row(i + 1, hl=i)
        cap("%s: the act seed starts from the map seed, steps once, and keeps its low word %d as the level seed base%s." % (
            ACTR[i], a["base"],
            "; Act II then draws two tomb numbers mod 7 until they differ" if i == 1 else
            ("; Act III then takes one more draw and keeps its lowest bit" if i == 2 else "")))
        frames.append(k.done())
        calc = ["Init(act seed, map seed): %s (low:high)." % fs((n & drlg.M32, 666)),
                "Step once: act seed = %s; level seed base = its low word = %d." % (fs(a["first"]), a["base"])]
        if i == 1:
            calc.append("Tomb pairs: %d pair(s) of steps, low word mod 7 each, until the two differ; tombs = %d and %d (a + 66, b + 66)."
                        % ((a["steps"] - 1) // 2, a["tombs"][0], a["tombs"][1]))
        if i == 2:
            calc.append("One more step; the Kurast gate bit = low word and 1 = %d." % a["bit"])
        if i in (1, 2):
            calc.append("Act seed after these draws = %s (low:high). Later link-builder draws are not shown." % fs(a["seed"]))
        caps.append(dict(text="Act %s: Init on the map seed, one step, and the low word is the level seed base, %d." % (
            ACTR[i], a["base"]), calc=calc))
    # ---- step 4: levels
    a = T["acts"][act]
    hdr("A LEVEL'S SEED IS THE ACT'S BASE PLUS THE LEVEL ID")
    top(0)
    act_row(5, hl=act)
    lvl_row(len(levels))
    cap("In %s each level's seed is the level seed base plus the level id: a sum, with no draw on the act seed, so the "
        "order levels are built in does not matter." % ACTN[act])
    frames.append(k.done())
    caps.append(dict(
        text="Level seeds: Init on the act's base plus the level id, a sum with no draw.",
        calc=["%s level seed base = %d." % (ACTN[act], a["base"])] +
             ["Level %d: Init(%d + %d) = Init(%d) = %s (low:high), no draw." % (
                 L["id"], a["base"], L["id"], L["sum"], fs(L["seed"])) for L in T["levels"]]))
    # ---- step 5: rooms
    L0 = T["levels"][0]
    for i in range(rooms):
        R = T["rooms"][i]
        hdr("EACH ROOM TAKES ONE DRAW FROM ITS LEVEL")
        top(0)
        act_row(5, hl=act)
        lvl_row(len(levels))
        room_row(i + 1, hl=i)
        cap("Level %d, room %d: one draw on the level seed gives %d; the room's seed starts from it and steps once, "
            "and that first value %d is kept." % (L0["id"], R["n"], R["level"][0], R["room"][0]))
        frames.append(k.done())
        caps.append(dict(
            text="Level %d, room %d: one draw on the level seed, then the room's own seed starts from it and steps once." % (
                L0["id"], R["n"]),
            calc=["Level seed before the draw: %s (low:high)." % fs(T["rooms"][i - 1]["level"] if i else L0["seed"]),
                  "Step the level seed once: %s (low:high); the draw is its low word, %d." % (fs(R["level"]), R["level"][0]),
                  "Init(room seed, %d), then one step: room seed = %s (low:high)." % (R["level"][0], fs(R["room"])),
                  "The room keeps its first value %d as its starting point." % R["r04"]]))
    # ---- the whole tree
    hdr("THE SEED TREE")
    top(0)
    act_row(5, hl=act)
    lvl_row(len(levels))
    room_row(rooms)
    k.legend(20, 418, [("good", "THE VALUE THE NEXT ROW STARTS FROM"), ("dim", "A VALUE TAKEN ALONG THE WAY")], 1)
    cap("From one number the whole chain is fixed: acts from the map seed, levels by a sum, rooms by one draw each in "
        "the order the generator creates them.")
    frames.append(k.done())
    caps.append(dict(
        text="The whole chain from N: acts from the map seed, levels by a sum, rooms by one draw each in creation order.",
        calc=["map seed N = %d; level seed base of %s = %d." % (T["n"], ACTN[act], a["base"]),
              "level %d seed = %s; room 1 to %d seeds follow in creation order." % (L0["id"], fs(L0["seed"]), rooms)]))
    return frames, caps, T


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--act": "0", "--levels": "1,2,3", "--rooms": "3", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        n, act, rooms = int(argv[1], 0), int(opts["--act"]), int(opts["--rooms"])
        levels = [int(x) for x in opts["--levels"].split(",")]
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (0 < n <= drlg.M32 and 0 <= act <= 4 and 1 <= rooms <= 5 and 1 <= len(levels) <= 3
            and all(0 <= x < 0x1000 for x in levels) and opts["--theme"] in K.THEMES):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "seedtree-%x-schematic" % n)
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _t = build(n, act, levels, rooms, opts["--theme"])
    K.write_illustration(out, "seedtree", frames, caps, W, H, K.palette(opts["--theme"])[1], "seed tree animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
