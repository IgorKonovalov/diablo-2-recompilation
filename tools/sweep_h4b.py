"""Plan 0038 batch H4b (monsters-b): the checker of the tags that tools/gdb/mon-extra.py adds to tools/gdb/mon-stats.gdb.

Usage:
  python3 -I tools/sweep_h4b.py check <run.log> [...] [-v]
  python3 -I tools/sweep_h4b.py <part> <run.log> [...] [-v]      one part only

Parts (the inventory rows each serves are in docs/findings/monsters/0003 and 0004, sections "Plan 0038 batch H4b"):
  sik       SIK: the skill list after MonStatsInit's eight-slot loop against MonStats Skill1..8 (s16 +0x170 + 2k) and
            Sk1lvl..8 (s8 +0x198 + k) plus DifficultyLevels MonsterSkillBonus (+0x10) of the game byte +0x6D, with the
            logged bonus word; HSK the skills a teleport (26) or aura (30) handler added (stats 5, 13, 17, 20, 44)
  aura      AURS against g_UModAuraTable 0x0073BF68 and the AUR line of the same unit: the row is the drawn index (or
            AUR2's), level = clamp((add + lvl) * mul / div, 1, 99), the skill the row's (special 5, 20, 27, 29)
  names     CTAB, CMA, CMH, CNB, CNS, CNT (client): handler rows, the builder per mod, no text for a non-special,
            superunique Name, champion word + NameStr through 11072, random unique through 1721 / 1722 with the
            CNR rows, the last call wins (special 6, 7, 11, 66, 67, 71)
  restore   RS0..RSX (SpecialMonRestore) and MNR0..MNRX (MinionRestore): mods restored, name seed written after the
            apply and equal to the first instance's, the second aura call, flag-0 handlers over 1..4 and the nine
            bytes; MMS0 MonMakeSpecial calls (special 1, 2, 74)
  monplace  PMA0 / PMAV / PMAX: every MonPlace case with its class through LevelClassVariant and PresetFallenVariant,
            the mode 12 cases, the normal-difficulty group cases, and the unit created (special 65)
  tick      RTK0 / RTK1: one room-seed step per wanderer tick, on populated rooms too, and the seed carried between
            ticks (spawn 6)
  tentacle  MMT blocks: tentaclehead minions, count, the head's extra step, start j = low % 6, offsets 0x006E2CF0 by
            o = not(request flags bit 2), j <- (j + 5) % 6 (spawn 43, 44)
  masks     MK0 collision masks by MonStats2 spawnCol of the class being placed (spawn 3); MC results of
            SpawnClassCellTest by class (spawn 42)
  players   SI0 / SI1: the player-count record of Align 1 and 2 classes and hirelings under /players > 1 (stats 23,
            hirelings 34); doomknight and willowisp creations (stats 13, 14, 40)
  watch     WCH hits by watch and by the function holding the pc (re/symbols.csv) (pool 7, 19; spawn 51; special 72)
  hwt       HWT writes of room bit 0x800000 (spawn 12)

Each part prints one `H4B <part> key=value ...` line and a few detail lines (all of them with -v). A part exits 1 when
an observation contradicts the model (`bad=` above 0); a case the logs never met is a zero count, not a failure. The
existing checkers (tools/monstats.py, which chains tools/monspawn.py, tools/monspecial.py, tools/collision.py,
tools/drlg.py and tools/monpool.py) run on the same logs separately and must report 0 mismatches.

Stdlib only. Read-only.
"""
import bisect
import collections
import csv
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)

import drlg  # noqa: E402
import monspecial  # noqa: E402
from excel_bin import find_file, read_bin  # noqa: E402
from rng import INIT_HIGH, step  # noqa: E402
import tbl  # noqa: E402

EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
LNG = os.path.join(ROOT, "workspace", "merged", "data", "local", "lng", "eng")
EXE = drlg.DEFAULT_EXE
VERBOSE = False


def parse(path):
    with open(path, "rb") as fh:
        for n, raw in enumerate(fh, 1):
            line = raw.decode("utf-8", "replace").rstrip("\n")
            sp = line.find(" ")
            if sp <= 0 or line[sp + 1:sp + 2] != "{":
                continue
            try:
                d = json.loads(line[sp + 1:])
            except ValueError:
                continue
            yield line[:sp], d, n


