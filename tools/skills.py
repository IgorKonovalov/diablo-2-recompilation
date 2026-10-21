"""Per-event model of the skill and missile machinery (plan 0045 Phase 2), checked against runtime logs, from
docs/findings/skills/0001-dispatch.md, 0002-missiles.md and 0003-handlers.md.

Usage:
  python3 -I tools/skills.py check <log> [...] [--excel DIR] [-v] [--json OUT]
  python3 -I tools/skills.py manifest <log> [...]          # sha256, size and line count of each log

<log> is written by tools/d2run.py with tools/gdb/skills.gdb (the tags of tools/gdb/skills.py). The model reads the
.bin tables the game loads (missiles, skills) from --excel (default workspace/merged/data/global/excel).

Checked (a mismatch is any difference):
  PAY   SKILLS_PayCost: cost = (lvlmana * max(lvl - 1, 0) + mana) << (manashift & 31), floored at minmana * 256,
        only when mana or lvlmana is set; paid (stat 8 -= cost, result 1) when cost <= stat 8, else nothing taken and
        result 0. Charge uses (an item skill) and Blood Mana (state 114) are not modelled: none of the sessions has
        them, and a PAY whose stat 8 change is neither 0 nor the cost is a mismatch.
  MC    sub_0059FA30_MissileCreate at its exit: the velocity (((VelLev * lvl) / 8 + Vel) << 8 or the caller's, then
        * 75 / 100), the path's acceleration (Accel) and maximum ((MaxVel & 0xFF) << 8), range (LevRange * lvl + Range,
        the sub-loop frames, the caller's override, less the frames already run), frames left (= range; a lob's
        remaining frames are taken as an oracle), activate mark (range - Activate or the caller's), skill and level;
        the missile's seed (one game-seed step inside SUnitCreate: SU0 -> SU1, the seed Init(post.low)), or the
        creation callback's re-seed (MCB1) when one ran; the owner's seed (the critical roll's 1..3 draws for a row
        that takes weapon damage, else none); the pierce count (missile stat 328) from a local seed Init(owner base
        stat 328). A CanSlow row whose owner is slowed (state 87, not logged) would
        show as a velocity mismatch.
  MF    sub_005ADBB0_MissileDoFrame of a windowed missile with do function 1, 2 or 3 that returned 1: the velocity
        step (the counter, the fifth-step acceleration, the cap), the position step (dir * ((v * 0x400) >> 6)) >> 12
        on both axes of the 16.16 position, frames left - 1; the missile's seed unchanged.
  SDO/SST  SKILLS_SrvDo / SKILLS_SrvStart: the caster's seed at the exit equals its seed at the entry stepped by the
        draws the nested logged events account for (MC critical draws, THR, DRR, REL) for the rows whose own function
        draws nothing (skills/0003 § 5: Teleport, Nova, Frost Nova, Meteor, Fire Bolt, Blaze, the curses, the
        auras' do); for every other row the steps are reported, not checked.
  CHAIN the game seed across consecutive missile creations of one SrvDo event (the pairs whose creations are not
        separated by any other logged unit creation), and the caster's seed across consecutive skill events.
  BD    MISSILE_BuildDamage inside a MISSILE_HitUnit: the draws on the missile's seed (physical, fire, magic,
        lightning, cold, poison, burn; RangeB(hi - lo) + lo when both stats are >= 1, the mastery MulDiv on both bounds
        first), the drawn packet fields, the physical percent (25 + 121 + 122, floored at -90) and the critical doubling,
        the cold and burn lengths; the missile's stats taken from the MH0 line (the hit's entry).
Reported (oracles, ADR-0014): MH (the hit's result and the boundary calls after the build), EVH/EVR, MAS, SP/SL/PA,
DLY.
Exit 0 only if every check holds. Stdlib only. Read-only.
"""
import hashlib
import json
import os
import struct
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from excel_bin import find_file, read_bin  # noqa: E402
from monstats import muldiv  # noqa: E402

