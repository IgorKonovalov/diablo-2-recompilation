#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S4e part 5f (`lane/n66z`), the closing part: no emulation. `static`, the objdump pins of
the part's static (c) readings; `xref`, the full direct-call, frame-slot and immediate scans they rest on; `sites`, the
routes (first allocator or import per direct call) of the remainders routed under ADR-0029 R2; `logs`, the level ids
and EQR gaps of the kept stats logs (aggregate 29). Parts 1 to 5e (tools/stats_s4e_emu.py, items_s4e_emu.py to
items_s4e9_emu.py, run/ to run9/) stay unchanged.

    python3 -I tools/items_s4e10_emu.py static                      objdump pins, per row
    python3 -I tools/items_s4e10_emu.py xref                        the scans
    python3 -I tools/items_s4e10_emu.py sites                       the R2 routes
    python3 -I tools/items_s4e10_emu.py logs                        aggregate 29 over s1017-run.lst and p47h-run.lst
    python3 -I tools/items_s4e10_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/n66z/s4e/run10. Rows: items/inventory 18, 87; stats/aggregate 2, 10, 29, 31, 36, 41;
stats/states 46; items/economy 46 (the caller half left by part 2). Stdlib only, plus objdump.
"""
import argparse
import collections
import csv
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_s4b as S4  # noqa: E402
import items_s4e3_emu as P3  # noqa: E402
import items_s4e7_emu as P7  # noqa: E402

DEFDIR = os.path.join(ROOT, "workspace", "logs", "n66z", "s4e", "run10")


def dis(lo, hi):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % lo,
                          "--stop-address=0x%x" % hi, S4.EXE], capture_output=True, text=True).stdout
    res = []
    for ln in out.splitlines():
        if ":\t" not in ln:
            continue
        a, _, txt = ln.strip().partition(":")
        res.append((int(a, 16), " ".join(txt.split())))
    return res


def funcs():
    rows = [r for r in csv.reader(open(os.path.join(ROOT, "re", "symbols.csv"))) if len(r) > 2 and r[1] == "func"]
    return sorted((int(r[0], 16), r[2]) for r in rows)


FUNCS = None


def owner(a):
    global FUNCS
    if FUNCS is None:
        FUNCS = funcs()
    lo = [f for f in FUNCS if f[0] <= a]
    hi = [f for f in FUNCS if f[0] > a]
    return (lo[-1] if lo else (0, "?")), (hi[0][0] if hi else a + 0x1000)


# ---------------------------------------------------------------------------------------------------------- static
PINS_STATIC = [
    ("inventory 18: InvRecordGrid copies 24 bytes from +0x10; InvPageGet reads its argument's two bytes", [
        (0x0065C23B, "mov", "edx,DWORD PTR [eax+0x10]"), (0x0065C25B, "mov", "eax,DWORD PTR [eax+0x24]"),
        (0x0063AE04, "movzx", "eax,BYTE PTR [ebx]"), (0x0063AE0A, "mov", "al,BYTE PTR [ebx+0x1]"),
        (0x0063AE53, "cmp", "dl,BYTE PTR [ebx]"), (0x0063AE5A, "cmp", "al,BYTE PTR [ebx+0x1]"),
        (0x0063AEB8, "mov", "cl,BYTE PTR [eax]"), (0x0063AEC2, "mov", "al,BYTE PTR [eax+0x1]"),
        (0x0063B067, "movzx", "edx,BYTE PTR [ebp-0x24]"), (0x0063B084, "movzx", "edx,BYTE PTR [ebp-0x23]"),
        (0x00560963, "movzx", "ecx,BYTE PTR [ebp-0x108]"), (0x0063C6F5, "movzx", "edx,BYTE PTR [ebp-0x108]"),
        (0x00660D02, "mov", "ecx,0x42"), (0x0063BBF2, "mov", "DWORD PTR [ebp-0x4],0x0"),
        (0x0063BC48, "cmp", "esi,DWORD PTR [ebp-0x4]")]),
    ("inventory 87: ITEMS_SetQuality's store; the cube's quality-9 output; ItemCreateByQuality's request quality", [
        (0x00627EAA, "cmp", "DWORD PTR [eax],0x4"), (0x00627EB9, "mov", "DWORD PTR [eax],ecx"),
        (0x00565EB6, "cmp", "BYTE PTR [ecx+0x6],0x9"), (0x00565EE5, "push", "0x9"), (0x00565EE8, "call", "0x627ea0"),
        (0x005574D1, "mov", "ecx,DWORD PTR [ebx+0x30]"), (0x005574DA, "push", "eax"),
        (0x005574DE, "call", "0x627ea0")]),
    ("aggregate 2: KeyConsume's link and reselect calls", [
        (0x0055F56B, "call", "0x627910"), (0x0055F57B, "call", "0x55da70")]),
    ("aggregate 10: STATLIST_Unlink calls the +0x38 callback", [
        (0x00625CED, "mov", "DWORD PTR [eax+0x38],ecx"), (0x00626BD2, "cmp", "DWORD PTR [ebp-0xc],0x0"),
        (0x00626BD9, "mov", "eax,DWORD PTR [edi+0x38]"), (0x00626BDC, "test", "eax,eax"),
        (0x00626BE0, "mov", "edx,DWORD PTR [edi+0x14]"), (0x00626BE3, "mov", "ecx,DWORD PTR [ebp-0xc]"),
        (0x00626BE6, "push", "edi"), (0x00626BE7, "call", "eax")]),
    ("aggregate 29: the act clock pass refreshes every player on a non-zero ActClockTick", [
        (0x0052D7BB, "lea", "esi,[edi+0xbc]"), (0x0052D7D2, "call", "0x61c040"), (0x0052D7D9, "je", "0x52d84c"),
        (0x0052D813, "call", "0x537860"), (0x0052D81C, "push", "0x1"), (0x0052D822, "call", "0x55fde0"),
        (0x0052D842, "mov", "esi,DWORD PTR [esi+0x4a8]"), (0x0052D855, "cmp", "ebx,0x5"),
        (0x0055FDE4, "push", "0x0"), (0x0055FDE8, "call", "0x55dbc0")]),
    ("aggregate 31: ITEMS_MakeEthereal writes only its argument", [
        (0x0065E4D4, "mov", "esi,DWORD PTR [ebp+0x8]"), (0x0065E4FC, "push", "0x400000"),
        (0x0065E501, "push", "esi"), (0x0065E502, "call", "0x6280d0"), (0x0065E52E, "push", "esi"),
        (0x0065E52F, "call", "0x627260"), (0x0065E5CB, "push", "esi"), (0x0065E5CC, "call", "0x627260"),
        (0x0065E5E9, "push", "esi"), (0x0065E5EA, "call", "0x627260")]),
    ("aggregate 36: add func 0 sends an aprop block to state 0, flags 0x40, as a prop block", [
        (0x0065FFB4, "push", "0x0"), (0x0065FFB6, "push", "0x40"), (0x0065FFB8, "push", "0x0"),
        (0x0065FFC5, "call", "0x65fe10"), (0x0065FFE3, "mov", "dl,BYTE PTR [ecx+0x87]"),
        (0x0065FFF2, "mov", "ecx,0x40"), (0x0065FFF7, "je", "0x660032"), (0x0065FFF9, "mov", "ecx,DWORD PTR [eax*4+0x6edb5c]"),
        (0x00660000, "mov", "eax,DWORD PTR [eax*4+0x6edb40]"), (0x0066000A, "push", "0x0"),
        (0x0066000C, "push", "ecx"), (0x0066000D, "push", "eax"), (0x00660019, "call", "0x65fe10"),
        (0x00660032, "xor", "eax,eax"), (0x00660034, "jmp", "0x660007")]),
    ("aggregate 41: EquipReqRefresh calls PlayerSkillReselect after its loop; the reselect's gates", [
        (0x0055DBCE, "je", "0x55def1"), (0x0055DBE6, "je", "0x55def1"), (0x0055DBF2, "call", "0x55d9d0"),
        (0x0055DBFF, "je", "0x55def0"), (0x0055DE99, "jl", "0x55de23"), (0x0055DEA0, "call", "0x55da70"),
        (0x0055DA76, "je", "0x55dab8"), (0x0055DA7E, "call", "0x6439b0"), (0x0055DA8A, "call", "0x620190"),
        (0x0055DA8F, "cmp", "ebx,eax"), (0x0055DA95, "call", "0x647960"), (0x0055DA9A, "sub", "eax,0x2"),
        (0x0055DA9F, "sub", "eax,0x5"), (0x0055DAB3, "call", "0x5701b0"), (0x0055DAD1, "call", "0x6201d0"),
        (0x0055DAF7, "call", "0x5701b0"), (0x00570346, "call", "0x56ff10"), (0x0056FFB4, "call", "0x56f7f0"),
        (0x0056FFFD, "call", "0x6251f0")]),
    ("economy 46: D2S_WriteCorpses's price call (player, item, difficulty 3, quest word, class 0x201, mode 0)", [
        (0x005698A8, "push", "0x0"), (0x005698AA, "push", "0x201"), (0x005698AF, "push", "eax"),
        (0x005698B0, "push", "0x3"), (0x005698B2, "push", "esi"), (0x005698B3, "push", "edi"),
        (0x005698B4, "call", "0x62fdc0"), (0x005698B9, "add", "ebx,eax")]),
    ("states 46: PetLimit -> PetRemove -> PetUnitRelease -> UnitKilled", [
        (0x0056E960, "call", "0x575900"), (0x005758DB, "call", "0x5750e0"), (0x00575137, "call", "0x574450"),
        (0x005744DB, "call", "0x57ccb0"), (0x00574501, "call", "0x5a7c20")]),
]


def pins_check(pins, tag):
    ok = 0
    for va, mn, sub in pins:
        line = [t for a, t in dis(va, va + 16) if a == va]
        txt = line[0] if line else ""
        good = bool(line) and txt.startswith(mn) and sub in txt
        ok += good
        print("  %s 0x%08X %s" % ("ok " if good else "BAD", va, txt))
    print("S4E10 static %s pins=%d ok=%d" % (tag.split(":")[0], len(pins), ok))
    return ok == len(pins)


def cmd_static():
    good, n = True, 0
    for row, pins in PINS_STATIC:
        print("row %s" % row)
        good &= pins_check(pins, row)
        n += len(pins)
    print("S4E10 static total pins=%d %s" % (n, "all ok" if good else "BAD"))
    return 0 if good else 1


# ---------------------------------------------------------------------------------------------------------- xref
REC_READERS = ((0x0065C1F0, 0x18, "InvRecordGrid"), (0x00660CB0, 0x108, "BeltsRecord"))
FRAME = re.compile(r"\[ebp-0x([0-9a-f]+)\]")


def xref_records():
    """inventory 18: per server call (at or above 0x00500000, each with a literal set 0, row 18's S4c half) of the two
    record readers, the out buffer's frame slot and every
    ebp-relative operand of the calling function inside that buffer (k = offset in the buffer); each lea of the buffer
    is a call argument, followed to its callee."""
    n_calls = n_reads = 0
    for tgt, size, nm in REC_READERS:
        for c in S4.raw_callers(tgt):
            (lo, fn), hi = owner(c)
            L = dis(lo, hi)
            idx = [i for i, (a, _) in enumerate(L) if a == c][0]
            back = L[max(0, idx - 12):idx]
            if c < 0x00500000:
                continue                      # the client's calls (row 18's first half: every literal-0 call is above)
            lea = [t for _, t in back if t.startswith("lea") and "ebp-" in t]
            X = int(FRAME.search(lea[-1]).group(1), 16)
            n_calls += 1
            print("== %s call 0x%08X in 0x%08X %s: out [ebp-0x%x], %d bytes" % (nm, c, lo, fn, X, size))
            for k, (a, t) in enumerate(L):
                for m in FRAME.finditer(t):
                    off = X - int(m.group(1), 16)
                    if 0 <= off < size:
                        nxt = ""
                        if t.startswith("lea"):
                            calls = [u for _, u in L[k + 1:k + 20] if u.startswith("call")]
                            nxt = "  -> next %s" % (calls[0] if calls else "(no call)")
                        else:
                            n_reads += 1
                        print("     k=0x%02x 0x%08X %s%s" % (off, a, t, nxt))
    print("S4E10 xref records server_calls=%d buffer_operands_not_lea=%d" % (n_calls, n_reads))


def pushed_args(c, n=2):
    (lo, _), _ = owner(c)
    L = dis(lo, c + 1)
    idx = [i for i, (a, _) in enumerate(L) if a == c]
    pushes = [t for _, t in L[:idx[0]] if t.startswith("push")] if idx else []
    return pushes[-n:][::-1]


def xref_callers():
    for t, nm in ((0x00627EA0, "ITEMS_SetQuality"), (0x00627910, "sub_00627910_StatListLinkOwner"),
                  (0x0055F140, "sub_0055F140_KeyConsume"), (0x0055DBC0, "sub_0055DBC0_EquipReqRefresh"),
                  (0x0055FDE0, "sub_0055FDE0_PlayerEquipRefresh"), (0x0055DA70, "sub_0055DA70_PlayerSkillReselect"),
                  (0x00575900, "sub_00575900_PetLimitRefresh"), (0x0065E4D0, "ITEMS_MakeEthereal")):
        cs = S4.raw_callers(t)
        fns = sorted({owner(c)[0] for c in cs})
        print("  %s 0x%08X: %d rel32 callers in %d functions, %d abs32" % (nm, t, len(cs), len(fns), len(S4.raw_abs(t))))
        for c in cs:
            (lo, fn), _ = owner(c)
            extra = ""
            if t == 0x00627EA0:
                pa = pushed_args(c)
                extra = "  quality arg: %s" % (pa[1] if len(pa) > 1 else "?")
            print("    0x%08X in 0x%08X %s%s" % (c, lo, fn, extra))
    print("S4E10 xref callers done")


def xref_branches():
    """aggregate 41: every branch of EquipReqRefresh's body that passes over its PlayerSkillReselect call."""
    L = dis(0x0055DBC0, 0x0055DF10)
    n = 0
    for a, t in L:
        m = re.match(r"j[a-z]+ 0x([0-9a-f]+)$", t)
        if m and a < 0x0055DEA0 < int(m.group(1), 16):
            n += 1
            print("  0x%08X %s" % (a, t))
    rets = [(a, t) for a, t in L if t.startswith("ret")]
    print("  rets: %s" % ", ".join("0x%08X %s" % r for r in rets))
    print("S4E10 xref reselect_bypass_branches=%d" % n)


def xref_ethereal():
    """aggregate 31: every `push 0x400000` of .text with its function (the flag's other users, not read)."""
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", S4.EXE], capture_output=True,
                         text=True).stdout
    sites = []
    for ln in out.splitlines():
        if ":\t" in ln:
            a, _, txt = ln.strip().partition(":")
            if " ".join(txt.split()) == "push 0x400000":
                sites.append(int(a, 16))
    for s in sites:
        (lo, fn), _ = owner(s)
        print("  0x%08X in 0x%08X %s" % (s, lo, fn))
    print("S4E10 xref push_0x400000=%d functions=%d" % (len(sites), len({owner(s)[0] for s in sites})))


