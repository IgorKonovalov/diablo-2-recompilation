#!/usr/bin/env python3
"""Static scans behind docs/findings/skills/0002-missiles.md (plan 0045 Phase 1, batch P1.2).

Usage:
  python3 -I tools/skills_missiles_scan.py <game.exe>                 # all code sections
  python3 -I tools/skills_missiles_scan.py <game.exe> tables          # the missile function tables and their bounds
  python3 -I tools/skills_missiles_scan.py <game.exe> calls           # direct callers of the missile machinery
  python3 -I tools/skills_missiles_scan.py <game.exe> tabreads        # every instruction that names a table, with its bound test
  python3 -I tools/skills_missiles_scan.py <game.exe> ammo            # the useAmmo argument at each skill missile creator call
  python3 -I tools/skills_missiles_scan.py <game.exe> collmask        # the mask argument at each CollisionTest call
  python3 -I tools/skills_missiles_scan.py <game.exe> links           # word reads of the Missiles link fields after a 0x1A4 multiply
  python3 -I tools/skills_missiles_scan.py <game.exe> sites           # instruction windows the finding cites
  python3 -I tools/skills_missiles_scan.py <game.exe> rows <excel dir>  # (not in `all`) Missiles/Skills function numbers
                                                                      # against the tables. Counts and row ids only.

Reads the PE image for the tables (code addresses and counts only) and runs
`objdump -d -M intel --no-show-raw-insn` for the code scans. Prints addresses and counts, no game data, except
that `rows` names the few rows the finding discusses (row id and the function numbers). One `SCAN <section> ...`
summary line per section.
  tables   collide table 0x0073C720 (9 x {filter, mask}), do table 0x0073C768 (bound dword 0x0073C71C), hit table
           0x0073C840 (bound 0x0073C83C), damage table 0x0073C960 (bound 0x0073C95C); the skill do table 0x007322B0
           entries that equal the throw helpers.
  calls    `call 0x<target>` / `jmp 0x<target>` for each target in TARGETS, with the enclosing function.
  tabreads every operand naming a table base or bound, with the 4 instructions before it.
  ammo     for each call of 0x0056ECB0 / 0x0056EE90, the eighth `push` counted back from the call (the stack
           argument useAmmo, pushed first); `?` when a non-push instruction that writes ESP intervenes.
  collmask for each call of 0x0064D9B0 (CollisionTest), the fifth push back (the mask argument) and whether an
           immediate mask has bit 0x40.
  links    `WORD PTR [reg+off]` reads for off in 0x16 (ExplosionMissile), 0x18, 0x1A (SubMissile1/2), 0x24
           (HitSubMissile1) within 25 instructions after an `imul ...,0x1a4`, split server (0x0059F000-0x005E0000)
           and other.
Function starts: an address that follows padding or a `ret`/`jmp` and is a direct call target or a table entry.
"""
import bisect
import os
import re
import struct
import subprocess
import sys

COLL_TABLE, COLL_N = 0x0073C720, 9
DO_TABLE, DO_BOUND_AT = 0x0073C768, 0x0073C71C
HIT_TABLE, HIT_BOUND_AT = 0x0073C840, 0x0073C83C
DMG_TABLE, DMG_BOUND_AT = 0x0073C960, 0x0073C95C
SKILL_DO_TABLE, SKILL_DO_BOUND = 0x007322B0, 0xBF
SRV_LO, SRV_HI = 0x0059F000, 0x005E0000

TARGETS = {
    0x0059FA30: "sub_0059FA30_MissileCreate",
    0x0056ECB0: "sub_0056ECB0_SkillMissileCreate",
    0x0056EE90: "sub_0056EE90_SkillMissileCreateLob",
    0x0056EDE0: "sub_0056EDE0_MissileCreateAt",
    0x0059F900: "sub_0059F900_MissileInitDamage",
    0x0064B860: "sub_0064B860_MissileDamageBlock",
    0x0064A850: "sub_0064A850_CritRoll",
    0x0059F940: "sub_0059F940_MissilePierceCount",
    0x0056D810: "sub_0056D810_CallDoFunc",
    0x005ADBB0: "sub_005ADBB0_MissileDoFrame",
    0x005ADCC0: "sub_005ADCC0_MissileFrameEvent",
    0x005AE1F0: "sub_005AE1F0_MissileMoveCollide",
    0x005ADF10: "MISSILE_HitUnit",
    0x005A89A0: "MISSILE_BuildDamage",
    0x005AD730: "MISSILE_ApplyDamage",
    0x005ADCD0: "sub_005ADCD0_MissileApplyAndAc",
    0x005AD9D0: "sub_005AD9D0_MissileEndHit",
    0x005ADB00: "sub_005ADB00_MissileJustHitState",
    0x005ADA80: "sub_005ADA80_MissilePierceUse",
    0x00641CB0: "sub_00641CB0_FindUnitAtCell",
    0x0064D9B0: "sub_0064D9B0_CollisionTest",
}

