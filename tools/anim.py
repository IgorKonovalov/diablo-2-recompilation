#!/usr/bin/env python3
"""Model and per-event check of animation and frame timing (plan 0050 Phase 2), against logs written by
tools/gdb/anim.gdb (tools/gdb/anim.py).

Usage:
  python3 -I tools/anim.py check [--root workspace/merged] [--exe workspace/install/app/game.exe] [-v] <log> ...
  python3 -I tools/anim.py lengths <recipe.json> ...     # the lengths a recipe's rate items give (tool for recipes)

What it models (docs/findings/anim/0001-0003; the Boundary of plan 0050 Phase 2):
  RATE   each SR line (UNIT_AnimSetRate's exit): the record name (anim/0001 § 2: token + mode token + weapon class),
         its frames and speed (animdata.d2), the branch (anim/0002 §§ 1, 3 with the image's mode-class tables), the
         rate +0x4C and the sequence step +0x3C (cast, attack), the path speed (moving, knockback; anim/0003 § 1).
         Inputs taken from the line: the unit's class, mode, stats 67/68/69/93/96/99/102/105 (the full values, the
         stats spec's), states, the used skill, the equipped items' classes.
  SCHED  each SCH line (SUNIT_ScheduleModeEvents): the start frame (anim/0001 § 4, g_AttackStartFrames), the rate and
         length from the last SR of the unit and the record (player sequences from g_PlrSeqTables), and the queued
         list (kind, frame, code, index) of anim/0001 § 7, compared with the q the logger read at the 13 call sites.
  FIRE   each queued event against the dispatches (PDS/MDS) at its frame: fired, or cancelled first (CAN, a newer
         SCH, MSET), or the unit gone; a dispatch with no queued event is a mismatch.
  STEP   each pair of consecutive PS0 lines of one unit (one per frame): PathVelocityStep, the point snap, the
         subtile walk with the CT results as the oracle, and the next state (position, point index); the path speed
         against the unit's last SR.
  ADV    each pair of consecutive AD0 lines (UNIT_AnimAdvance, one windowed monster): frame, event byte, sequence.
  DRAIN  each DR0/DR1 pair (sub_0057F240_RunStaminaDrain).
  GHR    each GR0/GR1 (sub_0057CB00_GetHitRoll): the divisor, the bands, the 0-2 RangePow2 draws on the defender's
         seed, the return; the max HP (GRH) is the boundary.
  PMA    each PA0/PA1 (sub_0057EEC0_PlayerModeAllowed): the Concentration draw (anim/0003 § 6.2) on the seed.
  OBJ    each OA0/OA1 (an object's UNIT_AnimInit): the Sync draw and the rate (objects G2), +0x44, +0x48; chained
         pairs on one object's seed; each OQ (an object queue) against Objects FrameCnt and its OEV.
Every compared value counts one check; the summary line is
  CHECK anim <kind>=<checked>/<mismatched> ... and exit 0 iff no mismatch.
Stdlib only; tools/animdata.py, tools/anim_rates.py (the rate helpers), tools/anim_scan.py (the image reader),
tools/excel_bin.py, tools/rng.py.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import anim_rates as AR    # noqa: E402
import anim_scan as AS     # noqa: E402
import animdata as AD      # noqa: E402
import excel_bin as eb     # noqa: E402
import rng as RNG          # noqa: E402
from combat_survey import Table  # noqa: E402

M32 = 0xFFFFFFFF
ROOT = os.path.dirname(HERE)
PLR_TOKEN = ["AM", "SO", "NE", "PA", "BA", "DZ", "AI"]
PMODES = ["DT", "NU", "WL", "RN", "GH", "TN", "TW", "A1", "A2", "BL", "SC", "TH", "KK", "S1", "S2", "S3", "S4", "DD",
          "GH", "GH"]
MMODES = ["DT", "NU", "WL", "GH", "A1", "A2", "BL", "SC", "S1", "S2", "S3", "S4", "DD", "GH", "xx", "RN"]
TOWNS = (1, 40, 75, 103, 109)


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def cdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def seed_of(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


class Data:
    def __init__(self, root, exe):
        ex = os.path.join(root, "data", "global", "excel")
        refs = eb.Refs(ex)
        self.mon = Table(ex, "monstats", refs).rec
        self.mon2 = Table(ex, "monstats2", refs).rec
        self.obj = Table(ex, "objects", refs).rec
        self.cs = Table(ex, "charstats", refs).rec
        self.sk = Table(ex, "skills", refs).rec
        items = []
        for name in ("weapons", "armor", "misc"):
            t = Table(ex, name, refs)
            for r in t.rec:
                r = dict(r)
                r["_kind"] = name
                items.append(r)
        self.items = items
        self.mseq = collections.defaultdict(list)
        for r in Table(ex, "monseq", refs).rec:
            self.mseq[r["sequence"]].append(r)
        recs = AD.load(os.path.join(root, "data", "global", "animdata.d2"))
        self.anim = {}
        for r in recs:
            self.anim.setdefault(r.name, r)          # the first record of a name wins (anim/0001 § 2.1)
        pe = AS.PE(exe)
        self.pe = pe
        self.mcls = {}
        for name, base, cnt in AR.MCLS:
            self.mcls[name] = [tuple(s32(pe.dw(base + 20 * m + 4 * k)) for k in range(5)) for m in range(cnt)]
        self.start = [[pe.dw(0x006E8E60 + 4 * (wc * 7 + c)) for c in range(7)] for wc in range(14)]
        self.iwcls = {}
        for i in range(pe.dw(0x007446E0)):
            self.iwcls[pe.rd(0x007446A0 + 8 * i, 4).decode("latin-1").strip(" \0")] = pe.dw(0x007446A4 + 8 * i)
        self.cwcls = {}
        for i in range(13):
            self.cwcls[pe.rd(0x006EB748 + 8 * i, 4).decode("latin-1").strip(" \0")] = pe.dw(0x006EB74C + 8 * i)
        # g_PlrSeqColumns: entry i = (column i, the composit weapon-class index it holds); the lookup is by index
        self.seqcol = {pe.dw(0x0074841C + 8 * i): pe.dw(0x00748418 + 8 * i) for i in range(14)}
        self.walk, self.run = {}, {}
        for i in range(len(self.mon)):
            self.speeds(i)

    # --- records -----------------------------------------------------------------------------------------------
    def record(self, name):
        r = self.anim.get(name.upper())
        if r is None:
            return "", 2048, 256, bytes(144), False      # the fallback record, name empty (anim/0001 § 2)
        return r.name, r.frames, r.speed, r.events, True

    def mon_name(self, cls, mode):
        m = self.mon[cls]
        code = m["Code"]
        ex = m["MonStatsEx"]
        m2 = self.mon2[ex] if ex is not None and 0 <= ex < len(self.mon2) else None
        tok = MMODES[mode]
        if mode == 13:
            tok = "GH"
        if m2 is None:
            wc = "HTH"
        elif mode in (0, 12) and not m2.get("compositeDeath"):
            wc = "HTH"
        else:
            wc = m2["BaseW"] or "HTH"
        return (code + tok + wc).replace(" ", "").upper()

    def speeds(self, i):
        """sub_00650F00_MonStatsSpeeds for row i: (+0x036, +0x038) (anim/0002 § 3.5, anim/0003 § 1.1)."""
        if i in self.walk:
            return self.walk[i], self.run[i]
        m = self.mon[i]
        b = m["BaseId"]
        if b is None or not 0 <= b < len(self.mon):
            b = i
        _, _, sp, _, _ = self.record(self.mon_name(b, 2))
        vb, vi = self.mon[b]["Velocity"] or 0, m["Velocity"] or 0
        w = sp
        if b != i and vb > 0:
            w = (s16(vi) * sp & M32) // vb
        w = min(w, 0x7FFF)
        if i < 410:
            rb = self.walk.get(b) if b != i else w
            if rb is None:
                rb = self.speeds(b)[0]
            rn = cdiv(rb, 2)
        else:
            _, _, rn, _, _ = self.record(self.mon_name(b, 15))
        rnb, rni = self.mon[b]["Run"] or 0, m["Run"] or 0
        if b != i and rnb > 0:                     # both bases scaled by Run(i) / Run(b) (anim/0002 § 3.5)
            rn = (s16(rni) * rn & M32) // rnb
        rn = min(rn, 0x7FFF)
        self.walk[i], self.run[i] = w, rn
        return w, rn

    def item(self, idx):
        return self.items[idx] if 0 <= idx < len(self.items) else None

    def weapon(self, eq):
        """the hand item that is a weapon: (body location, item row) or None (right hand first)."""
        for bl in (4, 5):
            for e in eq:
                if e[0] == bl:
                    it = self.item(e[1])
                    if it and it["_kind"] == "weapons":
                        return bl, it, e
        return None

    def plr_wclass(self, cls, mode, eq):
        """COMPOSIT_WeaponClass for a player (anim/0001 § 2), single weapon only."""
        if mode in (0, 17):
            return "HTH"
        w = self.weapon(eq)
        if not w:
            return (self.cs[cls]["baseWClass"] or "hth").upper()
        _, it, _ = w
        others = [e for e in eq if e[0] in (4, 5) and e is not w[2]]
        if it.get("2handed") and not (it.get("1or2handed") and cls == 4):
            wc = it["2handedwclass"]
        else:
            wc = it["wclass"]
        return (wc or "hth").upper()

    def plr_name(self, cls, mode, eq):
        wc = self.plr_wclass(cls, mode, eq)
        if mode == 11 and wc not in ("1HS", "1HT", "1JS", "1JT", "1SS", "1ST"):
            wc = "HTH"
        return PLR_TOKEN[cls] + PMODES[mode] + wc

    def start_frame(self, cls, mode, eq):
        """UNIT_AnimStartFrame for a player (anim/0001 § 4), no dual wield."""
        if mode not in (7, 8):
            return 0
        w = self.weapon(eq)
        wc = 0
        if w:
            wc = self.iwcls.get(w[1]["wclass"] or "", 0)
        return self.start[wc][cls]


# ----------------------------------------------------------------------------------------------- the rate
def skill_rec(d, sid):
    return d.sk[sid] if sid is not None and 0 <= sid < len(d.sk) else None


def bonus(i, v):
    return AR.bonus(i, v)


def rate_model(d, line):
    """-> (name, r, sr or None, path speed or None, branch) for an SR line."""
    u = line["u"]
    t, cls, mode = u["t"], u["c"], u["m"]
    stt = {int(k): v for k, v in line["st"].items()}
    g = lambda s: stt.get(s, 0)  # noqa: E731
    ss = set(line["ss"])
    sk = line["sk"]
    skr = skill_rec(d, sk[0]) if sk else None
    if t == 0:
        name = d.plr_name(cls, mode, line.get("eq", []))
    else:
        name = d.mon_name(cls, mode)
    nm, frames, spd, ev, found = d.record(name)
    def fc(q):
        return AR.floor0_cap(q)
    out_sr = None
    pv = None
    if (t, mode) in ((0, 10), (1, 7)) or (t == 0 and mode == 18 and skr and skr["seqtrans"] == 10):
        r = fc(AR.rate_u(spd, min(100 + bonus(2, g(105)), 175)))
        out_sr, br = r, "cast"
    elif (t, mode) in ((0, 9), (1, 6)):
        q = AR.rate_u(spd, bonus(3, g(102)) + (100 if 101 in ss else 50))
        r, br = fc(q if q >= 1 else 1), "block"
    elif (t, mode) in ((0, 4), (1, 3)):
        r, br = fc(AR.rate_u(spd, bonus(1, g(99)) + 50)), "gethit"
    elif (t, mode) in ((0, 19), (1, 13)):
        vb = (0xD5 if t == 0 else d.speeds(cls)[0])
        r, br, pv = fc(vb), "knockback", 0x1000
    else:
        tab = d.mcls["P"] if t == 0 else (d.mcls["M"] if cls < 410 else d.mcls["X"])
        ent = tab[mode] if mode < len(tab) else (0, 0, 0, 0, 0)
        skm, mv, ska, at, fx = ent
        npc = t == 1 and d.mon[cls]["npc"]
        if npc:
            is_move = mode in (2, 15)
        else:
            is_move = bool(mv) or (bool(skm) and sk is not None and (sk[1] & 1) and not (sk[1] & 0x1000))
        if is_move:
            if line.get("pv") is None:
                return nm, None, None, None, "move-nopath", found, frames, spd
            x = max(bonus(4, g(96)) + g(67), 25)
            if t == 0:
                vb = 0x65 if mode == 3 else 0xD5
                pb = (d.cs[cls]["WalkVelocity"] or 0) << 8
            else:
                w, rn = d.speeds(cls)
                vb = rn if mode == 15 else w
                pb = (d.mon[cls]["Velocity"] or 0) << 8
            r = fc(cdiv(s32(vb * x), 100))
            pv = cdiv(s32(pb * x), 100)
            br = "move"
        elif bool(at) or (bool(ska) and skr is not None and skr["UseAttackRate"]):
            x = bonus(0, g(93)) + g(68)
            if t == 0 and mode == 18:
                x -= 30
            x = max(15, min(175, x))
            r = fc(AR.rate_u(spd, x))
            out_sr, br = r, "attack"
        elif bool(fx):
            r, br = fc(spd), "fixed"
        else:
            r, br = fc(AR.rate_u(spd, max(15, min(175, g(69))))), "default"
    return nm, r, out_sr, pv, br, found, frames, spd


# ----------------------------------------------------------------------------------------------- the schedule
def plr_seq(d, seqnum, wc):
    """g_PlrSeqTables[seqnum] column for the composit weapon class wc: [(mode, frame, dir, event)], length."""
    pe = d.pe
    tab = pe.dw(0x007483B8 + 4 * seqnum)
    if not tab:
        return None
    idx = d.cwcls.get(wc.lower())
    if idx is None:
        return None
    col = d.seqcol.get(idx)
    if col is None:
        return None
    ptr, ln, fr = (pe.dw(tab + 12 * col + k) for k in (0, 4, 8))
    if not ptr:
        return None
    frames = [tuple(pe.rd(ptr + 6 * i + 2, 4)) for i in range(ln)]
    return frames, ln


def schedule(T, S, r, L, ev_at):
    """anim/0001 § 7: -> [(kind, frame, a, b)] as queued (frames before EventQueueAt's raise)."""
    out = []
    if r == 0:
        return [(1, T + 1, 0, 0)]
    f, n, acc, t = S, 0, (S << 8) + r, T
    while acc < L:
        t += 1
        while f <= (acc >> 8) and f < 0x90:
            e = ev_at(f)
            if e in (1, 2, 4):
                out.append((0, t, e, n))
                n += 1
            elif e == 3:
                out.append((0, t, 3, 0))
            f += 1
        acc += r
    if t == T:
        t += 1
    out.append((1, t + 1, 0, 0))
    return out


# ----------------------------------------------------------------------------------------------- the step
def path_step(v, d, k=0x400):
    s = s32(v * k) >> 6
    return s32(d[0] * s) >> 12, s32(d[1] * s) >> 12


def halve(ix, iy):
    while ix > 0x10000 or ix < -0x10000:
        ix >>= 1
        iy >>= 1
    while iy > 0x10000 or iy < -0x10000:
        ix >>= 1
        iy >>= 1
    return ix, iy


def sub(v):
    return (v >> 16) & 0xFFFF


def aim(p, x, y, i):
    """PathStep after the move: sub_0064FE40_PathAimNextPoint for a path of type != 4 with points left: the index
    passes every point whose subtile centre is the position (to the end: the index becomes the count)."""
    if p["ty"] == 4 or i >= p["np"] or "pts" not in p:
        return x, y, i
    pts = p["pts"]
    while i < len(pts) and (pts[i][0] << 16) + 0x8000 == x and (pts[i][1] << 16) + 0x8000 == y:
        if i >= p["np"] - 1:
            return x, y, p["np"]
        i += 1
    return x, y, i


def step_model(p, cts):
    """One PathStep from the state p (a PS0 line) with the collision results cts [(tested, r)]:
    -> (x, y, i, stopped, used_cts, note)."""
    if not (p["f34"] & 0x20) or p["np"] <= 0 or p["v"] == 0 or p["i"] >= p["np"]:
        return None
    sx, sy = path_step(p["v"], p["d"], p.get("k") or 0x400)
    if sx == 0 and sy == 0:
        return None
    x, y = p["x"], p["y"]
    snapped = False
    if p["ty"] != 4 and p["pt"]:
        px, py = (p["pt"][0] << 16) + 0x8000, (p["pt"][1] << 16) + 0x8000
        m = max(abs(s32(sx)), abs(s32(sy)))
        if abs(s32(px - x)) <= m and abs(s32(py - y)) <= m:
            sx, sy, snapped = s32(px - x), s32(py - y), True
    tx, ty = (x + sx) & M32, (y + sy) & M32
    i = p["i"]
    if sub(x) == sub(tx) and sub(y) == sub(ty):
        return aim(p, tx, ty, i + snapped) + (False, 0, "same")
    ix, iy = halve(sx, sy)
    cx, cy = x, y
    csub = (sub(cx), sub(cy))
    tsub = (sub(tx), sub(ty))
    k = 0
    count = 0
    while csub != tsub:
        nx, ny = (cx + ix) & M32, (cy + iy) & M32
        nsub = (sub(nx), sub(ny))
        if nsub != csub:
            if k >= len(cts):
                return "need-ct"
            tested, r = cts[k]
            k += 1
            if tested != (nsub[0] | (nsub[1] << 16)):
                return ("ct-mismatch", tested, nsub)
            if r == 0:
                return ((cx & 0xFFFF0000) + 0x8000, (cy & 0xFFFF0000) + 0x8000, p["np"], True, k, "blocked")
            count += 1
            if count >= 10:
                break
        cx, cy, csub = nx, ny, nsub
    return aim(p, tx, ty, i + snapped) + (False, k, "walk")


# ----------------------------------------------------------------------------------------------- the checker
class Checker:
    def __init__(self, d, verbose=False):
        self.d = d
        self.v = verbose
        self.n = collections.Counter()
        self.bad = collections.Counter()
        self.ex = collections.defaultdict(list)
        self.tally = collections.Counter()

    def ok(self, kind, cond, msg=None):
        self.n[kind] += 1
        if not cond:
            self.bad[kind] += 1
            if len(self.ex[kind]) < 8:
                self.ex[kind].append(msg)
        return cond

    def run(self, path):
        lines = []
        with open(path, errors="replace") as f:
            for raw in f:
                tag, _, rest = raw.partition(" ")
                if not rest.startswith("{"):
                    continue
                try:
                    lines.append((tag, json.loads(rest)))
                except ValueError:
                    continue
        self.mon_cls = {}
        for tag, d in lines:
            if tag in ("SR", "MSET", "SCH") and d["u"]["t"] == 1:
                self.mon_cls[d["u"]["u"]] = d["u"]["c"]
        self.check_rates(lines)
        self.check_sched(lines)
        self.check_steps(lines)
        self.check_adv(lines)
        self.check_drain(lines)
        self.check_ghr(lines)
        self.check_pma(lines)
        self.check_obj(lines)
        self.check_actions(lines)
        self.check_chain(lines)
        self.check_block_gate(lines)
        self.check_delay(lines)

    # --- rates ---------------------------------------------------------------------------------------------------
    def check_rates(self, lines):
        self.last_sr = {}
        for tag, d in lines:
            if tag != "SR":
                continue
            u = d["u"]
            if d["c8"] & 8:
                self.tally["sr-transformed-skipped"] += 1
                continue
            res = rate_model(self.d, d)
            nm, r, sr, pv, br, found, frames, spd = res
            key = "rate"
            got = d["rec"]
            self.ok("name", got and got[0] == nm, ("name", d["n"], nm, got))
            if got:
                self.ok("record", got[1] == frames and got[2] == spd, ("rec", d["n"], nm, frames, spd, got))
            if br == "move-nopath":
                self.tally["sr-move-nopath"] += 1
                continue
            self.ok(key, r == d["r"], ("r", d["n"], br, u, r, d["r"], d["st"], d.get("sk")))
            if sr is not None:
                self.ok("seqstep", sr == d["sr"], ("sr", d["n"], br, sr, d["sr"]))
            if pv is not None and d.get("pv") is not None:
                self.ok("pathspeed", pv == d["pv"], ("pv", d["n"], br, u, pv, d["pv"], d["st"]))
            self.tally["sr-%s-%s" % ("p" if u["t"] == 0 else "m", br)] += 1

    # --- schedules and their events ------------------------------------------------------------------------------
    def check_sched(self, lines):
        d = self.d
        last = {}           # unit -> last SR line
        pend = collections.defaultdict(list)    # unit -> [(kind, frame, a, b, sched n)]
        disp = collections.defaultdict(set)     # (unit, frame) -> {(kind, a, b)}
        cancels = collections.defaultdict(list)  # unit -> [(frame, kind, line n)]
        freed = {}                                # unit -> [(frame, line n)]
        last_fr = max((x.get("fr") or 0 for _, x in lines if isinstance(x.get("fr"), int)), default=0)
        for tag, x in lines:
            if tag in ("PDS", "MDS"):
                disp[(x["u"], x["fr"])].add((x["k"], x["a"], x["b"], x["n"]))
            elif tag == "CAN":
                cancels[x["u"]].append((x["fr"], x["k"], x["n"]))
            elif tag == "FREE":
                freed.setdefault(x["u"], []).append((x["fr"], x["n"]))
        queued = {}     # (unit, kind, frame, a, b) -> sched line
        for tag, x in lines:
            if tag == "SR":
                last[x["u"]["u"]] = x
                continue
            if tag != "SCH":
                continue
            u = x["u"]
            uu = u["u"]
            T = x["T"]
            sr = last.get(uu)
            if x["seq"]:
                if u["t"] != 0 or not x.get("sk"):
                    self.tally["sch-seq-monster"] += 1
                    continue
                skr = skill_rec(d, x["sk"][0])
                wc = d.plr_wclass(u["c"], 7, sr.get("eq", []) if sr else [])
                ps = plr_seq(d, skr["seqnum"], wc) if skr else None
                if ps is None:
                    self.ok("sched", False, ("noseq", x["n"], x["sk"], wc))
                    for q in x["q"]:
                        queued[(uu, q[0], max(q[1], T + 1), q[2], q[3])] = x["n"]
                    continue
                frames, ln = ps
                r = x["sr"]
                L = ln << 8
                self.ok("sched-len", x["sl"] == L, ("sl", x["n"], L, x["sl"]))
                S = 0
                ev = lambda f: frames[f][3] if f < len(frames) else 0  # noqa: E731
                if sr:
                    self.ok("sched-rate", sr["sr"] == r, ("sr@sch", x["n"], sr["sr"], r))
            else:
                r = x["r"]
                if sr:
                    self.ok("sched-rate", sr["r"] == r, ("r@sch", x["n"], sr["n"], sr["r"], r))
                rec = x["rec"]
                nm, frames, spd, events, found = d.record(rec[0]) if rec else ("?", 2048, 256, bytes(144), False)
                L = frames << 8
                self.ok("sched-len", x["L"] == L, ("L", x["n"], nm, L, x["L"]))
                S = d.start_frame(u["c"], u["m"], sr.get("eq", []) if sr else []) if u["t"] == 0 else 0
                ev = lambda f, e=events: e[f] if f < 144 else 0  # noqa: E731
                if "s0" in x:
                    self.ok("startframe", x["s0"] == S, ("S", x["n"], u, S, x["s0"]))
            want = schedule(T, S, r, L, ev)
            got = [tuple(q) for q in x["q"]]
            good = self.ok("sched", got == want, ("q", x["n"], u, T, S, r, L, want, got))
            who = "p" if u["t"] == 0 else "m"
            if good:
                self.tally["sch-%s-%d-%d" % (who, u["c"] if who == "p" else 0, u["m"])] += 1
                if who == "p":
                    # the rate cases (plan 0050 Phase 2 *Done when*): class, mode, record, rate
                    self.tally["rate-p%d-m%d-%s-r%d" % (u["c"], u["m"], (x["rec"] or ["?"])[0],
                                                       x["sr"] if x["seq"] else x["r"])] += 1
                else:
                    self.tally["sch-m-m%d-c%d" % (u["m"], u["c"])] += 1
                if who == "m":
                    self.tally["sch-mclass-%d" % u["c"]] += 1
            for q in got:
                fr = max(q[1], T + 1)
                queued[(uu, q[0], fr, q[2], q[3])] = x["n"]
                pend[uu].append((q[0], fr, q[2], q[3], x["n"]))
        # fired or cancelled
        used = set()
        for uu, evs in pend.items():
            for kind, fr, a, b, sn in evs:
                hit = [e for e in disp.get((uu, fr), ()) if e[0] == kind and e[1] == a and e[2] == b]
                if hit:
                    self.ok("fire", True)
                    used.add((uu, fr, kind, a, b))
                    continue
                # cancelled: a CAN of this kind (or both) after the schedule and before the frame
                can = [c for c in cancels.get(uu, ()) if c[2] > sn and c[0] <= fr and c[1] == kind]
                if can:
                    self.tally["cancelled"] += 1
                    continue
                if any(f[1] > sn and f[0] <= fr for f in freed.get(uu, ())):
                    self.tally["unit-freed-first"] += 1
                    continue
                if fr > last_fr:
                    self.tally["after-log-end"] += 1
                    continue
                self.tally["unfired-nocancel"] += 1
                self.ok("fire", False, ("unfired", uu, sn, kind, fr, a, b))
        for (uu, fr), es in disp.items():
            for kind, a, b, n in es:
                if (uu, fr, kind, a, b) not in used:
                    if (uu, kind, fr, a, b) in queued:
                        continue
                    self.ok("dispatch", False, ("unqueued", n, uu, fr, kind, a, b))
                else:
                    self.ok("dispatch", True)

    # --- movement ------------------------------------------------------------------------------------------------
    def check_steps(self, lines):
        prev = {}
        cts = []
        cur = None
        last_sr = {}
        for tag, x in lines:
            if tag == "SR":
                last_sr[x["u"]["u"]] = x
            elif tag == "CT":
                if cur is not None:
                    cts.append((x["t"], x["r"]))
            elif tag == "PS0":
                u = x["u"]
                if cur is not None:
                    self.step_pair(prev[cur], cts, x if x["u"] == cur else None)
                p0 = prev.get(u)
                if p0 is not None and cur != u:
                    pass
                srl = last_sr.get(u)
                if srl and srl.get("pv") is not None and x["t"] in (0, 1):
                    self.ok("pathspeed-step", x["v"] == srl["pv"], ("v", x["n"], u, x["v"], srl["pv"], srl["n"]))
                if x["a"]:
                    self.tally["ps-accel"] += 1
                prev[u] = x
                cur = u
                cts = []
                self.tally["ps-%s-%d" % ("p" if x["t"] == 0 else "m", x["m"])] += 1
            elif tag == "MSET" and cur is not None and x["u"]["u"] == cur:
                pass
        self.tally["ps-lines"] = sum(1 for t, _ in lines if t == "PS0")
        # anim/0003's open question: the first run of an every-frame event queued at a mode start (EF) during the
        # frame's unit-list run: the offset of the unit's first PathStep (PS0) or advance (AD0) after its EF line
        pend = {}
        for tag, x in lines:
            if tag == "EF":
                pend[x["u"]] = x
            elif tag in ("PS0", "AD0") and x["u"] in pend:
                e = pend.pop(x["u"])
                if x["m"] == e["m"]:
                    who = "p" if x.get("t", 1) == 0 else "m"
                    off = x["fr"] - e["fr"]
                    self.tally["ef-first-%s-%s-offset=%d" % (tag[:2].lower(), who, off)] += 1
                    if "ph" in e:
                        # queued at the head of the type's every-frame list: run in this frame only if that list's
                        # walk (phase 3 players, 5 monsters) is still to come
                        want = 0 if e["ph"] < (3 if who == "p" else 5) else 1
                        self.ok("ef-first", off == want, ("ef", e["n"], e["ph"], want, off))
            elif tag == "MSET" and x["u"]["u"] in pend:
                pend.pop(x["u"]["u"], None)

    def step_pair(self, p, cts, nxt):
        res = step_model(p, cts)
        if res is None:
            return
        if nxt is None or nxt["fr"] != p["fr"] + 1:
            self.tally["step-unpaired"] += 1
            return
        if isinstance(res, str) or (isinstance(res, tuple) and isinstance(res[0], str)):
            self.ok("step", False, ("ct", p["n"], res))
            return
        x, y, i, stopped, k, note = res
        if stopped:
            self.tally["step-blocked"] += 1
            return
        same_path = nxt["np"] == p["np"] and nxt.get("pts") == p.get("pts")
        if same_path:
            self.ok("step-point", nxt["i"] == i, ("i", p["n"], i, nxt["i"]))
        else:
            self.tally["step-replanned"] += 1
        good = self.ok("step", (x, y) == (nxt["x"], nxt["y"]), ("xy", p["n"], note, (x, y), (nxt["x"], nxt["y"]),
                                                                 p["v"], p["d"], p["pt"]))
        if good:
            self.tally["step-%s-%s" % ("p" if p["t"] == 0 else "m", note)] += 1

    def mon_seq(self, cls, sk):
        """the monseq rows of the monster's used skill (anim/0001 § 5: MonStats Sk<k>seq of the first Skill<k> = sk)."""
        m = self.d.mon[cls]
        for k in range(1, 9):
            if m.get("Skill%d" % k) == sk and sk not in (None, 199):
                o = m.get("Sk%dseq" % k)
                if o is not None and o >= 1:
                    return self.d.mseq.get(o)
                return None
        return None

    def seq_adv(self, prev, rows):
        """UNIT_AnimAdvance's sequence branch (anim/0001 § 8) -> (sp, L, a44, e4e, m40)."""
        sp0 = prev["sp"]
        sp = sp0 + prev["sr"]
        if sp >= prev["sl"]:
            sp -= prev["sl"]
        L = prev["L"] - prev["sr"]
        f = sp >> 8
        row = rows[f] if f < len(rows) else None
        if row is None:
            return None
        if sp == sp0:
            e = row["event"] or 0
        elif sp < sp0:
            e = 0
        else:
            e = 0
            for g in range((sp0 >> 8) + 1, f + 1):
                ev = rows[g]["event"] if g < len(rows) else 0
                if ev:
                    e = ev
        return sp, L, (row["frame"] or 0) << 8, e, row["mode"]

    def check_adv(self, lines):
        prev = None
        kbe = set()
        for tag, x in lines:
            if tag == "KBE":
                kbe.add((x["ecx"], x["fr"]))
                kbe.add((x["edx"], x["fr"]))
        for tag, x in lines:
            if tag != "AD0":
                continue
            pair = prev is not None and prev["u"] == x["u"] and x["fr"] == prev["fr"] + 1 and x["m"] == prev["m"]
            if pair and not prev["seq"] and not x["seq"]:
                ev = None
                if prev["rec"]:
                    _, _, _, events, found = self.d.record(prev["rec"][0])
                    ev = events if found else None
                a, e = AR.adv_model(prev["a44"], prev["L"], prev["r"], ev)
                if self.ok("adv", (a, e) == (x["a44"], x["e4e"]), ("adv", prev["n"], prev["a44"], prev["L"],
                                                                 prev["r"], (a, e), (x["a44"], x["e4e"]))):
                    self.tally["adv-m%d" % x["m"]] += 1
            elif pair and prev["seq"] and x["seq"]:
                cls = None
                rows = None
                if prev.get("sk"):
                    cls = self.mon_cls.get(prev["u"])
                    rows = self.mon_seq(cls, prev["sk"][0]) if cls is not None else None
                if rows is None:
                    self.tally["adv-seq-norows"] += 1
                else:
                    res = self.seq_adv(prev, rows)
                    got = (x["sp"], x["L"], x["a44"], x["e4e"], x["m40"])
                    if self.ok("adv-seq", res == got, ("advseq", prev["n"], res, got)):
                        self.tally["adv-seq"] += 1
            # a monster knockback ends in the frame its advance reaches the length (anim/0003 § 4)
            if x["m"] == 13 and not x["seq"]:
                ev = None
                a, _ = AR.adv_model(x["a44"], x["L"], x["r"], ev)
                at_end = x["L"] <= a + x["r"]
                got = (x["u"], x["fr"]) in kbe
                if self.ok("kb-end", at_end == got, ("kbend", x["n"], at_end, got)):
                    if at_end:
                        self.tally["kb-end-monster"] += 1
            prev = x

    def check_chain(self, lines):
        """ADR-0014 chaining: for the drawing kinds (GetHitRoll on the defender's seed, PlayerModeAllowed on the
        player's, an object's animation start on its own), a pair is chained when an event's seed before equals the
        previous drawing event's seed after on the same unit (no unlogged draw between)."""
        last = {}
        opened = {}
        for tag, x in lines:
            if tag in ("GR0", "PA0"):
                u = (x["d"] if tag == "GR0" else x["u"])["u"]
                opened[x["n"]] = (tag[:2], u, x["s"])
            elif tag == "OA0":
                opened[x["n"]] = ("OA", x["o"]["u"], x["s"])
            elif tag in ("GR1", "PA1", "OA1"):
                v = opened.pop(x["k"], None)
                if not v:
                    continue
                kind, u, before = v
                if before == x["s"]:
                    continue            # no draw in this event
                prev = last.get(u)
                if prev is not None:
                    self.tally["chain-%s-%s" % (prev[0], kind)] += 1 if prev[1] == before else 0
                    self.tally["chain-%s-%s-broken" % (prev[0], kind)] += 0 if prev[1] == before else 1
                last[u] = (kind, x["s"])
            elif tag == "FREE":
                last.pop(x["u"], None)

    def check_block_gate(self, lines):
        """anim/0003 § 6.1: a blocked hit on a player (result 0x10 or 0x8000, without 0x4000) starts the block mode only when
        frame - stat 95 > stat 102 / 8 (signed, toward zero) + 15 (rev 4 GH lines carry the stats)."""
        schs = collections.defaultdict(set)
        cmds = collections.defaultdict(set)     # (unit, frame) of a block-mode request (PlrModeLeaveOk, req 9)
        for tag, x in lines:
            if tag == "SCH" and x["u"]["t"] == 0 and x["u"]["m"] == 9:
                schs[x["u"]["u"]].add(x["T"])
            elif tag == "PL0" and x["req"] == 9:
                cmds[x["u"]["u"]].add(x["fr"])
        for tag, x in lines:
            if tag != "GH" or x["d"]["t"] != 0 or x.get("st") is None:
                continue
            if not (x["res"] & 0x8010) or x["res"] & 0x4000 or x["res"] & 0x380:
                continue
            st = x["st"]
            gate = x["fr"] - st.get("95", 0) > cdiv(st.get("102", 0), 8) + 15
            # the gate decides whether the block-mode command is issued; the command's own tests (the current
            # mode, anim/0003 § 6.2) decide whether the mode starts
            got = x["fr"] in cmds.get(x["d"]["u"], ())
            if self.ok("block-gate", gate == got, ("block", x["n"], gate, got, st)):
                self.tally["block-gate-%s" % ("open" if gate else "shut")] += 1
                if gate:
                    self.tally["block-gate-open-mode-%s" % ("started" if x["fr"] in schs.get(x["d"]["u"], ())
                                                            else "refused")] += 1

    def check_delay(self, lines):
        """P1b-12 (D1/D2): for a player's delay skill, the interval from one do to the next and the delay (DLY)."""
        last = {}
        for tag, x in lines:
            if tag == "DLY":
                last[x["u"]] = x
            elif tag == "PDS" and x["k"] == 0 and x["u"] in last:
                d = last[x["u"]]
                if x["fr"] > d["fr"]:
                    self.tally["delay-next-do-minus-d=%d" % ((x["fr"] - d["fr"]) - d["d"])] += 1
                    del last[x["u"]]

    def check_actions(self, lines):
        """P1b-1 (plan 0050 Phase 2): per player action, T, the kind-1 end frame E1 (T + n), the next request (PL0) with
        PlrModeLeaveOk's result and PlrModeEndPending's E, and the next mode start (MSET). Checks E against E1 while
        the end is queued; the rest is tallied (ACT lines with -v)."""
        acts = []
        cur = {}
        for idx, (tag, x) in enumerate(lines):
            if tag == "SCH" and x["u"]["t"] == 0:
                e1 = [q[1] for q in x["q"] if q[0] == 1]
                a = {"T": x["T"], "m": x["u"]["m"], "e1": e1[0] if e1 else None, "ev": [q[1] for q in x["q"] if q[0] == 0],
                     "n": x["n"], "req": None, "leave": None, "E": None, "next": None, "u": x["u"]["u"]}
                acts.append(a)
                cur[a["u"]] = a
            elif tag == "PL0" and x["u"]["u"] in cur:
                a = cur[x["u"]["u"]]
                if a["req"] is None and x["fr"] >= a["T"]:
                    a["req"] = (x["fr"], x["req"])
                    a["pl"] = x["n"]
            elif tag == "PLE":
                for a in cur.values():
                    if a.get("pl") and a["E"] is None and a["leave"] is None:
                        a["E"] = x["E"]
            elif tag == "PL1":
                for a in cur.values():
                    if a.get("pl") == x["k"]:
                        a["leave"] = x["r"]
            elif tag == "MSET" and x["u"]["t"] == 0 and x["u"]["u"] in cur:
                a = cur[x["u"]["u"]]
                if a["next"] is None and x["fr"] >= a["T"] and x["to"] != a["m"]:
                    a["next"] = (x["fr"], x["to"])
        for a, b in zip(acts, acts[1:] + [None]):
            if b is not None and b["u"] == a["u"] and a["e1"] is not None:
                dd = (b["T"] - a["T"]) - (a["e1"] - a["T"])
                # back to back (the next action within 3 frames of the end), else a gap
                self.tally["act-m%d-nextact-minus-n=%s" % (a["m"], dd if abs(dd) <= 3 else "gap")] += 1
            if a["E"] is not None and a["e1"] is not None and a["req"] and a["req"][0] <= a["e1"]:
                self.ok("endpending-E", a["E"] == a["e1"], ("E", a["n"], a["E"], a["e1"]))
            if a["e1"] is None or a["next"] is None:
                continue
            n = a["e1"] - a["T"]
            off = a["next"][0] - a["T"]
            self.tally["act-m%d-next-minus-n=%d" % (a["m"], off - n)] += 1
            if self.v:
                print("ACT m=%d T=%d n=%d ev=%s req=%s leave=%s E=%s next=%s" % (
                    a["m"], a["T"], n, [e - a["T"] for e in a["ev"]], a["req"] and (a["req"][0] - a["T"], a["req"][1]),
                    a["leave"], a["E"], (off, a["next"][1])))

    def check_drain(self, lines):
        d = self.d
        open_ = {}
        lid = None
        for tag, x in lines:
            if tag == "PLR":
                lid = x.get("lid")
            elif tag == "DR0":
                open_[x["n"]] = (x, lid)
            elif tag == "DR1":
                v = open_.pop(x["k"], None)
                if not v:
                    continue
                x0, lv = v
                s10 = x0["st"].get("10", 0)
                if lv in TOWNS:
                    self.ok("drain", x["r"] == 1 and x["st"].get("10", 0) == s10, ("town", x0["n"]))
                    continue
                q = (d.cs[x0["c"]]["RunDrain"] or 0) * 2
                if x0["arm"] is not None:
                    it = d.item(x0["arm"])
                    sp = (it or {}).get("speed") or 0
                    q *= cdiv(sp, 10) + 1
                s154 = x0["st"].get("154", 0)
                if s154:
                    q += cdiv(s32(q * s154), 100)
                q = max(q, 1)
                after = s10 - q
                want_r = 1 if after > 0 else 0
                want10 = after if after > 0 else 0
                if self.ok("drain", (x["r"], x["st"].get("10", 0)) == (want_r, want10),
                           ("drain", x0["n"], q, s10, (want_r, want10), (x["r"], x["st"].get("10", 0)))):
                    self.tally["drain-%s" % ("zero" if want_r == 0 else "run")] += 1

    def check_ghr(self, lines):
        opened, hp = {}, {}
        for tag, x in lines:
            if tag == "GR0":
                opened[x["n"]] = x
            elif tag == "GRH":
                hp[x["k"]] = x["hp"]
            elif tag == "GR1":
                g = opened.pop(x["k"], None)
                if not g:
                    continue
                lo, hi = seed_of(g["s"])
                tot, poi, hc = g["tot"], g["poi"], g["hc"]
                draws = 0
                D = None
                if 1 in g["ss"] or (poi and poi == tot) or tot < 0x100:
                    r = 1
                    band = "none"
                else:
                    h = hp.get(x["k"])
                    if h is None:
                        self.ok("ghr", False, ("nohp", g["n"]))
                        continue
                    D = {2: 8, 6: 8, 10: 8, 11: 8, 4: 32, 8: 32, 5: 64}.get(hc, 16)
                    r = None
                    if tot < cdiv(h, D):
                        r, band = 1, "below"
                    else:
                        band = "full"
                        if tot < cdiv(h, cdiv(D, 2)):
                            band = "half"
                            v, lo, hi = RNG.rng_pow2(lo, hi, 2)
                            draws += 1
                            if v == 0:
                                r = 1
                        if r is None and tot < cdiv(h, D // 4 if D >= 0 else cdiv(D, 4)):
                            if band == "full":
                                band = "quarter"
                            v, lo, hi = RNG.rng_pow2(lo, hi, 4)
                            draws += 1
                            if v == 0:
                                r = 1
                        if r is None:
                            r = 0
                            if g["d"]["t"] == 1:
                                m2 = self.d.mon2[self.d.mon[g["d"]["c"]]["MonStatsEx"]]
                                if not m2.get("mGH"):
                                    r = 1
                    self.tally["ghr-D%d" % D] += 1
                want_s = "%08x:%08x" % (lo, hi)
                if self.ok("ghr", (r, want_s) == (x["r"], x["s"]), ("ghr", g["n"], band, (r, want_s), (x["r"], x["s"]))):
                    self.tally["ghr-%s" % band] += 1
                    self.tally["ghr-draws-%d" % draws] += 1
                    h = hp.get(x["k"])
                    if band != "none" and h and D == 16:
                        # P1b-9 (H6): a get-hit with the total in [hp/16, hp/12), a refusal above hp/12
                        if x["r"] == 0 and cdiv(h, 16) <= tot < cdiv(h, 12):
                            self.tally["ghr-p1b9-gethit-in-16-12"] += 1
                        if x["r"] == 1 and tot >= cdiv(h, 12):
                            self.tally["ghr-p1b9-refused-above-12"] += 1

    def check_pma(self, lines):
        opened = {}
        for tag, x in lines:
            if tag == "PA0":
                opened[x["n"]] = x
            elif tag == "PA1":
                p = opened.pop(x["k"], None)
                if not p:
                    continue
                lo, hi = seed_of(p["s"])
                draw = False
                sk = p["sk"]
                skr = skill_rec(self.d, sk[0]) if sk else None
                if 54 not in p["ss"] and p["u"]["m"] not in (0, 17) and skr is not None and skr.get("interrupt") \
                        and 42 in p["ss"] and not (p["a"][2] == sk[0] and skr.get("srvdofunc") in (67, 76)):
                    draw = True
                    _, lo, hi = RNG.rng_range(lo, hi, 100)
                if self.ok("pma-seed", "%08x:%08x" % (lo, hi) == x["s"], ("pma", p["n"], draw, p["s"], x["s"])):
                    self.tally["pma-%s" % ("draw" if draw else "nodraw")] += 1

    def check_obj(self, lines):
        d = self.d
        opened = {}
        lastseed = {}
        for tag, x in lines:
            if tag == "OA0":
                opened[x["n"]] = x
            elif tag == "OA1":
                o0 = opened.pop(x["k"], None)
                if not o0:
                    continue
                cls, mode = o0["o"]["c"], x["m"]
                row = d.obj[cls]
                fd = row["FrameDelta%d" % mode] if mode < 8 else 0
                fd = s16(fd or 0)
                lo, hi = seed_of(o0["s"])
                drew = False
                if row["Sync"]:
                    r = fd
                else:
                    n = fd >> 3
                    v = 0
                    if n >= 1:
                        v, lo, hi = RNG.rng_range(lo, hi, n)
                        drew = True
                    r = fd - (fd >> 4) + v
                r = max(0, min(0x7FFF, r))
                L = (row["FrameCnt%d" % mode] or 0) << 8
                a44 = (row["Start%d" % mode] or 0) << 8
                good = self.ok("obj", (s16(r), "%08x:%08x" % (lo, hi), L, a44) == (x["r"], x["s"], x["L"], x["a44"]),
                               ("obj", o0["n"], cls, mode, (r, lo, hi, L, a44), (x["r"], x["s"], x["L"], x["a44"])))
                if good:
                    self.tally["obj-%s" % ("draw" if drew else "nodraw")] += 1
                    if drew:
                        u = o0["o"]["u"]
                        if lastseed.get(u) == o0["s"]:
                            self.tally["obj-chained"] += 1
                        lastseed[u] = x["s"]

    def report(self):
        for k in sorted(self.tally):
            print("TALLY %s %d" % (k, self.tally[k]))
        for k in sorted(self.ex):
            for e in self.ex[k]:
                print("BAD %s %r" % (k, e))
        parts = ["%s=%d/%d" % (k, self.n[k], self.bad[k]) for k in sorted(self.n)]
        print("CHECK anim " + " ".join(parts))
        return 0 if not sum(self.bad.values()) else 1


# ----------------------------------------------------------------------------------------------- oracle replacement
RATE_PROPS = {"swing1": 93, "swing2": 93, "swing3": 93, "cast1": 105, "cast2": 105, "cast3": 105, "balance1": 99,
              "balance2": 99, "balance3": 99, "block2": 102, "move1": 96, "move2": 96, "move3": 96}


def read_txt(path):
    import csv
    with open(path, encoding="latin-1", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    return [dict(zip(rows[0], r)) for r in rows[1:]]


def recipe_rates(d, root, rec):
    """the rate stats a recipe's items carry (magic suffix mods, unique props at max), and the right-hand weapon
    row; None for an item kind this reader does not resolve."""
    ex = os.path.join(root, "data", "global", "excel")
    uniq = {r["index"]: r for r in read_txt(os.path.join(ex, "uniqueitems.txt"))}
    suf = [r for r in read_txt(os.path.join(ex, "magicsuffix.txt")) if r["Name"] != "Expansion"]
    pre = [r for r in read_txt(os.path.join(ex, "magicprefix.txt")) if r["Name"] != "Expansion"]
    codes = {it.get("code"): i for i, it in enumerate(d.items) if it.get("code")}
    st = collections.Counter()
    eq = []
    for it in rec.get("items", []):
        props = []
        code = it.get("code")
        if "unique" in it:
            u = uniq.get(it["unique"])
            if u is None:
                return None
            code = u["code"]
            mx = it.get("roll", "max") == "max"
            for k in range(1, 13):
                pc = u.get("prop%d" % k)
                if pc:
                    props.append((pc, int((u["max%d" % k] if mx else u["min%d" % k]) or 0)))
        elif "set" in it or "rare" in it:
            return None
        for key, tab in (("suffix", suf), ("prefix", pre)):
            if key in it:
                r = tab[it[key]]
                for k in (1, 2, 3):
                    pc = r.get("mod%dcode" % k)
                    if pc:
                        props.append((pc, int(r["mod%dmax" % k] or 0)))  # magic affixes: min = max for every rate mod
        if it.get("equip") in ("rarm2", "larm2") or "store" in it or "belt_slot" in it:
            continue
        for pc, v in props:
            if pc in RATE_PROPS:
                st[RATE_PROPS[pc]] += v
        bl = {"rarm": 4, "larm": 5, "tors": 3}.get(it.get("equip"))
        if bl and code in codes:
            eq.append([bl, codes[code], 0, 0, 0, 255])
    return st, eq


def replay_skills(d, root, logs):
    """Plan 0045's skills logs (SST0 at the start of a skill mode, SDO0 at its do): the do frame predicted from the
    recipe's items (the rate stats they carry, the right-hand weapon) and the record, against SDO0's frame."""
    import skills_sessions as SS
    out = collections.Counter()
    bad = []
    for path in logs:
        save = None
        lines = []
        with open(path, errors="replace") as f:
            for raw in f:
                if raw.startswith("# installed "):
                    save = raw.split()[2][:-4]
                tag, _, rest = raw.partition(" ")
                if tag in ("SST0", "SDO0") and rest.startswith("{"):
                    lines.append((tag, json.loads(rest)))
        rn = SS.SAVES.get(save, (None,))[0]
        if not rn:
            out["log-no-recipe"] += 1
            continue
        rec = json.load(open(os.path.join(HERE, "d2s_recipes", rn + ".json")))
        rr = recipe_rates(d, root, rec)
        if rr is None:
            out["log-items-unresolved"] += 1
            continue
        st, eq = rr
        wpn = [e for e in eq if e[0] in (4, 5) and d.item(e[1]) and d.item(e[1])["_kind"] == "weapons"]
        if len(wpn) > 1:
            out["log-dual-wield-not-modelled"] += 1
            continue
        open_ = {}
        for tag, x in lines:
            u = x["u"]
            if u["t"] != 0:
                continue
            if tag == "SST0":
                open_[u["u"]] = x
                continue
            s0 = open_.pop(u["u"], None)
            if not s0 or s0["a"][0] != x["a"][0] or s0["u"]["m"] != u["m"]:
                out["do-unpaired"] += 1
                continue
            cls, mode, T = u["c"], u["m"], s0["fr"]
            skr = skill_rec(d, x["a"][0])
            if mode in (2, 3, 6) or skr is None:
                out["do-moving"] += 1
                continue
            stats = {"68": 100 - ((d.weapon(eq) or (0, {}, 0))[1].get("speed") or 0), "69": 100, "67": 100}
            for k, v in st.items():
                stats[str(k)] = v
            line = {"u": {"t": 0, "c": cls, "m": mode}, "st": stats, "ss": [], "sk": [x["a"][0], 0], "eq": eq,
                    "pv": None}
            nm, r, sr, pv, br, found, frames, spd = rate_model(d, line)
            if mode == 18:
                ps = plr_seq(d, skr["seqnum"], d.plr_wclass(cls, 7, eq))
                if ps is None:
                    out["do-noseq"] += 1
                    continue
                fr_, ln = ps
                if sr is None:
                    out["do-seq-no-step"] += 1
                    continue
                q = schedule(T, 0, sr, ln << 8, lambda f: fr_[f][3] if f < len(fr_) else 0)
            else:
                _, _, _, ev, _ = d.record(nm) if found else ("", frames, spd, bytes(144), False)
                q = schedule(T, d.start_frame(cls, mode, eq), r, frames << 8, lambda f: ev[f] if f < 144 else 0)
            first = [e[1] for e in q if e[0] == 0 and e[2] in (1, 2)]
            if not first:
                out["do-no-event"] += 1
                continue
            good = first[0] == x["fr"]
            out["do-%s" % ("ok" if good else "bad")] += 1
            out["do-%s-m%d" % (br, mode)] += 1
            if not good and len(bad) < 12:
                bad.append((os.path.basename(path), x["n"], cls, mode, x["a"][0], nm, r, T, first[0], x["fr"], dict(st)))
    for k in sorted(out):
        print("TALLY %s %d" % (k, out[k]))
    for b in bad:
        print("BAD do %r" % (b,))
    print("CHECK anim-replay-skills do=%d/%d" % (out["do-ok"] + out["do-bad"], out["do-bad"]))
    return 1 if out["do-bad"] else 0


def ghr_draws(tot, poi, hp, hc, lo, hi, freeze=False, mon_gh=True):
    """sub_0057CB00_GetHitRoll (anim/0003 § 6.3) -> (return, band, draws, lo, hi)."""
    if freeze or (poi and poi == tot) or tot < 0x100:
        return 1, "none", 0, lo, hi
    D = {2: 8, 6: 8, 10: 8, 11: 8, 4: 32, 8: 32, 5: 64}.get(hc, 16)
    if tot < cdiv(hp, D):
        return 1, "below", 0, lo, hi
    draws, band = 0, "full"
    if tot < cdiv(hp, cdiv(D, 2)):
        band = "half"
        v, lo, hi = RNG.rng_pow2(lo, hi, 2)
        draws += 1
        if v == 0:
            return 1, band, draws, lo, hi
    if tot < cdiv(hp, cdiv(D, 4)):
        if band == "full":
            band = "quarter"
        v, lo, hi = RNG.rng_pow2(lo, hi, 4)
        draws += 1
        if v == 0:
            return 1, band, draws, lo, hi
    return (0 if mon_gh else 1), band, draws, lo, hi


def replay_combat(logs):
    """The combat runs' GH0/GH1 (the defender's seed around COMBAT_GetHit) against GetHitRoll's draws predicted from
    the AD1 packet (after the reductions: result +0x04, element fields, total +0x4C, +0x60, +0x64) and the
    defender's stat 7 (AD1 "ld"[1], for UnitGetMaxHp): only get-hits (result 0x4) with none of 0x2, 0x8, 0x10, 0x80,
    0x100, 0x200, 0x8000, on a defender left alive. States (freeze, stun) are not in these logs."""
    import struct
    out = collections.Counter()
    bad = []
    for path in logs:
        ad1 = ev0 = None
        with open(path, errors="replace") as f:
            for raw in f:
                tag, _, rest = raw.partition(" ")
                if tag == "AD1":
                    ad1 = json.loads(rest)
                elif tag == "EV0":
                    ad1 = None
                    ev0 = json.loads(rest)
                elif tag == "GH0" and ad1 is not None:
                    gh0 = json.loads(rest)
                elif tag == "GH1" and ad1 is not None:
                    g1 = json.loads(rest)
                    p = bytes.fromhex(ad1["p"])
                    res = struct.unpack_from("<H", p, 4)[0]
                    if not res & 4 or res & 0x839A or (ad1["ld"] and ad1["ld"][0] <= 0):
                        out["skip"] += 1
                        continue
                    tot, poi = struct.unpack_from("<i", p, 0x4C)[0], struct.unpack_from("<i", p, 0x28)[0]
                    hc = struct.unpack_from("<I", p, 0x60)[0]
                    if not p[0x64] and not hc & 0xF0:
                        el = any(struct.unpack_from("<i", p, o)[0] > 0 for o in (0x24, 0x10, 0x1C, 0x28))
                        if el or res & 0x2000:
                            hc |= 0x10                     # any element or doubled nibble: D 16 (anim/0003 § 7)
                        elif hc == 0:
                            hc = 13
                    lo, hi = seed_of(gh0["sd"])
                    r, band, nd, lo, hi = ghr_draws(tot, poi, ad1["ld"][1], hc, lo, hi)
                    good = "%08x:%08x" % (lo, hi) == g1["sd"]
                    out["ghr-%s" % ("ok" if good else "bad")] += 1
                    out["ghr-%s-kind-%s" % ("ok" if good else "bad", ev0.get("k") if ev0 else None)] += 1
                    out["ghr-band-%s" % band] += 1
                    if not good and len(bad) < 10:
                        bad.append((os.path.basename(path), band, nd, tot, ad1["ld"][1], hex(hc), gh0["sd"], g1["sd"]))
                    ad1 = None
    for k in sorted(out):
        print("TALLY %s %d" % (k, out[k]))
    for b in bad:
        print("BAD ghr %r" % (b,))
    print("CHECK anim-replay-combat ghr=%d/%d" % (out["ghr-ok"] + out["ghr-bad"], out["ghr-bad"]))
    return 1 if out["ghr-bad"] else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("check", "replay-skills", "replay-combat"))
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--root", default=os.path.join(ROOT, "workspace", "merged"))
    ap.add_argument("--exe", default=os.path.join(ROOT, "workspace", "install", "app", "game.exe"))
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    if a.cmd == "replay-combat":
        return replay_combat(a.logs)
    d = Data(a.root, a.exe)
    if a.cmd == "replay-skills":
        return replay_skills(d, a.root, a.logs)
    c = Checker(d, a.v)
    for p in a.logs:
        c.run(p)
    return c.report()


if __name__ == "__main__":
    sys.exit(main())
