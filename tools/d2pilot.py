#!/usr/bin/env python3
"""Scripted exploration for agent-driven harness runs (plan 0018 Phase 2): Teleport hops to standable cells, Nova
casts, belt potions, steered by the live gdb log.

    python3 -I tools/d2pilot.py where <run.log>
    python3 -I tools/d2pilot.py explore <run.log> [--hops N] [--hop R] [--nova K] [--potion P] [--shots DIR]
                                                  [--to-pdef DEF] [--slot N | --display :7] [--cx X --cy Y]
                                                  [--loot R] [--loot-max N]     # plan 0023: operate containers
                                                  [--to-warp] [--radius R] [--give-up N] [--burst N] [--blind-nova]
    python3 -I tools/d2pilot.py hop <run.log> <dx> <dy>          # one Teleport to the player + (dx, dy) sub-tiles
    python3 -I tools/d2pilot.py farm <run.log> [--wp TAB,ROW] [--time S] [--es N] [...]   # one fixed-target session
    python3 -I tools/d2pilot.py mons <run.log>                   # the last monster scan and the level's warp rooms
    python3 -I tools/d2pilot.py wp <run.log> <tab> <row> [--wp-x X --wp-y Y]   # town waypoint travel

Watchdog (explore, farm): when neither the log nor the player position changes for --stall seconds (20), a STALL line
names what the pilot was doing and the game process state (gdb holding it shows as 't'), a screenshot is saved, the
current path is dropped; a second stall in a row ends the command. `wp` polls the screen for the waypoint list and
the log for the level change instead of fixed waits. Screen y for clicks taken from screenshots is scaled by
600/571: the harness window shows the 800x600 frame in 571 rows while the game reads the pointer unscaled.

Slots (tools/slots.py): --slot N drives display :7+N; a --display that contradicts it is an error; with neither the
pilot drives slot 0 (:7). It prints the slot and display it drives to stderr. Screenshots of slot N >= 1 are named
pilot-sN-*.png and stall-sN-*.png (slot 0 keeps pilot-*.png and stall-*.png), and the STALL line reports the game.exe
running on the pilot's display only.

The log must be written with tools/gdb/mon-special.gdb or tools/gdb/pilot.py (PLR: the player's position from its
collision mark, RL: the level's DRLG rooms, RRESEED: room activation, CB: each activated room's collision grid;
pilot.py adds MON, the live monsters near the player with life and lightning resist, and the rooms' warps).

Lightning-immune monsters (plan 0019 Phase 2, owner rule): with MON lines in the log, Nova is cast only when a live
monster whose lightning resist (its live base stat 41: MonStats ResLi of the difficulty plus what its special mods
added) is below 100 stands within --radius sub-tiles; immune packs get no cast and the pilot moves on. A target whose
life has not changed after --give-up casts is ignored from then on. At each stop up to --burst casts. Without MON
lines (older logs), or with --blind-nova, Nova is cast every --nova hops as before. `farm` (the item-hunting loop of
harness-play.md): waypoint, then Nova at whatever it can hurt in range, else one hop towards the nearest live boss
(unique, superunique or champion), until the bosses it saw are down (see cmd_farm).
--to-warp heads for a room of the current level that has a warp (stairs, a cave mouth) and stops there. Nothing here feeds a model:
it only decides where to click. A target is a cell whose activation-time collision value has none of the player's
blocking bits (0x1C09, drlg/0005) in a 3x3 square, reached on a breadth-first path over such cells towards the nearest
DRLG room of the current level that has not been activated yet (the population pass runs at activation). Clicks are
window-relative on the 800x600 game window: screen = (cx + 16 (dx - dy), cy + 8 (dx + dy)) for a sub-tile offset
(dx, dy) from the player. Teleport is the left skill cast with Shift held; Nova the right skill. The game window must
have been activated (the steps file's first click does that). --es N casts Energy Shield every N seconds (on the
weapon-swap set's right button with --es-swap 1, else on the main right button); the life orb is sampled after every
hop and a belt potion is drunk below --drink (the orb turns green when poisoned; both colours count as life).
"""
import argparse
import collections
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import collision  # noqa: E402

BLOCK = 0x1C09


class LogState:
    def __init__(self, path):
        self.path = path
        self.f = open(path, errors="replace")
        self.buf = ""
        self.pos = None             # (x, y, lid, room)
        self.rl = {}                # DRLG room -> (level pointer, rect in tiles)
        self.pdef = {}              # DRLG room -> LvlPrest Def of its preset (RL "pdef")
        self.lid_of = {}            # DRLG room -> level id
        self.lptr = {}              # level id -> level pointer
        self.active = set()         # DRLG rooms activated
        self.cells = {}             # (x, y) -> collision value at activation
        self.n_plr = 0
        self.specials = 0
        self.mon = []               # the last MON scan (tools/gdb/pilot.py): live monsters near the player
        self.mon_t = 0              # number of MON scans read
        self.far = {}               # the bosses of the last "far" MON scan beyond the near square, by unit id
        self.warps = {}             # DRLG room -> warp nodes (RL / RRESEED "warps", tools/gdb/pilot.py)
        self.wrp = {}               # (level id, LvlWarp row, x, y): warp units (WRP, tools/gdb/pilot.py)
        self.objs = {}              # object unit -> (class, x, y, mode at creation) (OU0/OUX, tools/gdb/objects.py)
        self.operated = set()       # object units operated (OO0)
        self.ou0 = None

    def poll(self):
        data = self.f.read()
        if not data:
            return
        data = self.buf + data
        lines = data.split("\n")
        self.buf = lines.pop()
        for line in lines:
            tag, _, rest = line.partition(" ")
            if tag not in ("PLR", "RL", "RRESEED", "CB", "SMA0", "SU0", "MON", "WRP", "OU0", "OUX", "OO0"):
                continue
            try:
                d = json.loads(rest)
            except ValueError:
                continue
            if tag == "PLR":
                self.pos = (d["x"], d["y"], d["lid"], d["room"])
                self.n_plr += 1
            elif tag == "RL":
                self.rl[d["room"]] = (d["level"], d["rect"])
                self.pdef[d["room"]] = d.get("pdef")
                if d.get("warps"):
                    self.warps[d["room"]] = d["warps"]
            elif tag == "WRP":
                x0, y0 = 5 * d["rect"][0], 5 * d["rect"][1]
                self.wrp[(d["lid"], d["rec"], x0 + d["dx"], y0 + d["dy"])] = 1
            elif tag == "MON":
                if d.get("far"):
                    x, y = d["x"], d["y"]
                    self.far = {m["id"]: m for m in d["m"] if abs(m["x"] - x) > 48 or abs(m["y"] - y) > 48}
                    self.mon = [m for m in d["m"] if abs(m["x"] - x) <= 48 and abs(m["y"] - y) <= 48]
                else:
                    self.mon = d["m"]
                self.mon_t += 1
            elif tag == "RRESEED":
                if d.get("warps"):
                    self.warps[d["room"]] = d["warps"]
                self.lid_of[d["room"]] = d["level"]
                self.active.add(d["room"])
                if d["room"] in self.rl:
                    self.lptr[d["level"]] = self.rl[d["room"]][0]
            elif tag == "CB":
                z = collision.unz(d["z"])
                c = z.get("cells")
                x0, y0, w, h = d["rect"]
                if c and c[4]:
                    vals = collision.u16cells(c[4])
                    for j in range(h):
                        for i in range(w):
                            self.cells[(x0 + i, y0 + j)] = vals[j * w + i]
            elif tag in ("SMA0", "SU0"):
                self.specials += 1
            elif tag == "OU0":                  # tools/gdb/objects.py: an object's creation (plan 0023)
                self.ou0 = (d["cls"], d["x"], d["y"]) if d["type"] == 2 else None
            elif tag == "OUX":
                o = d.get("o") or {}
                if getattr(self, "ou0", None) and o.get("u"):
                    self.objs[o["u"]] = self.ou0 + (o["mode"],)
                self.ou0 = None
            elif tag == "OO0":
                self.operated.add(d["u"])

    def frontier(self, lid):
        lp = self.lptr.get(lid)
        if lp is None:
            return []
        return [(r, rect) for r, (p, rect) in self.rl.items() if p == lp and r not in self.active]

    def level_rooms(self, lid):
        lp = self.lptr.get(lid)
        return [r for r, (p, _) in self.rl.items() if p == lp] if lp is not None else []