SITES = [
    ("SkillMissileCreate: params, flags 0x21, stack args", 0x0056ECB0, 0x0056EDD4),
    ("SkillMissileCreateAt: distance test, flags 1", 0x0056EDE0, 0x0056EE84),
    ("SkillMissileCreateLob: flags 0x420, source = unit", 0x0056EE90, 0x0056EF8C),
    ("SrvDo: the srvmissile creation", 0x0056F9D0, 0x0056FA35),
    ("MissileCreate: position, target, velocity, distance test", 0x0059FA30, 0x0059FC50),
    ("MissileCreate: unit create, range, activate, path, damage, pierce", 0x0059FC51, 0x0059FED0),
    ("MissileInitDamage: registers to the damage block", 0x0059F900, 0x0059F937),
    ("CritRoll: three inline LCG steps on ESI's seed", 0x0064A850, 0x0064A92D),
    ("MissileDoFrame: town tests, do call, free on 2", 0x005ADBB0, 0x005ADCBD),
    ("MoveAndCollide (do 1)", 0x005AE1F0, 0x005AE3FA),
    ("HitUnit", 0x005ADF10, 0x005AE1E9),
    ("CallDoFunc bound", 0x0056D810, 0x0056D835),
    ("hit 22 -> CallDoFunc(sHitPar1)", 0x005AD012, 0x005AD03C),
    ("do 14 -> CallDoFunc(Param2) every Param1 frames", 0x005AEFAF, 0x005AF009),
    ("missile event queued every frame at creation", 0x0059F8A0, 0x0059F8DB),
    ("event record: frame -1, list by unit type", 0x005415E0, 0x0054164A),
    ("frame pass: the missile lists first", 0x005414D0, 0x0054150D),
    ("useAmmo by hand (AMMO ?): throw helpers 3 and 5, shared pushes before the lob test", 0x0056F4F5, 0x0056F524),
    ("useAmmo by hand: 0x0056F614", 0x0056F5E5, 0x0056F614),
    ("useAmmo by hand: SrvDo 0x0056FA29, pushes shared with the lob call", 0x0056F9FA, 0x0056FA29),
    ("useAmmo by hand: 0x005A377C and 0x005A37AB", 0x005A3758, 0x005A37AB),
    ("useAmmo by hand: 0x005CE08B", 0x005CE048, 0x005CE08B),
    ("useAmmo by hand: 0x005CE18B", 0x005CE148, 0x005CE18B),
    ("useAmmo by hand: 0x005D8952", 0x005D892F, 0x005D8952),
    ("do 3: the 0x40 cell mark while the path is not moving", 0x005AE480, 0x005AE51F),
    ("ApplyDamage: knockback draw on the missile seed", 0x005AD730, 0x005AD8EF),
    ("BuildDamage: the RangeB draws on the missile seed", 0x005A89A0, 0x005A8C6F),
    ("BuildDamage element helper", 0x005A8910, 0x005A899F),
    ("collide filters", 0x005A8730, 0x005A88D1),
    ("hit filter by CollideType", 0x005ADA40, 0x005ADA6D),
    ("pierce use and the justhit state", 0x005ADA80, 0x005ADBA8),
    ("pierce count at creation (local seed)", 0x0059F940, 0x0059FA2F),
]
KNOWN_STARTS = [0x0056F7F0, 0x0056F640, 0x0056F070, 0x0056F460, 0x0056F550, 0x005A8910, 0x005A8730, 0x005A87B0,
                0x005A87F0, 0x005A8850, 0x005A8890, 0x005ADA40, 0x005ADA80]
SKILL_ST_TABLE, SKILL_ST_BOUND = 0x00732140, 0x5B

INSN = re.compile(r"^\s*([0-9a-f]+):\s+(.*)$")


