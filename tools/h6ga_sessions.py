#!/usr/bin/env python3
"""Plan 0038 H6g rows 2 and 29, the corrected Ancients session (lane h6ga, harness slot 2): ExpGrantCapped at 0x0058C5C0
on a Normal level-25 character. Written on tools/harness_runner.py (plan 0056). Logger tools/gdb/h6g-quest.gdb
(tools/gdb/h6g.py: EG0, EGS, EGX and the altar lines AL0, ALS); checked by tools/sweep_h6g.py check.

Usage:
  python3 -I tools/h6ga_sessions.py list
  python3 -I tools/h6ga_sessions.py run --slot N --tag TAG --saves DIR --run RUN [--dev] SESSION [SESSION ...]

Sessions (the character is built by tools/d2s.py from tools/d2s_recipes/player-h6g-anc25.json, saved as <DIR>/H6gAnc25.d2s):
  anc80   the same route with the level-80 character of player-h6g-anc.json (<DIR>/H6gAnc.d2s): the cut does not bind.
  anc25   Act V waypoint 5,8 (level 118), explore to the summit door, level 120, the altar (object 546, --to-pdef 1089),
          then the three Ancients (classes 540-542); no town portal on level 120.
--dev writes dev- logs (the checker's glob does not match them). Nothing here feeds a model: the pilot decides clicks.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import harness_runner as hr  # noqa: E402

PY = hr.PY
LOGS = os.path.join(ROOT, "workspace", "logs", "h6g")
GDB = os.path.join(HERE, "gdb", "h6g-quest.gdb")
STEPS = os.path.join(HERE, "gdb", "enter-normal.steps")

# name: (save, map seed, [(kind, args, timeout)])   kinds: qs (tools/quest_sessions.py act), pilot, until
ROUTE = [("qs", ["towp2", "wp:5,8", "explore:40"], 400),
         ("pilot", ["farm", "--descend", "76", "--time", "1", "--descend-time", "150"], 200),
         ("pilot", ["objop", "--obj-cls", "546", "--to-pdef", "1089", "--obj-mem", "--times", "1", "--time", "90",
                    "--done-wait", "4", "--obj-near", "6"], 150),
         ("pilot", ["farm", "--boss-cls", "540,541,542", "--time", "240", "--nova-key", "F1", "--es-key", "F2",
                    "--es", "20", "--sweep"], 300),
         ("until", ["EGX", 1], 30)]
SESSIONS = {
    "anc25": ("H6gAnc25", 4314, ROUTE),     # level 25, the cut binds
    "anc80": ("H6gAnc", 4314, ROUTE),       # level 80 (player-h6g-anc.json), the grant uncut: the fixed amount shows
}


def run_one(name, slot, tag, saves, run, dev):
    save, seed, cmds = SESSIONS[name]
    stem = hr.new_stem(LOGS, ("dev-" if dev else "") + run, slot, seed, name)
    log = stem + ".log"
    shots = stem + "-shots"
    os.makedirs(shots, exist_ok=True)
    out = open(stem + ".pilot.txt", "a")
    hr.install(slot, tag, out=out)
    proc = hr.launch(slot, seed, log, gdb=GDB, steps=STEPS, after=1800,
                     install=(tag, [os.path.join(saves, save + ".d2s")]), out=out, stem=stem)
    try:
        r = hr.wait_ready(log, "PLR", 240, proc=proc, tick=lambda: hr.hide_window(slot))
        print("ready: %s" % r, flush=True)
        hr.mark(stem, name, "ready", log)
        if r != hr.READY:
            return False
        hr.mark(stem, name, "start", log)
        for kind, args, timeout in cmds:
            if kind == "qs":
                rc = hr.sh([*PY, hr.tool("quest_sessions.py"), "act", "--slot", str(slot), log] + args, timeout, out)
            elif kind == "pilot":
                rc = hr.sh([*PY, hr.tool("d2pilot.py"), args[0], log, "--slot", str(slot)] + args[1:] +
                           ["--shots", shots], timeout, out)
            else:
                rc = 0 if hr.wait_count(log, args[0], args[1], timeout, proc=proc) else 1
            print("  %s %s -> %s" % (kind, args[0], rc), flush=True)
        hr.mark(stem, name, "end", log)
    finally:
        hr.stop(slot, proc, out=out)
        out.close()
    return True


def main(argv):
    if not argv or argv[0] not in ("list", "run"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print(k, v[0], v[1], len(v[2]), "step(s)")
        return 0
    a, opt, names, dev, k = argv[1:], {}, [], False, 0
    while k < len(a):
        if a[k] in ("--slot", "--tag", "--saves", "--run"):
            opt[a[k][2:]] = a[k + 1]
            k += 2
        elif a[k] == "--dev":
            dev = True
            k += 1
        else:
            names.append(a[k])
            k += 1
    if not names or any(n not in SESSIONS for n in names) or set(opt) != {"slot", "tag", "saves", "run"}:
        print(__doc__)
        return 2
    for n in names:
        run_one(n, int(opt["slot"]), opt["tag"], os.path.abspath(opt["saves"]), opt["run"], dev)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