DEAD_MODES = (0, 12)                # MonMode DT (death) and DD (dead)
IMMUNE = 100                        # lightning resist at or above this: Nova does nothing


def live(m):
    return m["mode"] not in DEAD_MODES and (m["hp"] is None or m["hp"] > 0)


def immune(m):
    """Lightning immune: the live base stat 41 (MonStats ResLi of the difficulty plus what its special mods added,
    monsters/0003 handler table) is 100 or more."""
    return m.get("lr") is not None and m["lr"] >= IMMUNE


def nova_targets(st, radius, ignored=()):
    """Live, not lightning-immune monsters within radius sub-tiles of the player, nearest first."""
    if not st.pos:
        return []
    px, py = st.pos[0], st.pos[1]
    out = [m for m in st.mon if live(m) and not immune(m) and m["id"] not in ignored
           and math.hypot(m["x"] - px, m["y"] - py) <= radius]
    return sorted(out, key=lambda m: math.hypot(m["x"] - px, m["y"] - py))


class NovaGate:
    """Casts Nova only at what it can hurt: a live monster in range whose lightning resist is below 100. A monster
    whose life has not moved after --give-up casts at it is ignored from then on (the fallback for a resist the scan
    cannot see, e.g. an aura)."""

    def __init__(self, radius, give_up):
        self.radius, self.give_up = radius, give_up
        self.casts = {}             # monster id -> (casts with it in range, its life at the first of them)
        self.ignored = set()
        self.skipped_immune = 0

    def targets(self, st):
        t = nova_targets(st, self.radius, self.ignored)
        if not t and st.pos:
            px, py = st.pos[0], st.pos[1]
            self.skipped_immune += sum(1 for m in st.mon if live(m) and immune(m)
                                       and math.hypot(m["x"] - px, m["y"] - py) <= self.radius)
        return t

    def cast(self, p, st):
        t = self.targets(st)
        if not t:
            return False
        for m in t:
            n, hp0 = self.casts.get(m["id"], (0, m["hp"]))
            if n >= self.give_up and m["hp"] == hp0:
                self.ignored.add(m["id"])
                continue
            if m["hp"] != hp0:
                n, hp0 = 0, m["hp"]
            self.casts[m["id"]] = (n + 1, hp0)
        p.nova()
        return True


def standable(cells, x, y):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            v = cells.get((x + dx, y + dy))
            if v is None or v & BLOCK:
                return False
    return True


def near_warp(st, x, y, r=6):
    """A cell within r sub-tiles of a warp unit (WRP lines): a Teleport click there can take the warp."""
    return any(abs(wx - x) <= r and abs(wy - y) <= r for (_, _, wx, wy) in st.wrp)


def in_rect(x, y, rect):
    x0, y0, w, h = (5 * v for v in rect)
    return x0 <= x < x0 + w and y0 <= y < y0 + h


def pick_on_path(st, path, hop, bad):
    """The farthest standable cell of path within the hop radius of the player (None if none)."""
    px, py = st.pos[0], st.pos[1]
    cells = st.cells
    # resume from the path cell nearest to the player
    j0 = min(range(len(path)), key=lambda j: (path[j][0] - px) ** 2 + (path[j][1] - py) ** 2)
    pick = alt = None
    for c in path[j0 + 1:]:
        if math.hypot(c[0] - px, c[1] - py) > hop:
            break
        if c in bad:
            continue
        if standable(cells, *c):
            pick = c
        elif not cells.get(c, BLOCK) & BLOCK and math.hypot(c[0] - px, c[1] - py) >= 3:
            alt = c                     # a free cell on a narrow path (its 3x3 square is not all free)
    return pick or alt