def seed_t(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def fmt(t):
    return "%08x:%08x" % t


class T:
    """Tables by position (.bin) and constant data of the pinned game.exe."""
    _inst = None

    @classmethod
    def get(cls):
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        self.sp = monspecial.Data(EXCEL, EXE)
        self.ms = self.sp.ms
        self.ms2 = self.sp.ms2
        self.su = self.sp.su
        self.dl, sz = read_bin(find_file(EXCEL, "difficultylevels", ".bin"))
        self.aura = self.sp.aura_rows
        self.handler = list(struct.unpack("<%dI" % len(self.sp.mu), drlg.exe_read(EXE, 0x0073C008, 4 * len(self.sp.mu))))
        self.tent = struct.unpack("<36i", drlg.exe_read(EXE, 0x006E2CF0, 144))
        self.uprefix = [s for _, s in tbl.unique_rows(EXCEL, "uniqueprefix")]
        self.usuffix = [s for _, s in tbl.unique_rows(EXCEL, "uniquesuffix")]
        self.uapp = [s for _, s in tbl.unique_rows(EXCEL, "uniqueappellation")]
        self.gs = {}
        self.names = [r[0] for r in csv.reader(open(os.path.join(EXCEL, "monstats.txt"), encoding="latin-1"),
                                               delimiter="\t")][1:]
        self.names = [n for n in self.names if n and n != "Expansion"]

    def s16(self, rec, off):
        return struct.unpack_from("<h", rec, off)[0]

    def u16(self, rec, off):
        return struct.unpack_from("<H", rec, off)[0]

    def name(self, c):
        return self.names[c] if 0 <= c < len(self.names) else str(c)

    def skill_bonus(self, d):
        return struct.unpack_from("<i", self.dl[d], 0x10)[0]

    def spawncol(self, c):
        x = self.u16(self.ms[c], 0x18)
        return self.ms2[x][0x0A] if 0 <= x < len(self.ms2) else None

    def base(self, c):
        return self.u16(self.ms[c], 0x02)

    def align(self, c):
        return self.ms[c][0x4C]

    def strings(self, exp):
        k = "spx" if exp else "sp"
        if k not in self.gs:
            self.gs[k] = tbl.GameStrings(LNG, k)
        return self.gs[k]


class Report:
    def __init__(self, part):
        self.part = part
        self.c = collections.Counter()
        self.bad = []
        self.notes = []

    def n(self, k, v=1):
        self.c[k] += v

    def fail(self, msg):
        self.bad.append(msg)

    def note(self, msg):
        self.notes.append(msg)

    def out(self):
        kv = " ".join("%s=%s" % (k.replace(" ", "_"), v) for k, v in sorted(self.c.items()))
        print("H4B %s bad=%d %s" % (self.part, len(self.bad), kv))
        for m in self.bad[:None if VERBOSE else 20]:
            print("  BAD " + m)
        for m in self.notes[:None if VERBOSE else 30]:
            print("  " + m)
        return 1 if self.bad else 0


def game_exp(path):
    for tag, d, _ in parse(path):
        if tag == "SI0":
            return d.get("exp", 1), d.get("g6d", 0)
        if tag == "PMA0" and d.get("exp") is not None:
            return d["exp"], d.get("diff", 0)
    return 1, 0


# --- skills --------------------------------------------------------------------------------------------------------
def part_sik(paths):
    R, t = Report("sik"), T.get()
    for p in paths:
        sik = {}
        for tag, d, n in parse(p):
            if tag == "SIK":
                c, g = d["cls"], d["g6d"]
                rec = t.ms[c]
                dd = min(g, 2) if g is not None else 0
                exp_bonus = t.skill_bonus(dd)
                if d["bonus"] != exp_bonus:
                    R.fail("%s:%d class %d difficulty %s: bonus %d, MonsterSkillBonus %d" % (p, n, c, g, d["bonus"], exp_bonus))
                want = []
                for k in range(8):
                    s, lv = t.s16(rec, 0x170 + 2 * k), struct.unpack_from("<b", rec, 0x198 + k)[0]
                    if s >= 0 and lv > 0:
                        want.append([s, lv + d["bonus"]])
                got = d["sk"] or []
                if sorted(map(tuple, got)) != sorted(map(tuple, want)):
                    R.fail("%s:%d class %d (%s) difficulty %s: skills %s, model %s" % (p, n, c, t.name(c), g, got, want))
                R.n("SIK lines")
                R.n("SIK difficulty %s bonus %d" % (g, d["bonus"]))
                if want:
                    R.n("SIK with skills")
                    R.n("skills set", len(want))
                if len(set(s for s, _ in want)) != len(want):
                    R.n("SIK with a repeated skill id")
                if c in (311, 312):
                    R.n("SIK doomknight 311/312")
                sik[d["u"]] = got
            elif tag == "HSK":
                before = {tuple(x) for x in sik.get(d["u"], [])}
                added = [x for x in (d["sk"] or []) if tuple(x) not in before]
                R.n("HSK mod %d" % d["m"])
                R.note("HSK %s:%d mod %d unit %d: added %s" % (os.path.basename(p), n, d["m"], d["u"], added)) if VERBOSE else None
                if d["m"] == 26:
                    if any(lv != 1 for _, lv in added) or len(added) != 1:
                        R.fail("%s:%d teleport handler added %s (one skill at level 1 expected)" % (p, n, added))
                    else:
                        R.n("HSK teleport: one skill at level 1 (skill %d)" % added[0][0])
                sik[d["u"]] = d["sk"] or []
    return R.out()


# --- aura ----------------------------------------------------------------------------------------------------------
def aura_model(t, lvl, idx):
    lvl = 1 if lvl <= 0 else lvl
    mn, add, mul, div, skill = t.aura[idx]
    v = (add + lvl) * mul
    k = abs(v) // div * (1 if (v >= 0) == (div > 0) else -1)
    k = 1 if k <= 1 else (99 if k >= 99 else k)
    return skill, k


def part_aura(paths):
    R, t = Report("aura"), T.get()
    rows = ", ".join("(%d, %d, %d, %d, %d)" % tuple(r) for r in t.aura)
    R.note("g_UModAuraTable rows (minLevel, add, mul, div, skill): " + rows)
    for p in paths:
        aur, aur2 = {}, {}
        diff = game_exp(p)[1]
        for tag, d, n in parse(p):
            if tag == "SI0":
                diff = d.get("g6d", diff)
            elif tag == "AUR":
                aur[d["u"]] = d
                aur2.pop(d["u"], None)
                nrows = sum(1 for r in t.aura if r[0] <= max(d["lvl"], 1)) or 1
                if d["n"] != nrows:
                    R.fail("%s:%d AUR n %d, rows with minLevel <= %d: %d" % (p, n, d["n"], d["lvl"], nrows))
            elif tag == "AUR2":
                aur2[d["u"]] = d["idx"]
            elif tag == "AURS":
                R.n("AURS %s" % d["k"])
                if d["k"] != "row":
                    continue
                a = aur.get(d["u"])
                if a is None:
                    R.fail("%s:%d AURS without an AUR of unit %d" % (p, n, d["u"]))
                    continue
                idx = aur2.get(d["u"], a["r"])
                skill, k = aura_model(t, a["lvl"], idx)
                if (d["row"], d["skill"], d["lvl"]) != (idx, skill, k):
                    R.fail("%s:%d AURS row %d skill %d level %d; model row %d skill %d level %d (lvl %d)" % (
                        p, n, d["row"], d["skill"], d["lvl"], idx, skill, k, a["lvl"]))
                else:
                    R.n("AURS reproduced")
                    R.n("AURS row %d" % idx)
                    R.n("AURS difficulty %d" % diff)
                    if k in (1, 99):
                        R.n("AURS level clamped to %d" % k)
                R.note("%s:%d row %d (skill %d) lvl %d -> level %d" % (os.path.basename(p), n, idx, skill, a["lvl"], k))
    return R.out()


# --- client names --------------------------------------------------------------------------------------------------
def fmt_text(template, args):
    out = template
    for i, a in enumerate(args):
        out = out.replace("%%%d" % i, a)
    return out


def part_names(paths):
    R, t = Report("names"), T.get()
    for p in paths:
        exp = game_exp(p)[0]
        G = t.strings(exp)
        txt = lambda i: G.by_index(i)[3]  # noqa: E731
        ctab = None
        blocks = []          # per CMA: {"u", "cma", "calls": [cnb records]}
        cur = None
        last_cnb = None
        for tag, d, n in parse(p):
            if tag == "CTAB":
                ctab = d
            elif tag == "CMA":
                cur = {"cma": d, "calls": [], "cmh": [], "n": n}
                blocks.append(cur)
                last_cnb = None
            elif tag == "CMH" and cur is not None:
                cur["cmh"].append(d)
                if ctab and d["h"] != ctab["handlers"][d["m"]]:
                    R.fail("%s:%d CMH mod %d handler %08x, table %08x" % (p, n, d["m"], d["h"], ctab["handlers"][d["m"]]))
                R.n("client handler calls")
            elif tag == "CNB":
                last_cnb = {"d": d, "cns": [], "cnt": [], "cnr": [], "cn0": None, "n": n}
                if cur is not None and cur["cma"]["u"] == d["u"]:
                    cur["calls"].append(last_cnb)
            elif tag == "CNS" and last_cnb is not None:
                last_cnb["cns"].append(d["idx"])
            elif tag == "CNT" and last_cnb is not None:
                last_cnb["cnt"].append(d["text"])
            elif tag == "CNR" and last_cnb is not None:
                last_cnb["cnr"].append((d["k"], d["idx"]))
            elif tag == "CN0" and last_cnb is not None:
                last_cnb["cn0"] = d
        if ctab:
            h = ctab["handlers"]
            builder = {i for i, v in enumerate(h) if v == 0x004AC870}
            if builder != {1, 12, 16, 36, 37, 38, 39}:
                R.fail("%s: builder rows %s" % (p, sorted(builder)))
            R.n("CTAB builder rows 1 12 16 36-39", 1)
            champ = {m: w for m, w in ctab["champ"]}
            if champ != {16: 3220, 36: 11084, 37: 11085, 38: 11086, 39: 11087} or ctab["always"] != [1, 2, 3, 4]:
                R.fail("%s: CTAB champion words %s always %s" % (p, champ, ctab["always"]))
        else:
            champ = {16: 3220, 36: 11084, 37: 11085, 38: 11086, 39: 11087}
        for b in blocks:
            u = b["cma"]
            mf = u.get("mf", 0)
            for c in b["calls"]:
                d = c["d"]
                m = d["m"]
                kind = None
                if d["special"] != (1 if mf & 0x08 else 0):
                    R.fail("%s:%d CNB special %d for flags %#x" % (p, c["n"], d["special"], mf))
                if not mf & 0x08:
                    kind = "minion" if mf & 0x10 else "plain"
                    if c["cns"] or c["cnt"]:
                        R.fail("%s:%d non-special (flags %#x) got a name: %s %s" % (p, c["n"], mf, c["cns"], c["cnt"]))
                    else:
                        R.n("no name: flags %#x (%s)" % (mf, kind))
                    continue
                if mf & 0x02:
                    kind = "superunique"
                    idx = t.u16(t.su[u["su"]], 0x02) or 5382
                    want_s, want_t = [idx], [txt(idx)]
                elif mf & 0x04:
                    kind = "champion mod %d" % m
                    word = champ.get(m, 11087)
                    ns = t.u16(t.ms[u["cls"]], 0x06)
                    want_s = [word, ns, 11072]
                    want_t = [fmt_text(txt(11072), [txt(word), txt(ns)])]
                elif m == 12:
                    kind = "unique mod 12"
                    want_s, want_t = [3111], [txt(3111)]
                elif u["cls"] in t.sp.name_fixed:
                    kind = "fixed boss class"
                    R.note("%s:%d fixed-name class %d: %s %s" % (os.path.basename(p), c["n"], u["cls"], c["cns"], c["cnt"]))
                    R.n("names: fixed boss class")
                    continue
                else:
                    r = c["cnr"]
                    if len(r) == 2 and [k for k, _ in r] == ["S", "P"]:
                        kind = "unique 1721"
                        s_, p_ = r[1 - 1][1], r[1][1]
                        want_s = [1721]
                        want_t = [fmt_text(txt(1721), [txt(t.uprefix[p_]), txt(t.usuffix[s_])])]
                    elif len(r) == 5 and [k for k, _ in r] == ["S", "P", "A", "S", "P"]:
                        kind = "unique 1722"
                        a_, s_, p_ = r[2][1], r[3][1], r[4][1]
                        want_s = [1721, 1722] if 1721 in c["cns"] else [1722]
                        want_t = [fmt_text(txt(1722), [txt(t.uprefix[p_]), txt(t.usuffix[s_]), txt(t.uapp[a_])])]
                    else:
                        R.fail("%s:%d unique name rolls %s" % (p, c["n"], r))
                        continue
                    if c["cn0"] is None or c["cn0"]["ns"] != u["ns"]:
                        R.fail("%s:%d builder seed init %s, unit name seed %s" % (p, c["n"], c["cn0"], u["ns"]))
                    else:
                        R.n("builder Init(name seed) per call")
                if sorted(c["cns"]) != sorted(want_s) or c["cnt"] != want_t:
                    R.fail("%s:%d %s class %d: strings %s text %s; model %s %s" % (
                        p, c["n"], kind, u["cls"], c["cns"], c["cnt"], want_s, want_t))
                else:
                    R.n("names reproduced: " + kind.split(" mod ")[0] if kind.startswith("champion") else "names reproduced: " + kind)
                    if kind.startswith("champion"):
                        R.n("champion calls: mod %d" % m)
            # champion order: the client calls the builder for mod 1 first, then the champion mod; the last text wins
            if mf & 0x0C == 0x04 and b["calls"]:
                ms = [c["d"]["m"] for c in b["calls"]]
                R.n("champion builder call sequences %s" % ms)
                if ms[0] != 1 or ms[-1] not in (16, 36, 37, 38, 39):
                    R.fail("%s:%d champion builder order %s" % (p, b["n"], ms))
    return R.out()


# --- restores and MonMakeSpecial -----------------------------------------------------------------------------------
def part_restore(paths):
    R, t = Report("restore"), T.get()
    for p in paths:
        first_ns = {}        # (cls, id) -> name seed of the first instance (SMAX / SUX / an earlier restore)
        rs = None
        mn = None
        aurs_u = collections.defaultdict(list)
        ukey, first_aura = {}, {}
        for tag, d, n in parse(p):
            if tag == "SMAX" and d.get("u"):
                first_ns.setdefault((d["u"]["cls"], d["u"]["id"]), d.get("ns"))
            elif tag == "SUX" and d.get("unit"):
                u = d["unit"]
                if isinstance(u, dict) and "ns" in u:
                    first_ns.setdefault((u["cls"], u["id"]), u["ns"])
            elif tag == "SI0":
                ukey[d["u"]] = (d["cls"], d["id"])
            elif tag == "AURS":
                aurs_u[d["u"]].append((d.get("row"), d["skill"], d["lvl"], n))
                if d["u"] in ukey:
                    first_aura.setdefault(ukey[d["u"]], (d.get("row"), d["skill"], d["lvl"]))
            elif tag == "RS0":
                rs = {"rs0": d, "n": n}
                R.n("SpecialMonRestore calls")
                R.n("SpecialMonRestore return %08x" % d["ret"])
            elif tag in ("RS1", "RS2", "RSX") and rs is not None:
                rs[tag] = d
                if tag == "RSX":
                    saved = rs["rs0"]["saved"]
                    u1, u2 = rs.get("RS1"), rs.get("RS2")
                    if u1 is None or u2 is None:
                        R.fail("%s:%d restore without RS1/RS2" % (p, n))
                        rs = None
                        continue
                    if saved is not None and u1.get("mods") != saved:
                        R.fail("%s:%d restored mods %s, saved %s" % (p, n, u1.get("mods"), saved))
                    else:
                        R.n("restore: mods equal the saved bytes")
                    key = (u2["cls"], u2["id"])
                    if u1.get("ns") == u2.get("ns") and u2.get("ns") != first_ns.get(key):
                        R.n("restore: name seed unchanged by the write")
                    if key in first_ns:
                        if first_ns[key] == u2.get("ns"):
                            R.n("restore: name seed = the first instance's")
                        else:
                            R.fail("%s:%d restored name seed %s, first instance %s" % (p, n, u2.get("ns"), first_ns[key]))
                    else:
                        R.n("restore: first instance not in the log")
                        first_ns[key] = u2.get("ns")
                    au = [a for a in aurs_u.get(u2["u"], []) if a[3] > rs["n"]]
                    if saved and 30 in saved:
                        # the apply's call draws on the fresh name seed (RS1), the second call (0x005A457E) on the
                        # restored one (RS2): the second gives the first instance's aura, the first another one or the same
                        R.n("restore with aura: AURS calls %d" % len(au))
                        fa = first_aura.get(key)
                        if len(au) != 2:
                            R.fail("%s:%d aura restore calls %s" % (p, n, au))
                        elif fa is not None and au[1][:3] != fa:
                            R.fail("%s:%d aura restore: second call %s, first instance %s" % (p, n, au[1][:3], fa))
                        else:
                            R.n("restore with aura: second call = the first instance's aura" if fa else
                                "restore with aura: first instance not in the log")
                            R.n("restore with aura: the apply's call gave %s row" % ("the same" if au[0][:3] == au[1][:3] else "another"))
                    R.note("%s:%d restore class %d (%s) id %d flags %#x mods %s ns %s" % (
                        os.path.basename(p), n, u2["cls"], t.name(u2["cls"]), u2["id"], u2.get("mf", 0), u2.get("mods"),
                        u2.get("ns")))
                    rs = None
            elif tag == "MNR0":
                mn = {"d": d, "h": [], "n": n}
                R.n("MinionRestore calls")
            elif tag == "MNRH" and mn is not None:
                mn["h"].append(d["m"])
            elif tag == "MNRX" and mn is not None:
                saved = mn["d"]["saved"] or [0] * 9
                want = [m for m in [1, 2, 3, 4] + list(saved) if 0 <= m < len(t.handler) and t.handler[m]]
                if mn["h"] != want:
                    R.fail("%s:%d MinionRestore handler calls %s, model %s" % (p, n, mn["h"], want))
                else:
                    R.n("MinionRestore handler sequence reproduced")
                if d.get("mods") != list(saved):
                    R.fail("%s:%d MinionRestore mods %s saved %s" % (p, n, d.get("mods"), saved))
                else:
                    R.n("MinionRestore mods equal the saved bytes")
                mn = None
            elif tag == "MMS0":
                R.n("MonMakeSpecial calls (return %08x)" % d["ret"])
    return R.out()


# --- MonPlace ------------------------------------------------------------------------------------------------------
FIXED = {17: 19, 18: 58, 22: 141, 23: 278, 29: 453, 30: 492, 31: 522, 32: 438}   # spec monsters/special H, 0x0054E984..
MODE12 = {29, 30, 31, 32}
FALLEN = {(19, 6): 20, (19, 7): 21, (19, 12): 21, (19, 16): 21, (58, 6): 59, (58, 7): 59, (58, 12): 60, (58, 16): 60}


def part_monplace(paths):
    R, t = Report("monplace"), T.get()
    for p in paths:
        cur = None
        for tag, d, n in parse(p):
            if tag == "PMA0":
                cur = {"d": d, "v": {}, "mu": [], "n": n}
            elif cur is None:
                continue
            elif tag == "PMAV":
                cur["v"][d["k"]] = d
            elif tag == "MU":
                cur["mu"].append(d["unit"]["cls"] if d.get("unit") else None)
            elif tag == "PMAX":
                a = cur["d"]
                c, lid, diff = a["case"], a["lid"], a["diff"]
                v = cur["v"]
                key = "case %d" % c
                R.n(key + (" diff %s" % diff))
                if 0x11 <= c <= 0x20:
                    c0 = v.get("c0", {}).get("v")
                    lv, fv = v.get("lv", {}).get("v"), v.get("fv", {}).get("v")
                    if c in FIXED:
                        want = FIXED[c] if not (c == 30 and lid == 110) else 529
                        if c0 != want:
                            R.fail("%s:%d case %d level %d: class %s, spec %d" % (p, n, c, lid, c0, want))
                        if (c in MODE12) != (v.get("c0", {}).get("mode") == 12):
                            R.fail("%s:%d case %d mode %s" % (p, n, c, v.get("c0", {}).get("mode")))
                    if fv is not None and lv is not None and FALLEN.get((lv, lid), lv) != fv:
                        R.fail("%s:%d case %d level %d: PresetFallenVariant %d -> %d" % (p, n, c, lid, lv, fv))
                    made = [x for x in cur["mu"] if x is not None]
                    R.note("%s:%d case %d level %d diff %s: c0 %s lv %s fv %s g0 %s gv %s created %s eax %s" % (
                        os.path.basename(p), cur["n"], c, lid, diff, c0, lv, fv, v.get("g0", {}).get("v"),
                        v.get("gv", {}).get("v"), made, "%08x" % d["eax"]))
                    if fv is not None and made and made[0] != fv:
                        R.fail("%s:%d case %d: created %s, class %s" % (p, n, c, made, fv))
                    if lv is not None and c0 is not None:
                        R.n("LevelClassVariant %s -> %s (level %d)" % (t.name(c0), t.name(lv), lid))
                    if fv is not None and fv != lv:
                        R.n("PresetFallenVariant %s -> %s (level %d)" % (t.name(lv), t.name(fv), lid))
                    if c in FIXED and fv is not None:
                        R.n("fixed-class cases reproduced")
                    if "g0" in v:
                        R.n("group branch case %d diff %s" % (c, diff))
                elif c in (2, 3):
                    R.n("case 2/3 (modelled by monspawn)")
                cur = None
    return R.out()


# --- the wanderer tick ---------------------------------------------------------------------------------------------
def part_tick(paths):
    R = Report("tick")
    for p in paths:
        last = {}
        open_ = None
        for tag, d, n in parse(p):
            if tag == "RTK0":
                open_ = d
            elif tag == "RTK1" and open_ is not None and open_["room"] == d["room"]:
                r0 = seed_t(open_["rs"])
                s1 = step(*r0)
                pop = open_["f34"] & 1
                kind = "populated" if pop else "new"
                if fmt(s1) == d["rs"]:
                    R.n("ticks one step (%s room)" % kind)
                elif (s1[0] & 0x7FFF) == 0:
                    R.n("ticks with the wanderer roll (%s room)" % kind)
                else:
                    R.fail("%s:%d tick room %d: %s -> %s, one step %s" % (p, n, d["room"], open_["rs"], d["rs"], fmt(s1)))
                if d["gs"] != open_["gs"]:
                    R.n("ticks that moved the game seed (%s)" % kind)
                if d["room"] in last and pop:
                    if last[d["room"]] == open_["rs"]:
                        R.n("populated rooms: seed carried from the previous tick")
                    else:
                        R.n("populated rooms: other draws between ticks")
                last[d["room"]] = d["rs"]
                open_ = None
    return R.out()


# --- tentacles -----------------------------------------------------------------------------------------------------
def part_tentacle(paths):
    R, t = Report("tentacle"), T.get()
    for p in paths:
        units = {}
        mt_stack = []
        pending = None          # the head whose minions are being made
        last_mu0, head = None, None
        for tag, d, n in parse(p):
            if tag == "MT0":
                mt_stack.append(d)
                if pending is not None and pending["left"] > 0 and d["d"] == pending["d"] + 1:
                    o, j = pending["o"], pending["j"]
                    dx, dy = t.tent[2 * (o * 6 + j)], t.tent[2 * (o * 6 + j) + 1]
                    want = (pending["room"], 0, pending["m1"], 1, 0, pending["x"] + dx, pending["y"] + dy, -1, 0x40)
                    got = (d["room"], d["box"], d["cls"], d["a10"], d["a14"], d["x"], d["y"], d["rad"], d["fl"])
                    if got != want:
                        R.fail("%s:%d limb request %s, model %s" % (p, n, got, want))
                    else:
                        R.n("limb requests reproduced")
                    R.n("limb offset row %d" % (o * 6 + j))
                    pending["j"] = (j + 5) % 6
                    pending["left"] -= 1
            elif tag == "MTX":
                if mt_stack:
                    mt_stack.pop()
            elif tag == "MU0":
                last_mu0 = d
            elif tag == "MU" and d.get("unit") and mt_stack and last_mu0 is not None:
                u = d["unit"]
                units[u["u"]] = {"cls": u["cls"], "x": last_mu0["x"], "y": last_mu0["y"], "room": mt_stack[-1]["room"],
                                 "fl": mt_stack[-1]["fl"], "d": mt_stack[-1]["d"]}
            elif tag == "MM0":
                head = d
            elif tag == "MMT":
                U = units.get(head["unit"]) if head else None
                if U is None:
                    R.fail("%s:%d MMT for an unknown unit" % (p, n))
                    continue
                c = U["cls"]
                rec = t.ms[c]
                lo, hi = rec[0x2C], rec[0x2D]
                s0 = seed_t(head["us"])
                s = s0
                if lo >= hi:
                    cnt = lo
                else:
                    s = step(*s)
                    cnt = lo + s[0] % (hi - lo + 1)
                if (d["n"], d["us"]) != (cnt, fmt(s)):
                    R.fail("%s:%d tentacle count %d us %s, model %d %s" % (p, n, d["n"], d["us"], cnt, fmt(s)))
                    continue
                R.n("tentacle heads (BaseId %d)" % t.base(c))
                s2 = step(*s)
                o = (~(U["fl"] >> 2)) & 1
                R.n("tentacle heads o=%d" % o)
                pending = {"o": o, "j": s2[0] % 6, "left": cnt, "m1": t.s16(rec, 0x26), "x": U["x"], "y": U["y"],
                           "room": U["room"], "d": U["d"], "us": fmt(s2), "head": head["unit"]}
            elif tag == "MMX" and pending is not None and d["unit"] == pending["head"]:
                if pending["left"]:
                    R.fail("%s:%d %d limb requests missing" % (p, n, pending["left"]))
                if d["us"] != pending["us"]:
                    R.fail("%s:%d head seed at exit %s, model %s (one extra step)" % (p, n, d["us"], pending["us"]))
                else:
                    R.n("tentacle exits: head seed one step after the count")
                pending = None
    return R.out()


# --- collision masks and the class cell test ----------------------------------------------------------------------
MASKS = {1: 0x01C0, 2: 0x3F11, 3: 0}


def part_masks(paths):
    R, t = Report("masks"), T.get()
    for p in paths:
        stack = []
        for tag, d, n in parse(p):
            if tag == "MT0":
                stack.append(d)
            elif tag == "MTX":
                if stack:
                    stack.pop()
            elif tag == "MK0" and stack:
                c = stack[-1]["cls"]
                sc = t.spawncol(c)
                want = MASKS.get(sc, 0x3C01)
                R.n("MK0 spawnCol %s mask %#x" % (sc, d["mask"]))
                if sc in (1, 3):
                    R.n("MK0 spawnCol %d classes %s" % (sc, t.name(c)))
                if d["mask"] != want:
                    R.fail("%s:%d class %d spawnCol %s: mask %#x, model %#x" % (p, n, c, sc, d["mask"], want))
            elif tag == "MC" and stack:
                c = stack[-1]["cls"]
                if c in (206, 228, 298, 334, 528):
                    R.n("SpawnClassCellTest %s result %s" % (t.name(c), d["r"]))
    return R.out()


# --- player count ----------------------------------------------------------------------------------------------------
HIRE = {271, 338, 359, 560, 561}


def part_players(paths):
    R, t = Report("players"), T.get()
    for p in paths:
        si0, ucls = {}, {}
        for tag, d, n in parse(p):
            if tag == "SI0":
                si0[d["u"]] = d
            elif tag == "SI1" and d["u"] in si0:
                a = si0.pop(d["u"])
                c = a["cls"]
                al = t.align(c)
                pl = a.get("pset")
                if c in (311, 312):
                    R.n("doomknight %d creations" % c)
                if t.base(c) == 118:
                    R.n("willowisp-base creations (%s)" % t.name(c))
                if al in (1, 2) or c in HIRE:
                    key = "Align %d %s /players %s: record players %d hp%% %d" % (
                        al, t.name(c), pl, d["pb"][4], d["pb"][0])
                    R.n(key)
                    if pl and pl > 1 and (d["pb"][4] != 1 or d["pb"][0] != 0):
                        R.fail("%s:%d class %d Align %d at /players %d: record %s" % (p, n, c, al, pl, d["pb"]))
            if tag == "SI0":
                ucls[d["u"]] = d["cls"]
            elif tag in ("HST", "TST"):
                u = d.get("u")
                c = ucls.get(u)
                if c is not None and t.base(c) == 118 and d.get("m") in (5, 16, 39):
                    R.n("willowisp-base %s calls of %s (stat 25 halved by monstats.py)" % (
                        tag, {5: "strong", 16: "champion", 39: "berserk"}[d["m"]]))
    return R.out()


# --- watchpoints -----------------------------------------------------------------------------------------------------
def symbols():
    out = []
    with open(os.path.join(ROOT, "re", "symbols.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            if r["kind"] == "func":
                out.append((int(r["address"], 16), r["name"]))
    out.sort()
    return out


def part_watch(paths):
    R = Report("watch")
    syms = symbols()
    addrs = [a for a, _ in syms]
    for p in paths:
        for tag, d, n in parse(p):
            if tag == "WCHARM":
                R.n("armed %s%s" % (d["what"], "" if d.get("lid") is None else " level %d" % d["lid"]))
            elif tag == "WCH":
                i = bisect.bisect_right(addrs, d["pc"]) - 1
                fn = syms[i][1] if i >= 0 else "?"
                R.n("hit %s%s pc %08x in %s" % (d["what"], "" if d.get("lid") is None else " level %d" % d["lid"], d["pc"], fn))
    return R.out()


def part_hwt(paths):
    R = Report("hwt")
    for p in paths:
        for tag, d, n in parse(p):
            if tag == "HWT":
                R.n("HWT level %s" % d["lid"])
                R.n("HWT bit already set" if d["f28"] & 0x800000 else "HWT bit set by this write")
    return R.out()


PARTS = {"sik": part_sik, "aura": part_aura, "names": part_names, "restore": part_restore, "monplace": part_monplace,
         "tick": part_tick, "tentacle": part_tentacle, "masks": part_masks, "players": part_players,
         "watch": part_watch, "hwt": part_hwt}


def main(argv):
    global VERBOSE
    if "-v" in argv:
        VERBOSE = True
        argv = [a for a in argv if a != "-v"]
    if len(argv) < 2 or (argv[0] not in PARTS and argv[0] != "check"):
        print(__doc__)
        return 2
    paths = argv[1:]
    parts = list(PARTS) if argv[0] == "check" else [argv[0]]
    rc = 0
    for k in parts:
        rc |= PARTS[k](paths)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
