"""Scripted harness sessions for plan 0042 Phase 2 (quests and travel): one game per session on one slot, logged by
tools/gdb/quest-state.gdb, driven by tools/d2pilot.py's Pilot (clicks, Teleport, the waypoint menu) and the
actions below.

Usage:
  python3 -I tools/quest_sessions.py list
  python3 -I tools/quest_sessions.py run --slot N --tag TAG --run RUN SESSION [SESSION ...]
  python3 -I tools/quest_sessions.py act --slot N LOG ACTION [ACTION ...]      # actions on a running session
  python3 -I tools/quest_sessions.py load --slot N [NAME ...]     # load each built save, Save and Exit, compare

A session installs one save (workspace/runtime/quest-saves-p42/<Name>/<Name>.d2s), launches the game with
tools/d2run.py (seed, difficulty steps), plays its action list, and stops the slot (tools/slots.py stop N); the
slot's saves directory goes back to the TAG aside after each session. The log goes to
workspace/logs/quests/<RUN>-<SESSION>.log. Actions:

  talk:CLS:N          talk N times to the nearest unit of MonStats class CLS (walk, click it, wait for the
                      dispatched event 0 with that class, Escape, wait for event 2)
  menu:NAME:LINE:N    d2pilot.py npc NAME with --menu-line LINE (an NPC menu action, e.g. Warriv's travel), N times
  tp:N                N town-portal cycles: open (the book at inventory cell 0,0, right click), go through the field
                      end, come back through the town end (the owner: both ends freed)
  wp:CHAIN            d2pilot.py wpchain --chain CHAIN (space-separated TAB,ROW hops; '_' for a space here)
  towp                d2pilot.py npc waypoint walk (next to the town waypoint)
  nearwp              Teleport next to the current field level's waypoint (OBJP), e.g. after town-portal cycles
  explore:HOPS        d2pilot.py explore --hops HOPS (Nova, new rooms)
  walk:HOPS           d2pilot.py explore --any-level --walk --hops HOPS (a town)
  clickwarp:REC[:N]   Teleport next to the warp unit of LvlWarp row REC (WRP lines) and click it, up to N warp events
  warp:REC[:S]        d2pilot.py farm --descend REC --time 1 --descend-time S (default 400; find and take the
                      warp of the LvlWarp row REC, as the WRP lines number it)
  objop:CLS:N         d2pilot.py objop --obj-cls CLS --times N (Teleport to the object, operate it)
  qlog                open the quest log, click the act tabs, close it (packet 0x58 for the entries shown)
  key:K, sleep:S, shot:NAME
Nothing here feeds a model.
"""
import json
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
PY = [sys.executable, "-I"]
SAVES = [os.path.join(ROOT, "workspace", "runtime", "quest-saves-p42"),      # quest_saves.py build (plan 0042 P0)
         os.path.join(ROOT, "workspace", "runtime", "quest-saves-p42h"),     # d2s.py build of quest-tpc (Phase 2)
         os.path.join(ROOT, "workspace", "runtime", "quest-saves-p42q")]     # part 2's step recipes (build_part2)
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]
TOWNS = {1, 40, 75, 103, 109}
# a warp's place where it is fixed (Lut Gholein is one preset; part 1 and part 2 logs, WRP lines): a walking goal
# until the warp's room is logged
WARP_HINTS = {20: (5218, 5180), 24: (5050, 5142)}

# name: (save Name, steps, seed, [actions], extra pilot args)
SESSIONS = {}


_SELECT = {}


def warp_select(rec):
    """LvlWarp row rec (the WRP lines' numbering: the excel rows without the 'Expansion' divider): (SelectX, SelectY,
    SelectDX, SelectDY), or None when the box is empty."""
    if not _SELECT:
        path = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel", "lvlwarp.txt")
        rows = [ln.rstrip("\r\n").split("\t") for ln in open(path, errors="replace")]
        h = rows[0]
        k = 0
        for r in rows[1:]:
            if not r or r[0] == "Expansion":
                continue
            v = [int(r[h.index(c)] or 0) for c in ("SelectX", "SelectY", "SelectDX", "SelectDY")]
            _SELECT[k] = v
            k += 1
    v = _SELECT.get(rec)
    return v if v and v[2] > 0 and v[3] > 0 else None


def sess(name, save, steps, seed, actions, extra=None):
    SESSIONS[name] = (save, steps, seed, actions, extra or [])


