#!/usr/bin/env python3
"""Plan 0054 Phase 2 (`lane/p54`): per-event reproduction of `PathPlan`, the model and the check.

    python3 -I tools/path.py check LOG [LOG ...] [--out F]   reproduce every logged plan with the models, run the live controls, print the
                                                             outcome mix per type, the floors, the break lines and the grid tie, then the review sections
                                                             (the stock counts, controls per type, type 1 on the switch, the head backwards, the seed
                                                             watchpoints, corpse shapes; env PATH_DEV, PATH_IMAGE) and the `grid` report
    python3 -I tools/path.py mix|tie LOG [LOG ...] [--first N]  the check without the review sections
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
KEEP = ("AGM", "PLN", "PLG", "PLC", "PLX", "BRK", "S3C", "CAP", "CB", "PLR", "SEEDW", "SPX", "T1S", "L1M", "L1U", "COR")
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
ACT_FIRST_LEVEL = (40, 75, 103, 109)
_GRID_TABLES = None
# the seed watchpoint's writes that are not an LCG step: `rep stos` / `rep movs` over the unit's memory (path/0004 § 5), high dword as at the plan's exit
BLOCK_WRITE_PCS = {0x00681F4F: "rep stos", 0x00682A1A: "rep movs", 0x0057CAE6: "rep movs"}
ITEM_GROUND_MODES = (3, 5)       # an item unit's mode on the ground (3) or dropping (5): the 0x200 mark (drlg/0005 § 6, ground items)


def unz(s):
    return zlib.decompress(base64.b64decode(s))


def seed_of(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def seed_str(t):
    return "%08x:%08x" % (t[0] & 0xFFFFFFFF, t[1] & 0xFFFFFFFF)


class Plan:
    __slots__ = ("k", "game", "log", "pln", "plc", "plx", "rooms", "cb", "n", "w1", "l1")

    def __init__(self, k, game, log, pln):
        self.k, self.game, self.log, self.pln = k, game, log, pln
        self.plc = self.plx = None
        self.w1 = False
        self.l1 = ()
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
        self.spx = []            # logger rev 5
        self.t1s = []
        self.l1m = []
        self.l1u = []
        self.cor = []
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
            elif tag == "SPX":
                g.spx.append(d)
            elif tag == "T1S":
                g.t1s.append(d)
            elif tag == "L1M":
                g.l1m.append(d)
            elif tag == "L1U":
                g.l1u.append(d)
            elif tag == "COR":
                g.cor.append(d)
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


def units_cut(plan):
    """Whether the plan's unit list was cut: rev 5's PLC line says how many; rev 4 and before cut at 120 and did not say."""
    plc = plan.plc
    return plc.get("ucut", 0) > 0 if "ucut" in plc else len(plc["u"]) >= 120


def act_of(lid):
    """The act of a level id: the towns 1, 40, 75, 103, 109 open the acts (tbl:Levels.txt:Act)."""
    return sum(1 for t in ACT_FIRST_LEVEL if lid >= t)


def player_arrivals(g):
    """Rule W1 of path/0005: `PlayerChangeAct` leaves the player unmarked at the arrival, until it moves or its own plan's tail re-marks it (0x00649BE0).

    Walks a game's plans in log order, keeping the level of the player's entry in each unit list. Sets `plan.w1` on every planner plan that sees the player
    unmarked by the rule, and returns one record per level change, with the player's centre cell at the first plan of another unit that sees it unmoved."""
    out = []
    lid = None
    open_ = None                    # the record of the arrival under way
    w1 = False
    for plan in g.plans:
        if not plan.plc:
            continue
        me = next((u for u in plan.plc["u"] if u[0] == 0), None)
        room = plan.rooms.get(me[6]) if me else None
        now = room.get("lid") if room else None
        if now is not None and lid is not None and now != lid:
            open_ = {"log": g.log, "from": lid, "to": now, "act": int(act_of(now) != act_of(lid)), "k": None, "cell": None, "pos": (me[4], me[5])}
            out.append(open_)
            w1 = bool(open_["act"])
        if now is not None:
            lid = now
        if me is None:
            continue
        own = tuple(plan.plc["self"]) == (0, me[1])
        if open_ is not None and (me[4], me[5]) != open_["pos"]:
            open_ = None
            w1 = False
        if open_ is None:
            continue
        plan.w1 = w1 and not own
        if not own and open_["k"] is None and room is not None:
            r = P2.room_at(mk_world(plan), me[6], me[4], me[5])
            if r is not None:
                open_["k"], open_["cell"] = plan.k, r.cell(me[4], me[5])
        if own:
            open_ = None           # its tail re-marks it (0x00649BE0)
            w1 = False
    return out


