#!/usr/bin/env python3
"""Static scans behind docs/findings/skills/0001-dispatch.md (plan 0045 Phase 1, batch P1.1).

Usage:
  python3 -I tools/skills_dispatch_scan.py <game.exe>            # all sections
  python3 -I tools/skills_dispatch_scan.py <game.exe> tables     # the function-pointer tables of the dispatch
  python3 -I tools/skills_dispatch_scan.py <game.exe> calls      # direct callers of the dispatch functions
  python3 -I tools/skills_dispatch_scan.py <game.exe> conv       # Skills EType (+0x1DC) reads and the packet byte store after them
  python3 -I tools/skills_dispatch_scan.py <game.exe> c4         # writers of unit +0xC4 bit 6 (0x40)
  python3 -I tools/skills_dispatch_scan.py <game.exe> sites      # instruction windows the finding cites (cost result, finisher peek)
  python3 -I tools/skills_dispatch_scan.py <game.exe> rows <skills.txt>   # (not in `all`) Skills function numbers against the tables

Reads the PE image for the tables (code addresses only) and runs `objdump -d -M intel --no-show-raw-insn` for the
code scans. Prints addresses only, no game data. One `SCAN <section> ...` summary line per section.
  tables  st table 0x00732140 (bound 0x5B at 0x0056F75A), do table 0x007322B0 (bound 0xBF), player mode tables
          0x006E1740 ({start xy, start unit} x 20) and 0x00732C10 (frame x 20), client-packet table 0x006E0D18
          ({handler, flag} by packet id) for ids 0x01..0x11.
  calls   `call 0x<target>` / `jmp 0x<target>` for each target in TARGETS, with the enclosing function (the nearest
          preceding function start, see below).
  conv    every operand `[reg+0x1dc]` in 0x0056B000-0x005E0000 (the server skill code), then the first
          `mov BYTE PTR [ebp-0x..],` within the next 12 instructions; reported with the enclosing function and the
          st/do numbers the tables give it.
  c4      `or DWORD PTR [reg+0xc4],0x40` and `and DWORD PTR [reg+0xc4],0xffffffbf`, whole image and the server skill range.
  rows    every Skills row's srvstfunc, srvdofunc, srvprgfunc1..3 and ItemEffect (> 1) against the table bounds and
          non-null entries; counts of the dispatch flag columns the finding cites. Counts only, no cell values.
Function starts: an address that follows an int3/nop padding run or a `ret` and is the target of a direct call or a
table entry (st, do, packet, mode). Good enough for attribution; the finding cites addresses, not these guesses.
"""
import bisect
import re
import struct
import subprocess
import sys

ST_TABLE, ST_BOUND = 0x00732140, 0x5B
DO_TABLE, DO_BOUND = 0x007322B0, 0xBF
PLR_START, PLR_FRAME, NMODES = 0x006E1740, 0x00732C10, 20
PKT_TABLE = 0x006E0D18
SKILL_LO, SKILL_HI = 0x0056B000, 0x005E0000

TARGETS = {
    0x0056F640: "SKILLS_SrvStart",
    0x0056F7F0: "SKILLS_SrvDo",
    0x0056FAF0: "SKILLS_StartUsedSkill",
    0x0056FC50: "SKILLS_DoUsedSkill",
    0x0056BFE0: "SKILLS_PayCost",
    0x0056C160: "SKILLS_SrvManaCheck",
    0x00647960: "SKILLS_CanUse",
    0x0056EF90: "SKILLS_SetDelayState",
    0x0056CDA0: "SKILLS_QueuePeriodic",
    0x005FDA80: "ITEMSKILL_Cast",
    0x00549AD0: "PLRMSG_SkillAtXY",
    0x00549BA0: "PLRMSG_SkillAtUnit",
    0x005809D0: "sub_005809D0_PlayerModeCmd",
    0x00580A70: "PLAYER_ModeCmdUnit",
    0x005D9C80: "sub_005D9C80_MonSkillAttackDo",
    0x005A4F50: "sub_005A4F50_MonAttackStats",
    0x0056C3F0: "PLAYER_UseAmmo",
    0x005DAA40: "sub_005DAA40_SkillWeaponWear",
    0x0056BEC0: "sub_0056BEC0_UseCharge",
}