def sh(args, timeout=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


class Tail:
    """New JSON lines of the log after an offset."""

    def __init__(self, path):
        self.path = path
        self.off = os.path.getsize(path) if os.path.exists(path) else 0

    def mark(self):
        self.off = os.path.getsize(self.path)

    def lines(self):
        with open(self.path, errors="replace") as f:
            f.seek(self.off)
            data = f.read()
        out = []
        for line in data.splitlines():
            tag, _, rest = line.partition(" ")
            if rest.startswith("{"):
                try:
                    out.append((tag, json.loads(rest)))
                except ValueError:
                    pass
        return out

    def wait(self, pred, timeout):
        t0 = time.time()
        while time.time() - t0 < timeout:
            for tag, d in self.lines():
                if pred(tag, d):
                    return d
            time.sleep(0.15)
        return None


def last(path, tag):
    v = None
    with open(path, errors="replace") as f:
        for line in f:
            if line.startswith(tag + " "):
                v = line
    if v is None:
        return None
    try:
        return json.loads(v[len(tag) + 1:])
    except ValueError:
        return None


class Driver:
    def __init__(self, slot, log, extra):
        import d2pilot
        self.slot, self.log, self.extra = slot, log, extra
        self.d2p = d2pilot

        class A:
            display = ":%d" % (7 + slot)
            cx, cy, view_h = 400, 290, 571
        self.p = d2pilot.Pilot(A)
        self.st = d2pilot.LogState(log)

    def pos(self):
        self.st.poll()
        return self.st.pos

    def npc_units(self, cls):
        for tag in ("NPCQ", "NPC"):          # NPCQ first: written every 0.5 s; the NPC line lags a walking NPC
            d = last(self.log, tag)
            out = [u for u in d["n"] if u[0] == cls] if d else []
            if out:
                return out
        return []

    def click_rel(self, dx, dy, up=0, button=1):
        sx, sy = self.p.screen(dx, dy)
        sx, sy = max(10, min(790, sx)), max(10, min(530, sy - up))
        self.p.dpy.click(self.p.off[0] + int(sx), self.p.off[1] + int(sy), button=button, hold=0.08)

    def walk_towards(self, x, y, near):
        for _ in range(30):
            pos = self.pos()
            if not pos:
                time.sleep(0.5)
                continue
            dx, dy = x - pos[0], y - pos[1]
            d = math.hypot(dx, dy)
            if d <= near:
                return True
            k = min(9.0, d) / d
            self.click_rel(dx * k, dy * k)
            time.sleep(1.0)
        return False

    def talk(self, cls, n):
        done = 0
        for i in range(n * 3 + 120):
            if done >= n:
                break
            units = self.npc_units(cls)
            pos = self.pos()
            if not units or not pos:
                # not seen: walk towards the nearest part of the town not yet walked (d2pilot.explore_step)
                if pos:
                    tgt = self.d2p.explore_step(self.st, 9)
                    if tgt is False:
                        print("talk %d: not seen anywhere in level %s" % (cls, pos[2]), flush=True)
                        return done
                    if tgt:
                        self.click_rel(tgt[0] - pos[0], tgt[1] - pos[1])
                        time.sleep(1.1)
                        continue
                time.sleep(1.0)
                continue
            u = min(units, key=lambda u: math.hypot(u[3] - pos[0], u[4] - pos[1]))
            if math.hypot(u[3] - pos[0], u[4] - pos[1]) > 10:
                self.walk_towards(u[3], u[4], 8)
                units = self.npc_units(cls)
                pos = self.pos()
                u = min(units, key=lambda u: math.hypot(u[3] - pos[0], u[4] - pos[1]))
            t = Tail(self.log)
            self.click_rel(u[3] - pos[0], u[4] - pos[1], up=(40, 28, 55)[i % 3])
            d = t.wait(lambda tag, d: tag == "EV" and d.get("k") == "de" and d.get("ph") == 0 and d.get("ev") == 0
                       and d.get("ucls") == cls, 8)
            if not d:
                # no NpcInteractStart, so no window opened: no Escape here (an Escape with nothing open opens the
                # game menu, and the next click on the NPC's place can land on SAVE AND EXIT, part 2 x-talk1-b)
                print("talk %d: no event 0 (try %d)" % (cls, i + 1), flush=True)
                time.sleep(0.3)
                continue
            time.sleep(0.6)
            t.mark()
            self.p.dpy.key("Escape")
            t.wait(lambda tag, d: tag == "EV" and d.get("k") == "de" and d.get("ph") == 1 and d.get("ev") == 2, 4)
            done += 1
            print("talk %d: %d/%d" % (cls, done, n), flush=True)
            time.sleep(0.4)
        return done

    def tp(self, n):
        import d2pilot
        done = 0
        for i in range(n * 2):
            if done >= n:
                break
            pos0 = self.pos()
            t = Tail(self.log)
            self.p.dpy.key("i")
            time.sleep(0.5)
            x, y = d2pilot.cell_xy("inv:0,0")
            self.p.dpy.click(self.p.off[0] + x, self.p.off[1] + y, button=3, hold=0.08)
            time.sleep(0.4)
            self.p.dpy.key("i")
            d = t.wait(lambda tag, d: tag == "EV" and d.get("k") == "tp" and d.get("ph") == 1, 6)
            if not d:
                print("tp: no open (try %d)" % (i + 1), flush=True)
                self.p.dpy.key("Escape")
                time.sleep(0.5)
                continue
            fld = t.wait(lambda tag, d: tag == "PU" and d.get("at") == "field1", 2)
            par = t.wait(lambda tag, d: tag == "PU" and d.get("at") == "partner2", 2)
            if not fld or not par:
                print("tp: open refused or no pair", flush=True)
                time.sleep(1.0)
                continue
            time.sleep(1.2)
            ok = False
            for k in range(4):
                pos = self.pos()
                t2 = Tail(self.log)
                self.click_rel(fld["opos"][0] - pos[0], fld["opos"][1] - pos[1], up=30 + 10 * k)
                if t2.wait(lambda tag, d: tag == "EV" and d.get("k") == "portal" and d.get("ph") == 1, 6):
                    ok = True
                    break
            if not ok:
                print("tp: field end not taken", flush=True)
                continue
            time.sleep(2.0)
            ok = False
            for k in range(5):
                pos = self.pos()
                t3 = Tail(self.log)
                self.click_rel(par["opos"][0] - pos[0], par["opos"][1] - pos[1], up=30 + 10 * k)
                if t3.wait(lambda tag, d: tag == "EV" and d.get("k") == "portal" and d.get("ph") == 1, 6):
                    ok = True
                    break
                time.sleep(0.5)
            if not ok:
                print("tp: town end not taken", flush=True)
                return done
            done += 1
            print("tp: %d/%d" % (done, n), flush=True)
            time.sleep(2.0)
        return done

    def clickwarp(self, rec, tries):
        clicks = 0
        for _ in range(40):
            pos = self.pos()
            ws = [(x, y) for (lid, r, x, y) in self.st.wrp if r == rec
              and math.hypot(x - pos[0], y - pos[1]) < 200] if pos else []    # by position: a PLR line's level lags
            if not ws:
                print("clickwarp %d: no such warp logged in level %s" % (rec, pos[2] if pos else None), flush=True)
                return
            wx, wy = min(ws, key=lambda w: math.hypot(w[0] - pos[0], w[1] - pos[1]))
            dx, dy = wx - pos[0], wy - pos[1]
            d = math.hypot(dx, dy)
            if d > 6:
                k = min(9.0, d - 3) / d
                self.p.teleport(int(round(dx * k)), int(round(dy * k)))
                time.sleep(0.8)
                continue
            t = Tail(self.log)
            self.click_rel(dx, dy, up=8 + 8 * (clicks % 3))
            got = t.wait(lambda tag, d: tag == "EV" and d.get("k") == "warp" and d.get("ph") == 1, 4)
            clicks += 1
            if got:
                gate = [d for tag, d in t.lines() if tag == "EV" and d.get("k") == "warpgate" and d.get("ph") == 1]
                print("clickwarp %d: warp event, level %s -> %s, gate %s" % (
                    rec, pos[2], got.get("lid"), [g.get("eax") for g in gate]), flush=True)
                tries -= 1
                if got.get("lid") != pos[2] or tries <= 0:
                    time.sleep(1.5)
                    return
                time.sleep(1.0)
            elif clicks > 12:
                print("clickwarp %d: no warp event after %d clicks" % (rec, clicks), flush=True)
                return

    def move_near(self, x, y, near):
        """Get within `near` sub-tiles of (x, y): Teleport hops in the field, walking clicks along a known free path
        in a town (Teleport does not cast there). True when there."""
        for _ in range(45):
            pos = self.pos()
            if not pos:
                time.sleep(0.5)
                continue
            dx, dy = x - pos[0], y - pos[1]
            d = math.hypot(dx, dy)
            if d <= near:
                return True
            if pos[2] in TOWNS:
                tgt = self.d2p.path_near(self.st, (x, y), max(1, near - 1), 9.0)
                if tgt is not None:
                    self.click_rel(tgt[0] - pos[0], tgt[1] - pos[1])
                else:
                    k = min(9.0, d) / d
                    self.click_rel(dx * k, dy * k)
                time.sleep(1.0)
            else:
                k = min(9.0, d - near + 1) / d
                self.p.teleport(int(round(dx * k)), int(round(dy * k)))
                time.sleep(0.7)
        return False

    def warp_once(self, rec, clicks_max=10):
        """Take the warp of LvlWarp row rec (WRP lines) of the current level once: get next to it, click it until a
        warp event (EV k=warp ph=1) is logged. Returns the logged exit line, or None."""
        pos = self.pos()
        ws = [(x, y) for (lid, r, x, y) in self.st.wrp if r == rec
              and math.hypot(x - pos[0], y - pos[1]) < 200] if pos else []    # by position: a PLR line's level lags
        if not ws:
            return None
        wx, wy = min(ws, key=lambda w: math.hypot(w[0] - pos[0], w[1] - pos[1]))
        for k in range(clicks_max):
            if k % 3 == 0:
                # a click on a warp on screen walks to it and takes it: get within 9 sub-tiles only
                self.move_near(wx, wy, 9 if pos[2] in TOWNS else 5)
            pos = self.pos()
            if math.hypot(wx - pos[0], wy - pos[1]) < 4.5:
                # standing on the warp (just arrived through its pair): step off to a free cell 6-8 sub-tiles
                # away first; the warp does not take a click while the player stands on it
                cand = [(pos[0] + dx, pos[1] + dy) for dx in range(-8, 9) for dy in range(-8, 9)
                        if 6 <= math.hypot(dx, dy) <= 8 and self.d2p.standable(self.st.cells, pos[0] + dx, pos[1] + dy)
                        and math.hypot(pos[0] + dx - wx, pos[1] + dy - wy) >= 6]
                if cand:
                    c = cand[(7 * k) % len(cand)]
                    self.click_rel(c[0] - pos[0], c[1] - pos[1])
                else:
                    ang = 0.6 + k
                    self.click_rel(6 * math.cos(ang), 6 * math.sin(ang))
                time.sleep(1.3)
                pos = self.pos()
            t = Tail(self.log)
            box = warp_select(rec)
            if box and k % 2 == 0:
                # the warp's select box (LvlWarp SelectX/Y/DX/DY, pixels from the warp's screen point): its centre
                sx, sy = self.p.screen(wx - pos[0], wy - pos[1])
                sx, sy = sx + box[0] + box[2] // 2, sy + box[1] + box[3] // 2
                sx, sy = max(10, min(790, sx)), max(10, min(530, sy))
                self.p.dpy.click(self.p.off[0] + int(sx), self.p.off[1] + int(sy), button=1, hold=0.08)
            else:
                self.click_rel(wx - pos[0], wy - pos[1], up=8 + 8 * (k % 3))
            got = t.wait(lambda tag, d: tag == "EV" and d.get("k") == "warp" and d.get("ph") == 1, 7)
            if got:
                return got
            print("  warp %d: click %d from (%d, %d), warp (%d, %d): no warp event" % (rec, k, pos[0], pos[1], wx, wy),
                  flush=True)
        return None

    def pingpong(self, recs, n):
        """n warps through a pair of warps: each time the warp of whichever row of recs is logged in the current
        level (e.g. Lut Gholein 24 <-> harem 25)."""
        done = 0
        miss = 0
        while done < n and miss < 4:
            pos = self.pos()
            # the row whose logged warp unit (this level) is nearest; a WRP line can carry a stale level id, so
            # rows farther than 200 sub-tiles are not taken
            near = sorted((math.hypot(x - pos[0], y - pos[1]), rr) for (l, rr, x, y) in self.st.wrp
                          if rr in recs) if pos else []
            have = [rr for dd, rr in near if dd < 200][:1]
            if not have and pos:
                hint = [WARP_HINTS[r] for r in recs if r in WARP_HINTS and math.hypot(
                    WARP_HINTS[r][0] - pos[0], WARP_HINTS[r][1] - pos[1]) < 400]
                if hint:                      # walk towards the warp's usual place until its room is logged
                    print("pingpong: towards %s" % (hint[0],), flush=True)
                    self.move_near(hint[0][0], hint[0][1], 12)
                    continue
            if not have:
                print("pingpong: none of %s logged in level %s" % (recs, pos[2] if pos else None), flush=True)
                time.sleep(1.0)
                miss += 1
                continue
            got = self.warp_once(have[0])
            if not got:
                miss += 1
                print("pingpong: warp %d not taken" % have[0], flush=True)
                continue
            miss = 0
            done += 1
            t0 = time.time()
            while time.time() - t0 < 6:          # the PLR line follows the warp a little later
                q = self.pos()
                if q and q[2] == got.get("lid") and math.hypot(q[0] - got["pos"][0], q[1] - got["pos"][1]) < 30:
                    break
                time.sleep(0.3)
            if done % 10 == 0:
                print("pingpong: %d/%d" % (done, n), flush=True)
            time.sleep(1.2)
        return done

    def towp(self):
        """Walk to the town waypoint; while no waypoint object of the level is logged, walk towards the nearest part
        of the town not yet walked (d2pilot.explore_step)."""
        for _ in range(80):
            pos = self.pos()
            w = self.d2p.waypoint_at(self.log, pos[2]) if pos else None
            if w:
                if self.move_near(w[0], w[1] + 2, 4):
                    return True
                continue
            if pos:
                tgt = self.d2p.explore_step(self.st, 9)
                if tgt:
                    self.click_rel(tgt[0] - pos[0], tgt[1] - pos[1])
            time.sleep(1.1)
        print("towp: the town waypoint was not reached", flush=True)
        return False

    def saveexit(self):
        """Escape, SAVE AND EXIT GAME (window 400, 262); wait for the save file to be rewritten, copy it to
        <log without .log>.out.d2s (compared with the prediction by tools/quests.py check)."""
        import shutil
        import slots
        name = getattr(self, "save_name", None)
        src = os.path.join(slots.saves_dir(self.slot), (name or "") + ".d2s")
        m0 = os.path.getmtime(src) if name and os.path.exists(src) else 0
        self.p.dpy.key("Escape")
        time.sleep(1.0)
        self.p.dpy.click(self.p.off[0] + 400, self.p.off[1] + 262, button=1, hold=0.15)
        t0 = time.time()
        while time.time() - t0 < 20:
            if name and os.path.exists(src) and os.path.getmtime(src) > m0:
                break
            time.sleep(0.5)
        time.sleep(3)
        if name and os.path.exists(src) and os.path.getmtime(src) > m0:
            dst = self.log[:-4] + ".out.d2s"
            shutil.copyfile(src, dst)
            print("saveexit: written save kept as %s" % dst, flush=True)
        else:
            print("saveexit: no save written", flush=True)

    def field_wps(self):
        """{(level, x, y): mode} of the waypoint objects logged in non-town levels (OBJP lines, last mode)."""
        out = {}
        with open(self.log, errors="replace") as f:
            for line in f:
                if line.startswith("OBJP "):
                    try:
                        d = json.loads(line[5:])
                    except ValueError:
                        continue
                    if d.get("cls") in self.d2p.WAYPOINT_CLASSES and d.get("lid") not in TOWNS:
                        out[(d["lid"], d["x"], d["y"])] = d.get("mode")
        return out

    def activate(self, n, minutes):
        """Up to n waypoint activations from mode 0 within `minutes`: explore across levels (walking in a town,
        Teleport and Nova outside) until a field waypoint in mode 0 is logged, Teleport next to it and click it until
        its operate (EV wpop) is logged; Escape closes the menu if one opened."""
        done, t0, tried = 0, time.time(), set()
        while done < n and time.time() - t0 < 60 * minutes:
            pos = self.pos()
            todo = [(k, m) for k, m in self.field_wps().items() if m == 0 and k not in tried and pos and k[0] == pos[2]]
            if todo and pos:
                (lid, x, y), _ = min(todo, key=lambda km: math.hypot(km[0][1] - pos[0], km[0][2] - pos[1]))
                tried.add((lid, x, y))
                self.move_near(x, y + 2, 3)
                ok = False
                for k in range(6):
                    pos = self.pos()
                    t = Tail(self.log)
                    self.click_rel(x - pos[0], y - pos[1], up=20 + 10 * (k % 3))
                    got = t.wait(lambda tag, d: tag == "EV" and d.get("k") == "wpop" and d.get("ph") == 1, 4)
                    if got:
                        ok = True
                        print("activate: level %d (%d, %d) mode %s -> %s" % (lid, x, y, got.get("omode0"),
                                                                             got.get("omode")), flush=True)
                        break
                time.sleep(1.0)
                self.p.dpy.key("Escape")
                time.sleep(0.5)
                done += ok
                continue
            if pos and pos[2] in TOWNS:
                self.pilot(["explore", "--any-level", "--walk", "--hops", "12"], timeout=180)
            else:
                self.pilot(["explore", "--any-level", "--hops", "12", "--nova", "2"], timeout=240)
        print("activate: %d activations" % done, flush=True)
        return done

    def die(self, n):
        done = 0
        t0 = time.time()
        while done < n and time.time() - t0 < 600:
            hp = self.p.hp()
            if hp is not None and hp < 0.03:
                time.sleep(1.5)
                hp = self.p.hp()
                if hp is not None and hp < 0.03:
                    t = Tail(self.log)
                    time.sleep(2.0)
                    self.p.dpy.key("Escape")
                    got = t.wait(lambda tag, d: tag == "EV" and d.get("k") == "p41" and d.get("ph") == 1, 8)
                    print("die: dead; packet 0x41 %s" % ("logged" if got else "not logged"), flush=True)
                    done += bool(got)
                    time.sleep(3)
                    if done < n:
                        self.run(["towp2", "wp:1,2"])
                    continue
            pos = self.pos()
            if pos and pos[2] in TOWNS:
                time.sleep(1)
                continue
            self.pilot(["explore", "--hops", "4", "--nova", "0", "--drink", "0"], timeout=90)
        print("die: %d deaths" % done, flush=True)

    def pilot(self, args, timeout=900):
        return sh(PY + [os.path.join(HERE, "d2pilot.py")] + args[:1] + [self.log] + args[1:] +
                  ["--slot", str(self.slot)] + self.extra, timeout=timeout)

    def run(self, actions):
        for a in actions:
            kind, _, rest = a.partition(":")
            print("== %s" % a, flush=True)
            if kind == "talk":
                c, n = rest.split(":")
                self.talk(int(c), int(n))
            elif kind == "menu":
                name, line, n = rest.split(":")
                self.pilot(["npc", name, "talk", "--menu-line", line, "--repeat", "1", "--done-wait", "3"],
                           timeout=120)
            elif kind == "tp":
                self.tp(int(rest))
            elif kind == "wp":
                self.pilot(["wpchain", "--chain", rest.replace("_", " "), "--linger", "0.1"], timeout=1800)
            elif kind == "clickwarp":         # clickwarp:REC[:TRIES]: Teleport near the warp unit of that LvlWarp
                rec, _, n = rest.partition(":")  # row (WRP lines) and click it; a refused warp is clicked again
                self.clickwarp(int(rec), int(n or 3))
            elif kind == "nearwp":            # Teleport next to the waypoint of the current (field) level
                for _ in range(15):
                    pos = self.pos()
                    w = self.d2p.waypoint_at(self.log, pos[2]) if pos else None
                    if not w:
                        print("nearwp: no waypoint logged in level %s" % (pos[2] if pos else None), flush=True)
                        break
                    dx, dy = w[0] - pos[0], w[1] - pos[1]
                    d = math.hypot(dx, dy)
                    if d <= 4:
                        break
                    k = min(9.0, d - 2) / d
                    self.p.teleport(int(round(dx * k)), int(round(dy * k)))
                    time.sleep(0.8)
            elif kind == "towp":
                self.pilot(["npc", "waypoint", "walk"], timeout=180)
            elif kind == "towp2":             # part 2: walk to the town waypoint, exploring the town until it is logged
                self.towp()
            elif kind == "pingpong":          # pingpong:RECA:RECB:N  N warps through a warp pair
                a, b, n = rest.split(":")
                self.pingpong([int(a), int(b)], int(n))
            elif kind == "warp1":             # warp1:REC  take that warp once (walk in a town, Teleport elsewhere)
                got = self.warp_once(int(rest))
                print("warp1 %s: %s" % (rest, "level %s" % got.get("lid") if got else "not taken"), flush=True)
            elif kind == "explore":
                self.pilot(["explore", "--hops", rest, "--nova", "2"], timeout=900)
            elif kind == "walk":
                self.pilot(["explore", "--any-level", "--walk", "--hops", rest], timeout=600)
            elif kind == "warp":              # warp:REC[:SECONDS]
                rec, _, sec = rest.partition(":")
                sec = sec or "400"
                self.pilot(["farm", "--descend", rec, "--time", "1", "--descend-time", sec],
                           timeout=int(float(sec)) + 120)
            elif kind == "objop":             # objop:CLS:N[:PDEFS]  (PDEFS: the preset room to head for while unseen)
                c, n, *pd = rest.split(":")
                self.pilot(["objop", "--obj-cls", c, "--times", n, "--time", "240", "--done-wait", "4"] +
                           (["--to-pdef", pd[0]] if pd else []), timeout=400)
            elif kind == "qlog":              # the quest log: open it, click each act tab, close it
                self.p.dpy.key("q")
                time.sleep(1.0)
                for k in range(5):
                    self.p.dpy.click(self.p.off[0] + 120 + 60 * k, self.p.off[1] + 80, button=1, hold=0.08)
                    time.sleep(0.8)
                self.p.dpy.key("Escape")
                time.sleep(0.5)
            elif kind == "activate":          # activate:N:MINUTES  waypoint activations from mode 0 (field levels)
                n, m = rest.split(":")
                self.activate(int(n), float(m))
            elif kind == "tonpc":             # tonpc:CLS:PDEFS  leave the town, go to the preset room (LvlPrest Defs,
                cls, defs = rest.split(":")   # comma-separated) of the current field level until NPC CLS is seen
                t0 = time.time()
                while time.time() - t0 < 420:
                    pos = self.pos()
                    if self.npc_units(int(cls)):
                        print("tonpc: %s seen" % cls, flush=True)
                        break
                    if pos and pos[2] in TOWNS:
                        self.pilot(["explore", "--any-level", "--walk", "--hops", "6"], timeout=120)
                    else:
                        self.pilot(["explore", "--to-pdef", defs, "--hops", "30", "--nova", "2"], timeout=300)
                        if not self.npc_units(int(cls)):
                            self.pilot(["explore", "--hops", "15", "--nova", "2"], timeout=240)
            elif kind == "die":               # die:N  N deaths: hop among monsters without casting until the life
                self.die(int(rest))           # orb is empty, then Escape (the client's packet 0x41: back in town)
            elif kind == "approach":          # approach:CLS  Teleport next to object class CLS (no click)
                self.pilot(["objop", "--obj-cls", rest, "--approach", "--time", "240", "--obj-near", "6"], timeout=320)
            elif kind == "goto":              # goto:X:Y  walk (town) or Teleport next to a sub-tile position
                x, y = rest.split(":")
                print("goto: %s" % self.move_near(int(x), int(y), 7), flush=True)
            elif kind == "saveexit":          # Save and Exit; keep the written save beside the log (<log>.out.d2s)
                self.saveexit()
            elif kind == "key":
                self.p.dpy.key(rest)
                time.sleep(0.5)
            elif kind == "sleep":
                time.sleep(float(rest))
            elif kind == "shot":
                self.p.shot(os.path.join(ROOT, "workspace", "logs", "quests", rest + ".png"))
            else:
                print("unknown action %s" % a, flush=True)


def run_session(args, name):
    save, steps, seed, actions, extra = SESSIONS[name]
    log = os.path.join("workspace", "logs", "quests", "%s-%s.log" % (args.run, name))
    if os.path.exists(os.path.join(ROOT, log)):
        print("%s exists; not overwriting" % log)
        return 1
    sv = [os.path.join(d, save, save + ".d2s") for d in SAVES if os.path.exists(os.path.join(d, save, save + ".d2s"))][0] \
        if save else None             # None: no save installed (a character made through the menu)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(args.slot), "restore", args.tag])
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(args.slot), "aside", args.tag])
    launch = PY + [os.path.join(HERE, "d2run.py"), "--slot", str(args.slot), "--seed", str(seed), "--gdb",
                   "tools/gdb/quest-state.gdb", "--steps", "tools/gdb/%s.steps" % steps, "--after", "3600",
                   "--log", log] + (["--install", args.tag, sv] if sv else [])
    print("$ " + " ".join(launch), flush=True)
    subprocess.Popen(launch, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 120:
        if os.path.exists(os.path.join(ROOT, log)) and last(os.path.join(ROOT, log), "PLR"):
            break
        time.sleep(1)
    time.sleep(3)
    import shutil
    if sv:
        shutil.copyfile(sv, os.path.join(ROOT, log)[:-4] + ".in.d2s")     # the installed save, beside the log
    try:
        drv = Driver(args.slot, os.path.join(ROOT, log), extra)
        drv.save_name = save or "stubsorc"
        drv.run(actions)
    finally:
        time.sleep(2)
        sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(args.slot)])
        sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(args.slot), "restore", args.tag])
    print("session %s done: %s" % (name, log), flush=True)
    return 0


