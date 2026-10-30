#!/usr/bin/env python3
"""Plan 0056 Phase 2 probe: several games in one game process (the menu return of harness_runner.next_case).

    python3 -I tools/probe0056.py --slot N --tag TAG --chars DIR --seed S --run RUN [--switches K] [--dev]

DIR holds UniqNova.d2s and ProbeB.d2s (tool-built, tools/d2s.py build). One launch on tools/gdb/probe-0056.gdb
(mon-special.gdb plus tools/gdb/probe-state.py) with UniqNova entering normal difficulty; then K menu returns that
install UniqNova / ProbeB alternately. Per game it writes marks (start, end), the game process's RSS, the seconds of the
switch, and at the end the log's LC0 (level seed), PST (g_HitClassCounter, g_PlayersOverride) and TINIT counts per
game. Output: workspace/logs/p56b/<RUN>-s<N>-<seed>-probe.log (+ .marks.tsv, .rss.tsv); --dev writes dev- names.
Stdlib only.
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import harness_runner as hr  # noqa: E402
import slots  # noqa: E402

LOGS = os.path.join(ROOT, "workspace", "logs", "p56b")


def rss_kb():
    """{process name: VmRSS kB} of game.exe, gdb and the wine servers (all of them, any slot): coarse."""
    r = {}
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            cmd = open("/proc/%s/cmdline" % pid, "rb").read().replace(b"\0", b" ").decode(errors="replace")
            name = "game" if "game.exe" in cmd and "wine" not in cmd.split()[0] else \
                "gdb" if cmd.startswith("gdb") or "/gdb " in cmd[:60] else None
            if name:
                for ln in open("/proc/%s/status" % pid):
                    if ln.startswith("VmRSS"):
                        r["%s:%s" % (name, pid)] = int(ln.split()[1])
        except OSError:
            pass
    return r


NOVA = ["--nova-key", "F1", "--es-key", "F2", "--es", "25", "--radius", "9", "--mana-col", "4", "--drink", "0.5",
        "--nova-hold", "1.6", "--max-res", "1000"]


def game_pid(log):
    for ln in open(log, errors="replace"):
        if ln.startswith("# game pid "):
            return int(ln.split()[3])
    return None


def cg(name, pid="self"):
    """memory.current / memory.peak (kB) of the cgroup of `pid` (the game's: d2run.py's --mem-max scope), or None."""
    try:
        d = "/sys/fs/cgroup" + open("/proc/%s/cgroup" % pid).read().split("::")[1].strip()
        return int(open(os.path.join(d, name)).read()) // 1024
    except (OSError, ValueError, IndexError):
        return None


def fight(slot, log, out, secs):
    """City of the Damned (the Act IV waypoint, tab 4 row 2), then a Nova sweep: monsters hit the player."""
    py = [*hr.PY, os.path.join(HERE, "d2pilot.py")]
    hr.sh(py + ["wp", log, "--slot", str(slot), "--wp-x", "715", "--wp-y", "58", "4", "2"], 90, out)
    hr.sh(py + ["farm", log, "--slot", str(slot), "--sweep", "--time", str(secs)] + NOVA, secs + 60, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", type=int, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--chars", required=True)
    ap.add_argument("--seed", type=int, default=4801)
    ap.add_argument("--run", required=True)
    ap.add_argument("--switches", type=int, default=3)
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--fight", default="", help="game numbers (comma list) in which the pilot fights for --fight-secs")
    ap.add_argument("--players", type=int, default=0, help="type /players N in game 0 (the state that carries over)")
    ap.add_argument("--fight-secs", type=int, default=40)
    ap.add_argument("--dwell", type=float, default=15.0, help="seconds in each game before the switch")
    a = ap.parse_args()
    if a.slot == 0:
        sys.exit("slot 0 is the owner's")
    os.makedirs(LOGS, exist_ok=True)
    stem = hr.new_stem(LOGS, ("dev-" if a.dev else "") + a.run, a.slot, a.seed, "probe")
    log, out = stem + ".log", open(stem + ".out.txt", "w")
    nova, probeb = os.path.join(a.chars, "UniqNova.d2s"), os.path.join(a.chars, "ProbeB.d2s")
    rss = open(stem + ".rss.tsv", "w")
    t00 = time.time()
    hr.install(a.slot, a.tag, out=out)
    drv = hr.launch(a.slot, a.seed, log, gdb="tools/gdb/probe-0056.gdb", steps="tools/gdb/enter-normal.steps",
                    after=1800, install=(a.tag, [nova]), out=out, stem=stem)
    hr.mark(stem, "g0", "start", log, "launch")
    try:
        r = hr.wait_ready(log, "PLR", 180, proc=drv, tick=lambda: hr.hide_window(a.slot))
        boot = round(time.time() - t00, 1)
        hr.mark(stem, "g0", "ready" if r == hr.READY else "fail", log, "%s boot=%s s" % (r, boot))
        print("ready: %s boot %s s" % (r, boot), flush=True)
        if r != hr.READY:
            return 1
        time.sleep(a.dwell)
        if a.players:
            hr.sh([*hr.PY, os.path.join(HERE, "d2pilot.py"), "players", log, "--slot", str(a.slot), str(a.players)],
                  60, out)
            time.sleep(2)
        if "0" in a.fight.split(","):
            fight(a.slot, log, out, a.fight_secs)
        rss.write("g0\tcg_cur=%s cg_peak=%s %s\n" % (cg("memory.current", game_pid(log)), cg("memory.peak", game_pid(log)), rss_kb()))
        hr.mark(stem, "g0", "end", log)
        chars = [probeb, nova]
        for k in range(1, a.switches + 1):
            f = chars[(k - 1) % 2]
            res = hr.next_case(a.slot, log, [f], diff="normal", out=out, stem=stem, case="g%d" % k)
            hr.mark(stem, "g%d" % k, "ready" if res["ok"] else "fail", log, "switch %.1f s file %s" % (
                res["secs"], os.path.basename(f)))
            print("g%d: %s" % (k, res), flush=True)
            if not res["ok"]:
                break
            time.sleep(a.dwell)
            if str(k) in a.fight.split(","):
                fight(a.slot, log, out, a.fight_secs)
            rss.write("g%d\tcg_cur=%s cg_peak=%s %s\n" % (k, cg("memory.current", game_pid(log)), cg("memory.peak", game_pid(log)), rss_kb()))
            rss.flush()
            hr.mark(stem, "g%d" % k, "end", log)
        print("total wall %.0f s" % (time.time() - t00))
    finally:
        rss.close()
        hr.stop(a.slot, drv, out=out)
        print("log", log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
