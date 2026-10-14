"""Model of the special-monster draws (plan 0018 Phase 2): mod picks, mod handlers, minion transfer, superuniques and
the client name roll, from docs/findings/monsters/0003-special-monsters.md.

Usage:
  python3 -I tools/monspecial.py roll <seed-lo:hi> --cls C --diff D --exp 0|1 [--allow 0|1] [--mods m,m]
  python3 -I tools/monspecial.py name <name-seed>
  python3 -I tools/monspecial.py isa <type-a> <type-b>

The checker is tools/monspawn.py, which calls this module at every special in a log (SMR, SMA, the handler, aura,
superunique, MonPlace and client name tags of tools/gdb/mon-special.py); this file only holds the model.

Tables (by position, the .bin files the game loads): monumod (0x20), montype (12), monstats (0x1A8), monstats2
(0x134), superuniques (0x34), uniqueprefix / uniquesuffix / uniqueappellation (2). Constant data from the pinned
game.exe: g_UModHandlers 0x0073C008 (which rows have a server handler), g_UModAlwaysMods 0x006E2168 (1, 2, 3, 4),
g_UModAuraTable 0x0073BF68 (8 rows {minLevel, add, mul, div, skill}), and the client name builder's fixed-name
classes (jump tables 0x004ACB98 / 0x004ACB80 and 0x004ACC4C, plus class 544).

Every draw is modelled; nothing is taken from a log:
  * SpecialModsRoll 0x005A0760: skip at >= 8 mods; allowChampion: Range(us, 100) < MonUMod[0].constants -> one
    ChampionModPick; else Range(us, 1) and min(1 + d, 9 - k) UniqueModPick, stop at the first 0.
  * ChampionModPick 0x005A0500 / UniqueModPick 0x005A0600: candidates in row order (weight s16 > 0, champion byte set
    / clear, ModEligible, unique: not in `have`), one Range(us, total), first row whose weight exceeds the rest.
  * ModEligible 0x005A03E0 and MonTypeIsA 0x005A0070 on the matrix built by 0x00658460 (DataTables+0xC44): row t,
    bit c is set iff c is reachable from t through equiv1..3 (depth-first, stack of 125).
  * SpecialModsApply 0x005A2120: the handlers of 1..4 and of the list; only rndname (1) steps the unit seed (flag 1),
    and its low 16 bits become the name seed; aura (30): Range(Init(nameSeed), n) with n the aura rows whose minLevel
    <= the level (>= 1), index 5 for superunique 37.
  * ModsXferCopy 0x005A0930, the superunique build 0x005A49B0, Radament's Range(us, 5) + 2.
  * The client name roll 0x004AC870: Init(nameSeed & 0xFF) (the client keeps the low byte of the 16 bits the server
    sends, 0x0045F387); suffix, prefix; Range(100) < 50 -> appellation, suffix, prefix.
Stdlib only. Read-only.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import drlg  # noqa: E402
from excel_bin import find_file, read_bin  # noqa: E402
from rng import INIT_HIGH, step  # noqa: E402

DEFAULT_EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")

M_RNDNAME, M_AURA, M_CHAMPION, M_THIEF, M_QUESTCOMPLETE = 1, 30, 16, 24, 22
SU_LORD_DE_SEIS = 37
CLS_UBERMEPHISTO = 0x2C0
# SuperUniqueSpawn tails (record +0x08), docs/findings/monsters/0003 section 6
SU_TAIL_NO_DRAW = {6, 26, 27, 29, 36, 37, 38, 39, 43, 44, 45}
SU_TAIL_RADAMENT = 10
SU_TAIL_ESCORT = {60}                          # Nihlathak: EscortSpawn(LevelClassVariant(room, 453), ...), not modelled
SU_TAIL_ESCORT_FIXED = {42: (453, 20, 20, 0),   # Siege Boss: EscortSpawn(class, radius, count, flags) 0x005A4D6D
                        62: (381, 20, 10, 0x40)}  # Baal Subject 2 0x005A4E2D
RADAMENT_ESCORTS = (276, 382, 385, 389)        # after Range(5) + 2 of class 4


class ModelError(Exception):
    pass


class Seed:
    """A mutable seed {low, high}."""
    def __init__(self, t):
        self.lo, self.hi = t

    def t(self):
        return self.lo, self.hi

    def step(self):
        self.lo, self.hi = step(self.lo, self.hi)
        return self.lo

    def rangeb(self, n):
        """RNG_Range / RNG_RangeB and the inlined copies: (int32)n < 1 -> 0 and no step; else step, low % n."""
        if n & 0x80000000 or n == 0:
            return 0
        return self.step() % n


class Data:
    def __init__(self, excel=DEFAULT_EXCEL, exe=drlg.DEFAULT_EXE):
        self.mu, sz = read_bin(find_file(excel, "monumod", ".bin"))
        assert sz == 0x20
        self.mt, sz = read_bin(find_file(excel, "montype", ".bin"))
        assert sz == 12
        self.ms, sz = read_bin(find_file(excel, "monstats", ".bin"))
        assert sz == 0x1A8
        self.ms2, sz = read_bin(find_file(excel, "monstats2", ".bin"))
        assert sz == 0x134
        self.su, sz = read_bin(find_file(excel, "superuniques", ".bin"))
        assert sz == 0x34
        self.n_prefix = len(read_bin(find_file(excel, "uniqueprefix", ".bin"))[0])
        self.n_suffix = len(read_bin(find_file(excel, "uniquesuffix", ".bin"))[0])
        self.n_app = len(read_bin(find_file(excel, "uniqueappellation", ".bin"))[0])
        h = struct.unpack("<%dI" % len(self.mu), drlg.exe_read(exe, 0x0073C008, 4 * len(self.mu)))
        self.handler = [v != 0 for v in h]
        self.always = list(struct.unpack("<4I", drlg.exe_read(exe, 0x006E2168, 16)))
        a = struct.unpack("<40i", drlg.exe_read(exe, 0x0073BF68, 160))
        self.aura_rows = [a[5 * i:5 * i + 5] for i in range(8)]
        tb = drlg.exe_read(exe, 0x004ACB98, 178)
        jt = struct.unpack("<6I", drlg.exe_read(exe, 0x004ACB80, 24))
        fixed = {156 + i for i, b in enumerate(tb) if jt[b] != 0x004ACAF6}
        j2 = struct.unpack("<6I", drlg.exe_read(exe, 0x004ACC4C, 24))
        fixed |= {0x2C0 + i for i, v in enumerate(j2) if v != 0x004ACAF6}
        fixed.add(0x220)
        self.name_fixed = fixed
        self._isa = {}

    # --- records -----------------------------------------------------------------------------------------------
    def mu_s16(self, r, off):
        return struct.unpack_from("<h", self.mu[r], off)[0]

    def constants(self, r):
        return struct.unpack_from("<I", self.mu[r], 0x1C)[0] if 0 <= r < len(self.mu) else 0

    def xfer(self, m):
        return 0 <= m < len(self.mu) and self.mu[m][7] != 0

    def valid(self, c):
        return 0 <= c < len(self.ms)

    def ms_s16(self, c, off):
        return struct.unpack_from("<h", self.ms[c], off)[0]

    def minion_class(self, c):
        """sub_005A0BB0_UniqueMinionClass: minion1 if a valid class, else the class itself."""
        if not self.valid(c):
            return c
        m = self.ms_s16(c, 0x26)
        return m if 0 <= m < len(self.ms) else c

    def su_rec(self, i):
        if not 0 <= i < len(self.su):
            return None
        r = self.su[i]
        f = struct.unpack_from("<IiI3I", r, 0)        # hcIdx|Name (u16 u16), Class, Superunique, Mod1..3
        return {"cls": f[1], "idx": f[2], "mods": list(f[3:6]),
                "min": struct.unpack_from("<I", r, 0x1C)[0], "max": struct.unpack_from("<I", r, 0x20)[0],
                "autopos": r[0x24], "stacks": r[0x26]}

    # --- MonTypeIsA --------------------------------------------------------------------------------------------
    def isa(self, i, j):
        """0x00658460: True iff type j is reachable from type i through equiv1..3 (i itself included)."""
        k = (i, j)
        if k in self._isa:
            return self._isa[k]
        n = len(self.mt)
        res = False
        if j > 0 and 0 < i < n:
            stack = [i]
            while stack:
                c = stack.pop()
                if c == j:
                    res = True
                    break
                if c >= n or len(stack) > 124:
                    break
                if c < 0:
                    raise ModelError("negative MonType %d in the equiv walk" % c)
                rec = self.mt[c]
                e1 = struct.unpack_from("<h", rec, 2)[0]
                if e1 > 0:
                    stack.append(e1)
                    e2 = struct.unpack_from("<h", rec, 4)[0]
                    if e2 != 0:
                        stack.append(e2)
                        e3 = struct.unpack_from("<h", rec, 6)[0]
                        if e3 != 0:
                            stack.append(e3)
        self._isa[k] = res
        return res

    def montype_isa(self, cls, t):
        """sub_005A0070_MonTypeIsA(unit of class cls, t): matrix row t, bit = the class's MonType."""
        if not self.valid(cls):
            return False
        ct = self.ms_s16(cls, 0x1C)
        n = len(self.mt)
        if ct < 0 or ct >= n or t < 0 or t >= n:
            return False
        return self.isa(t, ct)

    def mode_allowed(self, cls, mode):
        """sub_0046C140_MonModeAllowed: MonStats2 byte +0xF0 + (mode >> 3), bit mode & 7."""
        if not self.valid(cls):
            return False
        i = self.ms_s16(cls, 0x18)
        if not 0 <= i < len(self.ms2):
            return False
        return bool(self.ms2[i][0xF0 + (mode >> 3)] & (1 << (mode & 7)))

    def eligible(self, r, exp, cls, isa_log):
        """sub_005A03E0_ModEligible; every MonTypeIsA call is appended to isa_log as (cls, t, result)."""
        rec = self.mu[r]
        if rec[6] == 0:
            return False
        if exp == 0 and struct.unpack_from("<H", rec, 4)[0] >= 100:
            return False
        for off in (0x0A, 0x0C):
            t = struct.unpack_from("<h", rec, off)[0]
            if t <= 0:
                break
            v = self.montype_isa(cls, t)
            isa_log.append((cls, t, 1 if v else 0))
            if v:
                return False
        fp = rec[9]
        if fp == 1:
            return self.mode_allowed(cls, 4)
        if fp == 2:
            if self.valid(cls):
                if self.ms[cls][0x0C] & 2:
                    return False
                if self.ms[cls][0x0E] & 2:
                    return False
            return True
        if fp == 3:
            return self.mode_allowed(cls, 2)
        return True

    # --- the two picks -----------------------------------------------------------------------------------------
    def pick(self, seed, diff, exp, cls, champion, have=None):
        """ChampionModPick (champion=True) or UniqueModPick. Returns (row or 0, record)."""
        off = (0x0E if champion else 0x14) + 2 * diff
        cands, total, isa_log = [], 0, []
        for r in range(len(self.mu)):
            w = self.mu_s16(r, off)
            if w <= 0:
                continue
            if (self.mu[r][8] != 0) != champion:
                continue
            if not self.eligible(r, exp, cls, isa_log):
                continue
            if not champion and have is not None and r in have:
                continue
            total += w
            cands.append((r, w))
            if len(cands) >= 256:
                break
        x = seed.rangeb(total)
        res, rest = 0, x
        for r, w in cands:
            if rest < w:
                res = r
                break
            rest -= w
        return res, {"kind": "champion" if champion else "unique", "cands": cands, "total": total, "x": x,
                     "res": res, "isa": isa_log, "us": seed.t()}

    # --- SpecialModsRoll ---------------------------------------------------------------------------------------
    def mods_roll(self, seed, mods, diff, exp, cls, allow, hook=None):
        """sub_005A0760_SpecialModsRoll. mods: the 9-byte list (changed in place). Returns a record of the draws.
        hook("r100", r), if given, is called right after the champion roll (the checker reads its log line there)."""
        out = {"r100": None, "champion": False, "picks": [], "skipped": False}
        k = mod_count(mods)
        if diff >= 3 or k >= 8:
            out["skipped"] = True
            return out
        if allow:
            r = seed.rangeb(100)
            out["r100"] = r
            if hook:
                hook("r100", r)
            if r < self.constants(0):
                out["champion"] = True
                m, rec = self.pick(seed, diff, exp, cls, True)
                out["picks"].append(rec)
                if m and k < 9:
                    mods[k] = m
                return out
        seed.rangeb(1)
        n = 1 + diff
        if k + n >= 9:
            n = 9 - k
        have = set(mods[:k])
        while n > 0:
            m, rec = self.pick(seed, diff, exp, cls, False, have)
            out["picks"].append(rec)
            if m == 0:
                break
            mods[k] = m
            k += 1
            have.add(m)
            n -= 1
        return out

    # --- handlers ----------------------------------------------------------------------------------------------
    def handler_seq(self, mods, every=False):
        """The mods whose server handler SpecialModsApply calls (flag 1), in call order (every=True: also the mods
        with no handler)."""
        seq = [m for m in self.always if every or (0 <= m < len(self.handler) and self.handler[m])]
        for m in mods[:9]:
            if m == 0:
                break
            if every or (0 <= m < len(self.handler) and self.handler[m]):
                seq.append(m)
        return seq

    def aura(self, name_seed, level, su_id):
        """sub_005A1650_UModAura's draw: (n, index before the override, index)."""
        lvl = level if level > 0 else 1
        n = sum(1 for row in self.aura_rows if not row[0] > lvl)
        if n == 0:
            n = 1
        s = Seed((name_seed & 0xFFFF, INIT_HIGH))
        r = s.rangeb(n)
        return n, r, (5 if su_id == SU_LORD_DE_SEIS else r)

    # --- client name -------------------------------------------------------------------------------------------
    def name_roll(self, name_seed):
        """The client roll of sub_004AC870_ClientMonNameBuild: list of (kind, value). The server sends the 16-bit name
        seed, but the client's monster-assign reader keeps its low byte (movzx cx, al at 0x0045F387), so the roll
        runs on Init(nameSeed & 0xFF)."""
        s = Seed((client_name_seed(name_seed), INIT_HIGH))
        out = [("S", s.rangeb(self.n_suffix)), ("P", s.rangeb(self.n_prefix))]
        r = s.rangeb(100)
        out.append(("R", r))
        if r < 50:
            out += [("A", s.rangeb(self.n_app)), ("S", s.rangeb(self.n_suffix)), ("P", s.rangeb(self.n_prefix))]
        return out


