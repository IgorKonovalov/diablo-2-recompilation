"""Per-event model of the server's combat formulas (plan 0037 Phase 2), checked against runtime logs, from
docs/findings/combat/0001-formulas.md.

Usage:
  python3 -I tools/combat.py check <log> [...] [--excel DIR] [--exe EXE] [-v] [--json OUT]
  python3 -I tools/combat.py manifest <log> [...]          # sha256, size and line count of each log

<log> is written by tools/d2run.py with tools/gdb/combat.gdb (the tags of tools/gdb/combat.py). The model reads the
.bin tables the game loads (monstats, difficultylevels, charstats, weapons, itemtypes, missiles, itemstatcost) from
--excel (default workspace/merged/data/global/excel) and two image tables from --exe (the pinned game.exe):
g_DamageResistTable 0x00732980 (12 rows of 11 dwords) and the player-count life percents 0x006E1590.

An event is one COMBAT_MeleeHitTest .. COMBAT_DeliverQueued (EV0 .. EVX: player attack "pa", monster attack on the
player or a hireling "ma", hireling attack "ha"), one MISSILE_ApplyDamage (MS0 .. MSX: on the player or a hireling
"md", the player's missile on a monster "pm"), or one MonAttackStats (MAS0 .. MAS1). Per event the checker:
  * predicts every draw on the attacker's and the defender's unit seed in the order of the finding, and asserts the
    seed at every logged snapshot (THR, DRR, BD0/RPE/BDC/BD1, AD0/AD1, EVH/EVR, LE1, DU0/DU1, KB0/KB1, GH0/GH1, EVX,
    MSX): the event's exit seeds are asserted, so a missing or extra draw is a mismatch;
  * predicts the outputs: AR and DEF (THB/THV), the chance c and the roll r (THR), every defence roll (DRR), the
    builder's packet (BD1), the percent P and the reduced packet (RDP/RD1), the result word and kill bit (AD0), the
    crushing-blow and open-wounds handlers (EVR life, STA), the leech (LE1) and the life change (AD1);
  * takes as value oracles (ADR-0014): every stat the unit lists hold at EV0/MS0 (and life 6..11 at each snapshot),
    UnitBlockChance (DRB), UnitIsMoving (DRM), WeaponBlockChance (WBC) and its skill check (WBS), the two-hand test
    (RPT), the weapon mastery damage and crit (RPM, BDC), the skill or missile packet when no builder ran (RD0, MS0);
  * takes as boundary oracles (ADR-0004: entry asserted, exit taken): stat-event handlers other than crushing blow
    (0x005BFFC0) and open wounds (0x005BFE60), COMBAT_DurabilityLoss (DU0/DU1), the knockback (KB0/KB1), COMBAT_GetHit
    (GH0/GH1);
  * drops (and counts) events with a PRG line (a progressive-charge state hook ran: Phase 1 review ruling 3), events
    with no exit line, and events whose defender is not hostile or is in town (no AD0 after a hit).
Chaining (ADR-0014; Phase 1 review ruling 5): per seed role. The player's seed chains across consecutive logged
events on it (any kinds); a monster's seed chains from MonAttackStats to the attack event it opens. A pair is chained
when the second event's entry seed equals the first's predicted exit; otherwise the second event is resynchronised
(its entry taken as logged) and the step distance found within 4096 steps is reported.
RGN lines (the windowed stat-74 tick) are checked against the open-wounds and poison states (STA): during the state,
each tick adds stat 74 to stat 6, capped at stat 7, never below 256.
Exit 0 only if every check holds. Stdlib only. Read-only.
"""
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import drlg  # noqa: E402
from excel_bin import find_file, read_bin  # noqa: E402
from monstats import muldiv, tdiv, s32  # noqa: E402

DEFAULT_EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
MULT = 0x6AC690C5
M32 = 0xFFFFFFFF
HIRE = {271: 1, 338: 2, 359: 3, 560: 4, 561: 4}
FN_CB, FN_OW, FN_FRZ = 0x005BFFC0, 0x005BFE60, 0x005BFC60
# packet offsets (re/types/combat.h)
F_FLAGS, F_RES, F_PHYS, F_ED, F_FIRE, F_BURN, F_BLEN, F_LIGHT, F_MAGIC, F_COLD, F_POIS, F_PLEN, F_CLEN, F_FLEN, \
    F_LIFE, F_MANA, F_STAM, F_STUN, F_ABS, F_TOTAL, F_RATE = (0, 4, 8, 0xC, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24, 0x28,
                                                             0x2C, 0x30, 0x34, 0x38, 0x3C, 0x40, 0x44, 0x48, 0x4C, 0x54)
ELEM_ROWS = {1: "fire", 2: "light", 3: "cold", 4: "magic", 8: "poison"}


