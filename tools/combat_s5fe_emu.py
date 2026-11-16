#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S5fe (`lane/n66w`): the missile critical chain and the progressive finisher's entry tests
under Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java, compared with the models
below.

    python3 -I tools/combat_s5fe_emu.py cases [--dir D]     write D/s5fe.cases, D/s5fe.mem and the table images
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/s5fe.cases D/s5fe.mem > D/s5fe.out
    python3 -I tools/combat_s5fe_emu.py check [--dir D]     compare, account for every traced read and write, controls
    python3 -I tools/combat_s5fe_emu.py static [--dir D]    the objdump reads the record cites (call sites, pops)
    python3 -I tools/combat_s5fe_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66w/s5fe/run. Every draw comes from random.Random("n66w-s5fe-<family>"). The declared
tables are batch S5e part 3's (tools/combat_s5e3_emu.py write_spec, unchanged: its seeded MonStats, ItemStatCost,
ItemTypes equivalence words and item records), written into D under their own names; this file adds only its own
observe lines.

Every callee runs whole on the declared image (ruling R2: no declared return) unless named as an observed boundary
(ADR-0021): the case ends at that call and its claim ends there. The allocator entries and the fatal path are guards.

Families (function, registers; inventory rows):
  crit 0x0064A850 sub_0064A850_MissileCritRoll (ESI unit; weapon), run whole to its return. Callees whole:
       STATS_GetUnitStat 0x00625480 (stat 337), sub_00625500_UnitGetStat (stat 141), SKILLS_GetMasteryBonus
       0x00645830 (unit, weapon, 0, 2) with UNIT_GetUsedSkill 0x00620250 / 0x006439A0 (the unit's skill list +0xA8
       null: no used skill), 0x00645720 (with no used skill it returns 0 and clears its flag, so the stat-344 entries
       decide), sub_006261D0_StatListGetEntries (stat 344 = 0x158), ITEMS_UnitIsType 0x00629BB0 with
       ITEMS_GetType/ITEMS_GetRecord.                                README 22, 23, 42; remainders README 18, 21, 32, 34.
  fin  0x005D5220 COMBAT_PrgFinisher (ECX game, EDX att; hit): its entry tests. A null hit or one whose result word
       (+4) lacks bit 0x1 returns; otherwise the case ends at UNIT_GetTargetUnit 0x00553540 (observed, from
       0x005D5244).                                                   delivery 7 (the finisher's half).

Controls as S5e: every named test reversed alone, every ordered compare's strictness switched alone; `sep` counts the
cases a control changes, `passed` those the emulator still matches (must be 0); `spec_*` controls are the spec's own
readings. Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import combat_s5e_emu as p1  # noqa: E402
import combat_s5e3_emu as p3  # noqa: E402
import anim_s6f_emu as f6  # noqa: E402
from combat_s5e_emu import (E, u32, s32, le32, put_unit, stat, lcg, ATT, GAME, SL_OFF, ARR_OFF,  # noqa: E402
                            FATAL, ALLOC)

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66w", "s5fe", "run")
FNS = {"crit": 0x0064A850, "fin": 0x005D5220}
FAMILIES = ("crit", "fin")
NCASES = {"crit": 3000, "fin": 600}
POP = {"crit": 4, "fin": 4}
OBS_TGT = 0x00553540
SITE = {("fin", OBS_TGT): 0x005D5249}
HIT = 0x20004100
WPN = f6.IT
ST_DS, ST_CB, ST_MAST = 337, 141, 0x158
p1.FNS.update(FNS)


class Case(p1.Case):
    """part 1's case; its call line names this file's function (p1.FNS gains these keys in memory only)."""


# ----------------------------------------------------------------------------------------------- crit
def chance(rnd):
    return rnd.choice([0, 0, rnd.randint(1, 99), rnd.randint(1, 99), 100, rnd.randint(101, 300),
                       rnd.randint(-99, -1), -rnd.randint(1, 1 << 31), rnd.getrandbits(32), None])


def gen_crit(rnd):
    c = Case("crit")
    seed = (rnd.getrandbits(32), rnd.getrandbits(32))
    s, rr = list(seed), []
    for _ in range(3):                                          # the three rolls' remainders on this seed
        rr.append(lcg(s) % 100)
    eq = rnd.random() < 0.25                                    # a chance equal to its roll: the strictness cases
    sv = {ST_DS: rr[0] if eq and rnd.random() < 0.4 else chance(rnd),
          ST_CB: rr[1] if eq and rnd.random() < 0.5 else chance(rnd)}
    if rnd.random() < 0.3:                                      # bias toward the third step
        sv[ST_DS] = rnd.choice([0, -rnd.randint(1, 50), None])
        sv[ST_CB] = rnd.choice([0, -rnd.randint(1, 50), None, rr[1]])
    u = put_unit(c, rnd, ATT, rnd.choice([0, 0, 1]), rnd.randrange(7), sv, [], listflag=True, seed=seed)
    c.put(ATT + 0xA8, le32(0))                                  # no skill list: no used skill
    ent = []
    if rnd.random() < 0.75:                                     # stat-344 entries (layer = an item type)
        tys = [rnd.randrange(f6.TY_N), rnd.randrange(f6.TY_N), rnd.choice([64, 70, 0x7FFF, 0xFFFF])]
        for ly in sorted(set(rnd.choice(tys) for _ in range(rnd.randint(1, 4)))):
            ent.append((ly, rnd.choice([rnd.randint(1, 99), rnd.randint(1, 99), 0, -rnd.randint(1, 50), 100,
                                        rnd.randint(101, 200)] + [rr[2]] * (3 if eq else 0))))
    keys = {(s << 16): u32(v) for s, v in u["stats"].items() if s != ST_MAST}
    for ly, v in ent:
        keys[(ST_MAST << 16) | ly] = u32(v)
    ks = sorted(keys)
    for i, k in enumerate(ks):
        c.put(ATT + ARR_OFF + 8 * i, le32(k) + le32(keys[k]))
    c.put(ATT + SL_OFF + 0x4C, struct.pack("<H", len(ks)) + bytes(2))
    u["stats"] = {k >> 16: s32(v) for k, v in keys.items() if not k & 0xFFFF}
    w = None
    if rnd.random() < 0.7:
        cls = rnd.randrange(f6.IREC_N)
        if ent and rnd.random() < 0.6:                          # bias: a weapon whose type matches an entry
            want = [ly for ly, _ in ent if ly < f6.TY_N]
            hits = [i for i in range(f6.IREC_N) if want and any(p3.Img3.typ(i, t) for t in want)]
            if hits:
                cls = rnd.choice(hits)
        w = dict(type=4, cls=cls)
        c.put(WPN, le32(4) + le32(cls) + bytes(0x38))
    c.regs = {"ESI": ATT}
    c.args = [WPN if w else 0]
    c.dumps = [(ATT + 0x20, 8)]
    c.a = dict(u=u, ent=ent, w=w)
    return c


def m_crit(e, a):
    u = a["u"]
    seed = list(u["seed"])

    def roll(name, ch):
        lo = lcg(seed)
        r = u32(lo - 100 * (lo // 100))                         # the inline remainder, 0..99
        if e.flip == "spec_unsigned":
            return r < u32(ch)
        e.names.add("spec_unsigned")
        return e.c(name, s32(r), "<", s32(ch))

    if roll("lt_337", stat(u, ST_DS)):
        return ("ret", 1, tuple(seed))
    v = stat(u, ST_CB)
    e.names.add("spec_141_gt0")
    step = (v > 0) if e.flip == "spec_141_gt0" else e.t("nz_141", v != 0)
    if step and roll("lt_141", v):
        return ("ret", 1, tuple(seed))
    if e.t("weapon", a["w"] is not None):
        best = 0
        for ly, val in a["ent"]:
            if e.t("ly_in", ly < f6.TY_N) and e.t("is_type", f6.is_type(e, a["w"], ly)) and \
                    e.c("best_lt", best, "<", s32(val)):
                best = s32(val)
        if e.t("nz_m", best != 0) and roll("lt_m", best):
            return ("ret", 1, tuple(seed))
    return ("ret", 0, tuple(seed))


# ----------------------------------------------------------------------------------------------- fin
def gen_fin(rnd):
    c = Case("fin")
    put_unit(c, rnd, ATT, 0, rnd.randrange(7), {}, [], nolist=True)
    k = rnd.choice(["null", "clear", "clear", "set"])
    pk = [rnd.getrandbits(32) for _ in range(0x70 // 4)]
    if k == "clear":
        pk[1] &= ~1
    elif k == "set":
        pk[1] |= 1
    c.put(HIT, b"".join(le32(x) for x in pk))
    c.ecx, c.edx = GAME, ATT
    c.args = [0 if k == "null" else HIT]
    c.dumps = [(ATT, 0x100), (HIT, 0x70)]
    c.a = dict(k=k, att=bytes(c.w[ATT + i] for i in range(0x100)), pk=b"".join(le32(x) for x in pk))
    return c


def m_fin(e, a):
    if e.t("hit_nz", a["k"] != "null") and e.t("res_bit0", a["k"] == "set"):
        return ("obs", OBS_TGT, (GAME, ATT), a["att"], a["pk"])
    return ("ret", a["att"], a["pk"] if a["k"] != "null" else None)


GEN = {"crit": gen_crit, "fin": gen_fin}
MODEL = {"crit": m_crit, "fin": m_fin}


def predict(fam, a, flip=None):
    e = E(flip)
    try:
        out = MODEL[fam](e, a)
    except (TypeError, KeyError, IndexError, AttributeError):
        return ("model-null",), e.names
    return out, e.names


# ----------------------------------------------------------------------------------------------- files
def write_spec(d):
    p3.write_spec(d)
    lines = [x for x in open(os.path.join(d, "s5e3.mem")).read().splitlines() if not x.startswith("observe ")]
    lines[0] = "# plan 0066 S5fe (tools/combat_s5fe_emu.py): S5e part 3's declared tables, this batch's boundaries"
    lines += ["observe %08x" % OBS_TGT]
    os.remove(os.path.join(d, "s5e3.mem"))
    with open(os.path.join(d, "s5fe.mem"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


def build(limit=None):
    cases = []
    for fam in FAMILIES:
        rnd = random.Random("n66w-s5fe-" + fam)
        for _ in range(NCASES[fam] if limit is None else min(limit, NCASES[fam])):
            cases.append(GEN[fam](rnd))
    return cases


def cmd_cases(d, limit=None):
    os.makedirs(d, exist_ok=True)
    write_spec(d)
    cases = build(limit)
    with open(os.path.join(d, "s5fe.cases"), "w") as fh:
        for c in cases:
            fh.write("\n".join(c.lines()) + "\n")
    print("cases %d -> %s" % (len(cases), os.path.join(d, "s5fe.cases")))


def observed(fam, c):
    if "stop" in c:
        return ("stop", c["stop"], c["msg"]), None
    dump = c["dumps"]
    if "obs" in c:
        st = c["stack"]
        ret = struct.unpack_from("<I", st, 0)[0]
        regs = (int(c["regs"]["ecx"], 16), int(c["regs"]["edx"], 16))
        return ("obs", c["obs"], regs, dump[ATT], dump[HIT]), ret
    if c["pop"] != POP[fam]:
        return ("pop", c["pop"]), None
    if fam == "crit":
        return ("ret", c["eax"], struct.unpack("<2I", dump[ATT + 0x20])), None
    return ("ret", dump[ATT], dump[HIT]), None


def same(fam, want, got, a):
    if want[0] == "model-null" or want[0] != got[0] or len(want) != len(got):
        return False
    for w, g in zip(want, got):
        if w is None:
            continue
        if isinstance(w, (tuple, list)):
            if g is None or tuple(w) != tuple(g):
                return False
        elif w != g:
            return False
    return True


def kind(want, a):
    if want[0] == "obs":
        return "obs:%x" % want[1]
    if want[0] == "ret" and isinstance(want[1], int):
        return "ret=%d" % want[1]
    return want[0] + ("" if "k" not in a else ":" + a["k"])


def steps(a):
    """the number of seed steps a crit case makes (its seed's distance from the input)."""
    s = list(a["u"]["seed"])
    want, _ = predict("crit", a)
    for n in range(4):
        if tuple(s) == tuple(want[2]):
            return n
        lcg(s)
    return -1


def cmd_check(d, limit=None, controls=True):
    cases = build(limit)
    calls, reads, writes = p1.read_out(os.path.join(d, "s5fe.out"))
    if len(calls) != len(cases):
        print("CASES %d emulated %d: mismatch" % (len(cases), len(calls)))
        return 1
    bad = 0
    per = {f: [0, 0, {}] for f in FAMILIES}
    names_by_fam = {f: set() for f in FAMILIES}
    got_all = []
    for i, (c, k) in enumerate(zip(cases, calls)):
        fam = c.fam
        want, names = predict(fam, c.a)
        names_by_fam[fam] |= names
        got, site = observed(fam, k)
        ok = same(fam, want, got, c.a)
        if ok and want[0] == "obs":
            ok = site == SITE[(fam, want[1])]
        per[fam][0] += 1
        kd = kind(want, c.a)
        if fam == "crit":
            kd += "/steps=%d" % steps(c.a)
        per[fam][2][kd] = per[fam][2].get(kd, 0) + 1
        if not ok:
            per[fam][1] += 1
            bad += 1
            if bad <= 25:
                print("MISMATCH %d %s want=%r got=%r site=%r" % (i, fam, want, got, site))
        got_all.append(got)
    # rows: the separating classes the record cites
    tally = {}
    for c in cases:
        if c.fam != "crit":
            continue
        a = c.a
        v1, v2 = stat(a["u"], ST_DS), stat(a["u"], ST_CB)
        n = steps(a)
        for name, cond in (("337_neg", v1 < 0), ("337_ge100", v1 >= 100), ("141_neg_stepped", v2 < 0 and n >= 2),
                           ("141_zero_no_step", v2 == 0 and n == 1 and a["w"] is None),
                           ("third_step", n == 3), ("weapon_mastery_0", a["w"] is not None and n < 3),
                           ("neg_entry", any(v < 0 for _, v in a["ent"])),
                           ("ly_out", any(ly >= f6.TY_N for ly, _ in a["ent"]))):
            if cond:
                tally[name] = tally.get(name, 0) + 1
    print("ROWS " + " ".join("crit:%s=%d" % kv for kv in sorted(tally.items())))
    for f in FAMILIES:
        n, b, kinds = per[f]
        print("FAMILY %s cases=%d mismatches=%d outcomes %s" % (f, n, b, " ".join(
            "%s:%d" % kv for kv in sorted(kinds.items()))))
    ctl_bad, ctl_lines = 0, []
    if controls:
        for f in FAMILIES:
            fc = [(c, g) for c, g in zip(cases, got_all) if c.fam == f]
            base = [predict(f, c.a)[0] for c, _ in fc]
            for nm in sorted(names_by_fam[f]):
                sep = passed = 0
                for (c, got), b in zip(fc, base):
                    alt, _ = predict(f, c.a, flip=nm)
                    if not same(f, b, alt, c.a) or not same(f, alt, b, c.a):
                        sep += 1
                        if same(f, alt, got, c.a):
                            passed += 1
                ctl_lines.append("CONTROL %s %s sep=%d passed=%d" % (f, nm, sep, passed))
                if passed:
                    ctl_bad += 1
        print("\n".join(ctl_lines))
    nsep0 = sum(1 for x in ctl_lines if " sep=0 " in x)
    acc = p3.account(reads, writes)
    for x in acc[:40]:
        print("UNACCOUNTED %s pc=%08x addr=%08x n=%d count=%d" % x)
    traced = {}
    for pc, addr, n, cnt in reads:
        traced[pc] = traced.get(pc, 0) + cnt
    print("TRACED " + " ".join("%08x:%d" % kv for kv in sorted(traced.items())))
    stops = sum(1 for k in calls if "stop" in k)
    print("S5FE total cases=%d mismatches=%d stops=%d controls=%d unseparated=%d controls_passed=%d unaccounted=%d"
          % (len(cases), bad, stops, len(ctl_lines), nsep0, ctl_bad, len(acc)))
    return 1 if bad or ctl_bad or acc else 0


# ----------------------------------------------------------------------------------------------- static
STATIC = (
    # (label, lo, hi): objdump listings the record cites; each printed line is an instruction of the pinned image
    ("crit-body", 0x0064A850, 0x0064A930),
    ("fin-entry", 0x005D5220, 0x005D5250),
    ("fin-peek", 0x005D5368, 0x005D5391),
    ("fin-ret", 0x005D549E, 0x005D54A6),
    ("fin-tail", 0x005D5442, 0x005D546A),
    ("copy64", 0x00650E60, 0x00650E83),
    ("do52-finisher", 0x005D79C0, 0x005D79E8),
    ("mdb-crit-sites", 0x0064BAC4, 0x0064BAD8),
    ("mdb-src-site", 0x0064BCFE, 0x0064BD1A),
    ("raq-queue", 0x0057DC80, 0x0057DC9D),
    ("queuehit-alloc", 0x0057CA80, 0x0057CAD0),
    ("qhremove-free", 0x0057CA50, 0x0057CA74),
    ("dragontalonhit", 0x005D5940, 0x005D5966),
    ("msgA3-alloc", 0x00571AA0, 0x00571AD0),
)


def cmd_static(d):
    if p1.img() is None:
        return 1
    for label, lo, hi in STATIC:
        if lo == hi:
            continue
        out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-M", "intel", "--start-address=0x%x" % lo,
                              "--stop-address=0x%x" % hi, p1.EXE], capture_output=True, text=True, check=True).stdout
        for ln in out.splitlines():
            ln = ln.strip()
            if ln and ln[0] in "0123456789abcdef" and ":\t" in ln:
                print("%s %s" % (label, " ".join(ln.split())))
    # every access of the peek's slot [ebp-0x24] in the whole finisher (0x005D5220..0x005D54A6)
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-M", "intel", "--start-address=0x5d5220",
                          "--stop-address=0x5d54a6", p1.EXE], capture_output=True, text=True, check=True).stdout
    hits = [" ".join(x.split()) for x in out.splitlines() if "ebp-0x24]" in x]
    for h in hits:
        print("fin-slot24 %s" % h)
    print("fin-slot24 count=%d" % len(hits))
    return 0


def cmd_manifest(d, write):
    names = sorted(x for x in os.listdir(d) if os.path.isfile(os.path.join(d, x)) and x != "manifest.sha256")
    out = []
    for n in names:
        with open(os.path.join(d, n), "rb") as fh:
            out.append("%s  %s" % (hashlib.sha256(fh.read()).hexdigest(), n))
    text = "\n".join(out) + "\n"
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as fh:
            fh.write(text)
    print(text, end="")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "static", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    o = ap.parse_args(argv)
    if o.cmd == "cases":
        cmd_cases(o.dir, o.limit)
        return 0
    if o.cmd == "check":
        return cmd_check(o.dir, o.limit)
    if o.cmd == "static":
        return cmd_static(o.dir)
    cmd_manifest(o.dir, o.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
