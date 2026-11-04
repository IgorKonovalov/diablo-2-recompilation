#!/usr/bin/env python3
"""Plan 0054 Phase 2 (`lane/p54`): per-event reproduction of `PathPlan`, the model and the check.

    python3 -I tools/path.py check LOG [LOG ...] [--out F]   reproduce every logged plan with the models, run the live controls, print the
                                                             outcome mix per type, the floors, the break lines and the grid tie
    python3 -I tools/path.py mix LOG [LOG ...]               the outcome mix only
    python3 -I tools/path.py tie LOG [LOG ...] [--first N]   the grid tie only
    python3 -I tools/path.py grid LOG [LOG ...] [--out F]    path/0005: the model on the tie's grid, frozen rules against the code's, bit attribution, the rest

The logs are those of tools/gdb/path.gdb (docs/findings/path/0001 § 13; tools/path_sessions.py). One PLAN is a PLN line, its PLU/PLG/PLC lines
when the request reaches a planner, and its PLX line. The model is the planners of tools/path_emu1.py .. path_emu3.py (run:2026-11-03-path-emu-1..3,
read from the game's code), fed with what the log holds:

  * a plan that reaches a planner (a PLC line): the LIVE cells of the window's rooms (PLG, at the planner call, after the unit's own marks are off),
    the request context and the path record as the planner sees them. The model's output is compared with the game's PLX line: the return
    (`eax`), the points (the record's point words, as many as the model returns), and the exit seed of the unit (unchanged unless the planner draws:
    type 10, type 16). The tail of PathPlan (the aim, the "every point at the position" refusal) is modelled with `path_emu1.aim` [I];
  * a straight plan (path flag 0x40000: types 4, 10, 14): the entry record, the model of `PathPlanStraight` (to-unit, random walk, spiral);
  * a plan refused before a planner (no PLC line): the return must be 0 and the seed unchanged; the reason is predicted from the record where it
    needs no grid (the target unit at 0, the start or target 0, target = start, the window, no room), else `refused:rooms-town-or-free`.

Nothing here reads a collision prediction for the comparison: the grids are the game's. The TIE (scoping question 3) compares the live cells with
the built map (`CB`, pilot.py) plus the unit list's marks for the first plans of each game and for all of them (`tie`).

Live controls: for every planner family each control of path_emu1..3's CONTROLS list is run on the same plans, and must fail every plan it
separates and pass none; the comparator is itself tested by mutating the logged return, one point and the exit seed of every matched plan (each must be
reported); a cell-flip control flips a cell the model tested and counts the plans whose output it changes (the model reads the live grid). A control
that separates 0 plans in a log says so: it proves nothing there.
"""
import argparse
import base64
import collections
import csv
import json
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import path_emu1 as P1  # noqa: E402
import path_emu2 as P2  # noqa: E402
import path_emu3 as P3  # noqa: E402

REGISTER = os.path.join(ROOT, "workspace", "logs", "r54a", "p1-register.txt")
LINE = re.compile(r"^([A-Z][A-Z0-9]*) (\{.*\})\s*$")
KEEP = ("AGM", "PLN", "PLG", "PLC", "PLX", "BRK", "S3C", "CAP", "CB", "PLR", "SEEDW")
# the planner addresses
PL = {0x00679C80: "greedy", 0x00679ED0: "near", 0x00679F70: "onept", 0x0067A000: "knock", 0x0067B850: "type1", 0x0067C2D0: "type15",
      0x0067AD00: "search", 0x00679E50: "type3", 0x00679FD0: "type11", 0x00679E60: "type12"}
CONTROLS = {
    "greedy": ("ctxroom", "order", "noflag", "rev", "dist", "refresh", "limit", "param0"),
    "near": ("le325", "noretry", "order", "noflag"),
    "knock": ("k", "floor", "ctxroom"),
    "onept": ("ctxroom",),
    "type1": ("h", "cost", "list", "offs", "gt0", "nostart", "resort", "pool", "max77", "min2"),
    "type15": ("lim40", "lim18", "min2", "reduce", "wswap", "noswap", "lim50"),
    "search": ("h", "cost", "tries", "row", "step", "regrid", "passes", "margin", "union"),
    "type4": (),
    "rwalk": ("shr", "n1", "step1", "accum", "noadd"),
    "spiral": ("swap", "round"),
}
FLOORS = {1: 100, 2: 100, 4: 100, 7: 100, 8: 100, 10: 100, 13: 100, 15: 100, 5: 30, 6: 30, 9: 30, 14: 30}
TOTAL_FLOOR = 2000
BREAK_FNS = {0x00679E50: "type 3", 0x00679FD0: "type 11", 0x00679E60: "type 12", 0x00663E00: "type-16 A", 0x00663ED0: "type-16 B"}
MARKED_OFF_MODES = (0, 12, 17)
_GRID_TABLES = None
ITEM_GROUND_MODES = (3, 5)       # an item unit's mode on the ground (3) or dropping (5): the 0x200 mark (drlg/0005 § 6, ground items)


def unz(s):
    return zlib.decompress(base64.b64decode(s))