def post_create_mods(d, cls):
    """sub_005B21B0_MonPostCreateMods, by the class's MonStats BaseId (+0x02): the mods appended after every MonSpawnTry
    creation (ModAppendApply with flag 0, or 1 for questcomplete 22, which also marks the unit special). None of these
    mods has a server handler, so they draw nothing."""
    if not d.valid(cls):
        return []
    b = d.ms_s16(cls, 0x02)
    if not 0 <= b < len(d.ms):
        b = cls
    if b in (0x162,) or 0x146 <= b <= 0x14A:
        return [14]                          # spcdamage (traps)
    if b == 0x1B4:
        return [34]
    if b == 0x1CD:
        return [33]
    if b == 0x1F5:
        return [35]
    if 0x21C <= b <= 0x21E:
        return [22]                          # ancientbarb1..3
    if 0x154 <= b <= 0x157:
        return [15]                          # boneprison1..4
    if b == 0x60:
        return [10]                          # mummy1: poisondead
    if b == 0x18:
        return [13]                          # brute2: rage
    if b == 0x5B:
        return [20]                          # scarab1: scarab
    if b == 0xD3:
        return [11, 22]                      # duriel
    return []


def client_name_seed(name_seed):
    """sub_0045F190 (client monster assign): BITBUF_ReadUnsigned(16), then only the low byte is kept (0x0045F387)."""
    return name_seed & 0xFF