LOAD_SET = ["TravelWpOne", "TravelWpTwo", "TravelWpThree", "TravelWpFour", "TravelWpFive", "TravelWpNone", "WpTabTwo",
            "WpTabFiveDraw", "WpArcane", "ActTwoWarriv", "ActThreeMeshif", "ActFourDurance", "ActFiveTyrael",
            "QuestFreshC", "QuestBookLost", "QuestBookHeld", "QuestSummit", "QuestPortalC"]


def run_load(args, names):
    """Plan 0042 Phase 0's first Phase 2 step: load each built save in Normal (tools/gdb/quest-load.steps: the
    inventory and character sheet shots, then Save and Exit), keep the written-back save under
    workspace/logs/quests/loads/, and list how its quest words and waypoints differ from the built file."""
    import shutil
    import slots
    import d2s
    out = os.path.join(ROOT, "workspace", "logs", "quests", "loads")
    os.makedirs(out, exist_ok=True)
    for name in names:
        sv = [os.path.join(d, name, name + ".d2s") for d in SAVES if os.path.exists(os.path.join(d, name, name + ".d2s"))]
        if not sv:
            print("LOAD %s: no built save" % name, flush=True)
            continue
        sv = sv[0]
        sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(args.slot), "restore", args.tag])
        sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(args.slot), "aside", args.tag])
        log = os.path.join("workspace", "logs", "quests", "loads", "%s-load-%s.log" % (args.run, name))
        sh(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(args.slot), "--seed", "4299", "--steps",
                 "tools/gdb/quest-load.steps", "--after", "8", "--install", args.tag, sv, "--log", log], timeout=180)
        sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(args.slot)])
        back = os.path.join(slots.saves_dir(args.slot), name + ".d2s")
        a = open(sv, "rb").read()
        if not os.path.exists(back):
            print("LOAD %s: no save written back" % name, flush=True)
            continue
        b = open(back, "rb").read()
        dst = os.path.join(out, "%s-%s.d2s" % (args.run, name))
        shutil.copyfile(back, dst)
        qa, qb = d2s.quest_words(a), d2s.quest_words(b)
        wa, wb = d2s.parse_waypoints(a), d2s.parse_waypoints(b)
        diffs = []
        for dd in range(3):
            for q in range(d2s.QUEST_WORD_COUNT):
                if qa[dd][q] != qb[dd][q]:
                    diffs.append("%s w%d %04x->%04x" % (d2s.DIFFICULTIES[dd], q, qa[dd][q], qb[dd][q]))
            if sorted(wa[dd]["bits"]) != sorted(wb[dd]["bits"]):
                diffs.append("%s waypoints +%s -%s" % (d2s.DIFFICULTIES[dd], sorted(set(wb[dd]["bits"]) - set(wa[dd]["bits"])),
                                                     sorted(set(wa[dd]["bits"]) - set(wb[dd]["bits"]))))
        import hashlib
        print("LOAD %s: written back %s (built %s); act bytes %s -> %s; quest/waypoint differences: %s" % (
            name, hashlib.sha256(b).hexdigest()[:8], hashlib.sha256(a).hexdigest()[:8], list(a[0xA8:0xAB]),
            list(b[0xA8:0xAB]), "; ".join(diffs) or "none"), flush=True)
        sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(args.slot), "restore", args.tag])
    return 0


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("list", "run", "act", "load"))
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--slot", type=int)
    ap.add_argument("--tag", default="p42h")
    ap.add_argument("--run", default="2026-10-17-quests")
    args = ap.parse_args(argv)
    if args.cmd == "list":
        for k, v in SESSIONS.items():
            print(k, v)
        return 0
    if args.slot is None or args.slot == 0:
        print("--slot N (N >= 1) is required")
        return 2
    if args.cmd == "act":
        log, actions = args.rest[0], args.rest[1:]
        Driver(args.slot, os.path.abspath(log), []).run(actions)
        return 0
    if args.cmd == "load":
        return run_load(args, args.rest or LOAD_SET)
    for name in args.rest:
        run_session(args, name)
    return 0