SITES = [
    ("cost result after SrvStart's pay call", 0x0056F7A5, 0x0056F7BB),
    ("cost result after SrvDo's pay call", 0x0056FA75, 0x0056FA8B),
    ("finisher: save seed, RNG_Step, restore seed", 0x005D5360, 0x005D5391),
    ("seed copy-out 0x00650E70 and copy-in 0x00650E60", 0x00650E60, 0x00650E7F),
]

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
        secs.append((va + 0x400000, max(vs, rs), ro))

    def dw(a):
        for va, sz, ro in secs:
            if va <= a < va + sz:
                return struct.unpack_from("<I", d, a - va + ro)[0]
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
    st = {i: dw(ST_TABLE + 4 * i) for i in range(ST_BOUND)}
    do = {i: dw(DO_TABLE + 4 * i) for i in range(DO_BOUND)}
    return st, do


def func_starts(insns, extra):
    starts = set(extra)
    prev = ""
    for a, t in insns:
        if t.startswith("call   0x") or t.startswith("jmp    0x"):
            try:
                starts.add(int(t.split()[1], 16))
            except ValueError:
                pass
    good = set()
    for a, t in insns:
        if a in starts and (prev.startswith("int3") or prev.startswith("ret") or prev.startswith("nop")
                            or prev.startswith("lea    ecx,[ecx+0x0]") or prev.startswith("jmp")):
            good.add(a)
        prev = t
    return sorted(good | set(extra))


def enclosing(starts, a):
    i = bisect.bisect_right(starts, a) - 1
    return starts[i] if i >= 0 else None


def sec_tables(dw):
    st, do = tables(dw)
    nst = [i for i, v in st.items() if v]
    ndo = [i for i, v in do.items() if v]
    for i in nst:
        print("ST %3d 0x%08X" % (i, st[i]))
    for i in ndo:
        print("DO %3d 0x%08X" % (i, do[i]))
    for m in range(NMODES):
        print("PMODE %2d start_xy=0x%08X start_unit=0x%08X frame=0x%08X" % (
            m, dw(PLR_START + 8 * m), dw(PLR_START + 8 * m + 4), dw(PLR_FRAME + 4 * m)))
    for p in range(1, 0x12):
        print("PKT 0x%02X 0x%08X flag=%d" % (p, dw(PKT_TABLE + 8 * p), dw(PKT_TABLE + 8 * p + 4)))
    print("SCAN tables st_nonnull=%d (ids %d..%d) do_nonnull=%d (ids %d..%d)" % (
        len(nst), min(nst), max(nst), len(ndo), min(ndo), max(ndo)))


def sec_calls(insns, starts):
    total = 0
    for tgt, name in TARGETS.items():
        sites = [a for a, t in insns if t in ("call   0x%x" % tgt, "jmp    0x%x" % tgt)]
        total += len(sites)
        print("CALLS %s 0x%08X n=%d: %s" % (name, tgt, len(sites), " ".join(
            "0x%08X(in 0x%08X)" % (a, enclosing(starts, a)) for a in sites)))
    print("SCAN calls targets=%d sites=%d" % (len(TARGETS), total))


def sec_conv(insns, starts, dw):
    st, do = tables(dw)
    rev = {}
    for i, v in st.items():
        if v:
            rev.setdefault(v, []).append("st%d" % i)
    for i, v in do.items():
        if v:
            rev.setdefault(v, []).append("do%d" % i)
    n = stores = 0
    funcs = set()
    for k, (a, t) in enumerate(insns):
        if not (SKILL_LO <= a < SKILL_HI) or "+0x1dc]" not in t:
            continue
        n += 1
        store = None
        for a2, t2 in insns[k + 1:k + 13]:
            if re.match(r"mov\s+BYTE PTR \[ebp-0x[0-9a-f]+\],", t2):
                store = (a2, t2)
                break
        f = enclosing(starts, a)
        funcs.add(f)
        if store:
            stores += 1
        print("CONV 0x%08X in 0x%08X %s | %s | store %s" % (
            a, f, ",".join(rev.get(f, ["-"])), t, "0x%08X %s" % store if store else "none"))
    print("SCAN conv reads=%d with_stack_byte_store=%d functions=%d" % (n, stores, len(funcs)))


