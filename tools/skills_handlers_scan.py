#!/usr/bin/env python3
"""Static scans behind docs/findings/skills/0003-handlers.md (plan 0045 Phase 1, batch P1.3).

Usage:
  python3 -I tools/skills_handlers_scan.py <game.exe>                  # tables, draws, refs, flagreads, sites
  python3 -I tools/skills_handlers_scan.py <game.exe> tables           # stat-event table, the do/start entries read
  python3 -I tools/skills_handlers_scan.py <game.exe> draws            # per function: inline LCG steps and RNG calls
  python3 -I tools/skills_handlers_scan.py <game.exe> refs             # callers and absolute pointers of chosen addresses
  python3 -I tools/skills_handlers_scan.py <game.exe> flagreads        # Skills flag/word reads after a 0x23C record multiply
  python3 -I tools/skills_handlers_scan.py <game.exe> conv             # the packet offset of skills/0001's EType stores
  python3 -I tools/skills_handlers_scan.py <game.exe> sites            # instruction windows the finding cites
  python3 -I tools/skills_handlers_scan.py <game.exe> rows <excel dir> # (not in `all`) event and dispatch columns of the
                                                                       # rows the finding names: row ids and numbers only

Reads the PE image for the tables (code addresses only) and runs `objdump -d -M intel --no-show-raw-insn` for the code
scans. Prints addresses and counts, no game data, except that `rows` prints the few row ids, stat ids and function
numbers the finding cites. One `SCAN <section> ...` summary line per section.

  draws    a function body runs from its entry to the first `int3` or the next known entry (a direct call target or a
           table entry), whichever comes first. `lcg` counts instructions naming the LCG multiplier 0x6AC690C5 (one per
           inline step); the other columns count `call` instructions to the named functions.
  refs     `call`/`jmp 0x<target>` sites, other instructions naming the address as an immediate, and every aligned
           or unaligned 4-byte occurrence of the address in the file (with its virtual address when it lies in a section).
  flagreads for each Skills flag bit, the `test BYTE PTR [r+off]` instructions with the bit as an immediate or as a
           register loaded from the bit-mask table 0x006CE268 + 4 * bit in the 8 instructions before, kept only when one
           of the 12 instructions before names the Skills record size 0x23C or the table field `+0xb98`; split into the
           server range 0x00530000-0x00660000 and the rest. weapsel: every operand `[r+0x168]` of any width.
"""
import os
import re
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skills_missiles_scan import pe_reader  # noqa: E402

EV_TABLE, EV_BOUND = 0x007325B0, 0x32          # g_StatEventFuncs; sub_0056E740_AddStatEvent tests n < 0x32
SKILL_ST_TABLE, SKILL_ST_BOUND = 0x00732140, 0x5B
SKILL_DO_TABLE, SKILL_DO_BOUND = 0x007322B0, 0xBF
MDO_TABLE, MDO_BOUND_AT = 0x0073C768, 0x0073C71C
MHIT_TABLE, MHIT_BOUND_AT = 0x0073C840, 0x0073C83C
MDMG_TABLE, MDMG_BOUND_AT = 0x0073C960, 0x0073C95C
UMOD_EVENTS, UMOD_STRIDE, UMOD_SLOT5 = 0x0073C0B8, 0x18, 0x14
SRV_LO, SRV_HI = 0x00530000, 0x00660000
LCG = "0x6ac690c5"

PRG = [36, 37, 38, 39, 40, 41, 143]
TIERA_ST = [1, 2, 4, 5, 15, 23, 26, 32, 36, 55, 65]
TIERA_DO = [1, 2, 3, 5, 7, 8, 18, 20, 22, 27, 28, 30, 31, 34, 35, 48, 65, 66, 83, 109, 114, 117, 146]
TIERA_MDO = [1, 2, 3, 5, 14, 23, 28, 34, 35]
TIERA_MHIT = [2, 3, 14, 17, 22, 23, 27, 36, 44, 58]
TIERA_MDMG = [3]

