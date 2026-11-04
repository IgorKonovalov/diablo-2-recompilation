"""Scripted harness sessions for plan 0055 Phase 2b (frame windows), on the runner library (tools/harness_runner.py):
one fresh single-player game process per scene, logged by tools/gdb/frame.gdb, driven by tools/d2pilot.py, checked by
`python3 -I tools/frame.py window`. Nothing here launches a game unless asked (`run --launch`, ADR-0022).

Usage (no game is started by `list`, `plan`, `gate`, or by `run` without --launch):
  python3 -I tools/frame_sessions.py list
  python3 -I tools/frame_sessions.py plan SCENE [--long] [--wp-x X --wp-y Y]     # print the staged session (also `run --dry`)
  python3 -I tools/frame_sessions.py build --saves DIR [--recipe framenova]       # the character (tools/d2s.py build)
  python3 -I tools/frame_sessions.py run --slot N --tag TAG --saves DIR --run RUN [--dry] [--launch] [--dev] SCENE ...
  python3 -I tools/frame_sessions.py gate LOG                                     # the pilot gate on a finished log

The pilot, the harness lane's first command (the Act I town, one fresh process, the first window only; it stops there):
  python3 -I tools/frame_sessions.py run --slot N --tag p55 --saves SAVES --run YYYY-MM-DD-frame --pilot-only --launch town

A session is one scene in one fresh process (harness-play.md § Fresh process, rule 3: `g_HitClassCounter` is process
state). The runner opens a window by appending `open LEN SCENE [cover=M]` to the session's control file (FRAME_CTL, read
by the logger at each FT0) and waits for the window's `WEND`. After the FIRST window of a scene (it is a pilot, plan 0055
Phase 2b) the runner runs the gate: (a) whole and (b) unmoved by tools/frame_window.py, (c) WEND ok, and the measured
lines per frame against three times the scene's estimate13 mid (town 47.6, pack 123.9, maze 152.7); a failure or an
excess stops the session there, for the architect. The player uses Teleport (hop, do 27) and Nova (do 22) through
tools/d2pilot.py and walks; no other skill is cast (the catalogue's rows for them are `docs/specs/skills/catalogue.md`;
the harness lane confirms both are in the reviewed tier before the batch). Single player: one game in the process, the
steps files of tools/gdb/enter-*.steps. Nothing here feeds a model: the pilot only decides where to click.

What cannot be settled until a game runs (named, not guessed): the Act I town's waypoint screen position (`--wp-x/--wp-y`;
d2pilot's defaults 712, 62 are another town's) and whether `wp --wp-find` works without the objects logger; the route
from the Rogue Encampment to Blood Moor (`explore` from the town is the stage, its exit not tried); the LvlWarp row of the
Den of Evil entrance (rows 0-3 of lvlwarp.txt are the four Blood Moor cave warps; `--descend-to 8` takes the one that
leads to the Den); whether Nova reaches Corpsefire's pack in the time given; the cost of the logger's breakpoint stops
(`frames per wall second` is the pilot's measurement, the 25 frames a second of the stock game is the best case); that
the character survives (SpecNova is the owner-reviewed recipe, its level against the monsters of the pack is not
measured here).
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ai_sessions as ais  # noqa: E402
import frame_volume  # noqa: E402
import frame_window as fw  # noqa: E402
import harness_runner as hr  # noqa: E402

LOGS = os.path.join(ROOT, "workspace", "logs", "frame")
GDB = "tools/gdb/frame.gdb"
STEPS = {"normal": "tools/gdb/enter-normal.steps"}
SEED0 = 5501
CAP_SECS = 40 * 60
FPS = 25.0
NOVA = ["--nova-key", "F2", "--radius", "9", "--mana-col", "4", "--drink", "0.5", "--nova-hold", "1.6", "--max-res", "1000"]
LEN = 250
WP_AT = "4884,5629"             # the Rogue Encampment's waypoint (OU0 of an objects log, smoke session; the start is fixed)
VIEW = ["--view-h", "0"]        # the game frame's rows are measured: the harness display here shows all 600


def window(scene, cover=0, what="", n=LEN):
    return ("window", scene, n, cover, what)


def scenes(wp_x=None, wp_y=None, long=False):
    """scene -> dict(diff, est, text, steps). A step: ("settle", s) | ("window", scene, len, cover, what) |
    ("pilot", argv, timeout) | ("bg", argv, timeout) | ("join",) | ("level", lid0) wait for a level other than lid0 |
    ("gate",) the pilot gate after the first window."""
    wp = (["--wp-x", str(wp_x)] if wp_x is not None else []) + (["--wp-y", str(wp_y)] if wp_y is not None else [])
    town = [("settle", 20), window("town", what="pilot: the player stands, the NPCs wander"), ("gate",),
            ("bg", ["hop", "--walk", "--hop-times", "12", "8", "0"], 40),
            window("town", what="the player walks in town (12 clicks of 8 sub-tiles, alternating; Teleport does not cast in town)"), ("join",),
            window("town", cover=1500, what="a frame = 0 (mod 1500) in the middle: the expiry sweep")]
    if long:
        town.append(window("town", cover=8192, what="a frame = 0 (mod 8192): SaveGameClients as a boundary oracle"))
    pack_far = ["farm", "--sweep", "--time", "400"] + NOVA
    pack = [("settle", 20), ("pilot", ["wp", "1", "2", "--wp-at", WP_AT], 150), ("settle", 4), ("bg", pack_far, 480),
            ("near", 22, 3, 240),
            window("pack", what="pilot: Cold Plains, the pack in range, Nova"), ("gate",),
            ("near", 22, 2, 150), window("pack", what="Nova and teleport hops, rooms activating"),
            ("near", 22, 1, 150), window("pack", cover=1500, what="mod 1500"),
            ("join",)]
    maze_go = ["farm", "--sweep", "--descend", "0,1,2,3", "--descend-to", "8", "--time", "420"] + NOVA + wp
    maze = [("settle", 20), ("pilot", ["explore", "--hops", "60", "--nova", "2"], 300), ("level", None),
            ("bg", maze_go, 500), ("level", None), ("settle", 6),
            window("maze", what="pilot: Den of Evil with Corpsefire (the first window of the scene)"), ("gate",),
            window("maze", what="the pack and Corpsefire"), window("maze", cover=1500, what="mod 1500"), ("join",)]
    return {
        "town": dict(diff="normal", est="town (1 player, 8 NPCs)", text="Act I town (Rogue Encampment)", steps=town),
        "pack": dict(diff="normal", est="outdoor pack (1 player, 15 monsters)", text="Cold Plains with a pack",
                     steps=pack),
        "maze": dict(diff="normal", est="maze boss (1 player, boss + 10 minions)", text="Den of Evil with Corpsefire",
                     steps=maze),
    }


def describe(step):
    k = step[0]
    if k == "window":
        return "window %s len=%d%s  # %s" % (step[1], step[2], " cover=%d" % step[3] if step[3] else "", step[4])
    if k in ("pilot", "bg"):
        return "%s d2pilot %s  (timeout %ds)" % ("run" if k == "pilot" else "start in background", " ".join(step[1]), step[2])
    if k == "settle":
        return "wait %ds" % step[1]
    if k == "near":
        return "wait until %d live monsters are within %d sub-tiles of the player (MON line), at most %d s" % (
            step[2], step[1], step[3])
    if k == "level":
        return "wait for the player to leave the level it is in (PLR lid changes)"
    if k == "join":
        return "wait for the background pilot command"
    return "pilot gate: tools/frame.py window --pilot on the log so far (stop on failure or above 3x estimate13)"


def plan_text(name, opts):
    sc = scenes(**opts)[name]
    est = frame_volume.estimate13_rows()[(sc["est"], "mid")]
    out = ["SCENE %s: %s, difficulty %s, one fresh process, estimate13 mid %.1f lines and %.1f stops per frame (stop above %.1f lines)"
           % (name, sc["text"], sc["diff"], est["lines"], est["stops"], 3 * est["lines"])]
    for i, s in enumerate(sc["steps"], 1):
        out.append("  %2d. %s" % (i, describe(s)))
    return "\n".join(out)


def gate(log, scene=None, out=None):
    """The pilot gate on the first window of a log: -> (ok, text). Fails on (a), (b), (c) or lines per frame above three
    times the scene's estimate13 mid."""
    buf = io.StringIO()
    rc = fw.run([log], pilot=True, out=buf)
    text = buf.getvalue()
    ok = rc == 0
    wins, _o = fw.parse_log(log)
    if wins:
        w = wins[0]
        est = frame_volume.estimate13_rows().get((scenes()[scene or w["scene"]]["est"], "mid"))
        s = fw.stats(w, fw.check_chain(w))
        if est and s["n"] and s["lines"] / s["n"] > 3 * est["lines"]:
            ok = False
            text += "GATE lines per frame %.1f above 3 x %.1f = %.1f: stop for the architect\n" % (
                s["lines"] / s["n"], est["lines"], 3 * est["lines"])
    return ok, text


