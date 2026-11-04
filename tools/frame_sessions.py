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


def window(scene, cover=0, what="", n=LEN, hooks=False):
    return ("window", scene, n, cover, what, hooks)


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
    # plan 0055 Phase 2b batch (ruling 4): Blood Moor's Fallen, then the Den of Evil's maze, in one process. `explore --any-level`
    # walks out of the Rogue Encampment (Teleport does not cast in a town) and goes on in Blood Moor; the windows open while it
    # runs. The class filter counts the tier's Fallen (reviewed AI rows 6 and 13) for the pack, any live monster for the maze.
    expl = ["explore", "--any-level", "--hops", "400", "--nova", "2", "--nova-key", "F2", "--radius", "9", "--drink", "0.5",
            "--es", "0"]
    descend = ["farm", "--sweep", "--descend", "0,1,2,3", "--descend-to", "8", "--time", "600"] + NOVA
    # the character starts beside Warriv and the stash: the first hops east and south clear them (a click toward them opens a
    # dialog or the stash, dev session 2026-11-04-frame2-w), then `explore` leaves the town by itself in about 30 s
    # One scene per fresh process (the pack and the maze are two sessions of a seed): the dev sessions 2026-11-04-frame2 showed that
    # `farm --sweep` leaves Blood Moor by itself when it has swept it, so the maze's descend cannot follow pack windows.
    walkout = [("settle", 20), ("pilot", ["hop", "--walk", "12", "0"], 60), ("pilot", ["hop", "--walk", "12", "0"], 60),
               ("pilot", ["hop", "--walk", "0", "12"], 60), ("pilot", ["hop", "--walk", "0", "12"], 60), ("bg", expl, 1200),
               ("lvl", 2, 360)]

    def pack_steps(first):
        # the first pack session's second window covers a frame = 0 (mod 8192), its last window arms the 65 hooks (FRAME_HOOKS,
        # ruling 4 (vi) of the lane/p55b review). `explore` goes on in Blood Moor while the windows run.
        return walkout + [("settle", 4), ("near", 22, 2, 300, "tier"),
                window("pack", n=500, what="pilot: Blood Moor, a Fallen pack in range, Nova (the pack scene's first window)"), ("gate", "pack"),
                ("near", 22, 2, 240, "tier"),
                window("pack", n=500, cover=8192 if first else 0,
                       what="the second pack window" + (" (a frame = 0 mod 8192: SaveGameClients as a boundary oracle)" if first else "")),
                ("near", 22, 2, 240, "tier"),
                window("pack", n=500, hooks=first, what="the third pack window" + (" (FRAME_HOOKS=1: the 65 universal hooks)" if first else "")),
                ("killbg",)]

    def maze_steps(first, h1=False):
        # `explore` stops at Blood Moor (killbg at the level wait); the descend then takes the warp of LvlWarp rows 0-3 that leads to 8
        return walkout + [("killbg",), ("settle", 4), ("bg", descend, 900), ("lvl", 8, 600), ("settle", 6), ("near", 30, 1, 300, "any"),
                window("maze", n=500, hooks=h1, what="pilot: the Den of Evil (the maze scene's first window)" + (" (FRAME_HOOKS=1: the 65 universal hooks)" if h1 else "")), ("gate", "maze"),
                ("near", 30, 1, 300, "any"),
                window("maze", n=500, cover=8192 if first else 0,
                       what="the second maze window" + (" (a frame = 0 mod 8192: SaveGameClients as a boundary oracle)" if first else "")),
                ("near", 30, 1, 300, "any"),
                window("maze", n=500, hooks=first, what="the third maze window" + (" (FRAME_HOOKS=1: the 65 universal hooks)" if first else "")),
                ("killbg",)]
    # plan 0055 `lane/p55d` (the owner's option A): the defender and Corpsefire windows. A pack's window 1 has the player standing
    # still with no pilot running (the Fallen walk up and melee her), window 2 the pilot again with Nova. `near` with "tier" holds
    # the pilot until a Fallen is in range, then the pilot is stopped for window 1.
    def packd_steps():
        return walkout + [("settle", 2), ("near", 22, 2, 300, "tier"), ("killbg",), ("settle", 1),
                window("pack", n=500, what="the player stands still, no pilot running (melee on the player: the defender rows)"), ("gate", "pack"),
                ("bg", expl, 1200), ("near", 22, 1, 120, "tier"),
                window("pack", n=500, what="Nova again (the pilot's explore), the same pack"), ("gate", "pack"), ("killbg",)]

    def den_steps():
        return walkout + [("killbg",), ("settle", 4), ("bg", descend, 900), ("lvl", 8, 600), ("settle", 2), ("near", 40, 1, 420, "corpse"),
                window("maze", n=500, what="the Den of Evil with Corpsefire near (zombie1, mod 27)"), ("gate", "maze"), ("killbg",)]
    return {
        "packd": dict(diff="normal", est="outdoor pack (1 player, 15 monsters)", text="Blood Moor's Fallen: a standing player, then Nova",
                      steps=packd_steps()),
        "den": dict(diff="normal", est="maze boss (1 player, boss + 10 minions)", text="the Den of Evil, a window opened with Corpsefire near",
                    steps=den_steps()),
        "town": dict(diff="normal", est="town (1 player, 8 NPCs)", text="Act I town (Rogue Encampment)", steps=town),
        "pack1": dict(diff="normal", est="outdoor pack (1 player, 15 monsters)", text="Blood Moor's Fallen pack, with the mod 8192 and hooks windows",
                      steps=pack_steps(True)),
        "pack": dict(diff="normal", est="outdoor pack (1 player, 15 monsters)", text="Blood Moor's Fallen pack", steps=pack_steps(False)),
        "maze": dict(diff="normal", est="maze boss (1 player, boss + 10 minions)", text="the Den of Evil", steps=maze_steps(False)),
        "mazeh": dict(diff="normal", est="maze boss (1 player, boss + 10 minions)", text="the Den of Evil, hooks armed in the first window",
                      steps=maze_steps(False, True)),
        "maze1": dict(diff="normal", est="maze boss (1 player, boss + 10 minions)", text="the Den of Evil, with the mod 8192 and hooks windows",
                      steps=maze_steps(True)),
    }