def reserved_landings(g):
    """Rule L1 of path/0005: from a logger rev 5 log, for each planner plan the reserved points held at its call: an L1M line before the plan's PLC line, with no L1U of
    the same point, pattern and mask between. Sets `plan.l1` to (room, x, y, pattern, mask) tuples; returns how many plans hold one."""
    events = sorted([(e["n"], 1, e) for e in g.l1m] + [(e["n"], 0, e) for e in g.l1u] + [(p.plc["n"], 2, p) for p in g.plans if p.plc and "n" in p.plc], key=lambda v: v[0])
    held = []
    n = 0
    for _, kind, e in events:
        if kind == 1:
            held.append((e["room"], e["x"], e["y"], e["pat"], e["mask"]))
        elif kind == 0:
            for i, h in enumerate(held):
                if h[1:] == (e["x"], e["y"], e["pat"], e["mask"]):
                    del held[i]
                    break
        else:
            e.l1 = tuple(held)
            n += 1 if held else 0
    return n


def tie_of(plan, cells=False, corpse=False, rules=None):
    """The live cells against the built map plus the unit list's marks for each room of the plan: (rooms compared, rooms exact, differing cells, bits).

    rules None: the frozen rules of `a501a7fa` (every object marks; a dead monster unmarked), with `corpse` the frozen hold-out reading of `178106ec`.
    rules "code": the rules read from the code in path/0005 (object_marked; corpse_mark), `corpse` ignored. "code+w1": those and W1 (`plan.w1`, player_arrivals). "code+w1+l1": and L1, the
    reserved landings of a rev 5 log (`plan.l1`, reserved_landings).
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
    code = rules in ("code", "code+w1", "code+w1+l1")
    tables = grid_tables() if code else None
    for u in plan.plc["u"]:
        if u[0] == 4:
            if len(u) >= 7 and u[5] in pred and u[6] in ITEM_GROUND_MODES:
                cell_op(pred, u[5], u[3], u[4], 0x200)
            continue
        if u[0] == 2:
            if len(u) >= 13 and u[5] in pred:
                _, uid, cls, x, y, room, mode, sx, sy, door, b13b, b167, b1b6 = u[:13]
                if code and not object_marked(u, tables[0]):
                    continue
                if code and sx and tgt and uid == tgt[1] and tgt[0] == 2 and plan.pln["fl"] & 0x800:
                    continue                                     # rule T1: PathPlan's target unmark under flag 0x800 when UNIT_GetSizeX is not 0 (0x00649B10..0x00649B25)
                if door:
                    mask = (0x804 if b1b6 else 0x400) if not b13b else 0x806
                else:
                    mask = 0x8000 if b167 & 4 else (0x404 if b1b6 else 0x400)
                rect_wh_op(pred, room, x, y, sx, sy, mask)
            continue
        t, uid, cls, mode, x, y, room, size, pat, mask, fl = u
        if (t, uid) == tuple(selfu):
            continue
        if tgt and (t, uid) == tuple(tgt) and plan.pln["fl"] & 0x800 and (size or not code):
            continue
        if rules in ("code+w1", "code+w1+l1") and t == 0 and plan.w1:
            continue                                         # rule W1: the arrival of PlayerChangeAct is unmarked
        if code and t == 1 and mode in (0, 12):
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
    if rules == "code+w1+l1":
        for room, x, y, pat, mask in plan.l1:
            if room in pred:
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
    """Rules C1..C3 of path/0005, the server's dead monster: `deadCol` 1 its live mark; else the 3 x 3. A record already at pattern 5, 0x8000 was re-created dead: the corpse
    call's 3 x 3, then the plus inside it (drlg/lifecycle H5). A monster relocated dead holds the same record and only the plus at the new place; the list does not separate them."""
    if mask == 0x8000:
        size_op(R, room, x, y, 3, 0x8000)
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
def report(paths, out=sys.stdout, first=10, full=False):
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
                kinds["control: " + ("a draw, the LCG step" if ok else seedw_label(e))] += 1
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
        for key, n in brk_hits(g).items():
            brk[key] += n
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
    if full:
        w()
        review_sections([(session_of(g.log), g) for g in games], w)
        w()
        grid_report(paths, out, games)
    return finish(w, res, byty, plans, nmatch, nmis, nunm, zero, passed)