def cmd_xref():
    xref_records()
    xref_callers()
    xref_branches()
    xref_ethereal()
    return 0


# ---------------------------------------------------------------------------------------------------------- sites
SITE_ROOTS = [(0x005701B0, "aggregate 41: PlayerSetSkill"), (0x0056FF10, "aggregate 41: AuraSelect"),
              (0x00575850, "states 46: PetLimit"), (0x00574450, "states 46: PetUnitRelease")]


def cmd_sites():
    P7.SITE_ROOTS = SITE_ROOTS
    return P7.cmd_sites()


# ---------------------------------------------------------------------------------------------------------- logs
def cmd_logs():
    """aggregate 29: per kept stats log, the level ids of its PLR lines and the commonest gaps between EQR frames."""
    n_logs = n_103 = n_136 = 0
    for lst in ("s1017-run.lst", "p47h-run.lst"):
        for p in open(os.path.join(ROOT, "workspace", "logs", "stats", lst)).read().split():
            lids, fr, first = collections.Counter(), [], None
            for ln in open(os.path.join(ROOT, p), errors="replace"):
                if ln.startswith("PLR "):
                    try:
                        lid = json.loads(ln[4:])["lid"]
                    except ValueError:
                        continue
                    lids[lid] += 1
                    first = lid if first is None else first
                elif ln.startswith("EQR "):
                    fr.append(json.loads(ln[4:])["fr"])
            gaps = collections.Counter(b - a for a, b in zip(fr, fr[1:]))
            top = gaps.most_common(1)[0][0] if gaps else None
            n_logs += 1
            n_103 += first == 103
            n_136 += top == 136
            print("  %-28s first_lid=%s lids=%s eqr=%d top_gaps=%s" % (os.path.basename(p), first, dict(lids), len(fr),
                                                                      gaps.most_common(3)))
    print("S4E10 logs logs=%d first_lid_103=%d commonest_gap_136=%d" % (n_logs, n_103, n_136))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["static", "xref", "sites", "logs", "manifest"])
    ap.add_argument("--dir", default=DEFDIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "static":
        return cmd_static()
    if a.cmd == "xref":
        return cmd_xref()
    if a.cmd == "sites":
        return cmd_sites()
    if a.cmd == "logs":
        return cmd_logs()
    return P3.cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