def plan(st, hop, bad, limit=400000, targets=None, want_path=False, skip=()):
    """Breadth-first search from the player to a standable cell inside, or next to an unknown cell of, a target room
    (default: the level's rooms not activated yet); returns the farthest cell of that path within the hop radius."""
    px, py, lid, _ = st.pos
    fr = [e for e in st.frontier(lid) if e[0] not in skip] if targets is None else targets
    if not fr:
        return None, "level done (%d rooms skipped)" % len(skip)
    cells = st.cells
    start = (px, py)
    prev = {start: None}
    q = collections.deque([start])
    goal = None
    while q and len(prev) < limit:
        c = q.popleft()
        x, y = c
        if targets is not None and c != start and any(in_rect(x, y, rect) for _, rect in fr):
            goal = c
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in prev:
                continue
            if n not in cells:
                if c != start and any(in_rect(n[0], n[1], rect) for _, rect in fr):
                    goal = c
                    break
                continue
            if cells[n] & BLOCK:
                continue
            prev[n] = c
            q.append(n)
        if goal:
            break
    if goal is None:
        # nothing reachable over known cells: aim at the nearest frontier room's centre
        r, rect = min(fr, key=lambda e: (5 * e[1][0] + 2.5 * e[1][2] - px) ** 2 + (5 * e[1][1] + 2.5 * e[1][3] - py) ** 2)
        tx, ty = 5 * rect[0] + 2.5 * rect[2], 5 * rect[1] + 2.5 * rect[3]
        d = math.hypot(tx - px, ty - py) or 1
        best = None
        reach = int(hop * 1.8)          # Teleport crosses blocked ground: any known standable cell in reach
        for y in range(py - reach, py + reach + 1):
            for x in range(px - reach, px + reach + 1):
                if math.hypot(x - px, y - py) > reach or (x, y) in bad or not standable(cells, x, y):
                    continue
                k = math.hypot(tx - x, ty - y)
                if best is None or k < best[0]:
                    best = (k, (x, y))
        if best and best[0] >= d - 2:
            best = None                 # no cell closer to the room: the caller skips it
        plan.last_room = r
        return (best[1] if best else None), "towards room centre %.0f away" % d
    path = []
    c = goal
    while c is not None:
        path.append(c)
        c = prev[c]
    path.reverse()
    if want_path:
        return path, "path %d to the frontier, %d rooms left" % (len(path), len(fr))
    pick = None
    for c in path[1:]:
        if math.hypot(c[0] - px, c[1] - py) > hop:
            break
        if standable(cells, *c) and c not in bad:
            pick = c
    if pick is None:
        for c in path[1:]:
            if c not in bad and math.hypot(c[0] - px, c[1] - py) <= hop and cells.get(c, BLOCK) & BLOCK == 0:
                pick = c
    return pick, "path %d to the frontier, %d rooms left" % (len(path), len(fr))


class Pilot:
    def __init__(self, args):
        import xdrive
        self.dpy = xdrive.Display(args.display)
        self.off = self.dpy.origin("Diablo II")
        self.cx, self.cy = args.cx, args.cy

    def screen(self, dx, dy):
        sx = self.cx + 16 * (dx - dy)
        sy = self.cy + 8 * (dx + dy)
        return sx, sy

    def teleport(self, dx, dy):
        sx, sy = self.screen(dx, dy)
        sx, sy = max(10, min(790, sx)), max(10, min(540, sy))
        self.dpy.keystate("Shift_L", True)
        time.sleep(0.05)
        self.dpy.click(self.off[0] + int(sx), self.off[1] + int(sy), button=1, hold=0.12)
        time.sleep(0.05)
        self.dpy.keystate("Shift_L", False)

    nova_hold = 0.12

    nova_key = None

    def nova(self):
        """Nova with Shift held. With nova_hold above a cast time the right button stays down, and the game repeats
        the cast at the character's own cast rate (back-to-back casts, no polling in between). With nova_key (an
        F-key bound to Nova in the save) the key is pressed first, so a lost key press heals at the next burst."""
        if self.nova_key:
            self.dpy.key(self.nova_key)
            time.sleep(0.05)
        self.dpy.keystate("Shift_L", True)
        time.sleep(0.05)
        self.dpy.click(self.off[0] + self.cx, self.off[1] + self.cy, button=3, hold=self.nova_hold)
        time.sleep(0.05)
        self.dpy.keystate("Shift_L", False)

    es_key = None

    def shield(self, swap):
        """Energy Shield. With es_key (an F-key bound to it in the save): that key, a right click, then nova_key; the
        keys are idempotent, unlike the weapon swap (W, right click, W), which a dropped W press leaves on the swap
        set for good (owner report, plan 0019 Phase 2)."""
        if self.es_key:
            self.dpy.key(self.es_key)
            time.sleep(0.1)
            self.dpy.click(self.off[0] + self.cx, self.off[1] + self.cy, button=3, hold=0.12)
            time.sleep(0.6)
            if self.nova_key:
                self.dpy.key(self.nova_key)
                time.sleep(0.05)
            return
        if swap:
            self.dpy.key("w")
            time.sleep(0.4)
        self.dpy.click(self.off[0] + self.cx, self.off[1] + self.cy, button=3, hold=0.12)
        time.sleep(0.6)
        if swap:
            self.dpy.key("w")
            time.sleep(0.4)

    def potion(self, k):
        self.dpy.key(str(k))

    def mana(self):
        """Fill of the mana orb, 0..1: the life orb's test mirrored (window 705..750 x 496..556), blue pixels."""
        return self.hp(x=705, blue=True)

    def hp(self, x=50, blue=False):
        """Fill of the life orb, 0..1: rows of the orb (window 50..95 x 496..556) with more than 10 red (or, poisoned,
        green) pixels."""
        import ctypes as C
        import xdrive
        X = xdrive.X11
        x0, y0, w, h = self.off[0] + x, self.off[1] + 496, 45, 60
        img = X.XGetImage(self.dpy.d, self.dpy.root, x0, y0, w, h, 0xFFFFFFFF, 2)
        if not img:
            return None
        im = xdrive.XImage.from_address(img)
        raw = C.string_at(im.data, im.bytes_per_line * h)
        rows = 0
        for y in range(h):
            line = raw[y * im.bytes_per_line: y * im.bytes_per_line + 4 * w]
            n = 0
            for x in range(w):
                b, g, r = line[4 * x], line[4 * x + 1], line[4 * x + 2]
                if blue:
                    if b > 80 and b > 2 * r and b > g + 20:
                        n += 1
                elif (r > 90 and r > 2 * g) or (g > 55 and g > 2 * r and g > 2 * b):   # red, or green when poisoned
                    n += 1
            if n > 10:
                rows += 1
        return rows / 56.0

    def grab(self, x0, y0, w, h):
        """BGRX bytes of a window-relative rectangle (display pixels, as in a screenshot)."""
        import ctypes as C
        import xdrive
        img = xdrive.X11.XGetImage(self.dpy.d, self.dpy.root, self.off[0] + x0, self.off[1] + y0, w, h, 0xFFFFFFFF, 2)
        if not img:
            return None, 0
        im = xdrive.XImage.from_address(img)
        return C.string_at(im.data, im.bytes_per_line * h), im.bytes_per_line

    def dark_share(self, x0, y0, w, h):
        raw, bpl = self.grab(x0, y0, w, h)
        if raw is None:
            return 0.0
        n = dark = 0
        for y in range(0, h, 4):
            for x in range(0, w, 4):
                b, g, r = raw[y * bpl + 4 * x: y * bpl + 4 * x + 3]
                n += 1
                dark += max(r, g, b) < 28
        return dark / n

    def menu_open(self):
        """The waypoint list is up: its inner panel (screenshot x 160..360, y 140..400) is almost black."""
        return self.dark_share(160, 140, 200, 260) > 0.75

    def click_at(self, x, y, button=1):
        """A click at screenshot coordinates: the window shows the 800x600 frame scaled to its client height
        (571 rows on the harness display) while the game reads the pointer unscaled, so y is scaled back."""
        self.dpy.click(self.off[0] + int(x), self.off[1] + int(round(y * 600 / self.client_h)), button=button,
                       hold=0.08)

    client_h = 571

    def shot(self, path):
        import xdrive
        self.dpy.shot(path, self.off[0], self.off[1], xdrive.GAME_W, xdrive.GAME_H)