# ---- the sessions of run:2026-10-17-quests (save Name, steps, seed, actions, extra pilot args)
CLS = CLASSIC_WP
sess("dev-act", "ActTwoWarriv", "enter-normal", 4290, ["menu:warriv:2:1", "sleep:3", "menu:warriv2:2:1", "sleep:3"])
X_A = "2,4 2,5 2,6 2,7 2,8 2,9 3,1 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 4,1 4,2 4,3 5,1 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9"
X_B = "1,1 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 2,1 2,2 2,3 3,1 4,1 5,1 2,1"
C_A = "1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 2,1 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 3,1 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 4,1 4,2 4,3"
C_B = "1,1 2,1 3,1 4,1 1,1"
TALK1 = ["menu:akara:1:1", "key:Escape", "menu:kashya:1:1", "key:Escape", "menu:charsi:1:1", "key:Escape",
         "menu:gheed:1:1", "key:Escape", "menu:warriv:1:1", "key:Escape", "qlog"]
sess("x-act", "ActTwoWarriv", "enter-normal", 4211, ["menu:warriv:2:1", "sleep:2", "menu:warriv2:2:1", "sleep:2"] * 11)
sess("x-wpnew", "TravelWpOne", "enter-normal", 4219, ["walk:25", "towp", "wp:3,1", "walk:40", "explore:40", "nearwp",
                                                      "wp:3,1"])