CALLEES = {
    0x0045C370: "Step", 0x0045C390: "Range", 0x0045C3E0: "RangeB", 0x00472210: "RangePow2",
    0x00650E40: "SeedInit", 0x00650E30: "SeedInitOne", 0x00650E50: "GetLow",
    0x0059FA30: "MissileCreate", 0x0056ECB0: "SkillMissile", 0x0056EE90: "SkillMissileLob",
    0x0056EDE0: "MissileAt", 0x0056D400: "NovaAt", 0x0056E0C0: "RollElem", 0x0056E170: "RollPhys",
    0x0057EC10: "MeleeHitTest", 0x0057DBF0: "ResolveQueue", 0x0057D4F0: "DeliverQueued",
    0x0057C6C0: "ApplyDamage", 0x0056B9C0: "AreaHit", 0x0056B7E0: "ForUnitsInRange", 0x0056E780: "ForUnitsNearTarget",
    0x0056E970: "ApplyTimed", 0x005FDCA0: "CastAtUnit", 0x005FDD60: "CastAtXY", 0x005A89A0: "BuildDamage",
    0x0056D940: "SpawnOwned", 0x005ADF10: "HitUnit",
}

FUNCS = [
    # progressive entries, the finisher and their helpers
    (0x005D5220, "COMBAT_PrgFinisher"), (0x005D4DB0, "do36 PrgNovaAtTarget"), (0x005D4E70, "do37 PrgRingLocalSeed"),
    (0x005D3E80, "do38 PrgAreaHit"), (0x005D3F90, "do39 PrgScatterLocalSeed"), (0x005D5010, "do40 PrgMissileAt"),
    (0x005D5080, "do41 PrgScatterLocalSeed2"), (0x005D4F40, "do143 PrgRingLocalSeed2"),
    (0x005D4150, "PrgRing64 (do37)"), (0x005D4870, "PrgRing64b (do143)"), (0x00571AA0, "UnitMsgA3"),
    (0x005D3CF0, "SkillSrvMissileByCharge"), (0x005D3DA0, "SkillPrgCalcByCharge"), (0x0056E170, "SkillRollPhys"),
    # missile-creation callbacks that re-seed the new missile
    (0x005D40F0, "cb ReseedFromArg"), (0x005D4680, "cb ReseedZigzag"), (0x005C9290, "cb ReseedPathXPlusArg"),
    (0x005CD110, "cb ReseedPathXPlusArgRoll"), (0x005AC040, "cb ReseedPathX"),
    # stat-event handlers (g_StatEventFuncs 1..31) and the item-cast helpers
    (0x005CAB40, "ev1"), (0x005CAC50, "ev2"), (0x005CAD40, "ev3"), (0x005C5F50, "ev4"), (0x005C61E0, "ev5"),
    (0x005BF670, "ev6"), (0x005BF960, "ev7"), (0x005BFA10, "ev8"), (0x005BFAA0, "ev9"), (0x005BF720, "ev10"),
    (0x005BF7D0, "ev11"), (0x005BF880, "ev12"), (0x005BFBB0, "ev13"), (0x005BFC60, "ev14"), (0x005BFE60, "ev15"),
    (0x005BFFC0, "ev16"), (0x005C0130, "ev17"), (0x005C0260, "ev18"), (0x005C0310, "ev19"), (0x005C0470, "ev20"),
    (0x005C05A0, "ev21"), (0x005C6370, "ev22"), (0x005C6530, "ev23"), (0x005CA6C0, "ev24"), (0x005C87A0, "ev25"),
    (0x005C6690, "ev26"), (0x005C6760, "ev27"), (0x005C01D0, "ev28"), (0x005C0770, "ev29"), (0x005C0670, "ev30"),
    (0x005C09E0, "ev31"), (0x005FDCA0, "ItemCastAtUnit"), (0x005FDD60, "ItemCastAtXY"), (0x005FDA80, "ITEMSKILL_Cast"),
    # SrvStart / PayCost callers inside skill functions
    (0x005CAF30, "do83"), (0x005CDF10, "do109"), (0x005CDDD0, "do109 hit"), (0x005D69D0, "st26"), (0x005D68A0, "do48"),
    # tier-A start and do functions
    (0x0056CA40, "st1"), (0x0056CAF0, "st2"), (0x005DA8B0, "st4"), (0x005DA8F0, "st5"), (0x005C3070, "st15"),
    (0x005D32F0, "st23"), (0x005D0180, "st36"), (0x0056CAB0, "st65"), (0x005CD910, "st55"),
    (0x0056F070, "do1"), (0x0056F1F0, "do2"), (0x0056F460, "do3"), (0x0056F550, "do5"), (0x005DB2D0, "do7"),
    (0x005DB410, "do8"), (0x005C9480, "do18"), (0x005C9800, "do20"), (0x005C9B50, "do22"), (0x005CA360, "do27"),
    (0x005CA3E0, "do28"), (0x005C37C0, "do30"), (0x005C35C0, "do30 apply"), (0x005C4B00, "do31"),
    (0x005D3490, "do34"), (0x005D35D0, "do35"), (0x005CF010, "do65"), (0x005CF3A0, "do66"), (0x005C6910, "do114"),
    (0x005C7160, "do117"), (0x005C8520, "do146"), (0x005C4470, "SummonInitStats"), (0x005C49E0, "SummonSetLevel"),
    # tier-A missile functions and their helpers
    (0x005AE1F0, "mdo1"), (0x005AE400, "mdo2"), (0x005AE480, "mdo3"), (0x005AE520, "mdo5"), (0x005AEF70, "mdo14"),
    (0x005AF790, "mdo23"), (0x005AFB80, "mdo28"), (0x005B04A0, "mdo34"), (0x005B0640, "mdo35"),
    (0x005A9D80, "mhit2"), (0x005A9F90, "mhit3"), (0x005AABB0, "mhit14"), (0x005AAFB0, "mhit17"),
    (0x005ADD20, "mhit22"), (0x005ACFC0, "mhit23"), (0x005ABA00, "mhit27"), (0x005ABF70, "mhit36"),
    (0x005A9E10, "mhit44"), (0x005ACDF0, "mhit58"), (0x005AD220, "mdmg3"),
    (0x005A9370, "SubRing16"), (0x005A9720, "SubAtSelf"), (0x005A9820, "SubAtRandomNear"), (0x005AAA90, "SubRing18"),
    (0x0056D400, "NovaAt64"), (0x0056BAD0, "AreaHitAt"),
    # helpers and other re-seed sites
    (0x00645390, "ReseedFromEntry"), (0x005A3610, "MonLocalSeedConst"), (0x005A6B70, "MonLocalSeedConst2"),
    (0x005C276A, "ItemSeedSaveRestore"), (0x0064FC60, "PathDirection"), (0x006505C0, "PathFlag8"),
    (0x00620C10, "UnitSetTargetUnit"), (0x005A43B0, "MissileUModEvent5"), (0x00645F00, "UnitRangedMissile"),
    (0x00575D90, "PetAdd"), (0x00575720, "PetGroupClear"), (0x00575850, "PetLimit"),
    (0x0057D810, "PreventHealHook"), (0x0056D940, "SpawnOwnedMonster"),
]