def sd_parse(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def sd_fmt(t):
    return "%08x:%08x" % t


def step(t):
    v = t[0] * MULT + t[1]
    return v & M32, (v >> 32) & M32


def rng_range(t, n):
    """RNG_Range / RNG_RangeB / the inlined low % n: (value, seed after). n < 1: no step, 0."""
    n = s32(n)
    if n < 1:
        return 0, t
    t = step(t)
    return t[0] % n, t


def steps_between(a, b, limit=4096):
    t = a
    for i in range(limit + 1):
        if t == b:
            return i
        t = step(t)
    return None


def sar7(v):
    """(v * src) / 128 as the code does it: cdq; and edx, 0x7F; add; sar 7 (toward zero)."""
    return tdiv(s32(v), 128)


class Tables:
    def __init__(self, excel=DEFAULT_EXCEL, exe=drlg.DEFAULT_EXE):
        def rb(name):
            return read_bin(find_file(excel, name, ".bin"))[0]
        self.ms = rb("monstats")
        self.dl = rb("difficultylevels")
        self.cs = rb("charstats")
        self.wp = rb("weapons")
        self.it = rb("itemtypes")
        self.mi = rb("missiles")
        rd = lambda a, n: drlg.exe_read(exe, a, n)  # noqa: E731
        self.hp_pct = list(struct.unpack("<9i", rd(0x006E1590, 36)))
        raw = struct.unpack("<132i", rd(0x00732980, 12 * 44))
        self.rows = []
        for i in range(12):
            r = raw[11 * i: 11 * i + 11]
            self.rows.append({"off": r[0], "res": r[1], "max": r[2], "pierce": r[3], "absp": r[4], "absf": r[5],
                              "slot": r[6], "mononly": r[7], "scaled": r[8]})
        self._blunt = {}

    def m8(self, cls, off):
        return self.ms[cls][off]

    def boss(self, cls):
        return bool(self.ms[cls][0x0C] & 0x40)

    def primeevil(self, cls):
        return bool(self.ms[cls][0x0C] & 0x80)

    def demon(self, cls):
        return bool(self.ms[cls][0x0D] & 0x20)

    def undead(self, cls):
        return bool(self.ms[cls][0x0D] & 0x18)

    def drain(self, cls, d):
        return self.ms[cls][0xA0 + d]

    def crit(self, cls):
        return self.ms[cls][0xA6]

    def coldeffect(self, cls, d):
        return struct.unpack_from("<b", self.ms[cls], 0x168 + d)[0]

    def el(self, cls, e, d):
        r = self.ms[cls]
        return {"mode": r[0xFE + e], "type": r[0x101 + e], "pct": r[0x104 + 3 * e + d]}

    def dl32(self, d, off):
        return struct.unpack_from("<i", self.dl[d], off)[0]

    def tohitfactor(self, cls):
        return struct.unpack_from("<i", self.cs[cls], 0x3C)[0]

    def blockfactor(self, cls):
        return self.cs[cls][0x49]

    def weapon(self, cls):
        if cls is None or not (0 <= cls < len(self.wp)):
            return None
        r = self.wp[cls]
        return {"sb": struct.unpack_from("<h", r, 0x106)[0], "db": struct.unpack_from("<h", r, 0x108)[0],
                "type": struct.unpack_from("<H", r, 0x11E)[0]}

    def missile_kb(self, mrec):
        return self.mi[mrec][0xAE] if 0 <= mrec < len(self.mi) else 0


class Mismatch(Exception):
    pass


class Ev:
    """One event: its lines, the two units and the predicted seeds."""

    def __init__(self, kind, head, lines):
        self.kind, self.head, self.lines = kind, head, lines
        self.deferred = False


def stat(u, sid, layer=None):
    st = u.get("st") or {}
    if layer is not None:
        return st.get("%d:%d" % (sid, layer), 0)
    return st.get(str(sid), 0)


def pk(hexs):
    b = bytes.fromhex(hexs)
    return list(struct.unpack("<28i", b)), b


def pget(p, off):
    return p[off // 4]


def pset(p, off, v):
    p[off // 4] = s32(v)


class Checker:
    def __init__(self, T, verbose=False):
        self.T, self.v = T, verbose
        self.stats = {}
        self.mism = []
        self.cnt = {}
        self.cases = {}
        self.player_seed = None          # (predicted exit, kind, log, line) of the last event on the player's seed
        self.mon_seed = {}               # unit pointer -> predicted exit after MonAttackStats
        self.chain = {}
        self.ow = {}                     # defender pointer -> list of [start frame, end frame, value]

    # --- bookkeeping ---------------------------------------------------------------------------------------------
    def inc(self, d, k, n=1):
        d[k] = d.get(k, 0) + n

    def case(self, k, n=1):
        self.inc(self.cases, k, n)

    def kc(self, kind, k, n=1):
        self.inc(self.cnt.setdefault(kind, {}), k, n)

    def fail(self, msg):
        raise Mismatch(msg)

    def eq(self, what, got, want):
        if got != want:
            self.fail("%s: logged %r, model %r" % (what, got, want))

    # --- chaining ------------------------------------------------------------------------------------------------
    def chain_in(self, role, kind, entry, prev):
        """prev = (predicted exit, previous kind) or None."""
        if prev is None:
            self.inc(self.chain, (role, "first-seen", kind))
            return
        if prev[0] == entry:
            self.inc(self.chain, (role, "pair", prev[1], kind))
        else:
            n = steps_between(prev[0], entry)
            self.inc(self.chain, (role, "resync", kind))
            self.inc(self.chain, (role, "resync-gap", "found" if n is not None else "far"))

    # --- the model pieces ----------------------------------------------------------------------------------------
    def get_defense(self, u):
        d = stat(u, 31) + tdiv(stat(u, 2), 4)
        p = stat(u, 171) + stat(u, 16)
        d = d + tdiv(s32(d * p), 100)
        if stat(u, 182):
            d += muldiv(d, stat(u, 182), 100)
        return d

    def tohit(self, ev, a, d, sa, g, lines, i, is_missile=0):
        """COMBAT_ToHitRoll: returns (hit, seed, index)."""
        T = self.T
        L = lines[i]
        thb = thv = None
        while L[0] in ("THB", "THV"):
            if L[0] == "THB":
                thb = L[1]
            else:
                thv = L[1]
            i += 1
            L = lines[i]
        if L[0] != "THR":
            self.fail("expected THR, got %s" % L[0])
        thr = L[1]
        arpct = ev.head.get("arPct", 0)
        defense = self.get_defense(d) + stat(d, 32 if is_missile else 33)
        if a["t"] == 0:
            base = (stat(a, 2) - 7) * 5 + stat(a, 19) + T.tohitfactor(a["c"])
            if thb is None:
                self.fail("no THB for a player attacker")
            self.eq("THB AR (PlayerBaseToHit)", thb["ar"], base)
            self.eq("THB DEF (UNIT_GetDefense + stat 33)", thb["def"], defense)
            self.case("tohitfactor class %d" % a["c"])
            mods = any(stat(a, s) for s in (115, 116, 123, 124))
            if not mods:
                self.eq("THV AR (no target mods)", thv["ar"], base)
                self.eq("THV DEF (no target mods)", thv["def"], defense)
            ar, df, pct = thv["ar"], thv["def"], thv["pct"]
            if a["c"] == 1 and not any(k.startswith("179:") for k in a.get("st", {})):
                self.eq("THV pct (no mastery: stat 119 + arPct)", pct, stat(a, 119) + arpct)
        else:
            ar = stat(a, 19) + arpct + 5 * stat(a, 2)
            self.eq("THV AR (monster)", thv["ar"], ar)
            self.eq("THV DEF", thv["def"], defense)
            self.eq("THV pct (monster: stat 119)", thv["pct"], stat(a, 119))
            df, pct = thv["def"], thv["pct"]
        self.eq("THV alvl", thv["al"], stat(a, 12))
        self.eq("THV dlvl", thv["dl"], stat(d, 12))
        alvl, dlvl = stat(a, 12), stat(d, 12)
        ar = s32(ar + muldiv(ar, pct, 100))
        if df < 0:
            ar, df = s32(ar - df), 0
        if ar < 0:
            df, ar = s32(df - ar), 0
        if df < 0:
            df = 0
        c = 100 if ar + df == 0 else tdiv(s32(100 * ar), s32(ar + df))
        c = tdiv(s32(c * alvl * 2), s32(alvl + dlvl))
        c = 5 if c <= 5 else (95 if c >= 95 else c)
        r, sa = rng_range(sa, 100)
        self.eq("THR c", thr["c"], c)
        self.eq("THR r", thr["r"], r)
        self.eq("THR attacker seed", thr["sa"], sd_fmt(sa))
        return r < c, sa, i + 1

    def block_formula(self, d, game_exp):
        """UnitBlockChance for a player, given that it holds a shield (else 0)."""
        b = stat(d, 20) + self.T.blockfactor(d["c"])
        if game_exp:
            lvl = max(stat(d, 12), 1)
            b = tdiv(s32((stat(d, 2) - 15) * b), 2 * lvl)
        return min(b, 75)

    def defence(self, d, sd, lines, i, is_missile, use_block, g):
        """COMBAT_DefenceRoll; returns (bits, seed, index). Bits: 1 block, 2 avoid, 4 dodge, 8 evade, 0x10 wblock."""
        def take(tag):
            nonlocal i
            if i < len(lines) and lines[i][0] == tag:
                x = lines[i][1]
                i += 1
                return x
            return None

        def roll(label, ch):
            nonlocal sd
            L = take("DRR")
            if L is None:
                self.fail("expected DRR %s" % label)
            r, sd = rng_range(sd, 100)
            self.eq("DRR label", L["lab"], label)
            self.eq("DRR %s chance" % label, L["ch"], ch)
            self.eq("DRR %s roll" % label, L["r"], r)
            self.eq("DRR %s seed" % label, L["s"], sd_fmt(sd))
            return r < ch

        if use_block:
            drb = take("DRB")
            if drb is None:
                if is_missile and i < len(lines) and lines[i][0] == "DRR" and lines[i][1]["lab"] == "block":
                    # logger r1 wrote no DRB/DRM inside missile events: the DRR chance is taken as the input
                    drb = {"b": lines[i][1]["ch"], "r1": True}
                    self.case("missile block chance from DRR (logger r1)")
                else:
                    self.fail("expected DRB")
            b = drb["b"]
            if d["t"] == 0 and not drb.get("r1"):
                want = self.block_formula(d, g["exp"])
                if b > 0 or want > 0:
                    self.eq("DRB block chance (player formula, shield held)", b, want)
                    self.case("player block chance checked (classic)" if not g["exp"] else
                              "player block chance checked (expansion)")
            if b > 0:
                if d["t"] == 1:
                    self.eq("DRB block chance (monster: stat 20)", b, min(stat(d, 20), 75))
                if d["t"] == 0 and not drb.get("r1"):
                    drm = take("DRM")
                    if drm is None:
                        self.fail("expected DRM")
                    if drm["mv"] and d["m"] != 2:
                        b = tdiv(b, 3)
                        self.case("block divided by 3 (moving player)")
                if roll("block", b):
                    self.case("block")
                    return 1, sd, i
        # COMBAT_AvoidRoll
        m = d["m"]
        evade_only = (d["t"] == 0 and m in (3, 2)) or (d["t"] != 0 and m in (15, 2))
        if evade_only:
            e = stat(d, 340)
            if e > 0 and roll("evade", e):
                self.case("evade")
                return 8, sd, i
            return 0, sd, i
        wbc = take("WBC")
        wb = wbc["wb"] if wbc else 0
        if wb > 0:
            wbs = take("WBS")
            if wbs and wbs["v"] == 13 and roll("wblock", wb):
                self.case("weapon block")
                return 0x10, sd, i
        ch = stat(d, 339 if is_missile else 338)
        if ch > 0 and roll("avoid" if is_missile else "dodge", ch):
            self.case("avoid" if is_missile else "dodge")
            return 2 if is_missile else 4, sd, i
        return 0, sd, i

    def roll_range(self, sa, field, mn, mx, pmin, pmax):
        """COMBAT_RollRange(max, field, pctMin; unit, min, pctMax)."""
        if mx <= 0:
            return max(field, 0), sa
        lo = mn + muldiv(mn, pmin, 100)
        hi = mx + muldiv(mx, pmax, 100)
        v = s32(field + lo)
        if hi > lo:
            r, sa = rng_range(sa, s32(hi - lo))
            v = s32(v + r)
        return max(v, 0), sa

    def roll_elem(self, a, sa, field, smin, smax, smast):
        mx = s32(stat(a, smax) << 8)
        if mx < 8:
            return max(field, 0), sa
        mn = s32(stat(a, smin) << 8)
        pm = stat(a, smast) if smast != -1 else 0
        return self.roll_range(sa, field, mn, mx, pm, pm)

    def build(self, ev, a, d, sa, lines, i, g):
        """COMBAT_BuildDamage from BD0 to BD1: returns (packet list, seed, index)."""
        T = self.T
        bd0 = lines[i][1]
        p, _ = pk(bd0["p"])
        self.eq("BD0 attacker seed", bd0["sa"], sd_fmt(sa))
        src = bd0["src"] or 128
        crit_flag = bd0["crit"]
        i += 1
        pset(p, F_FLAGS, p[0] | 0x20)
        hire = a["t"] == 1 and a["c"] in HIRE
        if (a["t"] == 0 or hire) and d["t"] == 1:
            ed0 = pget(p, F_ED)
            if T.demon(d["c"]) and stat(d, 0) is not None and stat(a, 121) > 0:
                ed0 += stat(a, 121)
            pset(p, F_ED, ed0)
            if stat(a, 120):
                self.fail("stat 120 (target AC reduction) not modelled")
            if any(k.startswith("180:") for k in a.get("st", {})):
                self.fail("stat 180 (damage against a monster type) not modelled")
        if not (p[0] & 1):
            # COMBAT_RollPhysical
            rpt = rpm = rpe = None
            while lines[i][0] in ("RPT", "RPM", "RPE"):
                t, x = lines[i]
                if t == "RPT":
                    rpt = x
                elif t == "RPM":
                    rpm = x
                else:
                    rpe = x
                i += 1
            if rpe is None:
                self.fail("no RPE")
            self.eq("RPE seed", rpe["sa"], sd_fmt(sa))
            w = rpe["w"]
            if w is not None:
                two = rpt is not None and rpt["v"] == 2
                mn, mx = (stat(a, 23), stat(a, 24)) if two else (stat(a, 21), stat(a, 22))
                mn, mx = s32(mn << 8), s32(mx << 8)
            else:
                mn, mx = stat(a, 21), stat(a, 22)
                mn = 1 if mn <= 0 else mn
                mx = 2 if mx <= 1 else mx
                mn, mx = s32(mn << 8), s32(mx << 8)
            add = s32(stat(a, 111) << 8)
            mx = s32(mx + add)
            mn = s32(mn + add)
            if mn < 1:
                mn = 256
            if mx <= mn:
                mx = mn + 256
            self.eq("RPE min", rpe["min"], mn)
            self.eq("RPE max", rpe["max"], mx)
            ed = pget(p, F_ED) + stat(a, 25)
            if w is not None:
                wr = T.weapon(w)
                if wr is None:
                    self.fail("weapon class %r not in weapons.bin" % w)
                if T.undead(d["c"]) if d["t"] == 1 else False:
                    pass
                if wr["sb"]:
                    ed += tdiv(s32(stat(a, 0) * wr["sb"]), 100)
                if wr["db"]:
                    ed += tdiv(s32(stat(a, 2) * wr["db"]), 100)
                if rpm is None:
                    self.fail("no RPM")
                ed += rpm["v"]
            else:
                ed += stat(a, 0)
            ed = max(ed, -90)
            self.eq("RPE ed", rpe["ed"], ed)
            self.eq("RPE stat 18", rpe["s18"], stat(a, 18))
            self.eq("RPE stat 17", rpe["s17"], stat(a, 17))
            lo = s32(mn + muldiv(mn, s32(stat(a, 18) + ed), 100))
            hi = s32(mx + muldiv(mx, s32(stat(a, 17) + ed), 100))
            v = s32(rpe["phys"] + lo)
            if hi > lo:
                r, sa = rng_range(sa, s32(hi - lo))
                v = s32(v + r)
            v = max(v, 0)
            if src != 128:
                v = muldiv(v, src, 128)
            pset(p, F_PHYS, v)
            # critical / deadly strike
            crit = False
            if lines[i][0] == "BDC":
                bdc = lines[i][1]
                i += 1
                self.eq("BDC seed", bdc["sa"], sd_fmt(sa))
                if bdc["v"] > 0:
                    r, sa = rng_range(sa, 100)
                    crit = r < bdc["v"]
            elif crit_flag == 0 and w is not None:
                self.fail("expected BDC")
            if not crit and stat(a, 337) > 0:
                r, sa = rng_range(sa, 100)
                crit = r < stat(a, 337)
            if not crit and stat(a, 141) > 0:
                r, sa = rng_range(sa, 100)
                crit = r < stat(a, 141)
                if crit:
                    self.case("deadly strike")
            if crit:
                pset(p, F_PHYS, pget(p, F_PHYS) * 2)
                pset(p, F_RES, pget(p, F_RES) | 0x2000)
                self.case("critical or deadly strike (x2)")
        for off, smin, smax, smast in ((F_FIRE, 48, 49, 329), (F_LIGHT, 50, 51, 330), (F_COLD, 54, 55, 331),
                                       (F_MAGIC, 52, 53, 357)):
            v, sa = self.roll_elem(a, sa, pget(p, off), smin, smax, smast)
            if src != 128:
                v = sar7(v * src)
            pset(p, off, v)
        if a["t"] == 1 and not hire:
            for off, flag, smin, smax in ((F_LIFE, 4, 60, 61), (F_MANA, 8, 62, 63), (F_STAM, 0x10, 64, 65)):
                if p[0] & flag:
                    continue
                v, sa = self.roll_elem(a, sa, pget(p, off), smin, smax, -1)
                pset(p, off, pget(p, off) + sar7(v * src))
        elif a["t"] == 0 or hire:
            if not p[0] & 4:
                pset(p, F_LIFE, pget(p, F_LIFE) + stat(a, 60))
            if not p[0] & 8:
                pset(p, F_MANA, pget(p, F_MANA) + stat(a, 62))
            for s, f in ((103, 0x100), (104, 0x200), (106, 0x400)):
                if stat(a, s):
                    p[0] |= f
        # poison
        s57, s58 = stat(a, 57), stat(a, 58)
        m = stat(a, 332) if s58 > 0 else 0
        v, sa = self.roll_range(sa, pget(p, F_POIS), s57, s58, m, m)
        v = sar7(v * src)
        pset(p, F_POIS, v)
        if v:
            if stat(a, 101) > 0:
                pset(p, F_PLEN, pget(p, F_PLEN) + stat(a, 101))
            else:
                pset(p, F_PLEN, pget(p, F_PLEN) + stat(a, 59))
                if stat(a, 326) > 1:
                    pset(p, F_PLEN, tdiv(pget(p, F_PLEN), stat(a, 326)))
        if pget(p, F_COLD) > 0:
            pset(p, F_CLEN, pget(p, F_CLEN) + sar7(stat(a, 56) * src))
        if pget(p, F_STUN) == 0:
            pset(p, F_STUN, pget(p, F_STUN) + sar7(stat(a, 66) * src))
        # burning: the unconditional RangeB(seed, 1)
        b = s32(pget(p, F_BURN) * src + 316)
        r, sa = rng_range(sa, 1)
        b = s32(b + r)
        pset(p, F_BURN, pget(p, F_BURN) + tdiv(max(b, 0), 128))
        if pget(p, F_BLEN) != 0:
            pset(p, F_BLEN, pget(p, F_BLEN) + sar7(stat(a, 315) * src))
        self.case("builder RangeB(1) steps")
        # event 3 (attackedinmelee) of the defender, for a player or hireling attacker
        while lines[i][0] == "EVH":
            sa, _, i = self.oracle_handler(lines, i, sa, None, a, d)
        conv = (pget(p, 0x64) >> 8) & 0xFF
        if conv:
            self.fail("conversion type %d not modelled" % conv)
        # sub_005A5560_MonCritDouble
        if a["t"] == 1 and T.crit(a["c"]):
            t = step(sa)
            sa = t
            if (t[0] % 100) & 0xFF < T.crit(a["c"]):
                for off in (F_PHYS, F_FIRE, F_LIGHT, F_MAGIC, F_COLD, F_POIS):
                    pset(p, off, pget(p, off) * 2)
                if not pget(p, 0x60) & 0xF0:
                    pset(p, 0x60, pget(p, 0x60) | 0x10)
                self.case("monster Crit doubling")
        L = lines[i]
        if L[0] != "BD1":
            self.fail("expected BD1, got %s" % L[0])
        got, _ = pk(L[1]["p"])
        self.eq("BD1 attacker seed", L[1]["sa"], sd_fmt(sa))
        self.eq_packet("BD1 packet", got, p)
        return p, sa, i + 1

    def eq_packet(self, what, got, want):
        if got != want:
            diff = ["+0x%02X: %d vs %d" % (4 * k, got[k], want[k]) for k in range(28) if got[k] != want[k]]
            self.fail("%s (logged vs model): %s" % (what, ", ".join(diff)))

    def oracle_handler(self, lines, i, s_unit_pred, s_other_pred, a, d):
        """An EVH .. EVR pair taken as a boundary oracle: assert the unit's entry seed, take the exits."""
        h = lines[i][1]
        self.kc("handlers", "oracle %08x e%d" % (h["fn"], h["e"]))
        j = i + 1
        depth = 1
        while j < len(lines):
            if lines[j][0] == "EVH":
                depth += 1
            elif lines[j][0] == "EVR":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= len(lines):
            self.fail("EVH without EVR")
        r = lines[j][1]
        return sd_parse(r["su"]), sd_parse(r["so"]) if r["so"] else None, j + 1

    def percent(self, a, d, g):
        """COMBAT_DamagePercent."""
        T = self.T
        if not a or not d or a["u"] == d["u"]:
            return 100
        ha = a["t"] == 1 and a["c"] in HIRE
        hd = d["t"] == 1 and d["c"] in HIRE
        if d["t"] == 0:
            if a["t"] == 0 or ha:
                return 17
            if "c4" not in a:
                return None
            return 17 if a["c4"] & 0x80000000 else 100
        if hd and ha:
            return 25
        if ha and d["t"] == 1 and T.boss(d["c"]):
            return T.dl32(g["diff"], 0x38)
        if a["t"] == 1 and T.primeevil(a["c"]):
            if "c4" not in d:
                return None           # logger before r3: the defender's +0xC4 bit 31 was not logged
            if d["c4"] & 0x80000000:
                return 200 if hd else 400
        return 100

    def resist_for(self, row, a, d, g, def_mon):
        T = self.T
        r = stat(d, row["res"]) if row["res"] != -1 else 0
        if row["pierce"] != -1 and (r < 100 or not def_mon):
            pv = stat(a, row["pierce"]) if a else 0
            if pv:
                r = s32(r - pv)
        pen = 0
        if not def_mon and row["res"] not in (36, 37):
            if not g["exp"]:
                pen = {1: -20, 2: -50}.get(g["diff"], 0)
            else:
                pen = T.dl32(g["diff"], 0)
            r = s32(r + pen)
        if r <= 0:
            return (-100 if r <= -100 else r), None
        if def_mon:
            return r, None
        if row["max"] != -1:
            cap = min(75 + stat(d, row["max"]), 95)
        else:
            cap = 50 if row["res"] == 36 else 75
        if max(r, -100) >= cap:
            return cap, cap
        return r, cap

    def reduce(self, a, d, p, g, bypass, red, absorb_log):
        T = self.T
        a_mon = a is not None and a["t"] == 1 and a["c"] not in HIRE
        d_mon = d["t"] == 1 and d["c"] not in HIRE
        for k, row in enumerate(T.rows):
            if row["mononly"] and not a_mon:
                break
            v = pget(p, row["off"])
            if v <= 0:
                pset(p, row["off"], 0)
                continue
            r, cap = self.resist_for(row, a, d, g, d_mon)
            name = ELEM_ROWS.get(k)
            if name:
                self.case("resist application %s" % name)
                if d_mon and r >= 100:
                    self.case("resist application %s immune" % name)
                if cap is not None and r >= cap:
                    self.case("resist application %s at cap" % name)
            if k == 0:
                self.case("resist application physical")
            if bypass:
                dd = v
                if r > 0:
                    r = 0
            else:
                dd = s32(v - red[row["slot"]])
                if red[row["slot"]] > 0:
                    self.case("flat reduction (DR or MDR) non-zero")
            if dd > 0 and r != 0:
                r = min(r, 100)
                dd = muldiv(dd, 100 - r, 100)
            if not bypass and row["absp"] != -1:
                pa = stat(d, row["absp"])
                if pa >= 40:
                    pa = 40
                if pa > 0:
                    x = muldiv(dd, pa, 100)
                    pset(p, F_ABS, pget(p, F_ABS) + x)
                    dd = s32(dd - x)
                    absorb_log.append(("pct", k, x))
                f = s32(stat(d, row["absf"]) << 8)
                if f > 0:
                    x = dd if f >= dd else f
                    pset(p, F_ABS, pget(p, F_ABS) + x)
                    dd = s32(dd - x)
                    absorb_log.append(("flat", k, x))
            pset(p, row["off"], dd)

    def reductions(self, a, d, p, g, lines, i):
        """COMBAT_ApplyReductions from RD0 to RD1."""
        T = self.T
        rd0 = lines[i][1]
        got0, _ = pk(rd0["p"])
        self.eq_packet("RD0 packet", got0, p)
        i += 1
        dr = s32(stat(d, 34) << 8)
        if dr > 0 and pget(p, F_RATE) > 0:
            dr = muldiv(dr, pget(p, F_RATE), 1024)
        mdr = s32(stat(d, 35) << 8)
        if mdr > 0 and pget(p, F_RATE) > 0:
            mdr = muldiv(mdr, pget(p, F_RATE), 1024)
        P = self.percent(a, d, g)
        if lines[i][0] != "RDP":
            self.fail("expected RDP")
        if P is None:
            P = lines[i][1]["P"]
            if P not in (100, 17, 200, 400):
                self.fail("RDP percent P %d outside the unlogged-bit branch values" % P)
            self.case("percent P with the +0xC4 bit unlogged (logger r2), taken: %d" % P)
        self.eq("RDP percent P", lines[i][1]["P"], P)
        if P in (200, 400):
            self.case("prime evil percent %d" % P)
        if a and a["t"] == 1 and a["c"] in HIRE and d["t"] == 1 and T.boss(d["c"]):
            self.case("hireling boss percent diff %d P %d" % (g["diff"], P))
        i += 1
        if P != 100:
            for row in T.rows:
                if row["scaled"] and pget(p, row["off"]) > 0:
                    pset(p, row["off"], muldiv(pget(p, row["off"]), P, 100))
        if lines[i][0] == "EVH":
            self.fail("event 11 (absorbdamage) handler ran: not modelled")
        # COMBAT_LengthImmunities
        if pget(p, F_CLEN) > 0 or pget(p, F_FLEN) > 0:
            if stat(d, 153):
                pset(p, F_CLEN, 0)
                pset(p, F_FLEN, 0)
            elif stat(d, 118):
                pset(p, F_CLEN, tdiv(pget(p, F_CLEN), 2))
                pset(p, F_FLEN, tdiv(pget(p, F_FLEN), 2))
        flags = p[0]
        if d["t"] == 1:
            und, dem = T.undead(d["c"]), T.demon(d["c"])
            bypass = (und and flags & 0x100) or (dem and flags & 0x200) or (not und and not dem and flags & 0x400)
        else:
            bypass = bool(flags & 0x400)
        absorb_log = []
        self.reduce(a, d, p, g, bool(bypass), [0, dr, mdr], absorb_log)
        a_mon = a is not None and a["t"] == 1 and a["c"] not in HIRE
        tot = sum(pget(p, o) for o in (F_PHYS, F_FIRE, F_LIGHT, F_MAGIC, F_COLD, F_POIS))
        if a_mon:
            tot += pget(p, F_LIFE)
        pset(p, F_TOTAL, tot)
        if lines[i][0] != "RD1":
            self.fail("expected RD1, got %s" % lines[i][0])
        got, _ = pk(lines[i][1]["p"])
        self.eq_packet("RD1 packet", got, p)
        if any(x for kind, _, x in absorb_log if kind == "pct" and x > 0) and d["t"] == 0:
            self.case("percent absorb on the player (heal amount > 0)")
        if stat(d, 34) or stat(d, 35) or any(x for _, _, x in absorb_log):
            self.case("events with DR, MDR or absorb non-zero")
        if not g["exp"] and g["diff"] and d["t"] == 0:
            self.case("classic resist penalty on the player diff %d" % g["diff"])
        return i + 1

    def crushing(self, h, r_line, a, d, sa, e):
        T = self.T
        c = stat(a, 136)
        hp = h["lo"][0]
        if c <= 0:
            self.eq("CB life (no chance)", r_line["lo"][0], hp)
            return sa
        r, sa = rng_range(sa, 100)
        if r >= c:
            self.eq("CB life (no hit)", r_line["lo"][0], hp)
            return sa
        if d["t"] == 0:
            k = 10
        elif d["c"] in HIRE:
            k = 10
        else:
            k = 8 if (T.boss(d["c"]) or (d.get("f", 0) & 2)) else 4
            n = max(stat(d, 100), 1)
            pct = T.hp_pct[n] if n < 9 else (n - 2) * 50
            if pct:
                k += muldiv(k, pct, 100)
            self.case("crushing blow players %d" % n)
        if e == 6:
            k *= 2
        cb = tdiv(hp, k)
        r36 = stat(d, 36)
        if r36 >= 100:
            r36 = 100
        if r36 > 0:
            cb = s32(cb - muldiv(cb, r36, 100))
        new = max(hp - cb, 0)
        self.eq("CB life after", r_line["lo"][0], new)
        f = d.get("f", 0) or 0
        who = "act boss" if d["t"] == 1 and T.boss(d["c"]) else ("superunique" if f & 2 else ("unique" if f & 8 else (
            "champion" if f & 4 else ("player" if d["t"] == 0 else "normal"))))
        self.case("crushing blow on %s" % who)
        return sa

    def openwounds(self, h, r_line, a, d, sa, e, sta, fr):
        c = stat(a, 135)
        if c <= 0:
            return sa, False
        r, sa = rng_range(sa, 100)
        if r >= c:
            return sa, False
        L = max(stat(a, 12), 1)
        t = (9, 18, 27, 36, 45)
        if L <= 1:
            band = 0
        elif L <= 15:
            band = (L - 1) * t[0]
        elif L <= 30:
            band = 14 * t[0] + (L - 15) * t[1]
        elif L <= 45:
            band = 14 * t[0] + 15 * t[1] + (L - 30) * t[2]
        elif L <= 60:
            band = 14 * t[0] + 15 * (t[1] + t[2]) + (L - 45) * t[3]
        else:
            band = 14 * t[0] + 15 * (t[1] + t[2] + t[3]) + (L - 60) * t[4]
        dmg = band + 40
        if d["t"] == 0:
            dmg = tdiv(dmg, 4)
            if e == 6:
                dmg = tdiv(dmg, 2)
        elif d["t"] == 1 and (d.get("f", 0) or 0) & 0xC:
            dmg = tdiv(dmg, 2)
        if sta is None:
            self.fail("open wounds hit without STA")
        self.eq("OW state", sta["state"], 62)
        self.eq("OW length", sta["len"], 200)
        self.eq("OW stat", sta["stat"], 74)
        self.eq("OW value", sta["val"], -dmg)
        self.ow.setdefault(d["u"], []).append([fr, fr + 200, -dmg])
        self.case("open wounds applied")
        if d["t"] == 1 and self.T.boss(d["c"]):
            self.case("open wounds on act boss")
        return sa, True

    def apply(self, ev, a, d, p, sa, sd, lines, i, g, missile):
        """COMBAT_ApplyDamage from AD0 to AD1."""
        T = self.T
        ad0 = lines[i][1]
        got, _ = pk(ad0["p"])
        fr = ad0["fr"]
        if not missile and fr != ev.head["g"]["frame"]:
            # the do-function queued the hit and COMBAT_DeliverQueued ran on a later frame: the AI drew on both seeds
            # in between and a skill may have changed the queued packet, so AD0 is a resynchronisation point
            self.case("deferred delivery (resynchronised at AD0)")
            if got != p:
                self.case("queued packet changed before the delivery (skill input)")
            p[:] = got
            sa, sd = sd_parse(ad0["sa"]), sd_parse(ad0["sd"])
            ev.deferred = True
        self.eq_packet("AD0 packet", got, p)
        self.eq("AD0 attacker seed", ad0["sa"], sd_fmt(sa))
        self.eq("AD0 defender seed", ad0["sd"], sd_fmt(sd))
        la, ld = list(ad0["la"]), list(ad0["ld"])
        i += 1
        if d["m"] in (0, 12) or not ld[0]:
            # dead defender: COMBAT_ApplyDamage returns before the events (0x0057C77D)
            if lines[i][0] != "AD1":
                self.fail("dead defender: expected AD1, got %s" % lines[i][0])
            x = lines[i][1]
            self.eq("AD1 attacker seed (dead defender)", x["sa"], sd_fmt(sa))
            self.eq("AD1 defender seed (dead defender)", x["sd"], sd_fmt(sd))
            self.eq("AD1 life (dead defender)", x["ld"][0], ld[0])
            self.case("hit on a dead defender (no effect)")
            return sa, sd, i + 1, pget(p, F_RES)
        if missile:
            if lines[i][0] != "RD0":
                self.fail("missile AD0 without RD0")
            i = self.reductions(a, d, p, g, lines, i)
        res = pget(p, F_RES) & 0xFFFF
        # events 5/1 (melee) or 6/2 (missile)
        while lines[i][0] == "EVH":
            h = lines[i][1]
            j = i + 1
            sta = None
            if j < len(lines) and lines[j][0] == "STA":
                sta = lines[j][1]
                j += 1
            if lines[j][0] != "EVR":
                if h["fn"] in (FN_CB, FN_OW):
                    self.fail("handler %08x: nested lines not modelled" % h["fn"])
                sa_u, so_u, i = self.oracle_handler(lines, i, None, None, a, d)
                if h["u"] == a["u"]:
                    self.eq("handler entry attacker seed", h["su"], sd_fmt(sa))
                    sa = sa_u
                    if so_u:
                        sd = so_u
                else:
                    self.eq("handler entry defender seed", h["su"], sd_fmt(sd))
                    sd = sa_u
                    if so_u:
                        sa = so_u
                ld[0] = lines[i - 1][1]["lo"][0] if h["u"] == a["u"] else lines[i - 1][1]["lu"][0]
                continue
            r_line = lines[j][1]
            if h["u"] == a["u"] and h["fn"] == FN_CB:
                self.eq("CB entry seed", h["su"], sd_fmt(sa))
                sa = self.crushing(h, r_line, a, d, sa, h["e"])
                self.eq("CB exit seed", r_line["su"], sd_fmt(sa))
                ld[0] = r_line["lo"][0]
                if ld[0] <= 0:
                    res |= 2
            elif h["u"] == a["u"] and h["fn"] == FN_OW:
                self.eq("OW entry seed", h["su"], sd_fmt(sa))
                sa, hit = self.openwounds(h, r_line, a, d, sa, h["e"], sta, fr)
                if not hit and sta is not None:
                    self.fail("STA without an open-wounds hit")
                self.eq("OW exit seed", r_line["su"], sd_fmt(sa))
            else:
                self.kc("handlers", "oracle %08x e%d" % (h["fn"], h["e"]))
                if h["u"] == a["u"]:
                    self.eq("handler entry attacker seed", h["su"], sd_fmt(sa))
                    sa = sd_parse(r_line["su"])
                    if r_line["so"]:
                        sd = sd_parse(r_line["so"])
                    ld[0] = r_line["lo"][0]
                else:
                    self.eq("handler entry defender seed", h["su"], sd_fmt(sd))
                    sd = sd_parse(r_line["su"])
                    if r_line["so"]:
                        sa = sd_parse(r_line["so"])
                    ld[0] = r_line["lu"][0]
            i = j + 1
        # phys capped at life, leech
        hp = ld[0]
        if pget(p, F_PHYS) >= hp:
            pset(p, F_PHYS, hp)
        sa, la = self.leech(a, d, p, sa, la, g, lines, i)
        if lines[i][0] == "LE1":
            i += 1
        # absorbed life to the defender, then the life change
        if pget(p, F_ABS):
            mx = ld[1]
            ld[0] = min(ld[0] + pget(p, F_ABS), mx) if ld[0] + pget(p, F_ABS) > ld[0] else ld[0] + pget(p, F_ABS)
            if d["t"] == 0 and pget(p, F_ABS) > 0:
                self.case("absorb heal on the player")
        tot = pget(p, F_TOTAL)
        if tot > 0:
            v = ld[0] - tot
            ld[0] = 0 if v < 256 else v
        # stun, cold, freeze, poison, burn
        if pget(p, F_STUN) > 0 and d["t"] == 1 and (d.get("f", 0) or 0) & 8:
            _, sa = rng_range(sa, 100)          # COMBAT_ApplyStun on a unique: one draw on the attacker's seed
            self.case("stun roll on a unique")
        if pget(p, F_CLEN) > 0:
            ce = T.coldeffect(d["c"], g["diff"]) if d["t"] == 1 else -50
            if ce != 0:
                _, sd = rng_range(sd, 100)
        if pget(p, F_FLEN) > 0:
            self.fail("freeze length > 0 not modelled")
        L = lines[i]
        if L[0] == "STA":           # poison or burn state
            i += 1
            L = lines[i]
        if L[0] != "AD1":
            self.fail("expected AD1, got %s" % L[0])
        x = L[1]
        self.eq("AD1 attacker seed", x["sa"], sd_fmt(sa))
        self.eq("AD1 defender seed", x["sd"], sd_fmt(sd))
        self.eq("AD1 defender life", x["ld"][0], ld[0])
        return sa, sd, i + 1, res

    def leech(self, a, d, p, sa, la, g, lines, i):
        T = self.T
        life, mana = pget(p, F_LIFE), pget(p, F_MANA)
        if life == 0 and mana == 0:
            return sa, la
        if d["t"] != 1:
            D = 100
        else:
            D = T.drain(d["c"], g["diff"])
            if D <= 0:
                return sa, la
        life, mana = s32(life << 6), s32(mana << 6)
        if a["t"] == 0:
            ls, ms = T.dl32(g["diff"], 0x28), T.dl32(g["diff"], 0x2C)
            if ls:
                life = tdiv(life, ls)
            if ms:
                mana = tdiv(mana, ms)
        pset(p, F_LIFE, life)
        pset(p, F_MANA, mana)
        hire = a["t"] == 1 and a["c"] in HIRE
        if a["t"] == 0 or hire:
            phys = pget(p, F_PHYS)
            if phys <= 0:
                return sa, la
            did_mana = False
            if mana:
                m = muldiv(phys, mana, 100)
                if D != 100:
                    m = muldiv(m, D, 100)
                m = tdiv(m, 64)
                la[2] = min(la[2] + m, la[3]) if m > 0 else la[2] + m
                did_mana = True
            if life:
                lv = muldiv(phys, life, 100)
                if D != 100:
                    lv = muldiv(lv, D, 100)
                lv = tdiv(lv, 64)
                la[0] = min(la[0] + lv, la[1]) if lv > 0 else la[0] + lv
                if did_mana:
                    _, sa = rng_range(sa, 2)
                    self.case("leech overlay Range(2)")
            self.case("leech diff %d" % g["diff"])
        else:
            self.case("monster drain diff %d" % g["diff"])
        if lines[i][0] == "LE1":
            x = lines[i][1]
            self.eq("LE1 attacker seed", x["sa"], sd_fmt(sa))
            self.eq("LE1 steal fields", x["st"][:2], [pget(p, F_LIFE), pget(p, F_MANA)])
            if a["t"] == 0 or hire:
                self.eq("LE1 attacker life", x["la"][0], la[0])
                self.eq("LE1 attacker mana", x["la"][2], la[2])
            la = list(x["la"])
        return sa, la

    def extras(self, sa, sd, lines, i):
        """DU0/DU1, events 7 and 3, KB0/KB1, GH0/GH1 as boundary oracles."""
        while i < len(lines) and lines[i][0] in ("DU0", "KB0", "GH0", "EVH", "DU1", "KB1", "GH1", "MAS0", "MAS1"):
            t, x = lines[i]
            if t in ("MAS0", "MAS1"):
                i += 1
                continue
            if t in ("DU0", "KB0", "GH0"):
                self.eq("%s attacker seed" % t, x["sa"] if "sa" in x else x.get("so"), sd_fmt(sa))
                self.eq("%s defender seed" % t, x["sd"], sd_fmt(sd))
                self.kc("oracles", t[:2])
                i += 1
            elif t in ("DU1", "KB1", "GH1"):
                sa = sd_parse(x["sa"] if "sa" in x else x["so"])
                sd = sd_parse(x["sd"])
                i += 1
            else:
                h = x
                su, so, i = self.oracle_handler(lines, i, None, None, None, None)
                if h["su"] == sd_fmt(sa) and h["so"] == sd_fmt(sd):
                    sa, sd = su, so
                elif h["su"] == sd_fmt(sd) and h["so"] == sd_fmt(sa):
                    sd, sa = su, so
                else:
                    self.fail("handler entry seeds %s/%s, model %s/%s" % (h["su"], h["so"], sd_fmt(sa), sd_fmt(sd)))
        return sa, sd, i

    # --- event kinds ---------------------------------------------------------------------------------------------
    def melee(self, ev):
        head, lines = ev.head, ev.lines
        a, d, g = head["a"], head["d"], head["g"]
        sa, sd = sd_parse(a["s"]), sd_parse(d["s"])
        i = 0
        res = 0
        auto = d["t"] == 0 and d["m"] == 3
        hit = False
        if lines[i][0] in ("THB", "THV", "THR"):
            hit, sa, i = self.tohit(ev, a, d, sa, g, lines, i)
            res = 1 if hit else 0
        elif auto:
            res, hit = 1, True
            self.case("running player hit without a roll")
        if hit:
            bits, sd, i = self.defence(d, sd, lines, i, 0, 1, g)
            if bits & 2:
                res |= 0x100
            if bits & 4:
                res |= 0x80
            if bits & 0x10:
                res |= 0x8000
            if bits & 1:
                res |= 0x10
            if bits:
                res &= ~1
        if res & 0x10:
            res &= ~1
        self.kc(ev.kind, "diff%d" % g["diff"])
        self.kc(ev.kind, "hit" if res & 1 else "miss")
        if ev.kind == "pa":
            self.kc(ev.kind, "class%d" % a["c"])
        if a["t"] == 1 and (a.get("f", 0) or 0) & 0x0E:
            self.case("champion or unique attack")
        if not g["exp"]:
            self.case("classic event diff %d" % g["diff"])
        p = None
        if i < len(lines) and lines[i][0] == "BD0":
            if not (res & 1):
                self.case("builder ran on a miss")
            p, sa, i = self.build(ev, a, d, sa, lines, i, g)
        if i < len(lines) and lines[i][0] == "RD0":
            if p is None:
                p, _ = pk(lines[i][1]["p"])
                self.case("packet input (no builder)")
            pset(p, F_RES, (pget(p, F_RES) & ~0xFFFF) | (pget(p, F_RES) & 0xFFFF))
            i = self.reductions(a, d, p, g, lines, i)
            tot = sum(pget(p, o) for o in (F_PHYS, F_FIRE, F_LIGHT, F_MAGIC, F_COLD, F_POIS))
            if a["t"] == 1:
                tot += pget(p, F_LIFE)
            if (tot & ~0xFF) > (stat(d, 6) & ~0xFF):
                p[1] |= 2
        if i < len(lines) and lines[i][0] == "AD0":
            if p is None:
                self.fail("AD0 without a packet")
            p[0] = 0x20
            sa, sd, i, _ = self.apply(ev, a, d, p, sa, sd, lines, i, g, False)
        sa, sd, i = self.extras(sa, sd, lines, i)
        while i < len(lines) and lines[i][0] in ("MAS0", "MAS1"):
            i += 1
        if i >= len(lines) or lines[i][0] != "EVX":
            self.fail("expected EVX, got %s" % (lines[i][0] if i < len(lines) else "end"))
        x = lines[i][1]
        if x["fr"] != g["frame"] and not ev.deferred:
            # queued on one frame, removed on a later one without a delivery (out of range, or a miss): the AI drew on
            # both seeds in between, so the exit is a resynchronisation, not an assertion
            self.case("deferred delivery without AD0 (exit resynchronised)")
            return sd_parse(x["sa"]), sd_parse(x["sd"])
        self.eq("EVX attacker seed", x["sa"], sd_fmt(sa))
        self.eq("EVX defender seed", x["sd"], sd_fmt(sd))
        return sa, sd

    def missile(self, ev):
        T = self.T
        head, lines = ev.head, ev.lines
        o, d, g = head["o"], head["d"], head["g"]
        so, sd = sd_parse(head["so"]), sd_parse(head["sd"])
        sm = sd_parse(head["sm"])
        p, _ = pk(head["p"])
        i = 0
        if T.missile_kb(head["mrec"]) > 0:
            _, sm = rng_range(sm, 100)
        bits, sd, i = self.defence(d, sd, lines, i, 1, 1 if pget(p, F_PHYS) != 0 else 0, g)
        self.kc(ev.kind, "diff%d" % g["diff"])
        if o["t"] == 1 and T.crit(o["c"]):
            so = step(so)
        if i < len(lines) and lines[i][0] == "AD0":
            p = pk(lines[i][1]["p"])[0]
            so, sd, i, _ = self.apply(ev, o, d, p, so, sd, lines, i, g, True)
        sa, sd, i = self.extras(so, sd, lines, i)
        while i < len(lines) and lines[i][0] in ("MAS0", "MAS1"):
            i += 1
        if i >= len(lines) or lines[i][0] != "MSX":
            self.fail("expected MSX, got %s" % (lines[i][0] if i < len(lines) else "end"))
        x = lines[i][1]
        self.eq("MSX owner seed", x["so"], sd_fmt(sa))
        self.eq("MSX defender seed", x["sd"], sd_fmt(sd))
        self.eq("MSX missile seed", x["sm"], sd_fmt(sm))
        return sa, sd

    def mas(self, ev):
        T = self.T
        u, mode, g = ev.head["u"], ev.head["mode"], ev.head["g"] or {"diff": 0}
        s = sd_parse(u["s"])
        d = g["diff"]
        n = 0
        for e in range(3):
            el = T.el(u["c"], e, d)
            if not el["mode"] or el["mode"] != mode or not el["pct"]:
                continue
            if el["pct"] < 100:
                r, s = rng_range(s, 100)
                if r >= el["pct"]:
                    continue
            n += 1
            if el["type"] == 10:
                _, s = rng_range(s, 5)
        if n:
            self.case("MonAttackStats El applied")
        x = ev.lines[-1]
        if x[0] != "MAS1":
            self.fail("expected MAS1")
        self.eq("MAS1 seed", x[1]["s"], sd_fmt(s))
        return s

    # --- driver --------------------------------------------------------------------------------------------------
    def run(self, path):
        lines = []
        with open(path, errors="replace") as fh:
            for no, ln in enumerate(fh, 1):
                tag, _, rest = ln.partition(" ")
                if tag in TAGS:
                    try:
                        lines.append((tag, json.loads(rest), no))
                    except ValueError:
                        self.inc(self.stats, "bad json")
        evs = []
        k = 0
        n = len(lines)
        while k < n:
            tag = lines[k][0]
            if tag in ("EV0", "MS0"):
                end = "EVX" if tag == "EV0" else "MSX"
                j = k + 1
                body = []
                ok = False
                while j < n:
                    t = lines[j][0]
                    if t == end:
                        body.append(lines[j][:2])
                        ok = True
                        break
                    if t in ("EV0", "MS0"):
                        break
                    if t not in ("RGN",):
                        body.append(lines[j][:2])
                    j += 1
                head = lines[k][1]
                # MonAttackStats calls inside the event (other monsters changing mode) are events of their own
                inner, rest_ = [], []
                q = 0
                while q < len(body):
                    if body[q][0] == "MAS0" and q + 1 < len(body) and body[q + 1][0] == "MAS1":
                        inner.append(("mas", body[q][1], [body[q + 1]], True, lines[k][2]))
                        q += 2
                        continue
                    if body[q][0] not in ("MAS0", "MAS1"):
                        rest_.append(body[q])
                    q += 1
                rest_ = self.own_lines(head, rest_)
                evs.append((head["k"], head, rest_, ok, lines[k][2]))
                evs.extend(inner)
                k = j + 1 if ok else j
                continue
            if tag == "MAS0":
                j = k + 1
                while j < n and lines[j][0] != "MAS1" and j < k + 4:
                    j += 1
                if j < n and lines[j][0] == "MAS1":
                    evs.append(("mas", lines[k][1], [lines[j][:2]], True, lines[k][2]))
                    k = j + 1
                    continue
            if tag == "RGN":
                evs.append(("rgn", lines[k][1], [], True, lines[k][2]))
            k += 1
        for kind, head, body, ok, no in evs:
            if kind == "rgn":
                self.tick(head)
                continue
            self.kc(kind, "events")
            if not ok:
                # no exit line (a deferred delivery overtaken by the next event): checked up to the last line logged
                body = body + [("END", {"lab": "END", "fr": -1})] * 4
                if kind == "mas":
                    self.kc(kind, "dropped: no exit line")
                    continue
            if any(t == "PRG" for t, _ in body):
                self.kc(kind, "dropped: progressive-charge hook (PRG)")
                continue
            ev = Ev(kind, head, body)
            try:
                if kind == "mas":
                    s = self.mas(ev)
                    self.mon_seed[head["u"]["u"]] = (s, "mas")
                    self.kc(kind, "checked")
                    continue
                if kind in ("md", "pm"):
                    ent_o, ent_d = sd_parse(head["so"]), sd_parse(head["sd"])
                    o, d = head["o"], head["d"]
                    sa, sd = self.missile(ev)
                    a = o
                else:
                    a, d = head["a"], head["d"]
                    ent_o, ent_d = sd_parse(a["s"]), sd_parse(d["s"])
                    sa, sd = self.melee(ev)
                self.kc(kind, "checked")
                for u in (a, d):
                    self.stats.setdefault("rgn_prev", {}).pop(u["u"], None)
                # chaining on the player's seed and the monster's seed
                if a["t"] == 0 or d["t"] == 0:
                    pe = ent_o if a["t"] == 0 else ent_d
                    self.chain_in("player", kind, pe, self.player_seed)
                    self.player_seed = (sa if a["t"] == 0 else sd, kind)
                if a["t"] == 1 and kind in ("ma", "ha"):
                    prev = self.mon_seed.pop(a["u"], None)
                    if prev is not None:
                        self.chain_in("monster", kind, ent_o, prev)
            except Mismatch as e:
                if not ok and "END" in str(e):
                    self.kc(kind, "checked up to its last line (no exit line)")
                    if a_is_player(head):
                        self.player_seed = None
                    continue
                self.kc(kind, "mismatch")
                self.mism.append("%s:%d %s %s" % (os.path.basename(path), no, kind, e))
                if a_is_player(head):
                    self.player_seed = None
            except (KeyError, IndexError, TypeError) as e:
                self.kc(kind, "mismatch")
                self.mism.append("%s:%d %s malformed event (%r)" % (os.path.basename(path), no, kind, e))
                self.player_seed = None

    def own_lines(self, head, body):
        """Drop the handler and state lines of other units: an event whose delivery is deferred spans frames, and
        the logger then also writes the dispatches and timed states of units outside the attack."""
        units = {(head.get(k) or {}).get("u") for k in ("a", "d", "o")} - {None}
        out, stack = [], []
        for t, x in body:
            if t == "EVH":
                keep = x["u"] in units or x["o"] in units
                stack.append(keep)
                if keep:
                    out.append((t, x))
                else:
                    self.inc(self.stats, "foreign handler lines dropped")
                continue
            if t == "EVR":
                if (stack.pop() if stack else True):
                    out.append((t, x))
                continue
            if t == "STA" and x["a"] not in units and x["d"] not in units:
                self.inc(self.stats, "foreign STA lines dropped")
                continue
            out.append((t, x))
        return out

    def tick(self, x):
        """One stat-74 tick (RGN): the value it will add is stat 74; check the previous tick's write."""
        u = x["u"]
        prev = self.stats.setdefault("rgn_prev", {}).get(u)
        if prev is not None and x["fr"] == prev["fr"] + 1:
            want = prev["hp"] + prev["rg"]
            if want > prev["mx"]:
                want = prev["mx"]
            if want < 256:
                want = 256
            self.case("stat-74 ticks checked")
            if x["hp"] != want and prev["rg"] != 0:
                self.mism.append("RGN unit %d frame %d: life %d, model %d" % (u, x["fr"], x["hp"], want))
        for w in self.ow.get(u, []):
            if w[0] - 1 <= x["fr"] <= w[1] + 10:
                w.append((x["fr"], x["rg"]))
                if w[0] <= x["fr"] < w[1]:
                    self.case("open-wounds window ticks logged")
        self.stats["rgn_prev"][u] = x

    def ow_durations(self):
        """For each open-wounds application whose window ticks were logged across its end: the first tick frame at
        which stat 74 rises by the bleed (the state's stat list gone), minus the application frame."""
        out = {}
        for u, ws in self.ow.items():
            for w in ws:
                ticks = dict(w[3:])
                dmg = -w[2]
                ends = [f for f in sorted(ticks) if f - 1 in ticks and ticks[f] - ticks[f - 1] == dmg and f > w[0]]
                if ends:
                    self.inc(out, "bleed ends at application frame + %d" % (ends[0] - w[0]))
        return out


def a_is_player(head):
    a = head.get("a") or head.get("o") or {}
    d = head.get("d") or {}
    return a.get("t") == 0 or d.get("t") == 0


TAGS = {"EV0", "THB", "THV", "THR", "DRB", "DRM", "DRR", "WBC", "WBS", "BD0", "RPT", "RPM", "RPE", "BDC", "BD1", "RD0",
        "RDP", "RD1", "AD0", "AD1", "EVH", "EVR", "LE1", "STA", "DU0", "DU1", "KB0", "KB1", "GH0", "GH1", "PRG", "EVX",
        "MS0", "MSX", "MAS0", "MAS1", "RGN", "CAP"}


def report(C, out=None):
    ok = not C.mism
    for m in C.mism[:60]:
        print("MISMATCH " + m)
    if len(C.mism) > 60:
        print("... %d more mismatches" % (len(C.mism) - 60))
    print("events per kind:")
    for kind in sorted(C.cnt):
        print("  %-9s %s" % (kind, json.dumps(C.cnt[kind], sort_keys=True)))
    print("chaining:")
    for k in sorted(C.chain, key=str):
        print("  %s: %d" % (" ".join(str(x) for x in k), C.chain[k]))
    for k, v in sorted(C.ow_durations().items()):
        print("open-wounds duration: %s: %d" % (k, v))
    print("cases:")
    for k in sorted(C.cases):
        print("  %s: %d" % (k, C.cases[k]))
    print("SUMMARY mismatches=%d events=%d" % (len(C.mism), sum(v.get("events", 0) for k, v in C.cnt.items()
                                                                if k != "handlers" and k != "oracles")))
    if out:
        with open(out, "w") as fh:
            json.dump({"mismatches": C.mism, "counts": C.cnt, "chain": {" ".join(map(str, k)): v for k, v in
                                                                         C.chain.items()}, "cases": C.cases}, fh,
                      indent=1, sort_keys=True)
    return 0 if ok else 1


def main(argv):
    if not argv or argv[0] not in ("check", "manifest"):
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    excel, exe, verbose, out, paths = DEFAULT_EXCEL, drlg.DEFAULT_EXE, False, None, []
    k = 0
    while k < len(rest):
        a = rest[k]
        if a == "--excel":
            excel, k = rest[k + 1], k + 2
        elif a == "--exe":
            exe, k = rest[k + 1], k + 2
        elif a == "--json":
            out, k = rest[k + 1], k + 2
        elif a in ("-v", "--verbose"):
            verbose, k = True, k + 1
        else:
            paths.append(a)
            k += 1
    if cmd == "manifest":
        for p in paths:
            data = open(p, "rb").read()
            print("%s  %d  %d  %s" % (hashlib.sha256(data).hexdigest(), len(data), data.count(b"\n"),
                                      os.path.basename(p)))
        return 0
    C = Checker(Tables(excel, exe), verbose)
    for p in paths:
        C.run(p)
    return report(C, out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