sess("x-act3", "ActThreeMeshif", "enter-normal", 4218, ["menu:meshif:2:1", "sleep:2", "menu:meshif2:3:1", "sleep:2"] * 6)
sess("x-lut", "QuestBookLost", "enter-normal", 4212, ["walk:25", "talk:331:22", "qlog", "towp", "wp:2,3", "tp:10",
                                                      "nearwp", "wp:" + X_A.replace(" ", "_"), "tp:6", "nearwp",
                                                      "wp:" + X_B.replace(" ", "_"), "tp:1"])
sess("x-summit0", "QuestSummit", "enter-normal", 4213, ["walk:25", "towp", "wp:5,8", "explore:40", "warp:76:150", "clickwarp:76:1", "objop:564:3", "tp:3"])
sess("x-summit1", "TravelWpFive", "enter-normal", 4214, ["towp", "wp:5,8", "explore:40", "warp:76:150", "clickwarp:76:1", "objop:564:2"])
sess("x-orb", "ActFourDurance", "enter-normal", 4215, ["walk:25", "towp", "wp:3,8", "objop:404:3"])
sess("x-off", "TravelWpOne", "enter-normal", 4216, TALK1)
sess("x-fresh", "QuestFresh", "enter-normal", 4217, TALK1)
sess("c-tp", "QuestPortalC", "enter-normal", 4221, TALK1 + ["towp", "wp:1,2", "tp:10", "nearwp", "wp:" + C_A.replace(" ", "_"),
                                                            "tp:6", "nearwp", "wp:" + C_B.replace(" ", "_"), "tp:1"],
     CLS)
