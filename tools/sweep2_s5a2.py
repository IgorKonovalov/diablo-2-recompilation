"""Plan 0066 Phase 1, batch S5a part 2: new models over the kept combat logs (run:2026-10-16-combat with its resume
lanes, run:2026-10-20-shortfalls p47h and run:2026-10-21-shortfalls2 p47b), on top of tools/sweep2_s5a.py (part 1,
whose counters and checks run unchanged and are printed again).

Usage:
  python3 -I tools/sweep2_s5a2.py <list> [...] [--no-shield-log N,...]   # the run lists, as sweep2_s5a.py combat

Every event the Checker of tools/combat.py accepts (its mismatches are reported first and must be 0) gets the part-1
counters, then the part-2 models; a model line reads `CHECK <name> ok=<n> bad=<n>`, a counter `COUNT <name> | <key> | <n>`.
The run ends with `S5a2 total bad=<n>`.

Part-2 models (the inventory rows each serves, combat-<spec>.md row numbers):
  * mas-stats    sub_005A4F50_MonAttackStats' writes (r2 read of 0x005A4F50-0x005A5443, kept in
                 workspace/logs/n66j/p2/): MonLvlStats(class, L, d, stat 12, mask 0x10 mode 5 / 0x20 modes 7, 8 /
                 0x08 others) -> to-hit TH*thc/100 and damage DM*min/max/100 (MulDiv; the raw cells for noRatio); the
                 owner skill-damage pair (classes with a MonStats SkillDamage: not modelled, counted); classic
                 (game +0x70 = 0) with d > 0 and Align != 1: damage tdiv(10x, 12), to-hit tdiv(10x, 15); expansion:
                 b = PlayerDmgBonus(game, max(stat 100, 1)) when UnitAlignGet(unit) = 0 (0 for d = 0 or n < 2,
                 table 0x006E21F4 = 0,0,8,..,56 for n < 9, else 8n - 16), x += tdiv(x*b, 128) on 21, 22, 19 and on
                 the El block's min, max and length; then per El<e> whose mode equals the mode passed and percent
                 is non-zero (below 100: one Range(seed, 100) that must be below it), El1's min/max/length
                 (mask 0x40 + e), type 10 a Range(seed, 5) + 1 and length 25 when 0, the type's stats written.
                 Compared on the MAS1 stats 19, 21, 22 and every El stat (damage 1, 29, 30, 33; README 35, 38;
                 player/party 12). Separation counters: the classic factors, b, the column set, L.
  * mas-el       the El stats written, for units whose first logged call held no El stat (another list, such as an
                 enchanted unique's minion's, adds to the same stats) and not hirelings (damage 33).
                 A hireling's 19/21/22 are checked against an offset learned at its first call (its MonStats cells
                 give 0; its Hireling.txt list adds the rest). A counter: the MAS0 mode against the attacker's mode
                 at its next EV0 (damage 30; other mode changes may come between, so not a check).
  * du-steps     COMBAT_DurabilityLoss (items/economy H1-H2): the attacker's seed steps once for a player
                 attacker, never for a monster; the defender's seed steps 3 times for a player defender
                 (RangeB(7), RangeB(W), the roll), never for a monster or a hireling (README 15; delivery 57); the
                 one 0x005CAED8 (mode-14) attack on the player is counted apart.
  * gh-steps     COMBAT_GetHit's draws on a player defender = sub_0057CB00_GetHitRoll's (anim/timing M1-M2): 0
                 unless the result has 0x1 and 0x4 and none of the earlier-returning bits 0x80, 0x100, 0x200, 0x10,
                 0x8000, 0x2, 0x8; then no draw when poison = total or total < 0x100, else bands by hp / D (stat 7 at
                 the outer AD1) with D from the hit class (an element nibble, or 0x10 for a doubled hit, gives 16;
                 else the low nibble: the attacker's MonStats2 HitClass for a melee hit, the packet's own for a
                 missile), RangePow2(2) then RangePow2(4) (README 15; delivery 57).
  * gh-steps-monster-not-more  a monster or hireling defender: states 1, 21, 54 (no-draw tests) are not logged, so the
                 logged steps are compared one way (never more than the model); a kill (UnitKilled) and a GetHit with
                 no delivery (0x005A54F0 runs first, unread) are counted only.
  * res-bits     result word at AD0/AD1 against what the logs show: 0x1 with THR r < c (melee) and a delivery,
                 0x2 with the defender's life 0 at AD1, 0x4 only on a hit, 0x2000 counted by build (README 5).
  * build-once   flag 0x2 at BD0 (SKILL_AttackDo's built packet): one BD0 per event, as flag 0 (README 5).
  * manahit-loss a monster attacker with stat 62 >= 256 (UModManaHit's x256), its hit on the player with no
                 handler in the delivery: mana at AD1 = AD0 mana - the packet's mana field (0 below 256); a counter
                 of the events where the v reading (field / 256) would give another result (delivery 28).
Stdlib only. Read-only.
"""
import collections
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import combat as C  # noqa: E402
import sweep2_s5a as P1  # noqa: E402
from excel_bin import find_file, read_bin  # noqa: E402
from monstats import muldiv, tdiv  # noqa: E402