REFS = [0x005AD9D0, 0x00645390, 0x005ACFC0, 0x005ADD20, 0x005C8520, 0x005CD910, 0x005AC040, 0x005C9290,
        0x005D40F0, 0x005D4680, 0x005CD110, 0x00571AA0, 0x005FDCA0, 0x005FDD60, 0x0056B9C0, 0x00575D90]

FLAGPATS = [  # (label, record offset, bit-mask table entry): the compiler loads the bit from 0x006CE268 + 4 * bit
    ("TgtPlaceCheck +0x08 bit 0", 0x8, 0x006CE268),
    ("repeat +0x05 bit 3", 0x5, 0x006CE274),
    ("leftskill +0x07 bit 6", 0x7, 0x006CE280),
]
WEAPSEL = re.compile(r"PTR \[e[a-z]{2}\+0x168\]")

SITES = [
    ("finisher: srvprgfunc 1..n-1 under prgstack, then n, then 0x00571AA0", 0x005D53E0, 0x005D5490),
    ("do 37: inline step on the unit seed at entry, its low word to 0x005D4150", 0x005D4E70, 0x005D4F2E),
    ("do 39: inline step, local seed, r*r pairs of RNG_Range", 0x005D3F90, 0x005D40E0),
    ("do 41: inline step, local seed, two inline local steps per missile", 0x005D5080, 0x005D5210),
    ("do 143: inline step at entry", 0x005D4F40, 0x005D5000),
    ("0x005D4150: local seed from EDX, one inline step per missile, callback 0x005D40F0", 0x005D41C0, 0x005D4250),
    ("ev7 knockback: inline step on the handler unit's seed, low & 0x7F", 0x005BF9C0, 0x005BF9F0),
    ("ev20 skill on attack/hit/kill: inline step, low % 100 < chance", 0x005C04C0, 0x005C0510),
    ("ev30 skill on death/level-up: inline step", 0x005C06B0, 0x005C0700),
    ("ev28 heal after kill: no draw", 0x005C01D0, 0x005C0260),
    ("do 146 (event-5 periodic): re-seed of the unit seed from the entry's +0x18", 0x005C8650, 0x005C86C0),
    ("hit 58: re-seed of the missile seed from SubX", 0x005ACE30, 0x005ACE80),
    ("callback 0x005AC040: re-seed from path +0x10", 0x005AC040, 0x005AC093),
    ("callback 0x005C9290: re-seed from path +0x10 plus EDX", 0x005C9290, 0x005C92F0),
    ("0x005A9820: re-seed from SubX + elapsed, 2 RangeB", 0x005A9840, 0x005A98E0),
    ("mdo 28: re-seed from MissileData+0x28, 2 Range, low back to +0x28", 0x005AFC60, 0x005AFCD0),
    ("mdo 35: re-seed from +0x28, one inline step, low back", 0x005B0680, 0x005B0700),
    ("mdmg 3: inline step on the missile seed, low & 0x7F < dParam1", 0x005AD220, 0x005AD290),
    ("hit-table read in HitUnit: index is the s16 cell itself", 0x005AE106, 0x005AE126),
    ("frame pass order: missiles, players, monsters, objects, the fifth list", 0x005414D0, 0x0054158F),
    ("COMBAT_ToHitRoll success: the prevent-heal hook after the draw's compare", 0x0057DB77, 0x0057DB87),
    ("PreventHealHook: stat 117, classes 704-709 excluded, state 52 for 120000 frames, stat 31", 0x0057D810, 0x0057D89A),
    ("StartUsedSkill: the ally test called only without TargetAlly, with the same id", 0x0056FB83, 0x0056FBCB),
    ("SkillAllyTest: ECX = the id argument, TargetAlly required", 0x00554D47, 0x00554D6B),
    ("TgtPlaceCheck reader in the monster AI target test", 0x005FD48A, 0x005FD4BC),
]