sess("nm-lut", "QuestBookLost", "enter-nightmare", 4222, ["walk:25", "talk:331:22", "towp", "wp:2,3", "tp:10",
                                                          "nearwp", "wp:" + X_A.replace(" ", "_"), "tp:6"], ["--es", "30"])
sess("h-lut", "QuestBookLost", "enter-hell", 4223, ["walk:70", "towp", "wp:2,3", "tp:10", "nearwp", "wp:" + X_A.replace(" ", "_"),
                                                    "tp:6", "nearwp", "wp:" + X_B.replace(" ", "_")], ["--es", "30"])
sess("h-wp5", "TravelWpFive", "enter-hell", 4225, ["walk:25", "towp", "wp:5,1_1,1_2,1_3,1_4,1_5,1_1,1_5,1", "tp:2",
                                                    "wp:5,2", "tp:4", "nearwp", "wp:5,1"], ["--es", "30"])
sess("c-wp", "QuestPortalC", "enter-nightmare", 4224, ["walk:25", "towp", "wp:" + C_A.replace(" ", "_"), "tp:8", "nearwp",
                                                       "wp:" + C_B.replace(" ", "_")], CLS + ["--es", "30"])

# ---- part 2, run:2026-10-18-quests2 (plan 0042 Phase 2 part 2)
sess("harem", "TravelWpTwo", "enter-normal", 4301, ["towp2", "wp:2,1", "pingpong:24:25:20"])
sess("sewer", "TravelWpTwo", "enter-normal", 4302, ["towp2", "wp:2,1", "pingpong:20:21:20"])