def pe_reader(path):
    d = open(path, "rb").read()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    n = struct.unpack_from("<H", d, pe + 6)[0]
    opt = struct.unpack_from("<H", d, pe + 20)[0]
    secs = []
    for i in range(n):
        o = pe + 24 + opt + 40 * i
        vs, va, rs, ro = struct.unpack_from("<IIII", d, o + 8)
        secs.append((va + 0x400000, vs, rs, ro))

    def dw(a):
        for va, vs, rs, ro in secs:
            if va <= a < va + max(vs, rs):
                return struct.unpack_from("<I", d, a - va + ro)[0] if a - va < rs else 0
        raise ValueError(hex(a))
    return dw


def disasm(path):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", path],
                         capture_output=True, text=True, check=True).stdout
    insns = []
    for line in out.splitlines():
        m = INSN.match(line)
        if m:
            insns.append((int(m.group(1), 16), m.group(2).strip()))
    return insns


def tables(dw):
    coll = [(dw(COLL_TABLE + 8 * i), dw(COLL_TABLE + 8 * i + 4)) for i in range(COLL_N)]
    nd, nh, nm = dw(DO_BOUND_AT), dw(HIT_BOUND_AT), dw(DMG_BOUND_AT)
    do = [dw(DO_TABLE + 4 * i) for i in range(nd)]
    hit = [dw(HIT_TABLE + 4 * i) for i in range(nh)]
    dmg = [dw(DMG_TABLE + 4 * i) for i in range(nm)]
    return coll, do, hit, dmg


def func_starts(insns, extra):
    starts = set(extra)
    for a, t in insns:
        if t.startswith("call   0x") or t.startswith("jmp    0x"):
            try:
                starts.add(int(t.split()[1], 16))
            except ValueError:
                pass
    good = set()
    prev = ""
    for a, t in insns:
        if a in starts and (prev.startswith("int3") or prev.startswith("ret") or prev.startswith("nop")
                            or prev.startswith("lea    ecx,[ecx+0x0]") or prev.startswith("jmp")):
            good.add(a)
        prev = t
    return sorted(good | set(extra))


def enclosing(starts, a):
    i = bisect.bisect_right(starts, a) - 1
    return starts[i] if i >= 0 else 0


def sec_tables(dw):
    coll, do, hit, dmg = tables(dw)
    for i, (f, m) in enumerate(coll):
        print("COLL %d filter=0x%08X mask=0x%04X" % (i, f, m))
    for name, tab in (("DO", do), ("HIT", hit), ("DMG", dmg)):
        for i, v in enumerate(tab):
            if v:
                print("%s %2d 0x%08X" % (name, i, v))
    shared = {}
    for i, v in enumerate(do):
        if v:
            shared.setdefault(v, []).append(i)
    print("DO_SHARED " + (" ".join("0x%08X=%s" % (v, ",".join(map(str, ids)))
                                   for v, ids in shared.items() if len(ids) > 1) or "-"))
    sdo = {dw(SKILL_DO_TABLE + 4 * i): i for i in range(SKILL_DO_BOUND) if dw(SKILL_DO_TABLE + 4 * i)}
    for a in (0x0056F070, 0x0056F460, 0x0056F550):
        print("SKILLDO 0x%08X is g_SkillDoFuncs[%s]" % (a, sdo.get(a, "-")))
    for n in (30,):
        print("SKILLDO g_SkillDoFuncs[%d] = 0x%08X" % (n, dw(SKILL_DO_TABLE + 4 * n)))
    print("SCAN tables do_bound=%d do_nonnull=%d hit_bound=%d hit_nonnull=%d dmg_bound=%d dmg_nonnull=%d "
          "coll_with_filter=%d" % (len(do), sum(1 for v in do if v), len(hit), sum(1 for v in hit if v),
                                   len(dmg), sum(1 for v in dmg if v), sum(1 for f, m in coll if f)))


def sec_calls(insns, starts):
    total = 0
    for tgt, name in TARGETS.items():
        sites = [a for a, t in insns if t in ("call   0x%x" % tgt, "jmp    0x%x" % tgt)]
        total += len(sites)
        fns = sorted(set(enclosing(starts, a) for a in sites))
        print("CALLS %s 0x%08X n=%d fns=%d: %s" % (name, tgt, len(sites), len(fns), " ".join(
            "0x%08X(in 0x%08X)" % (a, enclosing(starts, a)) for a in sites)))
        if tgt == 0x0059FA30:
            bands = {}
            for f in fns:
                key = ("0x0056B000-0x0056FFFF skills core" if 0x0056B000 <= f < 0x00570000 else
                       "0x00580000-0x0059EFFF player/monster/quest/object" if 0x00580000 <= f < 0x0059F000 else
                       "0x0059F000-0x005B0FFF missile functions" if 0x0059F000 <= f < 0x005B1000 else
                       "0x005B1000-0x005E0000 skill functions" if 0x005B1000 <= f < 0x005E0000 else "other")
                bands[key] = bands.get(key, 0) + 1
            print("CALLS MissileCreate callers by band: " + "; ".join("%s=%d" % kv for kv in sorted(bands.items())))
    print("SCAN calls targets=%d sites=%d" % (len(TARGETS), total))