def sec_c4(insns):
    s = [a for a, t in insns if re.match(r"or\s+DWORD PTR \[[a-z]+\+0xc4\],0x40$", t)]
    c = [a for a, t in insns if re.match(r"and\s+DWORD PTR \[[a-z]+\+0xc4\],0xffffffbf$", t)]
    ss = [a for a in s if SKILL_LO <= a < SKILL_HI]
    cs = [a for a in c if SKILL_LO <= a < SKILL_HI]
    print("C4SET " + " ".join("0x%08X" % a for a in s))
    print("C4CLR " + " ".join("0x%08X" % a for a in c))
    print("SCAN c4 set=%d clear=%d set_in_skill_range=%d clear_in_skill_range=%d" % (len(s), len(c), len(ss), len(cs)))


def sec_sites(insns):
    n = 0
    for label, lo, hi in SITES:
        print("SITE %s" % label)
        for a, t in insns:
            if lo <= a <= hi:
                print("  0x%08X %s" % (a, t))
                n += 1
    print("SCAN sites windows=%d instructions=%d" % (len(SITES), n))


def sec_rows(dw, txt):
    import csv
    st, do = tables(dw)
    rows = list(csv.reader(open(txt, encoding="latin-1"), delimiter="\t"))
    h = rows[0]
    recs = [dict(zip(h, r)) for r in rows[1:] if r and r[0] != "Expansion"]
    bad = 0
    used = {"st": set(), "do": set()}
    for r in recs:
        for col, tab, bound, key in (("srvstfunc", st, ST_BOUND, "st"), ("srvdofunc", do, DO_BOUND, "do"),
                                     ("srvprgfunc1", do, DO_BOUND, "do"), ("srvprgfunc2", do, DO_BOUND, "do"),
                                     ("srvprgfunc3", do, DO_BOUND, "do"), ("ItemEffect", do, DO_BOUND, "do")):
            v = r.get(col, "")
            if v == "" or (col == "ItemEffect" and int(v) <= 1):
                continue
            n = int(v)
            used[key].add(n)
            if not (0 <= n < bound) or not tab[n]:
                bad += 1
                print("ROWBAD %s %s=%d" % (r["skill"], col, n))
    def cnt(col, pred=lambda v: v not in ("", "0")):
        return sum(1 for r in recs if pred(r.get(col, "")))
    print("ROWS st_used=%d do_used=%d st_table_unused=%s do_table_unused=%s" % (
        len(used["st"]), len(used["do"]),
        ",".join(str(i) for i, v in st.items() if v and i not in used["st"]) or "-",
        ",".join(str(i) for i, v in do.items() if v and i not in used["do"]) or "-"))
    print("ROWS flags usemanaondo=%d decquant=%d InTown=%d LineOfSight=%d restrict=%d startmana=%d delay=%d "
          "periodic=%d aura=%d progressive=%d ItemEffect_gt1=%d ItemCheckStart=%d AttackNoMana=%d TargetableOnly=%d" % (
              cnt("usemanaondo"), cnt("decquant"), cnt("InTown"), cnt("LineOfSight"), cnt("restrict"),
              cnt("startmana"), cnt("delay"), cnt("periodic"), cnt("aura"), cnt("progressive"),
              cnt("ItemEffect", lambda v: v not in ("",) and int(v) > 1), cnt("ItemCheckStart"),
              cnt("AttackNoMana"), cnt("TargetableOnly")))
    print("SCAN rows rows=%d out_of_table=%d" % (len(recs), bad))


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
    st, do = tables(dw)
    extra = [v for v in list(st.values()) + list(do.values()) if v] + list(TARGETS)
    starts = func_starts(insns, extra)
    if which in ("calls", "all"):
        sec_calls(insns, starts)
    if which in ("conv", "all"):
        sec_conv(insns, starts, dw)
    if which in ("c4", "all"):
        sec_c4(insns)
    if which in ("sites", "all"):
        sec_sites(insns)


if __name__ == "__main__":
    main()