ROOT = os.path.dirname(HERE)
HIRE = C.HIRE
PDB = [0, 0, 8, 16, 24, 32, 40, 48, 56]          # data 0x006E21F4, r2 px (n = 0..8)
MAS_EL = {1: ((48, "mn"), (49, "mx")), 2: ((50, "mn"), (51, "mx")), 3: ((52, "mn"), (53, "mx")),
          4: ((54, "mn"), (55, "mx"), (56, "dur")), 5: ((57, "mn10"), (58, "mx10"), (59, "dur2")),
          6: ((60, "mn"), (61, "mx")), 7: ((62, "mn"), (63, "mx")), 8: ((64, "mn"), (65, "mx")),
          9: ((66, "dur"),), 11: ((316, "mn"), (317, "mx"), (315, "dur"))}
EL_STATS = sorted({sid for v in MAS_EL.values() for sid, _ in v})


def s32b(b, off):
    return int.from_bytes(b[off:off + 4], "little", signed=True)


def player_bonus(d, n):
    """sub_005A4F20_PlayerDmgBonus (r2): 0 for game +0x6D (d) = 0 or n < 2; table for n < 9; else 8n - 16."""
    if d == 0 or n < 2:
        return 0
    return PDB[n] if n < 9 else 8 * n - 16


def addb(x, b):
    return x + tdiv(x * b, 128) if b else x


