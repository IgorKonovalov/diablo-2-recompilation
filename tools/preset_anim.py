"""Animate a preset's keep/drop rolls (docs/specs/drlg/preset.md 2 and 3): the instance's unit list walked from its head,
each unit that draws taking one step of the seed and being kept or dropped by its test. Schematic only (ADR-0036):
boxes, text and lines in our own palette; each unit is one cell, with no map, tile or picture.

Usage:
  python3 -I tools/preset_anim.py <root> <seed> [--preset lutw|lutn|catne] [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); the tool reads the preset's unit list
(object, monster and place entries, and their ids) from the DS1 file the model reads, and the id tables beside it,
never a tile layer or a picture. <seed> is the seed the rolls run on, decimal or 0x hex, started with Init (an
illustrative input, never a seed a game derives). --preset: lutw or lutn (the two Lut Gholein maps) or catne (Catacombs
Level 2's map); default lutw. --theme: dark or light (default dark). --schematic is accepted for the export builder
and changes nothing. DIR defaults to workspace/render/anim/preset-<preset>-<seed hex>-schematic/ and must stay under
workspace/. Outputs:
  frame-NNN.png one frame per step; preset.gif the animated GIF; index.html the step-through page; steps.json the
  captions and calculations; schematic.json the marker's file list.

Steps: the list in walk order (the list's head is the last entry of the file); one step per unit that draws (the seed
before and after, the draw, its test, kept or dropped, and the units passed with no draw since the last roll); the
kept list. Every value comes from the DRLG model's preset unit data (tools/drlg.py: PresetUnitData.ds1 and
PresetUnitData.drop_rolls); the tests shown are the spec's step 3a table, checked against the model's answer at each
roll. Stdlib only.
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
PRESETS = {"lutw": ("Act2\\Town\\LutW.ds1", "LUT GHOLEIN, MAP LUTW"),
           "lutn": ("Act2\\Town\\LutN.ds1", "LUT GHOLEIN, MAP LUTN"),
           "catne": ("Act1\\Catacomb\\CatNE.ds1", "CATACOMBS LEVEL 2, MAP CATNE")}
VENDORS = {204: "VENDOR 1", 205: "VENDOR 2", 371: "LIGHTNING SPIRE", 372: "FIRE TOWER"}
# the spec's step 3a: (type, kind) -> (words of the test, python test, keep chance num, den)
MON_RULE = ("R MOD 3 = 0", lambda r: r % 3 == 0, 1, 3, lambda r: r % 3)
RULES = {("m", 204): MON_RULE, ("m", 205): MON_RULE, ("m", 371): MON_RULE, ("m", 372): MON_RULE,
         ("p", 33): ("R AND 3 != 0", lambda r: r & 3 != 0, 3, 4, lambda r: r & 3),
         ("p", 34): ("R AND 1 != 0", lambda r: r & 1 != 0, 1, 2, lambda r: r & 1),
         ("p", 35): ("R AND 3 = 0", lambda r: r & 3 == 0, 1, 4, lambda r: r & 3),
         ("o", 196): ("R AND 1 = 0", lambda r: r & 1 == 0, 1, 2, lambda r: r & 1), ("o", 261): ("R AND 1 = 0", lambda r: r & 1 == 0, 1, 2, lambda r: r & 1),
         ("o", 581): ("R AND 3 != 0", lambda r: r & 3 != 0, 3, 4, lambda r: r & 3)}
HELP = """<li>Top: one cell per unit of the preset's list, in the order the rolls walk it (the last entry of the file first).</li>
<li>A unit that is one of the ten ids takes one step of the seed and is kept or dropped by its test; every other unit is kept with no draw.</li>
<li>Each step is one roll: the seed before and after, the draw r, the test and its answer.</li>
<li>Every value is computed by our model for the illustrative seed given, not observed in the game.</li>"""


def fx(v):
    return "%08X" % v


def fs(lo, hi):
    return "{%08x:%08x}" % (lo, hi)


def kind_of(pu, u):
    """-> (rule key or None, words naming the unit) of one unit of the list (type, id, ...)."""
    typ, uid = u[0], u[1]
    if typ == 1 and uid < pu.nm:
        return ("m", uid), "MONSTER %d%s" % (uid, " (%s)" % VENDORS[uid] if uid in VENDORS else "")
    if typ == 1 and uid - pu.nm >= pu.ns:
        p = uid - pu.nm - pu.ns
        return ("p", p), ("GROUP %d PLACE" % (25 * (p - 32)) if p in (33, 34, 35) else "MONSTER PLACE %d" % p)
    if typ == 1:
        return None, "SUPERUNIQUE %d" % (uid - pu.nm)
    if typ == 2:
        return ("o", uid), ("FLOOR TRAP %d" % uid if uid in (196, 261) else "OBJECT %d" % uid)
    return None, "UNIT %d, TYPE %d" % (uid, typ)


def trace(root, seed, preset):
    """The model's rolls over a preset's unit list. -> dict: units (walk order), the draws per unit, the kept list and
    the seed before and after each roll. The seed is Init(seed): low = seed, high = 666."""
    exe = os.path.join(os.path.dirname(os.path.abspath(root)), "install", "app", "game.exe")
    pu = drlg.PresetUnitData(root, exe)
    cell, label = PRESETS[preset]
    units = pu.ds1(cell)["units"]
    s0 = (seed & drlg.M32, drlg.INIT_HIGH)
    inst, send, draws = pu.drop_rolls(units, s0, 0, 0)
    # which unit drew: the model on every prefix of the list (a unit drew when the prefix has one more draw)
    rows, prev, seeds = [], 0, [s0]
    for n in range(1, len(units) + 1):
        _i, sn, dn = pu.drop_rolls(units[:n], s0, 0, 0)
        if len(dn) > prev:
            rows.append(dict(n=n - 1, draw=dn[-1], before=seeds[-1], after=sn))
            seeds.append(sn)
            prev = len(dn)
    assert [r["draw"] for r in rows] == draws and seeds[-1] == send
    return dict(pu=pu, units=units, label=label, rows=rows, kept=inst, s0=s0, send=send)


def build(root, seed, preset, theme):
    T = trace(root, seed, preset)
    pu, units, rows = T["pu"], T["units"], T["rows"]
    n = len(units)
    drew = {r["n"]: r for r in rows}
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    cols = min(n, 34)
    cw = min(26, 900 // max(cols, 1))
    nrows = (n + cols - 1) // cols
    GX, GY = 20, 62

    def hdr(s):
        k.text(20, 12, s, "acc", 2, True)

    def grid(upto, cur=None):
        """The unit cells: units before `upto` are done (a roll's answer or kept with no draw), the rest wait."""
        for i in range(n):
            x, y = GX + (i % cols) * cw, GY + (i // cols) * 28
            if i in drew and i < upto:
                fill = "good" if drew[i]["draw"][3] else "bad"
            elif i < upto:
                fill = "roomdone"
            else:
                fill = "panel"
            edge = "acc" if i in drew else "grey"
            k.rect(x, y, cw - 2, 24, fill)
            k.outline(x, y, cw - 2, 24, edge, 2 if i in drew else 1)
            if i == cur:
                k.outline(x - 2, y - 2, cw + 2, 28, "txt", 2)
        k.legend(GX, GY + nrows * 28 + 6, [("panel", "NOT WALKED"), ("roomdone", "KEPT, NO DRAW"), ("good", "KEPT BY ITS ROLL"),
                                         ("bad", "DROPPED BY ITS ROLL")], 1, 12)
        k.text(GX, GY + nrows * 28 + 22, "THICK EDGE: A UNIT THAT DRAWS", "dim", 1)

    # ---- frame 0: the list
    ndraw = len(rows)
    hdr("KEEP OR DROP ROLLS: %s" % T["label"])
    k.text(GX, 38, "THE LIST IN WALK ORDER, FROM ITS HEAD: THE FILE'S LAST ENTRY FIRST", "dim", 2)
    grid(0)
    iy = GY + nrows * 28 + 54
    k.box(20, iy, 440, 110, [("%d UNITS" % n, "txt"), ("%d OF THEM DRAW (THICK EDGE)" % ndraw, "txt"),
                            ("THE OTHERS ARE KEPT, NO DRAW", "dim")], "panel", "dim", sc=2, align="l")
    k.box(480, iy, 460, 110, [("SEED THE ROLLS RUN ON", "dim"), (fs(*T["s0"]).replace("{", "").replace("}", "").upper()
                                                              .replace(":", " : "), "txt"), ("EACH ROLL IS ONE STEP", "dim")],
          "panel", "dim", sc=2, align="l")
    k.caption("The preset's units are walked from the head of the list. Ten kinds of unit are kept or dropped by chance, one "
              "draw each; every other unit is kept with no draw.", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The preset's %d units are walked from the head of the list; %d of them draw." % (n, ndraw),
        calc=["Unit list of %s: %d units, head first (the last entry of the file is the head)." % (T["label"].title(), n),
              "Units that draw: %d, at walk positions %s." % (ndraw, ", ".join(str(r["n"] + 1) for r in rows) or "none"),
              "Seed the rolls run on: Init(%d) = %s (low:high)." % (T["s0"][0], fs(*T["s0"]))]))
    # ---- one frame per roll
    passed_from = 0
    for j, r in enumerate(rows):
        u = units[r["n"]]
        key, words = kind_of(pu, u)
        rule = RULES[key]
        typ, uid, rv, keep = r["draw"]
        assert rule[1](rv) == keep and (typ, uid) == (u[0], u[1])
        passed = r["n"] - passed_from
        passed_from = r["n"] + 1
        hdr("ROLL %d OF %d: %s" % (j + 1, ndraw, words))
        grid(r["n"] + 1, cur=r["n"])
        iy = GY + nrows * 28 + 54
        lines = [("UNIT %d OF %d: %s" % (r["n"] + 1, n, words), "txt"),
                 ("SEED %s" % (fx(r["before"][0]) + ":" + fx(r["before"][1])), "dim"),
                 ("STEP: R = %s" % fx(rv), "txt"),
                 ("SEED %s" % (fx(r["after"][0]) + ":" + fx(r["after"][1])), "dim"),
                 ("KEPT IF %s" % rule[0], "txt"),
                 ("%s = %d: %s" % (" ".join(rule[0].split()[:3]), rule[4](rv), "KEPT" if keep else "DROPPED"),
                  "good" if keep else "bad")]
        k.box(20, iy, 560, 134, lines[:3] + lines[4:], "panel", "dim", sc=2, align="l")
        k.text(600, iy + 4, "KEEP CHANCE %d IN %d" % (rule[2], rule[3]), "dim", 2)
        k.bar(600, iy + 30, 340, 22, rule[2], rule[3], "good" if keep else "bad", label=None)
        since = "BEFORE THE FIRST ROLL," if j == 0 else "SINCE THE LAST ROLL,"
        k.text(600, iy + 64, "%d UNITS PASSED %s" % (passed, since), "dim", 1)
        k.text(600, iy + 78, "ALL KEPT, NO DRAW", "dim", 1)
        k.text(600, iy + 98, "SEED AFTER: %s:%s" % (fx(r["after"][0]), fx(r["after"][1])), "dim", 1)
        if keep:
            cap = ("%s takes a draw: r = %d, and the test %s holds, so it is kept." % (
                words.capitalize(), rv, rule[0].lower()))
        else:
            cap = ("%s takes a draw: r = %d, and the test %s fails, so it is dropped." % (
                words.capitalize(), rv, rule[0].lower()))
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        tw = {"R MOD 3 = 0": "r mod 3 = %d (kept when 0)" % (rv % 3), "R AND 1 != 0": "r and 1 = %d (kept when not 0)" % (rv & 1),
              "R AND 1 = 0": "r and 1 = %d (kept when 0)" % (rv & 1), "R AND 3 != 0": "r and 3 = %d (kept when not 0)" % (rv & 3),
              "R AND 3 = 0": "r and 3 = %d (kept when 0)" % (rv & 3)}[rule[0]]
        caps.append(dict(
            text="Roll %d: %s is %s." % (j + 1, words.lower(), "kept" if keep else "dropped"),
            calc=["Walk position %d of %d: %s (type %d, id %d); %d unit%s passed %s, all kept with no draw." % (
                r["n"] + 1, n, words.lower(), typ, uid, passed, "" if passed == 1 else "s",
                "before the first roll" if j == 0 else "since the last roll"),
                  "Seed before: %s (low:high); one step; seed after: %s." % (fs(*r["before"]), fs(*r["after"])),
                  "r = low word of the new seed = %d; test: %s." % (rv, tw),
                  "Keep chance %d in %d; result: %s." % (rule[2], rule[3], "kept" if keep else "dropped")]))
    # ---- the kept list
    hdr("THE KEPT LIST: %s" % T["label"])
    grid(n)
    iy = GY + nrows * 28 + 54
    kd = sum(1 for r in rows if r["draw"][3])
    k.box(20, iy, 440, 134, [("%d UNITS WALKED" % n, "txt"), ("%d KEPT, %d DROPPED" % (len(T["kept"]), n - len(T["kept"])), "txt"),
                            ("%d ROLLS: %d KEPT, %d DROPPED" % (ndraw, kd, ndraw - kd), "dim")], "panel", "dim", sc=2, align="l")
    k.box(480, iy, 460, 134, [("SEED AFTER THE LAST ROLL", "dim"), ("%s : %s" % (fx(T["send"][0]), fx(T["send"][1])), "txt"),
                             ("THE KEPT LIST IS BACK IN", "dim"), ("FILE ORDER", "dim")], "panel", "dim", sc=2, align="l")
    k.caption("The walk is done: %d of the %d units are kept. The kept units are back in file order, and the seed has stepped "
              "once per roll." % (len(T["kept"]), n), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The walk is done: %d of %d units are kept, in file order." % (len(T["kept"]), n),
        calc=["Kept: %d units (%d of them by a roll, %d with no draw); dropped: %d." % (
            len(T["kept"]), kd, len(T["kept"]) - kd, n - len(T["kept"])),
              "Seed after the last roll: %s (low:high) = Init(%d) stepped %d time%s." % (
                  fs(*T["send"]), T["s0"][0], ndraw, "" if ndraw == 1 else "s")]))
    return frames, caps, T


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--preset": "lutw", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            if i + 1 >= len(argv):
                print(__doc__.strip(), file=sys.stderr)
                return 2
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        n = int(argv[1], 0)
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (0 < n <= drlg.M32 and opts["--preset"] in PRESETS and opts["--theme"] in K.THEMES):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "preset-%s-%x-schematic" % (opts["--preset"], n))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _t = build(argv[0], n, opts["--preset"], opts["--theme"])
    K.write_illustration(out, "preset", frames, caps, W, H, K.palette(opts["--theme"])[1], "preset keep and drop rolls animation",
                         HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