def sec_tabreads(insns):
    names = {DO_TABLE: "do", HIT_TABLE: "hit", DMG_TABLE: "dmg", DO_BOUND_AT: "do_bound", HIT_BOUND_AT: "hit_bound",
             DMG_BOUND_AT: "dmg_bound", COLL_TABLE: "coll", COLL_TABLE + 4: "coll_mask"}
    n = 0
    for i, (a, t) in enumerate(insns):
        for base, nm in names.items():
            if ("0x%x]" % base) in t or ("0x%x," % base) in t or t.endswith("0x%x" % base):
                n += 1
                print("TABREAD %s 0x%08X %s" % (nm, a, t))
                for b, u in insns[max(0, i - 4):i]:
                    print("    0x%08X %s" % (b, u))
    print("SCAN tabreads sites=%d" % n)


def nth_push_back(insns, i, k):
    seen = 0
    j = i - 1
    while j >= 0 and i - j < 40:
        t = insns[j][1]
        if t.startswith("push"):
            seen += 1
            if seen == k:
                return insns[j]
        elif t.startswith("call") or t.startswith("pop") or "esp" in t.split(",")[0]:
            return None
        j -= 1
    return None


def sec_ammo(insns, starts):
    n = 0
    for i, (a, t) in enumerate(insns):
        if t in ("call   0x56ecb0", "call   0x56ee90"):
            p = nth_push_back(insns, i, 8)
            n += 1
            print("AMMO 0x%08X %s in 0x%08X useAmmo=%s" % (a, "lob" if t.endswith("ee90") else "line",
                                                         enclosing(starts, a), p[1].split()[1] if p else "?"))
    print("SCAN ammo sites=%d" % n)


def sec_collmask(insns, starts):
    n = imm40 = imm = 0
    for i, (a, t) in enumerate(insns):
        if t == "call   0x64d9b0":
            p = nth_push_back(insns, i, 5)
            n += 1
            v = p[1].split()[1] if p else "?"
            tag = ""
            if v.startswith("0x") or v.isdigit():
                imm += 1
                if int(v, 0) & 0x40:
                    imm40 += 1
                    tag = " bit40"
            print("COLLMASK 0x%08X in 0x%08X mask=%s%s" % (a, enclosing(starts, a), v, tag))
    print("SCAN collmask sites=%d immediate=%d immediate_with_0x40=%d" % (n, imm, imm40))


def sec_links(insns):
    for off, nm in ((0x16, "ExplosionMissile"), (0x18, "SubMissile1"), (0x1A, "SubMissile2"),
                    (0x24, "HitSubMissile1")):
        pat = re.compile(r"WORD PTR \[e[a-z]{2}\+0x%x\]" % off)
        srv, oth = [], []
        for i, (a, t) in enumerate(insns):
            if pat.search(t) and any("0x1a4" in u for b, u in insns[max(0, i - 25):i]):
                (srv if SRV_LO <= a < SRV_HI else oth).append(a)
        print("LINKS %s +0x%02X server=%d other=%d: %s | %s" % (nm, off, len(srv), len(oth),
              " ".join("0x%08X" % a for a in srv), " ".join("0x%08X" % a for a in oth)))
    print("SCAN links fields=4")


def sec_sites(insns):
    n = 0
    for label, lo, hi in SITES:
        print("SITE %s" % label)
        for a, t in insns:
            if lo <= a <= hi and not t.startswith("int3"):
                print("  0x%08X %s" % (a, t))
                n += 1
    print("SCAN sites windows=%d instructions=%d" % (len(SITES), n))


