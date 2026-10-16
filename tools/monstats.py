"""Model of a monster's stats at creation and after the special-mod handlers (plan 0025 Phase 2), checked against
runtime logs, from docs/findings/monsters/0004-stats.md.

Usage:
  python3 -I tools/monstats.py check <run.log> [...] [--excel DIR] [--no-chain] [-v]
  python3 -I tools/monstats.py stats --cls C --diff D --exp 0|1 --lid L [--players N] [--seed LO:HI] [--mods m,m]
                                     [--flag champion|unique|minion]      # one prediction, printed
  python3 -I tools/monstats.py fpsens <run.log> [...] [--excel DIR]     # x87 control-word sensitivity of the stat-7 callback

<run.log> is written by tools/d2run.py with tools/gdb/mon-stats.gdb (the tags of tools/gdb/mon-stats.py on top of every
tag of tools/gdb/mon-special.gdb). Tables are the .bin files the game loads, read by position (monstats, monstats2,
monlvl, monprop, difficultylevels, monumod, properties, itemstatcost, levels) from --excel (default
workspace/merged/data/global/excel).

Chain: unless --no-chain, `check` first runs tools/monspawn.py's checker (which runs tools/monspecial.py, the DRLG
models and tools/monpool.py) on the same logs and requires 0 mismatches there: the unit seed each creation starts from
(Init(step(game).low)), the creations, the mod lists and every handler's seed effects are predicted upstream. This
file predicts what they leave to it:

  * MonStatsInit 0x00573CB0 per creation (SI0..SIX): the appearance pick (one RangeB on the region entry's variant-set
    count, or one draw per MonStats2 component with a count >= 1: low & (c-1) for a power of two, else low % c), the
    doomknight Range(4) (classes 311, 312), MonPlayerBonus (n = max(1, PlayerCount) for Align 0, the HP/XP percent
    tables 0x006E1590 / 0x006E15B4, MonsterSkillBonus), the monster level (tools/monpool.py), L and d, MonLvlStats
    (MulDiv(MonLvl, MonStats, 100), raw cells for noRatio), the HP draw lo + RangeB(hi - lo + 1), the player bonus, the
    0x7FFFFF cap, AC, XP, resistances, block, the constants 67/68/69/352, stat 100, hpregen, the classic
    nightmare/hell adjustment 0x0063EEF0 (table 0x006EA9F0, level = Level + 25 d), MonProp (chance gate, PROP funcs 1,
    8, 17 with their unit-seed value roll; the list with flags 0x40). The unit seed is compared after every draw.
    MonEquipInit (MonStats MonEquip rows with oninit) is an ADR-0004 seed oracle: the seed after it is taken from SIX.
  * Every handler with flag 1 (HST) and every group-member call with flag 0 (TST): the stat writes of
    docs/findings/monsters/0004-stats.md section 8 (hpmultiply, leveladd, champion and its ghostly / fanatic /
    possessed variants, berserk, strong, fast, the five enchantments, resist / spectralhit / stoneskin); every other
    handler must leave the base stats unchanged.
  * A player-count change (PCHG): each live monster's stats 7, 12, 13 and 100 (LIVE) must still equal the model's
    last prediction for that unit (no rescale).

Base stats are compared as sets of non-zero (stat, param, value) entries (a SetStat of 0 leaves no entry).
Exit 0 only if every check holds. Stdlib only. Read-only.
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import drlg  # noqa: E402
import monpool  # noqa: E402
from excel_bin import find_file, read_bin  # noqa: E402
from rng import INIT_HIGH, step  # noqa: E402

DEFAULT_EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
TAGS = {"SI0", "SI1", "SI2", "SI3", "SI4", "SI5", "SIX", "HST", "TST", "PCHG", "LIVE"}
M32 = 0xFFFFFFFF
# handler addresses of g_UModHandlers 0x0073C008 (read from the exe) -> our names
H_NAMES = {0x5A0CE0: "rndname", 0x5A0DC0: "hpmultiply", 0x5A0E40: "leveladd", 0x5A17E0: "strong", 0x5A1910: "fast",
           0x5A1370: "resist", 0x5A1990: "fire", 0x5A0E80: "champion", 0x5A1B00: "lightning", 0x5A1C70: "cold",
           0x5A1E00: "poison", 0x5A1F90: "mana", 0x5A1600: "teleport", 0x5A1650: "aura", 0x5A1080: "ghostly",
           0x5A11F0: "fanatic", 0x5A1230: "possessed", 0x5A1280: "berserk", 0x5A1330: "always_run_ai"}
ENCHANT_STATS = {"fire": (48, 49), "lightning": (50, 51), "cold": (54, 55), "poison": (57, 58), "mana": (62, 63)}


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def tdiv(a, b):
    """C signed division, truncating toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def muldiv(a, b, c):
    """sub_00483360_MulDiv(a, b, c), signed."""
    a, b, c = s32(a), s32(b), s32(c)
    if c == 0:
        return 0
    if a > 0x100000:
        if c > (a >> 4):
            return s32(tdiv(a * b, c))
        return s32(tdiv(a, c) * b)
    if b > 0x10000:
        if c > (b >> 4):
            return s32(tdiv(a * b, c))
        return s32(tdiv(b, c) * a)
    return tdiv(s32(a * b), c)


