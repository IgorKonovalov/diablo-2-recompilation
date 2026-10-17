#!/usr/bin/env python3
"""Pure helpers of the two-client driver (plan 0044 Phase 1): `tools/d2pilot.py join` uses them to steer one client
of a TCP/IP game (usually the joiner, which runs without a debugger) from the HOST's gdb log. Nothing here touches a
display or the game; tools/test_joiner.py tests it without either.

The log lines come from tools/gdb/two-players.py:
    PLRS {"t": <time>, "p": [{"id", "cls", "mode", "x", "y", "room", "lid", "dead", "tk", "hl"}, ...],
          "pty": [{"id": <party id>, "m": [<unit id>, ...]}, ...]}

Who is who: `--me` / `--lead` take a unit id, or "host" (the first player id the log lists: the host is in its game
before anyone joins) or "join" (the first other id). Party actions are plan 0011's steps files
(tools/gdb/two-party-invite.steps, -accept, -leave) plus two-party-hostile.steps; the trade and exit geometry below is
UNCALIBRATED until the driver's live test (plan 0044 log) measures it on a slot.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = {a: os.path.join(HERE, "gdb", "two-party-%s.steps" % a) for a in ("invite", "accept", "leave", "hostile")}

# Travel gates read with the player's own PlayerData +0x160 tick (0x0055B6C0 with EDX = 0); docs/findings/multiplayer.
WAYPOINT_GATE_MS = 10000      # 0x0054C601: add eax, 0x2710
PORTAL_GATE_MS = 5000         # 0x005848C1: lea edi, [eax + 0x1388]
HOSTILE_REPEAT_MS = 60000     # 0x005A5F47: add eax, 0xEA60 (the pair's stamp)

# Window-relative 800x600 geometry, UNCALIBRATED (measure at the live test, then replace and record the screenshots).
TRADE_UI = {
    "accept": (110, 140),     # the "accept trade" box that opens on the asked player's screen
    "ok": (275, 412),         # the trade window's check button
    "grid": (88, 302, 10, 4),  # the trade grid (x0, y0, cols, rows) of 29-px cells, as tools/d2pilot.py's GRIDS
}
EXIT_MENU_XY = (400, 287)     # Escape menu: SAVE AND EXIT GAME
INV = (418, 316, 10, 4)       # inventory grid, measured on run:2026-10-15-sockets (d2pilot.py GRIDS)
CELL = 29


def parse_plrs(line):
    """The JSON of one PLRS line, or None."""
    tag, _, rest = line.partition(" ")
    if tag != "PLRS":
        return None
    try:
        d = json.loads(rest)
    except ValueError:
        return None
    return d if isinstance(d.get("p"), list) else None


class Players:
    """The players of the last PLRS line, and the order in which ids first appeared."""

    def __init__(self):
        self.last = None
        self.order = []

    def feed(self, d):
        for e in d["p"]:
            if e.get("id") is not None and e["id"] not in self.order:
                self.order.append(e["id"])
        self.last = d

    def resolve(self, who):
        """A unit id for 'host', 'join' or a number; None when not known yet."""
        if who is None:
            return None
        if isinstance(who, int):
            return who
        w = str(who)
        if w == "host":
            return self.order[0] if self.order else None
        if w == "join":
            return self.order[1] if len(self.order) > 1 else None
        return int(w, 0)

    def get(self, who):
        uid = self.resolve(who)
        if uid is None or not self.last:
            return None
        for e in self.last["p"]:
            if e.get("id") == uid:
                return e
        return None

    def party_of(self, who):
        """The party id of a player, or None when it is in no party."""
        uid = self.resolve(who)
        if uid is None or not self.last:
            return None
        for p in self.last.get("pty", []):
            if uid in p.get("m", []):
                return p["id"]
        return None

    def same_party(self, a, b):
        pa = self.party_of(a)
        return pa is not None and pa == self.party_of(b)


def read_players(path, players=None):
    """Feed every PLRS line of a log to a Players."""
    players = players or Players()
    with open(path, errors="replace") as f:
        for line in f:
            d = parse_plrs(line)
            if d:
                players.feed(d)
    return players


def follow_step(me, lead, near=6.0, hop=10.0):
    """One move of `follow`: None when me is within `near` sub-tiles of lead (Chebyshev), ('level', my lid, lead lid)
    when the two are in different levels, ('wait', why) when a position is missing, else ('move', dx, dy): the offset
    from me towards lead, clamped to `hop` sub-tiles along the larger axis and rounded."""
    if not me or not lead:
        return ("wait", "player not in the log")
    if me.get("x") is None or lead.get("x") is None:
        return ("wait", "no position")
    if me.get("lid") != lead.get("lid"):
        return ("level", me.get("lid"), lead.get("lid"))
    dx, dy = lead["x"] - me["x"], lead["y"] - me["y"]
    m = max(abs(dx), abs(dy))
    if m <= near:
        return None
    if m > hop:
        dx, dy = dx * hop / m, dy * hop / m
    return ("move", int(round(dx)), int(round(dy)))


def screen(cx, cy, dx, dy):
    """Window coordinates of a sub-tile offset from the player at the window point (cx, cy), as d2pilot's Pilot."""
    return cx + 16 * (dx - dy), cy + 8 * (dx + dy)


