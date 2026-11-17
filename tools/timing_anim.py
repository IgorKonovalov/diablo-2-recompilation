"""Animate the schedule of a timed mode (docs/specs/anim/timing.md sections E, F and J): the rate from the speed and a
speed bonus, then the animation position advancing by that rate once per game frame, the event frame falling due, and
the end. Schematic only (ADR-0036): boxes, text and bars in our own palette.

Usage:
  python3 -I tools/timing_anim.py <root> [--mode cast|gethit] [--stat N] [--frames F] [--speed V] [--start S]
        [--event E] [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); this tool reads no game file and ignores
it. It draws a toy animation record given by its numbers: --frames F (default 14), --speed V (the record's speed word,
default 256), --start S (the start frame, default 0), --event E (the frame carrying event byte 1, default 7; -1 for none).
--mode picks the rate branch of timing J2: cast (the faster cast rate stat, default 20) or gethit (the faster hit
recovery stat; default 0), and --stat N is that stat's value. The attack branch is not drawn (its X also takes the
attack speed stat, which this toy record does not model). The defaults are timing's worked example 1 (a Sorceress cast at 20), whose numbers the frames show.
--theme: dark or light palette values. --schematic is accepted for the export builder and changes nothing. DIR defaults to
workspace/render/anim/timing-<mode>-<stat>-schematic/ and must stay under workspace/. Outputs: frame-NNN.png, timing.gif,
index.html, steps.json, schematic.json (ADR-0036).

Steps: the inputs and the rate; one step per scan step k (the animation position 256 S + k r, the frames it passes, the
events it queues); the end. The rate is the model of tools/anim_rates.py (bonus, rate_cast, rate_gethit);
the queue is tools/anim.py schedule (the model of timing E1), and the closed forms of timing E2 (anim_rates.closed_len
and the event frame formula) are asserted equal to it. Times are game frames after the start frame T. Not shown: the
every-frame advance of monsters (timing F), the reschedules of skills (E3), the speed stats' other terms and a real
record's data. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim  # noqa: E402
import anim_common  # noqa: E402
import anim_rates  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 436
HELP = """<li>Top row: the game frames after the mode starts at T. The scan takes one step per game frame; the end fires one frame after the last step.</li>
<li>Middle row: the animation's own frames. The marker is the position in 1/256 of a frame, it advances by the rate r each step; a frame event queues on the step whose position has passed its frame.</li>
<li>The rate comes from the record's speed and a speed bonus; the length of the mode is the record's 256 F divided by r, rounded up, and at least 2.</li>
<li>The record is a toy given by its numbers, not a table row. Every value is computed by our model for the numbers given, not observed in the game.</li>"""
MODES = {"cast": ("FASTER CAST", 2), "gethit": ("FASTER HIT RECOVERY", 1)}


def rate_of(mode, speed, stat):
    """-> (bonus term, X, rate): timing J1 and the J2 branch of the mode."""
    b = anim_rates.bonus(MODES[mode][1], stat)
    if mode == "cast":
        x = min(100 + b, 175)
        return b, x, anim_rates.rate_cast(speed, b)
    x = b + 50
    return b, x, anim_rates.rate_gethit(speed, b)


def trace(F, S, ev, r):
    """The model's queue (anim.schedule from T = 0) and the closed forms of timing E2, asserted equal to it."""
    q = anim.schedule(0, S, r, F << 8, lambda f: 1 if f == ev else 0)
    end = [e for e in q if e[0] == 1][0][1]
    evs = [e for e in q if e[0] == 0]
    if r > 0:
        assert end == anim_rates.closed_len(F, S, r)
        assert end == anim_rates.sched_len(F, S, r)[0]
        n_steps = end - 1 if F > S and end > 2 else 0
        for e in evs:
            kf = max(1, anim_rates.ceil_div((ev - S) << 8, r))
            assert e[1] == kf and kf <= n_steps
    return q, end, evs