def div100(v):
    """the inlined signed /100 (0x51EB851F, sar 5, sign fix)."""
    return tdiv(s32(v), 100)


class Seed:
    def __init__(self, t):
        self.lo, self.hi = t

    def t(self):
        return self.lo, self.hi

    def step(self):
        self.lo, self.hi = step(self.lo, self.hi)
        return self.lo

    def rangeb(self, n):
        if n & 0x80000000 or n == 0:
            return 0
        return self.step() % n


def seed_t(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def fmt(t):
    return "%08x:%08x" % t


class Tables:
    def __init__(self, excel=DEFAULT_EXCEL, exe=drlg.DEFAULT_EXE):
        def rb(name, size):
            recs, sz = read_bin(find_file(excel, name, ".bin"))
            assert sz == size, (name, sz)
            return recs
        self.ms = rb("monstats", 0x1A8)
        self.ms2 = rb("monstats2", 0x134)
        self.ml = rb("monlvl", 0x78)
        self.mp = rb("monprop", 0x138)
        self.dl = rb("difficultylevels", 0x58)
        self.mu = rb("monumod", 0x20)
        self.pr = rb("properties", 0x2E)
        self.isc = rb("itemstatcost", 0x144)
        self.me = rb("monequip", 0x1C)
        self.pool = monpool.Tables(excel)
        rd = lambda a, n: drlg.exe_read(exe, a, n)  # noqa: E731
        self.hp_pct = list(struct.unpack("<9i", rd(0x006E1590, 36)))
        self.xp_pct = list(struct.unpack("<9i", rd(0x006E15B4, 36)))
        a = struct.unpack("<15i", rd(0x006EA9F0, 60))
        self.classic = [a[5 * i:5 * i + 5] for i in range(3)]
        h = struct.unpack("<%dI" % len(self.mu), rd(0x0073C008, 4 * len(self.mu)))
        self.handler = [H_NAMES.get(v, "?%08x" % v) if v else None for v in h]

    # --- records ---------------------------------------------------------------------------------------------------
    def m16(self, c, off):
        return struct.unpack_from("<h", self.ms[c], off)[0]

    def mu16(self, c, off):
        return struct.unpack_from("<H", self.ms[c], off)[0]

    def m2(self, c):
        i = self.m16(c, 0x18)
        return self.ms2[i] if 0 <= i < len(self.ms2) else None

    def c(self, r):
        """sub_005A00F0_UModConstant: MonUMod row r +0x1C, 0 outside the table."""
        return struct.unpack_from("<i", self.mu[r], 0x1C)[0] if 0 <= r < len(self.mu) else 0

    def dlrec(self, d):
        return self.dl[max(0, min(d, len(self.dl) - 1))]

    def dl32(self, d, off):
        return struct.unpack_from("<i", self.dlrec(d), off)[0]

    def mlrow(self, lvl):
        n = len(self.ml)
        i = min(lvl, n - 1)
        return self.ml[i] if 0 <= i < n else None

    def ml32(self, row, off):
        return struct.unpack_from("<i", row, off)[0]

    def hireling(self, c):
        return c in monpool.HIRELINGS

    def noratio(self, c):
        return bool(self.ms[c][0x0C] & 0x04)

    def monequip_oninit(self, c):
        r = self.m16(c, 0x2A)
        return 0 <= r < len(self.me) and self.me[r][2] != 0


class Model:
    """The stat model; every function takes the inputs it needs and returns predictions."""

    def __init__(self, T):
        self.T = T

    # --- MonStatsInit ------------------------------------------------------------------------------------------------
    def appearance(self, seed, cls, nvar, vb):
        """sub_005739D0_MonComponentsPick; returns the 16 bytes (None for a variant set whose bytes were not logged)."""
        if nvar:
            i = seed.rangeb(nvar)
            return bytes.fromhex(vb)[16 * i:16 * i + 16] if vb else None
        out = bytearray(16)
        m2 = self.T.m2(cls)
        for k in range(16):
            cnt = m2[0x15 + k] if m2 is not None else 0
            if cnt < 1:
                continue
            low = seed.step()
            out[k] = (low & (cnt - 1)) if cnt & (cnt - 1) == 0 else low % cnt
        return bytes(out)

    def player_bonus(self, cls, g6d, pset, g6a, alive=1):
        """sub_00573930_MonPlayerBonus -> [hpPct, xpPct, skillBonus, difficulty, players]."""
        T = self.T
        hp = xp = 0
        if T.ms[cls][0x4C] == 0:
            n = alive
            if 1 <= g6a <= 3 and pset > n:
                n = pset
            n = max(1, n)
            hp = T.hp_pct[n] if n < 9 else (n - 2) * 50
            xp = T.xp_pct[n] if n < 9 else 10 * n + 260
        else:
            n = 1
        dd = min(g6d, 2)
        return [hp, xp, T.dl32(g6d, 0x10), dd, n]

    def level(self, cls, lid, g6d, exp):
        lvl, d = monpool.monster_level(self.T.pool, cls, lid, g6d, exp)
        return lvl, d

    def monlvl_stats(self, cls, L, d, lvl):
        """sub_006538A0_MonLvlStats mask 7 -> [minHp, maxHp, ac, exp] (zeros when the row is out of range)."""
        T = self.T
        row = T.mlrow(lvl)
        if row is None:
            return [0, 0, 0, 0]
        d = 0 if d < 1 else min(d, 2)
        Lb = 1 if L else 0
        lo, hi = T.m16(cls, 0xB0 + 2 * d), T.m16(cls, 0xB6 + 2 * d)
        ac, ex = T.m16(cls, 0xBC + 2 * d), T.m16(cls, 0xD4 + 2 * d)
        if T.noratio(cls):
            return [lo, hi, ac, ex]
        o = 0xC * Lb + 4 * d
        return [muldiv(T.ml32(row, 0x30 + o), lo, 100), muldiv(T.ml32(row, 0x30 + o), hi, 100),
                muldiv(T.ml32(row, 0x00 + o), ac, 100), muldiv(T.ml32(row, 0x60 + o), ex, 100)]

    def base_stats(self, cls, lvl, d, pb, o, draw, exp, g6d):
        """The SetStat sequence of MonStatsInit (up to MonClassicDiffAdjust included); returns ({stat: value}, hp)."""
        T = self.T
        st = {}

        def ss(k, v):
            st[k] = s32(v)

        ss(12, lvl)
        ss(100, max(1, pb[4]))
        for k, off in ((36, 0x144), (37, 0x14A), (39, 0x150), (41, 0x156), (43, 0x15C), (45, 0x162)):
            ss(k, T.m16(cls, off + 2 * d))
        ss(20, T.ms[cls][0xA3 + d])
        ss(68, 100)
        ss(67, 75)
        ss(69, 100)
        ss(352, 128)
        base = o[0] + draw
        hp = base + muldiv(base, pb[0], 100)
        if hp >= 0x800000:
            hp = 0x7FFFFF
        hp8 = s32(hp << 8)
        ss(7, hp8)
        ss(6, hp8)
        ss(31, o[2])
        ss(13, muldiv(o[3], pb[1], 100) + o[3])
        r = struct.unpack_from("<I", T.ms[cls], 0x1A0)[0]
        if r & 0x80000000 or r & 0xFFFFF000:
            raise ValueError("DamageRegen %d stops the game (fatal 222/223)" % r)
        if r == 0:
            regen = 0
        elif hp8 > tdiv(0x7FFFFFFF, r):
            regen = s32((hp8 >> 12) * r)
        else:
            regen = s32(r * hp8) >> 12
        ss(74, regen)
        # sub_0063EEF0_MonClassicDiffAdjust(unit, expansion, game byte +0x6D)
        if exp == 0 and g6d != 0 and T.ms[cls][0x4C] != 1:
            for row in T.classic:
                k = row[0]
                v = st.get(k, 0)
                v = muldiv(v, row[1], row[2]) if g6d == 1 else muldiv(v, row[3], row[4])
                if k == 7:
                    self.set_maxhp(st, cls, v)
                else:
                    st[k] = v
            st[12] = T.m16(cls, 0xAA) + 25 * g6d
        return st

    def monprop(self, seed, cls, d):
        """MonProp slots (0x0057416A..0x00574220) -> ({(stat, param): value} for the 0x40 list, applied slots)."""
        T = self.T
        i = T.mu16(cls, 0x1A)
        out, applied = {}, []
        if i == 0xFFFF or i >= len(T.mp):
            return out, applied
        rec = T.mp[i]
        for k in range(6):
            prop, par, mn, mx = struct.unpack_from("<4i", rec, 0x04 + 0x60 * d + 0x10 * k)
            if prop < 0:
                break
            ch = rec[0x124 + 6 * d + k]
            if ch and seed.step() % 100 >= ch:
                continue
            applied.append((prop, par, mn, mx))
            self.prop_apply(seed, out, prop, par, mn, mx)
        return out, applied

    def prop_apply(self, seed, out, prop, par, mn, mx):
        """PROP_ApplyBlock mode 0 on a monster: the funcs met in MonProp (1, 8, 17)."""
        T = self.T
        pr = T.pr[prop]
        prev = 0
        for j in range(7):
            func = pr[0x18 + j]
            if func == 0:
                break
            stat = struct.unpack_from("<H", pr, 0x20 + 2 * j)[0]
            setf = pr[0x02 + j]

            def roll():
                if mn == mx:
                    return mn
                lo, hi = min(mn, mx), max(mn, mx)
                return lo + seed.rangeb(hi - lo + 1)
            if func == 1:
                v = roll()
            elif func == 8:
                v = prev if prev else roll()
            elif func == 17:
                v = par if par else roll()
            else:
                raise NotImplementedError("PROP func %d (property %d) in a MonProp row" % (func, prop))
            prev = v
            if v == 0 or stat == 0xFFFF:
                continue
            vs = v << T.isc[stat][0x18]
            key = (stat, 0)
            out[key] = s32(vs if setf else out.get(key, 0) + vs)

    # --- the unit's stat callback ------------------------------------------------------------------------------------
    def set_maxhp(self, st, cls, new):
        """SetStat(7, new) on a monster: MonStatsInit registers sub_0055B800_MonStatCallback (0x00573E62, before any
        SetStat), whose stat-7 case runs on every change of the value: when old > 0, new != old and stat 6 > 0, stat 6 =
        clamp(trunc(float32(new / max(old, 256) * cur)), 1, new) and, for a class with DamageRegen r != 0, stat 74 =
        ((new >> 8) * r) >> 4."""
        old = st.get(7, 0)
        st[7] = s32(new)
        if new == old or old <= 0:
            return
        cur = st.get(6, 0)
        if cur <= 0:
            return
        o = 0x100 if old <= 0x100 else old
        x = struct.unpack("<f", struct.pack("<f", (float(new) / float(o)) * float(cur)))[0]
        t = int(x)
        v = new if max(t, 1) >= new else max(t, 1)
        st[6] = s32(v)
        r = struct.unpack_from("<I", self.T.ms[cls], 0x1A0)[0]
        if r:
            st[74] = s32(s32((new >> 8) * r) >> 4)

    # --- the handlers ------------------------------------------------------------------------------------------------
    def hp_add_pct(self, st, pct, cls):
        """sub_005A0D20_MonHpAddPct."""
        h = st.get(7, 0)
        if h > 0x100000:
            q = s32(tdiv(h * pct, 100)) if (h & ~0xF) < 0x640 else s32(tdiv(h, 100) * pct)
        elif pct > 0x10000:
            q = s32(tdiv(h * pct, 100)) if (pct & ~0xF) < 0x640 else s32(tdiv(pct, 100) * h)
        else:
            q = tdiv(s32(h * pct), 100)
        h2 = s32(h + q)
        self.set_maxhp(st, cls, h2)
        st[6] = h2

    def add(self, st, k, v):
        if v:
            st[k] = s32(st.get(k, 0) + v)

    def is_willowisp(self, cls):
        return self.T.m16(cls, 0x02) == 0x76

    def velocity_bonus(self, cls):
        v = self.T.m16(cls, 0x32)
        if v <= 0:
            return None
        x = tdiv(0x800, v) - 0x80
        return 10 if x <= 10 else min(x, 100)

    def champion_part(self, st, cls, mod, g6d):
        T = self.T
        st[12] = s32(st.get(12, 0) - 1)
        x = st.get(13, 0) & M32
        st[13] = s32(x - 2 * (x // 5))
        cdb = T.dl32(g6d, 0x34)
        dmg = div100(cdb * T.c(11))
        th = div100(cdb * T.c(10))
        if self.is_willowisp(cls):
            dmg = tdiv(dmg, 2)
        self.add(st, 25, dmg)
        self.add(st, 119, th)
        if T.m16(cls, 0x32) > 0 and mod != 36:
            if mod == 37:
                self.add(st, 67, self.velocity_bonus(cls))
            else:
                self.add(st, 67, 20)

    def enchant_base(self, st, g6d, L):
        T = self.T
        d = min(g6d, 2)
        lvl = st.get(12, 0)
        n = len(T.ml)
        ell = min(max(lvl, 1), n - 1)
        row = T.ml[ell]
        return ell, d, T.ml32(row, 0x48 + 0xC * (1 if L else 0) + 4 * d)

    def resist(self, st, mod):
        """sub_005A1370_UModResist, flag 1."""
        if mod == 28:
            st[31] = s32(2 * st.get(31, 0))
        fi, li, co, po, dm, ma = (st.get(k, 0) for k in (39, 41, 43, 45, 36, 37))
        k = sum(1 for v in (fi, li, co, po, dm, ma) if v >= 100)
        if k >= 2:
            return

        def bump(stat, v, add, below):
            nonlocal k
            if k >= 2 or v >= below:
                return False
            st[stat] = s32(v + add)
            if v + add >= 100:
                k += 1
            return True
        if mod == 8:
            bump(43, co, 40, 100)
            bump(39, fi, 40, 100)
            bump(41, li, 40, 100)
        elif mod == 9:
            st[39] = s32(fi + 75)
        elif mod == 18:
            st[43] = s32(co + 75)
        elif mod == 17:
            st[41] = s32(li + 75)
        elif mod == 23:
            st[45] = s32(po + 75)
        elif mod == 25:
            st[37] = s32(ma + 20)
        elif mod == 27:
            bump(43, co, 20, 75)
            bump(39, fi, 20, 75)
            bump(41, li, 20, 75)
        elif mod == 28:
            st[36] = s32(dm + 50)

    def handler(self, st, cls, mod, flag, mf, g6d, L):
        """Apply MonUMod handler `mod` with flag 1 (the special) or 0 (a group member) to the stat dict in place.
        Returns the handler's name, or None for a mod with no handler."""
        T = self.T
        name = T.handler[mod] if 0 <= mod < len(T.handler) else None
        if name is None:
            return None
        if name == "hpmultiply":
            if g6d < 3:
                if flag:
                    self.hp_add_pct(st, T.c(4 + g6d) if mf & 4 else T.c(7 + g6d), cls)
                    st[74] = 0
                else:
                    self.hp_add_pct(st, T.c(1 + g6d), cls)
        elif name == "leveladd":
            st[12] = s32(st.get(12, 0) + 3)
            st[13] = s32(st.get(13, 0) * 5)
        elif name == "champion":
            if flag:
                self.champion_part(st, cls, mod, g6d)
        elif name == "ghostly":
            if flag:
                st[36] = 80
                self.champion_part(st, cls, mod, g6d)
                _ell, d, dm = self.enchant_base(st, g6d, L)
                self.add(st, 54, div100(T.c(0x16 + d) * dm))
                self.add(st, 55, div100(T.c(0x19 + d) * dm))
                self.add(st, 56, 150)
        elif name == "fanatic":
            if flag:
                st[16] = -70
                self.champion_part(st, cls, mod, g6d)
        elif name == "possessed":
            if flag:
                self.hp_add_pct(st, 100, cls)
                self.champion_part(st, cls, mod, g6d)
        elif name == "berserk":
            if flag:
                self.hp_add_pct(st, -75, cls)
                cdb = T.dl32(g6d, 0x34)
                v = div100(cdb * 300)
                dmg = tdiv(v, 2) if self.is_willowisp(cls) else v
                self.add(st, 25, dmg)
                self.add(st, 119, v)
        elif name == "strong":
            cdb = T.dl32(g6d, 0x34)
            dmg, th = (T.c(15), T.c(13)) if flag else (T.c(14), T.c(12))
            dmg, th = div100(cdb * dmg), div100(cdb * th)
            if self.is_willowisp(cls):
                dmg = tdiv(dmg, 2)
            self.add(st, 25, dmg)
            self.add(st, 119, th)
        elif name == "fast":
            v = self.velocity_bonus(cls)
            if v is not None:
                self.add(st, 67, v)
        elif name in ENCHANT_STATS:
            ell, d, dm = self.enchant_base(st, g6d, L)
            if flag:
                mn, mx = div100(T.c(0x1C + d) * dm), div100(T.c(0x1F + d) * dm)
            else:
                mn, mx = div100(T.c(0x10 + d) * dm), div100(T.c(0x13 + d) * dm)
            if name == "mana":
                mn, mx = s32(mn << 8), s32(mx << 8)
            a, b = ENCHANT_STATS[name]
            self.add(st, a, mn)
            self.add(st, b, mx)
            if name == "cold":
                self.add(st, 56, 5 * ell + 100)
            elif name == "poison":
                self.add(st, 59, (5 * ell + 150) * 2)
            if flag:
                self.resist(st, mod)
        elif name == "resist":
            if flag:
                self.resist(st, mod)
        # rndname, teleport, aura, always_run_ai: no stat write
        return name


def nz(b):
    """{(stat, param): value} of a logged array, zeros dropped."""
    return {(s, p): v for s, p, v in (b or []) if v != 0}


def nzd(st):
    return {(k, 0): v for k, v in st.items() if v != 0}


class Checker:
    def __init__(self, excel, verbose):
        self.T = Tables(excel)
        self.M = Model(self.T)
        self.verbose = verbose
        self.checks = self.fail = 0
        self.units = {}           # unit address -> state
        self.by_id = {}           # unit id -> every creation with that id, in order
        self.n = {}
        self.cases = {}
        self.creations = []
        self.handlers = {}
        self.no_ms = 0

    def ok(self, cond, msg):
        self.checks += 1
        if not cond:
            self.fail += 1
            if self.fail <= 60:
                print("MISMATCH %s" % msg)
        return cond

    def eq(self, what, got, want, where):
        return self.ok(got == want, "%s %s: logged %r, model %r" % (where, what, got, want))

    def note(self, k, v=1):
        self.n[k] = self.n.get(k, 0) + v

    def case(self, k, v):
        self.cases.setdefault(k, []).append(v)

    def diff(self, got, want):
        ks = sorted(set(got) | set(want))
        return ["%s: %r vs %r" % (k, got.get(k), want.get(k)) for k in ks if got.get(k) != want.get(k)]

    def cmp_stats(self, what, b, st, where):
        got, want = nz(b), nzd(st)
        if not self.ok(got == want, "%s %s: %s" % (where, what, "; ".join(self.diff(got, want)))):
            return False
        return True

    def run(self, path):
        lines = []
        for ln, line in enumerate(open(path, errors="replace"), 1):
            tag, _, rest = line.partition(" ")
            if tag == "LOGERR":
                self.ok(False, "%s:%d logger error %s" % (path, ln, rest.strip()))
                continue
            if tag in TAGS:
                try:
                    lines.append((tag, json.loads(rest), ln))
                except ValueError:
                    pass
        base = os.path.basename(path)
        cur = None
        self.units, self.by_id = {}, {}        # unit addresses and ids belong to one game
        for tag, d, ln in lines:
            where = "%s:%d" % (base, ln)
            try:
                if tag == "SI0":
                    cur = self.si0(d, where)
                elif tag in ("SI1", "SI2", "SI3", "SI4", "SI5", "SIX"):
                    if cur is None or cur["u"] != d["u"]:
                        self.ok(False, "%s %s without its SI0" % (where, tag))
                        continue
                    getattr(self, tag.lower())(cur, d, where)
                    if tag == "SIX":
                        cur = None
                elif tag in ("HST", "TST"):
                    self.handler(tag, d, where)
                elif tag == "PCHG":
                    self.note("player-count changes")
                    self.case("pchg", "%s %d -> %d" % (where, d["old"], d["new"]))
                elif tag == "LIVE":
                    self.live(d, where)
            except (ValueError, NotImplementedError, KeyError, IndexError) as e:
                self.ok(False, "%s %s model error %r" % (where, tag, e))

    # --- per creation ------------------------------------------------------------------------------------------------
    def si0(self, d, where):
        T, M = self.T, self.M
        cls = d["cls"]
        us = seed_t(d["us"])
        if us[1] != INIT_HIGH:                  # created on another path (a summon, a spawner's child): the entry
            self.note("creations whose entry unit seed is not an Init seed")   # seed is the upstream's, as logged
        U = {"u": d["u"], "id": d["id"], "cls": cls, "seed": Seed(us), "lid": d.get("lid", "?"), "g6a": d["g6a"],
             "g6d": d["g6d"], "exp": 1 if d["exp"] else 0, "g74": d["g74"], "pset": d["pset"], "where": where,
             "steps": 0}
        U["L"] = 1 if (d["g6a"] != 0 or d["g74"] != 0) else 0
        U["app"] = M.appearance(U["seed"], cls, d["nvar"] if d["ent"] else 0, d.get("vb"))
        U["nvar"] = d["nvar"] if d["ent"] else 0
        if cls in (311, 312):
            # B3: MonsterData +0x0E (appearance byte 10) <- Range(4); 312 also +0x0F (0x00573D68-0x00573DAC; plan 0038 H4b)
            r = U["seed"].rangeb(4)
            if U["app"] is not None:
                app = bytearray(U["app"])
                app[10] = r
                if cls == 312:
                    app[11] = r
                U["app"] = bytes(app)
            self.note("doomknight Range(4) class %d" % cls)
        self.units[d["u"]] = U
        self.by_id.setdefault(d["id"], []).append(U)
        return U

    def si1(self, U, d, where):
        M = self.M
        self.eq("unit seed after the appearance pick", d["us"], fmt(U["seed"].t()), where)
        if U["app"] is not None and d.get("app") is not None:
            self.eq("appearance bytes", d["app"], U["app"].hex(), where)
        pb = M.player_bonus(U["cls"], U["g6d"], U["pset"], U["g6a"])
        self.eq("MonPlayerBonus", d["pb"], pb, where)
        U["pb"] = pb
        if U["nvar"]:
            self.note("appearance: variant set pick")
        else:
            self.note("appearance: per-component draws")

    def si2(self, U, d, where):
        M = self.M
        if U["lid"] == "?":                 # a log written before SI0 carried the level id: the level is taken
            lvl, dd = d["lvl"], d["d"]      # from the log (development logs only)
            self.note("level taken from the log (no level id in SI0)")
        else:
            lvl, dd = M.level(U["cls"], U["lid"], U["g6d"], U["exp"])
        self.eq("level, L, d", (d["lvl"], d["L"], d["d"]), (lvl, U["L"], dd), where)
        o = M.monlvl_stats(U["cls"], U["L"], dd, lvl)
        self.eq("MonLvlStats (minHp, maxHp, ac, exp)", d["o"], o, where)
        U.update(lvl=lvl, d=dd, o=o)
        # the L- case: would the classic columns give another result?
        if not M.T.noratio(U["cls"]) and dd > 0:
            o0 = M.monlvl_stats(U["cls"], 0, dd, lvl)
            if o0 != o:
                self.note("creations where the L- columns differ from the plain ones")
                self.case("lminus", "%s cls %d d %d lvl %d: L=1 %s, L=0 would give %s" % (
                    where, U["cls"], dd, lvl, o, o0))

    def si3(self, U, d, where):
        o = U["o"]
        n = o[1] - o[0] + 1
        r = U["seed"].rangeb(n)
        if n < 1:
            self.note("HP draw with hi < lo: no step")
            self.case("reversed", "%s cls %d: lo %d hi %d" % (where, U["cls"], o[0], o[1]))
        self.eq("HP draw", d["r"], r, where)
        self.eq("unit seed after the HP draw", d["us"], fmt(U["seed"].t()), where)
        U["draw"] = r

    def si4(self, U, d, where):
        st = self.M.base_stats(U["cls"], U["lvl"], U["d"], U["pb"], U["o"], U["draw"], U["exp"], U["g6d"])
        U["st"] = st
        self.cmp_stats("base stats after MonClassicDiffAdjust", d["b"], st, where)
        if U["exp"] == 0 and U["g6d"] and self.T.ms[U["cls"]][0x4C] != 1:
            self.note("classic nightmare/hell adjustment")
            lv = self.T.m16(U["cls"], 0xAA) + 25 * U["g6d"]
            ld = self.T.m16(U["cls"], 0xAA + 2 * min(U["g6d"], 2))
            if lv != ld:
                self.note("classic: Level + 25 d differs from Level(d)")

    def si5(self, U, d, where):
        T, M = self.T, self.M
        before = U["seed"].t()
        mp, applied = M.monprop(U["seed"], U["cls"], U["d"])
        U["mp"] = mp
        self.eq("unit seed after MonProp", d["us"], fmt(U["seed"].t()), where)
        self.cmp_stats("base stats after MonProp", d["b"], U["st"], where)
        sub = [s for s in d.get("sub") or [] if s[0] & 0x40]
        got = nz(sub[0][2]) if sub else {}
        want = {k: v for k, v in mp.items() if v}
        self.ok(got == want, "%s MonProp list (flags 0x40): logged %r, model %r" % (where, got, want))
        if applied:
            self.note("MonProp rows applied")
            self.case("monprop", "%s cls %d d %d exp %d: %s -> %s%s" % (
                where, U["cls"], U["d"], U["exp"], applied, sorted(want.items()),
                " (value roll on the unit seed)" if before != U["seed"].t() else ""))
            U["monprop"] = True

    def six(self, U, d, where):
        if self.T.monequip_oninit(U["cls"]):
            self.note("MonEquip seed oracle (oninit class)")
            U["seed"] = Seed(seed_t(d["us"]))
        else:
            self.eq("unit seed after MonEquipInit (no oninit row: no draw)", d["us"], fmt(U["seed"].t()), where)
            self.cmp_stats("base stats at the exit", d["b"], U["st"], where)
        self.note("creations")
        key = ("expansion" if U["exp"] else "classic", ("normal", "nightmare", "hell")[min(U["g6d"], 2)], U["pb"][4])
        self.creations.append(key)

    # --- handlers ----------------------------------------------------------------------------------------------------
    def handler(self, tag, d, where):
        U = self.units.get(d["u"])
        if U is None or "st" not in U:
            self.no_ms += 1
            return
        flag = 1 if tag == "HST" else 0
        st = U["st"]
        before = dict(st)
        name = self.M.handler(st, U["cls"], d["m"], flag, d.get("mf", 0), U["g6d"], U["L"])
        ok = self.cmp_stats("stats after handler %s (mod %d, flag %d)" % (name, d["m"], flag), d["b"], st, where)
        if not ok:
            U["st"] = {k: v for (k, p), v in nz(d["b"]).items() if p == 0}   # resynchronise on the log
        k = (name or "none", d["m"], flag, ("expansion" if U["exp"] else "classic"),
             ("normal", "nightmare", "hell")[min(U["g6d"], 2)])
        self.handlers[k] = self.handlers.get(k, 0) + 1
        changed = sorted(k2 for k2 in set(before) | set(st) if before.get(k2, 0) != st.get(k2, 0))
        if name == "resist" and d["m"] == 27 and flag:
            self.case("spectral", "%s cls %d: %s -> %s" % (where, U["cls"],
                                                          [before.get(k2, 0) for k2 in (43, 39, 41)],
                                                          [st.get(k2, 0) for k2 in (43, 39, 41)]))
        if name == "berserk":
            self.case("berserk", "%s cls %d level %d -> %d (handler) " % (where, U["cls"], before.get(12, 0),
                                                                         st.get(12, 0)))
        if name == "aura" and U["exp"] == 0 and U["g6d"]:
            self.case("classic_aura", "%s cls %d d %d: level stat %d (Level %d + 25 d + 3 = %d; Level(d) + 3 = %d)" % (
                where, U["cls"], U["g6d"], st.get(12, 0), self.T.m16(U["cls"], 0xAA),
                self.T.m16(U["cls"], 0xAA) + 25 * U["g6d"] + 3, self.T.m16(U["cls"], 0xAA + 2 * min(U["g6d"], 2)) + 3))
        if self.verbose:
            print("%s %s %s mod %d flag %d changed %s" % (where, tag, name, d["m"], flag, changed))

    def live(self, d, where):
        U = self.units.get(d["u"])
        if U is None or U["id"] != d["id"] or "st" not in U:
            self.note("LIVE monsters without a model state")
            return
        s = d["s"]
        # A monster of a room that went inactive is removed and, when the room comes back, created again with the
        # same unit id and class through a full MonsterInit (new unit seed, new HP draw), after which the restore
        # path writes back the saved stats: stats 7, 12 and 13 are the first instance's, stat 100 the new one's.
        first = [V for V in self.by_id.get(U["id"], []) if V["cls"] == U["cls"] and "st" in V][0]
        if first is not U:
            self.note("LIVE monsters re-created from an inactive room (stats of the first instance)")
        for k in ("7", "12", "13"):
            self.eq("live stat %s after a player-count change" % k, s.get(k, 0), first["st"].get(int(k), 0), where)
        self.eq("live stat 100 after a player-count change", s.get("100", 0), U["st"].get(100, 0), where)
        self.note("live monsters compared after a player-count change")
        self.case("live", "%s cls %d players at creation %d: stat 7 %d, 13 %d, 100 %d" % (
            where, U["cls"], U["pb"][4], s.get("7", 0), s.get("13", 0), s.get("100", 0)))


def cmd_check(argv):
    excel, verbose, chain, paths = DEFAULT_EXCEL, False, True, []
    it = iter(argv)
    for a in it:
        if a == "--excel":
            excel = next(it)
        elif a == "-v":
            verbose = True
        elif a == "--no-chain":
            chain = False
        else:
            paths.append(a)
    if not paths:
        print(__doc__)
        return 2
    rc = 0
    if chain:
        import monspawn
        print("== tools/monspawn.py check (chain) ==")
        rc = monspawn.cmd_check((["--excel", excel] if excel != DEFAULT_EXCEL else []) + paths)
        print("== tools/monstats.py ==")
    c = Checker(excel, verbose)
    for p in paths:
        c.run(p)
    by = {}
    for k in c.creations:
        by[k] = by.get(k, 0) + 1
    print("creations by (game, difficulty, players): %s" % sorted(by.items()))
    for k in sorted(c.n):
        print("  %-66s %d" % (k, c.n[k]))
    print("handler calls compared (name, mod, flag, game, difficulty): %d kinds" % len(c.handlers))
    for k in sorted(c.handlers, key=str):
        print("  %-66s %d" % (k, c.handlers[k]))
    if c.no_ms:
        print("  handler lines of units created before the logger (skipped): %d" % c.no_ms)
    for k in sorted(c.cases):
        v = c.cases[k]
        print("case %s: %d" % (k, len(v)))
        for x in v[:8]:
            print("    " + x)
    print("monstats: %d checks, %d mismatches" % (c.checks, c.fail))
    return 1 if (c.fail or rc) else 0


def _fp_round(x, p, chop):
    """Round a positive Fraction to p significant bits: nearest-even, or toward zero when chop."""
    from fractions import Fraction
    e = x.numerator.bit_length() - x.denominator.bit_length()
    while Fraction(2) ** e > x:
        e -= 1
    while Fraction(2) ** (e + 1) <= x:
        e += 1
    q = x / Fraction(2) ** (e - p + 1)
    n, r = divmod(q.numerator, q.denominator)
    if not chop and (2 * r > q.denominator or (2 * r == q.denominator and n % 2)):
        n += 1
    return n * Fraction(2) ** (e - p + 1)


def _fp_callback(new, o, cur, p, chop):
    """The stat-7 callback's fild new / fidiv o / fimul cur at precision p, fstp float32, then the clamp."""
    from fractions import Fraction
    f = _fp_round(_fp_round(_fp_round(Fraction(new, o), p, chop) * cur, p, chop), 24, chop)
    t = f.numerator // f.denominator
    return new if max(t, 1) >= new else max(t, 1)


def cmd_fpsens(argv):
    """Run the check (no chain) and record every stat-7 callback that writes stat 6 (new != old, old > 0, cur > 0);
    then count, per x87 precision control (24, 53, 64 bits) and rounding mode (nearest, chop), the calls whose stat 6
    would differ from the model's double product rounded to float32. A variant that differs in a call the check
    reproduced is excluded by that run."""
    calls = []
    orig = Model.set_maxhp

    def rec(self, st, cls, new):
        old, cur = st.get(7, 0), st.get(6, 0)
        if new != old and old > 0 and cur > 0:
            calls.append((new, 0x100 if old <= 0x100 else old, cur))
        return orig(self, st, cls, new)
    Model.set_maxhp = rec
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        rc = cmd_check(["--no-chain"] + argv)
    Model.set_maxhp = orig
    print("check exit %d; stat-7 callback calls writing stat 6: %d (distinct inputs %d)" % (rc, len(calls), len(set(calls))))

    def model(new, o, cur):
        x = struct.unpack("<f", struct.pack("<f", (float(new) / float(o)) * float(cur)))[0]
        t = int(x)
        return new if max(t, 1) >= new else max(t, 1)
    for chop in (False, True):
        for p in (24, 53, 64):
            d = sum(1 for c in calls if _fp_callback(*c, p, chop) != model(*c))
            print("  PC %d, RC %s: %d calls differ from the model" % (p, "chop" if chop else "nearest", d))
    return rc


def cmd_stats(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="monstats.py stats")
    ap.add_argument("--cls", type=int, required=True)
    ap.add_argument("--diff", type=int, required=True)
    ap.add_argument("--exp", type=int, required=True)
    ap.add_argument("--lid", type=int, required=True)
    ap.add_argument("--players", type=int, default=1)
    ap.add_argument("--seed", help="the unit seed at MonStatsInit entry, lo:hi (default: no draw, HP = minimum)")
    ap.add_argument("--mods", default="")
    ap.add_argument("--flag", choices=("champion", "unique", "minion"), default=None)
    ap.add_argument("--excel", default=DEFAULT_EXCEL)
    a = ap.parse_args(argv)
    T = Tables(a.excel)
    M = Model(T)
    seed = Seed(seed_t(a.seed)) if a.seed else None
    if seed:
        M.appearance(seed, a.cls, 0, None)
    pb = M.player_bonus(a.cls, a.diff, a.players, 3)
    lvl, d = M.level(a.cls, a.lid, a.diff, a.exp)
    o = M.monlvl_stats(a.cls, 1, d, lvl)
    draw = seed.rangeb(o[1] - o[0] + 1) if seed else 0
    st = M.base_stats(a.cls, lvl, d, pb, o, draw, a.exp, a.diff)
    mp, _ = M.monprop(seed or Seed((0, 0)), a.cls, d)
    print("level %d d %d MonLvlStats %s draw %d" % (lvl, d, o, draw))
    print("creation: %s" % sorted(st.items()))
    if mp:
        print("MonProp: %s" % sorted(mp.items()))
    mods = [int(x) for x in a.mods.split(",") if x]
    if mods:
        mf = {"champion": 4, "unique": 8, "minion": 16}.get(a.flag, 0)
        flag = 0 if a.flag == "minion" else 1
        for m in [1, 2, 3, 4] + mods:
            M.handler(st, a.cls, m, flag, mf, a.diff, 1)
        print("after mods %s (flag %d): %s" % (mods, flag, sorted(st.items())))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "check":
        return cmd_check(argv[2:])
    if len(argv) >= 2 and argv[1] == "fpsens":
        return cmd_fpsens(argv[2:])
    if len(argv) >= 2 and argv[1] == "stats":
        return cmd_stats(argv[2:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