Q2_A2 = "2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,1 1,1 3,1 4,1 5,1 2,1"
sess("x-warps", "TravelWpTwo", "enter-normal", 4311, ["towp2", "wp:2,1", "pingpong:20:21:100", "towp2",
                                                       "wp:" + Q2_A2.replace(" ", "_"), "saveexit"])

# the Compelling Orb and the Travincal -> Durance gate (100): without qf2 (ActFourDurance wields a staff, holds qf1),
# then with qf2 wielded (quest-orbwill)
sess("x-orbno", "ActFourDurance", "enter-normal", 4312, ["towp2", "wp:3,8", "warp1:64", "objop:404:2:654", "warp1:64",
                                                         "saveexit"])
sess("x-orb", "QuestOrbWill", "enter-normal", 4313, ["towp2", "wp:3,8", "warp1:64", "objop:404:3:654", "sleep:3",
                                                     "warp1:64", "warp1:65", "warp1:66", "saveexit"])
# level 120's warp tiles: row 82 (to 118) and 83 (to 128), from both creators
sess("x-summit2", "QuestSummit", "enter-normal", 4314, ["towp2", "wp:5,8", "explore:40", "warp:76:150", "warp1:82",
                                                        "warp1:83", "saveexit"])
sess("x-summit3", "TravelWpFive", "enter-normal", 4315, ["towp2", "wp:5,8", "explore:40", "warp:76:150", "warp1:82",
                                                         "saveexit"])
