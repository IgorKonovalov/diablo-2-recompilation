#!/usr/bin/env python3
"""Plan 0055 P1.1: the frame-window log volume (lines per frame), measured on kept logs and estimated for a window.

    python3 -I tools/frame_volume.py measure LOG ...   per log: logged lines (lines starting with an upper-case tag),
                                                       the frame span of its "fr" fields, lines per frame; then the
                                                       totals and the mean lines per session
    python3 -I tools/frame_volume.py events LOG ...    per log (plan 0050's anim logger): the slot-list dispatch lines
                                                       (PDS, MDS) and every-frame starts (EF) per frame of the span:
                                                       a lower bound on unit events per frame (that logger filters
                                                       kinds 0 and 1 at the slot-list call sites only)
    python3 -I tools/frame_volume.py estimate          the window estimate of plan 0055 P1.1 from the per-unit rates
                                                       below (stated inputs, not measurements)

The estimate's model: a frame logs 2 frame lines (GameTick entry and exit with the game seed), 2 lines per unit event
(entry and exit with the unit and game seeds), 1 line per client message applied, and the timer and pass lines
(1 each when a pass runs: frame mod 20, 12, 11; an act clock change; a room populated). Stdlib only. Read-only.
"""
import re
import sys

FR = re.compile(r'"fr":(\d+)')

# Per-scene inputs (events per frame), from the readings cited in docs/findings/frame/0001 § 6:
#   every-frame units: a moving player (walk/run every-frame event, anim/timing A2), every-frame monster modes
#   (MonStats2 *mv modes, anim/timing F), live missiles (one do-frame each, skills/0002 § 11);
#   slot events: a mode end per mode (about 8-20 frames a mode), the AI event every 10-25 frames idle or once per mode
#   plus aidel in combat (ai/0001 § 2, § 13).
SCENES = [
    # name, player events, monsters awake, share of them in an every-frame mode, slot events per monster per frame,
    # missiles alive, objects/items events per frame, messages per frame
    ("town (1 player, 8 NPCs)", 0.8, 8, 0.4, 0.12, 0.0, 0.1, 0.2),
    ("outdoor pack (1 player, 15 monsters)", 1.0, 15, 0.5, 0.17, 3.0, 0.2, 0.3),
    ("maze boss (1 player, boss + 10 minions)", 1.0, 11, 0.5, 0.20, 8.0, 0.2, 0.3),
]
TIMER_LINES = 1 / 20 + 1 / 12 + 1 / 11


def logged_lines(path):
    n, frs = 0, []
    with open(path, errors="replace") as f:
        for ln in f:
            if ln[:1].isupper() and ln[:1].isalpha():
                n += 1
                m = FR.search(ln)
                if m:
                    frs.append(int(m.group(1)))
    return n, frs


def cmd_measure(paths):
    tot_n = tot_f = 0
    for p in paths:
        n, frs = logged_lines(p)
        span = (max(frs) - min(frs) + 1) if frs else 0
        tot_n += n
        tot_f += span
        print("LOG %s lines=%d frames=%d lines_per_frame=%.2f" % (p.rsplit("/", 1)[-1], n, span, n / span if span else 0))
    k = len(paths)
    print("TOTAL logs=%d lines=%d frames=%d lines_per_frame=%.2f lines_per_session=%.0f"
          % (k, tot_n, tot_f, tot_n / tot_f if tot_f else 0, tot_n / k if k else 0))


def cmd_events(paths):
    for p in paths:
        cnt, frs = {"PDS": 0, "MDS": 0, "EF": 0}, []
        with open(p, errors="replace") as f:
            for ln in f:
                tag = ln.split(" ", 1)[0]
                m = FR.search(ln)
                if m:
                    frs.append(int(m.group(1)))
                if tag in cnt:
                    cnt[tag] += 1
        span = (max(frs) - min(frs) + 1) if frs else 0
        ev = sum(cnt.values())
        print("EVLOG %s PDS=%d MDS=%d EF=%d frames=%d events_per_frame=%.3f"
              % (p.rsplit("/", 1)[-1], cnt["PDS"], cnt["MDS"], cnt["EF"], span, ev / span if span else 0))


def cmd_estimate():
    print("scene events_per_frame lines_per_frame lines_per_250_frame_window")
    lo = hi = None
    for name, pl, mons, ef, slot, mis, oth, msg in SCENES:
        events = pl + mons * ef + mons * slot + mis + oth
        lines = 2 + 2 * events + msg + TIMER_LINES
        lo = lines if lo is None else min(lo, lines)
        hi = lines if hi is None else max(hi, lines)
        print("EST %s events=%.1f lines=%.1f window=%.0f" % (name, events, lines, 250 * lines))
    print("EST range lines_per_frame=%.1f..%.1f; 10 windows of 250 frames=%.0f..%.0f lines" % (lo, hi, 2500 * lo, 2500 * hi))


def main(argv):
    if not argv or argv[0] not in ("measure", "events", "estimate"):
        sys.exit(__doc__)
    if argv[0] == "measure":
        cmd_measure(argv[1:])
    elif argv[0] == "events":
        cmd_events(argv[1:])
    else:
        cmd_estimate()


if __name__ == "__main__":
    main(sys.argv[1:])