def disasm(path):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", path],
                         capture_output=True, text=True, check=True).stdout
    pat = re.compile(r"^\s*([0-9a-f]+):\s+(.*)$")
    insns = []
    for line in out.splitlines():
        m = pat.match(line)
        if m:
            insns.append((int(m.group(1), 16), m.group(2).strip()))
    return insns


def tab(dw, base, n):
    return [dw(base + 4 * i) for i in range(n)]


def known_entries(dw, insns):
    ents = set(a for a, _ in FUNCS)
    for base, n in ((EV_TABLE, EV_BOUND), (SKILL_ST_TABLE, SKILL_ST_BOUND), (SKILL_DO_TABLE, SKILL_DO_BOUND),
                    (MDO_TABLE, dw(MDO_BOUND_AT)), (MHIT_TABLE, dw(MHIT_BOUND_AT)), (MDMG_TABLE, dw(MDMG_BOUND_AT))):
        ents.update(v for v in tab(dw, base, n) if v)
    for _, t in insns:
        if t.startswith("call   0x"):
            try:
                ents.add(int(t.split()[1], 16))
            except ValueError:
                pass
    return sorted(ents)


def sec_tables(dw):
    ev = tab(dw, EV_TABLE, EV_BOUND)
    for i, v in enumerate(ev):
        if v:
            print("EV %2d 0x%08X" % (i, v))
    st = tab(dw, SKILL_ST_TABLE, SKILL_ST_BOUND)
    do = tab(dw, SKILL_DO_TABLE, SKILL_DO_BOUND)
    for n in TIERA_ST:
        print("ST %3d 0x%08X" % (n, st[n]))
    for n in sorted(set(TIERA_DO + PRG)):
        print("DO %3d 0x%08X%s" % (n, do[n], " (progressive)" if n in PRG else ""))
    md, mh, mm = tab(dw, MDO_TABLE, dw(MDO_BOUND_AT)), tab(dw, MHIT_TABLE, dw(MHIT_BOUND_AT)), tab(dw, MDMG_TABLE, dw(MDMG_BOUND_AT))
    for n in TIERA_MDO:
        print("MDO %2d 0x%08X" % (n, md[n]))
    for n in TIERA_MHIT:
        print("MHIT %2d 0x%08X" % (n, mh[n]))
    for n in TIERA_MDMG:
        print("MDMG %2d 0x%08X" % (n, mm[n]))
    inv = {}
    for name, t in (("DO", do), ("ST", st), ("EV", ev), ("MDO", md), ("MHIT", mh), ("MDMG", mm)):
        for i, v in enumerate(t):
            if v:
                inv.setdefault(v, []).append("%s%d" % (name, i))
    for a in (0x005C8520, 0x005CD910, 0x005D69D0, 0x005D68A0, 0x005ACFC0, 0x005ADD20, 0x005ACDF0, 0x005C37C0):
        print("INV 0x%08X = %s" % (a, ",".join(inv.get(a, ["-"]))))
    u5 = [(i, dw(UMOD_EVENTS + UMOD_STRIDE * i + UMOD_SLOT5)) for i in range(64)]
    u5 = [(i, v) for i, v in u5 if v and 0x00400000 <= v < 0x00700000]
    print("UMOD5 " + (" ".join("%d:0x%08X" % iv for iv in u5) or "-"))
    print("SCAN tables ev_nonnull=%d ev_max=%d prg=%d st=%d do=%d mdo=%d mhit=%d mdmg=%d umod5_nonnull=%d" % (
        sum(1 for v in ev if v), max(i for i, v in enumerate(ev) if v), len(PRG), len(TIERA_ST),
        len(set(TIERA_DO + PRG)), len(TIERA_MDO), len(TIERA_MHIT), len(TIERA_MDMG), len(u5)))