def sec_rows(dw, xdir):
    import csv
    coll, do, hit, dmg = tables(dw)
    d = open(os.path.join(xdir, "missiles.bin"), "rb").read()
    count = struct.unpack_from("<I", d, 0)[0]
    used = {"do": {}, "hit": {}, "dmg": {}}
    bad = 0
    skipped = []
    ctypes = {}
    for r in range(count):
        o = 4 + 420 * r
        for name, off, tab in (("do", 0x0C, do), ("hit", 0x0E, hit), ("dmg", 0x10, dmg)):
            u = struct.unpack_from("<H", d, o + off)[0]
            s = struct.unpack_from("<h", d, o + off)[0]
            if u == 0:
                continue
            if s <= 0:
                skipped.append((r, name, u, s))
                continue
            used[name][s] = used[name].get(s, 0) + 1
            if not (s < len(tab) and tab[s]):
                bad += 1
                print("ROWBAD missile %d %s=%d" % (r, name, s))
        ct = d[o + 0x183]
        ctypes[ct] = ctypes.get(ct, 0) + 1
    for r, name, u, s in skipped:
        print("ROWSKIP missile %d %s u16=%d s16=%d (the `test ax,ax; jle` of every call site skips it)" % (r, name, u, s))
    for name, tab in (("do", do), ("hit", hit), ("dmg", dmg)):
        print("ROWS %s numbers_used=%d rows=%d table_nonnull_unused=%s" % (
            name, len(used[name]), sum(used[name].values()),
            ",".join(str(i) for i, v in enumerate(tab) if v and i not in used[name]) or "-"))
    print("ROWS collidetype " + " ".join("%d:%d(filter=%s)" % (k, v, "y" if k < COLL_N and coll[k][0] else "n")
                                          for k, v in sorted(ctypes.items())))
    rows = list(csv.reader(open(os.path.join(xdir, "skills.txt"), encoding="latin-1"), delimiter="\t"))
    h = rows[0]
    recs = [dict(zip(h, x)) for x in rows[1:] if x and x[0] != "Expansion"]
    nodo = [i for i, x in enumerate(recs) if x.get("srvmissile", "") and x.get("srvdofunc", "") in ("", "0")]
    lob = [i for i in nodo if recs[i].get("lob", "") not in ("", "0")]
    dq = [i for i in nodo if recs[i].get("decquant", "") not in ("", "0")]
    other = [i for i, x in enumerate(recs) if not x.get("srvmissile", "") and x.get("srvdofunc", "") in ("", "0")
             and any(x.get(c, "") for c in ("srvmissilea", "srvmissileb", "srvmissilec"))]
    print("ROWS skills srvmissile_without_srvdofunc=%d lob=%d decquant=%d; srvmissilea..c only, no srvdofunc: %d (%s)" % (
        len(nodo), len(lob), len(dq), len(other), ",".join(map(str, other)) or "-"))
    for i in (36, 251, 25):
        x = recs[i]
        print("ROWS skill %d srvdofunc=%s srvstfunc=%s lob=%s decquant=%s in_list=%s" % (
            i, x.get("srvdofunc") or "-", x.get("srvstfunc") or "-", x.get("lob") or "-", x.get("decquant") or "-",
            "y" if i in nodo else "n"))
    print("SCAN rows missiles=%d out_of_table=%d skipped_nonpositive=%d" % (count, bad, len(skipped)))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    which = sys.argv[2] if len(sys.argv) > 2 else "all"
    dw = pe_reader(path)
    if which == "rows":
        sec_rows(dw, sys.argv[3])
        return
    if which in ("tables", "all"):
        sec_tables(dw)
    if which == "tables":
        return
    insns = disasm(path)
    coll, do, hit, dmg = tables(dw)
    extra = [v for v in do + hit + dmg + [f for f, m in coll] if v] + list(TARGETS) + KNOWN_STARTS
    extra += [v for v in (dw(SKILL_DO_TABLE + 4 * i) for i in range(SKILL_DO_BOUND)) if v]
    extra += [v for v in (dw(SKILL_ST_TABLE + 4 * i) for i in range(SKILL_ST_BOUND)) if v]
    starts = func_starts(insns, extra)
    if which in ("calls", "all"):
        sec_calls(insns, starts)
    if which in ("tabreads", "all"):
        sec_tabreads(insns)
    if which in ("ammo", "all"):
        sec_ammo(insns, starts)
    if which in ("collmask", "all"):
        sec_collmask(insns, starts)
    if which in ("links", "all"):
        sec_links(insns)
    if which in ("sites", "all"):
        sec_sites(insns)


if __name__ == "__main__":
    main()