class Watchdog:
    """Stall detection (owner rule): when neither the log nor the player position has changed for --stall seconds,
    print a STALL line saying what the pilot was waiting for and the game's process state (a gdb-held stop shows as
    't'), save a screenshot, and tell the caller to recover. Two stalls in a row end the loop."""

    def __init__(self, args, st, pilot):
        self.args, self.st, self.p = args, st, pilot
        self.size, self.pos, self.t = -1, None, time.time()
        self.n = 0

    def game_state(self):
        """pid:state of the game.exe on the pilot's display (the slot's game, not another slot's)."""
        import slots
        for pid, (_, disp, st, _) in sorted(slots.games().items()):
            if disp == self.args.display:
                return "%d:%s" % (pid, st)
        return "none"

    def check(self, doing):
        """0 ok, 1 stalled (recover), 2 stalled twice (give up)."""
        try:
            size = os.path.getsize(self.st.path)
        except OSError:
            size = -1
        pos = self.st.pos
        now = time.time()
        if size != self.size or pos != self.pos:
            self.size, self.pos, self.t = size, pos, now
            self.n = 0
            return 0
        if now - self.t < self.args.stall:
            return 0
        self.n += 1
        shot = os.path.join(self.args.shots or os.path.dirname(self.st.path),
                            "stall%s-%d.png" % (self.args.shot_tag, int(now)))
        try:
            self.p.shot(shot)
        except Exception:  # noqa: BLE001
            shot = "-"
        print("STALL %.0f s: log and position unchanged while %s; game %s; screenshot %s" % (
            now - self.t, doing, self.game_state(), shot))
        sys.stdout.flush()
        self.t = now
        return 2 if self.n >= 2 else 1


def cmd_wp(args):
    st = LogState(args.log)
    st.poll()
    return wp_travel(args, st, Pilot(args), args.dx, args.dy)


def wp_travel(args, st, p, tab, row):
    """Waypoint travel from a town waypoint the character stands near: click the waypoint (--wp-x, --wp-y,
    screenshot coordinates), poll the screen until the list is up, click the act tab and the row, then poll the log
    until the level changes. No fixed waits beyond what the game needs."""
    lid0 = st.pos[2] if st.pos else None
    p.click_at(args.wp_x, args.wp_y)
    t0 = time.time()
    while not p.menu_open():
        if time.time() - t0 > 8:
            print("wp: the waypoint list did not open")
            return 1
        time.sleep(0.1)
    time.sleep(0.2)
    p.click_at(args.wp_tab_x0 + (tab - 1) * args.wp_tab_w, 73)
    time.sleep(0.3)
    y = 133 + (row - 1) * 34
    p.dpy.move(p.off[0] + 230, p.off[1] + int(round(y * 600 / p.client_h)))
    time.sleep(0.1)
    p.click_at(230, y)
    t1 = time.time()
    while time.time() - t1 < 15:
        st.poll()
        if st.pos and st.pos[2] != lid0:
            print("wp: level %s -> %s after %.1f s (menu after %.1f s)" % (lid0, st.pos[2], time.time() - t0, t1 - t0))
            return 0
        time.sleep(0.1)
    print("wp: no level change")
    return 1


def cmd_where(args):
    st = LogState(args.log)
    st.poll()
    if not st.pos:
        print("no PLR yet")
        return 1
    x, y, lid, room = st.pos
    lr = st.level_rooms(lid)
    print("player (%d, %d) level %s; level rooms %d, activated %d, frontier %d; specials so far %d" % (
        x, y, lid, len(lr), sum(1 for r in lr if r in st.active), len(st.frontier(lid)), st.specials))
    return 0


def cmd_hop(args):
    st = LogState(args.log)
    st.poll()
    p = Pilot(args)
    before = st.pos
    p.teleport(args.dx, args.dy)
    time.sleep(1.0)
    st.poll()
    print("before %s after %s (target %+d %+d)" % (before[:2] if before else None, st.pos[:2] if st.pos else None,
                                                    args.dx, args.dy))
    return 0


LOOT_FNS = None


def loot_fns(excel):
    """Objects records whose OperateFn is a container (1 casket, 3 urn, 4 chest, 5 barrel), plan 0023."""
    global LOOT_FNS
    if LOOT_FNS is None:
        from obj_survey import decode
        LOOT_FNS = {i for i, o in enumerate(decode(excel, "objects")) if o["OperateFn"] in (1, 3, 4, 5)}
    return LOOT_FNS


def loot(args, st, p, tried):
    """Operate the containers near the player (plan 0023): nearest first, those within --loot sub-tiles that were
    created closed (mode 0) and not yet operated or tried. A container farther than 4 sub-tiles gets a Teleport next
    to it first; then a plain left click on it (the character walks there and operates it). Returns the count clicked."""
    if not args.loot or not st.pos:
        return 0
    fns = loot_fns(args.excel)
    n = 0
    for _ in range(args.loot_max):
        st.poll()
        px, py = st.pos[0], st.pos[1]
        cand = [(math.hypot(x - px, y - py), u, x, y) for u, (c, x, y, m) in st.objs.items()
                if c in fns and m == 0 and u not in st.operated and u not in tried
                and math.hypot(x - px, y - py) <= args.loot]
        if not cand:
            break
        _, u, x, y = min(cand)
        tried.add(u)
        if math.hypot(x - px, y - py) > 4:
            best = None
            for yy in range(y - 3, y + 4):
                for xx in range(x - 3, x + 4):
                    if (xx, yy) != (x, y) and standable(st.cells, xx, yy):
                        k = math.hypot(xx - x, yy - y)
                        if best is None or k < best[0]:
                            best = (k, xx, yy)
            if best is None:
                continue
            p.teleport(best[1] - px, best[2] - py)
            time.sleep(args.wait)
            st.poll()
            px, py = st.pos[0], st.pos[1]
        sx, sy = p.screen(x - px, y - py)
        sy -= args.loot_dy
        if not (10 <= sx <= 790 and 10 <= sy <= 540):
            continue
        p.dpy.move(p.off[0] + int(sx), p.off[1] + int(sy))      # hover first: the game picks the object per frame
        time.sleep(0.3)
        p.dpy.click(p.off[0] + int(sx), p.off[1] + int(sy), button=1, hold=0.15)
        t0 = time.time()
        while time.time() - t0 < args.loot_wait:
            time.sleep(0.15)
            st.poll()
            if u in st.operated:
                break
        n += 1
        if args.verbose:
            print("loot: class %d at (%d, %d) %s" % (st.objs[u][0], x, y, "operated" if u in st.operated else "no OO0"))
    return n