def brk_hits(g):
    """A game's hits per (fn, side, ctl): rev 5's lines carry the hit's count `c`, printed at the first 20 and at each power of two; before it each hit was a line."""
    hits = collections.Counter()
    for b in g.brk:
        key = (b["fn"], b["side"], b["ctl"])
        hits[key] = max(hits[key], b["c"]) if "c" in b else hits[key] + 1
    return hits


def tie_report(games, w, first, corpse):
    t_first = collections.Counter()
    t_level = collections.Counter()
    t_all = collections.Counter()
    bits = collections.Counter()
    for g in games:
        k = 0
        lev = collections.Counter()
        for plan in g.plans:
            if not plan.plc:
                continue
            k += 1
            lev[plan.pln["ar"]] += 1
            t = tie_of(plan, False, corpse)
            for tc, name in ((t_first, k <= first), (t_level, lev[plan.pln["ar"]] <= first), (t_all, True)):
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
    w("  [%s] first plans per level: " % ("with the 3x3 corpse reading" if corpse else "units' own marks only") +
      ", ".join("%s %d" % kv for kv in sorted(t_level.items())))
    w("  [%s] all plans:   " % ("with the 3x3 corpse reading" if corpse else "units' own marks only") +
      ", ".join("%s %d" % kv for kv in sorted(t_all.items())))
    w("      differing bits (cells): " + (", ".join("0x%04x=%d" % kv for kv in sorted(bits.items())) or "none"))


def grid_report(paths, out=sys.stdout, games=None):
    """path/0005: the model on the tie's grid under the frozen rules and under the code's, the wrong plans by the bit alone sufficient, the residue by class."""
    w = lambda t="": print(t, file=out)
    games = games if games is not None else [g for p in paths for g in parse(p)]
    arrivals = [a for g in games for a in player_arrivals(g)]
    passes = [("frozen, units' own marks", None, False), ("frozen, the corpse reading", None, True), ("code rules O1, C1..C3, T1", "code", False), ("code rules with W1", "code+w1", False)]
    if sum(reserved_landings(g) for g in games):
        passes.append(("code rules with W1 and L1", "code+w1+l1", False))
    for name, rules, corpse in passes:
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
                                 [(u[3], u[4], u[5], u[9]) for u in players][:1], units_cut(plan)))
        w("[%s] %s" % (name, ", ".join("%s %d" % kv for kv in sorted(total.items()))))
        w("  differing bits (cells): " + ", ".join("0x%04x=%d" % kv for kv in sorted(bits.items())))
        w("  wrong plans: %d of %d, by type %s" % (sum(wrong.values()), total["plans"], sorted(wrong.items())))
        w("  by the bit alone sufficient: %s" % sorted(by.items(), key=lambda kv: -kv[1]))
        for r in rest:
            w("  REST session %s k=%d fr=%d type=%d unit=%s decisive cell (x, y, model, live)=%s player (mode, x, y, mask)=%s at-unit-cap=%s" % r)
    w("W1 (path/0005): the player's level changes, by whether the act changed, and the 0x1000 bit of the player's centre cell at the first other unit's plan that sees the unmoved player")
    tab = collections.Counter()
    for a in arrivals:
        tab[("act changed" if a["act"] else "same act", "no plan saw it" if a["cell"] is None else ("marked" if a["cell"] & 0x1000 else "unmarked"))] += 1
    for k, n in sorted(tab.items()):
        w("  %-11s %-14s %d" % (k[0], k[1], n))
    for a in arrivals:
        w("  ARRIVAL %s lid %s -> %s act-changed=%d k=%s cell=%s" % (os.path.basename(a["log"])[24:-4], a["from"], a["to"], a["act"], a["k"], "-" if a["cell"] is None else "%04x" % a["cell"]))
    return 0


def seedw_label(e):
    """A seed watchpoint's line that is not the LCG step, by the writer's address: the block write, or a write this table has not named."""
    if e["pc"] in BLOCK_WRITE_PCS and seed_of(e["to"])[1] == seed_of(e["from"])[1]:
        return "block write %s %08x" % (BLOCK_WRITE_PCS[e["pc"]], e["pc"])
    return "other writer %08x" % e["pc"]


def session_of(p):
    return os.path.basename(p)[19:-4]


