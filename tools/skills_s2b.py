"""Plan 0066 Phase 1, batch S2b: checks over the missile lines of the kept skills logs (run:2026-10-25-skills,
run:2026-10-27-skills, run:2026-10-30-skills-catalogue) for the (a-logs) statements of docs/specs/skills/missiles.md and
catalogue.md.

Usage:
  python3 -I tools/skills_s2b.py check <log> [...] [--excel DIR]

<log> is written by tools/d2run.py with tools/gdb/skills.gdb (tools/gdb/skills.py rev 3..5); tools/skills.py's parser
reads it. The tool prints counts, the cases that separate each reading, and every case that breaks a check ("break");
exit 0 only with no break. Read-only, stdlib only. tools/skills.py and tools/skills_s2a.py are imported, not changed.

The sections (the spec section each serves; skills/missiles unless named):
  FRAME  D2/D3, B1: the windowed missiles' frames (MF0 at 0x005ADC97, before the indexed do call; MF1 after it): the
         logged row number against Missiles pSrvDoFunc; a frame returning 1 followed by the missile's next frame; for
         do 1 the frames left, the hit calls nested in the frame (the frames left at an end call, at a unit hit
         against the activate mark), the frame's result against the nested end call's, the frames returning 2 with no
         hit call; per missile the frames run against the frames left at its creation (MC1).
  MH     E1: per MISSILE_HitUnit call (MH0..MH1) by kind: end calls (no unit) of rows without and with a hit function
         (a build directly in the call, the missile's seed across it, the result); unit calls of rows without a hit
         function (the order of THR, BD, MA directly in the call); unit calls of rows with a hit function against the
         table-only result (E1's formula without hitfn); a pierce used by a CollideKill row; the missile's stat 19 at
         the hit by owner type.
  DMG    catalogue entry points: the missile's seed from BD1 (the build's exit) to MA0 (MissileApplyAndAc's
         MISSILE_ApplyDamage entry) by the row's pSrvDmgFunc, and the packet's damage words BD1 -> AD0.
  MA     E3, I: MISSILE_ApplyDamage (MA0..MA1, a boundary): the missile's seed steps by the row's KnockBack (read
         as a byte at +0xAE, 0x005AD7CB); for KnockBack > 0, the roll Range(missile seed, 100) against the packet's
         +0x04 bit 3 at the AD0 inside; the DRR lines inside by unit.
  BDO    F1: per build with two or more draws, which pairs of the seven drew; per two drawn pairs, whether swapping
         their places in the draw order changes the packet (a separating build).
  MC     B2-B4, H2: SkillMissileCreate's creations from SKILLS_SrvDo's srvmissile (rows with no srvdofunc): flags,
         class, skill and level, the monster to-hit flag and value; the 0x1000 flag by owner type over every
         creation; Meteor's creations; the creation callbacks (MCB) inside MissileCreate; Firestorm's sub-missile
         arguments; Multiple Shot's creations group by group; the enclosing call of the class-408 creations.
  SKL    catalogue I4, J1, K2, R4: Amplify Damage's STA lines; Holy Fire's REL and AD lines; Bash's REL; the monster
         rows' caster steps per do event, against the nested creations' owner steps.
  OWN    I1: the owner's seed from a creation (MC1) to the to-hit roll (THR) of the same missile's hit, with the
         owner's seeds logged between (other creations, other rolls, its skill events).
"""
import os
import struct
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import skills as SK  # noqa: E402

M32 = 0xFFFFFFFF
EXIT = {"MC0": "MC1", "MH0": "MH1", "MA0": "MA1", "BD0": "BD1", "SDO0": "SDO1", "SST0": "SST1", "MCB0": "MCB1",
        "AD0": "AD1", "MAS0": "MAS1", "EVH": "EVR", "DQ0": "DQ1", "MHT0": "MHT1", "SP0": "SP1", "PF0": "PF1",
        "PAY0": "PAY1", "PH0": "PH1", "RSK0": "RSK1", "SL0": "SL1", "PA0": "PA1", "ARM0": "ARM1", "CU0": "CU1"}
# MISSILE_BuildDamage's pairs in the code's order (skills/0002 § 6; tools/skills.py BD_ROLLS)
BD_ROLLS = SK.Checker.BD_ROLLS
CB_FIRESTORM = 0x005C9290
CB_PATHX = 0x005AC040
SK_MSHOT, SK_AMP, SK_HOLYFIRE, SK_BASH, SK_FIRESTORM, SK_METEOR = 12, 66, 102, 126, 225, 56


