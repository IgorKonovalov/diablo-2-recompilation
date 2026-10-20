#!/usr/bin/env python3
"""Quick code re-reads behind the plan 0045 Phase 1b community cross-check (skills/0001-0003 *Leads used*).

Usage:
  python3 -I tools/skills_crosscheck_reread.py <game.exe>
  python3 -I tools/skills_crosscheck_reread.py rows <excel dir>   # the stock-row values the verdicts compare with

Phase 1b reads no code of its own; it re-reads, in objdump, the instruction windows behind the claims a fetched lead
contradicted or showed to be incomplete, so the verdict rests on a kept output (reverser review-fixes 6). Sections:

  R1  missile creation velocity  ((VelLev * lvl) / 8 + Vel) << 8           0x0059FB1B..0x0059FB3E
  R2  missile creation range     LevRange * lvl + Range                    0x0059FC93..0x0059FCAC
  R3  path velocity step         accel added on every fifth step           0x006502D0..0x0065034D
  R4  summon level               min(max(L * 3 / 4 + skillLvl, 1), L)      0x005C49E0..0x005C4A40
  R5  ItemTarget 2 helper        two inline LCG steps per try, <= 10 tries 0x005FD8D5..0x005FD9B7
  R6  every direct `call 0x5d5220` (COMBAT_PrgFinisher) in 0x00500000..0x00660000
  R7  the function holding each R6 site (first instruction after int3 padding, R6 sites inside 0x005D5300..0x005D7A00)
      and the g_SkillStartFuncs (0x00732140, bound 0x5B) / g_SkillDoFuncs (0x007322B0, bound 0xBF) slot that points at it

Prints addresses, instructions and counts only (no game data). Runs `objdump -d -M intel`.

`rows` reads skills.txt, missiles.txt and pettype.txt (tab-separated, latin-1) and prints, for the rows the verdicts
compare: the non-blank `delay`, `ItemTarget` and `prgstack` rows of Skills, the `mana`/`lvlmana`/`minmana`/`manashift`
of the rows named, the per-level cost of Teleport and Charged Bolt from skills/0001 section 7's formula, the
`pettype`/`petmax` of the summoning rows, and per Missiles column (`VelLev`, `Accel`, `LevRange`, `Pierce`,
`CollideKill`) the count of non-blank rows and the rows the verdicts name. Row names and numbers only.
"""
import re
import struct
import subprocess
import sys

WINDOWS = [
    ("R1 velocity", 0x0059FB1B, 0x0059FB3E),
    ("R2 range", 0x0059FC93, 0x0059FCAC),
    ("R3 accel", 0x006502D0, 0x0065034D),
    ("R4 summon level", 0x005C49E0, 0x005C4A40),
    ("R5 ItemTarget 2 helper", 0x005FD8D5, 0x005FD9B7),
]
FINISHER = 0x005D5220
START_TAB, START_N = 0x00732140, 0x5B
DO_TAB, DO_N = 0x007322B0, 0xBF


def objdump(exe, lo, hi):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x%x" % lo, "--stop-address=0x%x" % hi, exe],
                         capture_output=True, text=True, check=True).stdout
    return [l for l in out.splitlines() if re.match(r"\s+[0-9a-f]+:\t", l)]


def sections(d):
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    n = struct.unpack_from("<H", d, pe + 6)[0]
    opt = struct.unpack_from("<H", d, pe + 20)[0]
    out = []
    for i in range(n):
        o = pe + 24 + opt + 40 * i
        out.append((struct.unpack_from("<I", d, o + 12)[0], struct.unpack_from("<I", d, o + 8)[0],
                    struct.unpack_from("<I", d, o + 20)[0]))
    return out