def clamp_click(sx, sy, lo=10, hi_x=790, hi_y=540):
    return max(lo, min(hi_x, int(sx))), max(lo, min(hi_y, int(sy)))


def read_steps(path):
    """The commands of a steps file as xdrive runs them: [[cmd, arg...], ...] ('#' comments and blank lines dropped)."""
    out = []
    with open(path) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            out.append(["type", line[5:]] if line.startswith("type ") else line.split(None, 2))
    return out


def party_done(players, action, me, lead, tk0=None):
    """Whether the log shows a party action's effect: accept -> me and lead share a party; leave -> me in no party;
    hostile -> my +0x160 tick changed from tk0 (0x0055B720); invite -> True (nothing to see until the accept)."""
    if action == "invite":
        return True
    if action == "accept":
        return players.same_party(me, lead)
    if action == "leave":
        return players.get(me) is not None and players.party_of(me) is None
    if action == "hostile":
        e = players.get(me)
        return bool(e) and e.get("tk") is not None and e.get("tk") != tk0
    raise ValueError("unknown party action %r" % action)


def gate_open(kind, now, tk):
    """The travel gates as read (0x0054C5FC, 0x005848BC): open when now >= tk + the gate's wait (u32 compare)."""
    wait = {"waypoint": WAYPOINT_GATE_MS, "portal": PORTAL_GATE_MS}[kind]
    return ((tk + wait) & 0xFFFFFFFF) <= (now & 0xFFFFFFFF)


def grid_xy(spec):
    """'inv:c,r' or 'tr:c,r' (optionally ',w,h') -> window centre of that footprint."""
    page, _, rest = spec.partition(":")
    x0, y0, cols, rows = {"inv": INV, "tr": TRADE_UI["grid"]}[page]
    v = [int(t) for t in rest.split(",")]
    c, r = v[0], v[1]
    w, h = (v[2], v[3]) if len(v) == 4 else (1, 1)
    if not (0 <= c and c + w <= cols and 0 <= r and r + h <= rows):
        raise ValueError("%s: outside the %s grid" % (spec, page))
    return x0 + CELL * c + CELL * w // 2, y0 + CELL * r + CELL * h // 2


def plan_trade(tokens, lead_xy=None):
    """Turn trade tokens into clicks: [('click', x, y, button) | ('key', K) | ('sleep', S) | ('shot', PATH)].
       request          left click on the other player (lead_xy: its window point, from follow's geometry)
       accept           the accept box on the asked player's screen (TRADE_UI, uncalibrated)
       give:A>B         pick the inventory item at A up and put it at trade-grid cell B (inv:c,r>tr:c,r)
       ok               the trade window's check button
       key:K  sleep:S  shot:PATH  xy:X,Y"""
    out = []
    for tok in tokens:
        kind, _, arg = tok.partition(":")
        if kind == "request":
            if lead_xy is None:
                raise ValueError("request: the other player's position is not known")
            out.append(("click", lead_xy[0], lead_xy[1], 1))
        elif kind in ("accept", "ok"):
            x, y = TRADE_UI[kind]
            out.append(("click", x, y, 1))
        elif kind == "give":
            a, b = arg.split(">")
            out.append(("click",) + grid_xy(a) + (1,))
            out.append(("click",) + grid_xy(b) + (1,))
        elif kind == "xy":
            x, y = (int(v) for v in arg.split(","))
            out.append(("click", x, y, 1))
        elif kind == "key":
            out.append(("key", arg))
        elif kind == "sleep":
            out.append(("sleep", float(arg)))
        elif kind == "shot":
            out.append(("shot", arg))
        else:
            raise ValueError("trade: unknown token %r" % tok)
    return out