def cmd_explore(args):
    st = LogState(args.log)
    st.poll()
    p = Pilot(args)
    if not st.pos:
        print("no PLR yet")
        return 1
    lid0 = st.pos[2]
    targets = None
    gate = NovaGate(args.radius, args.give_up)
    if args.to_warp:
        targets = [(r, rect) for r, (lp, rect) in st.rl.items() if r in st.warps and lp == st.lptr.get(lid0)]
        print("target rooms with a warp: %s" % [(rect, st.warps[r]) for r, rect in targets])
        if not targets:
            return 1
    if args.to_pdef is not None:
        defs = {int(v) for v in str(args.to_pdef).split(",")}
        targets = [(r, rect) for r, (lp, rect) in st.rl.items() if st.pdef.get(r) in defs
                   and lp == st.lptr.get(lid0)]
        print("target rooms with preset def %s: %s" % (args.to_pdef, [rect for _, rect in targets]))
        if not targets:
            return 1
    bad = set()
    hist = []
    npot = 0
    skip = set()
    cache = None
    stuck = 0
    k = 0
    last = None
    t0 = time.time()
    t_es = None
    wd = Watchdog(args, st, p)
    tried = set()
    for k in range(1, args.hops + 1):
        if args.loot:
            loot(args, st, p, tried)
        if args.es and (t_es is None or time.time() - t_es > args.es):
            p.shield(args.es_swap)
            t_es = time.time()
        st.poll()
        if st.pos[2] != lid0:
            print("level changed %s -> %s (death or a warp); stop" % (lid0, st.pos[2]))
            break
        w = wd.check("exploring, hop %d from %s" % (k, st.pos[:2]))
        if w == 2:
            print("hop %d: stalled twice; stop" % k)
            break
        if w == 1:
            cache = None
            bad.add(last) if last else None
        if targets is not None and any(in_rect(st.pos[0], st.pos[1], rect) for _, rect in targets):
            print("hop %d: inside the target room at (%d, %d); stop" % (k, st.pos[0], st.pos[1]))
            break
        tgt = None
        if cache and (targets is not None or set(cache[1]) & {r for r, _ in st.frontier(lid0)} - skip):
            tgt = pick_on_path(st, cache[0], args.hop, bad)
            why = "cached path"
        if tgt is None:
            plan.last_room = None
            path, why = plan(st, args.hop, bad, targets=targets, want_path=True, skip=skip)
            while path is None and plan.last_room is not None and targets is None:
                skip.add(plan.last_room)          # unreachable from here: try the next nearest room
                plan.last_room = None
                path, why = plan(st, args.hop, bad, want_path=True, skip=skip)
            if isinstance(path, list):
                fr = targets if targets is not None else st.frontier(lid0)
                end = path[-1]
                near = [r for r, rect in fr if any(in_rect(end[0] + dx, end[1] + dy, rect)
                                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)))]
                cache = (path, near or [r for r, _ in fr])
                tgt = pick_on_path(st, path, args.hop, bad)
            else:
                cache = None
                tgt = path
        if tgt is None:
            print("hop %d: no target (%s); stop" % (k, why))
            break
        px, py = st.pos[0], st.pos[1]
        p.teleport(tgt[0] - px, tgt[1] - py)
        time.sleep(args.wait)
        st.poll()
        moved = (st.pos[0], st.pos[1]) != (px, py)
        if not moved:
            stuck += 1
            bad.add(tgt)
            cache = None
            if stuck >= 6:
                for _ in range(3):
                    a = random.uniform(0, 2 * math.pi)
                    p.teleport(int(args.hop * math.cos(a)), int(args.hop * math.sin(a)))
                    time.sleep(args.wait)
                stuck = 0
        else:
            stuck = 0
        hist.append((st.pos[0], st.pos[1]))
        if len(hist) >= 20 and max(math.hypot(a[0] - hist[-1][0], a[1] - hist[-1][1]) for a in hist[-20:]) < 15:
            if cache:
                skip.update(cache[1])           # the rooms this path aims at stay out of reach: give them up
        if (len(hist) >= 10 and max(math.hypot(a[0] - hist[-1][0], a[1] - hist[-1][1]) for a in hist[-10:]) < 6) or \
                (len(hist) >= 20 and max(math.hypot(a[0] - hist[-1][0], a[1] - hist[-1][1]) for a in hist[-20:]) < 15):
            # no progress over ten hops (monsters in the way): two long hops to random standable cells
            for _ in range(2):
                st.poll()
                qx, qy = st.pos[0], st.pos[1]
                cand = [(x, y) for y in range(qy - 18, qy + 19) for x in range(qx - 18, qx + 19)
                        if 12 <= math.hypot(x - qx, y - qy) <= 18 and standable(st.cells, x, y)]
                if cand:
                    x, y = random.choice(cand)
                    p.teleport(x - qx, y - qy)
                    time.sleep(args.wait)
            cache = None
            hist.clear()
            print("hop %d: no progress over ten hops, two long random hops" % k)
        if args.blind_nova or not st.mon_t:     # no MON scan in this log (an older logger): the blind rhythm
            if args.nova and k % args.nova == 0:
                p.nova()
                time.sleep(0.25)
        elif args.nova:
            for _ in range(args.burst):     # stay and cast while something Nova can hurt is in range
                st.poll()
                if not gate.cast(p, st):
                    break
                time.sleep(args.cast_wait)
        if args.potion and k % args.potion == 0:
            p.potion(1 + (k // args.potion) % 4)
        hp = p.hp()
        if hp is not None and hp < 0.05:
            time.sleep(0.5)
            if (p.hp() or 0) < 0.05:
                print("hop %d: the life orb is empty (death); stop" % k)
                break
        if hp is not None and hp < args.drink:
            npot += 1
            p.potion(1 + npot % 4)
            print("hop %d: life %.2f, potion %d" % (k, hp, 1 + npot % 4))
        if args.shots and k % args.shot_every == 0:
            p.shot(os.path.join(args.shots, "pilot%s-%04d.png" % (args.shot_tag, k)))
        if args.verbose or k % 10 == 0:
            print("hop %d: (%d, %d) -> %s %s; moved %s; frontier %d; specials %d; %.0f s" % (
                k, px, py, tgt, why, moved, len(st.frontier(lid0)), st.specials, time.time() - t0))
            sys.stdout.flush()
        last = tgt
    st.poll()
    print("done after %d hops: level %s frontier %d, specials seen %d; immune in range %d scans, gave up on %d" % (
        k, lid0, len(st.frontier(lid0)), st.specials, gate.skipped_immune, len(gate.ignored)))
    return 0


def greedy_hop(st, target, hop, min_hop, bad=(), avoid_warps=True):
    """The known standable cell within hop sub-tiles of the player (Teleport crosses walls) that is nearest to target,
    at least min_hop away and at least 3 sub-tiles nearer to the target than the player; None if there is none.
    A walk built from these hops strictly approaches its target, so it cannot shuttle back and forth."""
    px, py = st.pos[0], st.pos[1]
    d0 = math.hypot(target[0] - px, target[1] - py)
    best = None
    r = int(hop)
    for y in range(py - r, py + r + 1):
        for x in range(px - r, px + r + 1):
            rr = math.hypot(x - px, y - py)
            if rr > hop or rr < min_hop or (x, y) in bad or not standable(st.cells, x, y):
                continue
            if avoid_warps and near_warp(st, x, y):
                continue
            e = math.hypot(target[0] - x, target[1] - y)
            if e <= d0 - 3 and (best is None or e < best[0]):
                best = (e, (x, y))
    return best[1] if best else None


def room_centre(rect):
    return (5 * rect[0] + 2.5 * rect[2], 5 * rect[1] + 2.5 * rect[3])


UPKEEP = {"t_mana": 0.0, "t_es": None, "npot": 0}


def upkeep(args, p):
    """Belt potions and Energy Shield: a potion from the non-mana columns below --drink life, one from --mana-col
    below --mana-drink mana (at most every 2 s), Energy Shield every --es seconds."""
    u = UPKEEP
    if args.es and (u["t_es"] is None or time.time() - u["t_es"] > args.es):
        p.shield(args.es_swap)
        u["t_es"] = time.time()
    hp = p.hp()
    if hp is not None and hp < args.drink:
        u["npot"] += 1
        col = [c for c in (1, 2, 3, 4) if c != args.mana_col][u["npot"] % 3]
        p.potion(col)
        print("life %.2f, potion column %d" % (hp, col))
    mp = p.mana()
    if args.mana_col and mp is not None and mp < args.mana_drink and time.time() - u["t_mana"] > 2:
        p.potion(args.mana_col)
        u["t_mana"] = time.time()
        print("mana %.2f, potion column %d" % (mp, args.mana_col))


def descend(args, st, p, gate, deadline):
    """Find and take the warp of LvlWarp row --descend on the current level. Until a WRP line of that row is logged,
    hop towards one unactivated room of the level (the nearest when chosen, kept until it activates or no hop gets
    nearer, then skipped); once logged, hop to the warp and left-click its cell (no Shift). Every hop strictly
    approaches the current target (greedy_hop); Nova bursts clear what blocks the way. Returns True on a level change."""
    lid0 = st.pos[2]
    skip, bad = set(), set()
    goal = None
    clicks = still = 0
    path = None
    while time.time() < deadline:
        st.poll()
        if st.pos[2] != lid0:
            print("descend: level %s -> %s" % (lid0, st.pos[2]))
            return True
        upkeep(args, p)
        if gate.cast(p, st):
            continue
        px, py = st.pos[0], st.pos[1]
        cells = [(x, y) for (lid, rec, x, y) in st.wrp if lid == lid0 and rec == args.descend]
        if cells:
            w = min(cells, key=lambda c: math.hypot(c[0] - px, c[1] - py))
            if math.hypot(w[0] - px, w[1] - py) <= 6:
                sx, sy = p.screen(w[0] - px, w[1] - py)
                lift = (0, 12, 24, 36)[clicks % 4]
                p.dpy.click(p.off[0] + int(sx), p.off[1] + int(sy) - lift, button=1, hold=0.08)
                clicks += 1
                t0 = time.time()
                while time.time() - t0 < 2.5:
                    st.poll()
                    if st.pos[2] != lid0:
                        break
                    time.sleep(0.1)
                continue
            tgt = greedy_hop(st, w, args.hop, args.min_hop, bad, avoid_warps=False)
            if tgt is None:
                tgt = greedy_hop(st, w, 1.6 * args.hop, 2, bad, avoid_warps=False)
            if tgt is None:
                # a wall between: follow one breadth-first path over known free cells, never back along it
                if path is None:
                    path, why = plan(st, args.hop, bad, targets=[(None, [w[0] // 5 - 1, w[1] // 5 - 1, 3, 3])],
                                     want_path=True)
                    if not isinstance(path, list):
                        print("descend: no path to the warp at %s (%s)" % (w, why))
                        return False
                tgt = pick_on_path(st, path, args.hop, bad)
                if tgt is None:
                    print("descend: no hop along the path to the warp at %s" % (w,))
                    return False
        else:
            fr = {r: rect for r, rect in st.frontier(lid0) if r not in skip}
            if goal not in fr:
                if not fr:
                    print("descend: every room activated or skipped, no warp %d" % args.descend)
                    return False
                goal = min(fr, key=lambda r: math.hypot(room_centre(fr[r])[0] - px, room_centre(fr[r])[1] - py))
            tgt = greedy_hop(st, room_centre(fr[goal]), args.hop, args.min_hop, bad)
            if tgt is None:
                tgt = greedy_hop(st, room_centre(fr[goal]), 1.6 * args.hop, args.min_hop, bad)
            if tgt is None:
                skip.add(goal)
                goal = None
                continue
        p.teleport(tgt[0] - px, tgt[1] - py)
        time.sleep(args.wait)
        st.poll()
        if math.hypot(st.pos[0] - px, st.pos[1] - py) < 3:
            bad.add(tgt)
            still += 1
            if still in (4, 8):
                print("descend: %d hops without moving at %s (mana %.2f)" % (still, st.pos[:2], p.mana() or 0))
            if still >= 12:
                print("descend: stuck; give up")
                return False
        else:
            still = 0
    print("descend: time out")
    return False


def cmd_farm(args):
    """One short session at a fixed target (plan 0019 Phase 2): waypoint travel (--wp TAB,ROW), Energy Shield, then
    the kill loop. Each step, in this order: Nova when a live, not lightning-immune monster stands within --radius
    (the NovaGate test); else one Teleport hop towards the nearest live, not immune boss of the scan (unique,
    champion or superunique, near or far), to a standable cell at least --min-hop sub-tiles away that gets at least
    3 sub-tiles closer; else, before any boss has been seen, one exploration hop towards the nearest unactivated
    room. A boss that --chase hops in a row towards it bring no nearer is given up, and a boss whose lightning
    resist is --max-res or more (75: Nova barely scratches it) is not chased at all. With --descend REC the session
    first takes that warp (descend()). Exploration hops go to one unactivated room at a time (greedy_hop: each hop
    strictly nearer), so neither phase can shuttle between two cells. The loop ends when a boss has
    died and no live, not immune boss is left (after --linger seconds), at a level change (death), or after --time
    seconds. It never hops while something it can hurt is in range, so it cannot shuttle between two cells."""
    st = LogState(args.log)
    p = Pilot(args)
    t0 = time.time()
    while time.time() - t0 < 30:
        st.poll()
        if st.pos:
            break
        time.sleep(0.2)
    if not st.pos:
        print("farm: no PLR yet")
        return 1
    if args.players:
        # /players N in the chat line (the steps file's typing can land before the game takes keys)
        p.dpy.key("Return")
        time.sleep(0.3)
        p.dpy.key("slash")
        p.dpy.type("players")
        p.dpy.key("space")
        p.dpy.type(str(args.players))
        time.sleep(0.1)
        p.dpy.key("Return")
        time.sleep(0.4)
    if args.wp:
        tab, row = (int(v) for v in args.wp.split(","))
        if wp_travel(args, st, p, tab, row):
            return 1
        time.sleep(0.4)
    st.poll()
    gate = NovaGate(args.radius, args.give_up)
    p.nova_hold = args.nova_hold
    p.nova_key, p.es_key = args.nova_key, args.es_key
    if p.nova_key:
        p.dpy.key(p.nova_key)
    if args.descend is not None:
        if not descend(args, st, p, gate, time.time() + args.descend_time):
            print("farm done (no way down)")
            return 0
        time.sleep(0.5)
        st.poll()
    lid0 = st.pos[2]
    wd = Watchdog(args, st, p)
    boss_cls = {int(c) for c in args.boss_cls.split(",")} if args.boss_cls else set()
    seen, dead, chase = {}, set(), {}
    t_es = None
    t_mana = 0
    npot = 0
    xskip, xgoal = set(), None
    casts = hops = explore = 0
    t1 = time.time()
    t_done = None
    why_end = "time"
    while time.time() - t1 < args.time:
        st.poll()
        if st.pos[2] != lid0:
            why_end = "level %s -> %s" % (lid0, st.pos[2])
            break
        if wd.check("farm: %d casts, %d hops at %s" % (casts, hops, st.pos[:2])) == 2:
            why_end = "stalled twice"
            break
        upkeep(args, p)
        if gate.cast(p, st):
            casts += 1
            continue
        px, py = st.pos[0], st.pos[1]
        scan = {m["id"]: m for m in st.far.values()}
        scan.update({m["id"]: m for m in st.mon})
        for m in scan.values():
            if (m.get("mf") or 0) & 0x0E or m["cls"] in boss_cls:
                if m["id"] not in seen:
                    print("boss %d class %d mods %s lightning resist %s at %.0f%s" % (
                        m["id"], m["cls"], m["mods"], m["lr"], math.hypot(m["x"] - px, m["y"] - py),
                        "; skipped (resist at or above --max-res)" if (m["lr"] or 0) >= args.max_res else ""))
                seen[m["id"]] = m
                if not live(m) and m["id"] not in dead:
                    dead.add(m["id"])
                    print("boss %d class %d down after %.0f s" % (m["id"], m["cls"], time.time() - t1))
        want = [m for m in seen.values() if m["id"] not in dead and m["id"] not in gate.ignored and not immune(m)
                and (m["lr"] or 0) < args.max_res and chase.get(m["id"], (0, None))[0] < args.chase]
        if boss_cls:
            want = [m for m in want if m["cls"] in boss_cls]      # chase only those; the rest die when in range
        if args.sweep and not want:
            # after the bosses: any live monster Nova can hurt, then unactivated rooms, until --time
            want = [m for m in st.mon if live(m) and not immune(m) and (m["lr"] or 0) < args.max_res
                    and m["id"] not in gate.ignored and chase.get(m["id"], (0, None))[0] < args.chase]
        hunting = boss_cls and not any(seen[i]["cls"] in boss_cls for i in dead)
        if not want and hunting and explore >= args.hops:
            why_end = "no --boss-cls monster down after %d exploration hops" % explore
            break
        if not want and not hunting and not args.sweep:          # a sweep ends only by the clock
            if dead:
                if t_done is None:
                    t_done = time.time()
                if time.time() - t_done >= args.linger:
                    why_end = "bosses down"
                    break
                time.sleep(0.3)
                continue
            if seen or explore >= args.hops:
                why_end = "no target left" if seen else "nothing found"
                break
        if not want:
            fr = {r: rect for r, rect in st.frontier(lid0) if r not in xskip}
            if xgoal not in fr:
                if not fr:
                    why_end = "nothing found (level explored)"
                    break
                xgoal = min(fr, key=lambda r: math.hypot(room_centre(fr[r])[0] - px, room_centre(fr[r])[1] - py))
            tgt = greedy_hop(st, room_centre(fr[xgoal]), args.hop, args.min_hop)
            if tgt is None:
                xskip.add(xgoal)
                xgoal = None
                continue
            explore += 1
        else:
            t_done = None
            m = min(want, key=lambda m: math.hypot(m["x"] - px, m["y"] - py))
            d = math.hypot(m["x"] - px, m["y"] - py)
            n, d0 = chase.get(m["id"], (0, None))
            chase[m["id"]] = (0 if d0 is None or d < d0 - 2 else n + 1, d)   # hops that got no nearer
            best = None
            for y in range(py - int(args.hop), py + int(args.hop) + 1):
                for x in range(px - int(args.hop), px + int(args.hop) + 1):
                    r = math.hypot(x - px, y - py)
                    if r > args.hop or r < args.min_hop or not standable(st.cells, x, y) or near_warp(st, x, y):
                        continue
                    e = math.hypot(x - m["x"], y - m["y"])
                    if e <= d - 3 and (best is None or e < best[0]):
                        best = (e, (x, y))
            if best is None:
                path, why = plan(st, args.hop, set(), targets=[(None, [m["x"] // 5 - 1, m["y"] // 5 - 1, 3, 3])],
                                 want_path=True)
                tgt = pick_on_path(st, path, args.hop, set()) if isinstance(path, list) else path
                if tgt is None or math.hypot(tgt[0] - px, tgt[1] - py) < args.min_hop:
                    print("no way to boss %d (class %d); give it up" % (m["id"], m["cls"]))
                    gate.ignored.add(m["id"])
                    continue
            else:
                tgt = best[1]
        p.teleport(tgt[0] - px, tgt[1] - py)
        hops += 1
        time.sleep(args.wait)
    st.poll()
    print("farm done (%s) after %.0f s: %d casts, %d hops (%d exploring); bosses seen %d, down %d, given up %d" % (
        why_end, time.time() - t1, casts, hops, explore, len(seen), len(dead), len(gate.ignored)))
    return 0


def cmd_mons(args):
    st = LogState(args.log)
    st.poll()
    if not st.pos:
        print("no PLR yet")
        return 1
    px, py = st.pos[0], st.pos[1]
    for m in sorted(st.mon, key=lambda m: math.hypot(m["x"] - px, m["y"] - py)):
        print("%6d cls=%4d mode=%2d d=%5.1f hp=%s lr=%s mf=%s mods=%s" % (
            m["id"], m["cls"], m["mode"], math.hypot(m["x"] - px, m["y"] - py), m["hp"], m["lr"], m["mf"], m["mods"]))
    print("warps:", {hex(r): w for r, w in st.warps.items() if st.rl.get(r, (None,))[0] == st.lptr.get(st.pos[2])})
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("where", "explore", "hop", "farm", "mons", "wp"))
    ap.add_argument("log")
    ap.add_argument("dx", nargs="?", type=int, default=0)
    ap.add_argument("dy", nargs="?", type=int, default=0)
    ap.add_argument("--slot", type=int, help="harness slot: display :7+N (tools/slots.py); default 0 (:7)")
    ap.add_argument("--display", help="X display (default: the slot's; :7 without --slot)")
    ap.add_argument("--cx", type=int, default=400)
    ap.add_argument("--cy", type=int, default=290)
    ap.add_argument("--hops", type=int, default=200)
    ap.add_argument("--hop", type=float, default=10.0)
    ap.add_argument("--wait", type=float, default=0.45)
    ap.add_argument("--nova", type=int, default=2)
    ap.add_argument("--potion", type=int, default=0)
    ap.add_argument("--es", type=float, default=0, help="cast Energy Shield every this many seconds (0: never)")
    ap.add_argument("--es-swap", type=int, default=1, help="1: Energy Shield is the swap set's right skill")
    ap.add_argument("--drink", type=float, default=0.6, help="drink a belt potion below this life-orb fill")
    ap.add_argument("--to-pdef", help="go to the room of this LvlPrest Def (or any of a comma-separated list) in the "
                                      "current level, then stop")
    ap.add_argument("--to-warp", action="store_true", help="go to a room of the current level that has a warp, then stop")
    ap.add_argument("--blind-nova", action="store_true",
                    help="the old behaviour: Nova every --nova hops whatever is (or is not) in range")
    ap.add_argument("--radius", type=float, default=9.0, help="Nova range in sub-tiles for the target test")
    ap.add_argument("--give-up", type=int, default=6, help="abandon a target after this many casts with no life change")
    ap.add_argument("--burst", type=int, default=8, help="most Nova casts in a row at one stop")
    ap.add_argument("--cast-wait", type=float, default=0.35)
    ap.add_argument("--shots")
    ap.add_argument("--stall", type=float, default=20.0,
                    help="watchdog: seconds with neither the log nor the position changing before a STALL line")
    ap.add_argument("--wp-x", type=int, default=712, help="wp: the town waypoint (screenshot x)")
    ap.add_argument("--wp-tab-x0", type=int, default=115, help="wp: x of the first act tab (classic: 120)")
    ap.add_argument("--wp-tab-w", type=int, default=62, help="wp: act tab spacing (5 tabs: 62; classic, 4 tabs: 78)")
    ap.add_argument("--wp-y", type=int, default=62, help="wp: the town waypoint (screenshot y)")
    ap.add_argument("--shot-every", type=int, default=25)
    ap.add_argument("--wp", help="farm: waypoint travel first, 'TAB,ROW' of the waypoint list (e.g. 5,2)")
    ap.add_argument("--time", type=float, default=90, help="farm: end the kill loop after this many seconds")
    ap.add_argument("--linger", type=float, default=2.0, help="farm: seconds to stay after the last boss died")
    ap.add_argument("--chase", type=int, default=8, help="farm: give a boss up after this many hops that got no nearer to it")
    ap.add_argument("--min-hop", type=float, default=5.0, help="farm: shortest Teleport hop (sub-tiles)")
    ap.add_argument("--nova-hold", type=float, default=1.6,
                    help="farm: seconds the right button stays down per Nova burst (the game recasts at its cast rate)")
    ap.add_argument("--mana-drink", type=float, default=0.3, help="farm: drink from --mana-col below this mana-orb fill")
    ap.add_argument("--mana-col", type=int, default=4, help="farm: the belt column (hot key) holding mana potions; 0: none")
    ap.add_argument("--descend", type=int, help="farm: after the waypoint, find and take the warp of this LvlWarp row "
                                                "(67: Durance of Hate 2 -> 3) before the kill loop")
    ap.add_argument("--descend-time", type=float, default=150, help="farm: give the --descend search this long")
    ap.add_argument("--boss-cls", help="farm: MonStats rows that count as bosses besides the unique/champion flags "
                                       "(e.g. 242 Mephisto)")
    ap.add_argument("--sweep", action="store_true", help="farm: after the bosses keep killing whatever is near and "
                                                        "exploring, in the same game, until --time")
    ap.add_argument("--nova-key", help="farm: the F-key bound to Nova in the save (e.g. F1), pressed before every burst")
    ap.add_argument("--es-key", help="farm: the F-key bound to Energy Shield (e.g. F2); replaces the weapon swap")
    ap.add_argument("--players", type=int, default=0, help="farm: type /players N first (0: no)")
    ap.add_argument("--max-res", type=float, default=75, help="farm: skip a boss whose lightning resist is this or more")
    ap.add_argument("--loot", type=float, default=0, help="explore: operate the containers within this many sub-tiles "
                                                          "before each hop (needs tools/gdb/objects.py's lines; plan 0023)")
    ap.add_argument("--loot-max", type=int, default=4, help="explore: most containers operated at one stop")
    ap.add_argument("--loot-wait", type=float, default=2.5, help="explore: seconds to wait for the operate (OO0) line")
    ap.add_argument("--loot-dy", type=int, default=20, help="explore: click this many pixels above the object's cell")
    ap.add_argument("--excel", default=os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel"))
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    import slots
    try:
        args.slot, args.display = slots.pick_display(args.slot, args.display)
    except slots.SlotError as e:
        ap.error(str(e))
    args.shot_tag = "" if args.slot in (None, 0) else slots.suffix(args.slot)
    print("d2pilot: slot %s, display %s" % ("-" if args.slot is None else args.slot, args.display), file=sys.stderr)
    return {"where": cmd_where, "explore": cmd_explore, "hop": cmd_hop, "farm": cmd_farm,
            "mons": cmd_mons, "wp": cmd_wp}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