def sec_draws(insns, ents):
    import bisect
    addrs = [a for a, _ in insns]
    total_lcg = 0
    for start, label in FUNCS:
        i = bisect.bisect_left(addrs, start)
        if i >= len(addrs) or addrs[i] != start:
            print("DRAW 0x%08X %-28s not an instruction start" % (start, label))
            continue
        k = bisect.bisect_right(ents, start)
        nxt = ents[k] if k < len(ents) else 1 << 32
        cnt = {}
        lcg = 0
        end = start
        j = i
        while j < len(insns):
            a, t = insns[j]
            if a >= nxt or t.startswith("int3"):
                break
            if LCG in t:
                lcg += 1
            if t.startswith("call   0x"):
                try:
                    c = int(t.split()[1], 16)
                except ValueError:
                    c = None
                if c in CALLEES:
                    cnt[CALLEES[c]] = cnt.get(CALLEES[c], 0) + 1
            end = a
            j += 1
        total_lcg += lcg
        print("DRAW 0x%08X %-28s end=0x%08X lcg=%d %s" % (start, label, end, lcg,
              " ".join("%s=%d" % kv for kv in sorted(cnt.items())) or "-"))
    print("SCAN draws functions=%d lcg_total=%d" % (len(FUNCS), total_lcg))


def sec_refs(insns, path):
    data = open(path, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    secs = []
    for i in range(n):
        o = pe + 24 + opt + 40 * i
        vs, va, rs, ro = struct.unpack_from("<IIII", data, o + 8)
        secs.append((va + 0x400000, rs, ro))

    def va_of(off):
        for va, rs, ro in secs:
            if ro <= off < ro + rs:
                return "0x%08X" % (va + off - ro)
        return "file+0x%X" % off
    for a in REFS:
        h = "0x%x" % a
        calls = [b for b, t in insns if t in ("call   " + h, "jmp    " + h)]
        imms = [b for b, t in insns if (t.endswith("," + h) or t.endswith(" " + h)) and not t.startswith(("call", "j"))]
        pat = struct.pack("<I", a)
        ptrs = []
        o = data.find(pat)
        while o != -1:
            ptrs.append(va_of(o))
            o = data.find(pat, o + 1)
        print("REF 0x%08X calls=%d imm=%d ptrs=%d | %s | %s | %s" % (
            a, len(calls), len(imms), len(ptrs), " ".join("0x%08X" % b for b in calls) or "-",
            " ".join("0x%08X" % b for b in imms) or "-", " ".join(ptrs) or "-"))
    print("SCAN refs targets=%d" % len(REFS))


def sec_flagreads(insns):
    for label, off, mask in FLAGPATS:
        pat = re.compile(r"test\s+BYTE PTR \[e[a-z]{2}\+0x%x\],[abcd]l$" % off)
        imm = re.compile(r"test\s+BYTE PTR \[e[a-z]{2}\+0x%x\],0x%x$" % (off, {0x006CE268: 1, 0x006CE274: 8, 0x006CE280: 0x40}[mask]))
        srv, oth, loose = [], [], []
        for i, (a, t) in enumerate(insns):
            if pat.search(t) and any(("ds:0x%x" % mask) in u for _, u in insns[max(0, i - 8):i]):
                loose.append(a)
            hit = imm.search(t) or (pat.search(t) and any(("ds:0x%x" % mask) in u for _, u in insns[max(0, i - 8):i]))
            ctx = any(("0x23c" in u or "+0xb98]" in u) for _, u in insns[max(0, i - 12):i])
            if hit and ctx:
                (srv if SRV_LO <= a < SRV_HI else oth).append(a)
        print("FLAG %s server=%d other=%d: %s | %s" % (label, len(srv), len(oth),
              " ".join("0x%08X" % a for a in srv) or "-", " ".join("0x%08X" % a for a in oth) or "-"))
        print("FLAG %s mask-table loads without the context test n=%d: %s" % (label, len(loose),
              " ".join("0x%08X" % a for a in loose) or "-"))
    w = [a for a, t in insns if WEAPSEL.search(t)]
    print("FLAG weapsel +0x168 (any width) n=%d: %s" % (len(w), " ".join("0x%08X" % a for a in w)))
    print("SCAN flagreads patterns=%d" % (len(FLAGPATS) + 1))


CONV_STORES = [0x005C3175, 0x005C7747, 0x005CE887, 0x005CEB76, 0x005CFC7C, 0x005D62CC, 0x005D7FA8, 0x005D8BED,
               0x005D98CD, 0x005DA74D, 0x005DA9F9, 0x005DAC35, 0x005DB10F, 0x005DB3B6, 0x005DBD87]


def sec_conv(insns):
    """For each EType byte store of skills/0001 (CONV lines of dispatch-scan.txt): the 0x70-byte packet cleared in the
    same function (`push 0x70` with a `lea r,[ebp-N]` within 3 instructions), and the store's offset in it."""
    import bisect
    addrs = [a for a, _ in insns]
    st = re.compile(r"mov\s+BYTE PTR \[ebp-0x([0-9a-f]+)\],[a-d]l$")
    lea = re.compile(r"lea\s+e[a-z]{2},\[ebp-0x([0-9a-f]+)\]$")
    n65 = 0
    for sa in CONV_STORES:
        i = bisect.bisect_left(addrs, sa)
        m = st.match(insns[i][1])
        off = int(m.group(1), 16)
        bases = set()
        j = i
        while j > 0 and i - j < 600 and not insns[j - 1][1].startswith("int3"):
            j -= 1
            if insns[j][1] == "push   0x70":
                for _, u in insns[max(0, j - 3):j + 4]:
                    mm = lea.match(u)
                    if mm:
                        bases.add(int(mm.group(1), 16))
        rel = sorted(b - off for b in bases if b > off)
        if 0x65 in rel:
            n65 += 1
        print("CONV 0x%08X store [ebp-0x%X] packet bases %s -> offsets %s" % (
            sa, off, ",".join("ebp-0x%X" % b for b in sorted(bases)) or "-", ",".join("+0x%X" % r for r in rel) or "-"))
    print("SCAN conv stores=%d at_plus_0x65=%d" % (len(CONV_STORES), n65))


def sec_sites(insns):
    n = 0
    for label, lo, hi in SITES:
        print("SITE %s" % label)
        for a, t in insns:
            if lo <= a <= hi and not t.startswith("int3"):
                print("  0x%08X %s" % (a, t))
                n += 1
    print("SCAN sites windows=%d instructions=%d" % (len(SITES), n))


def find_ci(xdir, name):
    for f in os.listdir(xdir):
        if f.lower() == name:
            return os.path.join(xdir, f)
    raise FileNotFoundError(name)


def sec_rows(xdir):
    import csv

    def load(name):
        rows = list(csv.reader(open(find_ci(xdir, name), encoding="latin-1"), delimiter="\t"))
        h = rows[0]
        return [dict(zip(h, x)) for x in rows[1:] if x and x[0] != "Expansion"]
    isc = load("itemstatcost.txt")
    funcs = {}
    for x in isc:
        for e, f in (("itemevent1", "itemeventfunc1"), ("itemevent2", "itemeventfunc2")):
            if x.get(e):
                funcs.setdefault(int(x[f]), []).append("stat%s/%s" % (x["ID"], x[e]))
    for k in sorted(funcs):
        print("ROWS itemeventfunc %2d: %s" % (k, " ".join(funcs[k])))
    sk = load("skills.txt")
    af = {}
    for i, x in enumerate(sk):
        for e, f in (("auraevent1", "auraeventfunc1"), ("auraevent2", "auraeventfunc2"), ("auraevent3", "auraeventfunc3")):
            if x.get(e):
                af.setdefault(int(x[f]), []).append("skill%d/%s" % (i, x[e]))
    for k in sorted(af):
        print("ROWS auraeventfunc %2d: %s" % (k, " ".join(af[k])))
    used = set(funcs) | set(af)
    print("ROWS eventfuncs_used=%s unused_in_1_31=%s" % (",".join(map(str, sorted(used))),
          ",".join(str(i) for i in range(1, 32) if i not in used)))
    for col in ("repeat", "startmana", "TgtPlaceCheck", "weapsel", "leftskill"):
        ids = [i for i, x in enumerate(sk) if x.get(col, "") not in ("", "0")]
        print("ROWS skills %s rows=%d%s" % (col, len(ids), (": " + ",".join(map(str, ids))) if len(ids) <= 20 else ""))
    prg = [i for i, x in enumerate(sk) if any(x.get("srvprgfunc%d" % k) for k in (1, 2, 3))]
    for i in prg:
        x = sk[i]
        print("ROWS prg skill%d srvprgfunc=%s/%s/%s prgstack=%s" % (i, x.get("srvprgfunc1") or "-",
              x.get("srvprgfunc2") or "-", x.get("srvprgfunc3") or "-", x.get("prgstack") or "-"))
    print("SCAN rows itemeventfuncs=%d auraeventfuncs=%d prg_rows=%d" % (len(funcs), len(af), len(prg)))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    which = sys.argv[2] if len(sys.argv) > 2 else "all"
    if which == "rows":
        sec_rows(sys.argv[3])
        return
    dw = pe_reader(path)
    if which in ("tables", "all"):
        sec_tables(dw)
    if which == "tables":
        return
    insns = disasm(path)
    if which in ("draws", "all"):
        sec_draws(insns, known_entries(dw, insns))
    if which in ("refs", "all"):
        sec_refs(insns, path)
    if which in ("flagreads", "all"):
        sec_flagreads(insns)
    if which in ("conv", "all"):
        sec_conv(insns)
    if which in ("sites", "all"):
        sec_sites(insns)


if __name__ == "__main__":
    main()
