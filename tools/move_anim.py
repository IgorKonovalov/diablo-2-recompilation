"""Animate a moving unit's per-frame step on subtiles (docs/specs/anim/movement.md section B): the step from the path speed and
the direction, the position in 16.16 subtiles after each game frame, the snap onto the point on the last frame, and the end.
Schematic only (ADR-0036): boxes and text in our own palette; the unit is a toy given by its numbers.

Usage:
  python3 -I tools/move_anim.py <root> [--speed walk|run|knockback|N] [--dist D] [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); this tool reads no game file and ignores it.
--speed: the path speed v: walk 1536 (a player's walk at X = 100 in the worked example), run 2304, knockback 4096, or a number
from 1 to 32767 (the default is walk). --dist D: the point's distance on the x axis in subtiles, 1 to 5 (default 3). The unit
starts at the centre of subtile 0 and its direction is the axis row, (4096, 0). --theme: dark or light palette values.
--schematic is accepted for the export builder and changes nothing. DIR defaults to
workspace/render/anim/move-<v>-<D>-schematic/ and must stay under workspace/. Outputs: frame-NNN.png, move.gif, index.html,
steps.json, schematic.json (ADR-0036).

Steps: the inputs; one step per game frame of the walk (the position after the step, the snap on the last); the end. Every
step is a call of tools/anim.py step_model (movement B1 and B3, the model that reproduces the logged steps), with path_step for
the axis step; every free subtile entered is passed as free to its collision walk. The closed form of B3 (a point D subtiles
away takes the ceiling of 65536 D / step frames) is asserted equal to the number of calls. Not shown: the collision walk's
blocked and tenth-crossing cases (B4), the diagonal rows, the path's later points, replans and the target check (B5), and how
the speed itself comes about (A). Times are game frames after the first step. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim  # noqa: E402
import anim_common  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 420
SPEEDS = {"walk": 1536, "run": 2304, "knockback": 4096}
HELP = """<li>The strip is a row of subtiles; the unit starts at the centre of the first one and has one point, at the centre of a later one.</li>
<li>Each game frame the unit moves by a step computed from its path speed; the step is the same on every frame until the last one.</li>
<li>On the last frame the point is nearer than a whole step, so the step becomes exactly the distance left and the unit lands on the point.</li>
<li>Positions are in 1/65536 of a subtile. Every value is computed by our model for the toy numbers given, not observed in the game.</li>"""


def walk_frames(v, dist):
    """The frames of the walk by the model: -> list of dict(x, y, i, step, snapped, sub) after each call of step_model, ending
    when the point is reached."""
    pt = (dist, 0)
    p = dict(f34=0x20, np=1, v=v, d=(4096, 0), pt=pt, ty=0, x=0x8000, y=0x8000, i=0, pts=[pt])
    out = []
    sx, sy = anim.path_step(v, p["d"], 0x400)
    for _ in range(100000):
        if p["i"] >= p["np"]:
            break
        res = anim.step_model(p, [(-1, 1)])               # a probe: the mismatch reports the subtile the step enters
        if isinstance(res, tuple) and res and res[0] == "ct-mismatch":
            nsub = res[2]
            res = anim.step_model(p, [(nsub[0] | (nsub[1] << 16), 1)])
        elif res == "need-ct" or res is None:
            break
        x, y, i = res[0], res[1], res[2]
        out.append(dict(x=x, y=y, i=i, step=anim.s32(x - p["x"]), snapped=anim.s32(x - p["x"]) != sx, before=p["x"]))
        p.update(x=x, y=y, i=i)
    return out


def build(v, dist, theme):
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    fr = walk_frames(v, dist)
    n = len(fr)
    s = anim.s32(v * 0x400) >> 6
    sx, sy = anim.path_step(v, (4096, 0), 0x400)
    assert sy == 0 and sx == (4096 * s) >> 12
    if sx:
        assert n == -(-(65536 * dist) // sx)              # movement B3: ceil(65536 d / step) frames
    ncell = dist + 1
    cw = min(150, 880 // ncell)
    X0, Y0 = 20, 120

    def header(s_):
        k.text(20, 12, s_, "acc", 2, True)

    def strip(pos, trail=()):
        """Subtiles 0..dist as cells, the point's centre marked, the unit at pos (16.16) and its earlier positions."""
        for c in range(ncell):
            k.box(X0 + c * cw, Y0, cw + 1, 70, [], "panel", "grey", sc=2)
            k.text(X0 + c * cw + 6, Y0 + 52, "SUBTILE %d" % c, "dim", 1)
        px = X0 + dist * cw + cw // 2
        k.vline(px, Y0 - 8, Y0 + 78, "blue", 2)
        k.text_c(px, Y0 - 24, "POINT", "blue", 2, True)
        for t in trail:
            k.vline(X0 + t * cw // 65536, Y0 + 20, Y0 + 40, "dim", 2)
        ux = X0 + pos * cw // 65536
        k.rect(ux - 5, Y0 + 14, 11, 28, "acc")
        k.outline(ux - 5, Y0 + 14, 11, 28, "txt")

    def text(rows, y0=215, dy=26):
        for i, r in enumerate(rows):
            sx_, col, b = (r + (False,))[:3] if isinstance(r, tuple) else (r, "txt", False)
            k.text(20, y0 + i * dy, sx_, col, 2, b)

    def put(cap, txt, calc):
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(text=txt, calc=calc))

    # ---- the inputs
    header("A UNIT'S STEP: PATH SPEED %d, A POINT %d SUBTILES AWAY" % (v, dist))
    strip(0x8000)
    text([("S = (V * 1024) >> 6 = (%d * 1024) >> 6 = %d" % (v, s), "txt", True),
          "STEP = (D * S) >> 12, D = 4096 ON THE AXIS ROW", "     = (4096 * %d) >> 12 = %d" % (s, sx),
          "THAT IS %d.%03d OF A SUBTILE A FRAME" % (sx // 65536, sx % 65536 * 1000 // 65536),
          "THE UNIT STARTS AT THE CENTRE OF SUBTILE 0: POSITION 32768",
          ("%d FRAMES TO REACH THE POINT" % n, "acc", True)], dy=26)
    put("A unit with path speed %d steps %d in 1/65536 of a subtile each game frame along the axis; the point is %d subtiles away, "
        "at a subtile centre, and the unit takes %d frames to reach it (movement B1, B3)." % (v, sx, dist, n),
        "A toy unit: path speed %d, a point %d subtiles away." % (v, dist),
        ["movement B1: s = (p.speed * k) >> 6 = (%d * 1024) >> 6 = %d with k = 0x400." % (v, s),
         "movement B1: stepX = (dirX * s) >> 12 = (4096 * %d) >> 12 = %d." % (s, sx),
         "movement B3: a point d subtiles away takes ceil(65536 d / step) = ceil(%d / %d) = %d frames." % (65536 * dist, sx, n)])
    # ---- the steps
    trail = []
    for j, f in enumerate(fr):
        header("GAME FRAME %d OF %d" % (j + 1, n))
        trail.append(f["before"])
        strip(f["x"], trail)
        sub, frac = f["x"] >> 16, f["x"] & 0xFFFF
        left = (dist << 16) + 0x8000 - f["before"]
        rows = [("POSITION = %d + %d = %d" % (f["before"], f["step"], f["x"]), "txt", True),
                "  = SUBTILE %d, %d / 65536" % (sub, frac),
                "LEFT BEFORE THE STEP: %d" % left]
        if (f["i"] >= 1):
            rows += [("LEFT %d IS NOT MORE THAN THE STEP %d:" % (left, sx), "good", True),
                     ("THE STEP BECOMES THE %d LEFT, THE POINT IS REACHED" % left, "good", True)]
        else:
            rows += ["LEFT %d IS MORE THAN THE STEP %d: NO SNAP" % (left, sx)]
        if sub != (f["before"] >> 16):
            rows += ["THE STEP ENTERS SUBTILE %d: ITS FREE TEST PASSES" % sub]
        text(rows, dy=26)
        put("Game frame %d: the unit moves %d to position %d, in subtile %d.%s" % (
            j + 1, f["step"], f["x"], sub, " The point is within one step, so the step becomes the %d left and the unit "
            "lands on the point (movement B3)." % left if (f["i"] >= 1) else ""),
            "Game frame %d: moves %d, position %d%s." % (j + 1, f["step"], f["x"], ", snapped onto the point" if (f["i"] >= 1) else ""),
            ["movement B1: step = %d; position = %d + %d = %d." % (f["step"] if not (f["i"] >= 1) else sx, f["before"],
                                                                    f["step"], f["x"]),
             ("movement B3: both axis distances left (%d, 0) are at most m = max(|stepX|, |stepY|) = %d: the step becomes the "
              "remaining delta %d and the point is reached." % (left, sx, left)) if (f["i"] >= 1) else
             "movement B3: the distance left %d exceeds m = %d, so the step stays." % (left, sx)])
    # ---- the end
    header("THE END: %d FRAMES" % n)
    strip(fr[-1]["x"], trail)
    text([("THE UNIT IS AT THE CENTRE OF SUBTILE %d" % dist, "txt", True), "NO POINT IS LEFT: THE PATH STOPS",
          "THE NEXT CALL SNAPS TO THE SUBTILE CENTRE AND ENDS THE MOVE",
          ("%d FRAMES = CEIL(65536 * %d / %d)" % (n, dist, sx), "acc", True)], dy=26)
    put("The unit stands on the point after %d frames, the ceiling of 65536 * %d / %d; with no point left the path stops "
        "(movement B3, B5)." % (n, dist, sx), "The unit has reached the point after %d frames." % n,
        ["movement B3: ceil(65536 * %d / %d) = %d frames." % (dist, sx, n),
         "movement B5: with no point left PathStop snaps to the subtile centre and the step returns 2."])
    return frames, caps, k.pal, fr


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--speed": "walk", "--dist": "3", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            if i + 1 >= len(argv):
                print(__doc__.strip(), file=sys.stderr)
                return 2
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1 or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        v = SPEEDS[opts["--speed"]] if opts["--speed"] in SPEEDS else int(opts["--speed"])
        dist = int(opts["--dist"])
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (1 <= v <= 32767 and 1 <= dist <= 5) or (4096 * (anim.s32(v * 0x400) >> 6)) >> 12 < 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if -(-(65536 * dist) // ((4096 * (anim.s32(v * 0x400) >> 6)) >> 12)) > 40:
        print("too many frames for this speed (at most 40)", file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "move-%d-%d-schematic" % (v, dist))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _i = build(v, dist, opts["--theme"])
    K.write_illustration(out, "move", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "unit movement animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