def s16v(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


class Rows:
    def __init__(self, T):
        self.T = T

    def m(self, c):
        r = self.T.mi[c]
        h = lambda o: struct.unpack_from("<h", r, o)[0]  # noqa: E731
        return {"do": h(0x0C), "hit": h(0x0E), "dmg": h(0x10), "kb": r[0xAE], "ck": r[0x186], "expl": bool(r[4] & 2),
                "pierce": bool(r[4] & 4), "tohit": r[0x18B], "ae": r[0x18C], "lastcol": r[4] & 1}

    def hitfn(self, c):
        h = self.m(c)["hit"]
        return 0 < h < 71

    def dmgfn(self, c):
        h = self.m(c)["dmg"]
        return h if 0 < h < 31 else 0

    def sk(self, sid):
        r = self.T.sk[sid]
        return {"st": struct.unpack_from("<H", r, 0x2C)[0], "do": struct.unpack_from("<H", r, 0x2E)[0],
                "srvmissile": struct.unpack_from("<h", r, 0x46)[0], "lob": bool(r[4] & 2),
                "ats": struct.unpack_from("<h", r, 0x82)[0]}


def blkw(d, off, fmt="<i"):
    return struct.unpack_from(fmt, bytes.fromhex(d["p"]), off)[0]


class S2B:
    def __init__(self, T):
        self.T, self.R = T, Rows(T)
        self.c = defaultdict(Counter)
        self.breaks = []
        self.nbreak = Counter()
        self.ex = defaultdict(list)

    def bad(self, chk, log, n, msg):
        self.nbreak[chk] += 1
        if len(self.breaks) < 300:
            self.breaks.append("%s n=%s %s: %s" % (os.path.basename(log), n, chk, msg))

    # ------------------------------------------------------------------ structure
    def run(self, log):
        L = SK.parse(log)
        self.log = log
        self.fam = "cat" if "catalogue" in os.path.basename(log) else "run25" if "2026-10-25" in log else "run27"
        ex = {}
        for j, (t, d) in enumerate(L):
            if "k" in d and isinstance(d["k"], int) and t not in SK.AI_TAGS:
                ex[(t, d["k"])] = j
        self.L, self.exits = L, ex
        # each entry's exit index; the innermost open span at each line
        self.close = {}
        for i, (t, d) in enumerate(L):
            if t in EXIT and "n" in d:
                if t == "EVH":
                    continue
                j = ex.get((EXIT[t], d["n"]))
                if j is not None:
                    self.close[i] = j
        # EVH/EVR: a stack (EVR carries k too)
        for i, (t, d) in enumerate(L):
            if t == "EVH":
                j = ex.get(("EVR", d["n"]))
                if j is not None:
                    self.close[i] = j
        self.missiles(L)
        self.frames(L)
        self.hits(L)
        self.creations(L)
        self.skills(L)
        self.owner_chain(L)

    def direct(self, i):
        """the lines directly inside span i (nested spans skipped), as (index, tag, data)."""
        j = self.close[i]
        out = []
        k = i + 1
        while k < j:
            t, d = self.L[k]
            out.append((k, t, d))
            if k in self.close:
                k = self.close[k] + 1
            else:
                k += 1
        return out

    def missiles(self, L):
        """missile pointer -> its creation (class, owner type, MC0/MC1), the latest creation at each line."""
        self.mis = {}
        self.mis_at = {}
        for i, (t, d) in enumerate(L):
            if t == "MC0" and i in self.close:
                e = L[self.close[i]][1]
                m = e.get("m")
                if m:
                    self.mis_at[self.close[i]] = (m["u"], {"c": m["c"], "ot": (d.get("o") or {}).get("t"),
                                                           "o": (d.get("o") or {}).get("u"), "mc0": d, "mc1": e,
                                                           "i": i})

    # ------------------------------------------------------------------ FRAME
    def frames(self, L):
        C = self.c
        cur = {}
        openf = {}
        seq = defaultdict(list)          # missile pointer (per creation) -> [(MF0 index, MF1 index)]
        for i, (t, d) in enumerate(L):
            if i in self.mis_at:
                u, info = self.mis_at[i]
                cur[u] = (i, info)
            if t == "MF0":
                openf[d["m"]] = i
            elif t == "MF1" and d["m"] in openf:
                a = openf.pop(d["m"])
                if d["m"] in cur:
                    seq[cur[d["m"]][0]].append((a, i))
        for key, fr in seq.items():
            info = None
            for u, inf in [self.mis_at[key]]:
                info = inf
            c = info["c"]
            R = self.R.m(c)
            rem0 = (info["mc1"]["m"].get("md") or {}).get("rem")
            act = (info["mc1"]["m"].get("md") or {}).get("act")
            for a, b in fr:
                d0, d1 = L[a][1], L[b][1]
                if d0["do"] == R["do"]:
                    C["FRAME do = Missiles pSrvDoFunc, by do"][d0["do"]] += 1
                else:
                    self.bad("FRAME.do", self.log, d0["n"], "do %s row %s" % (d0["do"], R["do"]))
            # a result 1 is followed by the missile's next frame (or a free elsewhere, MFX)
            for q, (a, b) in enumerate(fr):
                r = L[b][1]["r"]
                if r == 1:
                    if q + 1 < len(fr):
                        nf = L[fr[q + 1][0]][1]["fr"]
                        C["FRAME result 1: next frame of the missile"]["frame + %d" % (nf - L[a][1]["fr"])] += 1
                    else:
                        mfx = any(t2 == "MFX" and d2["m"] == L[a][1]["m"] for t2, d2 in L[b + 1:b + 4000])
                        C["FRAME result 1: next frame of the missile"]["none logged (MFX %s)" % mfx] += 1
            if R["do"] != 1:
                continue
            nfr = 0
            last = None
            for a, b in fr:
                d0, d1 = L[a][1], L[b][1]
                nfr += 1
                mine = [(k, t2, d2) for k, (t2, d2) in enumerate(L[a + 1:b], a + 1)
                        if t2 == "MH0" and d2["m"]["u"] == d0["m"]]
                left = d0["md"]["rem"] - 1
                ends = [(k, d2) for k, t2, d2 in mine if d2["end"] == 1]
                units = [(k, d2) for k, t2, d2 in mine if d2["d"] is not None]
                for k, d2 in units:
                    rm, ac = d2["m"]["md"]["rem"], d2["m"]["md"]["act"]
                    C["FRAME do 1 unit hits: frames left against activate"][
                        "left < act" if rm < ac else "left = act" if rm == ac else "left > act (break)"] += 1
                    if rm > ac:
                        self.bad("FRAME.act", self.log, d2["n"], "unit hit at left %d > act %d" % (rm, ac))
                    if rm != left:
                        self.bad("FRAME.left", self.log, d2["n"], "hit left %d, frame left %d" % (rm, left))
                for k, d2 in ends:
                    rm = d2["m"]["md"]["rem"]
                    if rm <= 0:
                        why = "left 0 after the decrement (range spent)"
                    elif rm == d0["md"]["rem"]:
                        why = "left > 0, not yet decremented (before the decrement: the step)"
                    elif rm == left:
                        why = "left > 0, decremented (after the decrement: a crossed cell)"
                    else:
                        why = "other (break)"
                        self.bad("FRAME.endleft", self.log, d2["n"], "end at left %d, frame %d" % (rm, left))
                    e2 = L[self.close[k]][1] if k in self.close else None
                    C["FRAME do 1 end calls (none, 1) by frames left; frame result = the end call's"][
                        (why, e2 is not None and e2["r"] == d1["r"])] += 1
                    e = L[self.close[k]][1] if k in self.close else None
                    if e is not None and rm <= 0:
                        if d1["r"] == e["r"]:
                            C["FRAME do 1 range-spent frames: frame result = end call's"][e["r"]] += 1
                        else:
                            self.bad("FRAME.endr", self.log, d1["n"], "frame %s end %s" % (d1["r"], e["r"]))
                if left <= 0 and not ends:
                    self.bad("FRAME.spent", self.log, d1["n"], "left %d, no end call" % left)
                if d1["r"] == 2 and not mine:
                    C["FRAME do 1 frames returning 2 with no hit call"]["left %s" % ("0" if left <= 0 else "> 0")] += 1
                    self.ex["FRAME r2 no hit"].append((os.path.basename(self.log), d1["n"], c, left))
                last = (d1, ends)
            if last and last[0]["r"] == 2:
                spent = any(d2["m"]["md"]["rem"] <= 0 for _, d2 in last[1])
                if spent:
                    if rem0 is not None and nfr == rem0:
                        C["FRAME do 1 missiles ending at range spent: frames run = frames left at creation"][
                            "equal"] += 1
                    else:
                        self.bad("FRAME.range", self.log, last[0]["n"], "frames %d, created with %s" % (nfr, rem0))
                else:
                    why = "frames run < frames left at creation" if rem0 is not None and nfr < rem0 else \
                        "frames run %s, frames left at creation %s" % (nfr, rem0)
                    C["FRAME do 1 missiles ending before range"][why] += 1
            elif last:
                C["FRAME do 1 missiles still flying at the log's end or freed elsewhere"]["n"] += 1
            if act is not None and rem0 is not None:
                C["FRAME do 1 missiles: activate mark at creation"]["act < rem0" if act < rem0 else "act >= rem0"] += 1

    # ------------------------------------------------------------------ MH, DMG, MA, BDO
    def owner_type(self, i, mptr):
        """the owner type of the missile at line i (its latest creation before i)."""
        return self.cur_owner.get(mptr)

    def hits(self, L):
        C = self.c
        self.cur_owner = {}
        for i, (t, d) in enumerate(L):
            if i in self.mis_at:
                u, info = self.mis_at[i]
                self.cur_owner[u] = info
            if t != "MH0" or i not in self.close:
                continue
            e = L[self.close[i]][1]
            m = d["m"]
            R = self.R.m(m["c"])
            hf = self.R.hitfn(m["c"])
            dr = self.direct(i)
            tags = [t2 for _, t2, _ in dr]
            own = self.cur_owner.get(m["u"])
            ot = own["ot"] if own else None
            C["MH missile stat 19 at the hit, by owner type"][("player" if ot == 0 else "monster" if ot == 1 else
                                                                "other/unknown", "19" in (m.get("st") or {}))] += 1
            if d["d"] is None:
                kind = "hit function" if hf else "no hit function"
                C["MH end calls (no unit): end, row kind"][(d["end"], kind)] += 1
                C["MH end calls: a build directly in the call"][(kind, "BD0" in tags)] += 1
                if not hf and "BD0" in tags:
                    self.bad("MH.endbuild", self.log, d["n"], "end call of class %d built" % m["c"])
                for _, t2, d2 in dr:
                    if t2 == "BD0":
                        C["MH end calls of hit-function rows: the unit of each build inside"][
                            "a unit" if d2["d"] else "none"] += 1
                if R["ae"]:
                    C["MH AlwaysExplode rows' calls"][("end", e["r"])] += 1
                same = e["sm"] == m["s"]
                C["MH end calls: the missile's seed across the call"][(kind, "unchanged" if same else "moved")] += 1
                if not hf and not same:
                    self.bad("MH.endseed", self.log, d["n"], "class %d seed %s -> %s" % (m["c"], m["s"], e["sm"]))
                C["MH end calls: result"][(kind, e["r"])] += 1
                if not hf and e["r"] != 2:
                    self.bad("MH.endr", self.log, d["n"], "class %d result %s" % (m["c"], e["r"]))
                continue
            # a unit
            thr = [d2 for _, t2, d2 in dr if t2 == "THR"]
            if R["ae"]:
                C["MH AlwaysExplode rows' calls"][("unit", "THR %s" % ("miss" if thr and thr[0]["r"] >= thr[0]["c"]
                                                                      else "hit/none"), e["r"])] += 1
            if not hf:
                order = tuple(t2 for t2 in tags if t2 in ("THR", "BD0", "MA0"))
                C["MH unit calls, no hit function: THR/BD0/MA0 directly, in order"][order] += 1
                if order not in (("BD0", "MA0"), ("THR",), ("THR", "BD0", "MA0")):
                    self.bad("MH.order", self.log, d["n"], "order %s" % (order,))
                if "BD0" not in tags and not (thr and thr[0]["r"] >= thr[0]["c"]):
                    self.bad("MH.nobuild", self.log, d["n"], "no build, class %d" % m["c"])
                p0 = SK.stat(m.get("st"), 328)
                if R["pierce"] and R["ck"] and "BD0" in tags and e.get("m328", 0) == p0 - 1 and p0 > 0:
                    C["MH pierce used by a CollideKill row (no hit function)"]["result %s" % e["r"]] += 1
                    if e["r"] != 1:
                        self.bad("MH.piercekeep", self.log, d["n"], "result %s" % e["r"])
            else:
                passed = not thr or thr[0]["r"] < thr[0]["c"]
                if passed:
                    tbl = (0 if R["expl"] else 2) | (1 if R["ck"] else 0)
                    built = "BD0" in tags
                    C["MH unit calls, hit function, to-hit passed: table-only result builds / logged build"][
                        (bool(tbl & 2), built)] += 1
                    C["MH unit calls, hit function, to-hit passed: table-only result, logged build, result"][
                        (tbl, built, e["r"])] += 1
            # DMG: the build's exit to MISSILE_ApplyDamage's entry, by damage function
            for q, (k, t2, d2) in enumerate(dr):
                if t2 != "BD0" or k not in self.close:
                    continue
                b1 = L[self.close[k]][1]
                ma = next(((k2, d3) for k2, t3, d3 in dr[q + 1:] if t3 == "MA0"), None)
                dm = self.R.dmgfn(m["c"])
                if ma:
                    st = SK.steps_between(SK.sd_parse(b1["sm"]), SK.sd_parse(ma[1]["sa"]), 64)
                    C["DMG missile seed steps from BD1 to MA0, by pSrvDmgFunc"][(dm, st)] += 1
                    ad = [d3 for t3, d3 in self.inside(ma[0]) if t3 == "AD0"]
                    if ad:
                        p1 = struct.unpack("<28i", bytes.fromhex(b1["p"]))
                        p2 = struct.unpack("<28i", bytes.fromhex(ad[0]["p"])[:0x70])
                        same = p1[2:18] == p2[2:18]
                        ot = self.cur_owner.get(m["u"], {}).get("ot")
                        C["DMG packet words +0x08..+0x47: BD1 = the AD0 inside MA, by pSrvDmgFunc, owner type"][
                            (dm, ot, same)] += 1
                self.bdo(m, k, b1)
            for k, t2, d2 in dr:
                if t2 == "MA0" and k in self.close:
                    self.ma(m, R, k, d2, d)

    def inside(self, i):
        return [(t, d) for t, d in self.L[i + 1:self.close[i]]]

    def ma(self, m, R, k, d0, mh0):
        C = self.c
        d1 = self.L[self.close[k]][1]
        st = SK.steps_between(SK.sd_parse(d0["sa"]), SK.sd_parse(d1["sa"]), 64)
        C["MA missile seed steps across MISSILE_ApplyDamage, by KnockBack"][(R["kb"], st)] += 1
        want = 1 if R["kb"] else 0
        if st != want:
            self.bad("MA.kbstep", self.log, d0["n"], "class %d kb %d steps %s" % (m["c"], R["kb"], st))
        inner = self.inside(k)
        ad = [d2 for t2, d2 in inner if t2 == "AD0"]
        if R["kb"] and st == 1 and ad:
            roll = SK.step(SK.sd_parse(d0["sa"]))[0] % 100
            f = struct.unpack_from("<H", bytes.fromhex(ad[0]["p"]), 4)[0]
            got = bool(f & 8)
            C["MA knockback roll < KnockBack against packet +0x04 bit 3"][(R["kb"], roll, roll < R["kb"], got)] += 1
            if got != (roll < R["kb"]):
                self.bad("MA.kbflag", self.log, d0["n"], "roll %d kb %d flag %s" % (roll, R["kb"], got))
        for t2, d2 in inner:
            if t2 == "DRR":
                C["MA DRR lines inside: unit"]["the defender" if d2["u"] == d0["b"] else "other"] += 1

    def bdo(self, m, k, b1):
        """the draw order of MISSILE_BuildDamage: per two drawn pairs, does swapping them change the packet?"""
        C = self.c
        st = m.get("st") or {}
        b0 = self.L[k][1]
        pk = struct.unpack("<28i", bytes.fromhex(b1["p"]))
        drawn = []
        for idx, (lo_s, hi_s, ms, off) in enumerate(BD_ROLLS):
            lo, hi = SK.stat(st, lo_s), SK.stat(st, hi_s)
            if lo >= 1 and hi >= 1:
                if lo > hi:
                    lo, hi = hi, lo
                mm = SK.stat(st, ms) if ms else 0
                if mm:
                    lo += SK.muldiv(lo, mm, 100)
                    hi += SK.muldiv(hi, mm, 100)
                if hi - lo >= 1:
                    drawn.append((idx, lo, hi, off))
        if len(drawn) < 2:
            C["BDO builds by draws (%s)" % self.fam][len(drawn)] += 1
            return
        C["BDO builds by draws (%s)" % self.fam][len(drawn)] += 1
        C["BDO drawn sets (%s)" % self.fam][tuple(BD_ROLLS[x[0]][0] for x in drawn)] += 1

        def values(order):
            t = SK.sd_parse(b0["sm"])
            out = {}
            for idx, lo, hi, off in order:
                t = SK.step(t)
                out[off] = t[0] % (hi - lo) + lo
            return out

        def phys(v):
            pct = max(SK.stat(st, 25) + SK.stat(st, 121) + SK.stat(st, 122), -90)
            v += SK.tdiv(v * pct, 100)
            return v * 2 if SK.stat(st, 141) else v

        def match(vals):
            for off, v in vals.items():
                got = pk[off // 4]
                if off == 0x08:
                    v = phys(v)
                if got != v:
                    return False
            return True
        if not match(values(drawn)):
            self.bad("BDO.model", self.log, b0["n"], "the code order fails")
            return
        for a in range(len(drawn)):
            for b in range(a + 1, len(drawn)):
                alt = list(drawn)
                alt[a], alt[b] = alt[b], alt[a]
                sep = not match(values(alt))
                key = (BD_ROLLS[drawn[a][0]][0], BD_ROLLS[drawn[b][0]][0])
                C["BDO pairs (first-drawn min stat, second) in the code order: separating builds / builds"][
                    (key, "separating" if sep else "not separating")] += 1

    # ------------------------------------------------------------------ MC
    def creations(self, L):
        C = self.c
        # the windowed frame open at each MC0 (MF0 seen, its MF1 not yet), when no MH0 lies between
        self.open_mf = {}
        cur = None
        for i, (t, d) in enumerate(L):
            if t == "MF0":
                cur = d["m"]
            elif t == "MF1":
                cur = None
            elif t == "MH0":
                cur = None
            elif t == "MC0" and cur is not None:
                self.open_mf[i] = cur
        for i, (t, d) in enumerate(L):
            if t == "MC0" and i in self.close:
                f = blkw(d, 0, "<I")
                o = d.get("o") or {}
                C["MC flag 0x1000 by owner type (every creation)"][(o.get("t"), bool(f & 0x1000))] += 1
                if f & 0x1000 and o.get("t") == 0:
                    self.bad("MC.player1000", self.log, d["n"], "player creation with flag 0x1000")
                e = L[self.close[i]][1]
                for k, t2, d2 in self.direct(i):
                    if t2 == "MCB0" and k in self.close:
                        self.mcb(i, d, e, k, d2)
                cb = blkw(d, 0x54, "<I")
                if cb == CB_PATHX:
                    C["MC 0x005AC040 creations: lines inside MissileCreate"][
                        tuple(t2 for _, t2, _ in self.direct(i))] += 1
                src = blkw(d, 0x08, "<I")
                par = None
                for a, b in self.close.items():
                    if a < i < b and self.L[a][0] == "MH0" and (par is None or a > par):
                        par = a
                if par is not None:
                    pm = self.L[par][1]["m"]["u"]
                    C["MC creations inside a missile's hit call: source = that missile"][src == pm] += 1
                mf = self.open_mf.get(i)
                if mf is not None:
                    C["MC creations inside a windowed missile's frame (no hit between): source = that missile"][
                        src == mf] += 1
                cls = blkw(d, 0x10)
                if cls == 408:
                    self.encl408(i)
            if t == "SDO0" and i in self.close:
                sid = d["a"][0]
                S = self.R.sk(sid) if 0 <= sid < len(self.T.sk) else None
                if S is None:
                    continue
                dr = self.direct(i)
                mcs = [(k, d2) for k, t2, d2 in dr if t2 == "MC0" and k in self.close]
                if S["do"] == 0 and S["srvmissile"] >= 0 and mcs:
                    self.srvmissile(sid, S, d, mcs)
                if sid == SK_FIRESTORM:
                    seqc = []
                    for k, d2 in mcs:
                        cb = blkw(d2, 0x54, "<I")
                        a = [d3["arg"] for k3, t3, d3 in self.direct(k) if t3 == "MCB0"]
                        seqc.append((blkw(d2, 0x10), hex(cb) if cb else 0, tuple(a)))
                    C["MC Firestorm do events: (class, callback, MCB0 arg) per creation, in order"][tuple(seqc)] += 1
                if sid == SK_MSHOT:
                    self.mshot(d, mcs)
                if sid == SK_METEOR:
                    for k, d2 in mcs:
                        e = L[self.close[k]][1]
                        f = blkw(d2, 0, "<I")
                        sx, sy, tx, ty = struct.unpack_from("<iiii", bytes.fromhex(d2["p"]), 0x14)
                        tu = blkw(d2, 0x0C, "<I")
                        p = (e.get("m") or {}).get("path") or {}
                        C["MC Meteor do events: flags, target unit, target words, path direction"][
                            (hex(f), tu, (tx, ty), (p.get("dx"), p.get("dy")), p.get("v"))] += 1

    def srvmissile(self, sid, S, sdo, mcs):
        C = self.c
        k, d2 = mcs[-1]
        e = self.L[self.close[k]][1]
        f = blkw(d2, 0, "<I")
        cls = blkw(d2, 0x10)
        o = d2.get("o") or {}
        lob = S["lob"]
        want = 0x420 if lob else 0x21
        to = SK.stat(o.get("st"), 19) if o.get("t") == 1 else 0
        if to and not lob:
            want |= 0x1000
        md = ((e.get("m") or {}).get("md")) or {}
        ok = (f == want and cls == S["srvmissile"] and (md.get("sk"), md.get("lv")) == (sid, sdo["a"][1]))
        key = ("lob" if lob else "line", "player" if o.get("t") == 0 else "monster", hex(f),
               "owner stat 19 %s" % ("> 0" if SK.stat(o.get("st"), 19) else "0"))
        C["MC SrvDo srvmissile creations (rows with no srvdofunc): form, owner, flags"][key] += 1
        C["MC SrvDo srvmissile creations: flags, class, skill and level as B2/B3"][ok] += 1
        if not ok:
            self.bad("MC.srvmissile", self.log, d2["n"], "skill %d flags %x want %x class %d/%d md %s" %
                     (sid, f, want, cls, S["srvmissile"], md))
        if f & 0x1000:
            v = blkw(d2, 0x48)
            m19 = SK.stat(((e.get("m") or {}).get("st")), 19)
            C["MC SrvDo monster creations with 0x1000: +0x48 = owner stat 19, missile stat 19 = it"][
                (v == to, m19 == to)] += 1
            if v != to or m19 != to:
                self.bad("MC.tohit", self.log, d2["n"], "+0x48 %d owner 19 %d missile 19 %d" % (v, to, m19))
        if o.get("t") == 1 and not to:
            C["MC SrvDo monster creations, owner stat 19 = 0: flag 0x1000"][bool(f & 0x1000)] += 1
        if len(mcs) > 1:
            C["MC SrvDo srvmissile rows with more than one creation in the do"][sid] += 1

    def mcb(self, i, d, e, k, d2):
        C = self.c
        cb = blkw(d, 0x54, "<I")
        arg = blkw(d, 0x58, "<I")
        mm = (e.get("m") or {}).get("u")
        tags = [t2 for _, t2, _ in self.direct(i)]
        pos = tags.index("MCB0")
        before = tuple(tags[:pos])
        ok = cb == CB_FIRESTORM and d2["arg"] == arg and d2["m"] == mm
        C["MC callback lines (MCB0): +0x54 = 0x005C9290, EDX = +0x58, ECX = the new missile (MC1)"][ok] += 1
        C["MC callback lines: the lines before MCB0 inside MissileCreate"][before] += 1
        if not ok:
            self.bad("MC.mcb", self.log, d2["n"], "cb %x arg %s/%s m %s/%s" % (cb, d2["arg"], arg, d2["m"], mm))

    def encl408(self, i):
        C = self.c
        best = None
        for a, b in self.close.items():
            if a < i < b and self.L[a][0] in ("MH0", "MF0", "SDO0", "MC0"):
                if best is None or a > best:
                    best = a
        if best is None:
            capped = any(t == "CAP" and d.get("k") == "mh" for t, d in self.L[:i])
            C["MC class 408 creations: the innermost enclosing span"][
                ("none", "after the logger's MH cap" if capped else "before any MH cap")] += 1
            return
        t, d = self.L[best]
        if t == "MH0":
            c = d["m"]["c"]
            C["MC class 408 creations: the innermost enclosing span"][
                ("MH0", c, self.R.m(c)["hit"], "end %d" % d["end"])] += 1
        else:
            C["MC class 408 creations: the innermost enclosing span"][(t,)] += 1

    def mshot(self, sdo, mcs):
        C = self.c
        pts = []
        for k, d2 in mcs:
            f = blkw(d2, 0, "<I")
            tx, ty = struct.unpack_from("<ii", bytes.fromhex(d2["p"]), 0x1C)
            pts.append((f, tx, ty))
        n = len(pts)
        if n < 2:
            C["MC Multiple Shot do events by creations"][n] += 1
            return
        sx, sy = pts[1][1] - pts[0][1], pts[1][2] - pts[0][2]
        stepped = all((pts[q + 1][1] - pts[q][1], pts[q + 1][2] - pts[q][2]) == (sx, sy) for q in range(n - 1))
        groups = []
        for f, _, _ in pts:
            if groups and groups[-1][0] == f:
                groups[-1][1] += 1
            else:
                groups.append([f, 1])
        gk = tuple((hex(f), c) for f, c in groups)
        c3 = sum(c for f, c in groups if f == 0x820)
        g1 = (n - c3) // 2
        shape = gk == ((hex(0x10820), g1), (hex(0x820), c3), (hex(0x10820), n - g1 - c3)) if 0 < g1 < n else None
        C["MC Multiple Shot do events: creations, groups (flags, count)"][(n, gk)] += 1
        C["MC Multiple Shot: targets stepped by one vector (sx, sy), sx^2 + sy^2 <= 3"][
            (stepped, (sx, sy), sx * sx + sy * sy <= 3)] += 1
        C["MC Multiple Shot: groups outer g1 = (n - c3) / 2, centre c3, outer n - g1 - c3"][shape] += 1
        if not stepped or not shape or sx * sx + sy * sy > 3 or (sx, sy) == (0, 0):
            self.bad("MC.mshot", self.log, sdo["n"], "points %s" % (pts,))

    # ------------------------------------------------------------------ SKL
    def skills(self, L):
        C = self.c
        for i, (t, d) in enumerate(L):
            if t not in ("SDO0", "SST0") or i not in self.close:
                continue
            sid = d["a"][0]
            if not 0 <= sid < len(self.T.sk):
                continue
            S = self.R.sk(sid)
            e = L[self.close[i]][1]
            caster = d["u"]["u"]
            inner = self.inside(i)
            if t == "SDO0" and sid == SK_AMP:
                sta = [d2 for t2, d2 in inner if t2 == "STA"]
                units = [x["d"] for x in sta]
                ok = all(x["state"] == S["ats"] for x in sta) and len(set(units)) == len(units) and \
                    len(set(x["len"] for x in sta)) <= 1 and all(x["a"] == caster for x in sta)
                C["SKL Amplify Damage do events: STA lines (count), all state = auratargetstate, one per unit, "
                  "one length, applier = caster"][(len(sta), ok)] += 1
                if not ok:
                    self.bad("SKL.amp", self.log, d["n"], "STA %s" % sta)
            if t == "SDO0" and sid == SK_HOLYFIRE:
                rel = [d2 for t2, d2 in inner if t2 == "REL"]
                ad = [d2 for t2, d2 in inner if t2 == "AD0"]
                ok = len(rel) == 1 and rel[0]["u"] == caster
                st = SK.steps_between(SK.sd_parse(d["u"]["s"]), SK.sd_parse(rel[0]["s"]), 64) if rel else None
                fires = set(struct.unpack_from("<i", bytes.fromhex(a["p"]), 0x10)[0] for a in ad)
                C["SKL Holy Fire do events: one REL on the caster, caster steps SDO0 -> REL, AD0 lines, fire words"][
                    (ok, st, "AD %s" % ("0" if not ad else "1" if len(ad) == 1 else "2+"),
                     "one fire value" if len(fires) <= 1 else "%d values" % len(fires))] += 1
                if not ok or (len(ad) > 1 and len(fires) != 1):
                    self.bad("SKL.holyfire", self.log, d["n"], "REL %d fires %s" % (len(rel), fires))
                if len(ad) > 1:
                    C["SKL Holy Fire do events with 2+ units: units"][len(ad)] += 1
            if t == "SST0" and sid == SK_BASH:
                rel = [d2 for t2, d2 in inner if t2 == "REL"]
                C["SKL Bash starts (st %d): REL lines, on the caster" % S["st"]][
                    (len(rel), all(r["u"] == caster for r in rel))] += 1
                if any(r["u"] != caster for r in rel):
                    self.bad("SKL.bash", self.log, d["n"], "REL on another unit")
            if t == "SDO0" and d["u"]["t"] == 1 and self.fam == "cat":
                self.r4(d, e, S, sid, i)

    def r4(self, d, e, S, sid, i):
        """R4: the caster's steps in a monster do event, split into the steps inside the caster's logged nested spans
        (its creations' owner seed MC0 -> MC1, MonAttackStats MAS0 -> MAS1, COMBAT_MeleeHitTest MHT0 -> MHT1, a nested
        start SST0 -> SST1), its REL lines (one draw each), and the rest (the do's own code and unlogged callees)."""
        C = self.c
        caster = d["u"]["u"]
        k = SK.steps_between(SK.sd_parse(d["u"]["s"]), SK.sd_parse(e["s"]), 4096)
        nested = Counter()
        for k2, t2, d2 in self.direct(i):
            st = None
            if t2 == "MC0" and k2 in self.close and (d2.get("o") or {}).get("u") == caster:
                e2 = self.L[self.close[k2]][1]
                if e2.get("so"):
                    st = SK.steps_between(SK.sd_parse(d2["o"]["s"]), SK.sd_parse(e2["so"]), 64)
            elif t2 == "MAS0" and k2 in self.close and d2["u"]["u"] == caster:
                st = SK.steps_between(SK.sd_parse(d2["u"]["s"]), SK.sd_parse(self.L[self.close[k2]][1]["s"]), 64)
            elif t2 == "MHT0" and k2 in self.close and d2["a"] == caster:
                st = SK.steps_between(SK.sd_parse(d2["sa"]), SK.sd_parse(self.L[self.close[k2]][1]["sa"]), 64)
            elif t2 == "SST0" and k2 in self.close and d2["u"]["u"] == caster:
                st = SK.steps_between(SK.sd_parse(d2["u"]["s"]), SK.sd_parse(self.L[self.close[k2]][1]["s"]), 64)
            elif t2 == "REL" and d2["u"] == caster:
                st = 1
            elif t2 == "DQ0" and k2 in self.close and d2["a"] == caster:
                st = SK.steps_between(SK.sd_parse(d2["sa"]), SK.sd_parse(self.L[self.close[k2]][1]["sa"]), 64)
            if st:
                nested[t2] += st
        rest = None if k is None else k - sum(nested.values())
        key = (S["do"], sid, k, tuple(sorted(nested.items())), "rest %s" % rest)
        C["SKL R4 monster do events (catalogue run): do, skill, caster steps, steps inside the caster's nested "
          "spans and REL lines, the rest"][key] += 1

    # ------------------------------------------------------------------ OWN
    def owner_chain(self, L):
        """I1: the owner's seed from its creation to the THR of the missile's hit; the owner's seeds logged between."""
        C = self.c
        made = {}
        for i, (t, d) in enumerate(L):
            if i in self.mis_at:
                u, info = self.mis_at[i]
                if info["mc1"].get("so") and info["o"]:
                    made[u] = (i, info)
                else:
                    made.pop(u, None)
            if t != "MH0" or d["d"] is None or i not in self.close:
                continue
            thr = [(k, d2) for k, t2, d2 in self.direct(i) if t2 == "THR"]
            mu = d["m"]["u"]
            if not thr or mu not in made:
                continue
            j, info = made[mu]
            own = info["o"]
            k, th = thr[0]
            if th["a"] != own:
                C["OWN THR attacker = the missile's owner"][False] += 1
                continue
            C["OWN THR attacker = the missile's owner"][True] += 1
            obs = [SK.sd_parse(info["mc1"]["so"])]
            kinds = Counter()
            for q in range(j + 1, k):
                t2, d2 = L[q]
                s = None
                if t2 == "MC0" and (d2.get("o") or {}).get("u") == own:
                    s = d2["o"]["s"]
                elif t2 == "MC1" and q in self.mis_at and self.mis_at[q][1]["o"] == own:
                    s = d2.get("so")
                elif t2 == "THR" and d2["a"] == own:
                    s = d2["sa"]
                elif t2 in ("SDO0", "SST0") and d2["u"]["u"] == own:
                    s = d2["u"]["s"]
                elif t2 in ("SDO1", "SST1") and L[self.exits_entry(t2, d2)][1]["u"]["u"] == own:
                    s = d2["s"]
                elif t2 == "REL" and d2["u"] == own:
                    s = d2["s"]
                if s:
                    obs.append(SK.sd_parse(s))
                    kinds[t2] += 1
            obs.append(SK.sd_parse(th["sa"]))
            ok = True
            total = 0
            for a, b in zip(obs, obs[1:]):
                st = SK.steps_between(a, b, 4096)
                if st is None:
                    ok = False
                    break
                total += st
            between = "no owner line between" if not kinds else "owner lines between"
            C["OWN creation -> hit's THR: the owner's logged seeds chain forward"][(between, ok)] += 1
            if ok:
                C["OWN steps MC1 -> THR (after its roll): 1 = the roll alone, more = owner draws between"][
                    (between, "1" if total == 1 else "2+" if total > 1 else total)] += 1
            if not ok:
                C["OWN unchained pairs by owner lines between"][tuple(sorted(kinds))] += 1

    def exits_entry(self, t, d):
        # the entry line of an exit (SDO1/SST1 carry k = the entry's n)
        if not hasattr(self, "_n2i") or self._n2i_log is not self.L:
            self._n2i = {dd["n"]: q for q, (tt, dd) in enumerate(self.L) if "n" in dd and tt in ("SDO0", "SST0")}
            self._n2i_log = self.L
        return self._n2i[d["k"]]

    # ------------------------------------------------------------------ report
    def report(self):
        for sec in sorted(self.c):
            print("== " + sec)
            for k, v in sorted(self.c[sec].items(), key=lambda kv: repr(kv[0])):
                print("  %8d  %s" % (v, k))
        print("== examples: do 1 frames returning 2 with no hit call (log, MF1 n, class, frames left)")
        for x in self.ex["FRAME r2 no hit"][:40]:
            print("  %s" % (x,))
        print("== breaks by check")
        for k, v in sorted(self.nbreak.items()):
            print("  %-16s %d" % (k, v))
        for b in self.breaks:
            print("  BREAK " + b)
        tot = sum(self.nbreak.values())
        print("SURVEY s2b breaks=%d" % tot)
        return tot


def main(argv):
    if not argv or argv[0] != "check":
        print(__doc__)
        return 2
    args = argv[1:]
    excel = SK.DEFAULT_EXCEL
    if "--excel" in args:
        q = args.index("--excel")
        excel = args[q + 1]
        del args[q:q + 2]
    C = S2B(SK.Tables(excel))
    for p in args:
        C.run(p)
    return 1 if C.report() else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