def monsters_near(log, r, tail=400000):
    """The monsters within r sub-tiles of the player in the last MON line of the log's tail (alive: hit points above 0,
    mode not 0 or 12): the count. The pilot's MON line is around the last PLR position (tools/gdb/pilot.py)."""
    try:
        with open(log, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - tail))
            lines = f.read().decode("latin1").splitlines()
    except OSError:
        return 0
    for ln in reversed(lines):
        if ln.startswith("MON "):
            try:
                o = json.loads(ln[4:])
            except ValueError:
                continue
            return sum(1 for m in o.get("m", []) if (m.get("hp") or 0) > 0 and m.get("mode") not in (0, 12)
                       and ((m["x"] - o["x"]) ** 2 + (m["y"] - o["y"]) ** 2) ** 0.5 <= r)
    return 0


class Session:
    def __init__(self, slot, tag, saves, run_id, dev, pilot_only):
        self.slot, self.tag, self.saves, self.dev, self.pilot_only = slot, tag, os.path.abspath(saves), dev, pilot_only
        self.runname = ("dev-" if dev else "") + run_id
        os.makedirs(LOGS, exist_ok=True)
        self.out = open(os.path.join(LOGS, "%s-s%d.pilot.txt" % (self.runname, slot)), "a")
        self.shots = os.path.join("workspace", "logs", "frame", "%s-s%d-shots" % (self.runname, slot))
        os.makedirs(os.path.join(ROOT, self.shots), exist_ok=True)
        self.drv = self.stem = self.log = self.ctl = None
        self.bg = None
        self.nwin = 0
        self.t0 = 0.0

    def py(self, argv, timeout):
        a = [*hr.PY, os.path.join(HERE, "d2pilot.py"), argv[0], self.log, "--slot", str(self.slot)] + argv[1:] + VIEW + [
            "--shots", self.shots]
        return hr.sh(a, timeout, self.out)

    def launch(self, name, sc, seed, save):
        self.stem = hr.new_stem(LOGS, self.runname, self.slot, seed, name)
        self.log = self.stem + ".log"
        self.ctl = self.stem + ".ctl"
        open(self.ctl, "w").close()
        os.environ["FRAME_CTL"] = self.ctl            # inherited by d2run.py and with it by gdb (tools/gdb/frame.py)
        hr.install(self.slot, self.tag, out=self.out)
        self.drv = hr.launch(self.slot, seed, self.log, gdb=GDB, steps=STEPS[sc["diff"]], after=3000,
                             install=(self.tag, [save]), out=self.out, stem=self.stem)
        hr.mark(self.stem, name, "start", self.log, "launch seed=%d" % seed)
        r = hr.wait_ready(self.log, "Frame logger armed", 180, proc=self.drv, tick=lambda: hr.hide_window(self.slot))
        ok = r == hr.READY and hr.wait_count(self.log, "PLR", 1, 180, self.drv)
        self.t0 = time.time()
        return bool(ok)

    def open_window(self, step):
        _k, scene, n, cover, _what = step
        with open(self.ctl, "a") as f:
            f.write("open %d %s%s\n" % (n, scene, " cover=%d" % cover if cover else ""))
        self.nwin += 1
        wait = 120 + n / FPS * 40 + (cover / FPS * 3 if cover else 0)
        return hr.wait_count(self.log, "WEND", self.nwin, wait, self.drv)

    def run_scene(self, name, sc):
        seed = SEED0     # one map seed: the town waypoint (WP_AT) is where this seed puts it; another seed moves the town
        save = os.path.join(self.saves, "SpecNova.d2s")
        if not self.launch(name, sc, seed, save):
            hr.mark(self.stem, name, "fail", self.log, "no PLR")
            return "failed", "no PLR"
        hr.mark(self.stem, name, "ready", self.log)
        lid0 = ais.level_of(self.log)
        if lid0 != 1:       # the Rogue Encampment: smoke session 1 found the character in Act IV (recipe difficulty byte 131)
            hr.mark(self.stem, name, "fail", self.log, "level %s, not the Act I town" % lid0)
            return "failed", "the session starts in level %s, not the Act I town (1)" % lid0
        for step in sc["steps"]:
            k = step[0]
            if k == "settle":
                time.sleep(step[1])
            elif k == "level":
                t = time.time()
                while ais.level_of(self.log) == lid0 and time.time() - t < 300 and self.drv.poll() is None:
                    time.sleep(1)
                if ais.level_of(self.log) == lid0:
                    return "failed", "the player never left level %s" % lid0
                lid0 = ais.level_of(self.log)
            elif k == "pilot":
                if self.py(step[1], step[2]) is None:
                    return "failed", "pilot timeout"
            elif k == "bg":
                a = [*hr.PY, os.path.join(HERE, "d2pilot.py"), step[1][0], self.log, "--slot", str(self.slot)] + step[1][1:] + VIEW + [
                    "--shots", self.shots]
                self.bg = hr.detach(a, os.path.join(LOGS, "%s-s%d.bg.txt" % (self.runname, self.slot)))
            elif k == "near":
                t = time.time()
                while monsters_near(self.log, step[1]) < step[2] and time.time() - t < step[3] and self.drv.poll() is None:
                    time.sleep(0.4)
                got = monsters_near(self.log, step[1])
                self.out.write("near: %d monsters within %d after %.1f s\n" % (got, step[1], time.time() - t))
                if got < step[2]:
                    return "failed", "no pack within %d sub-tiles in %d s" % (step[1], step[3])
            elif k == "join":
                time.sleep(2)
            elif k == "window":
                if not self.open_window(step):
                    return "failed", "window %d did not complete" % self.nwin
            elif k == "gate":
                ok, text = gate(self.log, name)
                self.out.write(text)
                sys.stdout.write(text)
                if not ok:
                    return "failed", "the pilot gate failed (stop for the architect)"
                if self.pilot_only:
                    return "kept", "pilot only"
        return "kept", "%d windows, wall %.0f s" % (self.nwin, time.time() - self.t0)

    def close(self, why):
        if self.drv is not None:
            hr.mark(self.stem, "-", "end", self.log, why)
            hr.stop(self.slot, self.drv, out=self.out)
            self.drv = None