def describe(step):
    k = step[0]
    if k == "window":
        return "window %s len=%d%s%s  # %s" % (step[1], step[2], " cover=%d" % step[3] if step[3] else "",
                                               " hooks=1" if len(step) > 5 and step[5] else "", step[4])
    if k in ("pilot", "bg"):
        return "%s d2pilot %s  (timeout %ds)" % ("run" if k == "pilot" else "start in background", " ".join(step[1]), step[2])
    if k == "settle":
        return "wait %ds" % step[1]
    if k == "near":
        return "wait until %d live %smonsters are within %d sub-tiles of the player (MON line), at most %d s" % (
            step[2], {"tier": "tier ", "corpse": "Corpsefire (zombie1, mod 27) "}.get(step[4] if len(step) > 4 else "", ""), step[1], step[3])
    if k == "lvl":
        return "wait until the player is in level %d (PLR lid), at most %d s" % (step[1], step[2])
    if k == "killbg":
        return "stop the background pilot command"
    if k == "level":
        return "wait for the player to leave the level it is in (PLR lid changes)"
    if k == "join":
        return "wait for the background pilot command"
    return "pilot gate of the %s scene's first window: stop on (a), (c) or above 3x estimate13; a mismatch is listed, not a stop" % (
        step[1] if len(step) > 1 else "first")


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


def gate2(log, scene, index=0):
    """The pilot gate of the batch: the (index)th window of the log by (a) whole, (c) completed with no LOGERR or CAP, and lines
    per frame against three times the scene's estimate13 mid. A mismatch is listed in the text and is not a stop (the batch
    goes on, that window is uncounted: plan 0055 log, 2026-11-04 review). -> (ok, text, mismatches)."""
    import frame_xs
    wins, _o = fw.parse_log(log)
    if len(wins) <= index:
        return False, "GATE no window %d in the log\n" % index, []
    w = wins[index]
    fails = fw.check_whole(w)
    x = frame_xs.check_chain2(w)
    s = fw.stats(w, fw.check_chain(w))
    est = frame_volume.estimate13_rows().get((fw.SCENE_EST.get(scene or w["scene"], ""), "mid"))
    carried = w["wend"] is not None and w["wend"].get("ok") and not any(t in ("LOGERR", "CAP") for _n, t, _o in w["lines"])
    text = "GATE window %d (%s, %d frames): (a) whole %s, (c) carried %s, mismatches %d" % (
        index + 1, w["scene"], w["len"], "PASS" if not fails else "FAIL " + "; ".join(fails[:2]), "PASS" if carried else "FAIL",
        len(x["fails"]))
    ok = not fails and bool(carried)
    if est and s["n"]:
        ncli = sum(1 for _n, t, o in w["lines"] if fw.client_fn_line(t, o))      # client function 0x00473090's XS lines (plan 0055 log, lane/p55c review)
        lpf = (s["lines"] - ncli) / s["n"]
        text += ", %.1f lines per frame without the client function's %d (3x estimate13 %.1f)" % (lpf, ncli, 3 * est["lines"])
        if lpf > 3 * est["lines"]:
            ok = False
            text += " OVER: stop for the architect"
    text += "\n"
    for f in x["fails"][:8]:
        text += "  MISMATCH line %d %s [%s] %s\n" % (f["line"], f["tag"], f["kind"], f["msg"])
    return ok, text, x["fails"]