def main():
    exe = sys.argv[1]
    d = open(exe, "rb").read()
    secs = sections(d)

    def off2va(off):
        for va, vs, ra in secs:
            if ra <= off < ra + vs:
                return 0x400000 + va + off - ra
        return None

    for name, lo, hi in WINDOWS:
        print("## %s 0x%08X..0x%08X" % (name, lo, hi))
        for l in objdump(exe, lo, hi):
            print(l)
    print("## R6 direct calls to 0x%08X in 0x00500000..0x00660000" % FINISHER)
    pat = "call   0x%x" % FINISHER
    sites = [int(l.split(":")[0], 16) for l in objdump(exe, 0x00500000, 0x00660000) if pat in l]
    for s in sites:
        print("SITE 0x%08X" % s)
    print("SCAN R6 sites=%d" % len(sites))
    print("## R7 enclosing functions of the R6 sites in 0x005D5300..0x005D7A00")
    start, cc = None, False
    found = []
    for l in objdump(exe, 0x005D5300, 0x005D7A00):
        m = re.match(r"\s+([0-9a-f]+):\t((?:[0-9a-f]{2} )+)\s*\t?(.*)", l)
        if not m:
            continue
        a, ins = int(m.group(1), 16), m.group(3)
        if ins.startswith("int3"):
            cc = True
            continue
        if cc:
            start, cc = a, False
        if pat in ins:
            found.append((a, start))
    for a, f in found:
        refs, i = [], d.find(struct.pack("<I", f))
        while i != -1:
            refs.append(off2va(i))
            i = d.find(struct.pack("<I", f), i + 1)
        lab = []
        for r in refs:
            if r is not None and START_TAB <= r < START_TAB + 4 * START_N:
                lab.append("g_SkillStartFuncs[%d]" % ((r - START_TAB) // 4))
            elif r is not None and DO_TAB <= r < DO_TAB + 4 * DO_N:
                lab.append("g_SkillDoFuncs[%d]" % ((r - DO_TAB) // 4))
            else:
                lab.append("0x%08X" % r if r is not None else "file-only")
        print("FUNC site 0x%08X in 0x%08X slots %s" % (a, f, ", ".join(lab) or "none"))
    print("SCAN R7 sites=%d" % len(found))


def table(path):
    lines = open(path, encoding="latin-1").read().split("\n")
    head = lines[0].rstrip("\r").split("\t")
    rows = []
    for l in lines[1:]:
        if not l.strip():
            continue
        c = l.rstrip("\r").split("\t")
        c += [""] * (len(head) - len(c))
        rows.append(dict(zip(head, c)))
    return rows


def rows_main(xd):
    import os
    sk = table(os.path.join(xd, "skills.txt"))
    mi = table(os.path.join(xd, "missiles.txt"))
    nb = lambda v: v.strip() not in ("", "0")
    for col in ("delay", "ItemTarget", "prgstack"):
        hit = [(i, r["skill"], r[col]) for i, r in enumerate(sk) if nb(r[col])]
        print("SKILLS %s n=%d %s" % (col, len(hit), "; ".join("%d %s=%s" % h for h in hit)))
    for name in ("Teleport", "Charged Bolt", "Raise Skeleton", "Fire Bolt"):
        r = next(r for r in sk if r["skill"] == name)
        mana, lv, sh = int(r["mana"] or 0), int(r["lvlmana"] or 0), int(r["manashift"] or 0)
        cost = [((lv * max(l - 1, 0) + mana) << sh) / 256 for l in range(1, 21)]
        print("MANA %s mana=%s lvlmana=%s minmana=%s manashift=%s cost1..20=%s" % (
            name, r["mana"], r["lvlmana"], r["minmana"], r["manashift"], ",".join("%g" % c for c in cost)))
    for i, r in enumerate(sk):
        if nb(r["pettype"]) or nb(r["petmax"]):
            print("PET %d %s pettype=%s petmax=%s" % (i, r["skill"], r["pettype"], r["petmax"]))
    named = {"VelLev": None, "Accel": ("nova", "frostnova", "howl"), "LevRange": ("blaze", "firewallmaker"),
             "Pierce": ("arrow", "multipleshotarrow", "guidedarrow", "lightningfury", "bonespear", "firebolt"),
             "CollideKill": ("arrow", "guidedarrow", "bonespear", "firebolt", "lightningbolt")}
    for col, names in named.items():
        hit = [(i, r["Missile"], r[col]) for i, r in enumerate(mi) if nb(r[col])]
        show = hit if names is None else [(i, r["Missile"], r[col]) for i, r in enumerate(mi) if r["Missile"] in names]
        print("MISSILES %s n=%d %s" % (col, len(hit), "; ".join("%d %s=%s" % h for h in show)))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "rows":
        rows_main(sys.argv[2])
    else:
        main()
