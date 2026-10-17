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
    python3 -I tools/d2pilot.py wpchain <run.log> --chain "4,2 4,3 5,2" [--linger S]   # waypoint to waypoint
    python3 -I tools/d2pilot.py players <run.log> <n>            # type /players n in the chat line
    python3 -I tools/d2pilot.py npc <run.log> <name> trade|gamble|hire [--repeat N] [--stay]   # a town NPC's menu
    python3 -I tools/d2pilot.py npc <run.log> charsi imbue|larzuk socket|anya personalize --item inv:c,r[,w,h]
                                                                 # plan 0032: a quest item service on one item
    python3 -I tools/d2pilot.py objop <run.log> --obj-cls C [--to-pdef DEFS] [--approach] [--times N --done TAG]
                                                                 # plan 0032: reach and operate an object (the Hellforge)
    python3 -I tools/d2pilot.py hunt <run.log> --mon-cls C [--time S]   # plan 0032: reach and kill one monster class
    python3 -I tools/d2pilot.py insert <run.log> TOKEN...        # inventory actions (tools/gdb/sockets.gdb log):
        A>B (insert the item at cell A into the item whose footprint is B), key:K, click:CELL, rclick:CELL,
        xy:X,Y (a click at window coordinates), sleep:S, shot:PATH; CELL = inv:c,r[,w,h] | cube:c,r[,w,h] (the cube open) | eq:head|tors|rarm|larm|...
    python3 -I tools/d2pilot.py cube <run.log> [--plan FILE] TOKEN...   # Horadric Cube sessions (tools/gdb/cube.gdb
        log): the insert tokens, plus mv:A>B (move an item), tm (press Transmute, wait for CUBX), drop:CELL

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
TOWNS = (1, 40, 75, 103, 109)       # Levels ids of the five towns


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
        self.any_level = False      # explore --any-level: the frontier spans every level with an activated room
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
        self.npcs = {}              # MonStats class -> [(unit id, mode, x, y)] (NPC lines, tools/gdb/vendors.py)
        self.objs_xy = []           # every object unit's position (OBJS lines, tools/gdb/vendors.py)
        self.objs_cls = []          # the same with the object class: [class, x, y]
        self.visited = set()        # (level id, x // 10, y // 10) of every PLR line

    def poll(self):
        data = self.f.read()
        if not data:
            return
        data = self.buf + data
        lines = data.split("\n")
        self.buf = lines.pop()
        for line in lines:
            tag, _, rest = line.partition(" ")
            if tag not in ("PLR", "RL", "RRESEED", "CB", "SMA0", "SU0", "MON", "WRP", "OU0", "OUX", "OO0", "MZ1", "NPC",
                           "OBJS"):
                continue
            try:
                d = json.loads(rest)
            except ValueError:
                continue
            if tag == "PLR":
                self.pos = (d["x"], d["y"], d["lid"], d["room"])
                self.visited.add((d["lid"], d["x"] // 10, d["y"] // 10))
                self.n_plr += 1
            elif tag == "RL":
                self.rl[d["room"]] = (d["level"], d["rect"])
                self.active.discard(d["room"])      # a rebuilt level can reuse a freed room's address
                self.pdef[d["room"]] = d.get("pdef")
                if d.get("warps"):
                    self.warps[d["room"]] = d["warps"]
            elif tag == "MZ1":                  # drlg-gen.py: the maze generator's own rooms, freed after the conversion
                for r in d["rooms"]:
                    self.rl.pop(r[0], None)
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
            elif tag == "OBJS":
                self.objs_xy = [(x, y) for _, x, y in d["o"]]
                self.objs_cls = d["o"]
            elif tag == "NPC":
                npcs = {}
                for c, i, m, x, y in d["n"]:
                    npcs.setdefault(c, []).append((i, m, x, y))
                self.npcs = npcs

    def frontier(self, lid):
        if self.any_level:
            lps = {self.rl[r][0] for r in self.active if r in self.rl}
            return [(r, rect) for r, (p, rect) in self.rl.items() if p in lps and r not in self.active]
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


class MeleeGate:
    """plan 0034 Phase 2: a character without Nova. Left-clicks the nearest live monster within radius (the left
    skill, Attack: the character walks to it and strikes), whatever its resists; a monster whose life has not moved
    after --give-up clicks is ignored from then on."""

    def __init__(self, radius, give_up, button=1, hold=0.12):
        self.radius, self.give_up = radius, give_up
        self.button, self.hold = button, hold     # plan 0037 Phase 2: Attack on the right button (Teleport on the left)
        self.casts = {}
        self.ignored = set()
        self.skipped_immune = 0

    def cast(self, p, st):
        if not st.pos or st.pos[2] in TOWNS:     # town NPCs are monsters too: a click would talk to them
            return False
        px, py = st.pos[0], st.pos[1]
        t = sorted((m for m in st.mon if live(m) and m["id"] not in self.ignored
                    and math.hypot(m["x"] - px, m["y"] - py) <= self.radius),
                   key=lambda m: math.hypot(m["x"] - px, m["y"] - py))
        if not t:
            return False
        m = t[0]
        n, hp0 = self.casts.get(m["id"], (0, m["hp"]))
        if n >= self.give_up and m["hp"] == hp0:
            self.ignored.add(m["id"])
            return True
        if m["hp"] != hp0:
            n, hp0 = 0, m["hp"]
        self.casts[m["id"]] = (n + 1, hp0)
        sx, sy = p.screen(m["x"] - px, m["y"] - py)
        sx, sy = max(10, min(790, sx)), max(10, min(int(540 * p.vs), sy))
        p.dpy.click(p.off[0] + int(sx), p.off[1] + int(sy) - 20, button=self.button, hold=self.hold)
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
        vh = getattr(args, "view_h", 571)
        self.vs = (vh or self.frame_rows()) / 571.0   # screen samples: rows shown / the 571 the offsets were taken on

    def screen(self, dx, dy):
        sx = self.cx + 16 * (dx - dy)
        sy = self.cy + 8 * (dx + dy)
        return sx, sy

    walk = False                    # explore --any-level in a town: Teleport is not allowed there, walk instead

    def teleport(self, dx, dy):
        sx, sy = self.screen(dx, dy)
        sx, sy = max(10, min(790, sx)), max(10, min(int(540 * self.vs), sy))
        if self.walk:
            self.dpy.click(self.off[0] + int(sx), self.off[1] + int(sy), button=1, hold=0.12)
            time.sleep(1.2)
            return
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
        x0, y0, w, h = self.off[0] + x, self.off[1] + int(round(496 * self.vs)), 45, int(round(60 * self.vs))
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
        return rows / (56.0 * self.vs)

    def frame_rows(self):
        """--view-h 0: the rows the game frame fills on screen (the lowest row with non-black pixels + 1)."""
        import xdrive
        rh = xdrive.X11.XDisplayHeight(self.dpy.d, 0)
        n = max(1, min(200, rh - self.off[1] - 400))     # rows of the window below y 400 that are on the screen
        raw, bpl = self.grab(0, 400, 800, n)
        last = 400
        for y in range(n):
            line = raw[y * bpl: y * bpl + 3200] if raw else b""
            if any(line[4 * x] > 20 or line[4 * x + 1] > 20 or line[4 * x + 2] > 20 for x in range(0, 800, 8)):
                last = 400 + y + 1
        return last

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
        return self.dark_share(160, int(140 * self.vs), 200, int(260 * self.vs)) > 0.75

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
    p = Pilot(args)
    if args.wp_find:
        # plan 0023: find the town waypoint among the objects the log saw created (InitFn 17), hop next to it and
        # click it where it stands on screen (needs tools/gdb/objects.py's OU0/OUX lines)
        from obj_survey import decode
        wps = {i for i, o in enumerate(decode(args.excel, "objects")) if o["InitFn"] == 17}
        px, py = st.pos[0], st.pos[1]
        cand = sorted((math.hypot(x - px, y - py), x, y) for u, (c, x, y, m) in st.objs.items() if c in wps)
        if not cand:
            print("wp: no waypoint object in the log")
            return 1
        _, x, y = cand[0]
        for _ in range(12):
            st.poll()
            px, py = st.pos[0], st.pos[1]
            d = math.hypot(x - px, y - py)
            if d <= 7:
                break
            k = min(10.0, d - 4) / d
            p.teleport(int(round((x - px) * k)), int(round((y - py) * k)))
            time.sleep(args.wait + 0.2)
        st.poll()
        sx, sy = p.screen(x - st.pos[0], y - st.pos[1])
        args.wp_x, args.wp_y = int(sx), int(round((sy - 12) * p.client_h / 600))
        print("wp: waypoint at (%d, %d), click (%d, %d)" % (x, y, args.wp_x, args.wp_y))
    return wp_travel(args, st, p, args.dx, args.dy)


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
    time.sleep(0.6)
    for _ in range(2):                  # a tab click right after the list opens is sometimes lost: click it twice
        p.click_at(args.wp_tab_x0 + (tab - 1) * args.wp_tab_w, 73)
        time.sleep(0.4)
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


WAYPOINT_CLASSES = {119, 145, 156, 157, 237, 238, 288, 323, 324, 398, 402, 429, 494, 496, 511, 539}  # Objects SubClass & 64


def waypoint_at(path, lid):
    """The last OBJP line (tools/gdb/drlg-maze.py) of a waypoint object in level lid: its sub-tile position."""
    pos = None
    for line in open(path, errors="replace"):
        if line.startswith("OBJP "):
            try:
                d = json.loads(line[5:])
            except ValueError:
                continue
            if d.get("cls") in WAYPOINT_CLASSES and d.get("lid") == lid and d.get("x") is not None:
                pos = (d["x"], d["y"])
    return pos


def cmd_wpchain(args):
    """Plan 0026 Phase 2: a chain of waypoint hops (--chain "TAB,ROW TAB,ROW ..."), each from the waypoint the
    character stands at. Per hop: the waypoint's position from the log (OBJP), else the player's own; click it at a few
    offsets until the list is up (no Escape between tries; a Nova burst before each retry, for monsters standing on
    the waypoint), choose the tab and the row, wait for the level change, then --linger seconds for the level builds to
    settle."""
    st = LogState(args.log)
    p = Pilot(args)
    hops = [tuple(int(v) for v in h.split(",")) for h in args.chain.split()]
    done = 0
    for tab, row in hops:
        st.poll()
        if not st.pos:
            print("wpchain: no PLR yet")
            return 1
        lid0 = st.pos[2]
        opened = False
        for attempt in range(6):
            if attempt >= 1:                 # monsters on the waypoint take the clicks: clear them with Nova first
                p.nova_hold = 1.6
                p.nova()
                time.sleep(0.3)
            st.poll()
            px, py = st.pos[0], st.pos[1]
            w = waypoint_at(args.log, st.pos[2])
            wx, wy = w if w else (px, py)
            sx, sy = p.screen(wx - px, wy - py)
            off = [(0, -12), (0, -30), (12, -20), (-12, -20), (0, 4), (0, -45)][attempt]
            sx, sy = max(10, min(790, sx + off[0])), max(10, min(int(540 * p.vs), sy + off[1]))
            p.click_at(sx, sy)
            t0 = time.time()
            while time.time() - t0 < 3:
                if p.menu_open():
                    opened = True
                    break
                time.sleep(0.1)
            if opened:
                break
            print("wpchain: hop %d,%d: the list did not open (try %d at %d,%d; waypoint %s, player %s)" % (
                tab, row, attempt + 1, sx, sy, w, (px, py)))
            sys.stdout.flush()
        if not opened:
            if args.shots:
                p.shot(os.path.join(args.shots, "wpchain-fail-%d.png" % int(time.time())))
            print("wpchain: giving up at hop %d,%d after %d hops" % (tab, row, done))
            return 1
        time.sleep(0.3)
        for _ in range(2):              # a tab click right after the list opens is sometimes lost (as in wp_travel)
            p.click_at(args.wp_tab_x0 + (tab - 1) * args.wp_tab_w, 73)
            time.sleep(0.4)
        y = 133 + (row - 1) * 34
        p.dpy.move(p.off[0] + 230, p.off[1] + int(round(y * 600 / p.client_h)))
        time.sleep(0.1)
        p.click_at(230, y)
        t1 = time.time()
        moved = False
        while time.time() - t1 < 30:
            st.poll()
            if st.pos and st.pos[2] != lid0:
                moved = True
                break
            time.sleep(0.2)
        if not moved:
            print("wpchain: hop %d,%d: no level change (still %s)" % (tab, row, lid0))
            if args.shots:
                p.shot(os.path.join(args.shots, "wpchain-stuck-%d.png" % int(time.time())))
            return 1
        done += 1
        print("wpchain: hop %d,%d: level %s -> %s after %.1f s" % (tab, row, lid0, st.pos[2], time.time() - t1))
        sys.stdout.flush()
        t2 = time.time()                     # let the builds (and the logger) settle: the log stops growing
        size = -1
        while time.time() - t2 < 120:
            s = os.path.getsize(args.log)
            if s == size:
                break
            size = s
            time.sleep(args.linger)
        if args.shots:
            p.shot(os.path.join(args.shots, "wpchain-%02d-%d-%d.png" % (done, tab, row)))
    print("wpchain: %d hops done" % done)
    return 0


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


def type_players(p, n):
    """/players N in the chat line (the steps file's typing can land before the game takes keys)."""
    p.dpy.key("Return")
    time.sleep(0.3)
    p.dpy.key("slash")
    p.dpy.type("players")
    p.dpy.key("space")
    p.dpy.type(str(n))
    time.sleep(0.1)
    p.dpy.key("Return")
    time.sleep(0.4)



# ---------------------------------------------------------------- inventory actions (plan 0029 Phase 2)
# Window-relative geometry of the 800x600 frame, measured once on run:2026-10-15-sockets screenshots (tooling.md):
# a cell is 29 px; the inventory grid (10 x 4) starts at (418, 316), the Horadric Cube grid (3 x 4, open: right-click
# the cube) at (198, 199); the paper-doll slots are clicked at their centres.
GRIDS = {"inv": (418, 316, 10, 4), "cube": (198, 199, 3, 4)}
EQUIP = {"head": (562, 92), "neck": (620, 104), "rarm": (447, 163), "tors": (562, 177), "larm": (678, 163),
         "glov": (447, 266), "belt": (562, 252), "feet": (678, 266), "rrin": (505, 252), "lrin": (620, 252)}
CELL = 29


def cell_xy(spec):
    """'inv:c,r[,w,h]' / 'cube:c,r[,w,h]' -> the centre of that w x h footprint (1 x 1 by default); 'eq:SLOT' -> the
    paper-doll slot."""
    page, _, rest = spec.partition(":")
    if page == "eq":
        return EQUIP[rest]
    x0, y0, cols, rows = GRIDS[page]
    v = [int(t) for t in rest.split(",")]
    c, r = v[0], v[1]
    w, h = (v[2], v[3]) if len(v) == 4 else (1, 1)
    if not (0 <= c and c + w <= cols and 0 <= r and r + h <= rows):
        raise ValueError("%s: outside the %s grid" % (spec, page))
    return x0 + CELL * c + CELL * w // 2, y0 + CELL * r + CELL * h // 2


def log_tail(path, start):
    with open(path, errors="replace") as f:
        f.seek(start)
        return f.read(), f.tell()


def insert_outcome(text):
    """What the game did with the last click, from tools/gdb/sockets.gdb lines: ('inserted'|'refused'|'swap'|'none',
    detail)."""
    for line in text.splitlines():
        tag, _, rest = line.partition(" ")
        if tag == "INSX":
            try:
                d = json.loads(rest)
            except ValueError:
                continue
            return ("inserted" if d.get("ret") else "refused"), "ret %s nf %s" % (d.get("ret"), d.get("nf"))
    for line in text.splitlines():
        tag, _, rest = line.partition(" ")
        if tag == "PKT":
            try:
                d = json.loads(rest)
            except ValueError:
                continue
            if d.get("op") in (0x1F, 0x18, 0x20, 0x1D):
                return "swap", "client packet 0x%02x" % d["op"]
    return "none", "no packet"


def cmd_insert(args, tokens):
    """Play a list of inventory tokens (see main): A>B inserts the item at A into the item whose footprint is B (pick A
    up, click B's centre), waits for the logger's answer and prints it. When the client swapped the two instead (it
    sends 0x1F, not the insert 0x28), the swap is undone: click B's centre again (the parent goes back, the child
    comes up), then A (the child goes back)."""
    p = Pilot(args)
    pos = os.path.getsize(args.log) if os.path.exists(args.log) else 0
    n_ok = 0
    for tok in tokens:
        kind, _, arg = tok.partition(":") if ">" not in tok else ("ins", "", tok)
        if kind == "key":
            p.dpy.key(arg)
            time.sleep(0.6)
        elif kind == "sleep":
            time.sleep(float(arg))
        elif kind == "shot":
            p.shot(arg)
        elif kind == "xy":            # a click at window coordinates (the cube's Transmute button: xy:240,340)
            x, y = (int(v) for v in arg.split(","))
            p.dpy.click(p.off[0] + x, p.off[1] + y, button=1, hold=0.12)
            time.sleep(1.0)
        elif kind in ("click", "rclick"):
            x, y = cell_xy(arg)
            p.dpy.click(p.off[0] + x, p.off[1] + y, button=1 if kind == "click" else 3, hold=0.12)
            time.sleep(0.8)
        elif kind == "ins":
            a, b = arg.split(">")
            ax, ay = cell_xy(a)
            bx, by = cell_xy(b)
            _, pos = log_tail(args.log, pos)
            p.dpy.click(p.off[0] + ax, p.off[1] + ay, button=1, hold=0.12)
            time.sleep(args.pick_wait)
            p.dpy.click(p.off[0] + bx, p.off[1] + by, button=1, hold=0.12)
            out, det, waited = "none", "", 0.0
            text = ""
            while waited < args.ins_wait:
                time.sleep(0.25)
                waited += 0.25
                more, pos = log_tail(args.log, pos)
                text += more
                out, det = insert_outcome(text)
                if out != "none":
                    time.sleep(0.25)
                    more, pos = log_tail(args.log, pos)
                    text += more
                    break
            print("INSERT %s: %s (%s)" % (arg, out, det))
            sys.stdout.flush()
            if out == "inserted":
                n_ok += 1
            elif out == "swap":
                time.sleep(0.3)
                p.dpy.click(p.off[0] + bx, p.off[1] + by, button=1, hold=0.12)
                time.sleep(0.6)
                p.dpy.click(p.off[0] + ax, p.off[1] + ay, button=1, hold=0.12)
                time.sleep(0.6)
                more, pos = log_tail(args.log, pos)
                print("UNDO %s: %s" % (arg, ", ".join(l.split(" {")[0] + " " + l[l.find('"op"'):l.find('"op"') + 9]
                                                     for l in more.splitlines() if l.startswith("PKT"))))
            elif out == "refused":
                # the child stays on the cursor: put it back
                time.sleep(0.2)
                p.dpy.click(p.off[0] + ax, p.off[1] + ay, button=1, hold=0.12)
                time.sleep(0.6)
            time.sleep(args.ins_gap)
        else:
            raise SystemExit("insert: unknown token %r" % tok)
    print("insert: %d inserted" % n_ok)
    return 0

# ---------------------------------------------------------------- NPC menus (plan 0031 Phase 2)
# Town NPCs by name: MonStats class and the lines of their dialogue menu below the name line, in the state of the
# vendor saves (every quest done; run:2026-10-15-vendors). The menu is a translucent box drawn above the NPC, the NPC's
# name and then the options 15 px apart, the first option highlighted in blue; option k is clicked at the blue line's
# x centre and y + 15 (k - 1). Measured from the run's screenshots (tooling.md § NPC menus).
NPCS = {
    # name: (MonStats class, menu lines under the name, usual place as an offset from the town waypoint or None)
    "akara": (148, ["talk", "trade", "cancel"], None),
    "gheed": (147, ["talk", "trade", "gamble", "cancel"], None),
    "charsi": (154, ["talk", "trade", "cancel"], None),
    "kashya": (150, ["talk", "hire", "cancel"], None),
    "fara": (178, ["talk", "trade", "cancel"], (49, -7)),
    "drognan": (177, ["talk", "trade", "cancel"], (20, -52)),
    "lysander": (202, ["talk", "trade", "cancel"], (47, 27)),
    "elzix": (199, ["talk", "trade", "gamble", "cancel"], (-36, 19)),
    "greiz": (198, ["talk", "hire", "cancel"], (-35, -31)),
    "ormus": (255, ["talk", "trade", "cancel"], (-41, 36)),
    "alkor": (254, ["talk", "trade", "gamble", "cancel"], (-76, -41)),
    "asheara": (252, ["talk", "hire", "trade", "cancel"], (-125, 44)),
    "hratli": (253, ["talk", "trade", "cancel"], (-34, 117)),
    "jamella": (405, ["trade", "gamble", "cancel"], (39, 39)),
    "halbu": (257, ["trade", "cancel"], (39, 4)),
    "malah": (513, ["talk", "trade", "cancel"], (-32, -39)),
    "larzuk": (511, ["talk", "trade", "cancel"], (31, -38)),
    "anya": (512, ["talk", "trade", "gamble", "cancel"], (-8, 46)),
    "qual-kehk": (515, ["talk", "hire", "cancel"], (-56, 12)),
    "nihlathak": (514, ["talk", "gamble", "cancel"], None),
    "waypoint": (None, [], None),       # npc <log> waypoint walk: walk next to the town waypoint (OBJP lines)
}
NPC_DONE = {"trade": ("TO", lambda d: d.get("gamble") == 0), "gamble": ("GBX", None), "hire": ("HIRE", None)}
# Quest item services (plan 0032 Phase 2, tools/gdb/quests.py): with the reward pending the NPC's menu has one more line
# just before "cancel" (Charsi: talk, trade, imbue, cancel). The service opens the inventory beside a one-item box:
# the pilot picks the --item cell up, puts it into the box and presses the box's check mark, then waits for the line.
SERVICES = {"imbue": ("charsi", "IMBX"), "socket": ("larzuk", "LZY"), "personalize": ("anya", "PZ")}


def find_box(p, x0, y0, w, h, minw, maxw, pre, post, dark=0.6):
    """A framed box (an NPC menu, an NPC's speech panel, the hire list's header) in the window rectangle (x0, y0, w,
    h): (left, top, right, bottom) or None. "Bright" is a max channel above 45, "dark" below 40. A candidate top frame
    row y is the row above a dark run (at least minw - 6 px) in row y + 4 that is bright on 60 % of [a - 3, b + 3]; the
    sides are the bright columns within 3 px outside the run, bright on 90 % of the rows from y to the bottom; the
    bottom is the first row 20 or more below y that is bright on 70 % of the width, bright on 4 of the 5 pixels next
    to each side (text rows are padded) and has dark rows (50 %) 2..7 above it. The box must be minw..maxw wide, pass
    pre(left, right) and post(top, bottom), and be dark inside (a share `dark` of its sampled pixels; the scene around
    it may be bright too). The tallest box wins. Row and column prefix sums keep it to a few hundred ms."""
    raw, bpl = p.grab(x0, y0, w, h)
    if raw is None:
        return None
    B = [bytearray(w) for _ in range(h)]
    D = [bytearray(w) for _ in range(h)]
    for y in range(h):
        row = raw[y * bpl: y * bpl + 4 * w]
        by, dy = B[y], D[y]
        for x in range(w):
            m = max(row[4 * x], row[4 * x + 1], row[4 * x + 2])
            if m > 45:
                by[x] = 1
            elif m < 40:
                dy[x] = 1
    RB = []                             # row prefix sums: RB[y][x] = bright pixels in row y before x
    RD = []
    for y in range(h):
        acc, acd = [0], [0]
        for x in range(w):
            acc.append(acc[-1] + B[y][x])
            acd.append(acd[-1] + D[y][x])
        RB.append(acc)
        RD.append(acd)
    CB = [[0] * (h + 1) for _ in range(w)]          # column prefix sums of bright
    for x in range(w):
        c = CB[x]
        for y in range(h):
            c[y + 1] = c[y] + B[y][x]

    def rshare(R, y, xa, xb):           # share of row y over [xa, xb] (frame coordinates relative to x0)
        if not (0 <= y < h):
            return 0.0
        xa, xb = max(0, xa), min(w - 1, xb)
        return (R[y][xb + 1] - R[y][xa]) / float(xb - xa + 1) if xb >= xa else 0.0

    def dark_band(xa, ya, xb, yb):
        n = d = 0
        for y in range(max(0, ya), min(h, yb)):
            n += xb - xa - 5
            d += RD[y][xb - 2] - RD[y][xa + 3]
        return d / float(n) if n > 0 else 0.0

    def side(x, ya, yb):                # the brightest column within 3 px of x over rows ya..yb
        best = None
        for c in range(max(0, x - 3), min(w, x + 4)):
            v = (CB[c][yb] - CB[c][ya]) / float(max(1, yb - ya))
            if best is None or v > best[0]:
                best = (v, c)
        return best

    best = None
    tried = set()
    for y in range(0, h - 30):
        dr = D[y + 4] if y + 4 < h else None
        if dr is None:
            break
        x = 0
        while x < w:
            if not dr[x]:
                x += 1
                continue
            a = x
            while x < w and dr[x]:
                x += 1
            b = x - 1
            if b - a + 1 < minw - 6 or b - a + 1 > maxw:
                continue
            if rshare(RB, y, a - 3, b + 3) < 0.6:
                continue
            la = side(a - 2, y, min(h, y + 25))
            lb = side(b + 2, y, min(h, y + 25))
            if not la or not lb or la[0] < 0.9 or lb[0] < 0.9:
                continue
            xa, xb = la[1], lb[1]
            if (xa, xb, y // 4) in tried:
                continue
            tried.add((xa, xb, y // 4))
            if not (minw <= xb - xa <= maxw) or not pre(x0 + xa, x0 + xb):
                continue
            bot = None
            for yy in range(y + 20, h):
                if (rshare(RB, yy, xa, xb) >= 0.7 and sum(B[yy][xa + 1:xa + 6]) >= 4 and sum(B[yy][xb - 5:xb]) >= 4
                        and dark_band(xa, yy - 7, xb, yy - 2) >= 0.5):
                    bot = yy
                    break
                if (CB[xa][yy + 1] - CB[xa][yy]) == 0 and (CB[xa][min(h, yy + 3)] - CB[xa][yy]) == 0:
                    break                   # the left side ended without a bottom row
            if bot is None or not post(y0 + y, y0 + bot):
                continue
            if (CB[xa][bot] - CB[xa][y]) / float(bot - y) < 0.9 or (CB[xb][bot] - CB[xb][y]) / float(bot - y) < 0.9:
                continue
            if dark_band(xa, y + 3, xb, bot - 2) < dark:
                continue
            if best is None or bot - y > best[3] - best[1]:
                best = (x0 + xa, y0 + y, x0 + xb, y0 + bot)
    return best


def menu_box(p, sx, sy):
    """The NPC menu above the NPC's feet at screen point (sx, sy): a box 40 to 320 px wide, centred on the NPC (within
    90 px: it may have walked on since the click), ending 20 to 260 px above its feet."""
    x0, y0 = max(0, sx - 260), max(0, sy - 320)
    return find_box(p, x0, y0, min(800, sx + 260) - x0, max(1, sy - y0), 40, 320,
                    lambda xa, xb: abs((xa + xb) / 2.0 - sx) <= 90, lambda top, bot: sy - 260 <= bot <= sy - 20)


def menu_lines(p, sx, sy):
    """The NPC menu above the NPC's feet at screen point (sx, sy), found by its highlighted first option (blue text:
    blue > red + 50, > green + 40 and > 100 with red and green within 12, in rows holding 3 or more such pixels; the
    menu box itself is
    translucent and its frame is lost over a bright scene):
    (x centre, y of the first option, number of option lines) or None. The blue line needs the NPC's name 15 px above
    it (8 or more beige pixels, red above 120 and green above 100, in that band), its centre within 90 px of sx, and
    a second option line under it (searched from the top of the screen to 150 px under the click; the nearest to sx
    wins, then the lowest). The option lines are 15 px apart, and one is counted (at most 6) while its band (centre
    +-4 rows, the blue line's x extent +-40) holds 8 or more white pixels (all channels above 140)."""
    x0, y0 = max(0, sx - 220), 0
    w, h = min(800, sx + 220) - x0, max(1, min(540, sy + 150) - y0)   # the NPC may have walked since the click
    raw, bpl = p.grab(x0, y0, w, h)
    if raw is None:
        return None
    rows = {}
    for y in range(h):
        base = y * bpl
        for x in range(w):
            b, g, r = raw[base + 4 * x], raw[base + 4 * x + 1], raw[base + 4 * x + 2]
            if b > 100 and b > r + 50 and b > g + 40 and abs(r - g) <= 12:   # the menu's blue is violet-grey:
                rows.setdefault(y, []).append(x)                              # red = green (a lamp's is cyan)
    clusters = []
    for y in sorted(y for y in rows if len(rows[y]) >= 3):     # a "/" leaves single pixels above and below a line
        if clusters and y - clusters[-1][-1] <= 2:
            clusters[-1].append(y)
        else:
            clusters.append([y])
    def white(yc, xa, xb, name=False):
        n = 0
        for y in range(max(0, yc - 4), min(h, yc + 5)):
            base = y * bpl
            for x in range(max(0, xa - 40), min(w, xb + 41)):
                b, g, r = raw[base + 4 * x], raw[base + 4 * x + 1], raw[base + 4 * x + 2]
                if (r > 120 and g > 100) if name else min(b, g, r) > 140:
                    n += 1
        return n

    def options(y1, xa, xb):
        n = 1
        while n < 6 and y1 + 15 * n < h - 4 and white(y1 + 15 * n, xa, xb) >= 8:
            n += 1
        return n

    best = None
    for c in clusters:
        xs = [x for y in c for x in rows[y]]
        if not (5 <= c[-1] - c[0] + 1 <= 12) or len(xs) < 25 or not (12 <= max(xs) - min(xs) <= 140):
            continue
        yc = (c[0] + c[-1]) // 2
        if abs(x0 + (min(xs) + max(xs)) // 2 - sx) > 90:   # the menu is centred over the NPC (which may walk on)
            continue
        if white(yc - 15, min(xs), max(xs), True) < 8:     # the NPC's name above it (a waypoint's glow has none)
            continue
        n = options(yc, min(xs), max(xs))
        if n < 2:                                          # every menu has a second line (cancel at least)
            continue
        key = (abs(x0 + (min(xs) + max(xs)) // 2 - sx), -c[-1])   # nearest the NPC's x, then the lowest
        if best is None or key < best[0]:
            best = (key, yc, min(xs), max(xs), n)
    if best is None:
        return None
    _, y1, xa, xb, n = best
    return x0 + (xa + xb) // 2, y0 + y1, n


def white_count(p, x0, y0, w, h, lo=170):
    """Pixels of the window rectangle whose three channels are all above lo (white text)."""
    raw, bpl = p.grab(x0, y0, w, h)
    if raw is None:
        return 0
    n = 0
    for y in range(h):
        base = y * bpl
        for x in range(w):
            if raw[base + 4 * x] > lo and raw[base + 4 * x + 1] > lo and raw[base + 4 * x + 2] > lo:
                n += 1
    return n


def speech_box(p):
    """An NPC's speech panel (its first greeting, a quest text) at the top of the screen: 200 or more white pixels
    (text) in the window rectangle x 240..560, y 5..130 (the panel is translucent, so its frame is not reliable)."""
    return white_count(p, 240, 5, 320, 125) >= 200


def path_near(st, goal, r, hop, limit=300000):
    """A breadth-first path over the known cells without the player's blocking bits from the player to a cell within
    r sub-tiles of goal; returns the last cell of that path within hop of the player, or None."""
    px, py = st.pos[0], st.pos[1]
    start = (px, py)
    prev = {start: None}
    q = collections.deque([start])
    end = None
    while q and len(prev) < limit:
        c = q.popleft()
        if math.hypot(c[0] - goal[0], c[1] - goal[1]) <= r:
            end = c
            break
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + ddx, c[1] + ddy)
            if n in prev:
                continue
            v = st.cells.get(n)
            if v is None or v & BLOCK:
                continue
            prev[n] = c
            q.append(n)
    if end is None:
        return None
    path = []
    while end is not None:
        path.append(end)
        end = prev[end]
    path.reverse()
    pick = None
    for c in path[1:]:              # the last path cell within hop (walking finds its own way between them)
        if math.hypot(c[0] - px, c[1] - py) > hop:
            break
        if not clickable(st, c, goal):
            continue
        pick = c
    return pick


def explore_step(st, hop, far=30, limit=400000):
    """The next walking click towards the nearest cell (by path length over cells of the player's level free of the
    player's blocking bits) that is `far` sub-tiles or more from every cell the player has been on in this level (PLR
    lines); False when no such cell is reachable, None when no clickable cell lies on the path within hop."""
    px, py, lid = st.pos[0], st.pos[1], st.pos[2]
    vis = {(vx, vy) for vl, vx, vy in st.visited if vl == lid}
    k = far // 10 + 1

    def fresh(c):
        gx, gy = c[0] // 10, c[1] // 10
        for ax in range(gx - k, gx + k + 1):
            for ay in range(gy - k, gy + k + 1):
                if (ax, ay) in vis and math.hypot(10 * ax + 5 - c[0], 10 * ay + 5 - c[1]) < far:
                    return False
        return True

    tiles = set()                       # the level's own tiles: the search never leaves the town
    for r, (lp, rect) in st.rl.items():
        if lp == st.lptr.get(lid):
            for tx in range(rect[0], rect[0] + rect[2]):
                for ty in range(rect[1], rect[1] + rect[3]):
                    tiles.add((tx, ty))
    start = (px, py)
    prev = {start: None}
    q = collections.deque([start])
    end = None
    while q and len(prev) < limit:
        c = q.popleft()
        if fresh(c):
            end = c
            break
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + ddx, c[1] + ddy)
            if n in prev or (tiles and (n[0] // 5, n[1] // 5) not in tiles):
                continue
            v = st.cells.get(n)
            if v is None or v & BLOCK:
                continue
            prev[n] = c
            q.append(n)
    if end is None:
        return False
    path = []
    while end is not None:
        path.append(end)
        end = prev[end]
    path.reverse()
    pick = None
    for c in path[1:]:
        if math.hypot(c[0] - px, c[1] - py) > hop:
            break
        if clickable(st, c):
            pick = c
    return pick


def clickable(st, c, goal=None, r=2):
    """A walking click on cell c would not land on a unit or take a warp: no object (OBJS), no NPC other than at goal
    and no warp (WRP; a town's sewer or cellar entrance) within r sub-tiles (sprites stand above their cells, so the
    test is generous)."""
    if near_warp(st, c[0], c[1], r + 2):
        return False
    for x, y in st.objs_xy:
        if abs(x - c[0]) <= r and abs(y - c[1]) <= r:
            return False
    for units in st.npcs.values():
        for _, _, x, y in units:
            if goal and math.hypot(x - goal[0], y - goal[1]) < 3:
                continue
            if abs(x - c[0]) <= r and abs(y - c[1]) <= r:
                return False
    return True


def hire_box(p):
    """The hire list ("Hire which Mercenary?"): 600 or more white pixels (its rows of names and prices) in the window
    rectangle x 180..620, y 125..360."""
    return white_count(p, 180, 125, 440, 235) >= 600


def walk_to_wp(args):
    """Walk until the town waypoint (the last OBJP line of a waypoint class in the player's level) is within 4
    sub-tiles."""
    st = LogState(args.log)
    p = Pilot(args)
    t0 = time.time()
    while time.time() - t0 < args.npc_time:
        st.poll()
        w = waypoint_at(args.log, st.pos[2]) if st.pos else None
        if not w:
            time.sleep(0.5)
            continue
        px, py = st.pos[0], st.pos[1]
        dx, dy = w[0] - px, w[1] - py
        d = math.hypot(dx, dy)
        if d <= 4:
            print("npc: at the waypoint (%d, %d), player (%d, %d)" % (w[0], w[1], px, py))
            return 0
        tgt = path_near(st, (w[0], w[1] + 2), 3, args.hop)
        if tgt is not None:
            sx, sy = p.screen(tgt[0] - px, tgt[1] - py)
        else:
            k = min(args.hop, d) / d
            sx, sy = p.screen(dx * k, dy * k + 2)
        p.dpy.click(p.off[0] + int(max(10, min(790, sx))), p.off[1] + int(max(10, min(520, sy))), button=1, hold=0.12)
        time.sleep(args.walk_wait)
    print("npc: the waypoint was not reached")
    return 1


def log_still(path, secs=0.9):
    """True when the log did not grow for secs: in single player an open game menu pauses the game, and with it the
    TICK heartbeat of tools/gdb/vendors.py (every 0.5 s while the server runs)."""
    a = os.path.getsize(path)
    time.sleep(secs)
    return os.path.getsize(path) == a


def escape(p, log, close_menu=True):
    """Escape (closes an NPC menu, a speech, a trade/gamble/hire window); if that left the game paused (no window was
    open, so the game menu came up; or a submenu of it), Escape again until the log grows, at most 4 times."""
    p.dpy.key("Escape")
    time.sleep(0.4)
    if not close_menu:
        return True
    for _ in range(4):
        if not log_still(log):
            return True
        print("npc: the game is paused (its menu is open): Escape")
        p.dpy.key("Escape")
        time.sleep(0.5)
    return not log_still(log)


HIRE_ROW0, HIRE_DY, HIRE_YES = (300, 140), 34, (300, 149)   # hire list rows (window, 800x600); the replace box's Yes


def hire_buy(p, log, row):
    """Hire the list row `row` (the list is open): click it; when the player already has a mercenary the game asks
    "This Mercenary will replace your current one" (Yes / No), so without an HHI line (HIRE_Hire, tools/gdb/
    hirelings.py) within 1.5 s click Yes. True once the HHX line (HIRE_Hire's return) is in the log."""
    start = os.path.getsize(log)
    x, y = HIRE_ROW0[0], HIRE_ROW0[1] + HIRE_DY * (row - 1)
    p.dpy.move(p.off[0] + x, p.off[1] + y)
    time.sleep(0.15)
    p.dpy.click(p.off[0] + x, p.off[1] + y, button=1, hold=0.1)

    def seen(tg):
        text, _ = log_tail(log, start)
        return any(ln.startswith(tg + " ") for ln in text.splitlines())
    t0 = time.time()
    while time.time() - t0 < 1.5 and not seen("HHI"):
        time.sleep(0.2)
    if not seen("HHI"):
        p.dpy.click(p.off[0] + HIRE_YES[0], p.off[1] + HIRE_YES[1], button=1, hold=0.1)
    t0 = time.time()
    while time.time() - t0 < 4.0:
        if seen("HHX"):
            return True
        time.sleep(0.2)
    return False


def cmd_npc(args):
    """Walk to a town NPC by its logged position (NPC lines of tools/gdb/vendors.py), click it, wait for its menu box,
    click the menu line of the action, and wait for the confirmation (trade: a TO line with gamble 0; gamble: GBX, the
    gamble window built; hire: the hire list on the screen, which the client opens without a packet; HIRE_BuildStock
    runs when the NPC is first clicked). --repeat N does it N times, closing the window with Escape after
    each (a gamble refresh: the close frees the gamble inventory). --stay leaves the last window open."""
    name, action = args.npc_name.lower(), args.npc_action
    if name not in NPCS:
        print("npc: unknown NPC %r (%s)" % (name, ", ".join(sorted(NPCS))))
        return 1
    cls, menu, hint = NPCS[name]
    if hint and not args.hint:
        args.hint = "%d,%d" % hint
    if name == "waypoint":
        return walk_to_wp(args)
    if action in SERVICES:
        if SERVICES[action][0] != name:
            print("npc: %s is %s's service" % (action, SERVICES[action][0]))
            return 1
        if not args.item:
            print("npc: %s needs --item CELL (the inventory cell of the item)" % action)
            return 1
        menu = menu[:-1] + [action, menu[-1]]
    line = args.menu_line or (menu.index(action) + 1 if action in menu else None)
    if line is None:
        print("npc: %s has no %s line (menu %s); pass --menu-line" % (name, action, menu))
        return 1
    st = LogState(args.log)
    p = Pilot(args)
    p.walk = True
    tag = "-" + args.shot_tag if args.shot_tag else ""
    done_tag, done_ok = NPC_DONE.get(action, (None, None))
    if action in SERVICES:
        done_tag, done_ok = SERVICES[action][1], None

    def npc_pos():
        st.poll()
        units = st.npcs.get(cls) or []
        if not units or not st.pos:
            return None
        px, py = st.pos[0], st.pos[1]
        return min(units, key=lambda u: math.hypot(u[2] - px, u[3] - py))

    ok = 0
    still = [None, 0, -1]               # the player's cell after the last walking click, how often it repeated, the
    # log size then

    def jitter(tgt):
        if still[1] < 2 or not st.pos:
            return tgt
        px, py = st.pos[0], st.pos[1]
        if still[1] % 2 == 0 and math.hypot(tgt[0] - px, tgt[1] - py) > 4:   # first a short step the same way (a
            k = 3.5 / math.hypot(tgt[0] - px, tgt[1] - py)                    # roof over the far cell eats clicks)
            c = (int(round(px + (tgt[0] - px) * k)), int(round(py + (tgt[1] - py) * k)))
            if st.cells.get(c, BLOCK) & BLOCK == 0:
                return c
        for _ in range(60):
            a, r = random.uniform(0, 2 * math.pi), random.uniform(2, 6)
            c = (int(px + r * math.cos(a)), int(py + r * math.sin(a)))
            if standable(st.cells, *c) and clickable(st, c):
                return c
        return tgt

    def walked():
        """After a walking click: False when the player has not moved over 8 clicks in a row (a click opened a panel,
        or the way is blocked): the caller stops, leaving the screen as it is for a look. From the second click
        without a move, the next walking click goes to a random free cell nearby (some spots, such as a roof over the
        target, take a click without a walk)."""
        st.poll()
        cur = st.pos[:2] if st.pos else None
        still[1] = still[1] + 1 if cur == still[0] else 0
        still[0] = cur
        size = os.path.getsize(args.log)
        if size == still[2]:                # no TICK since the last click: the game is paused, its menu is up (a
            print("npc: the game is paused (its menu is open): Escape")    # stray Escape); close it before walking
            escape(p, args.log)
        still[2] = os.path.getsize(args.log)
        if still[1] >= 8:
            print("npc: %s: the player has not moved over 8 walking clicks; stopping" % name)
            if args.shots:
                p.shot(os.path.join(args.shots, "npc%s-%s-stuck.png" % (tag, name)))
            return False
        return True

    for rep in range(args.repeat):
        t0 = time.time()
        opened = False
        while time.time() - t0 < args.npc_time and not opened:
            u = npc_pos()
            if u is None:
                if not st.pos:
                    time.sleep(0.5)
                    continue
                # not seen yet: its room is not active. Walk towards the nearest room of the town that has not
                # been activated (the NPC units exist only in active rooms)
                px, py = st.pos[0], st.pos[1]
                if st.pos[2] not in TOWNS:
                    print("npc: the player left the town (level %s); stopping" % st.pos[2])
                    return 1
                w = waypoint_at(args.log, st.pos[2])
                if w and args.hint:             # first towards the NPC's usual place, by its offset from the waypoint
                    hx, hy = (int(v) for v in args.hint.split(","))
                    if math.hypot(w[0] + hx - px, w[1] + hy - py) > 6:
                        tgt = path_near(st, (w[0] + hx, w[1] + hy), 5, args.hop)
                        if tgt is not None:
                            tgt = jitter(tgt)
                            sx, sy = p.screen(tgt[0] - px, tgt[1] - py)
                            p.dpy.click(p.off[0] + int(max(10, min(790, sx))), p.off[1] + int(max(10, min(520, sy))),
                                        button=1, hold=0.12)
                            time.sleep(args.walk_wait)
                            if not walked():
                                return 1
                            continue
                # town rooms all activate with the level, but units come into being only near the player: walk along
                # the shortest path to the nearest reachable cell 30 sub-tiles or more from everywhere the player has
                # been
                tgt = explore_step(st, args.hop)
                if tgt is False:
                    print("npc: %s (class %d) not seen anywhere in level %s" % (name, cls, st.pos[2]))
                    return 1
                if tgt is None:
                    a = random.uniform(0, 2 * math.pi)
                    tgt = (px + args.hop * math.cos(a), py + args.hop * math.sin(a))
                tgt = jitter(tgt)
                sx, sy = p.screen(tgt[0] - px, tgt[1] - py)
                p.dpy.click(p.off[0] + int(max(10, min(790, sx))), p.off[1] + int(max(10, min(520, sy))), button=1,
                            hold=0.12)
                time.sleep(args.walk_wait)
                if not walked():
                    return 1
                continue
            px, py = st.pos[0], st.pos[1]
            dx, dy = u[2] - px, u[3] - py
            d = math.hypot(dx, dy)
            fx, fy = p.screen(dx, dy)
            onscreen = d <= args.click_far and 40 <= fx <= 760 and 90 <= fy - args.npc_dy <= 500
            if d > args.near and not onscreen:     # on the screen: a click on the NPC itself walks the way to it
                tgt = path_near(st, (u[2], u[3]), args.near - 2, args.hop)
                if tgt is None:              # no known path: straight at it
                    k = min(args.hop, d - args.near / 2) / d
                    tgt = (px + dx * k, py + dy * k)
                tx, ty = jitter(tgt)
                sx, sy = p.screen(tx - px, ty - py)
                p.dpy.click(p.off[0] + int(max(10, min(790, sx))), p.off[1] + int(max(10, min(520, sy))), button=1,
                            hold=0.12)
                time.sleep(args.walk_wait)
                if not walked():
                    return 1
                continue
            sx, sy = p.screen(dx, dy)
            sx, sy = int(max(10, min(790, sx))), int(max(60, min(520, sy - args.npc_dy)))
            p.dpy.click(p.off[0] + sx, p.off[1] + sy, button=1, hold=0.12)
            t1 = time.time()
            box = None
            while time.time() - t1 < args.menu_wait:
                time.sleep(0.25)
                box = menu_lines(p, sx, sy + args.npc_dy)
                if box:                     # the same menu twice: not a frame of it fading in
                    time.sleep(0.2)
                    if menu_lines(p, sx, sy + args.npc_dy) == box:
                        break
                    box = None
            if not box:
                if speech_box(p):           # a first greeting or a quest text: Escape ends it, then click again
                    print("npc: %s: a speech panel; Escape" % name)
                    escape(p, args.log)
                    time.sleep(0.8)
                    continue
                print("npc: %s: no menu after the click at (%d, %d), d %.1f; retrying" % (name, sx, sy, d))
                continue
            time.sleep(0.2)
            mx, y1, n_opt = box
            if args.verbose:
                print("npc: %s menu: first option at (%d, %d), %d options" % (name, mx, y1, n_opt))
            ln = line
            if not args.menu_line and n_opt != len(menu):
                # "Talk" comes and goes (a greeting or quest news to tell); other extras (imbue, sockets,
                # personalise) come after trade, gamble and hire, so only a missing or added first "talk" moves them
                if menu[0] == "talk" and n_opt == len(menu) - 1:
                    ln = line - 1
                elif menu[0] != "talk" and n_opt > len(menu):
                    ln = line + 1
                if args.verbose or ln != line:
                    print("npc: %s menu has %d options, the table %d (%s): clicking option %d" % (
                        name, n_opt, len(menu), menu, ln))
                if n_opt < 2 or ln < 1:
                    if args.shots:
                        p.shot(os.path.join(args.shots, "npc%s-%s-menu.png" % (tag, name)))
                    escape(p, args.log)
                    return 1
            my = y1 + 15 * (ln - 1)
            start = os.path.getsize(args.log)
            p.dpy.move(p.off[0] + mx, p.off[1] + my)
            time.sleep(0.1)
            p.dpy.click(p.off[0] + mx, p.off[1] + my, button=1, hold=0.1)
            if action in SERVICES:      # the box and the inventory open on the client; item -> box -> check mark
                time.sleep(1.0)
                bx, by = (int(v) for v in args.svc_box.split(","))
                kx, ky = (int(v) for v in args.svc_ok.split(","))
                ix, iy = cell_xy(args.item)
                for x, y in ((ix, iy), (bx, by), (kx, ky)):
                    p.dpy.click(p.off[0] + x, p.off[1] + y, button=1, hold=0.12)
                    time.sleep(0.7)
                if args.shots:
                    p.shot(os.path.join(args.shots, "npc%s-%s-%s-ok.png" % (tag, name, action)))
            t2 = time.time()
            while time.time() - t2 < args.done_wait:
                time.sleep(0.2)
                if done_tag is None:
                    opened = True
                    break
                if done_tag == "HIRE":          # the hire list is client-side: no packet when it opens; the screen
                    if hire_box(p):             # (600 white pixels: a list of 3 rows or more)
                        opened = True
                        break
                    if args.buy:                # a short list (one or two rows) is not seen by hire_box: hire_buy
                        time.sleep(0.8)         # checks the hire itself by its HHX line
                        opened = True
                        break
                    continue
                text, _ = log_tail(args.log, start)
                for ln in text.splitlines():
                    tg, _, rest = ln.partition(" ")
                    if tg != done_tag:
                        continue
                    try:
                        dd = json.loads(rest)
                    except ValueError:
                        continue
                    if done_ok is None or done_ok(dd):
                        opened = True
                        break
                if opened:
                    break
            if not opened:
                print("npc: %s %s: no %s line after the menu click; Escape and retry" % (name, action, done_tag))
                escape(p, args.log)
                time.sleep(0.5)
        if not opened:
            print("npc: %s %s: gave up after %.0f s" % (name, action, time.time() - t0))
            if args.shots:
                p.shot(os.path.join(args.shots, "npc%s-%s-fail.png" % (tag, name)))
            return 1
        ok += 1
        time.sleep(args.linger_open)
        if action == "hire" and args.buy:
            if not hire_buy(p, args.log, args.buy):
                print("npc: %s hire: no HHX line after the row click" % name)
                if args.shots:
                    p.shot(os.path.join(args.shots, "npc%s-%s-buyfail-%d.png" % (tag, name, rep)))
                return 1
            if args.shots and args.verbose:
                p.shot(os.path.join(args.shots, "npc%s-%s-bought-%d.png" % (tag, name, rep)))
            escape(p, args.log)             # the NPC menu comes back after a hire: close it
            time.sleep(args.close_wait)
            continue
        if args.shots and (rep == 0 or args.verbose):
            p.shot(os.path.join(args.shots, "npc%s-%s-%s-%d.png" % (tag, name, action, rep)))
        if rep < args.repeat - 1 or not args.stay:
            escape(p, args.log)
            time.sleep(args.close_wait)
    print("npc: %s %s: %d/%d opened" % (name, action, ok, args.repeat))
    return 0



def optimistic_hop(st, goal, hop, bad, step=2):
    """A breadth-first path on a coarse grid (step sub-tiles) over the current level's DRLG rooms (RL lines) from the
    player to goal, where a cell known from an activated room must be standable and an unknown cell counts as free
    (the rooms not yet activated: Teleport is aimed there and the room activates on the way). Returns the farthest
    path cell within hop that is known standable (else the farthest unknown one), or None. Plan 0032 Phase 2: the
    River of Flame, whose lava splits the known cells."""
    lid = st.pos[2]
    lp = st.lptr.get(lid)
    rects = [rect for r, (pp, rect) in st.rl.items() if pp == lp]
    if not rects:
        return None

    def inside(x, y):
        return any(5 * r[0] <= x < 5 * (r[0] + r[2]) and 5 * r[1] <= y < 5 * (r[1] + r[3]) for r in rects)

    def free(x, y):
        v = st.cells.get((x, y))
        if v is None:
            return inside(x, y)
        return standable(st.cells, x, y)

    px, py = st.pos[0], st.pos[1]
    start = (px - px % step, py - py % step)
    gx, gy = int(goal[0]) - int(goal[0]) % step, int(goal[1]) - int(goal[1]) % step
    prev = {start: None}
    q = collections.deque([start])
    end = None
    while q and len(prev) < 200000:
        c = q.popleft()
        if abs(c[0] - gx) <= 6 and abs(c[1] - gy) <= 6:
            end = c
            break
        for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
            n = (c[0] + dx, c[1] + dy)
            if n in prev or not free(*n):
                continue
            prev[n] = c
            q.append(n)
    if end is None:
        # no walkable way (a moat, a lava field): Teleport jumps over blocked cells, so take the cell within
        # 2.4 hops, known standable or unknown inside a room, nearest to the goal and at least 3 nearer than now
        d0 = math.hypot(goal[0] - px, goal[1] - py)
        r = int(2.4 * hop)
        best = None
        for y in range(py - r, py + r + 1, step):
            for x in range(px - r, px + r + 1, step):
                rr = math.hypot(x - px, y - py)
                if rr > 2.4 * hop or rr < 3 or (x, y) in bad or not free(x, y):
                    continue
                e = math.hypot(goal[0] - x, goal[1] - y)
                if e <= d0 - 3 and (best is None or e < best[0]):
                    best = (e, (x, y))
        return best[1] if best else None
    path = []
    while end is not None:
        path.append(end)
        end = prev[end]
    path.reverse()
    best = best_u = None
    for c in path[1:]:
        if math.hypot(c[0] - px, c[1] - py) > hop:
            break
        if c in bad or math.hypot(c[0] - px, c[1] - py) < 3:
            continue
        if st.cells.get(c) is not None and standable(st.cells, *c):
            best = c
        else:
            best_u = c
    return best or best_u


def cmd_objop(args):
    """Operate one object N times (plan 0032 Phase 2: the Hellforge, class 376, takes the soulstone and three hammer
    strikes). With --to-pdef, while no object of the class is logged, Teleport towards the nearest room of that
    LvlPrest Def (greedy hops over known cells, else blind hops of --hop across unknown ones: the River of Flame's
    lava). Then find the nearest object of --obj-cls in the OBJS lines (tools/gdb/vendors.py), Teleport towards it
    (greedy hops over standable cells) until it is within --obj-near sub-tiles, then left-click it --times times,
    each time waiting up to --done-wait s for a new --done line (any line when --done is not given), with belt upkeep
    between the clicks. Nothing here feeds a model."""
    st = LogState(args.log)
    p = Pilot(args)
    t0 = time.time()
    done = 0
    blind = [0, set()]
    misses = [0]
    gate = NovaGate(args.radius, args.give_up)
    p.nova_hold = args.nova_hold
    while time.time() - t0 < args.time and done < args.times:
        st.poll()
        if not args.no_nova and gate.cast(p, st):    # Nova first at whatever it can hurt in range
            upkeep(args, p)
            continue
        objs = [o for o in getattr(st, "objs_cls", []) if o[0] == args.obj_cls]
        if not st.pos:
            time.sleep(0.5)
            continue
        px, py = st.pos[0], st.pos[1]
        if not objs and args.to_pdef:
            # the object's room is not active yet: head for the preset room (RL pdef), over known cells when a
            # greedy hop exists, else a blind Teleport of --hop towards it (lava and gaps are crossed that way)
            want = {int(x) for x in args.to_pdef.split(",")}
            lp = st.lptr.get(st.pos[2])
            rooms = [st.rl[r][1] for r, pd in st.pdef.items() if pd in want and r in st.rl and st.rl[r][0] == lp]
            if not rooms:
                time.sleep(0.5)
                continue
            xs = [5 * rc[0] + 2.5 * rc[2] for rc in rooms]
            ys = [5 * rc[1] + 2.5 * rc[3] for rc in rooms]
            goal = (sum(xs) / len(xs), sum(ys) / len(ys))     # the preset's centre (its rooms together)
            upkeep(args, p)
            c = optimistic_hop(st, goal, args.hop, blind[1])
            if c is None:
                a = math.atan2(goal[1] - py, goal[0] - px) + random.uniform(-1.2, 1.2)
                c = (int(px + args.hop * math.cos(a)), int(py + args.hop * math.sin(a)))
            p.teleport(c[0] - px, c[1] - py)
            time.sleep(args.wait)
            st.poll()
            if st.pos and math.hypot(st.pos[0] - px, st.pos[1] - py) < 3:
                blind[1].add(c)
            continue
        if not objs:
            time.sleep(0.5)
            continue
        o = min(objs, key=lambda o: math.hypot(o[1] - px, o[2] - py))
        d = math.hypot(o[1] - px, o[2] - py)
        upkeep(args, p)
        if d > args.obj_near:
            c = greedy_hop(st, (o[1], o[2]), args.hop, 2.0, bad=blind[1], avoid_warps=False)
            if c is None:
                c = optimistic_hop(st, (o[1], o[2]), args.hop, blind[1], step=1)
            if c is None:
                print("objop: no hop towards the object at (%d, %d), d %.1f" % (o[1], o[2], d))
                time.sleep(1.0)
                continue
            p.teleport(c[0] - px, c[1] - py)
            time.sleep(args.wait)
            st.poll()
            if st.pos and math.hypot(st.pos[0] - px, st.pos[1] - py) < 2:
                blind[1].add(c)
            continue
        if args.approach:
            print("objop: within %.1f of the object at (%d, %d)" % (d, o[1], o[2]))
            return 0
        sx, sy = p.screen(o[1] - px, o[2] - py)
        start = os.path.getsize(args.log)
        # a click that brought no line is retried a little higher or to the side: the player's own sprite or a corpse
        # over the object's anchor cell takes the click otherwise (plan 0032 Phase 2)
        jx, jy = ((0, 0), (0, 15), (25, 10), (-25, 10), (0, -15), (0, 30))[misses[0] % 6]
        p.dpy.click(p.off[0] + int(sx) + jx, p.off[1] + int(sy) - args.obj_dy - jy, button=1, hold=0.12)
        t1 = time.time()
        ok = False
        while time.time() - t1 < args.done_wait:
            time.sleep(0.3)
            text, _ = log_tail(args.log, start)
            if any(ln.startswith((args.done or "") + " ") for ln in text.splitlines()):
                ok = True
                break
        done += ok
        misses[0] = 0 if ok else misses[0] + 1
        print("objop: click %d at (%d, %d) d %.1f: %s" % (done, o[1], o[2], d, "done" if ok else "no %s line" % args.done))
        time.sleep(args.linger)
        if args.shots:
            p.shot(os.path.join(args.shots, "objop%s-%d.png" % (args.shot_tag, int(time.time()))))
    print("objop: %d/%d" % (done, args.times))
    return 0 if done >= args.times else 1


def cmd_hunt(args):
    """Kill one monster class (plan 0032 Phase 2: Mephisto across the Durance moat, Andariel at the end of the
    catacombs): its unit from the MON lines (near or "far" scans, tools/gdb/pilot.py), Teleport towards it along
    optimistic_hop paths (unknown cells count as free) or greedy hops, Nova bursts at whatever Nova can hurt within
    --radius, until a unit of --mon-cls is dead or --time runs out. Nothing here feeds a model."""
    st = LogState(args.log)
    p = Pilot(args)
    p.nova_hold = args.nova_hold
    if args.nova_key:
        p.nova_key = args.nova_key
    gate = make_gate(args)
    bad = set()
    skip = set()
    skip_rect = set()
    goal = [None]
    t0 = time.time()
    seen = False
    while time.time() - t0 < args.time:
        st.poll()
        if not st.pos:
            time.sleep(0.5)
            continue
        byid = {m["id"]: m for m in st.far.values()}
        byid.update({m["id"]: m for m in st.mon})      # the near scan is the newer one
        ms = [m for m in byid.values() if m["cls"] == args.mon_cls]
        if any(not live(m) for m in ms) and not any(live(m) for m in ms):
            print("hunt: class %d down after %.0f s" % (args.mon_cls, time.time() - t0))
            time.sleep(args.linger)
            return 0
        upkeep(args, p, st)
        if gate.cast(p, st):
            continue
        live_ms = [m for m in ms if live(m)]
        px, py = st.pos[0], st.pos[1]
        if not live_ms:
            # not created yet (its room has not activated): head for the farthest unactivated room of the level
            # from where we stand, over optimistic paths; the rooms activate as we pass
            fr = [rect for r, rect in st.frontier(st.pos[2]) if r not in skip and tuple(rect) not in skip_rect]
            if not fr:
                time.sleep(0.5)
                continue
            if goal[0] is None or goal[0] not in [tuple(r) for r in fr]:
                goal[0] = tuple(max(fr, key=lambda rc: math.hypot(room_centre(rc)[0] - px, room_centre(rc)[1] - py)))
            c = optimistic_hop(st, room_centre(goal[0]), args.hop, bad, step=2)
            if c is None:
                skip_rect.add(goal[0])
                goal[0] = None
                continue
            p.teleport(c[0] - px, c[1] - py)
            time.sleep(args.wait)
            st.poll()
            if st.pos and math.hypot(st.pos[0] - px, st.pos[1] - py) < 2:
                bad.add(c)
            continue
        seen = True
        m = min(live_ms, key=lambda m: math.hypot(m["x"] - px, m["y"] - py))
        d = math.hypot(m["x"] - px, m["y"] - py)
        if d <= args.radius - 2:
            p.nova()                    # in range but not a Nova target (resist above the gate's): cast anyway
            continue
        c = greedy_hop(st, (m["x"], m["y"]), args.hop, 2.0, bad=bad, avoid_warps=True)
        if c is None:
            c = optimistic_hop(st, (m["x"], m["y"]), args.hop, bad, step=1)
        if c is None:
            print("hunt: no hop towards class %d at (%d, %d), d %.1f" % (args.mon_cls, m["x"], m["y"], d))
            time.sleep(1.0)
            continue
        p.teleport(c[0] - px, c[1] - py)
        time.sleep(args.wait)
        st.poll()
        if st.pos and math.hypot(st.pos[0] - px, st.pos[1] - py) < 2:
            bad.add(c)
    print("hunt: time out (class %d %s)" % (args.mon_cls, "seen" if seen else "never seen"))
    return 1


def cube_outcome(text):
    """The last transmute in tools/gdb/cube.gdb lines: None until its CUBX line, else a summary dict."""
    res = None
    for line in text.splitlines():
        tag, _, rest = line.partition(" ")
        if tag not in ("CUB0", "CROW", "CPL", "CUBX", "CPORTR", "PAN"):
            continue
        try:
            d = json.loads(rest)
        except ValueError:
            continue
        if tag == "CUB0":
            res = dict(n=len(d.get("items") or []), row=None, placed=[], portal=None, done=False)
        elif res is None:
            continue
        elif tag == "CROW":
            res["row"] = d["row"]
        elif tag == "CPL":
            res["placed"].append((d.get("it") or {}).get("cls"))
        elif tag == "CPORTR":
            res["portal"] = d["r"]
        elif tag == "PAN":
            res["portal"] = "pandemonium %d" % d["k"]
        elif tag == "CUBX":
            res["done"] = True
            res["after"] = [it.get("cls") for it in d.get("items") or []]
            res["xy"] = [it.get("xy") for it in d.get("items") or []]
    return res if res and res["done"] else None


def read_plan(path):
    """Tokens of a plan file: whitespace-separated, '#' starts a comment to the end of the line."""
    out = []
    with open(path) as f:
        for line in f:
            out.extend(line.split("#", 1)[0].split())
    return out


def cmd_cube(args, tokens):
    """Play a cube session (plan 0030 Phase 2) against a tools/gdb/cube.gdb log. Tokens (also read from --plan FILE):
    key:K, sleep:S, shot:PATH, xy:X,Y, click:CELL, rclick:CELL as for insert; mv:A>B picks the item at cell A up and
    puts it down with its footprint's centre at B; out:inv:x,y,w,h moves the first item the cube holds after the
    last transmute (at the cell its CUBX line gives) to that footprint; tm presses Transmute (--tm-xy) and waits for the logger's CUBX line,
    then prints the row matched (or none), the classes placed and the classes left in the cube; drop:CELL picks the
    item at CELL up and drops it on the ground (--drop-xy, a point of the floor between the two panels)."""
    p = Pilot(args)
    if args.plan:
        tokens = read_plan(args.plan) + list(tokens)
    pos = os.path.getsize(args.log) if os.path.exists(args.log) else 0
    n_tm = n_row = 0
    last = None

    def click(x, y, button=1):
        p.dpy.click(p.off[0] + x, p.off[1] + y, button=button, hold=0.12)

    for tok in tokens:
        kind, _, arg = tok.partition(":")
        if kind == "key":
            p.dpy.key(arg)
            time.sleep(0.6)
        elif kind == "sleep":
            time.sleep(float(arg))
        elif kind == "shot":
            p.shot(arg)
        elif kind == "xy":
            x, y = (int(v) for v in arg.split(","))
            click(x, y)
            time.sleep(0.6)
        elif kind in ("click", "rclick"):
            x, y = cell_xy(arg)
            click(x, y, 1 if kind == "click" else 3)
            time.sleep(0.6)
        elif kind == "mv":
            a, b = arg.split(">")
            click(*cell_xy(a))
            time.sleep(args.pick_wait)
            click(*cell_xy(b))
            time.sleep(args.pick_wait)
        elif kind == "out":
            # out>inv:x,y,w,h: the first item the cube holds after the last transmute (its cell from the CUBX line)
            # goes to that footprint
            _, b = arg.split(">") if ">" in arg else ("", arg)
            w, h = (int(v) for v in b.split(",")[2:4])
            xy = (last or {}).get("xy") or []
            if not xy or not xy[0]:
                print("OUT: no cube cell logged, nothing moved")
                continue
            click(*cell_xy("cube:%d,%d,%d,%d" % (xy[0][0], xy[0][1], w, h)))
            time.sleep(args.pick_wait)
            click(*cell_xy(b))
            time.sleep(args.pick_wait)
        elif kind == "drop":
            click(*cell_xy(arg))
            time.sleep(args.pick_wait)
            click(*(int(v) for v in args.drop_xy.split(",")))
            time.sleep(args.pick_wait)
        elif kind == "tm":
            _, pos = log_tail(args.log, pos)
            click(*(int(v) for v in args.tm_xy.split(",")))
            text, waited, res = "", 0.0, None
            while waited < args.tm_wait:
                time.sleep(0.25)
                waited += 0.25
                more, pos = log_tail(args.log, pos)
                text += more
                res = cube_outcome(text)
                if res:
                    break
            n_tm += 1
            last = res
            if res is None:
                print("TRANSMUTE %d: no CUBX line in %.1f s (%s)" % (n_tm, waited,
                                                                   "CUB0 seen" if "CUB0 " in text else "no CUB0"))
            else:
                n_row += res["row"] is not None
                print("TRANSMUTE %d: %d items, row %s, placed %s, portal %s, cube after %s" % (
                    n_tm, res["n"], res["row"], res["placed"], res["portal"], res["after"]))
            sys.stdout.flush()
            time.sleep(args.ins_gap)
        else:
            raise SystemExit("cube: unknown token %r" % tok)
    print("cube: %d transmutes pressed, %d matched a row" % (n_tm, n_row))
    return 0


def cmd_players(args):
    """Type /players N (N = the first positional number) and return."""
    p = Pilot(args)
    type_players(p, args.dx)
    return 0


def cmd_explore(args):
    st = LogState(args.log)
    st.any_level = args.any_level
    st.poll()
    p = Pilot(args)
    p.nova_key, p.es_key = args.nova_key, args.es_key     # skill hotkeys (harness-play.md), as in farm
    if not st.pos:
        print("no PLR yet")
        return 1
    if args.players:
        type_players(p, args.players)
    if p.nova_key:
        p.dpy.key(p.nova_key)
    lid0 = st.pos[2]
    targets = None
    gate = (MeleeGate(args.radius, args.give_up, button=args.melee_button or 1, hold=args.melee_hold)
            if args.melee else NovaGate(args.radius, args.give_up))
    if args.to_warp:
        targets = [(r, rect) for r, (lp, rect) in st.rl.items() if r in st.warps and lp == st.lptr.get(lid0)]
        print("target rooms with a warp: %s" % [(rect, st.warps[r]) for r, rect in targets])
        if not targets:
            return 1
    if args.to_rect is not None:                    # a tile rect (e.g. a room the warp-point model names), then stop
        v = [int(x) for x in args.to_rect.split(",")]
        targets = [(None, v[i:i + 4]) for i in range(0, len(v), 4)]
        print("target rects: %s" % [t for _, t in targets])
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
    notgt = 0
    for k in range(1, args.hops + 1):
        if args.loot:
            loot(args, st, p, tried)
        if args.es and (t_es is None or time.time() - t_es > args.es):
            p.shield(args.es_swap)
            t_es = time.time()
        st.poll()
        if st.pos[2] != lid0:
            if not args.any_level or st.pos[2] in TOWNS:
                print("level changed %s -> %s (death or a warp); stop" % (lid0, st.pos[2]))
                break
            print("level changed %s -> %s (--any-level: go on)" % (lid0, st.pos[2]))
            lid0 = st.pos[2]
        p.walk = args.walk or (args.any_level and st.pos[2] in TOWNS)
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
        if tgt is None and args.persist and notgt < args.persist and "level done" not in why:
            notgt += 1                  # plan 0023: a random standable hop and a fresh plan instead of stopping
            st.poll()
            qx, qy = st.pos[0], st.pos[1]
            cand = [(x, y) for y in range(qy - 14, qy + 15) for x in range(qx - 14, qx + 15)
                    if 6 <= math.hypot(x - qx, y - qy) <= 14 and standable(st.cells, x, y)]
            if cand:
                x, y = random.choice(cand)
                p.teleport(x - qx, y - qy)
                time.sleep(args.wait)
            cache = None
            bad.clear()
            continue
        if tgt is None:
            print("hop %d: no target (%s); stop" % (k, why))
            break
        notgt = 0
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


UPKEEP = {"t_mana": 0.0, "t_es": None, "npot": 0, "t_merc": 0.0, "merc_max": 0}


HIRE_CLS = (271, 338, 359, 560, 561)


def upkeep(args, p, st=None):
    """Belt potions and Energy Shield: a potion from the non-mana columns below --drink life, one from --mana-col
    below --mana-drink mana (at most every 2 s), Energy Shield every --es seconds. With --merc-drink F and a log
    state, a belt potion is given to the mercenary (Shift + the column key) when the life of its last MON entry
    falls below F of the most it was seen with (at most every 2 s)."""
    u = UPKEEP
    if st is not None and args.merc_drink and time.time() - u["t_merc"] > 2:
        hm = [m for m in st.mon if m.get("cls") in HIRE_CLS and m.get("hp")]
        if hm:
            hp = hm[0]["hp"]
            u["merc_max"] = max(u["merc_max"], hp)
            if hp < args.merc_drink * u["merc_max"]:
                u["npot"] += 1
                col = [c for c in (1, 2, 3, 4) if c != args.mana_col][u["npot"] % 3]
                p.dpy.keystate("Shift_L", True)
                p.potion(col)
                p.dpy.keystate("Shift_L", False)
                u["t_merc"] = time.time()
                print("merc life %d/%d, potion column %d to the mercenary" % (hp, u["merc_max"], col))
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


def descend_rows(args):
    return {int(x) for x in str(args.descend).split(",")}


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
        upkeep(args, p, st)
        if gate.cast(p, st):
            continue
        px, py = st.pos[0], st.pos[1]
        cells = [(x, y) for (lid, rec, x, y) in st.wrp if lid == lid0 and rec in descend_rows(args)]
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
            tgt = None
            if path is None:
                # once on a path, stay on it: a path step that leads away from the warp followed by a greedy hop
                # back towards it shuttled between two cells for the whole search (h37r, seed 3738)
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
                    print("descend: every room activated or skipped, no warp %s" % args.descend)
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
        type_players(p, args.players)
    if args.wp:
        tab, row = (int(v) for v in args.wp.split(","))
        if wp_travel(args, st, p, tab, row):
            return 1
        time.sleep(0.4)
    st.poll()
    gate = make_gate(args)
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
        upkeep(args, p, st)
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


def make_gate(args):
    """--melee-button N (plan 0037 Phase 2): a MeleeGate clicking button N (3: Attack on the right button, so Teleport
    stays on Shift + left) instead of Nova, in farm, hunt and objop; explore keeps --melee."""
    if getattr(args, "melee_button", 0):
        return MeleeGate(args.radius, args.give_up, button=args.melee_button, hold=args.melee_hold)
    return NovaGate(args.radius, args.give_up)


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
    tokens = None
    if len(sys.argv) > 2 and sys.argv[1] in ("insert", "cube"):
        # insert <log> TOKEN... [options]: tokens are the positionals after the log that do not start with --
        rest, tokens, opts = sys.argv[3:], [], []
        it = iter(rest)
        for a in it:
            if a.startswith("--"):
                opts.append(a)
                if "=" not in a and a not in ("--verbose",):
                    opts.append(next(it))
            else:
                tokens.append(a)
        sys.argv = sys.argv[:3] + opts
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("where", "explore", "hop", "farm", "mons", "wp", "wpchain", "players", "insert",
                                    "cube", "npc", "objop", "hunt"))
    ap.add_argument("log")
    ap.add_argument("dx", nargs="?", default="0")
    ap.add_argument("dy", nargs="?", default="0")
    ap.add_argument("--slot", type=int, help="harness slot: display :7+N (tools/slots.py); default 0 (:7)")
    ap.add_argument("--display", help="X display (default: the slot's; :7 without --slot)")
    ap.add_argument("--view-h", type=int, default=571, help="rows of the game frame on screen (571 on the usual "
                    "harness display; 515 on a 544-row display; 0: measured from the screen): scales the orb and menu samples and the hop clamp")
    ap.add_argument("--cx", type=int, default=400)
    ap.add_argument("--cy", type=int, default=290)
    ap.add_argument("--hops", type=int, default=200)
    ap.add_argument("--hop", type=float, default=10.0)
    ap.add_argument("--wait", type=float, default=0.45)
    ap.add_argument("--nova", type=int, default=2)
    ap.add_argument("--potion", type=int, default=0)
    ap.add_argument("--es", type=float, default=0, help="cast Energy Shield every this many seconds (0: never)")
    ap.add_argument("--es-swap", type=int, default=1, help="1: Energy Shield is the swap set's right skill")
    ap.add_argument("--merc-drink", type=float, default=0, help="farm, hunt: give the mercenary a belt potion "
                    "(Shift + column key) below this fill of its most seen MON life (0: never)")
    ap.add_argument("--drink", type=float, default=0.6, help="drink a belt potion below this life-orb fill")
    ap.add_argument("--to-pdef", help="go to the room of this LvlPrest Def (or any of a comma-separated list) in the "
                                      "current level, then stop")
    ap.add_argument("--to-rect", help="explore: go to this tile rect x,y,w,h (several: concatenated), then stop")
    ap.add_argument("--any-level", action="store_true",
                    help="explore: aim at unactivated rooms of any level that has an activated room (leaves a town)")
    ap.add_argument("--to-warp", action="store_true", help="go to a room of the current level that has a warp, then stop")
    ap.add_argument("--walk", action="store_true", help="explore: always walk (left click), never Teleport")
    ap.add_argument("--melee", action="store_true", help="explore: left-click the nearest live monster in --radius "
                                                         "instead of Nova (a character without Nova; plan 0034)")
    ap.add_argument("--blind-nova", action="store_true",
                    help="the old behaviour: Nova every --nova hops whatever is (or is not) in range")
    ap.add_argument("--melee-button", type=int, default=0, help="farm, hunt: attack with this mouse button (3: Attack "
                    "on the right button) instead of Nova; explore --melee: the button (default 1)")
    ap.add_argument("--melee-hold", type=float, default=0.12, help="melee: seconds the attack button is held per click")
    ap.add_argument("--radius", type=float, default=9.0, help="Nova range in sub-tiles for the target test")
    ap.add_argument("--give-up", type=int, default=6, help="abandon a target after this many casts with no life change")
    ap.add_argument("--burst", type=int, default=8, help="most Nova casts in a row at one stop")
    ap.add_argument("--cast-wait", type=float, default=0.35)
    ap.add_argument("--shots")
    ap.add_argument("--stall", type=float, default=20.0,
                    help="watchdog: seconds with neither the log nor the position changing before a STALL line")
    ap.add_argument("--wp-x", type=int, default=712, help="wp: the town waypoint (screenshot x)")
    ap.add_argument("--wp-find", action="store_true", help="wp: find the town waypoint from the object lines (plan 0023)")
    ap.add_argument("--wp-tab-x0", type=int, default=115, help="wp: x of the first act tab (classic: 120)")
    ap.add_argument("--wp-tab-w", type=int, default=62, help="wp: act tab spacing (5 tabs: 62; classic, 4 tabs: 78)")
    ap.add_argument("--wp-y", type=int, default=62, help="wp: the town waypoint (screenshot y)")
    ap.add_argument("--shot-every", type=int, default=25)
    ap.add_argument("--chain", default="", help="wpchain: waypoint hops 'TAB,ROW TAB,ROW ...' from the current waypoint")
    ap.add_argument("--wp", help="farm: waypoint travel first, 'TAB,ROW' of the waypoint list (e.g. 5,2)")
    ap.add_argument("--time", type=float, default=90, help="farm: end the kill loop after this many seconds")
    ap.add_argument("--linger", type=float, default=2.0, help="farm: seconds to stay after the last boss died")
    ap.add_argument("--chase", type=int, default=8, help="farm: give a boss up after this many hops that got no nearer to it")
    ap.add_argument("--min-hop", type=float, default=5.0, help="farm: shortest Teleport hop (sub-tiles)")
    ap.add_argument("--nova-hold", type=float, default=1.6,
                    help="farm: seconds the right button stays down per Nova burst (the game recasts at its cast rate)")
    ap.add_argument("--mana-drink", type=float, default=0.3, help="farm: drink from --mana-col below this mana-orb fill")
    ap.add_argument("--mana-col", type=int, default=4, help="farm: the belt column (hot key) holding mana potions; 0: none")
    ap.add_argument("--descend", help="farm: after the waypoint, find and take the warp of this LvlWarp row (or of any of a "
                                      "comma-separated list, e.g. 67,68: Durance Down L/R) "
                                                "(67: Durance of Hate 2 -> 3) before the kill loop")
    ap.add_argument("--descend-time", type=float, default=150, help="farm: give the --descend search this long")
    ap.add_argument("--boss-cls", help="farm: MonStats rows that count as bosses besides the unique/champion flags "
                                       "(e.g. 242 Mephisto)")
    ap.add_argument("--sweep", action="store_true", help="farm: after the bosses keep killing whatever is near and "
                                                        "exploring, in the same game, until --time")
    ap.add_argument("--nova-key", help="farm, explore: the F-key bound to Nova in the save (e.g. F1), pressed before every burst")
    ap.add_argument("--es-key", help="farm, explore: the F-key bound to Energy Shield (e.g. F2); replaces the weapon swap")
    ap.add_argument("--players", type=int, default=0, help="farm, explore: type /players N first (0: no)")
    ap.add_argument("--max-res", type=float, default=75, help="farm: skip a boss whose lightning resist is this or more")
    ap.add_argument("--loot", type=float, default=0, help="explore: operate the containers within this many sub-tiles "
                                                          "before each hop (needs tools/gdb/objects.py's lines; plan 0023)")
    ap.add_argument("--persist", type=int, default=0, help="explore: on 'no target', make a random hop and plan again, "
                                                           "up to this many times in a row, before stopping")
    ap.add_argument("--loot-max", type=int, default=4, help="explore: most containers operated at one stop")
    ap.add_argument("--loot-wait", type=float, default=2.5, help="explore: seconds to wait for the operate (OO0) line")
    ap.add_argument("--loot-dy", type=int, default=20, help="explore: click this many pixels above the object's cell")
    ap.add_argument("--excel", default=os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel"))
    ap.add_argument("--pick-wait", type=float, default=0.45, help="insert: seconds between picking the child up and "
                                                                 "clicking the parent")
    ap.add_argument("--ins-wait", type=float, default=3.0, help="insert: seconds to wait for the logger's answer")
    ap.add_argument("--ins-gap", type=float, default=0.3, help="insert: seconds between two inserts")
    ap.add_argument("--plan", help="cube: read tokens from this file ('#' comments) before the command-line tokens")
    ap.add_argument("--tm-xy", default="240,340", help="cube: the Transmute button (window coordinates)")
    ap.add_argument("--tm-wait", type=float, default=6.0, help="cube: seconds to wait for the logger's CUBX line")
    ap.add_argument("--drop-xy", default="360,330", help="cube: a floor point between the two panels (drop:CELL)")
    ap.add_argument("--repeat", type=int, default=1, help="npc: open the window this many times (Escape between)")
    ap.add_argument("--stay", action="store_true", help="npc: leave the last window open")
    ap.add_argument("--buy", type=int, default=0,
                    help="npc ... hire: hire list row N (1 = top) after each opening, answer Yes to the replace box "
                         "and wait for the HHX line of tools/gdb/hirelings.py (plan 0033)")
    ap.add_argument("--item", help="npc imbue|socket|personalize: the inventory cell of the item, inv:c,r[,w,h]")
    ap.add_argument("--svc-box", default="170,165", help="npc services: the item box (window coordinates)")
    ap.add_argument("--svc-ok", default="137,240", help="npc services: the box's check mark (window coordinates)")
    ap.add_argument("--menu-line", type=int, default=0, help="npc: click this menu line (1 = under the name) instead "
                                                             "of the table's")
    ap.add_argument("--near", type=float, default=9.0, help="npc: walk until the NPC is this close (sub-tiles)")
    ap.add_argument("--click-far", type=float, default=0.0,
                    help="npc: click the NPC itself once it is on the screen and this close (the game walks to it; 0: off, roofs hide some NPCs)")
    ap.add_argument("--hint", help="npc: X,Y offset of the NPC's usual place from the town waypoint (sub-tiles), "
                                   "walked to first when the NPC is not in the log yet")
    ap.add_argument("--npc-dy", type=int, default=44, help="npc: click this many pixels above the NPC's feet")
    ap.add_argument("--npc-time", type=float, default=60.0, help="npc: give one opening this long")
    ap.add_argument("--walk-wait", type=float, default=1.1, help="npc: seconds after each walk click")
    ap.add_argument("--menu-wait", type=float, default=4.0, help="npc: seconds to wait for the menu box")
    ap.add_argument("--done-wait", type=float, default=6.0, help="npc: seconds to wait for the logger's confirmation")
    ap.add_argument("--linger-open", type=float, default=0.3, help="npc: seconds the window stays open")
    ap.add_argument("--close-wait", type=float, default=0.6, help="npc: seconds after the Escape")
    ap.add_argument("--obj-cls", type=int, default=376, help="objop: the object class (objects.txt row)")
    ap.add_argument("--obj-near", type=float, default=4.0, help="objop: click the object from this close (sub-tiles)")
    ap.add_argument("--obj-dy", type=int, default=30, help="objop: click this many pixels above the object's cell")
    ap.add_argument("--times", type=int, default=1, help="objop: the number of confirmed clicks")
    ap.add_argument("--done", help="objop: the log tag that confirms a click (e.g. QS)")
    ap.add_argument("--mon-cls", type=int, help="hunt: the MonStats row to kill")
    ap.add_argument("--no-nova", action="store_true", help="objop: never stop to cast Nova (Hell: Teleport through)")
    ap.add_argument("--approach", action="store_true", help="objop: stop within --obj-near of the object, no click")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    if args.cmd == "npc":
        args.npc_name, args.npc_action = args.dx, args.dy
    else:
        try:
            args.dx, args.dy = int(args.dx), int(args.dy)
        except ValueError:
            ap.error("dx and dy must be integers")
    import slots
    try:
        args.slot, args.display = slots.pick_display(args.slot, args.display)
    except slots.SlotError as e:
        ap.error(str(e))
    args.shot_tag = "" if args.slot in (None, 0) else slots.suffix(args.slot)
    print("d2pilot: slot %s, display %s" % ("-" if args.slot is None else args.slot, args.display), file=sys.stderr)
    if args.cmd == "insert":
        return cmd_insert(args, tokens or [])
    if args.cmd == "cube":
        return cmd_cube(args, tokens or [])
    return {"where": cmd_where, "explore": cmd_explore, "hop": cmd_hop, "farm": cmd_farm,
            "mons": cmd_mons, "wp": cmd_wp, "wpchain": cmd_wpchain, "players": cmd_players, "npc": cmd_npc,
            "objop": cmd_objop, "hunt": cmd_hunt}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