def empty_grid_counts(rows):
    """Section 5: the planner plans whose output differs when the same rooms hold no marks at all."""
    global mk_world
    orig = mk_world

    def empty(plan):
        R = orig(plan)
        for r in R.values():
            r.c = [0] * len(r.c)
        return R
    ng = collections.Counter()
    nt = collections.Counter()
    mk_world = empty
    try:
        for s, g, plan, pred in rows:
            if pred is None or not plan.plc:
                continue
            nt[plan.ty] += 1
            try:
                p = predict_planner(plan)
                if pred_key(p) != pred_key(pred):
                    ng[plan.ty] += 1
            except Unmodelled:
                ng[plan.ty] += 1
    finally:
        mk_world = orig
    return ng, nt


def review_sections(games, w):
    """What the kept logs say beyond the outcome mix (the architect's review of `lane/p54`, formerly its own tool, numbered as it was; sections 6 and 12 are `grid_report`):
    the plans after a probe's write; the natural spiral lists; the break control's cap and last hit; controls per path type with the model faults a control's exception hid;
    type 1's controls on greedy-near's switch; the plans whose output needs the grid; the tie's first plans; the head tested backwards; the seed watchpoints; the corpse shapes."""
    # ---- evaluate
    rows = []  # (session, game, plan, pred)
    for s, g in games:
        for plan in g.plans:
            if plan.plx is None:
                continue
            try:
                kind, pred = evaluate(plan)
            except Unmodelled:
                continue
            rows.append((s, g, plan, pred if kind == "model" else None))
    types = sorted({r[2].ty for r in rows})

    w("1. PLANS AFTER A PROBE'S WRITE (ADR-0003)")
    first = {}
    for s, g, plan, pred in rows:
        if plan.pln.get("probe") and s not in first:
            first[s] = plan.k
    for s, k in sorted(first.items()):
        w("  %s first write at plan k=%d; plans from there on %d of %d" % (
            s, k, sum(1 for r in rows if r[0] == s and r[2].k >= k), sum(1 for r in rows if r[0] == s)))
    w("  type  all  stock(without the plans from the first write on)  stock-reached  without those two sessions")
    for t in types:
        a = [r for r in rows if r[2].ty == t]
        st = [r for r in a if not (r[0] in first and r[2].k >= first[r[0]])]
        no = [r for r in a if r[0] not in first]
        w("  %4d %5d %5d %5d %5d" % (t, len(a), len(st), sum(1 for r in st if r[3] is not None), len(no)))
    a = [r for r in rows if not (r[0] in first and r[2].k >= first[r[0]])]
    w("  total %d, stock %d, without the two sessions %d" % (len(rows), len(a), sum(1 for r in rows if r[0] not in first)))
    w()

    w("2. NATURAL SPIRAL PLANS")
    rel = collections.Counter()
    fr = collections.Counter()
    bys = collections.Counter()
    for s, g, plan, pred in rows:
        if plan.ty != 14 or plan.pln.get("probe"):
            continue
        rec = plan.pln["rec"]
        fr[(struct.unpack_from("<H", rec, 0)[0], struct.unpack_from("<H", rec, 4)[0])] += 1
        sx, sy = struct.unpack_from("<H", rec, 2)[0], struct.unpack_from("<H", rec, 6)[0]
        pts = struct.unpack_from("<%dI" % plan.plx["eax"], plan.plx["rec"], 0x9C)
        rel[tuple(((p & 0xFFFF) - sx, (p >> 16) - sy) for p in pts)] += 1
        bys[("after a write" if s in first else "stock session", s)] += 1
    w("  start fractions %s; distinct point lists relative to the start: %d; by session %s" % (dict(fr), len(rel), sorted(bys.items())))
    w()

    w("3. BREAK CONTROL (cap 100 per side per game) AND THE WINDOW")
    w("  session  last server control frame, last client control frame, last greedy PLC frame, last S3C frame, last PLN frame")
    for s, g in games:
        srv = [b["fr"] for b in g.brk if b["ctl"] and b["side"] == "srv"]
        cli = [b["fr"] for b in g.brk if b["ctl"] and b["side"] == "cli"]
        gr = [p.plc.get("fr", p.pln["fr"]) for p in g.plans if p.plc and p.plc["pl"] == 0x00679C80]
        w("  %-22s srv %3d@%5d cli %3d@%5d greedyPLC %5d s3c %5d plans-to %5d" % (
            s, len(srv), max(srv or [0]), len(cli), max(cli or [0]), max(gr or [0]), max([x["fr"] for x in g.s3c] or [0]), max([p.pln["fr"] for p in g.plans] or [0])))
    srv = sum(max([b["fr"] for b in g.brk if b["ctl"] and b["side"] == "srv"] or [0]) for s, g in games)
    cli = sum(max([b["fr"] for b in g.brk if b["ctl"] and b["side"] == "cli"] or [0]) for s, g in games)
    end = sum(max([p.pln["fr"] for p in g.plans] or [0]) for s, g in games)
    w("  frames to the last plan, all sessions %d; to the server control's last line %d; to the client control's %d" % (end, srv, cli))
    ra = collections.Counter()
    for s, g in games:
        for b in g.brk:
            if not b["ctl"]:
                ra[(s, "%08x" % b["fn"], b["side"], b["ty"], "%08x" % b["ra"], "%08x" % (b["pra"] or 0))] += 1
    w("  watched hits (session, fn, side, path type, ra, pra): %s" % sorted(ra.items()))
    w()

    w("4. CONTROLS PER PATH TYPE (separating, of which the control's model raised, passed)")
    tab = collections.defaultdict(lambda: [0, 0, 0])
    for s, g, plan, pred in rows:
        if pred is None:
            continue
        fam = control_family(plan)
        names = list(CONTROLS.get(fam, ()))
        for neg in names:
            k = (plan.ty, fam, neg)
            e = tab[k]
            try:
                _, p = evaluate(plan, neg)
            except Exception:
                e[0] += 1
                e[1] += 1
                continue
            if pred_key(p) != pred_key(pred):
                e[0] += 1
                if not compare(plan, p):
                    e[2] += 1
    for k, e in sorted(tab.items()):
        w("  type %2d %-7s %-8s %5d %5d %d" % (k[0], k[1], k[2], e[0], e[1], e[2]))
    w("  type-1 controls on greedy-near's switch (never run by the check: its family is `near`)")
    t1 = [r for r in rows if r[3] is not None and r[3]["label"] == "near:type1"]
    w("  plans through the switch: %d; returns %s" % (len(t1), sorted(collections.Counter(min(r[3]["eax"], 6) for r in t1).items())))
    for neg in CONTROLS["type1"]:
        sep = rais = ps = 0
        for s, g, plan, pred in t1:
            try:
                _, p = evaluate(plan, neg)
            except Exception:
                sep += 1
                rais += 1
                continue
            if pred_key(p) != pred_key(pred):
                sep += 1
                if not compare(plan, p):
                    ps += 1
        w("  near:type1 %-8s %5d %5d %d" % (neg, sep, rais, ps))
    w()

    w("5. PLANS WHOSE OUTPUT NEEDS THE GRID (the model on the same rooms with every cell 0)")
    ng, nt = empty_grid_counts(rows)
    for t in sorted(nt):
        w("  type %2d planner plans %5d, output differs on an empty grid %5d" % (t, nt[t], ng[t]))
    w("  types 4, 10, 14: straight, the model reads no grid")
    w()

    w("7. THE TIE'S FIRST 10 PLANS OF EACH GAME: where, and which bits (not printed by the check)")
    lev = collections.Counter()
    ty = collections.Counter()
    bits = collections.Counter()
    sense = collections.Counter()
    units = collections.Counter()
    for s, g in games:
        k = 0
        for plan in g.plans:
            if not plan.plc:
                continue
            k += 1
            if k > 10:
                break
            lev[plan.pln["ar"]] += 1
            ty[plan.ty] += 1
            for u in plan.plc["u"]:
                units[u[0]] += 1
            t = tie_of(plan, True, False)
            for a, x, y, pv, lv in (t or {}).get("diff", ()):
                bits[pv ^ lv] += 1
                sense["model has it, live lacks it" if pv & (pv ^ lv) else "live has it, model lacks it"] += 1
    w("  levels %s; path types %s; unit-list entries by unit type %s" % (sorted(lev.items(), key=str), sorted(ty.items()), sorted(units.items())))
    w("  xor values %s; %s" % (sorted(bits.items()), sorted(sense.items())))
    w()

    w("8. THE HEAD, BACKWARDS: plans that reached a planner, tested with the record-only refusal reasons of path.py")
    rv = collections.Counter()
    ctx = collections.Counter()
    for s, g, plan, pred in rows:
        if not plan.plc:
            continue
        rv[str(refusal_reason(plan))] += 1
        rec = plan.pln["rec"]
        c = plan.plc["ctx"]
        ctx["ctx start = record start" if struct.unpack_from("<HH", c, 0) == (struct.unpack_from("<H", rec, 2)[0], struct.unpack_from("<H", rec, 6)[0]) else "ctx start differs"] += 1
    w("  %s; %s" % (sorted(rv.items()), sorted(ctx.items())))
    w()

    w("9. SEED WATCHPOINTS")
    cl = collections.Counter()
    wr = collections.Counter()
    for s, g, plan, pred in rows:
        if plan.ty == 10:
            cl[(plan.pln["u"][1])] += 1
    w("  type-10 plans by missile class: %s" % sorted(cl.items()))
    w("  type-10 plans by session: %s" % sorted(collections.Counter(r[0] for r in rows if r[2].ty == 10).items()))
    A, = (0x6AC690C5,)
    for s, g in games:
        byk = {p.k: p for p in g.plans}
        for e in g.seedw:
            lo, hi = seed_of(e["from"])
            l2, h2 = seed_of(e["to"])
            full = lo * A + hi
            pl = byk.get(e["k"])
            step = l2 == full & 0xFFFFFFFF
            wr[(s, "ctl" if e.get("ctl") else "ty10", "lcg" if step else seedw_label(e), "hi same" if h2 == hi else "hi moved", "lo 0" if l2 == 0 else "lo not 0")] += 1
            if e.get("ctl"):
                w("  ctl k=%d class=%s fr %d->%d from %s to %s pc %08x lcg=%d hi-after-step=%d st0=%08x" % (
                    e["k"], pl.pln["u"][1] if pl else "?", pl.pln["fr"] if pl else -1, e["fr"], e["from"], e["to"], e["pc"], step, h2 == (full >> 32) & 0xFFFFFFFF, e["st"][0]))
    for k, n in sorted(wr.items(), key=str):
        w("  %s: %d" % (k, n))
    pcs = collections.Counter("%08x" % e["pc"] for s, g in games for e in g.seedw if not e.get("ctl"))
    w("  type-10 pcs: %s" % sorted(pcs.items()))
    w()

    w("10. RETURN 0 AFTER A PLANNER: the planner's own 0, or the tail's refusal")
    z = collections.Counter()
    for s, g, plan, pred in rows:
        if pred is not None and pred["eax"] == 0:
            z[(plan.ty, "planner 0" if pred.get("n") == 0 else "tail")] += 1
    w("  %s" % sorted(z.items()))
    w()
    w("11. THE UNIT LIST: keys of PLC %s; lists cut at the cap (120 to rev 4, rev 5's `ucut`): %d; a field for the marked state: none named by tools/gdb/path.py" % (
        sorted(k for k in rows[0][2].plc) if rows and rows[0][2].plc else [], sum(1 for r in rows if r[2].plc and units_cut(r[2]))))

    w("13. CORPSES IN THE LIVE CELLS: each distinct mode-12 monster (id, x, y) of the unit lists, the 0x8000 cells of its 3 x 3")
    corpses("kept logs", games, w)
    dev = [(session_of(p), g) for p in os.environ.get("PATH_DEV", "").split() for g in parse(p)]
    if dev:
        corpses("development logs dev2..dev5", dev, w)
    w()

    w("14. THE TIE'S FIRST-PLAN 0x400 CELLS BY OBJECT: objects of the unit list whose rectangle holds a differing cell (class, door, +0x167, +0x1B6)")
    ob = collections.Counter()
    for s, g in games:
        k = 0
        for plan in g.plans:
            if not plan.plc:
                continue
            k += 1
            if k > 10:
                break
            t = tie_of(plan, True, False)
            cells = {(x, y) for a, x, y, pv, lv in (t or {}).get("diff", ())}
            for u in plan.plc["u"]:
                if u[0] == 2 and len(u) >= 13:
                    x, y, sx, sy = u[3], u[4], u[7], u[8]
                    l, tp = x - (sx >> 1), y - (sy >> 1)
                    if any((xx, yy) in cells for yy in range(tp, tp + sy) for xx in range(l, l + sx)):
                        ob[(u[2], u[9], "0x%02x" % u[11], u[12])] += 1
    w("  %s" % sorted(ob.items()))
    w()

    w("15. WHICH CLASSES THE SEED WATCHPOINTS COVERED, AND THE FRAMES TO THE WRITE")
    wc = collections.Counter()
    for s, g in games:
        byk = {p.k: p for p in g.plans}
        for e in g.seedw:
            if not e.get("ctl"):
                wc[byk[e["k"]].pln["u"][1] if e["k"] in byk else "?"] += 1
    w("  watched type-10 classes: %s" % sorted(wc.items()))
    w()

    rev5_sections([g for s, g in games], w)
    w("16. THE SPIRAL'S PRODUCTS: iterations of a natural plan whose stored FISTP integer differs under truncation and rounding (image table, r += 0x2580, angle += 16)")
    w("  %s (env PATH_IMAGE, default the pinned image under workspace/)" % spiral_products())