class S5b(P1.S5):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        ex = C.DEFAULT_EXCEL
        self.ml = read_bin(find_file(ex, "monlvl", ".bin"))[0]
        self.m2 = read_bin(find_file(ex, "monstats2", ".bin"))[0]
        self.chk2 = collections.defaultdict(lambda: [0, 0])
        self.cnt2 = collections.Counter()
        self.bad2 = []
        self.nbad2 = collections.Counter()
        self.pend_mode = {}
        self.mas_off = {}
        self.el_other = {}
        self.stun_until, self.cold_until = {}, {}
        self.ghfit = collections.defaultdict(lambda: collections.Counter())   # (log, attacker class) -> D -> ok
        self.ghfit_n = collections.Counter()

    def run(self, path):
        self.pend_mode = {}
        self.stun_until, self.cold_until = {}, {}
        return super().run(path)

    def ck2(self, name, ok, why=""):
        self.chk2[name][0 if ok else 1] += 1
        self.nbad2[name] += 0 if ok else 1
        if not ok and self.nbad2[name] <= 15:
            self.bad2.append("%s %s %s" % (name, self._log, why))
        return ok

    def c2(self, name, key, n=1):
        self.cnt2[(name, str(key))] += n

    # ------------------------------------------------------------------ MonAttackStats output model
    def ms16(self, cls, off):
        return struct.unpack_from("<h", self.T.ms[cls], off)[0]

    def mas_model(self, cls, lvl, d, L, mode, seed, exp, n, align0=True):
        """-> ({stat: value}, seed after, notes) for one MonAttackStats call (module docstring)."""
        r = self.T.ms[cls]
        notes = []
        d = 0 if d < 1 else min(d, 2)
        nml = len(self.ml)
        row = self.ml[lvl] if 0 <= lvl < nml else None
        r32 = lambda off: struct.unpack_from("<i", row, off)[0] if row is not None else 0  # noqa: E731
        noratio = bool(r[0x0C] & 0x04)
        th_o = 0x18 + 0xC * L + 4 * d
        dm_o = 0x48 + 0xC * L + 4 * d
        if mode == 5:
            cth, cmn, cmx = 0xC8, 0xE6, 0xEC
        elif 7 <= mode <= 8:
            cth, cmn, cmx = 0xCE, 0xF2, 0xF8
        else:
            cth, cmn, cmx = 0xC2, 0xDA, 0xE0
        cell = lambda off: self.ms16(cls, off + 2 * d)  # noqa: E731
        if row is None:
            th = mn = mx = 0
        elif noratio:
            th, mn, mx = cell(cth), cell(cmn), cell(cmx)
        else:
            th, mn, mx = (muldiv(r32(th_o), cell(cth), 100), muldiv(r32(dm_o), cell(cmn), 100),
                          muldiv(r32(dm_o), cell(cmx), 100))
        b = player_bonus(d, max(n, 1)) if (exp and align0) else 0
        if not exp:
            if d and r[0x4C] != 1:
                notes.append("classic factors")
                mn, mx, th = tdiv(mn * 10, 12), tdiv(mx * 10, 12), tdiv(th * 10, 15)
        elif b:
            notes.append("b=%d" % b)
            mn, mx, th = addb(mn, b), addb(mx, b), addb(th, b)
        w = {21: mn, 22: mx, 19: th}
        t = seed
        for e in range(3):
            em = r[0xFE + e]
            if not em or em != mode:
                continue
            pct = r[0x104 + d + 3 * e]
            if not pct:
                continue
            if pct < 100:
                t = C.step(t)
                if t[0] % 100 >= pct:
                    continue
            if row is None:
                emn = emx = edur = 0
            else:
                edur = self.ms16(cls, 0x132 + 2 * d)
                if noratio:
                    emn = emx = 0
                else:
                    emn = muldiv(r32(dm_o), self.ms16(cls, 0x10E + 2 * d), 100)
                    emx = muldiv(r32(dm_o), self.ms16(cls, 0x120 + 2 * d), 100)
            if b:
                emn, emx, edur = addb(emn, b), addb(emx, b), addb(edur, b)
            typ = r[0x101 + e]
            if typ == 10:
                t = C.step(t)
                typ = t[0] % 5 + 1
                if edur == 0:
                    edur = 25
            for sid, how in MAS_EL.get(typ, ()):
                w[sid] = {"mn": emn, "mx": emx, "dur": edur, "mn10": emn * 10, "mx10": emx * 10,
                          "dur2": edur * 2}[how]
            if e and row is not None and not noratio:
                own = (muldiv(r32(dm_o), self.ms16(cls, 0x10E + 6 * e + 2 * d), 100),
                       muldiv(r32(dm_o), self.ms16(cls, 0x120 + 6 * e + 2 * d), 100),
                       self.ms16(cls, 0x132 + 6 * e + 2 * d))
                el1 = (muldiv(r32(dm_o), self.ms16(cls, 0x10E + 2 * d), 100),
                       muldiv(r32(dm_o), self.ms16(cls, 0x120 + 2 * d), 100), self.ms16(cls, 0x132 + 2 * d))
                notes.append("el%d own cells %s El1's" % (e + 1, "differ from" if own != el1 else "equal"))
            notes.append("el%d applied type %d" % (e + 1, typ))
        return w, t, notes

    def mas(self, ev):
        s = super().mas(ev)              # the Checker's seed model (a Mismatch propagates as before)
        try:
            self.mas2(ev)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            self.c2("mas-error", type(e).__name__)
        return s

    def mas2(self, ev):
        u, mode, g = ev.head["u"], ev.head["mode"], ev.head["g"] or {"diff": 0, "exp": 1}
        cls = u["c"]
        st0 = u.get("st") or {}
        st1 = ev.lines[-1][1].get("st") or {}
        self.pend_mode[u["u"]] = (mode, u.get("m"))
        self.c2("MAS0 mode (old mode)", "%d (%s)" % (mode, u.get("m")))
        if not st0 and not st1:
            self.c2("mas no stat list", 1)
            return
        if struct.unpack_from("<H", self.T.ms[cls], 0xA8)[0] != 0xFFFF:
            self.c2("mas skill-damage class (pair not modelled)", cls)
            return
        d, exp = g.get("diff", 0), g.get("exp", 1)
        lvl = st0.get("12", 0)
        n = st0.get("100", 0)
        ahire = cls in HIRE
        seed = C.sd_parse(u["s"])
        want, t, notes = self.mas_model(cls, lvl, d, 1, mode, seed, exp, n, align0=not ahire)
        got = {sid: st1.get(str(sid), 0) for sid in want}
        if ahire:
            # a hireling's MonStats cells are 0 here; its own lists (Hireling.txt) add to the same stats: the offset
            # (logged - written) is learned at its first call and must stay the same (as tools/skills.py's summons)
            ukey = (self._log, u["u"])
            off = self.mas_off.get(ukey)
            if off is None:
                self.mas_off[ukey] = {sid: got_ - want.get(sid, 0) for sid, got_ in
                                      ((sid, st1.get(str(sid), 0)) for sid in want)}
                self.c2("mas hireling: offset learned at its first call", cls)
                return
            want = {sid: v + off.get(sid, 0) for sid, v in want.items()}
            self.c2("mas hireling checked with its learned offset", cls)
        # El stats: another list may hold them too (an enchanted unique's minion: 50/51 before any call); compared
        # only for units whose first logged call showed no El stat at all
        ukey = (self._log, u["u"])
        if ukey not in self.el_other:
            self.el_other[ukey] = any(st0.get(str(sid), 0) for sid in EL_STATS)
        elw = {sid: v for sid, v in want.items() if sid not in (19, 21, 22)}
        if elw:
            if self.el_other[ukey] or ahire:
                self.c2("mas El written, unit with El stats from another list (not compared)", cls)
            else:
                self.ck2("mas-el", all(got[sid] == v for sid, v in elw.items()), "cls %d mode %d d %d: want %s got %s"
                         % (cls, mode, d, elw, {sid: got[sid] for sid in elw}))
        want = {sid: want[sid] for sid in (19, 21, 22)}
        got = {sid: got[sid] for sid in want}
        okk = self.ck2("mas-stats", got == want, "cls %d lvl %d mode %d d %d exp %d n %d hire %s: want %s got %s" % (
            cls, lvl, mode, d, exp, n, ahire, want, got))
        # the El stats the call did not write: 0 after the clear, unless another list holds them
        unw = {sid: st1.get(str(sid), 0) for sid in EL_STATS if sid not in want and st1.get(str(sid), 0)}
        self.c2("mas unwritten El stat non-zero after the call", bool(unw))
        if not okk:
            self.c2("mas-stats bad by class/mode", "%d/%d d%d e%d" % (cls, mode, d, exp))
            return
        key = "d%d e%d n%d%s" % (d, exp, max(n, 1), " hire" if ahire else "")
        self.c2("mas-stats ok by diff/exp/players", key)
        if not exp and d:
            self.c2("mas classic nightmare/hell call by MonStats Align (+0x4C)", self.T.ms[cls][0x4C])
        if any(k.startswith("b=") for k in notes) and elw and not (self.el_other[ukey] or ahire):
            alt0, _, _ = self.mas_model(cls, lvl, d, 1, mode, seed, exp, 1)
            self.c2("mas El applied and compared with b > 0 (separates from b = 0 on the El stats)", "%s %s" % (
                [k for k in notes if k.startswith("b=")][0], any(alt0.get(sid) != v for sid, v in elw.items())))
        if any("own cells" in k for k in notes):
            self.c2("mas El2/El3 applied: own cells against El1's, compared", "%s %s" % (
                [k for k in notes if "own cells" in k][0], "compared" if elw and not (self.el_other[ukey] or ahire)
                else "not compared"))
        for k in notes:
            if "own cells" not in k:
                self.c2("mas notes", k.split(" type")[0] if k.startswith("el") else k)
            if k.startswith("el") and " applied type " in k:
                self.c2("mas El applied: type", k.split("type ")[1])
        # separation (review-fix 10): would the other reading give other values on this call?
        base = {k2: want[k2] for k2 in (19, 21, 22)}
        if not exp and d:
            alt, _, _ = self.mas_model(cls, lvl, d, 1, mode, seed, 1, 1)
            self.c2("mas sep: classic factors (vs none)", {k2: alt[k2] for k2 in base} != base)
            alt2 = dict(alt)
            # each factor alone reversed
            th0 = alt[19]
            self.c2("mas sep: classic to-hit 10/15 (vs 10/12)", tdiv(th0 * 10, 12) != want[19])
            self.c2("mas sep: classic damage 10/12 (vs 10/15)", (tdiv(alt2[21] * 10, 15), tdiv(alt2[22] * 10, 15))
                    != (want[21], want[22]))
        if exp and d and max(n, 1) >= 2:
            alt, _, _ = self.mas_model(cls, lvl, d, 1, mode, seed, exp, 1, align0=not ahire)
            sep = {k2: alt[k2] for k2 in base} != base
            self.c2("mas sep: player bonus b (vs b = 0)", "%s n%d%s" % (sep, max(n, 1), " hire" if ahire else ""))
            if not ahire:
                for dn in (-1, 1):
                    if 1 <= n + dn:
                        alt, _, _ = self.mas_model(cls, lvl, d, 1, mode, seed, exp, n + dn)
                        self.c2("mas sep: b at n%+d" % dn, {k2: alt[k2] for k2 in base} != base)
                # the b reading of n >= 9 against 8(n - 1)
                if n >= 9:
                    self.c2("mas n >= 9 (8n - 16 vs 8(n - 1) separates)", "n%d" % n)
        if exp and not d and n >= 2 and not ahire:
            # the d = 0 test of PlayerDmgBonus: the bonus the same n would give in nightmare
            bb = player_bonus(1, n)
            self.c2("mas sep: normal with n >= 2, b = 0 (vs b of n)", "%s n%d" % (
                any(addb(v, bb) != v for v in base.values()), n))
        if exp and d and max(n, 1) < 2:
            self.c2("mas b = 0 (one player) in nightmare/hell", "d%d" % d)
        cols = {}
        for mm in (4, 5, 7):
            alt, _, _ = self.mas_model(cls, lvl, d, 1, mm, seed, exp, n, align0=not ahire)
            cols[mm] = {k2: alt[k2] for k2 in base}
        mine = 5 if mode == 5 else 7 if mode in (7, 8) else 4
        self.c2("mas sep: column set (another set differs)", any(cols[mm] != base for mm in cols if mm != mine))
        if not ahire:
            altL, _, _ = self.mas_model(cls, lvl, d, 0, mode, seed, exp, n, align0=True)
            self.c2("mas sep: L columns (vs plain)", {k2: altL[k2] for k2 in base} != base)
        # an El group of another mode: its stats would differ from the written ones
        r = self.T.ms[cls]
        for e in range(3):
            em, pct = r[0xFE + e], r[0x104 + min(max(d, 0), 2) + 3 * e]
            if em and pct and em != mode:
                self.c2("mas El group of another mode not applied (its type's stats)",
                        "type %d: %s" % (r[0x101 + e], all(got.get(sid, 0) == 0 for sid, _ in
                                                            MAS_EL.get(r[0x101 + e], ())) or
                                         any(sid in want for sid, _ in MAS_EL.get(r[0x101 + e], ()))))

    # ------------------------------------------------------------------ per-event models
    def post(self, ev, missile):
        super().post(ev, missile)
        try:
            self.post2(ev, missile)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            self.c2("post2-error", "%s %s" % (type(e).__name__, e))

    def base_hc(self, a):
        """sub_00623C20_UnitBaseHitClass for a monster: MonStats2 HitClass (+0x014) of MonStatsEx (+0x018)."""
        ex = struct.unpack_from("<h", self.T.ms[a["c"]], 0x18)[0]
        return self.m2[ex][0x14] if 0 <= ex < len(self.m2) else None

    @staticmethod
    def gh_divisor(hc):
        hc &= 0xFFFFFFFF
        return 8 if hc in (2, 6, 10, 11) else 32 if hc in (4, 8) else 64 if hc == 5 else 16

    @staticmethod
    def ghr_steps(seed, total, poison, hp, D):
        """sub_0057CB00_GetHitRoll's draws (anim/timing M2): -> (steps, returns 0 = get hit)."""
        if (poison != 0 and poison == total) or total < 0x100:
            return 0, 1
        if total < tdiv(hp, D):
            return 0, 1
        t, k = seed, 0
        if total < tdiv(hp, tdiv(D, 2)):
            t = C.step(t)
            k += 1
            if t[0] & 1 == 0:
                return k, 1
        if total < tdiv(hp, tdiv(D, 4)):
            t = C.step(t)
            k += 1
            if t[0] & 3 == 0:
                return k, 1
        return k, 0

    def post2(self, ev, missile):
        h, L = ev.head, ev.lines
        k = ev.kind
        g = h["g"]
        a = h.get("o") if missile else h["a"]
        d = h["d"]
        tags = [t for t, _ in L]
        dhire = d["t"] == 1 and d["c"] in HIRE
        ahire = a["t"] == 1 and a["c"] in HIRE
        # --- MAS mode against the attack's mode (damage 30) ---
        if not missile and a["t"] == 1 and a["u"] in self.pend_mode:
            mm, old = self.pend_mode.pop(a["u"])
            self.c2("mas mode against the attacker's mode at its next EV0 (a counter: other mode changes may come "
                    "between)", "same" if mm == a.get("m") else "MAS %d EV0 %s" % (mm, a.get("m")))
            self.c2("mas-newmode: MAS0 old mode differs from the new", "%s" % (old != mm))
        ad0 = next((x for t, x in L if t == "AD0"), None)
        # the outer delivery's AD1 is the last one (a stat-event handler may deliver a nested packet first)
        ad1 = next((x for t, x in reversed(L) if t == "AD1"), None)
        # --- README 5: one build per event, by BD0 flag 0x2 ---
        bds = [x for t, x in L if t == "BD0"]
        if bds:
            f0 = s32b(bytes.fromhex(bds[0]["p"]), 0)
            self.ck2("build-once", len(bds) == 1, "%s %d builds" % (k, len(bds)))
            self.c2("BD0 flag 0x2 by kind", "%s 0x2=%s" % (k, bool(f0 & 2)))
        # --- README 5: result bits ---
        thr = next((x for t, x in L if t == "THR"), None)
        if ad0 is not None:
            res0 = s32b(bytes.fromhex(ad0["p"]), 4) & 0xFFFF
            if thr is not None and not missile:
                self.ck2("res-0x1-hit", bool(res0 & 1) == (thr["r"] < thr["c"]), "res 0x%x r %d c %d" % (
                    res0, thr["r"], thr["c"]))
            if ad1 is not None:
                res1 = s32b(bytes.fromhex(ad1["p"]), 4) & 0xFFFF
                self.c2("result bits AD0 -> AD1", "0x%04x -> 0x%04x" % (res0, res1))
                if "ld" in ad1:
                    self.ck2("res-0x2-killed", bool(res1 & 2) == (ad1["ld"][0] <= 0) or not (res1 & 1),
                             "res 0x%x life %d" % (res1, ad1["ld"][0]))
                    self.c2("res 0x2 with life 0 at AD1 (separating both ways)", "%s %s" % (
                        bool(res1 & 2), ad1["ld"][0] <= 0))
                self.ck2("res-0x4-on-hit", not (res1 & 4) or (res1 & 1), "res 0x%x" % res1)
        # --- DU (README 15; delivery 57) ---
        for idx, (t, x) in enumerate(L):
            if t != "DU0":
                continue
            y = next((z for u, z in L[idx + 1:] if u == "DU1"), None)
            if y is None:
                continue
            na = C.steps_between(C.sd_parse(x["sa"]), C.sd_parse(y["sa"]), 64)
            nd = C.steps_between(C.sd_parse(x["sd"]), C.sd_parse(y["sd"]), 64)
            wa = 1 if a["t"] == 0 else 0
            wd = 3 if d["t"] == 0 else 0
            role = "%s->%s" % ("player" if a["t"] == 0 else "hireling" if ahire else "monster",
                               "player" if d["t"] == 0 else "hireling" if dhire else "monster")
            if d["t"] == 0 and h.get("ret") == 0x005CAED8:
                # the mode-14 attack's own delivery path (the sandraider2 case of combat/damage E): not modelled here
                self.c2("du monster->player from the 0x005CAED8 attack (excluded)", "%s %s" % (na, nd))
                continue
            self.ck2("du-steps", (na, nd) == (wa, wd), "%s %s: steps %s %s" % (k, role, na, nd))
            self.c2("du steps by role", "%s %s %s" % (role, na, nd))
            if d["t"] == 0:
                self.c2("du monster->player steps by attack return", "0x%08X %s" % (h.get("ret", 0), nd))
            self.c2("du missile event", missile)
        # --- GH (README 15; delivery 57) ---
        for idx, (t, x) in enumerate(L):
            if t != "GH0":
                continue
            y = next((z for u, z in L[idx + 1:] if u == "GH1"), None)
            if y is None:
                continue
            sd0 = C.sd_parse(x["sd"])
            nd = C.steps_between(sd0, C.sd_parse(y["sd"]), 64)
            dmon = d["t"] == 1
            src = next((z for u_, z in reversed(L[:idx]) if u_ == "AD1"), None) or next(
                (z for u_, z in reversed(L[:idx]) if u_ == "AD0"), None)
            if src is None:
                if dmon:
                    # a monster defender's GetHit first calls 0x005A54F0 (unread), before any result test
                    self.c2("gh monster defender, no delivery: steps", nd)
                    continue
                self.ck2("gh-steps", nd == 0, "%s no delivery: %s" % (k, nd))
                self.c2("gh no delivery (miss or no AD)", "steps %s" % nd)
                continue
            p = bytes.fromhex(src["p"])
            res = s32b(p, 4) & 0xFFFF
            if dmon and res & 2:
                self.c2("gh monster killed (UnitKilled boundary)", "steps>0 %s" % bool(nd))
                continue
            early = res & (0x80 | 0x100 | 0x200 | 0x10 | 0x8000 | 0x2 | 0x8) if not dmon else res & 0x10
            if not (res & 1) or not (res & 4) or early:
                if dmon:
                    self.c2("gh monster defender, no GetHitRoll by result: steps", "0x%04x %s" % (res, nd))
                    self.ck2("gh-steps-monster-not-more", nd == 0, "%s res 0x%x: %s" % (k, res, nd))
                    continue
                self.ck2("gh-steps", nd == 0, "%s res 0x%x: %s" % (k, res, nd))
                self.c2("gh no GetHitRoll by result", "%s 0x%04x steps %s" % ("mon" if dmon else "plr", res, nd))
                continue
            total, poison = s32b(p, C.F_TOTAL), s32b(p, C.F_POIS)
            hp = (src.get("ld") or [0, 0])[1]
            hc = s32b(p, 0x60)
            nib_set = bool(hc & 0xF0)
            if not p[0x64] and not nib_set:
                el = any(s32b(p, o) > 0 for o in (C.F_COLD, C.F_FIRE, C.F_LIGHT, C.F_POIS))
                if el or res & 0x2000:
                    nib_set = True
            low = hc & 0xF
            fitted = False
            if not nib_set and not missile and not p[0x64] and low == 0:
                if a["t"] == 1:
                    low = self.base_hc(a) or 0
                else:
                    fitted = True
            if nib_set or low == 0 and not fitted:
                Ds = [16]
            elif fitted:
                Ds = [8, 16, 32, 64]
            else:
                Ds = [self.gh_divisor(low)]
            outs = {D: self.ghr_steps(sd0, total, poison, hp, D)[0] for D in Ds}
            if fitted:
                key = (self._log, a["c"])
                for D, n_ in outs.items():
                    self.ghfit[key][D] += (n_ == nd)
                self.ghfit_n[key] += 1
                self.c2("gh player melee hit, divisor fitted per log", 1)
                continue
            D = Ds[0]
            if dmon:
                # a monster or hireling defender: states 1, 21 and 54 (no-draw tests) are not in these logs, so the
                # model can only be compared one way: the logged steps are never more than GetHitRoll's
                rel = "equal" if outs[D] == nd else "fewer" if nd is not None and nd < outs[D] else "more"
                self.c2("gh monster/hireling defender: logged steps against GetHitRoll's", "%s (model %d)" % (
                    rel, outs[D]))
                self.ck2("gh-steps-monster-not-more", rel != "more", "%s res 0x%x: want %d got %s" % (
                    k, res, outs[D], nd))
                if rel == "fewer":
                    fr = g["frame"]
                    stn = self.stun_until.get(d["u"])
                    self.c2("gh monster fewer: stunned by a logged packet / cold length running", "%s %s" % (
                        stn is not None and stn[0] <= fr <= stn[1], self.cold_until.get(d["u"], -1) >= fr))
                continue
            ok = self.ck2("gh-steps", outs[D] == nd, "%s res 0x%x total %d hp %d D %d hc 0x%x: want %d got %s" % (
                k, res, total, hp, D, hc, outs[D], nd))
            if not ok:
                fr = g["frame"]
                stn = self.stun_until.get(d["u"])
                self.c2("gh-steps bad: defender stunned by a logged packet (stunLen) / cold length", "%s %s" % (
                    stn is not None and stn[0] <= fr <= stn[1], self.cold_until.get(d["u"], -1) >= fr))
                self.c2("gh-steps bad: defender class/mode", "%s/%s" % (d["c"], d.get("m")))
                self.c2("gh-steps bad by kind/def/res/want/got", "%s %s 0x%04x hc 0x%x want %d got %s" % (
                    k, "mon" if dmon else "plr", res, hc, outs[D], nd))
            if ok:
                self.c2("gh GetHitRoll steps ok", "%s D%d steps %d" % ("mon" if dmon else "plr", D, nd))
                # separation: the other divisors
                alt = {D2: self.ghr_steps(sd0, total, poison, hp, D2)[0] for D2 in (8, 16, 32)}
                self.c2("gh sep: another divisor gives other steps", any(v != nd for D2, v in alt.items() if D2 != D))
        # stun and cold lengths of the delivered packet, for the defender's later events (a proxy for states 21, 11)
        if src is not None if "src" in dir() else False:
            pass
        _src = ad1 if ad1 is not None else ad0
        if _src is not None:
            pp = bytes.fromhex(_src["p"])
            if s32b(pp, 4) & 1:
                fr = (ad0 or {}).get("fr", g["frame"])
                if s32b(pp, C.F_STUN) > 0:
                    self.stun_until[d["u"]] = (fr, fr + s32b(pp, C.F_STUN))
                if s32b(pp, C.F_CLEN) > 0 or s32b(pp, C.F_FLEN) > 0:
                    self.cold_until[d["u"]] = fr + max(s32b(pp, C.F_CLEN), s32b(pp, C.F_FLEN))
        # --- manahit (delivery 28) ---
        bd1 = next((x for t, x in L if t == "BD1"), None)
        st = a.get("st", {})
        if a["t"] == 1 and not ahire and bd1 is not None and st.get("62", 0) >= 256:
            b1 = bytes.fromhex(bd1["p"])
            mana = s32b(b1, C.F_MANA)
            src = next((x for t, x in L if t == "BD0"), {}).get("src") or 128
            lo, hi = (st.get("62", 0) * src) // 128, (st.get("63", 0) * src) // 128
            self.c2("manahit attacker builds", "hit=%s v=%d..%d" % (bool(s32b(b1, 4) & 1), st.get("62", 0) // 256,
                                                                     st.get("63", 0) // 256))
            if ad0 is not None and ad1 is not None and d["t"] == 0:
                pm = s32b(bytes.fromhex(ad0["p"]), C.F_MANA)
                m0, m1 = ad0["ld"][2], ad1["ld"][2]
                nested = any(t == "EVH" for t, _ in L[tags.index("AD0"):tags.index("AD1")])
                if not nested:
                    want = m0 - pm if pm else m0
                    want = 0 if want < 256 else want
                    self.ck2("manahit-loss", m1 == want, "mana %d - %d -> %d" % (m0, pm, m1))
                    # the two readings separate when the v reading (field / 256) would leave mana above the floor
                    vread = m0 - pm // 256
                    vread = 0 if vread < 256 else vread
                    self.c2("manahit on player: 256v reading (logged) against the v reading (field / 256)",
                            "separates=%s loss=all-held %s" % (vread != m1, m1 == 0))


def main(argv):
    lists, nsl = [], ()
    k = 0
    while k < len(argv):
        if argv[k] == "--no-shield-log":
            nsl, k = nsl + tuple(argv[k + 1].split(",")), k + 2
        else:
            lists.append(argv[k])
            k += 1
    if not lists:
        print(__doc__)
        return 2
    paths = []
    for lst in lists:
        for ln in open(lst):
            ln = ln.strip()
            if ln:
                paths.append(os.path.join(ROOT, ln) if not os.path.isabs(ln) else ln)
    S = S5b(C.Tables(), no_shield_logs=nsl)
    for p in paths:
        S.run(p)
    print("S5A2 combat logs %d, Checker mismatches %d" % (len(paths), len(S.mism)))
    for m in S.mism[:20]:
        print("CHECKER-MISMATCH " + m)
    for kind in sorted(S.cnt):
        print("EVENTS %s %s" % (kind, dict(sorted(S.cnt[kind].items()))))
    bad1 = sum(b for _, b in S.chk.values())
    print("PART1 checks bad=%d (sweep2_s5a.py's nine, unchanged)" % bad1)
    bad = 0
    for name in sorted(S.chk2):
        ok, b = S.chk2[name]
        bad += b
        print("CHECK %s ok=%d bad=%d" % (name, ok, b))
    for m in S.bad2:
        print("BAD " + m)
    for (name, key), n in sorted(S.cnt2.items()):
        print("COUNT %s | %s | %d" % (name, key, n))
    for key in sorted(S.ghfit, key=str):
        n = S.ghfit_n[key]
        fits = {D: c for D, c in sorted(S.ghfit[key].items())}
        print("GHFIT %s cls %d: %d hits, D -> matching %s" % (key[0], key[1], n, fits))
    print("S5a2 total bad=%d checker=%d part1-bad=%d" % (bad, len(S.mism), bad1))
    return 0 if bad == 0 and not S.mism and not bad1 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