def mod_count(mods):
    """sub_005A0260_ModCount: mods up to the first 0, at most 9."""
    for i in range(9):
        if mods[i] == 0:
            return i
    return 9


def mod_append(mods, m):
    """sub_005A02E0_ModAppend: the first free slot, none if 9 are used (writes 0 too)."""
    k = mod_count(mods)
    if k < 9:
        mods[k] = m


def xfer_copy(d, dst, src):
    """sub_005A0930_ModsXferCopy(dst = minion, src = boss, overwrite 0)."""
    out = list(dst)
    k = mod_count(out)          # EDX: counts the boss mods examined, from the minion's count
    w = k                       # ESI: the next slot written
    j = 0
    while k < 9:
        m = src[j]
        if m == 0:
            break
        if d.xfer(m):
            out[w] = m
            w += 1
        k += 1
        j += 1
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    d = Data()
    if argv[1] == "isa":
        print(d.isa(int(argv[2]), int(argv[3])))
        return 0
    if argv[1] == "name":
        print(d.name_roll(int(argv[2], 0)))
        return 0
    if argv[1] == "roll":
        lo, hi = (int(v, 16) for v in argv[2].split(":"))

        def opt(name, default):
            return int(argv[argv.index(name) + 1]) if name in argv else default
        mods = [0] * 9
        if "--mods" in argv:
            for i, v in enumerate(argv[argv.index("--mods") + 1].split(",")):
                mods[i] = int(v)
        s = Seed((lo, hi))
        out = d.mods_roll(s, mods, opt("--diff", 0), opt("--exp", 1), opt("--cls", 0), opt("--allow", 1))
        print(out["r100"], out["champion"], [(p["res"], p["x"], p["total"]) for p in out["picks"]], mods,
              "%08x:%08x" % s.t())
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