def seed_of(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def seed_str(t):
    return "%08x:%08x" % (t[0] & 0xFFFFFFFF, t[1] & 0xFFFFFFFF)


class Plan:
    __slots__ = ("k", "game", "log", "pln", "plc", "plx", "rooms", "cb", "n")

    def __init__(self, k, game, log, pln):
        self.k, self.game, self.log, self.pln = k, game, log, pln
        self.plc = self.plx = None
        self.rooms = {}
        self.cb = {}
        self.n = 0

    @property
    def ty(self):
        return self.pln["ty"]

    @property
    def straight(self):
        return bool(self.pln["fl"] & 0x40000)

    @property
    def unit_type(self):
        return self.pln["u"][0]


class Game:
    def __init__(self, log, index):
        self.log, self.index = log, index
        self.plans = []
        self.brk = []
        self.s3c = []
        self.seedw = []
        self.caps = []
        self.rooms = {}          # (addr, hash) -> {"r", "mr", "nr", "cells"}
        self.cb = {}             # room -> (rect, cells list)
        self.plr = 0


def parse(path):
    """One Game per AGM line (a log of a fresh process holds one)."""
    games = []
    g = None
    cur = None
    byk = {}
    with open(path, errors="replace") as fh:
        for line in fh:
            m = LINE.match(line)
            if not m or m.group(1) not in KEEP:
                continue
            tag = m.group(1)
            try:
                d = json.loads(m.group(2))
            except ValueError:
                continue
            if tag == "AGM":
                g = Game(path, len(games))
                games.append(g)
                byk = {}
                continue
            if g is None:
                continue
            if tag == "CB":
                z = d.get("z")
                if not z:
                    continue
                c = json.loads(unz(z)).get("cells")
                if c and c[4]:
                    g.cb[d["room"]] = (d["rect"], c[:4], list(struct.unpack("<%dH" % (len(c[4]) // 4), bytes.fromhex(c[4]))))
            elif tag == "PLN":
                pl = Plan(d["n"], g.index, path, d)
                pl.pln["rec"] = unz(d["rec"])
                g.plans.append(pl)
                byk[d["n"]] = pl
            elif tag == "PLG":
                cells = list(struct.unpack("<%dH" % (len(unz(d["z"])) // 2), unz(d["z"]))) if d["z"] else None
                g.rooms[(d["a"], d["h"], d.get("nh"))] = {"r": d["r"], "mr": d.get("mr"), "nr": d["nr"], "cells": cells, "lid": d.get("lid")}
            elif tag == "PLC":
                pl = byk.get(d["k"])
                if pl:
                    d["rec"] = unz(d["rec"])
                    d["ctx"] = bytes.fromhex(d["ctx"])
                    pl.plc = d
                    pl.rooms = {e[0]: g.rooms[tuple(e) if len(e) == 3 else (e[0], e[1], None)] for e in d["rm"] if (tuple(e) if len(e) == 3 else (e[0], e[1], None)) in g.rooms}
                    pl.cb = {e[0]: g.cb.get(e[0]) for e in d["rm"]}
            elif tag == "PLX":
                pl = byk.get(d["k"])
                if pl:
                    d["rec"] = unz(d["rec"])
                    pl.plx = d
            elif tag == "BRK":
                g.brk.append(d)
            elif tag == "S3C":
                g.s3c.append(d)
            elif tag == "SEEDW":
                g.seedw.append(d)
            elif tag == "CAP":
                g.caps.append(d)
    return games


# ------------------------------------------------------------------------------------------------------ the model
class Stub(dict):
    """The rooms of a straight plan: type 4's rectangle test only sets a flag the check does not compare."""

    def __missing__(self, k):
        class S:
            def has(self, x, y):
                return True
        return S()


class Unmodelled(Exception):
    pass


def mk_world(plan):
    """Room objects of the plan's window, from the live cells, and the model memory for the record."""
    rooms = []
    byaddr = {}
    for a, g in plan.rooms.items():
        if g["cells"] is None:
            continue
        if g["mr"] and g["mr"] != g["r"]:
            raise Unmodelled("room rect differs from its map's")
        x0, y0, w, h = g["r"]
        r = P2.Room(len(rooms), (x0, y0, w, h), list(g["cells"]), "live")
        r.addr = a
        rooms.append(r)
        byaddr[a] = r
    for r in rooms:
        r.near = [byaddr[a] for a in plan.rooms[r.addr]["nr"] if a in byaddr]
    return byaddr


def mk_mem(plan, rec, seed):
    """The model's memory: the path record (pointer fields remapped), the unit and the target unit."""
    M = P1.Mem()
    b = bytearray(rec)
    struct.pack_into("<I", b, 0x30, P3.UNIT)
    tg = plan.pln["tg"]
    if tg:
        struct.pack_into("<I", b, 0x58, P3.TARGET)
    M.w(P3.UPATH, bytes(b), False)
    M.w32(P3.UNIT, plan.unit_type)
    M.w32(P3.UNIT + 0x2C, P3.UPATH)
    M.w32(P3.UNIT + 0x20, seed[0])
    M.w32(P3.UNIT + 0x24, seed[1])
    if tg:
        M.w32(P3.TARGET, tg[0])
        M.w32(P3.TARGET + 0x2C, P3.TPATH)
        x, y = tg[4] or 0, tg[5] or 0
        if tg[0] == 2 or 4 <= tg[0] <= 5:
            M.w32(P3.TPATH + 0xC, x)
            M.w32(P3.TPATH + 0x10, y)
        else:
            M.w16(P3.TPATH + 2, x)
            M.w16(P3.TPATH + 6, y)
    return M


def points_of(M, n):
    return tuple(M.r32(P3.UPATH + 0x9C + 4 * i) for i in range(min(n, 78)))


def ctx_case(plan):
    c = plan.plc["ctx"]
    sx, sy, tx, ty, room, troom = struct.unpack_from("<HHHHII", c, 0)
    refresh, limit, b1c, typ, size, pattern, mask, path = c[0x14], struct.unpack_from("<I", c, 0x18)[0], c[0x1C], \
        struct.unpack_from("<i", c, 0x20)[0], struct.unpack_from("<i", c, 0x24)[0], struct.unpack_from("<i", c, 0x28)[0], \
        struct.unpack_from("<I", c, 0x2C)[0], struct.unpack_from("<I", c, 0x30)[0]
    return {"s": P3.mk(sx, sy), "t": P3.mk(tx, ty), "room": room, "troom": troom, "refresh": refresh, "limit": limit, "b1C": b1c, "type": typ,
            "pattern": pattern, "mask": mask, "fn": plan.plc["pl"]}


def tail(M, n, neg=None):
    """PathPlan's tail after the planner (path/0001 § 6, [I]): the count into +0x28, 0 clears; the aim; every point at the position is a refusal."""
    if n == 0:
        return 0
    M.w32(P3.UPATH + 0x28, n, False)
    if neg == "notail":
        return n
    P1.aim(M, P3.UPATH, 1, 1)
    if P1.s32(M.r32(P3.UPATH + 0x24)) >= n:
        return 0
    return n


def predict_planner(plan, neg=None, flips=None):
    """The model for a plan that reached a planner: dict(eax, pts, seed, label, tested)."""
    fn = plan.plc["pl"]
    name = PL.get(fn)
    if name is None:
        raise Unmodelled("planner %08x" % fn)
    R = mk_world(plan)
    case = ctx_case(plan)
    if case["room"] not in R:
        raise Unmodelled("the unit's room has no map")
    if flips:
        for (a, i, v) in flips:
            R[a].c[i] = v
    seed = seed_of(plan.plc["s"])
    M = mk_mem(plan, plan.plc["rec"], seed)
    M.w(P3.CTX, b"\0" * 0x34, False)
    case["b"] = M.b
    tested = []
    orig = P2.ptb

    def spy(Rr, hint, x, y, pattern, mask):
        tested.append((hint, x & 0xFFFF, y & 0xFFFF, pattern, mask))
        return orig(Rr, hint, x, y, pattern, mask)

    if flips is None:
        P2.ptb = spy
    try:
        stat = {}
        if name == "search":
            case["seed"] = seed
            S = P2.Search(case, R, {}, neg)
            o = S.run()
            if o.get("assert"):
                raise Unmodelled("search rectangle over 50 000 cells")
            n = o["eax"]
            pts = o["points"] or []
            for i, p in enumerate(pts):
                M.w32(P3.UPATH + 0x9C + 4 * i, p, False)
            stat = {"draws": o.get("draws", 0), "end": o.get("end")}
            seed = o["seed"] if o.get("seed") else seed
            label = "search:" + str(o.get("end"))
        else:
            c = P3.C(case, R, M, neg)
            n = P3.PLANNERS[fn](c)
            stat = c.stat
            label = name
            if name == "near":
                label = "near:" + ("type1" if stat.get("t1") else "greedy")
            elif name == "type1":
                label = "type1"
        eax = tail(M, n, neg)
        return {"eax": eax, "n": n, "pts": points_of(M, n) if eax else (), "seed": seed, "label": label, "tested": tested, "stat": stat,
                "ppts": points_of(M, n)}
    except P3.Assert as e:
        raise Unmodelled("model assert %x" % e.line)
    except KeyError as e:
        raise Unmodelled("model read: %s" % e)
    finally:
        P2.ptb = orig


def predict_straight(plan, neg=None):
    rec = plan.pln["rec"]
    seed = seed_of(plan.pln["s0"])
    M = mk_mem(plan, rec, seed)
    ty = plan.ty
    try:
        if ty == 4:
            n = P1.plan_to_unit(M, Stub(), P3.UPATH)
            return {"eax": n, "n": n, "pts": points_of(M, n) if n else (), "seed": seed, "label": "type4", "stat": {}}
        if ty == 10:
            st = {}
            n = P3.rwalk(M, P3.UNIT + 0x20, neg, st)
            return {"eax": n, "n": n, "pts": points_of(M, n), "seed": (M.r32(P3.UNIT + 0x20), M.r32(P3.UNIT + 0x24)), "label": "rwalk",
                    "stat": st}
        if ty == 14:
            st = {}
            n = P3.spiral(M, "emu" if neg == "round" else neg, st)
            return {"eax": n, "n": n, "pts": points_of(M, n), "seed": seed, "label": "spiral", "stat": st}
    except KeyError as e:
        raise Unmodelled("model read: %s" % e)
    raise Unmodelled("straight type %d" % ty)


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def refusal_reason(plan):
    """The reason a request ends before a planner, where the record alone gives it (path/0001 § 1); None when it needs rooms, the town test or the grid."""
    rec = plan.pln["rec"]
    tg = plan.pln["tg"]
    if tg and (not (tg[4] or 0) or not (tg[5] or 0)):
        return "target-unit-at-0"
    sx, sy = u16(rec, 2), u16(rec, 6)
    if sx == 0 and sy == 0:
        return "start-0"
    tx, ty = u16(rec, 0x10), u16(rec, 0x12)
    if tg:
        tx, ty = tg[4] & 0xFFFF, tg[5] & 0xFFFF
        if tg[0] in (0, 1) and rec[0x68]:
            return None                                                  # the x87 offset: not modelled
        if tg[0] == 2 and len(tg) > 6 and tg[6]:
            return None                                                  # the object step moves the target
    if tx == 0 and ty == 0:
        return "target-0"
    if (tx, ty) == (sx, sy):
        return "target=start"
    if abs(tx - sx) > 100 or abs(ty - sy) > 100:
        return "window"
    if struct.unpack_from("<I", rec, 0x1C)[0] == 0:
        return "no-room"
    return None


def compare(plan, pred):
    """List of differences between the model and the PLX line ([] = match)."""
    x = plan.plx
    bad = []
    if x is None:
        return ["no PLX line"]
    if x["eax"] != pred["eax"]:
        bad.append("eax %d != model %d" % (x["eax"], pred["eax"]))
    n = pred["eax"] if pred["eax"] else 0
    if pred.get("ppts") is not None and not pred["eax"]:
        n = 0
    if n:
        got = tuple(struct.unpack_from("<%dI" % n, x["rec"], 0x9C))
        if got != tuple(pred["pts"][:n]):
            bad.append("points differ at %d" % next(i for i in range(n) if got[i] != pred["pts"][i]))
    if x["s"] != seed_str(pred["seed"]):
        bad.append("seed %s != model %s" % (x["s"], seed_str(pred["seed"])))
    return bad


def evaluate(plan, neg=None):
    """(kind, pred or reason): kind in model, refused, unmodelled."""
    if plan.straight:
        return "model", predict_straight(plan, neg)
    if plan.plc:
        return "model", predict_planner(plan, neg)
    return "refused", refusal_reason(plan)


# ------------------------------------------------------------------------------------------------------ the check
def load_register():
    reg = {}
    if os.path.exists(REGISTER):
        for line in open(REGISTER):
            m = re.match(r"R ([0-9A-F]{8}) .*owner=(.+?) type=(\S+)", line)
            if m:
                reg[int(m.group(1), 16) + 5] = (m.group(2), m.group(3))
    return reg


def size_class(n):
    return "0" if n == 0 else ("1" if n == 1 else ("2-5" if n <= 5 else ("6-20" if n <= 20 else "21+")))


class Result:
    def __init__(self):
        self.rows = []                           # per plan dicts
        self.mismatch = []
        self.unmodelled = collections.Counter()
        self.controls = {}                       # (family, control) -> [separating, passed]
        self.mut = collections.Counter()
        self.flip = collections.Counter()
        self.spiral = collections.Counter()
        self.nocaller = []


def control_family(plan):
    if plan.straight:
        return {4: "type4", 10: "rwalk", 14: "spiral"}.get(plan.ty)
    if plan.plc:
        n = PL.get(plan.plc["pl"])
        return n


def run_controls(plans, res, matched):
    """Every control on the same plans: separating = its prediction differs from the model's; passed = it equals the game's line."""
    for plan, base in matched:
        fam = control_family(plan)
        names = CONTROLS.get(fam, ())
        if fam == "search":
            names = names
        for neg in names:
            key = (fam, neg)
            row = res.controls.setdefault(key, [0, 0])
            try:
                _, pred = evaluate(plan, neg)
            except (Unmodelled, Exception):
                row[0] += 1                     # a model that cannot run the control's variant separates
                continue
            if pred_key(pred) != pred_key(base):
                row[0] += 1
                if not compare(plan, pred):
                    row[1] += 1


def pred_key(p):
    return (p["eax"], tuple(p["pts"][:p["eax"]]) if p["eax"] else (), p["seed"])


def mutate_controls(plans, res):
    """The comparator tested on the logs themselves: a changed return, point or seed in the game's line must be reported."""
    for plan, base in plans:
        x = plan.plx
        kept = (x["eax"], x["s"], x["rec"])
        tests = []
        tests.append(("eax", lambda: x.__setitem__("eax", x["eax"] + 1)))
        tests.append(("seed", lambda: x.__setitem__("s", seed_str((seed_of(x["s"])[0] ^ 1, seed_of(x["s"])[1])))))
        if base["eax"]:
            def pt():
                b = bytearray(x["rec"])
                b[0x9C] ^= 1
                x["rec"] = bytes(b)
            tests.append(("point", pt))
        for name, f in tests:
            f()
            bad = compare(plan, base)
            res.mut[(name, bool(bad))] += 1
            x["eax"], x["s"], x["rec"] = kept


def flip_controls(matched, res):
    """A cell the model tested, set blocked in the model's copy of the live grid: the plans whose output changes read the live cells."""
    for plan, base in matched:
        if not plan.plc or not base.get("tested"):
            continue
        res.flip["plans"] += 1
        a, x, y, pat, mask = base["tested"][0]
        r = None
        R = mk_world(plan)
        for rr in R.values():
            if rr.has(x, y):
                r = rr
                break
        if r is None:
            continue
        idx = (y - r.y0) * r.w + (x - r.x0)
        for v in (0xFFFF, 0):
            try:
                pred = predict_planner(plan, None, [(r.addr, idx, v)])
            except Unmodelled:
                continue
            if pred_key(pred) != pred_key(base):
                res.flip["changed"] += 1
                break


def check(paths, out, quiet=False):
    res = Result()
    reg = load_register()
    matched = []
    games = []
    for p in paths:
        games += parse(p)
    plans = [pl for g in games for pl in g.plans]
    byty = collections.defaultdict(lambda: collections.Counter())
    for plan in plans:
        ty = plan.ty
        row = byty[ty]
        row["plans"] += 1
        if plan.plx is None:
            row["noplx"] += 1
            res.unmodelled["no PLX line"] += 1
            continue
        owner = reg.get(plan.pln["ra"])
        if plan.unit_type == 0:
            who = "player"
        else:
            who = owner[0] if owner else "?"
        row["by:" + who] += 1
        if owner is None and plan.pln["ra"] not in reg and reg:
            res.nocaller.append(plan.k)
        try:
            kind, pred = evaluate(plan)
        except Unmodelled as e:
            row["unmodelled"] += 1
            res.unmodelled[str(e)] += 1
            continue
        if kind == "refused":
            row["refused"] += 1
            bad = []
            if plan.plx["eax"] != 0:
                bad.append("refused request returned %d" % plan.plx["eax"])
            if plan.plx["s"] != plan.pln["s0"]:
                bad.append("seed moved on a refusal")
            lab = pred or "rooms-town-or-free"
            row["out:refused:" + lab] += 1
            if bad:
                res.mismatch.append((plan, bad))
                row["mismatch"] += 1
            else:
                row["match"] += 1
            continue
        if plan.plc or plan.straight:
            row["reached"] += 1
        bad = compare(plan, pred)
        row["out:" + pred["label"]] += 1
        row["ret:" + size_class(plan.plx["eax"])] += 1
        row["pts_max"] = max(row["pts_max"], plan.plx["eax"])
        if plan.plx["s"] != plan.pln["s0"]:
            row["draws"] += 1
        if bad:
            row["mismatch"] += 1
            res.mismatch.append((plan, bad))
        else:
            row["match"] += 1
            matched.append((plan, pred))
            if plan.unit_type == 1 and plan.plx["s"] == plan.pln["s0"]:
                row["nodraw"] += 1                                       # a monster's plan exit with the unit seed unchanged
            if who == "movement":
                row["replan"] += 1
                if plan.pln["tg"]:
                    row["replan-tg"] += 1
        if plan.ty == 14:
            alt = predict_straight(plan, "round")
            row_t = not compare(plan, pred)
            row_r = not compare(plan, alt)
            sep = pred_key(pred) != pred_key(alt)
            res.spiral[("separating" if sep else "same", "trunc" if row_t else "-", "round" if row_r else "-")] += 1
    run_controls(plans, res, matched)
    mutate_controls(matched, res)
    flip_controls(matched, res)
    return games, plans, byty, res, matched


def grid_tables(excel=None):
    """The two table inputs of the grid rules (path/0005): object class -> HasCollision0..7, monster class -> deadCol. Cached; `excel` for the tests."""
    global _GRID_TABLES
    if excel is None and _GRID_TABLES is not None:
        return _GRID_TABLES
    d = excel if isinstance(excel, str) else os.environ.get("PATH_EXCEL") or os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")

    def tsv(name):
        with open(os.path.join(d, name), errors="replace") as fh:
            return list(csv.DictReader(fh, delimiter="\t"))
    hc = {}
    for r in tsv("objects.txt"):
        if (r.get("Id") or "").strip():
            hc[int(r["Id"])] = tuple(int(r["HasCollision%d" % i] or 0) for i in range(8))
    ex = {r["Id"]: int(r.get("deadCol") or 0) for r in tsv("monstats2.txt") if r.get("Id")}
    dc = {}
    for r in tsv("monstats.txt"):
        if (r.get("hcIdx") or "").strip():
            dc[int(r["hcIdx"])] = ex.get(r.get("MonStatsEx"), 0)
    _GRID_TABLES = (hc, dc)
    return _GRID_TABLES


def object_marked(u, hc):
    """Rule O1 of path/0005: an object's rectangle is in the grid when the byte HasCollision[mode] of its class is set. Rev 5's entry carries the byte."""
    if len(u) >= 14:
        return bool(u[13])
    row = hc.get(u[2])
    mode = u[6]
    return bool(row and 0 <= mode < 8 and row[mode])


def tie_of(plan, cells=False, corpse=False, rules=None):
    """The live cells against the built map plus the unit list's marks for each room of the plan: (rooms compared, rooms exact, differing cells, bits).

    rules None: the frozen rules of `a501a7fa` (every object marks; a dead monster unmarked), with `corpse` the frozen hold-out reading of `178106ec`.
    rules "code": the rules read from the code in path/0005 (object_marked; corpse_mark), `corpse` ignored.
    """
    if not plan.plc:
        return None
    R = mk_world(plan)
    base = {}
    for a, r in R.items():
        cb = plan.cb.get(a)
        if cb is None or list(cb[0]) != list(plan.rooms[a]["r"]) or len(cb[2]) != len(r.c):
            continue
        base[a] = list(cb[2])
    if not base:
        return {"compared": 0}
    pred = {a: P2.Room(R[a].i, tuple(plan.rooms[a]["r"]), base[a], "pred") for a in base}
    for a, r in pred.items():
        r.addr = a
    for a, r in pred.items():
        r.near = [pred[n.addr] for n in R[a].near if n.addr in pred]
    selfu = plan.plc["self"]
    tgt = plan.plc.get("tgt")
    dropped = 0
    tables = grid_tables() if rules == "code" else None
    for u in plan.plc["u"]:
        if u[0] == 4:
            if len(u) >= 7 and u[5] in pred and u[6] in ITEM_GROUND_MODES:
                cell_op(pred, u[5], u[3], u[4], 0x200)
            continue
        if u[0] == 2:
            if len(u) >= 13 and u[5] in pred:
                _, uid, cls, x, y, room, mode, sx, sy, door, b13b, b167, b1b6 = u[:13]
                if rules == "code" and not object_marked(u, tables[0]):
                    continue
                if rules == "code" and tgt and uid == tgt[1] and tgt[0] == 2 and plan.pln["fl"] & 0x800:
                    continue                                     # rule T1: PathPlan's target unmark under flag 0x800 (0x00649B1A..0x00649B25)
                if door:
                    mask = (0x804 if b1b6 else 0x400) if not b13b else 0x806
                else:
                    mask = 0x8000 if b167 & 4 else (0x404 if b1b6 else 0x400)
                rect_wh_op(pred, room, x, y, sx, sy, mask)
            continue
        t, uid, cls, mode, x, y, room, size, pat, mask, fl = u
        if (t, uid) == tuple(selfu):
            continue
        if tgt and (t, uid) == tuple(tgt) and plan.pln["fl"] & 0x800:
            continue
        if rules == "code" and t == 1 and mode in (0, 12):
            if room in pred:
                corpse_mark(pred, room, x, y, pat, mask, tables[1].get(cls, 0))
            continue
        if corpse and rules is None and mode == 12 and mask == 0x100 and room in pred:
            size_op(pred, room, x, y, 3, 0x8000)                 # the reading fitted on the development logs: a dead monster's 3 x 3 of 0x8000
        if mode in MARKED_OFF_MODES:
            continue
        if room not in pred:
            dropped += 1
            continue
        if t == 3:
            size_op(pred, room, x, y, size, mask)
        else:
            pattern_op(pred, room, x, y, pat, mask)
    bits = 0
    ncell = 0
    exact = 0
    detail = collections.Counter()
    cl = []
    for a, r in pred.items():
        d = [(i, p ^ l) for i, (p, l) in enumerate(zip(r.c, R[a].c)) if p != l]
        if cells:
            cl += [(a, r.x0 + i % r.w, r.y0 + i // r.w, r.c[i], R[a].c[i]) for i, _ in d]
        if not d:
            exact += 1
        for i, x in d:
            ncell += 1
            bits |= x
            for b in range(16):
                if x >> b & 1:
                    detail[1 << b] += 1
    return {"compared": len(pred), "exact": exact, "cells": ncell, "bits": bits, "detail": detail, "outside": dropped, "diff": cl}


def corpse_mark(R, room, x, y, pat, mask, dead_col):
    """Rules C1..C3 of path/0005, the server's dead monster: created dead the plus of its record (pattern 5, 0x8000); `deadCol` 1 its live mark; else the 3 x 3."""
    if mask == 0x8000:
        pattern_op(R, room, x, y, pat, mask)
    elif dead_col:
        pattern_op(R, room, x, y, pat, mask)
    else:
        size_op(R, room, x, y, 3, 0x8000)


def cell_op(R, hint, x, y, v):
    r = P2.room_at(R, hint, x, y) if hint in R else None
    if r is None:
        return
    r.c[(y - r.y0) * r.w + (x - r.x0)] |= v


def pattern_op(R, hint, x, y, p, m):
    plus = ((-1, 0), (0, 0), (1, 0), (0, -1), (0, 1))
    if p in (1, 3):
        for dx, dy in plus:
            cell_op(R, hint, x + dx, y + dy, m)
        if m:
            cell_op(R, hint, x, y, 0x1000 if p == 1 else 0x2000)
    elif p in (2, 4):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                cell_op(R, hint, x + dx, y + dy, m)
        if m:
            for dx, dy in plus:
                cell_op(R, hint, x + dx, y + dy, 0x1000 if p == 2 else 0x2000)
    elif p == 5:
        for dx, dy in plus:
            cell_op(R, hint, x + dx, y + dy, m)


def rect_wh_op(R, hint, x, y, w, h, m):
    """COLL_RectOrWH 0x0064DE30: the rectangle of w x h around (x, y) (w / 2 unsigned)."""
    if w == 1 and h == 1:
        cell_op(R, hint, x, y, m)
        return
    l, t = x - (w >> 1), y - (h >> 1)
    for yy in range(t, t + h):
        for xx in range(l, l + w):
            cell_op(R, hint, xx, yy, m)


def size_op(R, hint, x, y, s, m):
    if s == 1:
        cell_op(R, hint, x, y, m)
    elif s == 2:
        pattern_op(R, hint, x, y, 5, m)
    elif s == 3:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                cell_op(R, hint, x + dx, y + dy, m)


# ---------------------------------------------------------------------------------------------------- the report
def report(paths, out=sys.stdout, first=10):
    games, plans, byty, res, matched = check(paths, out)
    w = lambda s="": print(s, file=out)
    sessions = len(games)
    nmatch = sum(r["match"] for r in byty.values())
    nmis = sum(r["mismatch"] for r in byty.values())
    nunm = sum(r["unmodelled"] + r["noplx"] for r in byty.values())
    reached = sum(r["reached"] for r in byty.values())
    w("PATH check logs=%d games=%d plans=%d reached-a-planner=%d matched=%d mismatched=%d unmodelled=%d" % (
        len(paths), sessions, len(plans), reached, nmatch, nmis, nunm))
    w()
    w("OUTCOME MIX per path type (plans = PLN lines; reached = a planner was called or the type is straight; match counts refusals that agree)")
    w("type  plans reached refused match mismatch  ret0 ret1 ret2-5 ret6-20 ret21+  maxret draws  callers")
    straight = {4, 10, 14}
    for ty in sorted(byty):
        r = byty[ty]
        callers = ",".join("%s=%d" % (k[3:], v) for k, v in sorted(r.items()) if k.startswith("by:"))
        w("%4d %6d %7d %7d %5d %8d  %4d %4d %6d %7d %6d  %6d %5d  %s" % (
            ty, r["plans"], r["reached"] + (0 if ty not in straight else 0), r["refused"], r["match"], r["mismatch"], r["ret:0"], r["ret:1"], r["ret:2-5"],
            r["ret:6-20"], r["ret:21+"], r["pts_max"], r["draws"], callers))
    w()
    w("OUTCOME LABELS per type")
    for ty in sorted(byty):
        labs = ", ".join("%s=%d" % (k[4:], v) for k, v in sorted(byty[ty].items()) if k.startswith("out:"))
        w("%4d  %s" % (ty, labs))
    w()
    w("FLOORS (matched plans per type; refusals included; the floor counts plans that agree with the model)")
    for ty, f in sorted(FLOORS.items()):
        n = byty[ty]["match"] if ty in byty else 0
        reach = (byty[ty]["match"] - byty[ty]["refused"]) if ty in byty else 0
        w("type %2d floor %3d  matched %4d (reached a planner or straight: %4d)  %s" % (ty, f, n, reach, "met" if reach >= f else "SHORT"))
    w("total matched %d of floor %d  %s" % (nmatch, TOTAL_FLOOR, "met" if nmatch >= TOTAL_FLOOR else "SHORT"))
    w()
    w("AI NO-DRAW PREDICTION (monster plans that reached a planner or a straight type, reproduced with the unit seed unchanged at the exit; floor 50 per AI type)")
    for ty in (1, 2, 5, 6, 7, 13, 15):
        n = byty[ty]["nodraw"] if ty in byty else 0
        w("  type %2d  %4d  %s" % (ty, n, "met" if n >= 50 else "SHORT"))
    rp = sum(r["replan"] for r in byty.values())
    rpt = sum(r["replan-tg"] for r in byty.values())
    w("REPLANS of anim/movement G1 (owner movement, reproduced): %d, with a target unit (the revalidation): %d  %s" % (rp, rpt, "met" if rp >= 50 else "SHORT"))
    w()
    w("CONTROLS (family control: separating plans, passed; a control that separates 0 plans here proves nothing in this log)")
    zero, passed = [], []
    for (fam, neg), (sep, ps) in sorted(res.controls.items()):
        w("  %-8s %-8s separating %5d passed %d" % (fam, neg, sep, ps))
        if sep == 0:
            zero.append((fam, neg))
        if ps:
            passed.append((fam, neg))
    w("  comparator mutations (changed return / seed / one point in the log must be reported): " + ", ".join(
        "%s detected %d of %d" % (k, res.mut[(k, True)], res.mut[(k, True)] + res.mut[(k, False)]) for k in ("eax", "seed", "point")))
    w("  cell flip: %d plans with a tested cell; flipping the first tested cell changed the model's output in %d" % (res.flip["plans"], res.flip["changed"]))
    w()
    if res.spiral:
        w("SPIRAL (type 14) truncation vs rounding: " + ", ".join("%s/%s/%s=%d" % (k[0], k[1], k[2], v) for k, v in sorted(res.spiral.items())))
        w()
    w("CHAINED DRAWS (the next write to the seed of a unit after its type-10 plan, a hardware watchpoint: the low dword must be the LCG step of the exit seed)")
    kinds = collections.Counter()
    for g in games:
        for e in g.seedw:
            lo, hi = seed_of(e["from"])
            lo2 = seed_of(e["to"])[0]
            ok = lo2 == ((lo * 0x6AC690C5 + hi) & 0xFFFFFFFF)
            pl = next((p for p in g.plans if p.k == e["k"]), None)
            if e.get("ctl"):
                kinds["control: " + ("a draw, the LCG step" if ok else "NOT the LCG step")] += 1
                continue
            kinds["chained (the low dword is the LCG step of the exit seed)" if ok else (
                "released without a draw (the low dword overwritten, 0 or an allocator link, the high dword as at the exit)"
                if seed_of(e["to"])[1] == hi else "neither")] += 1
            if pl is not None and pl.plx is not None and pl.plx["s"] != e["from"]:
                kinds["exit seed differs from the plan's PLX"] += 1
    nw = sum(len(g.seedw) for g in games)
    w("  watched writes %d: %s" % (nw, ", ".join("%s %d" % kv for kv in sorted(kinds.items())) or "none"))
    w()
    w("BREAK LINES")
    brk = collections.Counter()
    for g in games:
        for b in g.brk:
            brk[(b["fn"], b["side"], b["ctl"])] += 1
    for (fn, side, ctl), n in sorted(brk.items(), key=lambda kv: (kv[0][0], str(kv[0][1]), kv[0][2])):
        w("  %08x %-9s side=%s %s hits=%d" % (fn, BREAK_FNS.get(fn, "control: greedy"), side, "control" if ctl else "watch", n))
    srv = [b for g in games for b in g.brk if not b["ctl"] and b["side"] == "srv"]
    w("  server-caller hits on a watched function: %d" % len(srv))
    sites = collections.Counter()
    hits = 0
    for g in games:
        for s in g.s3c:
            sites[s["site"]] = max(sites[s["site"]], s["c"])
            hits += s["hit"]
    w("  +0x3C store sites seen %d of 22, stores of 3/11/12 observed: %d; sites: %s" % (
        len(sites), hits, " ".join("%08x:%d" % kv for kv in sorted(sites.items()))))
    w()
    w("TIE (live cells vs the built map plus the unit list's marks; first %d plans of each game, and all)" % first)
    for corpse in (False, True):
        tie_report(games, w, first, corpse)
    w()
    w("UNMODELLED: " + ("; ".join("%s=%d" % kv for kv in res.unmodelled.most_common()) or "none"))
    return finish(w, res, byty, plans, nmatch, nmis, nunm, zero, passed)


def tie_report(games, w, first, corpse):
    t_first = collections.Counter()
    t_all = collections.Counter()
    bits = collections.Counter()
    for g in games:
        k = 0
        for plan in g.plans:
            if not plan.plc:
                continue
            k += 1
            t = tie_of(plan, False, corpse)
            for tc, name in ((t_first, k <= first), (t_all, True)):
                if not name:
                    continue
                if t is None or not t["compared"]:
                    tc["plans without a built map"] += 1
                    continue
                tc["plans"] += 1
                tc["rooms"] += t["compared"]
                tc["rooms exact"] += t["exact"]
                tc["cells differing"] += t["cells"]
                tc["plans exact"] += 1 if t["exact"] == t["compared"] else 0
            if t and t.get("compared") and tc is not None:
                for b, n in t["detail"].items():
                    bits[b] += n
    w("  [%s] first plans: " % ("with the 3x3 corpse reading" if corpse else "units' own marks only") +
      ", ".join("%s %d" % kv for kv in sorted(t_first.items())))
    w("  [%s] all plans:   " % ("with the 3x3 corpse reading" if corpse else "units' own marks only") +
      ", ".join("%s %d" % kv for kv in sorted(t_all.items())))
    w("      differing bits (cells): " + (", ".join("0x%04x=%d" % kv for kv in sorted(bits.items())) or "none"))


def grid_report(paths, out=sys.stdout):
    """path/0005: the model on the tie's grid under the frozen rules and under the code's, the wrong plans by the bit alone sufficient, the residue by class."""
    w = lambda t="": print(t, file=out)
    games = [g for p in paths for g in parse(p)]
    for name, rules, corpse in (("frozen, units' own marks", None, False), ("frozen, the corpse reading", None, True), ("code rules O1, C1..C3, T1", "code", False)):
        total = collections.Counter()
        bits = collections.Counter()
        wrong = collections.Counter()
        by = collections.Counter()
        rest = []
        for g in games:
            for plan in g.plans:
                if not plan.plc or plan.plx is None:
                    continue
                t = tie_of(plan, True, corpse, rules)
                if not t or not t.get("compared"):
                    continue
                total["plans"] += 1
                total["rooms"] += t["compared"]
                total["rooms exact"] += t["exact"]
                total["cells"] += t["cells"]
                for b, n in t["detail"].items():
                    bits[b] += n
                if not t["diff"]:
                    continue
                R = mk_world(plan)
                fl = [(a, (y - R[a].y0) * R[a].w + (x - R[a].x0), pv, lv, x, y) for a, x, y, pv, lv in t["diff"]]

                def bad(fs):
                    try:
                        return bool(compare(plan, predict_planner(plan, None, fs)))
                    except Unmodelled:
                        return True
                if not bad([(f[0], f[1], f[2]) for f in fl]):
                    continue
                wrong[plan.ty] += 1
                hit = []
                for b in (0x2, 0x4, 0x40, 0x80, 0x100, 0x200, 0x400, 0x800, 0x1000, 0x2000, 0x8000):
                    fs = [(f[0], f[1], (f[3] & ~b) | (f[2] & b)) for f in fl if (f[2] ^ f[3]) & b]
                    if fs and bad(fs):
                        hit.append("0x%04x" % b)
                by[tuple(hit) or ("only together",)] += 1
                if rules:
                    key = [f for f in fl if bad([(f[0], f[1], f[2])])][:1]
                    players = [u for u in plan.plc["u"] if u[0] == 0]
                    rest.append((os.path.basename(g.log)[24:-4], plan.k, plan.pln["fr"], plan.ty, plan.pln["u"][:4], [(f[4], f[5], "%04x" % f[2], "%04x" % f[3]) for f in key],
                                 [(u[3], u[4], u[5], u[9]) for u in players][:1], len(plan.plc["u"]) >= 120))
        w("[%s] %s" % (name, ", ".join("%s %d" % kv for kv in sorted(total.items()))))
        w("  differing bits (cells): " + ", ".join("0x%04x=%d" % kv for kv in sorted(bits.items())))
        w("  wrong plans: %d of %d, by type %s" % (sum(wrong.values()), total["plans"], sorted(wrong.items())))
        w("  by the bit alone sufficient: %s" % sorted(by.items(), key=lambda kv: -kv[1]))
        for r in rest:
            w("  REST session %s k=%d fr=%d type=%d unit=%s decisive cell (x, y, model, live)=%s player (mode, x, y, mask)=%s at-unit-cap=%s" % r)
    return 0


def finish(w, res, byty, plans, nmatch, nmis, nunm, zero, passed):
    if res.nocaller:
        w("PLANS whose caller is not a PathPlan call site of the register: %d (first k %s)" % (len(res.nocaller), res.nocaller[:5]))
    w()
    for plan, bad in res.mismatch[:30]:
        w("MISMATCH %s k=%d type=%d ra=%08x: %s" % (os.path.basename(plan.log), plan.k, plan.ty, plan.pln["ra"], "; ".join(bad)))
    w("RESULT %s: %d mismatches over %d reproduced plans; %d unmodelled; controls passing a separated plan: %d; controls separating nothing: %d" % (
        "OK" if not nmis and not passed else "FAIL", nmis, nmatch, nunm, len(passed), len(zero)))
    return 0 if not nmis and not passed else 1


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("check", "mix", "tie", "grid"))
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--first", type=int, default=10)
    a = ap.parse_args(argv)
    out = open(a.out, "w") if a.out else sys.stdout
    try:
        if a.cmd == "grid":
            return grid_report(a.logs, out)
        return report(a.logs, out, a.first)
    finally:
        if a.out:
            out.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