def build(mode, stat, F, speed, S, ev, theme):
    b, x, r = rate_of(mode, speed, stat)
    q, end, evs = trace(F, S, ev, r)
    steps = end - 1 if F > S else 0           # scan steps k = 1 .. N, the end fires at T + N + 1
    steps = max(steps, 0)
    ev_t = evs[0][1] if evs else None
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    label = MODES[mode][0]
    ncells = end + 1
    cwg = min(64, 900 // ncells)
    cwa = min(64, 900 // F)

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def timeline(cur_k, queued):
        k.text(20, 44, "GAME FRAMES AFTER THE START T", "dim", 2)
        for i in range(ncells):
            lab = "T" if i == 0 else "+%d" % i
            tag = None
            fill, edge = "panel", "grey"
            if i == cur_k:
                fill, edge = "cur", "acc"
            if ev_t is not None and i == ev_t and ev_t in queued:
                fill, edge = "qd_magic", "blue"
                tag = "EVENT"
            if i == end and end in queued:
                fill, edge = "qd_set", "good"
                tag = "END"
            k.box(20 + i * cwg, 66, cwg + 1, 34, [lab], fill, edge, "txt", 2 if cwg >= 40 else 1)
            if tag:
                k.text_c(20 + i * cwg + cwg // 2, 106, tag, "good" if tag == "END" else "blue", 1, True)

    def animrow(acc):
        k.text(20, 140, "ANIMATION FRAMES: %d, THE EVENT ON FRAME %s" % (F, ev if ev >= 0 else "NONE"), "dim", 2)
        for f in range(F):
            passed = acc is not None and f <= (acc >> 8)
            fill, edge = ("good" if False else "cur") if passed else "panel", "grey"
            if f == ev:
                edge, fill = "blue", ("qd_magic" if not passed else "cur")
            k.box(20 + f * cwa, 162, cwa + 1, 40, [str(f)], fill, edge, "txt", 2 if cwa >= 30 else 1)
        if acc is not None:
            mx = 20 + acc * cwa // 256
            k.vline(mx, 160, 226, "acc", 3)
            k.text(min(mx + 6, 20 + F * cwa - 150), 214, "POSITION %d.%02d" % (acc >> 8, (acc & 255) * 100 // 256), "acc", 2, True)

    # ---- inputs
    header("SCHEDULE: %s %d, %d FRAMES, SPEED %d" % (label, stat, F, speed))
    timeline(None, set())
    animrow(None)
    ytxt = 250
    if mode == "cast":
        calc = "B = 120 X %d / (120 + %d) = %d;  X = MIN(100 + B, 175) = %d" % (stat, stat, b, x)
    else:
        calc = "B = 120 X %d / (120 + %d) = %d;  X = B + 50 = %d" % (stat, stat, b, x)
    if stat == 0:
        calc = calc.replace("120 X 0 / (120 + 0) = 0", "0")
    k.text(20, ytxt, calc, "txt", 2)
    k.text(20, ytxt + 30, "RATE R = SPEED X X / 100 = %d X %d / 100 = %d" % (speed, x, r), "acc", 2, True)
    k.text(20, ytxt + 60, "LENGTH L = 256 X F = %d;  START POSITION 256 X S = %d" % (F << 8, S << 8), "dim", 2)
    k.text(20, ytxt + 90, "STEP K, ON GAME FRAME T + K: POSITION = 256 S + K R", "dim", 2)
    k.text(20, ytxt + 116, "SCANNING STOPS WHEN THE POSITION REACHES L", "dim", 2)
    k.caption("%d animation frames at speed %d with %s %d: the rate is %d per game frame, in 1/256 of an "
              "animation frame (timing J, E)." % (F, speed, label.lower(), stat, r), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="A toy record of %d frames, speed %d, start frame %d, event byte 1 on frame %d, with %s %d: the rate is %d." % (
            F, speed, S, ev, label.lower(), stat, r),
        calc=["timing J1: B = (k x s) / (k + s) with k = 120 and s = %d gives %d." % (stat, b),
              "timing J2: X = %d, r = speed x X / 100 = %d x %d / 100 = %d." % (x, speed, x, r),
              "timing E1: length L = 256 F = %d, S = %d, so the position starts at %d and gains %d per step." % (
                  F << 8, S, S << 8, r)]))
    # ---- the steps
    queued = set()
    prev_hi = None
    for kk in range(1, steps + 1):
        acc = (S << 8) + kk * r
        lo = S if prev_hi is None else prev_hi + 1
        hi = acc >> 8
        prev_hi = max(hi, prev_hi if prev_hi is not None else hi)
        fired = [e for e in evs if e[1] == kk]
        assert bool(fired) == (ev >= 0 and lo <= ev <= min(hi, 0x8F) and kk <= steps)
        if fired:
            queued.add(kk)
        header("STEP %d, ON GAME FRAME T + %d" % (kk, kk))
        timeline(kk, queued | ({ev_t} if ev_t is not None and ev_t < kk else set()))
        animrow(acc)
        k.text(20, 250, "POSITION = 256 X %d + %d X %d = %d  (FRAME %d)" % (S, kk, r, acc, acc >> 8), "txt", 2, True)
        k.text(20, 280, "THIS STEP SCANS FRAMES %d TO %d" % (lo, hi) if hi >= lo else "THIS STEP SCANS NO NEW FRAME", "dim", 2)
        if fired:
            k.text(20, 310, "FRAME %d CARRIES EVENT BYTE 1: QUEUED FOR T + %d" % (ev, kk), "blue", 2, True)
            k.text(20, 340, "CLOSED FORM: T + MAX(1, CEIL(256 X (%d - %d) / %d)) = T + %d" % (ev, S, r, kk), "dim", 2)
        elif ev_t is not None and ev_t < kk:
            k.text(20, 310, "EVENT BYTE 1 ALREADY QUEUED FOR T + %d" % ev_t, "dim", 2)
        k.text(20, 372, "%d STEPS SO FAR; NEXT POSITION %d %s %d" % (kk, acc + r, "<" if acc + r < (F << 8) else ">=", F << 8),
               "dim", 2)
        k.caption("Step %d on game frame T + %d: the position is %d, frame %d.%s" % (
            kk, kk, acc, acc >> 8, " Frame %d carries the event, so it is queued for T + %d (timing E1, E2)." % (ev, kk)
            if fired else ""), CAP_Y, 76)
        frames.append(k.done())
        calc = ["timing E1: step k = %d, t = T + %d: position = 256 S + k r = %d + %d x %d = %d < L = %d." % (
            kk, kk, S << 8, kk, r, acc, F << 8),
                "timing E1: frames %d to %d are scanned." % (lo, hi) if hi >= lo else "timing E1: no new frame is scanned."]
        if fired:
            calc.append("timing E1: event byte 1 on frame %d: UnitQueueEvent(kind 0, frame T + %d, a 1, b 0)." % (ev, kk))
        caps.append(dict(text="Step %d, game frame T + %d: position %d, frame %d%s." % (
            kk, kk, acc, acc >> 8, ", the event is queued" if fired else ""), calc=calc))
    # ---- the end
    header("THE END: T + %d" % end)
    timeline(end, queued | {end} | ({ev_t} if ev_t is not None else set()))
    animrow(None)
    k.text(20, 250, "LENGTH N = MAX(2, CEIL(256 X (%d - %d) / %d)) = %d" % (F, S, r, end), "txt", 2, True)
    k.text(20, 280, "%d SCAN STEPS, THE END ONE FRAME AFTER THE LAST" % steps, "dim", 2)
    if ev_t is not None:
        k.text(20, 310, "EVENT ON FRAME %d: T + %d" % (ev, ev_t), "blue", 2, True)
    else:
        k.text(20, 310, "NO FRAME EVENT FIRES", "dim", 2)
    k.caption("The mode ends at T + %d%s (timing E2)." % (
        end, ", with the event at T + %d" % ev_t if ev_t is not None else ""), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The mode ends at T + %d%s." % (end, ", the event at T + %d" % ev_t if ev_t is not None else ""),
        calc=["timing E2: n = max(2, ceil(256 (F - S) / r)) = max(2, ceil(%d / %d)) = %d." % ((F - S) << 8, r, end),
              "timing E1: queued = %s." % "; ".join(
                  ("kind %d at T + %d" % (e[0], e[1])) for e in q)]))
    return frames, caps, k.pal, (r, end, ev_t)


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--mode": "cast", "--stat": None, "--frames": "14", "--speed": "256", "--start": "0", "--event": "7",
            "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1 or opts["--mode"] not in MODES or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        mode = opts["--mode"]
        stat = int(opts["--stat"]) if opts["--stat"] is not None else (20 if mode == "cast" else 0)
        F, speed, S, ev = int(opts["--frames"]), int(opts["--speed"]), int(opts["--start"]), int(opts["--event"])
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (2 <= F <= 24 and 1 <= speed <= 1024 and 0 <= S < F and -1 <= ev < F and 0 <= stat <= 600):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    b, x, r = rate_of(mode, speed, stat)
    if r < 1 or (F - S) << 8 > 16 * r:
        print("the rate %d gives a schedule too long or empty for a frame set" % r, file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim",
                                        "timing-%s-%d-schematic" % (mode, stat))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _i = build(mode, stat, F, speed, S, ev, opts["--theme"])
    K.write_illustration(out, "timing", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "animation schedule animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