# path/0005's copy table: UnitCorpseColl's call -> (argument, the copy the code's module says)
CORPSE_SITES = {0x00461018: (0, "cli"), 0x004B05E3: (0, "cli"), 0x004B0A05: (0, "cli"), 0x004C8963: (0, "cli"), 0x0057F367: (1, "srv"), 0x005A65D9: (1, "srv"), 0x005CAF8E: (1, "srv")}
TYPE1_SITES = {0x005E3BCC: "AiHireFollow", 0x005E4300: "AiPetMove", 0x005E5DD9: "state 13", 0x005E5EE7: "state 13", 0x005E5F40: "state 13", 0x005CD484: "SkillDo103DiabRun", 0x005CBC44: "SkillSt48SwarmMove"}
L1_SITES = {0x005D9123: ("Whirlwind", None), 0x005D9EF8: ("Leap", 0x80), 0x005DA5D5: ("Leap Attack", 0x80), 0x005CB902: ("Jump", 0x100)}


def sine_table(path=None):
    img = path or os.environ.get("PATH_IMAGE") or os.path.join(ROOT, "workspace", "install", "app", "game.exe")
    if not os.path.exists(img):
        return None
    with open(img, "rb") as fh:
        b = fh.read()
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec, opt = struct.unpack_from("<H", b, pe + 6)[0], struct.unpack_from("<H", b, pe + 20)[0]
    va = 0x00707800 - 0x400000
    for i in range(nsec):
        vs, vaddr, rs, rp = struct.unpack_from("<4I", b, pe + 24 + opt + 40 * i + 8)
        if vaddr <= va < vaddr + rs:
            return struct.unpack_from("<512f", b, rp + va - vaddr)
    return None