def run(a):
    sc_all = scenes(a.wp_x, a.wp_y, a.long)
    for n in a.scenes:
        if n not in sc_all:
            sys.exit("unknown scene %r (town, pack, maze)" % n)
        print(plan_text(n, dict(wp_x=a.wp_x, wp_y=a.wp_y, long=a.long)))
    if a.dry or not a.launch:
        print("not launching (%s)" % ("--dry" if a.dry else "pass --launch to start the game"))
        return 0
    if a.slot not in (1, 2):
        sys.exit("the slot is given in the lane's prompt: 1 or 2")
    results = []
    for n in a.scenes:                               # a fresh process per scene: each Session.run_scene launches
        s = Session(a.slot, a.tag, a.saves, a.run, a.dev, a.pilot_only)
        try:
            results.append((n,) + s.run_scene(n, sc_all[n]))
        finally:
            s.close("scene %s end" % n)
            s.out.close()
        if results[-1][1] != "kept":
            break
    for r in results:
        print("%s %s %s" % r)
    return 0 if all(r[1] == "kept" for r in results) else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list")
    for name in ("plan", "run"):
        p = sub.add_parser(name)
        p.add_argument("--long", action="store_true", help="add the frame = 0 (mod 8192) window to the town session")
        p.add_argument("--wp-x", type=int)
        p.add_argument("--wp-y", type=int)
        if name == "plan":
            p.add_argument("scenes", nargs="+")
        else:
            p.add_argument("--slot", type=int, required=True)
            p.add_argument("--tag", required=True)
            p.add_argument("--saves", required=True)
            p.add_argument("--run", required=True)
            p.add_argument("--dev", action="store_true")
            p.add_argument("--dry", action="store_true")
            p.add_argument("--launch", action="store_true", help="start the game (without it the plan is printed)")
            p.add_argument("--pilot-only", action="store_true", help="stop after the first window's gate")
            p.add_argument("scenes", nargs="+")
    p = sub.add_parser("build")
    p.add_argument("--saves", required=True)
    p.add_argument("--recipe", default="framenova")
    p = sub.add_parser("gate")
    p.add_argument("log")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for k, v in scenes().items():
            print("%-5s %s (%d steps)" % (k, v["text"], len(v["steps"])))
        return 0
    if a.cmd == "plan":
        for n in a.scenes:
            print(plan_text(n, dict(wp_x=a.wp_x, wp_y=a.wp_y, long=a.long)))
        return 0
    if a.cmd == "build":
        os.makedirs(a.saves, exist_ok=True)
        return subprocess.run([*hr.PY, "tools/d2s.py", "build", ais.EXCEL, "tools/d2s_recipes/%s.json" % a.recipe, ais.BASE,
                               os.path.join(a.saves, "SpecNova.d2s")], cwd=ROOT).returncode
    if a.cmd == "gate":
        ok, text = gate(a.log)
        sys.stdout.write(text)
        return 0 if ok else 1
    if a.cmd == "run":
        return run(a)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
