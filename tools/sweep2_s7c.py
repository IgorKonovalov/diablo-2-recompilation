#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S7c (`lane/n66m`): new checks over the kept path.gdb logs of run:2026-11-04-path and
run:2026-11-04-path-2, for the 18 path/README and path/search rows of the batch (docs/plans/0066-inventory/README.md § 4).

    python3 -I tools/sweep2_s7c.py check [--out F]

One pass per log (`tools/path.py`'s `parse`, unchanged), the plans of run:2026-11-04-path counted stock only (from a
session's first probe plan on, its plans are dropped, as `path.py`'s review section 1 does). Every plan is evaluated
with `path.py`'s `evaluate` (the control: its match count must equal the kept checks' stock counts), then observers:

  masks      README 9, 10: the record's testMask (+0x50) and markMask (+0x4C) at PathPlan's entry, players against
             0x1C09 / 0x80, monsters against PATH_MonTestMask's rule (MonStats flying 0x1804, opendoors 0x3401, else
             0x3C01; a class whose BaseId row is 38 0x804) and 0x100
  slot       README 22: the planner address at the call 0x00649BAE (PLC `pl`) against g_PathPlanFuncs[ctx type], read
             from the pinned image (path_emu1.Image)
  player     README 42: player plans from PlrModeStartMove (return 0x0057F11C) by (mode, type, +0x90)
  ai         README 43: monster plans from MonPathPlanType's request (0x005A62F4) by type; its fallback (0x005A6353):
             type 15, and for every request plan of type 2, 7, 9 or 13 that left +0x28 = 0 the unit's next logged plan
  replan     README 2, 31: PathReplan's plans (0x006503CE, 0x006503E2) by type, the record at entry
  tail       README 47, 72, search 36: the model's record after PathPlan's tail (path.py `tail`, the aim) against the
             PLX record at the aim's offsets (+0x24, +0x64..+0x66, +0x6A..+0x7F), and the output words of C's steps
             19 to 26 (+0x28 = the return, flag 0x20, +0x14 = +0x10, +0x38 = 0, +0x10 = the last point without flag
             0x10 and target unit; a 0 return: +0x24 = +0x28 = 0, flag 0x20 clear)
  live       README 73: the live cell at the start (ctx) against the unit's own mark bits, and at the target's
             position under flag 0x800; control: the other units' cells hold their bits
  spiral     search 2, 17, 19, README 78, search 21: type 14: no PLC line, the seed and +0x90 / +0x91 unchanged, the
             SPX iterations per plan, the points against the structure and four variants (step 0x2500 / 0x2600,
             angle 15 / 17), the points that lie on a cell blocked under the plan's testMask in every dump of its room
  rwalk      search 15: type 10: the steps of the game's points by turn (straight, side), and the map variant
             "(lo & 31) 30, 31 straight" (12/32) against the game's points
  near       search 7: players' type-7 plans: dx^2 + dy^2 of the context's start and target against greedy-near's
             switch to type 1 (the model's branch)

Stdlib only. Read-only. Output: one section per observer and `S7c total bad=N control_bad=M`.
"""
import argparse
import collections
import csv
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import path as P  # noqa: E402
import path_emu1 as P1  # noqa: E402
import path_emu2 as P2  # noqa: E402
import path_emu3 as P3  # noqa: E402

LOGDIR = os.path.join(ROOT, "workspace", "logs", "path")
MANIFESTS = ("manifest-2026-11-04-path.sha256", "manifest-path-2.sha256")
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
RA_PLR_MOVE = 0x0057F11C
RA_MON_REQ = 0x005A62F4
RA_MON_FALLBACK = 0x005A6353
RA_REPLAN_A = 0x006503CE
RA_REPLAN_B = 0x006503E2
FALLBACK_TYPES = (2, 7, 9, 13)        # the byte table 0x005A6368 (types 2..13), entry 0


def logs():
    out = []
    for m in MANIFESTS:
        for line in open(os.path.join(LOGDIR, m)):
            name = line.split()[1]
            if name.endswith(".log"):
                out.append(os.path.join(LOGDIR, name))
    return out


def monstats():
    with open(os.path.join(EXCEL, "monstats.txt"), errors="replace") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    rows = [r for r in rows if (r.get("hcIdx") or "").strip()]      # the class id is hcIdx (the "Expansion" row has none)
    ids = {r["Id"]: int(r["hcIdx"]) for r in rows}
    out = {}
    for r in rows:
        i = int(r["hcIdx"])
        base = ids.get(r.get("BaseId") or "", -1)
        if base == 38:
            m = 0x804
        elif int(r.get("flying") or 0):
            m = 0x1804
        elif int(r.get("opendoors") or 0):
            m = 0x3401
        else:
            m = 0x3C01
        out[i] = (m, r["Id"], base)
    return out


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def spiral_var(fx, fy, step, dang):
    """path_emu3.spiral (trunc) with the radius step and the angle step as parameters."""
    I = P3.img()
    lx, ly = fx, fy
    r, ang, k, pts = 0, 0, 0, []
    while k < 77:
        r += step
        ang += dang
        f = struct.unpack("<f", struct.pack("<f", float(r)))[0]
        cs = I.sine[(ang + 0x80) & 0x1FF]
        sn = I.sine[ang & 0x1FF]
        a, b = int(cs * f), int(sn * f)
        x = (a + fx) & 0xFFFFFFFF
        y = (b + fy) & 0xFFFFFFFF
        if (x >> 16) != (lx >> 16) or (y >> 16) != (ly >> 16):
            pts.append((x >> 16) | ((y >> 16) << 16))
            k += 1
            lx, ly = x, y
    return tuple(pts)


def rwalk_var(rec, seed):
    """path_emu3.rwalk with (lo & 31) 30 and 31 mapped to a straight step (12/32 straight, 10/32 each side)."""
    I = P3.img()
    n = rec[0x91] >> 1
    cur = P3.mk(u16(rec, 2), u16(rec, 6))
    base = P3.triple(cur, u32(rec, 0x10))[0]
    lo, hi = seed
    pts = []
    for _ in range(n):
        v = lo * P3.A + hi
        lo, hi = v & 0xFFFFFFFF, v >> 32 & 0xFFFFFFFF
        add = (-1, 0, 1)[(lo & 31) % 3] if (lo & 31) < 30 else 0
        d = (add + base) & 7
        pts.append(cur)
        dx, dy = I.step[d]
        cur = P3.mk(P3.X(cur) + 2 * dx, P3.Y(cur) + 2 * dy)
    pts.append(cur)
    return tuple(pts)


_TAIL = {}
_orig_tail = P.tail


def _spy_tail(M, n, neg=None):
    r = _orig_tail(M, n, neg)
    _TAIL["M"] = M
    return r


P.tail = _spy_tail

_NEAR = {}
_orig_near = P3.PLANNERS[0x00679ED0]


def _spy_near(c):
    """path_emu3.near with its branch recorded: greedy reached (no switch test), d2 > 324 (no switch), or the switch."""
    c.setp(0x24, 0)
    c.setp(0x28, 0)
    n = P3.greedy(c)
    d2 = (P3.X(c.s) - P3.X(c.t)) ** 2 + (P3.Y(c.s) - P3.Y(c.t)) ** 2
    _NEAR["d2"] = d2
    if n:
        p = c.path(0x98 + 4 * n)
        if P3.dist8(p, c.t) <= c.refresh and p != c.s:
            _NEAR["branch"] = "greedy reached"
            return n
    if d2 > 324:
        _NEAR["branch"] = "short, d2 > 324"
        return n
    _NEAR["branch"] = "short, switch"
    c.stat["t1"] = 1
    r = P3.type1(c)
    if r:
        return r
    if n == 0:
        return 0
    return P3.greedy(c)


P3.PLANNERS[0x00679ED0] = _spy_near
AIM_OFFS = list(range(0x24, 0x28)) + [0x64, 0x65, 0x66] + list(range(0x6A, 0x80))


class S7c:
    def __init__(self):
        self.c = collections.defaultdict(collections.Counter)
        self.bad = collections.Counter()
        self.ex = collections.defaultdict(list)
        self.ms = monstats()
        self.img = P1.img()

    def note(self, sec, key, ok=True, ex=None):
        self.c[sec][key] += 1
        if not ok:
            self.bad[sec] += 1
            self.c[sec]["FAILED: " + key] += 1
            if ex is not None and len(self.ex[sec]) < 6:
                self.ex[sec].append("%s: %s" % (key, ex))

    def run_log(self, path):
        name = os.path.basename(path)
        for g in P.parse(path):
            first = None
            for pl in g.plans:
                if pl.pln.get("probe"):
                    first = pl.k
                    break
            plans = [pl for pl in g.plans if first is None or pl.k < first]
            self.c["control"]["games"] += 1
            if first is not None:
                self.c["control"]["plans dropped after a probe write"] += len(g.plans) - len(plans)
            self.game(name, g, plans)

    def game(self, name, g, plans):
        rooms_by_addr = collections.defaultdict(list)
        for (a, h, nh), r in g.rooms.items():
            if r["cells"] is not None and (not r["mr"] or r["mr"] == r["r"]):
                rooms_by_addr[a].append(r)
        capped = {(c["k"], c["key"] if not isinstance(c["key"], list) else tuple(c["key"])): c["n"] for c in g.caps}
        byunit = collections.defaultdict(list)
        for pl in plans:
            byunit[(pl.unit_type, pl.pln["u"][2])].append(pl)
        spx = {s["k"]: s for s in g.spx}
        self.capped = capped
        for pl in plans:
            self.c["control"]["plans"] += 1
            if pl.plx is None:
                self.c["control"]["no PLX"] += 1
                continue
            _TAIL.clear()
            _NEAR.clear()
            try:
                kind, pred = P.evaluate(pl)
            except P.Unmodelled:
                self.note("control", "unmodelled", False, "%s k=%d" % (name, pl.k))
                continue
            if kind == "model":
                bad = P.compare(pl, pred)
            else:
                bad = [] if (pl.plx["eax"] == 0 and pl.plx["s"] == pl.pln["s0"]) else ["refusal"]
            self.note("control", "matched" if not bad else "mismatched", not bad, "%s k=%d %s" % (name, pl.k, bad))
            self.c["control"]["type %d" % pl.ty] += 1
            self.masks(name, pl)
            self.slot(name, pl)
            self.player(name, pl)
            self.replan(name, pl, byunit)
            if kind == "model" and not bad:
                self.tail(name, pl, pred)
                self.live(name, pl)
                if pl.ty == 14 and pl.straight:
                    self.spiral(name, pl, pred, spx.get(pl.k), rooms_by_addr)
                if pl.ty == 10 and pl.straight:
                    self.rwalk(name, pl, pred)
                if pl.unit_type == 0 and pl.ty == 7 and pl.plc and _NEAR:
                    self.near(name, pl, pred)
        self.ai(name, plans, byunit, capped)

    # ---- README 9, 10
    def masks(self, name, pl):
        rec = pl.pln["rec"]
        t, m = u32(rec, 0x50), u32(rec, 0x4C)
        ut = pl.unit_type
        if ut == 0:
            ok = (t, m) == (0x1C09, 0x80)
            self.note("masks", "player test 0x%X mark 0x%X ra %08X ty %d" % (t, m, pl.pln["ra"], pl.ty), True)
            self.note("masks", "player %s" % ("match" if ok else "differ"), True)
        elif ut == 1:
            cls = pl.pln["u"][1]
            want = self.ms.get(cls, (None,))[0]
            ok = t == want
            self.note("masks", "monster test %s" % ("match" if ok else "differ"), True)
            self.note("masks", "monster test rule %s" % {0x804: "wraith", 0x1804: "flying", 0x3401: "opendoors",
                                                        0x3C01: "else"}.get(want, "?"), True)
            if not ok:
                self.note("masks", "monster test differ: class %d %s rule 0x%X logged 0x%X ra %08X ty %d" % (
                    cls, self.ms.get(cls, (0, "?"))[1], want or 0, t, pl.pln["ra"], pl.ty), True)
            self.note("masks", "monster mark %s" % ("0x100" if m == 0x100 else "0x%X" % m), True)
            self.c["masks-classes"][(cls, t)] += 1

    # ---- README 22
    def slot(self, name, pl):
        if not pl.plc:
            return
        ty = struct.unpack_from("<i", pl.plc["ctx"], 0x20)[0]
        want = self.img.slot(ty) if 0 <= ty <= 16 else None
        self.note("slot", "PLC planner = g_PathPlanFuncs[ctx type]", pl.plc["pl"] == want,
                  "%s k=%d ty %d pl %08X slot %s" % (name, pl.k, ty, pl.plc["pl"], want))
        self.c["slot-types"][ty] += 1
        self.c["slot-types-pln"][(pl.ty, ty)] += 1

    # ---- README 42
    def player(self, name, pl):
        if pl.unit_type != 0:
            return
        ra = pl.pln["ra"]
        mode = pl.pln["u"][3]
        if ra == RA_PLR_MOVE:
            # the unit's mode at PathPlan's entry is the mode before the start (the new mode is EDI, set after the plan,
            # 0x0057F148); PathMoveReset (0x0057F0C0) then 7, or 8 with +0x90 = 5 for the new mode 19 (0x0057F103)
            rec = pl.pln["rec"]
            key = "PlrModeStartMove type %d +0x90 %d (mode before the start %d)" % (pl.ty, rec[0x90] if pl.ty == 8 else -1, mode)
            ok = pl.ty == 7 or (pl.ty == 8 and rec[0x90] == 5)
            self.note("player", key, ok, "%s k=%d %s" % (name, pl.k, key))
            self.note("player", "PlrModeStartMove: type 7, or 8 with +0x90 = 5", ok)
        else:
            self.note("player", "other site %08X type %d mode %d" % (ra, pl.ty, mode), True)

    # ---- README 2, 31
    def replan(self, name, pl, byunit):
        ra = pl.pln["ra"]
        if ra not in (RA_REPLAN_A, RA_REPLAN_B):
            return
        rec = pl.pln["rec"]
        site = "0x006503CE" if ra == RA_REPLAN_A else "0x006503E2"
        mid = u32(rec, 0x24) < u32(rec, 0x28)
        self.note("replan", "%s type %d tg %s eax0 %s points-left-at-entry %s flag10 %s" % (
            site, pl.ty, bool(pl.pln["tg"]), pl.plx["eax"] == 0, mid, bool(pl.pln["fl"] & 0x10)), True)
        if ra == RA_REPLAN_A:
            self.note("replan", "first call: type 13 or 2", pl.ty in (13, 2), "%s k=%d ty %d" % (name, pl.k, pl.ty))
            if pl.ty == 2:
                self.note("replan", "type 2: +0x10 = +0x18 at entry", rec[0x10:0x14] == rec[0x18:0x1C])
        else:
            prev = None
            lst = byunit[(pl.unit_type, pl.pln["u"][2])]
            i = lst.index(pl)
            if i:
                prev = lst[i - 1]
            fb = prev is not None and prev.pln["ra"] == RA_REPLAN_A and prev.plx and prev.plx["eax"] == 0 and \
                prev.pln["fr"] == pl.pln["fr"]
            self.note("replan", "second site type %d after a failed first call %s" % (pl.ty, fb), True)
            if pl.ty == 15:
                cut = any(n < pl.k for (kk, key), n in self.capped.items() if key in (2, 13, 15))
                self.note("replan", "second site type 15 follows a failed first call%s" % ("" if fb else ", or its first call unlogged after a 2/13/15 cap line"),
                          fb or cut, "%s k=%d" % (name, pl.k))
            else:
                self.note("replan", "second site non-15 without a first call", not fb, "%s k=%d" % (name, pl.k))

    # ---- README 43
    def ai(self, name, plans, byunit, capped):
        for pl in plans:
            if pl.unit_type != 1 or pl.plx is None:
                continue
            ra = pl.pln["ra"]
            if ra == RA_MON_REQ:
                self.note("ai", "request type %d" % pl.ty, pl.ty in (1, 2, 5, 6, 7, 13, 15), "%s k=%d" % (name, pl.k))
                if pl.ty in FALLBACK_TYPES or pl.ty in (5, 6, 15):
                    lst = byunit[(1, pl.pln["u"][2])]
                    i = lst.index(pl)
                    nxt = lst[i + 1] if i + 1 < len(lst) else None
                    fb = nxt is not None and nxt.pln["ra"] == RA_MON_FALLBACK and nxt.pln["fr"] == pl.pln["fr"]
                    empty = pl.plx["n28"] == 0
                    if pl.ty in FALLBACK_TYPES and empty:
                        if fb:
                            self.note("ai", "type %d with +0x28 = 0 -> fallback 15 logged" % pl.ty, True)
                        else:
                            cut = ("reach", 15) in capped or ("ref", 15) in capped
                            self.note("ai", "type %d with +0x28 = 0 -> no fallback logged (type-15 cap reached in the game: %s)" % (
                                pl.ty, cut), cut, "%s k=%d" % (name, pl.k))
                    else:
                        self.note("ai", "type %d +0x28 %s -> fallback %s" % (pl.ty, "0" if empty else ">0", fb), not fb,
                                  "%s k=%d" % (name, pl.k))
            elif ra == RA_MON_FALLBACK:
                lst = byunit[(1, pl.pln["u"][2])]
                i = lst.index(pl)
                prev = lst[i - 1] if i else None
                ok = pl.ty == 15 and prev is not None and prev.pln["ra"] == RA_MON_REQ and prev.ty in FALLBACK_TYPES \
                    and prev.plx and prev.plx["n28"] == 0 and prev.pln["fr"] == pl.pln["fr"]
                if ok:
                    self.note("ai", "fallback plan: type 15 after an empty 2/7/9/13 request in its frame", True)
                else:
                    cut = any(n < pl.k for (kk, key), n in capped.items() if key in FALLBACK_TYPES)
                    self.note("ai", "fallback plan: type 15, its request unlogged after a 2/7/9/13 cap line", pl.ty == 15 and cut,
                              "%s k=%d" % (name, pl.k))
            else:
                self.note("ai", "monster other site %08X type %d" % (ra, pl.ty), True)

    # ---- README 47, 72; search 36
    def tail(self, name, pl, pred):
        x = pl.plx["rec"]
        eax = pl.plx["eax"]
        if pl.plc:
            M = _TAIL.get("M")
            n = pred.get("n", 0)
            if M is not None and n:
                b = M.b if hasattr(M, "b") else None
                got = bytes(x[o] for o in AIM_OFFS)
                mod = bytes(M.r8(P3.UPATH + o) for o in AIM_OFFS)
                atcall = bytes(pl.plc["rec"][o] for o in AIM_OFFS)
                self.c["tail"]["aim offsets changed since the planner call (separating 'no aim'): %s" % (got != atcall)] += 1
                if eax:
                    self.note("tail", "aim writes: model = PLX record (planner plans with a return > 0)", got == mod,
                              "%s k=%d ty %d" % (name, pl.k, pl.ty))
                else:
                    # every point at the position: the fail path zeroes +0x24 after the aim (C's step 24, fail)
                    self.note("tail", "aim writes but +0x24 on a count with return 0 (every point at the position); +0x24 = 0",
                              got[4:] == mod[4:] and u32(x, 0x24) == 0, "%s k=%d ty %d" % (name, pl.k, pl.ty))
            if eax:
                fl = u32(x, 0x34)
                self.note("tail", "+0x28 = return", u32(x, 0x28) == eax, "%s k=%d" % (name, pl.k))
                self.note("tail", "flag 0x20 set", bool(fl & 0x20), "%s k=%d" % (name, pl.k))
                self.note("tail", "+0x38 = 0", u32(x, 0x38) == 0, "%s k=%d" % (name, pl.k))
                self.note("tail", "+0x24 < +0x28", u32(x, 0x24) < eax, "%s k=%d" % (name, pl.k))
                last = u32(x, 0x9C + 4 * (eax - 1))
                knock = pl.plc["pl"] == 0x0067A000          # knockback writes the target point and clears the target unit
                if not fl & 0x10 and not u32(x, 0x58):      # step 25 tests the flag and the target unit after the planner
                    self.note("tail", "no flag 0x10, no target unit after the planner: +0x10 = the last point", u32(x, 0x10) == last,
                              "%s k=%d" % (name, pl.k))
                    if not knock:
                        self.note("tail", "  and +0x14 = +0x10 as at the planner call (copied before that write)",
                                  x[0x14:0x18] == pl.plc["rec"][0x10:0x14], "%s k=%d" % (name, pl.k))
                    else:
                        self.note("tail", "  knockback: +0x14 holds its own target point (not compared)", True)
                else:
                    self.note("tail", "flag 0x10 or a target unit after the planner: +0x14 = +0x10", x[0x14:0x18] == x[0x10:0x14],
                              "%s k=%d" % (name, pl.k))
                    if not knock:
                        self.note("tail", "  and +0x10 as at the planner call", x[0x10:0x14] == pl.plc["rec"][0x10:0x14],
                                  "%s k=%d" % (name, pl.k))
            else:
                fl = u32(x, 0x34)
                self.note("tail", "return 0 after a planner: +0x24 = +0x28 = 0 and flag 0x20 clear",
                          u32(x, 0x24) == 0 and u32(x, 0x28) == 0 and not fl & 0x20, "%s k=%d" % (name, pl.k))
        else:
            self.note("tail", "straight type %d: return %s" % (pl.ty, "0" if not eax else ">0"), True)
            if eax:
                self.note("tail", "straight: +0x28 = return", u32(x, 0x28) == eax, "%s k=%d" % (name, pl.k))

    # ---- README 73
    def live(self, name, pl):
        if not pl.plc:
            return
        R = P.mk_world(pl)
        units = pl.plc["u"]
        sid = tuple(pl.plc["self"])
        tid = tuple(pl.plc["tgt"]) if pl.plc.get("tgt") else None
        mob = [u for u in units if u[0] in (0, 1, 3) and len(u) >= 11]

        def cell(x, y):
            for r in R.values():
                if r.has(x, y):
                    return r.cell(x, y)
            return None

        def crowded(u, others):
            return any(abs(o[4] - u[4]) <= 3 and abs(o[5] - u[5]) <= 3 for o in others)
        ctx = pl.plc["ctx"]
        sx, sy, tx, ty = struct.unpack_from("<HHHH", ctx, 0)
        hint = struct.unpack_from("<I", ctx, 8)[0]
        pattern, tmask = struct.unpack_from("<iI", ctx, 0x28)
        others = [u for u in mob if (u[0], u[1]) != sid]
        me = next((u for u in mob if (u[0], u[1]) == sid), None)
        if hint in R and me is not None and (sx, sy) == (me[4], me[5]):
            c0 = R[hint].cell(sx, sy) if R[hint].has(sx, sy) else 0
            blk = c0 & tmask & (0x1000 | me[9])
            cr = crowded(me, others)
            if not cr:
                self.note("live", "self, no other unit within 3: its start cell holds none of its own blocking bits (testMask & (0x1000 | markMask))", not blk,
                          "%s k=%d cell %X" % (name, pl.k, R[hint].cell(sx, sy) if R[hint].has(sx, sy) else -1))
            else:
                self.c["live"]["self, another unit within 3: start %s" % ("blocked" if blk else "free")] += 1
            c = R[hint].cell(sx, sy) if R[hint].has(sx, sy) else None
            if c is not None and not cr:
                self.c["live"]["self, no other unit within 3: own mark bit at its cell %s (0x100 and 0x80 are in no planner mask)" % (
                    "set" if c & me[9] else "clear")] += 1
        if tid and pl.pln["fl"] & 0x800:
            tu = next((u for u in mob if (u[0], u[1]) == tid), None)
            if tu is not None and hint in R and P2.room_at(R, hint, tu[4], tu[5]) is not None:
                blk = P2.room_at(R, hint, tu[4], tu[5]).cell(tu[4], tu[5]) & tmask & (0x1000 | tu[9])
                if not crowded(tu, [u for u in mob if (u[0], u[1]) not in (tid, sid)]) and not crowded(tu, [me] if me else []):
                    self.note("live", "target under 0x800, no other unit within 3: its cell holds none of its blocking bits (testMask & (0x1000 | markMask))", not blk,
                              "%s k=%d" % (name, pl.k))
        # control: another unit, alive and alone within 3, blocks the plan's own pattern and testMask at its position
        for u in others:
            if (u[0], u[1]) == tid or not u[9]:
                continue
            if u[0] == 0 and u[3] in (0, 17) or u[0] == 1 and u[3] in (0, 12) or u[0] == 3:
                continue
            if hint not in R or crowded(u, [o for o in mob if o is not u]):
                continue
            if P2.room_at(R, hint, u[4], u[5]) is None:
                continue
            blk = P2.room_at(R, hint, u[4], u[5]).cell(u[4], u[5]) & tmask & (0x1000 | u[9])
            self.c["live-control"]["other unit type %d alone within 3: its cell %s its blocking bits (testMask & (0x1000 | markMask))" % (
                u[0], "holds" if blk else "lacks")] += 1

    # ---- search 2, 17, 19; README 78; search 21
    def spiral(self, name, pl, pred, spx, rooms_by_addr):
        self.note("spiral", "type 14: no PLC line (no planner call, no grid dump)", pl.plc is None)
        self.note("spiral", "seed unchanged", pl.plx["s"] == pl.pln["s0"])
        r0, r1 = pl.pln["rec"], pl.plx["rec"]
        self.note("spiral", "+0x90, +0x91 unchanged", r0[0x90:0x92] == r1[0x90:0x92], "%s k=%d" % (name, pl.k))
        self.note("spiral", "77 points", pl.plx["eax"] == 77)
        fx, fy = u32(r0, 0), u32(r0, 4)
        game = tuple(struct.unpack_from("<%dI" % pl.plx["eax"], r1, 0x9C))
        self.c["spiral-start"][(fx & 0xFFFF, fy & 0xFFFF)] += 1
        for step, da, lab in ((0x2500, 16, "step 0x2500"), (0x2600, 16, "step 0x2600"), (0x2580, 15, "angle 15"),
                              (0x2580, 17, "angle 17")):
            v = spiral_var(fx, fy, step, da)
            sep = v != tuple(pred["pts"])
            self.c["spiral-variants"]["%s: separating %s, equals the game %s" % (lab, sep, v == game)] += 1
            if v == game and sep:
                self.bad["spiral"] += 1
        if spx is not None:
            self.c["spiral-iterations"][(len(spx["x"]), (fx & 0xFFFF, fy & 0xFFFF))] += 1
        mask = u32(r0, 0x50)
        hit = 0
        for p in game:
            x, y = p & 0xFFFF, p >> 16
            dumps = []
            for a, lst in rooms_by_addr.items():
                for r in lst:
                    x0, y0, w, h = r["r"]
                    if x0 <= x < x0 + w and y0 <= y < y0 + h:
                        dumps.append(r["cells"][(y - y0) * w + (x - x0)])
            if dumps and all(c & mask & 0x04 for c in dumps):
                hit += 1
        self.c["spiral-blocked"]["test mask 0x%X, points on a cell with bit 0x04 of that mask in every dump of its room: %s" % (
            mask, "0" if not hit else ("1-5" if hit <= 5 else "6+"))] += 1

    # ---- search 15
    def rwalk(self, name, pl, pred):
        x = pl.plx["rec"]
        n = pl.plx["eax"]
        pts = struct.unpack_from("<%dI" % n, x, 0x9C)
        rec = pl.pln["rec"]
        base = P3.triple(P3.mk(u16(rec, 2), u16(rec, 6)), u32(rec, 0x10))[0]
        I = P3.img()
        for i in range(n - 1):
            dx = P3.X(pts[i + 1]) - P3.X(pts[i])
            dy = P3.Y(pts[i + 1]) - P3.Y(pts[i])
            d = next((k for k in range(8) if (2 * I.step[k][0], 2 * I.step[k][1]) == (dx, dy)), None)
            turn = None if d is None else ((d - base + 1) & 7) - 1
            self.c["rwalk-steps"]["straight" if turn == 0 else ("side" if turn in (-1, 1) else "other %s" % turn)] += 1
        v = rwalk_var(rec, P.seed_of(pl.pln["s0"]))
        sep = v != tuple(pred["pts"])
        self.c["rwalk-variant"]["12/32 straight map: separating %s, equals the game %s" % (sep, v == tuple(pts))] += 1
        if sep and v == tuple(pts):
            self.bad["rwalk"] += 1

    # ---- search 7
    def near(self, name, pl, pred):
        d2, br = _NEAR.get("d2"), _NEAR.get("branch")
        self.c["near"]["%s, d2 %s" % (br, "<= 324" if d2 <= 324 else "> 324")] += 1
        self.c["near-d2"][(br, d2 if 300 <= d2 <= 360 else ("<300" if d2 < 300 else ">360"))] += 1
        if br and br.startswith("short"):
            self.note("near", "greedy short: switch iff d2 <= 324", (br == "short, switch") == (d2 <= 324))

    def report(self, w):
        for sec in ("control", "masks", "slot", "player", "ai", "replan", "tail", "live", "spiral", "near"):
            w("== %s (bad %d)" % (sec, self.bad[sec]))
            for k, v in sorted(self.c[sec].items(), key=lambda kv: str(kv[0])):
                w("  %-100s %7d" % (k, v))
            for e in self.ex[sec]:
                w("  example: %s" % e)
        for sec in ("masks-classes", "slot-types", "slot-types-pln", "live-control", "spiral-start", "spiral-variants",
                    "spiral-iterations", "spiral-blocked", "rwalk-steps", "rwalk-variant", "near-d2"):
            w("== %s%s" % (sec, (" (bad %d)" % self.bad[sec.split("-")[0]]) if sec in ("spiral-variants", "rwalk-variant") else ""))
            for k, v in sorted(self.c[sec].items(), key=lambda kv: str(kv[0])):
                w("  %-100s %7d" % (k, v))
        w("== bound: r += 0x2580 as int32: largest iteration that fits %d (r = %d), first that wraps %d (r = %d > %d)" % (
            (2 ** 31 - 1) // 0x2580, ((2 ** 31 - 1) // 0x2580) * 0x2580, (2 ** 31 - 1) // 0x2580 + 1,
            ((2 ** 31 - 1) // 0x2580 + 1) * 0x2580, 2 ** 31 - 1))
        control_bad = self.bad["control"]
        tot = sum(v for k, v in self.bad.items() if k != "control")
        w("S7c total bad=%d control_bad=%d" % (tot, control_bad))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("--out")
    ap.add_argument("--logs", nargs="*")
    a = ap.parse_args(argv)
    S = S7c()
    for p in (a.logs or logs()):
        S.run_log(p)
    out = open(a.out, "w") if a.out else sys.stdout
    S.report(lambda s="": out.write(s + "\n"))
    if a.out:
        out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