DEFAULT_EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
MULT = 0x6AC690C5
M32 = 0xFFFFFFFF
INIT_HIGH = 0x29A
# skills whose start and do functions draw nothing of their own (skills/0003 § 5, the "Draws (own)" column);
# Fire Bolt and Blaze have no srvdofunc: their only action is SrvDo's srvmissile
NO_OWN_DRAWS = {36: True, 44: True, 48: True, 54: True, 56: True, 66: True, 98: True, 68: True, 92: True,
                102: True, 117: True, 130: True, 221: True, 225: True, 251: True, 25: True, 12: True}
# (70 Raise Skeleton is left out: skills/0003 § 5 reads "none", the dev logs show one caster step after the spawn
# returns; reported as a distribution, not checked. 92 Poison Nova: not tier A, the Necromancer's killer, the same do 22 as Nova; 102 Holy Fire's one RollElemDamage is
# the nested REL line, counted with the nested draws)


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    return max(-0x8000, min(0x7FFF, v))


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def sd_parse(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def sd_fmt(t):
    return "%08x:%08x" % t


def step(t):
    v = t[0] * MULT + t[1]
    return v & M32, (v >> 32) & M32


def steps_between(a, b, limit=4096):
    t = a
    for i in range(limit + 1):
        if t == b:
            return i
        t = step(t)
    return None


class Tables:
    def __init__(self, excel=DEFAULT_EXCEL):
        self.mi = read_bin(find_file(excel, "missiles", ".bin"))[0]
        self.sk = read_bin(find_file(excel, "skills", ".bin"))[0]

    def mrec(self, cls):
        r = self.mi[cls]
        u8 = lambda o: r[o]  # noqa: E731
        h = lambda o: struct.unpack_from("<h", r, o)[0]  # noqa: E731
        H = lambda o: struct.unpack_from("<H", r, o)[0]  # noqa: E731
        return {"vel": u8(0x9A), "vellev": u8(0x9B), "maxvel": H(0x9C), "accel": h(0x9E), "range": h(0x96),
                "levrange": h(0x98), "activate": u8(0x136), "subloop": u8(0x180), "substart": u8(0x181),
                "substop": u8(0x182), "pierce": bool(r[4] & 4), "canslow": bool(r[4] & 8),
                "mskill": bool(r[5] & 0x80), "skill": h(0x194), "srcdmg": u8(0x12D), "srcmiss": u8(0x12E),
                "do": h(0x0C)}

    def srec(self, sid):
        r = self.sk[sid]
        return {"mana": struct.unpack_from("<h", r, 0x18A)[0], "lvlmana": struct.unpack_from("<h", r, 0x18C)[0],
                "shift": r[0x188] & 31, "minmana": struct.unpack_from("<H", r, 0x186)[0], "srcdam": r[0x1A5]}


class Mismatch(Exception):
    pass


def parse(path):
    out = []
    with open(path, errors="replace") as fh:
        for ln in fh:
            sp = ln.find(" {")
            if sp < 1 or sp > 8:
                continue
            tag = ln[:sp]
            if not tag.isalnum() or not tag.isupper():
                continue
            try:
                d = json.loads(ln[sp + 1:])
            except ValueError:
                continue
            out.append((tag, d))
    return out


def stat(st, sid):
    return (st or {}).get(str(sid), 0)


class Checker:
    def __init__(self, T, verbose=False):
        self.T, self.v = T, verbose
        self.ok = Counter()
        self.bad = Counter()
        self.info = Counter()
        self.miss = []
        self.dist = defaultdict(Counter)

    def fail(self, log, kind, n, msg):
        self.bad[kind] += 1
        if len(self.miss) < 200:
            self.miss.append("%s n=%s %s: %s" % (os.path.basename(log), n, kind, msg))

    def check(self, kind, cond, log, n, msg):
        if cond:
            self.ok[kind] += 1
        else:
            self.fail(log, kind, n, msg)
        return cond

    # ---------------------------------------------------------------- PAY
    def pay(self, log, d0, d1, utype):
        sid, lvl = d0["a"]
        r = self.T.srec(sid)
        m0, m1 = stat(d0["st"], 8), stat(d1["st"], 8)
        if utype != 0:                           # only players pay: any other unit returns 1, nothing taken
            self.check("PAY", m0 == m1 and d1["r"] == 1, log, d0["n"], "non-player r %d" % d1["r"])
            self.info["PAY non-player"] += 1
            return
        if not (r["mana"] or r["lvlmana"]):
            self.check("PAY", m0 == m1 and d1["r"] == 0, log, d0["n"], "no cost row, mana %d -> %d r %d" %
                       (m0, m1, d1["r"]))
            return
        cost = s32((r["lvlmana"] * max(lvl - 1, 0) + r["mana"]) << r["shift"])
        floored = cost < r["minmana"] * 0x100
        if floored:
            cost = r["minmana"] * 0x100
            self.info["PAY floor binds"] += 1
        if cost <= m0:
            ok = m1 == m0 - cost and d1["r"] == 1
        else:
            ok = m1 == m0 and d1["r"] == 0
            self.info["PAY refused (cost above mana)"] += 1
        self.check("PAY", ok, log, d0["n"], "skill %d lvl %d cost %d mana %d -> %d r %d" %
                   (sid, lvl, cost, m0, m1, d1["r"]))

    # ---------------------------------------------------------------- MC
    def mc(self, log, d0, d1, inner):
        """d0 MC0, d1 MC1, inner: the lines between them (SU0/SU1/MCB0/MCB1/MCM)."""
        n = d0["n"]
        blk = bytes.fromhex(d0["p"])
        f = struct.unpack_from("<I", blk, 0)[0]
        cls = struct.unpack_from("<i", blk, 0x10)[0]
        vel_in = struct.unpack_from("<i", blk, 0x28)[0]
        skill, lvl, loops = struct.unpack_from("<iii", blk, 0x2C)
        ran, act_in, _tohit, rng_in = struct.unpack_from("<iiii", blk, 0x40)
        m = d1.get("m")
        if not m:
            self.info["MC no missile"] += 1
            return
        R = self.T.mrec(cls)
        self.info["MC"] += 1
        path, md = m.get("path") or {}, m.get("md") or {}
        # velocity
        if f & 4:
            v = vel_in if f & 0x10 else s32(vel_in << 8)
        else:
            v = s32((tdiv(R["vellev"] * lvl, 8) + R["vel"]) << 8)
        if v:
            v = tdiv(v * 75, 100)
        # a CanSlow row of an owner in state 87 (slowmissiles, not logged) would be scaled by stat 161: no
        # session meets a Slow Missiles caster, so any difference is a mismatch
        self.check("MC.vel", path.get("v") == v, log, n, "cls %d lvl %d flags %x vel %d, got %s%s" %
                   (cls, lvl, f, v, path.get("v"), " (CanSlow row)" if R["canslow"] else ""))
        if R["vellev"] and not (f & 4):
            self.info["MC VelLev rows (C2)"] += 1
        self.check("MC.accel", path.get("a") == R["accel"] and path.get("mx") == (R["maxvel"] & 0xFF) << 8, log, n,
                   "cls %d accel %d max %d, got %s %s" % (cls, R["accel"], (R["maxvel"] & 0xFF) << 8, path.get("a"),
                                                         path.get("mx")))
        # range, frames left, activate
        mcb = [d for t, d in inner if t == "MCB1"]
        if f & 0x8000:
            rng = rng_in
        else:
            rng = R["levrange"] * lvl + R["range"]
            if f & 8 and R["subloop"]:
                rng += (R["substop"] - R["substart"]) * loops
            if R["levrange"]:
                self.info["MC LevRange rows (C4)"] += 1
        if f & 0x200:
            rng -= ran
        rng16 = s16(rng)
        act = s16(rng - (act_in if f & 0x800 else R["activate"]))
        got = (md.get("rng"), md.get("act"))
        if mcb:
            self.info["MC with a creation callback (range taken after it)"] += 1
        else:
            self.check("MC.range", got == (rng16, act), log, n, "cls %d lvl %d flags %x range %d act %d, got %s" %
                       (cls, lvl, f, rng16, act, got))
            if not f & 0x400:
                self.check("MC.left", md.get("rem") == rng16, log, n, "cls %d left %d got %s" %
                           (cls, rng16, md.get("rem")))
            else:
                self.info["MC lob frames left (oracle)"] += 1
        self.check("MC.skill", (md.get("sk"), md.get("lv")) == (s16(max(skill, 0) if skill >= 1 else 0), s16(lvl)),
                   log, n, "cls %d skill %d lvl %d got %s %s" % (cls, skill, lvl, md.get("sk"), md.get("lv")))
        # the missile's seed
        su0 = [d for t, d in inner if t == "SU0"]
        su1 = [d for t, d in inner if t == "SU1"]
        if len(su0) == 1 and len(su1) == 1:
            pre, post = sd_parse(su0[0]["pre"]), sd_parse(su1[0]["post"])
            self.check("MC.gameseed", step(pre) == post, log, n, "game seed %s -> %s" % (sd_fmt(pre), sd_fmt(post)))
            want = (post[0], INIT_HIGH)
            if mcb:
                cb = mcb[-1]
                self.info["MC re-seeded by the callback"] += 1
                self.check("MC.seed", sd_parse(m["s"]) == sd_parse(cb["s"]), log, n, "callback seed %s, got %s" %
                           (cb["s"], m["s"]))
                cb0 = [d for t, d in inner if t == "MCB0"][-1]
                self.check("MC.cbseed", sd_parse(cb["s"]) == ((cb0["x10"] + cb0["arg"]) & M32, INIT_HIGH), log, n,
                           "callback x %s + arg %s -> %s" % (cb0["x10"], cb0["arg"], cb["s"]))
            else:
                self.check("MC.seed", sd_parse(m["s"]) == want, log, n, "seed %s, got %s" % (sd_fmt(want), m["s"]))
        else:
            self.fail(log, "MC.seed", n, "SU lines %d/%d" % (len(su0), len(su1)))
        # the owner's seed: the critical roll for a row that takes weapon damage
        o = d0.get("o") or {}
        if R["skill"] < 1 and not R["mskill"]:
            src, srcmiss = R["srcdmg"], R["srcmiss"]
        else:
            sk = R["skill"]
            if R["mskill"] and skill > 0:
                sk = skill
            src = self.T.srec(sk)["srcdam"] if 0 <= sk < len(self.T.sk) else 0
            srcmiss = 0
            if R["srcdmg"] == 0xFF:
                src = 0
        draws, crit = 0, 0
        if o and o.get("s") and d1.get("so"):
            t = sd_parse(o["s"])
            if src:
                mcm = [d for tg, d in inner if tg == "MCM"]
                c337, c141 = stat(o.get("st"), 337), stat(o.get("st"), 141)
                t = step(t)
                draws = 1
                if s32(t[0] % 100) < c337:
                    crit = 1
                elif c141:
                    t = step(t)
                    draws += 1
                    crit = int(s32(t[0] % 100) < c141)
                if not crit and mcm and mcm[0]["v"]:
                    t = step(t)
                    draws += 1
                    crit = int(s32(t[0] % 100) < mcm[0]["v"])
                self.info["MC critical rolls (owner draws %d)" % draws] += 1
                self.check("MC.crit", stat(m.get("st"), 141) == crit, log, n, "crit %d got stat 141 %s" %
                           (crit, stat(m.get("st"), 141)))
            elif srcmiss and d0.get("src"):
                self.info["MC source-damage rows (source seed not modelled)"] += 1
            self.check("MC.owner", t == sd_parse(d1["so"]), log, n, "owner seed %s after %d draws, got %s" %
                       (sd_fmt(t), draws, d1["so"]))
            self.dist["MC owner draws"][draws] += 1
        # the pierce count
        if R["pierce"] and o.get("t") in (0, 1):
            p = stat(o.get("st"), 166) + stat(o.get("st"), 156)
            cnt = 0
            if p:
                t = (o.get("b328", 0) & M32, INIT_HIGH)
                for _ in range(4):
                    t = step(t)
                    if s32(t[0] % 100) < p:
                        cnt += 1
                    else:
                        break
                self.info["MC pierce draws"] += 1
            self.check("MC.pierce", stat(m.get("st"), 328) == cnt or m.get("b328", 0) == cnt, log, n,
                       "pierce %d got %s" % (cnt, stat(m.get("st"), 328)))
        return v

    # ---------------------------------------------------------------- MF
    def mf(self, log, d0, d1):
        n = d0["n"]
        p0, p1 = d0.get("path"), d1.get("path")
        if d0.get("do") not in (1, 2, 3) or d1["r"] != 1 or not p0 or not p1:
            self.info["MF frames not checked (do %s, r %s)" % (d0.get("do"), d1["r"])] += 1
            return
        if d0["md"]["rem"] != d1["md"]["rem"] + 1:
            self.fail(log, "MF.left", n, "left %s -> %s" % (d0["md"]["rem"], d1["md"]["rem"]))
        else:
            self.ok["MF.left"] += 1
        self.check("MF.seed", d0["s"] == d1["s"], log, n, "seed %s -> %s" % (d0["s"], d1["s"]))
        v, a, cnt, mx = p0["v"], p0["a"], p0["cnt"], p0["mx"]
        if v == 0 and p1["v"] == 0:
            self.check("MF.still", (p0["x"], p0["y"]) == (p1["x"], p1["y"]), log, n, "a still missile moved")
            return
        if a:
            cnt += 1
            if cnt >= 5:
                cnt = 0
                v += a
                if v > mx:
                    v, a = mx, 0
                elif v < 0:
                    v = 0
        self.check("MF.vel", (p1["v"], p1["a"], p1["cnt"]) == (v, a, cnt), log, n,
                   "v %d a %d cnt %d, got %s %s %s" % (v, a, cnt, p1["v"], p1["a"], p1["cnt"]))
        if p0["a"]:
            self.info["MF accelerating steps (C3)"] += 1
            if cnt == 0:
                self.info["MF fifth steps (C3)"] += 1
        s = (p1["v"] * 0x400) >> 6
        dx, dy = (p0["dx"] * s) >> 12, (p0["dy"] * s) >> 12
        want = ((p0["x"] + dx) & M32, (p0["y"] + dy) & M32)
        self.check("MF.pos", (p1["x"], p1["y"]) == want, log, n, "pos %s, got %s (v %d dir %d,%d)" %
                   (want, (p1["x"], p1["y"]), p1["v"], p0["dx"], p0["dy"]))

    # ---------------------------------------------------------------- BD
    # MISSILE_BuildDamage's draws on the missile's seed (skills/0002 § 6): (min stat, max stat, mastery stat, offset)
    BD_ROLLS = ((21, 22, None, 0x08), (48, 49, 329, 0x10), (52, 53, 357, 0x20), (50, 51, 330, 0x1C),
                (54, 55, 331, 0x24), (57, 58, 332, 0x28), (316, 317, 329, 0x14))

    def bd(self, log, mh0, b0, b1):
        """mh0: the MH0 line (the missile's stats at the hit), b0/b1 the BD lines inside it."""
        n = b0["n"]
        st = mh0["m"].get("st") or {}
        t = sd_parse(b0["sm"])
        pk = list(struct.unpack("<28i", bytes.fromhex(b1["p"])))
        vals = {}
        draws = 0
        for lo_s, hi_s, ms, off in self.BD_ROLLS:
            lo, hi = stat(st, lo_s), stat(st, hi_s)
            if lo >= 1 and hi >= 1:
                m = stat(st, ms) if ms else 0
                if m:
                    lo += muldiv(lo, m, 100)
                    hi += muldiv(hi, m, 100)
                d = hi - lo
                if d >= 1:
                    t = step(t)
                    draws += 1
                    vals[off] = t[0] % d + lo
                else:
                    vals[off] = lo
        self.dist["BD draws on the missile seed"][draws] += 1
        self.check("BD.seed", t == sd_parse(b1["sm"]), log, n, "missile seed %s after %d draws, got %s" %
                   (sd_fmt(t), draws, b1["sm"]))
        for off, v in vals.items():
            if off == 0x08:
                continue                                  # physical: the percent terms follow (checked below)
            self.check("BD.elem", pk[off // 4] == v, log, n, "packet +0x%02x %d, got %d" % (off, v, pk[off // 4]))
        if 0x08 in vals:
            ph = vals[0x08]
            pct = stat(st, 25) + stat(st, 121) + stat(st, 122)
            if any(k.startswith("180:") for k in st):
                self.info["BD physical with stat-180 entries (not checked)"] += 1
                return
            pct = max(pct, -90)
            ph += tdiv(ph * pct, 100)
            if stat(st, 141):
                ph *= 2
            self.check("BD.phys", pk[0x08 // 4] == ph, log, n, "physical %d (pct %d crit %d), got %d" %
                       (ph, pct, stat(st, 141), pk[0x08 // 4]))
        for sid, off in ((56, 0x30), (315, 0x18)):
            if stat(st, sid):
                self.check("BD.len", pk[off // 4] == stat(st, sid), log, n, "length +0x%02x %d got %d" %
                           (off, stat(st, sid), pk[off // 4]))

    # ---------------------------------------------------------------- SL
    def sl(self, log, d0, d1):
        """sub_005C49E0_SummonSetLevel(summon, lvl, skill level): lvl <= 0 takes L = the owner's level and sets
        min(max(L * 3 / 4 + skill level, 1), L), leaving the level unset when L is 0; else the level is lvl (C1)."""
        _m, lvl, sl = d0["a"]
        L = d0.get("o12") or 0
        if lvl <= 0:
            want = min(max(tdiv(L * 3, 4) + sl, 1), L) if L else d0.get("m12")
            self.info["SL from the owner's level (C1)"] += 1
        else:
            want = lvl
            self.info["SL given level"] += 1
        self.check("SL.level", d1["m12"] == want, log, d0["n"], "summon level %s (L %d, lvl %d, skill %d), got %s" %
                   (want, L, lvl, sl, d1["m12"]))

    # ---------------------------------------------------------------- MH
    def mh(self, log, d0, d1, inner):
        """The to-hit roll of a missile (THR: the roll is the attacker's next draw, low % 100) and a missed roll: the
        missile ends (result 2), a Pierce row having used one pierce (stat 328 - 1) before the roll (case C5)."""
        n = d0["n"]
        thr = [dd for tt, dd in inner if tt == "THR"]
        for t in thr:
            self.check("THR.roll", t["r"] == sd_parse(t["sa"])[0] % 100, log, t["n"], "roll %d, seed after %s" %
                       (t["r"], t["sa"]))
        m = d0["m"]
        if len(thr) == 1 and d0.get("d"):
            hit = thr[0]["r"] < thr[0]["c"]
            if hit:
                self.info["MH to-hit hits"] += 1
                return
            self.info["MH to-hit misses"] += 1
            p0 = stat(m.get("st"), 328)
            R = self.T.mrec(m["c"])
            want = p0 - 1 if (R["pierce"] and p0 > 0) else p0
            if R["pierce"] and p0 > 0:
                self.info["MH missed with a pierce left (C5)"] += 1
            self.check("MH.missed", d1["r"] == 2 and d1.get("m328", 0) == want, log, n,
                       "missed: result %s stat 328 %d -> %s (want 2, %d)" % (d1["r"], p0, d1.get("m328"), want))

    # ---------------------------------------------------------------- the run
    def run(self, log):
        L = parse(log)
        self.info["logs"] += 1
        by_n = {d.get("n"): (t, d) for t, d in L if "n" in d}
        exits = {}
        for t, d in L:
            if t.endswith("1") and "k" in d:
                exits[(t[:-1], d["k"])] = d
        pos = {d["n"]: i for i, (t, d) in enumerate(L) if "n" in d}
        caster_last = {}
        mf_open = {}
        utype = {}
        for i, (t, d) in enumerate(L):
            if t in ("SST0", "SDO0"):
                utype[d["u"]["u"]] = d["u"]["t"]
            if t == "PAY0":
                d1 = exits.get(("PAY", d["n"]))
                if d1:
                    self.pay(log, d, d1, utype.get(d["u"]))
            elif t == "MC0":
                d1 = exits.get(("MC", d["n"]))
                if not d1:
                    self.info["MC no exit line"] += 1
                    continue
                j = pos[d1["n"]]
                inner = [(tt, dd) for tt, dd in L[i + 1:j] if tt in ("SU0", "SU1", "MCB0", "MCB1", "MCM")]
                # nested creations (a callback creating a missile) would put their SU lines here too
                if any(tt == "MC0" for tt, _ in L[i + 1:j]):
                    self.info["MC with a nested creation (not checked)"] += 1
                    continue
                self.mc(log, d, d1, inner)
            elif t == "MH0":
                d1 = exits.get(("MH", d["n"]))
                if not d1:
                    continue
                j = pos[d1["n"]]
                inner = L[i + 1:j]
                self.mh(log, d, d1, inner)
                bds = [(tt, dd) for tt, dd in inner if tt in ("BD0", "BD1")]
                if len(bds) == 2 and bds[0][0] == "BD0" and bds[1][0] == "BD1" and bds[1][1]["k"] == bds[0][1]["n"]:
                    self.bd(log, d, bds[0][1], bds[1][1])
                elif bds:
                    self.info["MH with %d BD lines (not checked)" % len(bds)] += 1
            elif t == "SL0":
                d1 = exits.get(("SL", d["n"]))
                if d1 and "m12" in d:                   # logger rev 2
                    self.sl(log, d, d1)
            elif t == "MF0":
                mf_open[d["m"]] = d
            elif t == "MF1":
                d0 = mf_open.pop(d["m"], None)
                if d0:
                    self.mf(log, d0, d)
            elif t in ("SST0", "SDO0"):
                kind = t[:3]
                d1 = exits.get((kind, d["n"]))
                if not d1:
                    self.info["%s no exit line" % kind] += 1
                    continue
                self.info["%s %d" % (kind, d["a"][0])] += 1
                u = d["u"]["u"]
                s0 = sd_parse(d["u"]["s"])
                # chaining: the caster's seed against its exit seed at the previous skill event
                if u in caster_last:
                    prev = caster_last[u]
                    k = steps_between(prev, s0, 4096)
                    if k == 0:
                        self.ok["CHAIN.caster"] += 1
                    else:
                        self.info["CHAIN.caster resync"] += 1
                        self.dist["caster resync steps"][k if k is not None else ">4096"] += 1
                j = pos[d1["n"]]
                tt = s0
                draws = 0
                mcs = []
                for t2, d2 in L[i + 1:j]:
                    if t2 == "MC0" and (d2.get("o") or {}).get("u") == u:
                        e = exits.get(("MC", d2["n"]))
                        if e and e.get("so"):
                            k = steps_between(sd_parse(d2["o"]["s"]), sd_parse(e["so"]), 64)
                            draws += k or 0
                        mcs.append(d2)
                    elif t2 == "THR" and d2.get("a") == u:
                        draws += 1
                    elif t2 == "DRR" and d2.get("u") == u:
                        draws += 1
                    elif t2 == "REL" and d2.get("u") == u and d2.get("n", 0) >= 1:
                        draws += 1
                for _ in range(draws):
                    tt = step(tt)
                s1 = sd_parse(d1["s"])
                sid = d["a"][0]
                if NO_OWN_DRAWS.get(sid):
                    self.check(kind + ".seed", tt == s1, log, d["n"], "skill %d caster seed %s after %d nested draws, "
                               "got %s" % (sid, sd_fmt(tt), draws, d1["s"]))
                else:
                    k = steps_between(s0, s1, 4096)
                    self.dist["%s skill %d caster steps" % (kind, sid)][k] += 1
                caster_last[u] = s1
                # the game seed across consecutive creations of this event
                prev_post = None
                for d2 in mcs:
                    e = exits.get(("MC", d2["n"]))
                    j2 = pos[e["n"]] if e else None
                    a2 = pos[d2["n"]]
                    su = [dd for tt3, dd in L[a2 + 1:j2] if tt3 in ("SU0", "SU1")] if j2 else []
                    if len(su) != 2:
                        prev_post = None
                        continue
                    if prev_post is not None:
                        k = steps_between(prev_post, sd_parse(su[0]["pre"]), 4096)
                        if k == 0:
                            self.ok["CHAIN.gameseed"] += 1
                        else:
                            self.info["CHAIN.gameseed resync"] += 1
                            self.dist["game seed gap between creations"][k] += 1
                    prev_post = sd_parse(su[1]["post"])
            elif t == "MC1" and d.get("win") is not None:
                pass
        # the first step of a windowed missile: frames from its creation to its first MF line
        created = {}
        for t, d in L:
            if t == "MC0":
                created[d["n"]] = d.get("fr")
            elif t == "MC1" and d.get("win") is not None and d.get("m"):
                created[("m", d["m"]["u"])] = created.get(d["k"])
            elif t == "MF0":
                fr0 = created.pop(("m", d["m"]), None)
                if fr0 is not None and d.get("fr") is not None:
                    self.dist["first MF frame - creation frame"][d["fr"] - fr0] += 1
        for t, d in L:
            if t in ("MH0", "EVH", "MAS0", "SP0", "SL0", "PA0", "DLY", "BD0", "ARM0", "PF0", "STA"):
                self.info["oracle %s" % t] += 1
        return by_n


def report(C, out=None):
    lines = []
    lines.append("checks (ok / mismatch):")
    for k in sorted(set(C.ok) | set(C.bad)):
        lines.append("  %-18s %7d %5d" % (k, C.ok[k], C.bad[k]))
    lines.append("counts:")
    for k in sorted(C.info):
        lines.append("  %-60s %7d" % (k, C.info[k]))
    lines.append("distributions:")
    for k in sorted(C.dist):
        lines.append("  %s: %s" % (k, ", ".join("%s x%d" % (a, b) for a, b in sorted(C.dist[k].items(),
                                                                                  key=lambda x: str(x[0])))))
    tot = sum(C.bad.values())
    lines.append("mismatches: %d" % tot)
    for m in C.miss[:60]:
        lines.append("  " + m)
    text = "\n".join(lines)
    print(text)
    if out:
        with open(out, "w") as fh:
            json.dump({"ok": C.ok, "bad": C.bad, "info": C.info,
                       "dist": {k: {str(a): b for a, b in v.items()} for k, v in C.dist.items()},
                       "mismatches": C.miss}, fh, indent=1, sort_keys=True)
    return tot


def main(argv):
    if not argv or argv[0] not in ("check", "manifest"):
        print(__doc__)
        return 2
    logs, excel, verbose, out = [], DEFAULT_EXCEL, False, None
    k = 1
    while k < len(argv):
        a = argv[k]
        if a == "--excel":
            excel = argv[k + 1]
            k += 2
        elif a == "--json":
            out = argv[k + 1]
            k += 2
        elif a == "-v":
            verbose = True
            k += 1
        else:
            logs.append(a)
            k += 1
    if argv[0] == "manifest":
        for p in logs:
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            n = sum(1 for _ in open(p, "rb"))
            print("%s  %s  %d bytes  %d lines" % (h, p, os.path.getsize(p), n))
        return 0
    C = Checker(Tables(excel), verbose)
    for p in logs:
        C.run(p)
    return 1 if report(C, out) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