def monsters_near(log, r, tail=400000, kinds="any"):
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
            mc = fw.monster_classes() if kinds == "tier" else {}
            return sum(1 for m in o.get("m", []) if (m.get("hp") or 0) > 0 and m.get("mode") not in (0, 12)
                       and ((m["x"] - o["x"]) ** 2 + (m["y"] - o["y"]) ** 2) ** 0.5 <= r
                       and (kinds != "tier" or mc.get(m.get("cls"), ("", ""))[1] in fw.TIER_AI)
                       and (kinds != "corpse" or (m.get("cls") == 5 and 27 in (m.get("mods") or []))))     # Corpsefire: zombie1, Mod1 27
    return 0


class Session:
    def __init__(self, slot, tag, saves, run_id, dev, pilot_only, seed=SEED0):
        self.slot, self.tag, self.saves, self.dev, self.pilot_only = slot, tag, os.path.abspath(saves), dev, pilot_only
        self.seed = seed
        self.nwin_gated = 0
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
        # the hook breakpoints exist (disabled) only when the process starts with FRAME_HOOKS: a scene with a hooks window sets it
        if any(st[0] == "window" and len(st) > 5 and st[5] for st in sc["steps"]):
            os.environ["FRAME_HOOKS"] = "1"
        else:
            os.environ.pop("FRAME_HOOKS", None)
        hr.install(self.slot, self.tag, out=self.out)
        self.drv = hr.launch(self.slot, seed, self.log, gdb=GDB, steps=STEPS[sc["diff"]], after=3000,
                             install=(self.tag, [save]), out=self.out, stem=self.stem)
        hr.mark(self.stem, name, "start", self.log, "launch seed=%d" % seed)
        r = hr.wait_ready(self.log, "Frame logger armed", 180, proc=self.drv, tick=lambda: hr.hide_window(self.slot))
        ok = r == hr.READY and hr.wait_count(self.log, "PLR", 1, 180, self.drv)
        self.t0 = time.time()
        return bool(ok)

    def open_window(self, step):
        scene, n, cover = step[1], step[2], step[3]
        hooks = len(step) > 5 and step[5]
        with open(self.ctl, "a") as f:
            f.write("open %d %s%s%s\n" % (n, scene, " cover=%d" % cover if cover else "", " hooks=1" if hooks else ""))
        self.nwin += 1
        wait = 120 + n / FPS * 40 + (cover / FPS * 3 if cover else 0)
        return hr.wait_count(self.log, "WEND", self.nwin, wait, self.drv)

    def run_scene(self, name, sc):
        seed = self.seed     # a new map seed per session (5501, 5503, 5505); the town windows' walk and the waypoint need 5501
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
                self.out.write("bg: %s pid %d\n" % (" ".join(step[1][:2]), self.bg))
            elif k == "near":
                kinds = step[4] if len(step) > 4 else "any"
                t = time.time()
                while monsters_near(self.log, step[1], kinds=kinds) < step[2] and time.time() - t < step[3] and self.drv.poll() is None:
                    time.sleep(0.4)
                got = monsters_near(self.log, step[1], kinds=kinds)
                self.out.write("near: %d %s monsters within %d after %.1f s\n" % (got, kinds, step[1], time.time() - t))
                if got < step[2]:
                    return "failed", "no %s pack within %d sub-tiles in %d s" % (kinds, step[1], step[3])
            elif k == "lvl":
                t = time.time()
                while ais.level_of(self.log) != step[1] and time.time() - t < step[2] and self.drv.poll() is None:
                    time.sleep(1)
                if ais.level_of(self.log) != step[1]:
                    return "failed", "the player is in level %s, not %d, after %d s" % (ais.level_of(self.log), step[1], step[2])
                self.out.write("lvl: level %d after %.1f s\n" % (step[1], time.time() - t))
            elif k == "killbg":
                if self.bg:
                    try:
                        os.killpg(self.bg, 15)
                    except OSError:
                        pass
                    self.bg = None
            elif k == "join":
                time.sleep(2)
            elif k == "window":
                if not self.open_window(step):
                    return "failed", "window %d did not complete" % self.nwin
            elif k == "gate" and len(step) > 1:
                ok, text, _mm = gate2(self.log, step[1], self.nwin_gated)
                self.nwin_gated = self.nwin
                self.out.write(text)
                sys.stdout.write(text)
                if not ok and self.dev and "OVER" in text and "FAIL" not in text.split("lines per frame")[0]:
                    sys.stdout.write("DEV session: over the stop rate, the route goes on (a kept session stops here)\n")
                elif not ok:
                    return "failed", "the pilot gate failed (stop for the architect)"
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
        s = Session(a.slot, a.tag, a.saves, a.run, a.dev, a.pilot_only, a.seed)
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
            p.add_argument("--seed", type=int, default=SEED0, help="the map seed of the session (a new one per kept session)")
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
