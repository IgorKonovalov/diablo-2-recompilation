"""Animate the game's random number generator (docs/specs/rng/README.md): one seed's two words, the multiply-and-add,
the draw and its `mod n`, draw after draw. Schematic only (ADR-0036): boxes, text and bars in our own palette.

Usage:
  python3 -I tools/rng_anim.py <root> <seed> [--count N] [--range N] [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); this tool reads no game file and ignores
it. <seed> is the number the seed starts from, in decimal or 0x hex (an illustrative input, as the randomness page's
worked example uses 12345). --count: the draws shown (default 8, at most 12). --range: n of each draw (default 100;
at least 1). --theme: the palette's dark or light values (default dark). --schematic is accepted for the export builder
and changes nothing: this tool has no other mode. DIR defaults to workspace/render/anim/rng-<seed>-<count>-schematic/
and must stay under workspace/. Outputs:
  frame-NNN.png  one frame per step; rng.gif the frames as an animated GIF; index.html the step-through page with each
  step's arithmetic; steps.json the captions and calculations; schematic.json the marker's file list (ADR-0036).

Steps: the start (Init: the low word is the number, the high word 666); then one step per draw: low x 6AC690C5 + high as
one 64-bit number, its low 32 bits the new low word and its high 32 bits the new high word, the draw the new low word
mod n; a last step with the whole tape. Every value is computed by the RNG model of tools/rng.py (step and rng_range);
the arithmetic shown is the model's step, asserted equal to it. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import rng  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 436
HELP = """<li>Top row: the seed's two words before the draw, the multiplier, and the 64-bit result low x multiplier + high; its upper half becomes the new high word and its lower half the new low word.</li>
<li>Middle: the draw is the new low word mod n (here n is the range); that remainder is the number the game uses.</li>
<li>Bottom: the numbers drawn so far, newest highlighted. A range below 1 would draw nothing and leave the seed alone; it is not shown.</li>
<li>Every value is computed by our model of the generator for the illustrative seed given, not observed in the game.</li>"""


def trace(seed, count, n):
    """The model's run: [(low, high) before, (low, high) after, product, result] per draw, plus the start state.
    Each draw is rng.rng_range (the model of Range); the product is the arithmetic of rng.step, asserted equal to it."""
    lo, hi = seed & rng.MASK, rng.INIT_HIGH
    start = (lo, hi)
    draws = []
    for _ in range(count):
        before = (lo, hi)
        prod = lo * rng.MULT + hi
        res, nlo, nhi = rng.rng_range(lo, hi, n)
        assert (nlo, nhi) == (prod & rng.MASK, (prod >> 32) & rng.MASK) == rng.step(lo, hi)
        draws.append((before, (nlo, nhi), prod, res))
        lo, hi = nlo, nhi
    return start, draws


def build(seed, count, n, theme):
    start, draws = trace(seed, count, n)
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    mult_dec = rng.MULT

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def word_box(x, y, w, label, val, fill="panel", edge="dim", col="txt"):
        k.rect(x, y, w, 76, fill)
        k.outline(x, y, w, 76, edge)
        k.text_c(x + w // 2, y + 8, label, "dim", 2)
        k.text_c(x + w // 2, y + 34, "%08X" % val, col, 3, True)

    def tape(done, cur):
        k.text(20, 372, "DRAWS", "dim", 2)
        cw = min(100, (W - 40) // count)
        vals = [str(draws[i][3]) if i < done else None for i in range(count)]
        k.tape(20, 392, vals, cw, 34, cur=cur, sc=2)

    def op(x, y, s):
        k.text_c(x, y + 30, s, "txt", 3, True)

    def blank_row(state, ghost=False):
        lo, hi = state
        word_box(20, 54, 170, "LOW", lo)
        op(205, 54, "X")
        word_box(225, 54, 170, "MULTIPLIER", rng.MULT, edge="blue", col="blue")
        op(410, 54, "+")
        word_box(430, 54, 170, "HIGH", hi)

    # ---- the start
    header("INIT: THE SEED STARTS AS TWO WORDS")
    word_box(20, 54, 170, "LOW", start[0], edge="acc")
    word_box(225, 54, 170, "HIGH", start[1], edge="acc")
    k.text(20, 150, "N = %d" % (start[0]), "txt", 3, True)
    k.text(20, 190, "LOW = N, HIGH = 666", "dim", 2)
    k.text(20, 230, "EACH DRAW STEPS THE SEED ONCE, THEN TAKES THE NEW LOW WORD MOD THE RANGE", "dim", 2)
    tape(0, None)
    k.caption("Seed N = %d, range %d, %d draws. The seed is two 32-bit words; Init sets the low word to N and "
              "the high word to 666." % (start[0], n, count), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="Init: the seed starts as two 32-bit words, the low word set to N and the high word to 666.",
        calc=["N = %d (illustrative), range n = %d, %d draws." % (start[0], n, count),
              "low word = N = %d, high word = 666." % start[0],
              "seed = {%08x:%08x} (low:high)." % start]))
    # ---- the draws
    for i, (before, after, prod, res) in enumerate(draws):
        header("SEED %d   RANGE(%d)   DRAW %d OF %d" % (start[0], n, i + 1, count))
        blank_row(before)
        k.text_c(618, 84, "=", "txt", 3, True)
        # the product, as its two halves
        k.text(635, 33, "64-BIT RESULT", "dim", 2)
        word_box(635, 54, 150, "BITS 32-63", after[1], edge="good", col="good")
        word_box(790, 54, 150, "BITS 0-31", after[0], edge="acc", col="acc")
        k.arrow(710, 134, 710, 184, "good")
        k.arrow(865, 134, 865, 184, "acc")
        k.text_c(710, 192, "NEW HIGH", "good", 2, True)
        k.text_c(865, 192, "NEW LOW", "acc", 2, True)
        k.text(20, 150, "LOW X 6AC690C5 + HIGH, ONE 64-BIT NUMBER", "dim", 2)
        k.text(20, 180, "= %d" % prod, "txt", 2)
        # the draw
        k.rect(20, 230, 920, 110, "panel")
        k.outline(20, 230, 920, 110, "dim")
        k.text(34, 240, "THE DRAW = NEW LOW MOD THE RANGE", "dim", 2)
        s = "%d MOD %d = " % (after[0], n)
        k.text(34, 280, s, "txt", 3, True)
        k.text(34 + K.text_w(s, 3) + 6, 280, str(res), "acc", 4, True)
        k.bar(34, 322, 700, 10, res, max(n - 1, 1), "acc", "grey")
        k.text(748, 318, "0..%d" % (n - 1), "dim", 2)
        tape(i + 1, i)
        k.caption("Draw %d: step the seed, then the new low word mod %d is %d. The next draw starts from the new "
                  "words." % (i + 1, n, res), CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="Draw %d: the seed steps once and the draw is the new low word mod %d, here %d." % (i + 1, n, res),
            calc=["step: low x 0x6AC690C5 + high, one 64-bit number: %d x %d + %d = %d." % (
                      before[0], mult_dec, before[1], prod),
                  "new low = its bits 0 to 31 = %d; new high = its bits 32 to 63 = %d." % after,
                  "seed = {%08x:%08x} (low:high)." % after,
                  "draw = new low mod n = %d mod %d = %d." % (after[0], n, res)]))
    # ---- the tape
    header("THE %d DRAWS, IN ORDER" % count)
    k.text(20, 60, "EACH IS THE NEW LOW WORD OF ONE STEP, MOD %d" % n, "dim", 2)
    cw = min(100, (W - 40) // count)
    k.text(20, 120, "DRAWS", "dim", 2)
    k.tape(20, 140, [str(d[3]) for d in draws], cw, 44, sc=3)
    k.text(20, 210, "FINAL SEED (LOW:HIGH)", "dim", 2)
    k.text(20, 236, "%08X:%08X" % draws[-1][1], "txt", 3, True)
    k.caption("Same seed, same range, same %d numbers every time: each draw depends only on the two words the last one "
              "left." % count, CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The %d draws in order. The same seed and range give the same numbers every time." % count,
        calc=["draws = %s." % ", ".join(str(d[3]) for d in draws),
              "final seed = {%08x:%08x} (low:high)." % draws[-1][1]]))
    return frames, caps, k.pal


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--count": "8", "--range": "100", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    seed, count, n = int(argv[1], 0), int(opts["--count"]), int(opts["--range"])
    if not (1 <= count <= 12 and 1 <= n <= 0x7FFFFFFF and 0 <= seed <= rng.MASK and opts["--theme"] in K.THEMES):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "rng-%d-%d-schematic" % (seed, count))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal = build(seed, count, n, opts["--theme"])
    K.write_illustration(out, "rng", frames, caps, W, H, K.palette(opts["--theme"])[1], "random number generator animation",
                         HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
