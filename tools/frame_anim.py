"""Animate one server tick pass by pass (docs/specs/sim/frame.md sections B, C, D and J): the message drain before the
tick, the counter going up, the twenty ranks of GameTick in order, the ten walks over the unit event lists, the three
passes that run only on some frames, and for each pass which seeds it can draw on. Schematic only (ADR-0036): boxes,
text and bars in our own palette.

Usage:
  python3 -I tools/frame_anim.py <root> [--frame N] [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); this tool reads no game file and ignores
it. --frame N: the frame counter after GameTick's increment (default 1320, a multiple of 20, 12 and 11, so every
periodic pass runs; 1 to 100000). --theme: dark or light palette values. --schematic is accepted for the export builder
and changes nothing. DIR defaults to workspace/render/anim/frame-<N>-schematic/ and must stay under workspace/.
Outputs: frame-NNN.png, frame.gif, index.html, steps.json, schematic.json (ADR-0036).

There is no model of the tick in tools/ to drive: the frames draw the spec's pass list (sim/frame B1, D1) as a fixed
sequence, the ranks, names and orders written in this file from those two listings, and the draws and seeds each pass
can reach from the J table. No game log is read (a generator never reads one for the export). The only computed values are
the three modulo tests of ranks 17 to 19 and the sweep's, on the frame number given. A test compares the names and order
with the spec's listings. Not shown: what an event does (other pages), the queue (E, F), rooms (H), the periodic calls'
contents (I) and the frame windows (K). Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 436

# the spec's pass list: (rank, name, short label, period or None, what it draws, seeds, frame.md anchor, how sure)
PASSES = (
    (1, "ActsClockPass", "ACT CLOCKS", None, "NONE OF ITS OWN; A CLOCK CHANGE CAN REACH A SKILL CHANGE THAT DRAWS",
     "THE SKILL'S, BY ITS SPEC", "G1, J", "none of its own is confirmed"),
    (2, "GameFpsStats", "FPS STATS", None, "NONE", "NONE", "G2, J", "confirmed"),
    (3, "NewRoomsUpdate", "NEW ROOMS", None, "THE WANDERER TICK, THE POPULATION, THE RESTORE OF SAVED ITEMS",
     "THE ROOM'S OWN, A NEIGHBOUR'S, THE GAME'S, THE LEVEL'S, THE OBJECT REGION'S", "H2, J", "confirmed"),
    (14, "ClientsRoomSync", "ROOM SYNC", None, "ROOM ACTIVATIONS, LEVEL BUILDS, PRESET ROLLS",
     "THE ROOM'S OWN, THE LEVEL'S; NOT THE GAME SEED BY DIRECT REACH", "H3, J", "confirmed"),
    (15, "ActUnitsFrameReset", "UNIT RESET", None, "THE FREE OF AN INVENTORY ITEM WITH ITEM FLAG 1", "THE FREE'S",
     "G3, J", "the item-flag condition is inferred"),
    (16, "ActsRoomRemovalsClear", "REMOVALS", None, "NONE", "NONE", "G4, J", "confirmed"),
    (17, "QUESTS_TimersRun", "QUEST TIMERS", 20, "SIX QUEST CALLBACKS", "THE GAME'S, THE QUEST'S, THE LEVEL'S", "I1, J",
     "the seeds are inferred"),
    (18, "RoomsDeactivate", "ROOM RELEASE", 12, "THE SAVE TEST OF INACTIVE UNITS, THE FREE OF AN ACTIVE ROOM", "SEE THE LIFECYCLE'S SAVE RULE",
     "I2, J", "confirmed"),
    (19, "ActLevelsUnloadTick", "LEVEL UNLOAD", 11, "THE BUILD OF A LEVEL", "THAT LEVEL'S", "I3, J", "the seed is inferred"),
    (20, "ExpirySweepTick", "EXPIRY SWEEP", 1, "THE FREE OF AN EXPIRED ITEM; WORKS ONLY WHEN FRAME % 1500 = 0",
     "THE FREE'S", "I4, J", "confirmed"),
)
# the ten walks of D1, ranks 4 to 13: (rank, runner, unit type, mode)
WALKS = ((4, "MissileEventsRun", "MISSILES", 0), (5, "MissileEventsRun", "MISSILES", 1),
         (6, "PlayerEventsRun", "PLAYERS", 0), (7, "PlayerEventsRun", "PLAYERS", 1),
         (8, "MonEventsRun", "MONSTERS", 0), (9, "MonEventsRun", "MONSTERS", 1),
         (10, "ObjEventsRun", "OBJECTS", 0), (11, "ObjEventsRun", "OBJECTS", 1),
         (12, "ItemEventsRun", "ITEMS", 0), (13, "ItemEventsRun", "ITEMS", 1))
HELP = """<li>Left: the passes of one tick in the order the server runs them. The drain comes first, between ticks; the tick raises the frame counter, then runs ranks 1 to 20.</li>
<li>Right: what the current pass is and which seeds it can draw on, as the server frame page states them. A frame in which a pass has nothing to do leaves its seeds as they were.</li>
<li>Ranks 17 to 19 run on frames that divide by 20, 12 and 11; the sweep of rank 20 runs every frame but works only when the counter divides by 1500.</li>
<li>The pass list is drawn from the spec, not computed by a model of the tick; the only computed values are the divisibility tests on the frame number given.</li>"""

ROWS = [("21", "DRAIN", "SrvDrainMessages")] + [("%d" % p[0], p[2], p[1]) for p in PASSES[:3]] + \
       [("4-13", "TEN WALKS", "GameRunUnitEvents")] + [("%d" % p[0], p[2], p[1]) for p in PASSES[3:]]


def build(N, theme):
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    ROWY = 44
    RH = 29

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def railway(cur, done, runs):
        """The left list. cur: the row key being shown; done: keys passed; runs: {key: bool} for periodic rows."""
        for i, (rank, lab, fn) in enumerate(ROWS):
            y = ROWY + i * RH
            key = rank
            is_cur = key == cur
            skipped = key in runs and not runs[key]
            fill = "cur" if is_cur else "panel"
            edge = "acc" if is_cur else ("grey" if key in done else "dim")
            k.rect(20, y, 290, RH - 3, fill)
            k.outline(20, y, 290, RH - 3, edge, 2 if is_cur else 1)
            k.text(28, y + 7, rank, "acc" if is_cur else "dim", 2, True)
            k.text(28 + 66, y + 7, lab, "dim" if skipped else "txt", 2, is_cur)
            if skipped and (key in done or is_cur):
                k.text(300 - K.text_w("SKIP", 2), y + 7, "SKIP", "dim", 2)
            elif key in done and not is_cur:
                k.text(300 - K.text_w("DONE", 2), y + 7, "DONE", "good", 2)

    def right_text(title, lines):
        k.rect(330, 44, 610, 340, "panel")
        k.outline(330, 44, 610, 340, "dim")
        k.text(344, 56, title, "acc", 2, True)
        y = 92
        for lab, val, col in lines:
            k.text(344, y, lab, "dim", 2)
            for ln in anim_common.wrap(val, 46):
                y += 26
                k.text(344, y, ln, col, 2, col != "dim")
            y += 38

    runs = {"17": N % 20 == 0, "18": N % 12 == 0, "19": N % 11 == 0}
    done = set()

    # ---- the start
    header("ONE SERVER TICK, THE COUNTER AT %d" % N)
    railway(None, done, runs)
    k.rect(330, 44, 610, 340, "panel")
    k.outline(330, 44, 610, 340, "dim")
    k.text(344, 60, "THE HOST LOOP, ONCE PER 40 MS", "acc", 2, True)
    k.text(344, 100, "1. DRAIN THE MESSAGES (QUEUES 0, 1, 2)", "txt", 2)
    k.text(344, 130, "2. EACH LIVE GAME: TICK, THEN FLUSH", "txt", 2)
    k.text(344, 170, "THE TICK FIRST RAISES THE COUNTER: %d -> %d" % (N - 1, N), "txt", 2, True)
    k.text(344, 200, "THEN RUNS RANKS 1 TO 20 IN FIXED ORDER", "txt", 2)
    k.text(344, 240, "RANK 21 IS EVERYTHING BETWEEN TWO TICKS,", "dim", 2)
    k.text(344, 266, "THE DRAIN FIRST OF ALL", "dim", 2)
    k.caption("One tick at counter %d: the drain applies the messages between ticks; the tick raises the counter and runs "
              "ranks 1 to 20 in order (frame B)." % N, CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="One server tick at counter %d: the drain, then the counter goes up and ranks 1 to 20 run in order." % N,
        calc=["frame.md B1: GameTick raises game.frame to %d before its first pass; the passes run in rank order." % N,
              "frame.md B1: rank 21 is everything between tick N and tick N + 1, the drain first of all.",
              "frame.md: this illustration draws the spec's pass list; it is not computed by a model of the tick."]))
    # ---- the drain
    header("RANK 21: THE DRAIN, BETWEEN TWO TICKS")
    railway("21", done, runs)
    right_text("SrvDrainMessages", [
        ("WHAT IT DOES", "POPS EACH QUEUE IN ARRIVAL ORDER: SYSTEM MESSAGES, IN-GAME PACKETS, HOST CONTROL", "txt"),
        ("WHEN", "BETWEEN FRAMES, NEVER INSIDE A TICK", "txt"),
        ("SEEDS", "AS EACH PACKET HANDLER'S SPEC NAMES THEM", "txt")])
    k.caption("The drain: queues 0, 1, 2 in order, each in arrival order. A packet handled after tick N takes effect "
              "in tick N + 1's state (frame C).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The drain runs between ticks: the three queues in order, packets applied before the next tick.",
        calc=["frame.md C1: queue 0 (system), queue 1 (in-game packets of every client), queue 2 (host control), each FIFO.",
              "frame.md C4: messages are applied between frames, never inside GameTick; the handlers' draws are each subsystem's spec.",
              "frame.md J: rank 21's seeds are as each handler's spec names them."]))
    done.add("21")
    # ---- ranks 1-3, then the walks, then the rest
    order = [p for p in PASSES]
    seq = []
    for p in order:
        if p[0] == 14:
            seq.append(("walks", None))
        seq.append(("pass", p))
    for kind, p in seq:
        if kind == "walks":
            for ui in range(0, 10, 2):
                a, b_ = WALKS[ui], WALKS[ui + 1]
                header("RANKS %d AND %d: %s" % (a[0], b_[0], a[2]))
                railway("4-13", done, runs)
                k.rect(330, 44, 610, 340, "panel")
                k.outline(330, 44, 610, 340, "dim")
                k.text(344, 56, "GameRunUnitEvents: THE TEN WALKS", "acc", 2, True)
                for j, (rank, runner, ut, mode) in enumerate(WALKS):
                    col, row = j // 5, j % 5
                    x, y = 344 + col * 290, 92 + row * 46
                    cur = j in (ui, ui + 1)
                    was = j < ui
                    k.box(x, y, 276, 40, [("%d %s %s" % (rank, ut, "EVERY FRAME" if mode == 0 else "SLOT"), "txt")],
                          "cur" if cur else "panel", "acc" if cur else ("grey" if was else "dim"), "txt", 2)
                k.text(344, 330, "SLOT = FRAME %% 64 = %d" % (N % 64), "txt", 2, True)
                k.text(344, 356, "SEEDS: THE UNIT'S, ANOTHER UNIT'S, GAME, LOCAL", "dim", 2)
                k.caption("Ranks %d and %d: the %s' every-frame events, then the events in this frame's slot. The slot is "
                          "the counter mod 64 = %d (frame D1)." % (a[0], b_[0], a[2].lower(), N % 64), CAP_Y, 76)
                frames.append(k.done())
                caps.append(dict(
                    text="Ranks %d and %d: the %s' every-frame events, then the slot events of this frame." % (
                        a[0], b_[0], a[2].lower()),
                    calc=["frame.md D1: rank %d %s(mode 0, ctl.everyHead); rank %d %s(mode 1, ctl.slotHead[curSlot])." % (
                              a[0], a[1], b_[0], b_[1]),
                          "frame.md D1: curSlot = game.frame %% 64 = %d %% 64 = %d." % (N, N % 64),
                          "frame.md J: the walks have no draw of their own; each event's function and its spec name the seeds."]))
            done.add("4-13")
            continue
        rank, name, lab, period, draws, seeds, anchor, sure = p
        key = "%d" % rank
        header("RANK %d: %s" % (rank, lab))
        railway(key, done, runs)
        lines = []
        if period and period > 1:
            runs_now = N % period == 0
            lines.append(("RUNS WHEN", "FRAME %% %d = 0:  %d %% %d = %d, SO IT %s" % (
                period, N, period, N % period, "RUNS" if runs_now else "DOES NOT RUN THIS FRAME"),
                          "good" if runs_now else "dim"))
        elif period == 1:
            lines.append(("RUNS WHEN", "EVERY FRAME; IT WORKS ONLY WHEN FRAME %% 1500 = 0:  %d %% 1500 = %d, SO %s" % (
                N, N % 1500, "IT WORKS" if N % 1500 == 0 else "IT DOES NOTHING THIS FRAME"),
                          "good" if N % 1500 == 0 else "dim"))
        else:
            lines.append(("RUNS WHEN", "EVERY FRAME", "txt"))
        lines += [("DRAWS", draws, "txt"), ("SEEDS", seeds, "txt")]
        right_text(name, lines)
        if period and period > 1 and N % period != 0:
            cap = "Rank %d, %s: it runs when the counter divides by %d; %d does not, so it is skipped this tick (frame B1)." % (
                rank, name, period, N)
        else:
            cap = "Rank %d, %s. Its draws: %s; the seeds are listed beside (frame %s)." % (rank, name, draws.lower(), anchor)
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        calc = ["frame.md B1: rank %d %s%s." % (rank, name, "" if not period or period == 1 else
                                                  " runs when frame %% %d = 0 (%d %% %d = %d)" % (period, N, period, N % period))]
        if period == 1:
            calc.append("frame.md B1: every frame, but it works only when frame %% 1500 = 0 (%d %% 1500 = %d)." % (N, N % 1500))
        calc.append("frame.md J: draws: %s; seeds: %s (%s)." % (draws.lower(), seeds.lower(), sure))
        caps.append(dict(text="Rank %d, %s%s." % (rank, name, "" if not period or period == 1 or N % period == 0
                                                  else ", skipped at counter %d" % N), calc=calc))
        done.add(key)
    # ---- the end
    header("THE TICK IS DONE: COUNTER %d" % N)
    railway(None, done, runs)
    k.rect(330, 44, 610, 340, "panel")
    k.outline(330, 44, 610, 340, "dim")
    k.text(344, 60, "THEN THE FLUSH, AND THE NEXT PASS OF THE HOST LOOP", "acc", 2, True)
    k.text(344, 100, "NEXT: DRAIN, THEN A TICK AT COUNTER %d" % (N + 1), "txt", 2, True)
    k.text(344, 140, "RUNNING THIS FRAME: %s" % (", ".join("%d" % p[0] for p in PASSES if p[3] is None or N % p[3] == 0 or p[3] == 1)), "dim", 2)
    k.text(344, 170, "(AND THE WALKS 4 TO 13)", "dim", 2)
    k.text(344, 200, "SKIPPED THIS FRAME: %s" % (", ".join("%d" % p[0] for p in PASSES if p[3] and p[3] > 1 and N % p[3]) or "NONE"),
           "dim", 2)
    k.caption("The order inside a tick is fixed, so a draw on a seed two passes share always comes from the earlier "
              "pass first (frame B, J).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The tick is done; the next drain and the tick at counter %d follow." % (N + 1),
        calc=["frame.md B1: the ranks that ran at counter %d: %s, and the walks 4 to 13." % (
                  N, ", ".join("%d" % p[0] for p in PASSES if p[3] is None or p[3] == 1 or N % p[3] == 0)),
              "frame.md J: the passes run in one order, so which pass draws first on a shared seed does not vary."]))
    return frames, caps, k.pal


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--frame": "1320", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1 or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        N = int(opts["--frame"])
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not 1 <= N <= 100000:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "frame-%d-schematic" % N)
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal = build(N, opts["--theme"])
    K.write_illustration(out, "frame", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "server tick animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
