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
    python3 -I tools/frame_volume.py estimate13        the re-estimate of plan 0055 P1.3 (frame/0003 § 9): every line
                                                       kind of the closed log design, the queue line at the stated
                                                       queue rates per run event (low, mid, high), MSG at 2 lines per
                                                       message, and the breakpoint stops per frame

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


# P1.3 (frame/0003 § 9): per scene, the inputs of SCENES plus the room inputs: frames with a room created (any act
# of the scene's), rooms created per such frame, active rooms in that act (each walked by NewRoomsUpdate: RU0/RU1
# per room), room releases per frame.
ROOMS13 = {
    "town (1 player, 8 NPCs)": (0.010, 2.5, 25, 0.004),
    "outdoor pack (1 player, 15 monsters)": (0.020, 2.5, 30, 0.008),
    "maze boss (1 player, boss + 10 minions)": (0.020, 2.5, 30, 0.008),
}
# Queue rates (records queued per run event), low / mid / high: an every-frame mode event queues only at a mode change
# (ef), a slot event (mode end, AI, regeneration, kind 6/11) queues its follow-ups (slot), a missile event, an object
# or item event, a client message (a skill or move request starts a mode).
QRATES = {"low": dict(ef=0.05, slot=1.0, mis=0.5, oth=0.5, msg=0.5),
          "mid": dict(ef=0.10, slot=1.5, mis=1.0, oth=1.0, msg=1.0),
          "high": dict(ef=0.20, slot=2.0, mis=1.5, oth=1.5, msg=2.0)}
# Breakpoint sites that stop whether or not they write a line, per frame: the 8 FP sites, ACL once per loaded act
# (1), EventQueueEveryFrame's entry for the forwarded frame -1 records (counted in the queue lines), the
# NewRoomsUpdate act loop head (5 per frame), the timer pass sites (3, conditional on the remainder: at most 3).
FIXED_STOPS = 8 + 1 + 5 + 3


def cmd_estimate13():
    print("scene rate ev_per_frame FT UE QE MSG RU RC RR TM lines_per_frame lines_per_window stops_per_frame")
    rows = {}
    for name, pl, mons, ef, slot, mis, oth, msg in SCENES:
        fc, per, act_rooms, rel = ROOMS13[name]
        ef_ev = mons * ef + 0.6 * pl          # the player's walk is an every-frame mode about 60 % of the time
        slot_ev = mons * slot + 0.4 * pl
        events = ef_ev + slot_ev + mis + oth
        for rate, q in QRATES.items():
            ft = 2.0
            ue = 2.0 * events
            qe = q["ef"] * ef_ev + q["slot"] * slot_ev + q["mis"] * mis + q["oth"] * oth + q["msg"] * msg
            ms = 2.0 * msg
            ru = 2.0 * fc * act_rooms
            rc = fc * per
            rr = rel
            tm = TIMER_LINES
            lines = ft + ue + qe + ms + ru + rc + rr + tm
            stops = lines + FIXED_STOPS
            rows[(name, rate)] = lines
            print("EST13 %s rate=%s events=%.1f FT=%.1f UE=%.1f QE=%.2f MSG=%.1f RU=%.2f RC=%.3f RR=%.3f TM=%.3f "
                  "lines=%.1f window=%.0f stops=%.1f" % (name, rate, events, ft, ue, qe, ms, ru, rc, rr, tm, lines,
                                                       250 * lines, stops))
    for rate in QRATES:
        v = [rows[(n[0], rate)] for n in SCENES]
        print("EST13 range rate=%s lines_per_frame=%.1f..%.1f window=%.0f..%.0f ten_windows=%.0f..%.0f "
              "three_window_session=%.0f..%.0f" % (rate, min(v), max(v), 250 * min(v), 250 * max(v), 2500 * min(v),
                                                   2500 * max(v), 750 * min(v), 750 * max(v)))
    print("EST13 p45 lines_per_frame=4.09 lines_per_session=17786 q2_trigger_session_lines=177860")


def main(argv):
    if not argv or argv[0] not in ("measure", "events", "estimate", "estimate13"):
        sys.exit(__doc__)
    if argv[0] == "measure":
        cmd_measure(argv[1:])
    elif argv[0] == "events":
        cmd_events(argv[1:])
    elif argv[0] == "estimate13":
        cmd_estimate13()
    else:
        cmd_estimate()


if __name__ == "__main__":
    main(sys.argv[1:])