def spiral_stored(games, tab):
    """The stored products of SPX against both readings: every product of a line, computed from the image's table, r += 0x2580, angle += 16 (path/0003 § 9).
    The separating ones decide: truncation must hold in all of them, and rounding in none."""
    c = collections.Counter()
    for g in games:
        for e in g.spx:
            c["plans"] += 1
            r = ang = 0
            for vx, vy in zip(e["x"], e["y"]):
                r += 0x2580
                ang += 16
                f = float(struct.unpack("<f", struct.pack("<f", float(r)))[0])
                for v, s in ((vx, tab[(ang + 0x80) & 0x1FF]), (vy, tab[ang & 0x1FF])):
                    p = s * f
                    tr, ro = int(p), int(round(p))
                    c["products"] += 1
                    c["equal truncation"] += v == tr
                    c["equal rounding"] += v == ro
                    if tr != ro:
                        c["separating"] += 1
                        c["separating, truncation"] += v == tr
                        c["separating, rounding"] += v == ro
    return c


def corpse_shape(after):
    """The 0x8000 cells of a COR line's 5 x 5: the 3 x 3, the plus, none, or how many."""
    on = {(i % 5 - 2, i // 5 - 2) for i, v in enumerate(after) if v is not None and v & 0x8000}
    if on == {(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}:
        return "3x3"
    if on == {(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)}:
        return "plus"
    return "none" if not on else "other %d" % len(on)


def rev5_sections(games, w, tab=None):
    """The lines logger rev 5 adds. A log before rev 5 holds none, and each section says so."""
    w("REV 5, THE SPIRAL'S STORED PRODUCTS (SPX, read-only): the value the game stored after each FISTP against truncation and rounding")
    tab = tab or sine_table()
    if not any(g.spx for g in games):
        w("  no SPX lines")
    elif tab is None:
        w("  no image, PATH_IMAGE")
    else:
        c = spiral_stored(games, tab)
        w("  plans %d, products %d, equal to truncation %d, equal to rounding %d; separating %d: truncation %d, rounding %d" % (
            c["plans"], c["products"], c["equal truncation"], c["equal rounding"], c["separating"], c["separating, truncation"], c["separating, rounding"]))
        w("  stored products, truncation: %s" % ("HOLDS" if c["separating"] and c["separating, truncation"] == c["separating"] and not c["separating, rounding"] else "does not hold"))
    w("REV 5, TYPE-1 REQUEST SITES (T1S): hits per site, a site at 0 was not reached in this log")
    hits = collections.Counter()
    for g in games:
        h = {}
        for e in g.t1s:
            h[(e["site"], e["side"])] = max(h.get((e["site"], e["side"]), 0), e["c"])
        hits.update(h)
    for a, name in sorted(TYPE1_SITES.items()):
        w("  %08x %-20s srv %d cli %d" % (a, name, hits[(a, "srv")], hits[(a, "cli")]))
    w("REV 5, RESERVED LANDINGS (L1M): lines per site; mask against path/0005 L1")
    l1 = collections.Counter()
    for g in games:
        for e in g.l1m:
            want = L1_SITES.get(e["site"], ("?", None))[1]
            ok = want is None or e["mask"] == want
            l1[("%08x" % e["site"], e["side"], "unit type %s" % (e["u"][0] if e["u"] else "?"), "mask 0x%x" % e["mask"], "as read" if ok else "AGAINST THE READING")] += 1
    w("  %s" % (sorted(l1.items()) or "no L1M lines"))
    w("  releases (L1U) %d" % sum(len(g.l1u) for g in games))
    w("REV 5, UnitCorpseColl CALLS (COR): site, argument and side against path/0005's copy table, and the 0x8000 shape after the call (C1..C3)")
    cr = collections.Counter()
    for g in games:
        for e in g.cor:
            want = CORPSE_SITES.get(e["site"])
            verdict = "UNLISTED CALLER" if want is None else ("as read" if (e["arg"], e["side"]) == want else "AGAINST THE TABLE")
            cr[("%08x" % e["site"], "arg %d" % e["arg"], e["side"], corpse_shape(e["after"]), verdict)] += 1
    w("  %s" % (sorted(cr.items()) or "no COR lines"))


def corpses(name, games, w):
    shape = collections.Counter()
    classes = collections.Counter()
    for s, g in games:
        seen = set()
        for plan in g.plans:
            if not plan.plc:
                continue
            R = mk_world(plan)
            for u in plan.plc["u"]:
                if u[0] != 1 or u[3] != 12 or u[6] not in R:
                    continue
                key = (u[1], u[4], u[5])
                if key in seen:
                    continue
                seen.add(key)
                on = set()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        r = P2.room_at(R, u[6], u[4] + dx, u[5] + dy)
                        if r is not None and r.cell(u[4] + dx, u[5] + dy) & 0x8000:
                            on.add((dx, dy))
                sh = "3x3" if len(on) == 9 else ("plus" if on == {(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)} else ("none" if not on else "other %d" % len(on)))
                shape[(sh, "mask 0x%x" % u[9], "pattern %d" % u[8])] += 1
                classes[(sh, u[2])] += 1
    w("  [%s] %s" % (name, sorted(shape.items(), key=lambda kv: -kv[1])))
    w("  [%s] not 3x3, by class: %s; distinct classes 3x3: %d" % (name, [kv for kv in sorted(classes.items()) if kv[0][0] != "3x3"], sum(1 for k in classes if k[0] == "3x3")))


def spiral_products():
    img = os.environ.get("PATH_IMAGE") or os.path.join(ROOT, "workspace", "install", "app", "game.exe")
    if not os.path.exists(img):
        return "no image at %s" % img
    with open(img, "rb") as fh:
        b = fh.read()
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec, opt = struct.unpack_from("<H", b, pe + 6)[0], struct.unpack_from("<H", b, pe + 20)[0]
    va = 0x00707800 - 0x400000
    off = None
    for i in range(nsec):
        o = pe + 24 + opt + 40 * i
        vs, vaddr, rs, rp = struct.unpack_from("<4I", b, o + 8)
        if vaddr <= va < vaddr + rs:
            off = rp + va - vaddr
    tab = struct.unpack_from("<512f", b, off)
    r = ang = 0
    diff = tot = 0
    for it in range(1, 95):
        r += 0x2580
        ang += 16
        f = float(r)
        for v in (tab[(ang + 0x80) & 0x1FF] * f, tab[ang & 0x1FF] * f):
            tot += 1
            if int(round(v)) != int(v):
                diff += 1
    return "%d of %d products in the 94 iterations" % (diff, tot)


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
        return report(a.logs, out, a.first, a.cmd == "check")
    finally:
        if a.out:
            out.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