# Meshif both ways (the type-5 return to 40), from ActThreeMeshif (Lut Gholein; Meshif at about (5205, 5055))
sess("x-meshif", "ActThreeMeshif", "enter-normal", 4316, (["goto:5205:5060", "menu:meshif:2:1", "sleep:3",
                                                           "menu:meshif2:3:1", "sleep:3"] * 6) + ["saveexit"])

# NPC talk steps (quests/0001 § 7-§ 10 e11 rows) from the quest-talk recipes (the same words in every difficulty)
T1 = ["talk:148:3", "talk:150:2", "talk:155:3"]
T2 = ["talk:201:3", "talk:176:2", "goto:5205:5060", "talk:210:2"]
T3 = ["talk:253:2", "talk:255:2", "talk:252:2", "talk:254:2", "talk:245:2"]
T4 = ["talk:367:4", "talk:246:2"]
T5 = ["talk:511:2"]
X_ALL = ("1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,1 2,1 3,1 4,1 5,1 1,1").replace(" ", "_")   # Act I waypoints + towns
for d, dn, sd in (("x", "enter-normal", 4320), ("h", "enter-hell", 4330), ("nm", "enter-nightmare", 4340)):
    ex = ["--es", "30"] if d != "x" else []
    sess("%s-talk1" % d, "QuestTalkOne", dn, sd + 1, T1 + ["towp2", "wp:" + X_ALL, "saveexit"], ex)
    sess("%s-talk2" % d, "QuestTalkTwo", dn, sd + 2, T2 + ["saveexit"], ex)
    sess("%s-talk3" % d, "QuestTalkThree", dn, sd + 3, T3 + ["saveexit"], ex)
    sess("%s-talk4" % d, "QuestTalkFour", dn, sd + 4, T4 + ["saveexit"], ex)
    sess("%s-talk5" % d, "QuestTalkFive", dn, sd + 5, T5 + ["saveexit"], ex)
C_ALL = ("1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,1 2,1 3,1 4,1 1,1").replace(" ", "_")
sess("c-talk1", "QuestTalkOneC", "enter-normal", 4351, T1 + ["towp2", "wp:" + C_ALL, "saveexit"], CLS)
sess("c-talk2", "QuestTalkTwoC", "enter-normal", 4352, T2 + ["saveexit"], CLS)
sess("c-talk3", "QuestTalkThreeC", "enter-normal", 4353, T3 + ["saveexit"], CLS)
sess("c-talk4", "QuestTalkFourC", "enter-normal", 4354, T4 + ["saveexit"], CLS)

# waypoint activations from mode 0: saves without the act's field waypoints (towns only for that act)
sess("x-wpact3", "TravelWpOne", "enter-normal", 4361, ["towp2", "wp:3,1", "activate:7:14", "saveexit"])
sess("x-wpact5", "TravelWpOne", "enter-normal", 4362, ["towp2", "wp:5,1", "activate:3:10", "saveexit"])
sess("x-wpact2", "TravelWpOne", "enter-normal", 4363, ["towp2", "wp:2,1", "activate:3:10", "saveexit"])
sess("nm-wpact5", "TravelWpOne", "enter-nightmare", 4364, ["towp2", "wp:5,1", "activate:3:10", "saveexit"],
     ["--es", "30"])

# NPC 266 (navi, Flavie): the Blood Moor's border preset (Def 4-7) with file index 3 (drlg/preset step note 1:
# map seeds 45 and 9 have one)
sess("x-navi", "TravelWpTwo", "enter-normal", 45, ["tonpc:266:4,5,6,7", "talk:266:22", "saveexit"])
sess("x-navi9", "TravelWpTwo", "enter-normal", 9, ["tonpc:266:4,5,6,7", "talk:266:22", "saveexit"])

# NpcActTravel: Tyrael's Act IV -> V travel (word 28 first set, then set) and back by waypoint; Warriv each way
sess("x-tyrael", "ActFiveTyrael", "enter-normal", 4317, (["menu:tyrael:2:1", "sleep:3", "towp2", "wp:4,1", "sleep:2"] * 6)
     + ["saveexit"])
sess("x-act2", "ActTwoWarriv", "enter-normal", 4318, (["menu:warriv:2:1", "sleep:2", "menu:warriv2:2:1", "sleep:2"] * 10)
     + ["saveexit"])

# death and resurrection (packet 0x41): a 24-life save in the Cold Plains
sess("x-death", "QuestDeath", "enter-normal", 4319, ["towp2", "wp:1,2", "die:3", "saveexit"])

# a new character (the builder's double join, rejoin 1), Save and Exit
sess("x-newchar", None, "quest-newchar", 4371, ["sleep:4", "saveexit"])

# the Tristram portal in a later game (quest 4 switched off by the join): the cairn stones in the Stony Field
sess("x-tristram", "TravelWpOne", "enter-normal", 4372, ["towp2", "wp:1,3", "approach:17", "sleep:6", "saveexit"])

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
