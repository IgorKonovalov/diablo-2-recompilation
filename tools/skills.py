"""Per-event model of the skill and missile machinery (plan 0045 Phase 2), checked against runtime logs, from
docs/findings/skills/0001-dispatch.md, 0002-missiles.md and 0003-handlers.md.

Usage:
  python3 -I tools/skills.py check <log> [...] [--excel DIR] [-v] [--json OUT] [--gaps OUT]
  python3 -I tools/skills.py manifest <log> [...]          # sha256, size and line count of each log
  python3 -I tools/skills.py audit <log> [...]             # the oracle replacement: what a foreign log holds
  python3 -I tools/skills.py tally <log> [...] [--excel DIR] # the run's coverage counts against plan 0045's minimums

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
        creation callback's re-seed (MCB1) when one ran (0x005C9290: the exit seed on the stream of Init(path x + arg),
        the steps after the Init, the callback's path calls, reported); the owner's seed (the critical roll's 1..3 draws for a row
        that takes weapon damage, else none); the pierce count (missile stat 328) from a local seed Init(owner base
        stat 328). A CanSlow row whose owner is slowed (state 87, not logged) would
        show as a velocity mismatch.
  MF    sub_005ADBB0_MissileDoFrame of a windowed missile with do function 1, 2 or 3 that returned 1: the velocity
        step (the counter, the fifth-step acceleration, the cap), the position step (dir * ((v * 0x400) >> 6)) >> 12
        on both axes of the 16.16 position, frames left - 1; the missile's seed unchanged by the frame's own code: a
        hit nested in the frame (MH0..MH1) moves it by its BuildDamage draws (BD.seed) and the MISSILE_ApplyDamage
        boundary's exit (MA0 -> MA1, an oracle), and the frame exits with the last hit's seed (MF.hitseed, MF.seed).
  SDO/SST  SKILLS_SrvDo / SKILLS_SrvStart: the caster's seed at the exit equals its seed at the entry stepped by the
        draws the nested logged events account for (MC critical draws, THR, DRR, REL) for the rows whose own function
        draws nothing (skills/0003 § 5: Teleport, Nova, Frost Nova, Meteor, Fire Bolt, Blaze, the curses, the
        auras' do); for every other row the steps are reported, not checked.
  CHAIN the game seed across consecutive missile creations of one SrvDo event (the pairs whose creations are not
        separated by any other logged unit creation), and the caster's seed across consecutive skill events.
  BD    MISSILE_BuildDamage inside a MISSILE_HitUnit: the draws on the missile's seed (physical, fire, magic,
        lightning, cold, poison, burn; RangeB(hi - lo) + lo when both stats are >= 1, an inverted pair swapped, then
        the mastery MulDiv on both bounds), the drawn packet fields, the physical percent (25 + 121 + 122, floored at -90) and the critical doubling,
        the cold and burn lengths; the missile's stats taken from the MH0 line (the hit's entry).
  RSK   do 31's call of 0x005C4430 (logger rev 3): one caster draw for a class-363 summon at skill level > 2
        (0x005C4300) or a class-364 summon (0x005C43D0 -> 0x005C4180), none otherwise; the SDO.seed of rows 70 and 80
        counts the same draw per SP1 summon.
Part 2 (plan 0045 Phase 2 part 2, lane/p45k; logger rev 4/5):
  MAS   sub_005A4F50_MonAttackStats: 21, 22, 19 from MonLvlStats by the mode's A1/A2/S1 columns, the El<e> rolls on the
        unit seed and their stats (El1's bounds for every e: the mask 0x40 + e), a summon's other-list offset learned
        at its first call; classes with a SkillDamage owner pair are reported (MAS.seed, MAS.stats).
  EVH   each UNIT_DispatchEvent handler call: the handler unit's seed steps by the handler's own draws (EVH.seed; a
        cast handler's at least one, EVH.seed1), the howl gate on the other unit's flags, mana and life after a kill
        (EVH.mana, EVH.life), open wounds' roll against its STA 62 (EVH.ow).
  PH    sub_0057D810_PreventHealHook: STA state 52 (120 000 frames, stat 31 = 0) exactly when the attacker is a player,
        the defender a monster outside 704..709 and the attacker's stat 117 is non-zero; no draw (PH.state52, PH.seed).
  CU    SKILLS_CanUse at the request (and, rev 5, the client's per-frame check at its changes of code): the aura,
        passive, mana, startmana and delay codes (CU.code); the delay from the unit's last DLY line.
  SP    the summoned unit's seed Init(step(game).low) (SP.seed, SP.gameseed).
  MH.end  a damaging hit of a row with no hit function: the pierce use (stat 328 - 1) and the result (2 when CollideKill
        or the end call, without a pierce used).
  CHAIN.caster+logged  a caster resync attributed by walking the unit's own logged draws (THR, DRR, REL) and the logged
        exits of the spans the checker models or takes (MAS, EVH, MC, RSK; AD, DQ, MA, MHT as boundaries); every resync
        left is listed in --gaps OUT with the lines between.
Reported (oracles, ADR-0014): MH (a hit function's result and the boundary calls after the build), SL/PA, DLY.
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
# do 31's rows (70 Raise Skeleton, 80 Raise Skeletal Mage): the class draw of 0x005C4430 after the spawn, modelled
# per summon (skills/0003 § 5, corrected 2026-10-25).
RAISE_SKELETON = {70, 80}
# (92 Poison Nova: not tier A, the Necromancer's killer, the same do 22 as Nova; 102 Holy Fire's one RollElemDamage is
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


def step_n(t, k):
    for _ in range(k):
        t = step(t)
    return t


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
        # part 2: MonAttackStats (monstats 0x1A8-byte records, monlvl 0x78) and the request checks
        self.ms = read_bin(find_file(excel, "monstats", ".bin"))[0]
        self.ml = read_bin(find_file(excel, "monlvl", ".bin"))[0]

    def ms16(self, c, off):
        return struct.unpack_from("<h", self.ms[c], off)[0]

    def skrow(self, sid):
        """the Skills record fields SKILLS_CanUse and SKILLS_ManaOk read (docs/tables/Skills.md offsets)."""
        r = self.sk[sid]
        return {"b04": r[4], "b05": r[5], "delay": struct.unpack_from("<i", r, 0x190)[0],
                "startmana": struct.unpack_from("<H", r, 0x184)[0]}

    def mrec(self, cls):
        r = self.mi[cls]
        u8 = lambda o: r[o]  # noqa: E731
        h = lambda o: struct.unpack_from("<h", r, o)[0]  # noqa: E731
        H = lambda o: struct.unpack_from("<H", r, o)[0]  # noqa: E731
        return {"vel": u8(0x9A), "vellev": u8(0x9B), "maxvel": H(0x9C), "accel": h(0x9E), "range": h(0x96),
                "levrange": h(0x98), "activate": u8(0x136), "subloop": u8(0x180), "substart": u8(0x181),
                "substop": u8(0x182), "pierce": bool(r[4] & 4), "canslow": bool(r[4] & 8),
                "mskill": bool(r[5] & 0x80), "skill": h(0x194), "srcdmg": u8(0x12D), "srcmiss": u8(0x12E),
                "do": h(0x0C), "hitfn": h(0x0E), "collidekill": r[0x186], "explosion": bool(r[4] & 2),
                "tohit": r[0x18B], "alwaysexplode": r[0x18C]}

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
        self.gaps = []
        self.mon_flags = {}
        self.mas_off = {}
        self.mc_owner = {}
        self.summons = set()

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
        if r["lvlmana"] and lvl > 1:
            self.info["PAY with a lvlmana term (lvl > 1)"] += 1
        self.info["PAY manashift %d" % r["shift"]] += 1
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
                # 0x005C9290: Init(word path+0x10 + arg) at 0x005C92D1 (0x00650E40: low = value, high = 0x29A), then
                # the path calls 0x00648CF0, 0x00648E70 and 0x00649970 step the new seed (unread: a boundary, its
                # steps reported); the check is that the exit seed lies on the stream from that Init
                k = steps_between(((cb0["x10"] + cb0["arg"]) & M32, INIT_HIGH), sd_parse(cb["s"]), 5000)
                self.check("MC.cbseed", k is not None, log, n,
                           "callback x %s + arg %s -> %s" % (cb0["x10"], cb0["arg"], cb["s"]))
                self.dist["MCB steps after the Init (the path calls)"][k if k is not None else ">5000"] += 1
            elif struct.unpack_from("<I", blk, 0x54)[0] == 0x005AC040 and path.get("x10") is not None:
                # plan 0046 Phase 2: the creation callback 0x005AC040 (sub_005AC040_MissCbReseedPathX, skills/0003 § 9;
                # no logger line): Init(word at path +0x10, high 0x29A) at 0x005AC073 (0x00650E40), then the path
                # calls 0x00648CF0, 0x00648E70 and 0x00649970 (as 0x005C9290's) step the new seed: the creation
                # seed lies on the stream from that Init (the steps reported)
                self.info["MC re-seeded by callback 0x005AC040 (no logger line)"] += 1
                k = steps_between((path["x10"] & M32, INIT_HIGH), sd_parse(m["s"]), 5000)
                self.check("MC.cbseed2", k is not None, log, n, "0x005AC040: Init(path x %s) -> %s" %
                           (path["x10"], m["s"]))
                self.dist["0x005AC040 steps after the Init (the path calls)"][k if k is not None else ">5000"] += 1
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
    def mf(self, log, d0, d1, inner=()):
        n = d0["n"]
        p0, p1 = d0.get("path"), d1.get("path")
        if d0.get("do") not in (1, 2, 3) or d1["r"] != 1 or not p0 or not p1:
            self.info["MF frames not checked (do %s, r %s)" % (d0.get("do"), d1["r"])] += 1
            return
        if d0["md"]["rem"] != d1["md"]["rem"] + 1:
            self.fail(log, "MF.left", n, "left %s -> %s" % (d0["md"]["rem"], d1["md"]["rem"]))
        else:
            self.ok["MF.left"] += 1
        # the missile's seed: unchanged by the frame's own code; a hit nested in the frame (MH0..MH1 of this
        # missile) draws on it in BuildDamage (BD0 -> BD1, checked by BD.seed) and may step it inside the
        # MISSILE_ApplyDamage boundary (MA0 -> MA1, an oracle: ADR-0021); the frame's exit seed is the last hit's
        s = d0["s"]
        hits = 0
        for i, (tt, dd) in enumerate(inner):
            if tt != "MH0" or dd["m"].get("u") != d0["m"]:
                continue
            e = next((d2 for t2, d2 in inner[i + 1:] if t2 == "MH1" and d2.get("k") == dd["n"]), None)
            if e is None:
                continue
            hits += 1
            self.check("MF.hitseed", dd["m"].get("s") == s, log, dd["n"], "hit entry seed %s, frame seed %s" %
                       (dd["m"].get("s"), s))
            sub = inner[i + 1:next(j for j, (t2, d2) in enumerate(inner) if d2 is e)]
            want = dd["m"].get("s")
            bd1 = [d2 for t2, d2 in sub if t2 == "BD1"]
            if bd1:
                want = bd1[-1]["sm"]
            ma = [(t2, d2) for t2, d2 in sub if t2 in ("MA0", "MA1")]
            ma0 = next((d2 for t2, d2 in ma if t2 == "MA0" and d2.get("a") == d0["m"]), None)
            ma1 = next((d2 for t2, d2 in ma if t2 == "MA1" and ma0 and d2.get("k") == ma0["n"]), None)
            if ma0 and ma1:
                self.check("MF.hitseed", ma0["sa"] == want, log, ma0["n"], "boundary entry seed %s, after the "
                           "build %s" % (ma0["sa"], want))
                k = steps_between(sd_parse(ma0["sa"]), sd_parse(ma1["sa"]), 4096)
                self.dist["MA boundary steps on the missile seed"][k if k is not None else ">4096"] += 1
                want = ma1["sa"]
            self.check("MF.hitseed", e.get("sm") == want, log, e["n"], "hit exit seed %s, want %s" %
                       (e.get("sm"), want))
            s = e.get("sm")
        if hits:
            self.info["MF frames with a nested hit"] += 1
        self.check("MF.seed", s == d1["s"], log, n, "seed %s -> %s (%d nested hits)" % (d0["s"], d1["s"], hits))
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
                    self.info["MF capped at MaxVel"] += 1
                elif v < 0:
                    v = 0
                    self.info["MF floored at 0"] += 1
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
                if lo > hi:                               # an inverted pair is swapped before the mastery
                    lo, hi = hi, lo                       # (0x005A894B, physical 0x005A89EB)
                    self.info["BD inverted pairs (swapped)"] += 1
                m = stat(st, ms) if ms else 0             # the mastery read on the missile too (0x005A895F)
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
        if not thr and d0.get("d") and not self.T.mrec(m["c"])["tohit"]:
            self.mh_end(log, d0, d1, inner)              # a row with no to-hit roll
            return
        if len(thr) == 1 and d0.get("d"):
            hit = thr[0]["r"] < thr[0]["c"]
            if hit:
                self.info["MH to-hit hits"] += 1
                self.mh_end(log, d0, d1, inner)
                return
            self.info["MH to-hit misses"] += 1
            p0 = stat(m.get("st"), 328)
            R = self.T.mrec(m["c"])
            want = p0 - 1 if (R["pierce"] and p0 > 0) else p0
            if R["pierce"] and p0 > 0:
                self.info["MH missed with a pierce left (C5)"] += 1
            self.check("MH.missed", d1["r"] == 2 and d1.get("m328", 0) == want, log, n,
                       "missed: result %s stat 328 %d -> %s (want 2, %d)" % (d1["r"], p0, d1.get("m328"), want))


    # ================================================================ part 2 (plan 0045 Phase 2 part 2, lane/p45k)
    # ---------------------------------------------------------------- MAS
    # sub_005A4F50_MonAttackStats (ECX unit, EDX mode), read from the pinned image (objdump, 0x005A4F50-0x005A5443):
    # MonLvlStats(class, L, d, stat 12, mask, out) with mask 0x10 (mode 5: A2), 0x20 (modes 7, 8: S1), 0x08 (else: A1);
    # the owner skill-damage pair of 0x0056E050 added (summon classes with a MonStats SkillDamage: not modelled,
    # reported); classic games (game +0x70 == 0) with d > 0 and Align != 1 scale damage by 10/12 and to-hit by 10/15;
    # expansion games add x * b / 128 (truncating) with b = sub_005A4F20_PlayerDmgBonus(game, max(stat 100, 1)), which is
    # 0 for d = 0 or a player count below 2 (every session here: Normal or Nightmare, /players never typed); then
    # the list 0x00625760(unit, 1) cleared (0x00627340) and SetStat 21, 22, 19 on it (absent: nothing written, no draw). Then for e = 0, 1, 2:
    # El<e>Mode (+0xFE + e) must be non-zero and equal the mode; El<e>Pct (+0x104 + d + 3e) non-zero; below 100 one
    # RNG_Range(unit seed, 100) that must be below it; then MonLvlStats with mask 0x40 + e, which is El1's block (0x40)
    # with HP (0x01) or AC (0x02) added for e = 1, 2: the element's min, max and length are El1's for every e (the
    # out-block's +0x2C/+0x30/+0x34; 0 min and max for a noRatio class, whose raw cells go to +0x24/+0x28); El<e>Type
    # (+0x101 + e) 10 draws RNG_Range(unit seed, 5) + 1 as the type and a length of 0 becomes 25; the type's stats are
    # written (1: 48, 49; 2: 50, 51; 3: 52, 53; 4: 54, 55, 56 = length; 5: 57 = 10 min, 58 = 10 max, 59 = 2 length;
    # 6: 60, 61; 7: 62, 63; 8: 64, 65; 9: 66 = length; 11: 316, 317, 315 = length; 10 after the redraw cannot occur).
    MAS_EL = {1: ((48, "mn"), (49, "mx")), 2: ((50, "mn"), (51, "mx")), 3: ((52, "mn"), (53, "mx")),
              4: ((54, "mn"), (55, "mx"), (56, "dur")), 5: ((57, "mn10"), (58, "mx10"), (59, "dur2")),
              6: ((60, "mn"), (61, "mx")), 7: ((62, "mn"), (63, "mx")), 8: ((64, "mn"), (65, "mx")),
              9: ((66, "dur"),), 11: ((316, "mn"), (317, "mx"), (315, "dur"))}
    MAS_STATS = (19, 21, 22, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 315, 316, 317)

    def mas_model(self, cls, lvl, d, L, mode, seed, game70=1):
        """-> (writes {stat: value}, seed after, draws, notes) for one MonAttackStats call."""
        T = self.T
        notes = []
        d = 0 if d < 1 else min(d, 2)
        nml = len(T.ml)
        i = min(lvl, nml - 1)
        row = T.ml[i] if 0 <= i < nml else None
        r32 = lambda off: struct.unpack_from("<i", row, off)[0] if row is not None else 0  # noqa: E731
        noratio = bool(T.ms[cls][0x0C] & 0x04)
        th_o = 0x18 + 0xC * L + 4 * d
        dm_o = 0x48 + 0xC * L + 4 * d
        if mode == 5:
            cth, cmn, cmx = 0xC8, 0xE6, 0xEC
        elif 7 <= mode <= 8:
            cth, cmn, cmx = 0xCE, 0xF2, 0xF8
        else:
            cth, cmn, cmx = 0xC2, 0xDA, 0xE0
        cell = lambda off: T.ms16(cls, off + 2 * d)  # noqa: E731
        if row is None:
            th = mn = mx = 0
        elif noratio:
            th, mn, mx = cell(cth), cell(cmn), cell(cmx)
        else:
            th, mn, mx = (muldiv(r32(th_o), cell(cth), 100), muldiv(r32(dm_o), cell(cmn), 100),
                          muldiv(r32(dm_o), cell(cmx), 100))
        if not game70 and d and T.ms[cls][0x4C] != 1:
            notes.append("classic")
            mn, mx, th = tdiv(mn * 10, 12), tdiv(mx * 10, 12), tdiv(th * 10, 15)
        w = {21: mn, 22: mx, 19: th}
        t = seed
        draws = 0
        r = T.ms[cls]
        for e in range(3):
            em = r[0xFE + e]
            if not em or em != mode:
                continue
            pct = r[0x104 + d + 3 * e]
            if not pct:
                continue
            if pct < 100:
                t = step(t)
                draws += 1
                if t[0] % 100 >= pct:
                    notes.append("el%d roll failed" % (e + 1))
                    continue
            # MonLvlStats mask 0x40 + e: El1's block for every e
            if row is None:
                emn = emx = edur = 0
            else:
                edur = T.ms16(cls, 0x132 + 2 * d)
                if noratio:
                    emn = emx = 0
                else:
                    emn = muldiv(r32(dm_o), T.ms16(cls, 0x10E + 2 * d), 100)
                    emx = muldiv(r32(dm_o), T.ms16(cls, 0x120 + 2 * d), 100)
            if e and (T.ms16(cls, 0x10E + 6 * e + 2 * d), T.ms16(cls, 0x120 + 6 * e + 2 * d),
                      T.ms16(cls, 0x132 + 6 * e + 2 * d)) != (T.ms16(cls, 0x10E + 2 * d), T.ms16(cls, 0x120 + 2 * d),
                                                             edur):
                notes.append("el%d cells differ from el1 (separating)" % (e + 1))
            typ = r[0x101 + e]
            if typ == 10:
                t = step(t)
                draws += 1
                typ = t[0] % 5 + 1
                if edur == 0:
                    edur = 25
            for sid, how in self.MAS_EL.get(typ, ()):
                w[sid] = {"mn": emn, "mx": emx, "dur": edur, "mn10": emn * 10, "mx10": emx * 10,
                          "dur2": edur * 2}[how]
            notes.append("el%d applied (type %d)" % (e + 1, typ))
        return w, t, draws, notes

    def mas(self, log, d0, d1):
        n = d0["n"]
        u = d0["u"]
        cls = u["c"]
        st0, st1 = u.get("st") or {}, d1.get("st") or {}
        s0, s1 = sd_parse(u["s"]), sd_parse(d1["s"])
        if not st0 and not st1:
            # no stat list yet (the first calls at a creation): nothing written, no draw (0x005A4FAB)
            self.check("MAS.seed", s0 == s1, log, n, "no list, seed %s -> %s" % (u["s"], d1["s"]))
            self.info["MAS no stat list"] += 1
            return
        sdmg = struct.unpack_from("<H", self.T.ms[cls], 0xA8)[0]
        if sdmg != 0xFFFF:
            self.info["MAS skill-damage class %d (owner pair not modelled)" % cls] += 1
            return
        g = d0.get("g")
        L = 1 if g is None else int(bool(g[0] or g[3]))
        game70 = 1 if g is None else g[2]
        d = d0.get("diff") or 0
        w, t, draws, notes = self.mas_model(cls, stat(st0, 12), d, L, d0["mode"], s0, game70)
        self.dist["MAS draws"][draws] += 1
        for k in notes:
            self.info["MAS " + k] += 1
        self.check("MAS.seed", t == s1, log, n, "cls %d mode %d: %d draws, %s -> want %s got %s" %
                   (cls, d0["mode"], draws, u["s"], sd_fmt(t), d1["s"]))
        # the list is cleared first (0x00627340 at 0x005A4FB3), then 21, 22, 19 and the applied elements written. The
        # logged values are the unit's full list (every list summed), so only the written stats are compared; a stat
        # MAS_STATS names that the call does not write is reported when it changes (another list, or the clear)
        rev4 = g is not None
        want = {sid: v for sid, v in w.items() if sid in (19, 21, 22) or rev4}
        if rev4:
            for sid in self.MAS_STATS:
                if sid not in w and stat(st0, sid) != stat(st1, sid):
                    self.info["MAS unwritten stat %d changed (%s)" % (sid, "cleared" if not stat(st1, sid)
                                                                     else "other")] += 1
        got = {sid: stat(st1, sid) for sid in want}
        # a summon's other lists add to the same stats (the full list sums every list: e.g. its to-hit bonus): the
        # offset (logged value - written value) is learned at its first call and must stay the same afterwards
        key = (log, u["u"], u.get("id"))
        off = self.mas_off.get(key)
        if off is None:
            if (log, u["u"]) in self.summons:
                self.mas_off[key] = {sid: got[sid] - want[sid] for sid in want}
                self.info["MAS summon: offset learned at its first call"] += 1
                return
            off = {}
        else:
            self.info["MAS checked with a learned offset"] += 1
        want = {sid: v + off.get(sid, 0) for sid, v in want.items()}
        ok = self.check("MAS.stats", got == want, log, n, "cls %d lvl %d mode %d d %d: want %s got %s" %
                        (cls, stat(st0, 12), d0["mode"], d, {k: v for k, v in want.items() if v},
                         {k: v for k, v in got.items() if v}))
        if ok:
            # review-fix 10: does the mode's column choice separate? the other two column sets' writes
            alt = {mm: self.mas_model(cls, stat(st0, 12), d, L, mm, s0, game70)[0] for mm in (4, 5, 7)}
            mine = 5 if d0["mode"] == 5 else 7 if d0["mode"] in (7, 8) else 4
            own = {k2: w[k2] for k2 in (19, 21, 22)}
            others = [mm for mm in alt if mm != mine and {k2: alt[mm][k2] for k2 in (19, 21, 22)} != own]
            if others:
                self.info["MAS mode's columns separate from another set (A1/A2/S1)"] += 1
            if L == 1:
                altL = self.mas_model(cls, stat(st0, 12), d, 0, d0["mode"], s0, game70)[0]
                if {k2: altL[k2] for k2 in (19, 21, 22)} != own:
                    self.info["MAS the L columns separate from the plain ones"] += 1
        if ok and rev4 and any(k.startswith("el") and "applied" in k for k in notes):
            self.ok["MAS.elem"] += 1
        if ok and any("separating" in k for k in notes) and any("applied" in k for k in notes):
            self.info["MAS el2/el3 applied with cells that differ from el1 (separating)"] += 1

    # ---------------------------------------------------------------- H (stat-event handlers)
    # The handlers of skills/0003 section 3, by address: (number, name, draws on the handler's unit before any cast,
    # cast: a successful roll leads to an item cast whose draws are a boundary (ADR-0021), effect).
    HANDLERS = {0x005CAB40: (1, "MissileAtSource", 0, False), 0x005CAC50: (2, "CalcHitAttacker", 0, False),
                0x005CAD40: (3, "ElemHitAttacker", None, False), 0x005C5F50: (4, "ReturnDamage", 0, False),
                0x005C61E0: (5, "LifeTap", 0, False), 0x005BF670: (6, "ThornsPhys", 0, False),
                0x005BF960: (7, "Knockback", 1, False), 0x005BFA10: (8, "Howl", 1, False),
                0x005BFAA0: (9, "Stupidity", 1, False), 0x005BF720: (10, "ThornsLightning", 0, False),
                0x005BF7D0: (11, "ThornsFire", 0, False), 0x005BF880: (12, "ThornsCold", 0, False),
                0x005BFBB0: (13, "DamageToMana", 0, False), 0x005BFC60: (14, "Freeze", 1, False),
                0x005BFE60: (15, "OpenWounds", 1, False), 0x005BFFC0: (16, "CrushingBlow", 1, False),
                0x005C0130: (17, "ManaAfterKill", 0, False), 0x005C0260: (18, "HealAfterDemonKill", 0, False),
                0x005C0310: (19, "Slow", 0, False), 0x005C0470: (20, "SkillOnEvent", 1, True),
                0x005C05A0: (21, "SkillOnGetHit", 1, True), 0x005C6370: (22, "BoneArmorAbsorb", 0, False),
                0x005C6530: (23, "BloodGolemHit", 0, False), 0x005CA6C0: (24, "EnergyShield", 0, False),
                0x005C87A0: (25, "CycloneArmor", 0, False), 0x005C6690: (26, "BloodGolemDamaged", 0, False),
                0x005C6760: (27, "ClayGolemSlow", 0, False), 0x005C01D0: (28, "HealAfterKill", 0, False),
                0x005C0770: (29, "RestInPeace", 0, False), 0x005C0670: (30, "SkillOnDeathOrLevel", 1, True),
                0x005C09E0: (31, "Reanimate", 1, True)}

    def handler(self, log, h0, h1, inner):
        """One UNIT_DispatchEvent handler call (EVH .. EVR): the handler unit's seed steps by the handler's own draws
        (0 or 1 before a cast); a handler that casts (20, 21, 30, 31) on a successful roll leaves the cast's draws
        to the boundary (the steps after its first are reported). The other unit's seed: reported. Effects checked
        where the logged fields hold their inputs (rev 4: the handler's stat value `sv`): 17 mana += sv << 8 and 28
        life += sv << 8, each capped at stat 9 / stat 7; 15 and 16 the roll (low % 100 < sv) against the STA / life
        outcome is combat.py's (reported here)."""
        n = h0.get("n")
        fn = h0.get("fn") or 0
        u = h0.get("u")
        su0 = u.get("s") if isinstance(u, dict) else h0.get("su")
        su1 = h1.get("su")
        H = self.HANDLERS.get(fn)
        tag = "EVH %s" % (H[1] if H else "fn 0x%08X" % fn)
        self.info[tag] += 1
        self.info["EVH event %s" % h0.get("e")] += 1
        if not H or su0 is None or su1 is None:
            self.info["EVH not modelled (no seed or unknown handler)"] += 1
            return
        num, name, draws, cast = H
        a, b = sd_parse(su0), sd_parse(su1)
        k = steps_between(a, b, 4096)
        sv = h0.get("sv")
        if draws is None:
            self.dist["EVH %s steps" % name][k] += 1
            return
        if num == 4 and isinstance(u, dict) and stat(u.get("st"), 6) > 0 and stat(h1.get("st"), 6) <= 0:
            # plan 0046 Phase 2: the returned damage kills the cursed unit (its life stat 6 > 0 at the entry, 0 at the
            # exit): the death's own processing draws on that unit's seed (1 step in the log); reported, not checked
            self.info["EVH ReturnDamage kills the cursed unit (steps reported)"] += 1
            self.dist["EVH ReturnDamage steps when the cursed unit dies"][k] += 1
            return
        if draws == 0:
            self.check("EVH.seed", k == 0, log, n, "%s: no draw, steps %s" % (name, k))
            return
        if num == 8:
            # howl (0x005BFA10): the other unit must be a monster whose MonsterData +0x16 has neither 0x04 nor 0x08
            # (sub_005A0180 with 0x0C) before the stat test and the draw
            ot = h0.get("ot") or {}
            mf = ot.get("mf")
            if mf is None:
                mf = self.mon_flags.get((log, ot.get("id")))
            if ot.get("t") is not None and (ot.get("t") != 1 or (mf is not None and mf & 0x0C)):
                self.check("EVH.seed", k == 0, log, n, "Howl: other type %s flags %s, no draw, steps %s" %
                           (ot.get("t"), mf, k))
                self.info["EVH Howl gate (not a plain monster)"] += 1
                return
        if sv is not None and sv <= 0 and num in (7, 8, 9, 14, 15, 16, 20, 21):
            self.check("EVH.seed", k == 0, log, n, "%s: stat %d gate, steps %s" % (name, sv, k))
            self.info["EVH gate (stat <= 0)"] += 1
            return
        if cast:
            roll = step(a)[0] % 100
            if sv is not None and num in (20, 30) and roll >= sv:
                self.check("EVH.seed", k == 1, log, n, "%s: roll %d >= %d, one draw, steps %s" % (name, roll, sv, k))
                self.info["EVH %s roll failed (no cast)" % name] += 1
                return
            if sv is not None and num in (20, 30):
                self.info["EVH %s roll succeeded (cast: a boundary)" % name] += 1
            self.check("EVH.seed1", k is not None and k >= 1, log, n, "%s: at least one draw, steps %s" % (name, k))
            self.dist["EVH %s steps (the cast's after the first)" % name][k] += 1
            return
        self.check("EVH.seed", k == 1, log, n, "%s: one draw, steps %s" % (name, k))
        if sv is not None and num in (15, 16):
            hit = step(a)[0] % 100 < sv
            self.info["EVH %s roll %s" % (name, "hit" if hit else "missed")] += 1
            if num == 15:
                stas = [dd for tt, dd in inner if tt == "STA" and dd.get("state") == 62]
                self.check("EVH.ow", bool(stas) == hit, log, n, "open wounds roll %s, STA 62 lines %d" %
                           (hit, len(stas)))

    def handler_effect(self, log, h0, h1):
        fn = h0.get("fn") or 0
        sv = h0.get("sv")
        u = h0.get("u")
        if sv is None or not isinstance(u, dict):
            return
        st0, st1 = u.get("st") or {}, h1.get("st") or {}
        if fn in (0x005C0130, 0x005C01D0) and sv > 0:
            cur, mx = (stat(st0, 8), stat(st0, 9)) if fn == 0x005C0130 else (stat(st0, 6), stat(st0, 7))
            self.info["EVH %s: %s" % ("mana after kill" if fn == 0x005C0130 else "heal after kill",
                                      "the addition below the cap (separating)" if mx - cur > (sv << 8) else
                                      "the cap binds")] += 1
        if fn == 0x005C0130 and sv > 0:
            want = min(stat(st0, 8) + (sv << 8), stat(st0, 9))
            want = max(want, stat(st0, 8))
            self.check("EVH.mana", stat(st1, 8) == want, log, h0["n"], "mana after kill %d: %d -> want %d got %d" %
                       (sv, stat(st0, 8), want, stat(st1, 8)))
        elif fn == 0x005C01D0 and sv > 0:
            want = max(min(stat(st0, 6) + (sv << 8), stat(st0, 7)), stat(st0, 6))
            self.check("EVH.life", stat(st1, 6) == want, log, h0["n"], "life after kill %d: %d -> want %d got %d" %
                       (sv, stat(st0, 6), want, stat(st1, 6)))

    # ---------------------------------------------------------------- CU (SKILLS_CanUse at the request)
    def cu(self, log, c0, c1, cul, delay_until):
        """SKILLS_CanUse's code (skills/0001 section 2): 6 aura, 5 passive (the record's +0x04 bits 0x20, 0x10), then
        the ammunition and weapon tests (2, not modelled), the mana test (1: cost (lvlmana * max(lvl - 1, 0) + mana)
        << manashift above stat 8, lvl = clamp(base + bonus, 0, max) with base and bonus the CUL line's), restrict (4,
        not modelled), startmana (1), item charges (2), the delay (8: the unit is in state 121, taken from its last
        DLY line: set at frame f for d frames; the row's delay calc present). Checked: the code the model gives for
        the tests it models, given the logged result passed the ones it does not."""
        n = c0["n"]
        sid = c0.get("sk")
        r = c1["r"]
        self.info["CU code %d%s" % (r, " (client check, a change of code)" if c0.get("cl") else "")] += 1
        if sid is None or not (0 <= sid < len(self.T.sk)):
            self.check("CU.code", r == 3, log, n, "no record, code %d" % r)
            return
        R = self.T.skrow(sid)
        if R["b04"] & 0x20:
            self.check("CU.code", r == 6, log, n, "skill %d aura, code %d" % (sid, r))
            return
        if R["b04"] & 0x10:
            self.check("CU.code", r == 5, log, n, "skill %d passive, code %d" % (sid, r))
            return
        if r in (7, 2) and not cul:
            self.info["CU code %d (level 0 / ammunition, weapon: not modelled)" % r] += 1
            return
        if not cul:
            self.fail(log, "CU.code", n, "skill %d code %d with no mana test line" % (sid, r))
            return
        if c0.get("it", -1) != -1:
            self.info["CU item skill (charges, not modelled)"] += 1
            return
        P = self.T.srec(sid)
        lvl = max(cul["base"] + cul["bonus"], 0)
        cost = s32((P["lvlmana"] * max(lvl - 1, 0) + P["mana"]) << P["shift"])
        mana = stat(c0["u"].get("st"), 8)
        mana_ok = cost <= mana
        if not mana_ok:
            self.check("CU.code", r == 1, log, n, "skill %d lvl %d cost %d mana %d: code %d" % (sid, lvl, cost, mana, r))
            self.dist["CU code 1: cost - mana (1/256)"][min(cost - mana, 512)] += 1
            self.info["CU mana refusal predicted (cost %s mana)" % ">"] += 1
            return
        if r == 4:
            self.info["CU code 4 (restrict, not modelled)"] += 1
            return
        if R["startmana"] and mana < R["startmana"] << 8:
            self.check("CU.code", r == 1, log, n, "skill %d startmana: code %d" % (sid, r))
            return
        fr = c0.get("fr")
        in_delay = delay_until is not None and fr is not None and fr < delay_until
        has_delay = R["delay"] != -1
        want = 8 if (in_delay and has_delay) else 0
        if r == 2:
            self.info["CU code 2 after the mana test (item charges, not modelled)"] += 1
            return
        if delay_until is not None and fr is not None and has_delay and abs(fr - delay_until) <= 1:
            self.info["CU at the delay boundary frame (frame - end %d, code %d)" % (fr - delay_until, r)] += 1
        self.check("CU.code", r == want, log, n, "skill %d frame %s delay until %s (row delay %s): want %d got %d" %
                   (sid, fr, delay_until, has_delay, want, r))
        if want == 0 and r == 0 and mana - cost < 512:
            self.dist["CU code 0 within 2 mana of the cost: mana - cost (1/256)"][mana - cost] += 1
        if want == 8:
            self.info["CU delay refusal predicted"] += 1
            self.dist["CU code 8: frame - the delay's end frame"][fr - delay_until] += 1
        elif in_delay is False and delay_until is not None and fr is not None and has_delay:
            self.dist["CU code 0 after a delay, %s: frame - its end frame (0..3)" % (
                "client change" if c0.get("cl") else "request")][min(fr - delay_until, 4)
                                                                 if fr >= delay_until else "<0"] += 1
        elif in_delay:
            self.info["CU in state 121, row without delay: passes"] += 1

    # ---------------------------------------------------------------- CHAIN.caster with the unit's logged draws
    def caster_gap(self, log, u, utype, prev, s0, between, k, n):
        """ruling (c) of the part 1 review: walk the lines between two skill events of unit u, stepping u's seed for
        each of its own logged draws (THR: the attacker's to-hit roll, the seed after it logged; DRR: a defence roll
        on the defender's seed; REL: RollElemDamage's RangeB) and taking the logged exit of each span whose own draws
        the checker models (MAS0..MAS1, EVH..EVR, MC0..MC1 as the owner, RSK0..RSK1), comparing every logged
        observation of u's seed on the way (a span's entry, a hit's defender or attacker seed). The gap is attributed
        when every observation and the next event's entry agree; else it is listed with the lines between."""
        t = prev
        tags = []
        ok = True
        why = None
        open_spans = {}
        bopen = {}               # boundary spans (AD, DQ, MA, MHT) naming u: their exit seed is taken (ADR-0021)
        for tt, dd in between:
            obs = None
            if tt in ("AD1", "DQ1", "MA1", "MHT1") and (tt[:-1], dd.get("k")) in bopen:
                side = bopen.pop((tt[:-1], dd.get("k")))
                t = sd_parse(dd["sa"] if side == "a" else dd["sb"])
                tags.append(tt[:-1] + " exit")
                continue
            if bopen:
                continue         # inside a boundary: its own draws (the delivery's) are the exit's
            if tt in ("AD0", "DQ0", "MA0", "MHT0") and u in (dd.get("a"), dd.get("b")):
                side = "a" if dd.get("a") == u else "b"
                o2 = dd.get("sa") if side == "a" else dd.get("sb")
                if o2 and sd_parse(o2) != t:
                    ok, why = False, "%s n=%s" % (tt, dd.get("n"))
                    break
                bopen[(tt[:-1], dd["n"])] = side
                continue
            if tt == "THR" and dd.get("a") == u:
                t = step(t)
                obs = dd.get("sa")
                tags.append("THR")
            elif tt == "DRR" and dd.get("u") == u:
                t = step(t)
                obs = dd.get("s")
                tags.append("DRR")
            elif tt == "REL" and dd.get("u") == u:
                obs = dd.get("s")
                if obs and sd_parse(obs) != t:
                    ok, why = False, "REL entry"
                    break
                if dd.get("n", 0) >= 1:
                    t = step(t)
                obs = None
                tags.append("REL")
            elif tt == "MAS0" and dd["u"]["u"] == u:
                obs = dd["u"]["s"]
                open_spans[("MAS", dd["n"])] = 1
                tags.append("MAS")
            elif tt == "MAS1" and ("MAS", dd.get("k")) in open_spans:
                t = sd_parse(dd["s"])
            elif tt == "EVH" and isinstance(dd.get("u"), dict) and dd["u"]["u"] == u:
                obs = dd["u"]["s"]
                open_spans[("EV", dd["n"])] = 1
                tags.append("EVH")
            elif tt == "EVR" and ("EV", dd.get("k")) in open_spans:
                t = sd_parse(dd["su"])
            elif tt == "MC0" and (dd.get("o") or {}).get("u") == u:
                obs = dd["o"]["s"]
                open_spans[("MC", dd["n"])] = 1
                tags.append("MC")
            elif tt == "MC1" and ("MC", dd.get("k")) in open_spans and dd.get("so"):
                t = sd_parse(dd["so"])
            elif tt == "RSK0" and dd.get("u") == u:
                obs = dd["s"]
                open_spans[("RSK", dd["n"])] = 1
            elif tt == "RSK1" and ("RSK", dd.get("k")) in open_spans:
                t = sd_parse(dd["s"])
            elif tt in ("MH0",) and (dd.get("d") or {}).get("u") == u:
                obs = dd["d"].get("s")
                tags.append("MH0.d")
            elif tt in ("MA0", "AD0", "DQ0", "MHT0") and dd.get("b") == u:
                obs = dd.get("sb")
                tags.append(tt + ".b")
            elif tt in ("MA0", "AD0", "DQ0", "MHT0") and dd.get("a") == u:
                obs = dd.get("sa")
                tags.append(tt + ".a")
            elif tt == "PH0" and dd.get("d") == u:
                obs = dd.get("sd")
                tags.append("PH0.d")
            if obs is not None and sd_parse(obs) != t:
                ok, why = False, "%s n=%s" % (tt, dd.get("n"))
                break
        if ok and t == s0:
            self.ok["CHAIN.caster+logged"] += 1
            self.info["CHAIN.caster resync attributed (%s), %s" % ("player" if utype == 0 else "monster",
                                                                  "+".join(sorted(set(tags))) or "none")] += 1
            return
        who = "player" if utype == 0 else "monster"
        # a span closing between the two events that opened before the first one's exit: the first event (an item
        # cast of handler 20 or 21, a skill event of a summon's owner...) was nested in it
        seen = {dd.get("n") for _, dd in between}
        nested = any(tt in ("AD1", "DQ1", "MA1", "MHT1", "EVR", "MH1", "SDO1", "SST1") and dd.get("k") is not None and
                     dd["k"] not in seen for tt, dd in between)
        defender = any(tt == "PH0" and dd.get("d") == u or tt == "MH0" and (dd.get("d") or {}).get("u") == u or
                       tt in ("AD0", "MA0", "DQ0") and dd.get("b") == u for tt, dd in between)
        kind = "nested (a span open across the first event's exit)" if nested else (
            "off the stream within 4096 steps" if k is None else
            "a hit's defender between (PH0, MH0, AD0, MA0 or DQ0): its defence rolls, combat/0001" if defender else
            "no logged line names the unit" if not tags else "not attributed")
        self.info["CHAIN.caster resync left (%s): %s" % (who, kind)] += 1
        self.info["CHAIN.caster resync left (%s)" % who] += 1
        mas = sum(1 for tt, dd in between if tt == "MAS0" and dd["u"]["u"] == u)
        self.gaps.append("%s n=%s %s unit %s [%s]: %s steps; %s; first disagreement %s; own lines %s; MonAttackStats calls "
                         "%d; lines between %d (%s)" % (
                             os.path.basename(log), n, who, u, kind, k, "walk ended off the entry" if ok else "stopped",
                             why, "+".join(tags) or "none", mas, len(between),
                             ",".join(sorted({tt for tt, _ in between}))))

    # ---------------------------------------------------------------- PH (state 52)
    def ph(self, log, d0, d1, inner):
        """sub_0057D810_PreventHealHook (EDI attacker, ESI defender), called by COMBAT_ToHitRoll on a hit
        (skills/0003 section 3): a player attacker, a monster defender of a class outside 704..709 and the attacker's
        stat 117 non-zero give STATE_ApplyTimed(state 52, 120 000 frames, stat 31 = 0) on the defender, nothing
        otherwise; no draw on either seed."""
        want = d0.get("ta") == 0 and d0.get("td") == 1 and not (704 <= (d0.get("dc") or 0) <= 709) and \
            bool(d0.get("s117"))
        sta = [dd for tt, dd in inner if tt == "STA" and dd.get("state") == 52]
        got = len(sta) == 1 and sta[0]["d"] == d0["d"] and sta[0]["len"] == 120000 and sta[0]["stat"] == 31 and \
            sta[0]["val"] == 0
        self.check("PH.state52", (got if want else not sta), log, d0["n"], "want apply %s, STA 52 lines %s" %
                   (want, sta))
        self.info["PH state 52 applied" if want else "PH no apply (%s)" % (
            "stat 117 is 0" if not d0.get("s117") else "attacker or defender type, or class 704-709")] += 1
        self.check("PH.seed", (d0.get("sa"), d0.get("sd")) == (d1.get("sa"), d1.get("sd")), log, d0["n"],
                   "seeds moved in the hook")

    # ---------------------------------------------------------------- SP (the summoned unit)
    def sp(self, log, d0, d1, inner):
        """sub_0056D940_SpawnOwnedMonster: the created unit's seed is Init(step(game).low) inside its SUnitCreate
        (SU0 -> SU1, as a missile's: rng/seeds 7a), the hand-off to monsters/spawn; its stats at SP1 are reported."""
        m = d1.get("m")
        if not m:
            self.info["SP no unit"] += 1
            return
        self.summons.add((log, m["u"]))
        su0 = [dd for tt, dd in inner if tt == "SU0" and dd.get("u") == m["u"]]
        su1 = [dd for tt, dd in inner if tt == "SU1" and dd.get("u") == m["u"]]
        if len(su0) != 1 or len(su1) != 1:
            self.fail(log, "SP.seed", d0["n"], "SU lines %d/%d" % (len(su0), len(su1)))
            return
        pre, post = sd_parse(su0[0]["pre"]), sd_parse(su1[0]["post"])
        self.check("SP.gameseed", step(pre) == post, log, d0["n"], "game seed %s -> %s" % (su0[0]["pre"],
                                                                                         su1[0]["post"]))
        self.check("SP.seed", sd_parse(su1[0]["s"]) == (post[0], INIT_HIGH), log, d0["n"], "unit seed %s, want %s" %
                   (su1[0]["s"], sd_fmt((post[0], INIT_HIGH))))
        self.info["SP class %d" % m["c"]] += 1
        # the stats at the monsters/stats boundary: tools/monstats.py's MonStatsInit draws on the new unit's seed
        # (the appearance draws per MonStats2 component, then the HP draw lo + RangeB(hi - lo + 1) of MonLvlStats;
        # both stock summon classes met here are noRatio, so the raw MonStats cells and no level term), stat 6 = 7 =
        # hp << 8 and stat 31 the AC cell
        import monstats  # noqa: E402 (lazy: its tables load once)
        if not hasattr(self, "_msT"):
            self._msT = monstats.Tables()
            self._msM = monstats.Model(self._msT)
        S = monstats.Seed((post[0], INIT_HIGH))
        self._msM.appearance(S, m["c"], 0, None)
        lo, hi, ac, _ = self._msM.monlvl_stats(m["c"], 1, 0, 1)
        hp = lo + S.rangeb(hi - lo + 1)
        st = m.get("st") or {}
        self.check("SP.stats", (stat(st, 6), stat(st, 7), stat(st, 31)) == (hp << 8, hp << 8, ac), log, d0["n"],
                   "class %d: want life %d AC %d, got %s" % (m["c"], hp, ac, st))
        if hi > lo:
            self.info["SP HP drawn from a range (separating), class %d" % m["c"]] += 1
        mas = [dd for tt, dd in inner if tt == "MAS0" and dd["u"]["u"] == m["u"]]
        if mas:
            k = steps_between((post[0], INIT_HIGH), sd_parse(mas[0]["u"]["s"]), 4096)
            self.dist["SP init -> first MonAttackStats steps (MonStatsInit, class %d)" % m["c"]][k] += 1

    def mh_end(self, log, d0, d1, inner):
        """part 2: the end of a missile at a unit it damages (skills/0002 section 5), for rows with no hit function
        (pSrvHitFunc not in 1..70), on calls that reached the damage build (a BD line inside: no early return 1): the
        pierce use p = 2 (stat 328 - 1) when the row has Pierce, the owner has stat 166 or 156 (taken from the
        missile's creation line, MC0) and stat 328 > 0, else p = 3; c = (Explosion ? 0 : 2) | CollideKill; the result
        is 2 when (c & 1 or end) and p & 1, else 1."""
        m = d0["m"]
        R = self.T.mrec(m["c"])
        if not any(tt == "BD0" for tt, _ in inner):
            self.info["MH no build inside (a filter or a hit function returned first)"] += 1
            return
        if 0 < R["hitfn"] < 71:
            self.info["MH end with a hit function (its result: a boundary)"] += 1
            return
        o = self.mc_owner.get((log, m["u"]))
        if o is None:
            self.info["MH end: missile created before the log or not logged"] += 1
            return
        p328 = stat(m.get("st"), 328)
        pierce = R["pierce"] and (stat(o.get("st"), 166) or stat(o.get("st"), 156)) and p328 > 0
        p = 2 if pierce else 3
        c = (0 if R["explosion"] else 2) | (1 if R["collidekill"] else 0)
        want = 2 if ((c & 1) or d0.get("end")) and (p & 1) else 1
        want328 = p328 - 1 if pierce else p328
        self.check("MH.end", d1["r"] == want and d1.get("m328", 0) == want328, log, d0["n"],
                   "cls %d pierce %s CollideKill %d: want r %d 328 %d, got r %s 328 %s" %
                   (m["c"], bool(pierce), R["collidekill"], want, want328, d1["r"], d1.get("m328")))
        self.info["MH end: %s" % ("pierce used, continues" if pierce else
                                  "ends at the unit" if want == 2 else "continues (no CollideKill)")] += 1

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
        ev_open = []
        delay_until = {}
        ptr2id = {}
        utype = {}
        for i, (t, d) in enumerate(L):
            if t in ("SST0", "SDO0"):
                utype[d["u"]["u"]] = d["u"]["t"]
                ptr2id[d["u"]["u"]] = (d["u"]["t"], d["u"]["id"])
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
                if d1.get("m") and d.get("o"):
                    self.mc_owner[(log, d1["m"]["u"])] = d["o"]
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
            elif t == "RSK0":
                d1 = next((d2 for t2, d2 in L[i + 1:i + 400] if t2 == "RSK1" and d2.get("k") == d["n"]), None)
                sdo = next((d2 for t2, d2 in reversed(L[max(0, i - 400):i]) if t2 == "SDO0"), None)
                if d1 and sdo and sdo["a"][0] in RAISE_SKELETON:
                    k = 1 if (d["c"] == 363 and sdo["a"][1] > 2) or d["c"] == 364 else 0
                    self.check("RSK.seed", step_n(sd_parse(d["s"]), k) == sd_parse(d1["s"]), log, d["n"],
                               "class %s level %d: %d caster draws, %s -> %s" % (d["c"], sdo["a"][1], k, d["s"],
                                                                                 d1["s"]))
            elif t == "PH0":
                d1 = exits.get(("PH", d["n"]))
                if d1:
                    self.ph(log, d, d1, L[i + 1:pos[d1["n"]]])
            elif t == "MON":
                for mm in d.get("m") or ():
                    if "mf" in mm:
                        self.mon_flags[(log, mm.get("id"))] = mm["mf"]
            elif t == "MAS0":
                d1 = exits.get(("MAS", d["n"]))
                if d1:
                    self.mas(log, d, d1)
            elif t == "EVH":
                ev_open.append((i, d))
            elif t == "EVR":
                if ev_open:
                    j0, h0 = ev_open.pop()
                    if d.get("k") is None or d.get("k") == h0["n"]:
                        self.handler(log, h0, d, L[j0 + 1:i])
                        self.handler_effect(log, h0, d)
            elif t == "DLY":
                # keyed by the unit's guid: the client's checks (rev 5, "cl") run on the client's copy of the player
                if d.get("d", 0) > 0 and d.get("fr") is not None:
                    delay_until[ptr2id.get(d["u"], ("ptr", d["u"]))] = d["fr"] + d["d"]
            elif t == "CU0":
                c1 = exits.get(("CU", d["n"]))
                cul = next((d2 for t2, d2 in L[i + 1:i + 8] if t2 == "CUL" and d2.get("k") == d["n"]), None)
                if c1:
                    self.cu(log, d, c1, cul, delay_until.get((d["u"]["t"], d["u"]["id"]),
                                                             delay_until.get(("ptr", d["u"]["u"]))))
            elif t == "SP0":
                d1 = exits.get(("SP", d["n"]))
                if d1:
                    self.sp(log, d, d1, L[i + 1:pos[d1["n"]]])
            elif t == "MF0":
                mf_open[d["m"]] = (i, d)
            elif t == "MF1":
                o = mf_open.pop(d["m"], None)
                if o:
                    self.mf(log, o[1], d, L[o[0] + 1:i])
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
                    prev, ppos = caster_last[u]
                    k = steps_between(prev, s0, 4096)
                    if k == 0:
                        self.ok["CHAIN.caster"] += 1
                    else:
                        self.info["CHAIN.caster resync"] += 1
                        self.dist["caster resync steps"][k if k is not None else ">4096"] += 1
                        # part 2 (ruling (c)): add the unit's own logged draws between the two events
                        self.caster_gap(log, u, utype.get(u), prev, s0, L[ppos + 1:i], k, d["n"])
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
                sid = d["a"][0]
                own = None
                if kind == "SDO" and sid in RAISE_SKELETON:
                    # do 31 after the spawn: 0x005C4430 by the summon's class; 363 -> 0x005C4300, one caster draw
                    # (low % 100 against Skills Param1) when the skill level is > 2; 364 -> 0x005C43D0 ->
                    # 0x005C4180 with its second argument 1, one caster draw (low & 3); any other class none
                    own = 0
                    for t2, d2 in L[i + 1:j]:
                        if t2 == "SP1" and d2.get("m"):
                            c = d2["m"].get("c")
                            if (c == 363 and d["a"][1] > 2) or c == 364:
                                own += 1
                                self.info["SDO %d summon-class draw (class %d)" % (sid, c)] += 1
                    draws += own
                for _ in range(draws):
                    tt = step(tt)
                s1 = sd_parse(d1["s"])
                if NO_OWN_DRAWS.get(sid) or own is not None:
                    self.check(kind + ".seed", tt == s1, log, d["n"], "skill %d caster seed %s after %d nested draws, "
                               "got %s" % (sid, sd_fmt(tt), draws, d1["s"]))
                else:
                    k = steps_between(s0, s1, 4096)
                    self.dist["%s skill %d caster steps" % (kind, sid)][k] += 1
                caster_last[u] = (s1, pos[d1["n"]])
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


def audit(paths, excel=DEFAULT_EXCEL):
    """The oracle replacement (plan 0045 Phase 2): for a log written by another logger (tools/gdb/combat.py,
    tools/gdb/stats.py), count the oracle events of its own checker that this model could replace and the fields each
    replacement needs. A missile packet (combat MS0, RD0) needs the missile's stat list at the hit and the
    BuildDamage lines with the missile's seed (MH0 "m.st", BD0/BD1 "sm"); a creation or a motion step needs MC0/MF0; a
    stat-event handler fire (EVH/EVR) goes through the handler model (part 2: Checker.handler; a fire counts as replaced
    when the model checks its seed effect and the check holds; combat.py's crushing blow and open wounds outcomes stay
    combat.py's); an aura run (stats AU0/AU1) needs the run's RollElemDamage lines (REL).
    Prints one row per log and the totals; returns the rows."""
    rows = []
    tot = Counter()
    T = Tables(excel)
    for p in paths:
        c = Counter()
        for line in open(p, errors="replace"):
            tag, _, rest = line.partition(" ")
            if tag in ("MS0", "RD0", "EVH", "AU0", "MC0", "MF0", "MH0", "BD0", "BD1", "REL", "SDO0"):
                c[tag] += 1
                if tag == "MS0" and '"st"' in rest.split('"o"')[0]:
                    c["MS0 with the missile's stats"] += 1
                if tag in ("BD0", "BD1") and '"sm"' in rest:
                    c["BD with the missile seed"] += 1
                if tag == "MH0" and '"st"' in rest:
                    c["MH0 with the missile's stats"] += 1
        # part 2: the handler fires through the handler model (Checker.handler on the EVH/EVR pairs); a fire is
        # replaced when the model checks its seed effect and it holds (a cast handler's later draws stay a boundary)
        H = Checker(T, False)
        L = parse(p)
        ev = []
        for i, (t, d) in enumerate(L):
            if t == "EVH":
                ev.append((i, d))
            elif t == "EVR" and ev:
                j0, h0 = ev.pop()
                ok0, bad0 = sum(H.ok.values()), sum(H.bad.values())
                H.handler(p, h0, d, L[j0 + 1:i])
                if sum(H.bad.values()) == bad0 and sum(H.ok.values()) > ok0:
                    c["handler fires replaced"] += 1
        hb = sum(H.bad.values())
        tot["handler model mismatches"] += hb
        for k, v in H.info.items():
            if k.startswith("EVH ") and not k.startswith("EVH event"):
                tot["(handlers) " + k] += v
        repl = {
            "missile packets": (c["MS0"], min(c["MS0 with the missile's stats"], c["BD with the missile seed"])),
            "handler fires": (c["EVH"], c["handler fires replaced"]),
            "aura runs": (c["AU0"], min(c["AU0"], c["REL"])),
            "creations and steps": (c["MC0"] + c["MF0"], c["MC0"] + c["MF0"]),
        }
        rows.append((p, repl))
        for k, (a, b) in repl.items():
            tot[k + " events"] += a
            tot[k + " replaceable"] += b
        print("%s  %s" % (os.path.basename(p), "  ".join("%s %d/%d" % (k, b, a) for k, (a, b) in repl.items())))
    print("totals: " + ", ".join("%s %d" % kv for kv in sorted(tot.items())))
    return rows


def tally(paths, excel=DEFAULT_EXCEL):
    """Coverage counts of a run (plan 0045 Phase 2's Done-when): skill events per row, the start refusals (SST
    result 0) and the payment refusals (PAY result 0), creations of the VelLev and LevRange rows at a level above 1
    (cases C2, C4), windowed missiles followed from creation to their removal frame (an MF result 2), hit ends (MH
    result 2) with and without a unit, handler fires per event, summons, MonAttackStats, the creation callbacks.
    Counts only; the checks are `check`'s."""
    T = Tables(excel)
    c = Counter()
    for p in paths:
        L = parse(p)
        exits = {(t[:-1], d["k"]): d for t, d in L if t.endswith("1") and "k" in d}
        win = set()
        for t, d in L:
            if t in ("SST0", "SDO0"):
                c["%s row %d" % (t[:3], d["a"][0])] += 1
                e = exits.get((t[:3], d["n"]))
                if e and e.get("r") == 0:
                    c["%s refused (result 0), row %d" % (t[:3], d["a"][0])] += 1
            elif t == "PAY0":
                e = exits.get(("PAY", d["n"]))
                if e and e.get("r") == 0:
                    c["PAY refused (result 0)"] += 1
            elif t == "MC1" and d.get("m"):
                m = d["m"]
                R = T.mrec(m["c"])
                lv = (m.get("md") or {}).get("lv", 0)
                if R["vellev"] and lv > 1:
                    c["MC VelLev row %d at level > 1 (C2)" % m["c"]] += 1
                if R["levrange"] and lv > 1:
                    c["MC LevRange row %d at level > 1 (C4)" % m["c"]] += 1
                if d.get("win") is not None:
                    win.add(m["u"])
                    c["MC windowed"] += 1
            elif t == "MF1" and d["m"] in win and d.get("r") == 2:
                win.discard(d["m"])
                c["windowed missiles followed to their removal frame"] += 1
            elif t == "MH1":
                if d.get("r") == 2:
                    c["MH result 2 (the missile ends at the hit)"] += 1
            elif t == "MH0":
                c["MH with a unit" if d.get("d") else "MH without a unit"] += 1
            elif t == "EVH":
                c["EVH event %s fn 0x%08X" % (d.get("e"), d.get("fn") or 0)] += 1
                c["EVH fires"] += 1
            elif t == "CU0":
                e = exits.get(("CU", d["n"]))
                if e:
                    c["CU code %d, row %s" % (e["r"], d.get("sk"))] += 1
                    c["CU calls (request checks)"] += 1
            elif t == "STA" and d.get("state") == 52:
                c["STA state 52"] += 1
            elif t in ("SP0", "MAS0", "MCB0", "ARM0", "PF0"):
                c[t] += 1
    for k in sorted(c):
        print("  %-60s %7d" % (k, c[k]))
    return c


def main(argv):
    if argv and argv[0] == "tally":
        a = argv[1:]
        ex = DEFAULT_EXCEL
        if "--excel" in a:
            k = a.index("--excel")
            ex = a[k + 1]
            del a[k:k + 2]
        tally(a, ex)
        return 0
    if argv and argv[0] == "audit":
        audit(argv[1:])
        return 0
    if not argv or argv[0] not in ("check", "manifest"):
        print(__doc__)
        return 2
    logs, excel, verbose, out, gaps = [], DEFAULT_EXCEL, False, None, None
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
        elif a == "--gaps":
            gaps = argv[k + 1]
            k += 2
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
    if gaps:
        with open(gaps, "w") as fh:
            fh.write("caster resyncs left after the unit's own logged draws: %d\n" % len(C.gaps))
            for g in C.gaps:
                fh.write(g + "\n")
    return 1 if report(C, out) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
