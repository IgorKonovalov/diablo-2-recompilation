#!/usr/bin/env python3
"""Static reading of the .d2s legacy (< 92) and version 92..96 readers (`lane/rlg`, backlog 2026-10-27 archivist ->
reverser, legacy and version-92 readers). No game, no Ghidra: GNU objdump on the pinned Game.exe and the image's
bytes. The findings cite save/0001 § Plan 0038 lane/rlg; every list there is this tool's output.

    python3 -I tools/rlg_static.py [--exe GAME.EXE] > workspace/logs/rlg/static.txt

Sections of the output (one `## <name>` header each):
  versiontests  every compare of an immediate in 0x47..0x60 (71..96) and every range test on 0x47/0x48 in the
                functions of the two reader chains, with the instruction after it (the branch). Each hit is listed;
                which are version tests is said in the finding, hit by hit.
  jt-version    ITEMS_ReadFull's per-version base-adjust jump table (0x0062CDC4, versions 0x48..0x58).
  jt-fullprop   ITEMS_ReadFull's per-stat-id property switch (0x0062D999, ids 0..0xD5): id -> case address.
  jt-readprop   ITEMS_ReadProperty's per-stat-id switch (0x0062AC9A, ids 0x17..0x6A): id -> case address.
  v71record     sub_00532F30_ItemReadV71Record: every BITBUF read in address order, its width, signed or not, and
                the record offset the value is stored to.
  header        sub_00532690 (the legacy header reader): every access of its 0x82-byte header copy at
                [ebp-0xA4], as a header offset.
The last line is `RLG_STATIC hits=<n> functions=<n>`. Stdlib only, read-only.
"""
import argparse
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
IMAGE_BASE = 0x400000

# (name, start, end): end is the first address after the function (the next function's entry, or the jump tables
# that follow it). Legacy chain first, then the version 92..96 chain.
FUNCS = [
    ("PLRSAVE_ReadFile", 0x005343A0, 0x005344B0),
    ("sub_005344B0_PlayerLoadFromFile", 0x005344B0, 0x00534520),
    ("sub_00534520_PlayerLoadFromClient", 0x00534520, 0x005345A0),
    ("sub_005345A0_PlayerLoad", 0x005345A0, 0x00534630),
    ("D2S_ReadSave", 0x00534330, 0x005343A0),
    ("sub_00534020_ReadSaveLegacy", 0x00534020, 0x00534330),
    ("sub_00532690_ReadHeaderLegacy", 0x00532690, 0x00532BE0),
    ("sub_00532BE0_ReadQuestsLegacy", 0x00532BE0, 0x00532C70),
    ("sub_00532C70_ReadWaypointsLegacy", 0x00532C70, 0x00532D00),
    ("sub_00532D00_ReadNpcsLegacy", 0x00532D00, 0x00532D90),
    ("sub_00532DA0_ReadStatsLegacy", 0x00532DA0, 0x00532E70),
    ("sub_00532E90_ReadSkillsLegacy", 0x00532E90, 0x00532F30),
    ("sub_00532F30_ItemReadV71Record", 0x00532F30, 0x00533350),
    ("sub_00533350_ItemListReadV71", 0x00533350, 0x005335E0),
    ("sub_005337F0_ItemListReadByVersion", 0x005337F0, 0x00533850),
    ("sub_00533850_ReadCorpseLegacy", 0x00533850, 0x005339A0),
    ("sub_005339A0_ReadCorpsesLegacy", 0x005339A0, 0x00533A70),
    ("sub_00533C70_ReadMercOldSave", 0x00533C70, 0x00533F70),
    ("sub_00533F70_ReadHotkeysLegacy", 0x00533F70, 0x00534020),
    ("D2S_ReadSaveV92", 0x0056B180, 0x0056B3E0),
    ("D2S_ReadHeader", 0x0056A090, 0x0056A370),
    ("D2S_ReadQuests", 0x0056A370, 0x0056A3E0),
    ("D2S_ReadWaypoints", 0x0056A3E0, 0x0056A470),
    ("D2S_ReadNpcs", 0x0056A470, 0x0056A4F0),
    ("D2S_ReadStatsBits", 0x0056A4F0, 0x0056A620),
    ("D2S_ReadStats", 0x0056A620, 0x0056A710),
    ("D2S_ReadSkills", 0x0056A710, 0x0056A7E0),
    ("D2S_ReadItemList", 0x0056A7E0, 0x0056A830),
    ("D2S_ReadCorpses", 0x0056A830, 0x0056AA50),
    ("D2S_ReadMercHeader", 0x0056AA50, 0x0056AC10),
    ("D2S_ReadMercItems", 0x0056AC10, 0x0056ACE0),
    ("sub_0056ACE0_ReadGolemItem", 0x0056ACE0, 0x0056AE50),
    ("D2S_ReadGolem", 0x0056AE50, 0x0056AF20),
    ("sub_0056AF20", 0x0056AF20, 0x0056AF80),
    ("D2S_LoadFinish", 0x0056AF80, 0x0056B180),
    ("ITEMS_ReadInventoryList", 0x005335E0, 0x005337F0),
    ("sub_00558CB0_ItemCreateFromSave", 0x00558CB0, 0x00558D90),
    ("ITEMS_ReadCompact", 0x0062A970, 0x0062AC80),
    ("ITEMS_ReadProperty", 0x0062AC80, 0x0062AD9A),
    ("ITEMS_PeekHeader", 0x0062AE20, 0x0062AF50),
    ("ITEMS_ReadFull", 0x0062CBE0, 0x0062E280),
    ("ITEMS_Deserialize", 0x0062E430, None),
]

RE_CMP = re.compile(r"\bcmp\s+(.+),0x(4[7-9a-f]|5[0-9a-f]|60)$")
RE_RANGE = re.compile(r"\b(lea\s+\w+,\[e[abcd]x-0x4[78]\]|add\s+\w+,0xffffffb[89]|sub\s+\w+,0x4[78])$")
RE_INS = re.compile(r"^\s*([0-9a-f]+):\s+(.*?)\s*$")


def pe_bytes(exe):
    data = open(exe, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    secs = []
    for i in range(nsec):
        o = pe + 24 + opt + 40 * i
        vsz, va, rsz, rp = struct.unpack_from("<IIII", data, o + 8)
        secs.append((va, max(vsz, rsz), rp))

    def read(addr, n):
        rva = addr - IMAGE_BASE
        for va, sz, rp in secs:
            if va <= rva < va + sz:
                return data[rp + rva - va:rp + rva - va + n]
        raise ValueError(hex(addr))
    return read


def disasm(exe, start, end):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn",
                          "--start-address=0x%x" % start, "--stop-address=0x%x" % end, exe],
                         capture_output=True, text=True, check=True).stdout
    ins = []
    for line in out.splitlines():
        m = RE_INS.match(line)
        if m and not m.group(2).startswith("int3") and m.group(2):
            ins.append((int(m.group(1), 16), m.group(2)))
    return ins


def func_end(exe, start):
    """ITEMS_Deserialize: the end is the first `ret` followed by int3 padding."""
    ins = disasm(exe, start, start + 0x1000)
    for (a, t), nxt in zip(ins, ins[1:] + [(0, "")]):
        if t.startswith("ret") and (nxt[0] - a) > 4:
            return a + (3 if " " in t else 1)
    raise ValueError("no end for %x" % start)


def section_versiontests(exe):
    print("## versiontests")
    hits = 0
    for name, start, end in FUNCS:
        if end is None:
            end = func_end(exe, start)
        ins = disasm(exe, start, end)
        print("# %s 0x%08X-0x%08X" % (name, start, end))
        for i, (a, t) in enumerate(ins):
            if RE_CMP.search(t) or RE_RANGE.search(t):
                nxt = " | ".join(x[1] for x in ins[i + 1:i + 3])
                print("0x%08X  %-40s -> %s" % (a, t, nxt))
                hits += 1
    return hits


def section_tables(read):
    print("## jt-version (ITEMS_ReadFull, version - 0x48 -> byte table 0x0062E294 -> case table 0x0062E280)")
    bt = read(0x0062E294, 0x11)
    cases = struct.unpack("<5I", read(0x0062E280, 20))
    for i, b in enumerate(bt):
        print("version %d (0x%02X) -> case %d 0x%08X" % (0x48 + i, 0x48 + i, b, cases[b]))
    print("## jt-fullprop (ITEMS_ReadFull, stat id 0..0xD5 -> byte table 0x0062E330 -> case table 0x0062E2CC)")
    bt = read(0x0062E330, 0xD6)
    cases = struct.unpack("<25I", read(0x0062E2CC, 100))
    groups = {}
    for i, b in enumerate(bt):
        groups.setdefault(b, []).append(i)
    for b in sorted(groups):
        ids = groups[b]
        shown = ",".join(str(x) for x in ids) if len(ids) < 30 else "%d ids (every other id 0..213)" % len(ids)
        print("case %2d 0x%08X ids %s" % (b, cases[b], shown))
    print("## jt-readprop (ITEMS_ReadProperty, stat id - 0x17 -> byte table 0x0062ADCC -> case table 0x0062AD9C)")
    bt = read(0x0062ADCC, 0x54)
    cases = struct.unpack("<12I", read(0x0062AD9C, 48))
    groups = {}
    for i, b in enumerate(bt):
        groups.setdefault(b, []).append(i + 0x17)
    for b in sorted(groups):
        ids = groups[b]
        shown = ",".join(str(x) for x in ids) if len(ids) < 30 else "%d ids (every other id 23..106)" % len(ids)
        print("case %2d 0x%08X ids %s" % (b, cases[b], shown))


RE_PUSH = re.compile(r"^push\s+0x([0-9a-f]+)$")
RE_STORE = re.compile(r"^mov\s+(BYTE|WORD|DWORD) PTR \[esi(\+0x[0-9a-f]+)?(\+edi\*1\+0x[0-9a-f]+)?\],(\w+)$")


def section_v71(exe):
    print("## v71record (sub_00532F30_ItemReadV71Record: read order, width, store)")
    ins = disasm(exe, 0x00532F30, 0x00533350)
    reads = 0
    for i, (a, t) in enumerate(ins):
        if t in ("call   0x411020", "call   0x411030"):
            width = None
            for _, pt in reversed(ins[max(0, i - 6):i]):
                m = RE_PUSH.match(pt.replace("   ", " ").replace("  ", " "))
                if m:
                    width = int(m.group(1), 16)
                    break
            store = "(not stored)"
            regs = {"al", "ax", "eax"}
            for b, st in ins[i + 1:i + 12]:
                st = re.sub(r"\s+", " ", st)
                if st.startswith("call"):
                    break
                mz = re.match(r"^movzx (\w+),(al|ax)$", st)
                if mz:
                    regs.add(mz.group(1))
                    continue
                m = RE_STORE.match(st)
                if m and m.group(4) in regs:
                    store = "-> [esi%s%s] %s (0x%08X)" % (m.group(2) or "", m.group(3) or "", m.group(1), b)
                    break
                if st == "mov edi,eax":
                    store = "-> edi (0x%08X)" % b
                    break
            kind = "signed" if t.endswith("411030") else "unsigned"
            print("0x%08X read %s %s bits %s" % (a, kind, width if width is not None else "?(pushed earlier)", store))
            reads += 1
    print("# %d reads" % reads)


def section_header(exe):
    print("## header (sub_00532690: accesses of the header copy at [ebp-0xA4], offset = 0xA4 - k)")
    ins = disasm(exe, 0x00532690, 0x00532BE0)
    for a, t in ins:
        for m in re.finditer(r"\[ebp-0x([0-9a-f]+)\]", t):
            k = int(m.group(1), 16)
            if 0x22 <= k <= 0xA4:
                print("0x%08X  +0x%02X  %s" % (a, 0xA4 - k, t))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exe", default=EXE)
    args = ap.parse_args()
    read = pe_bytes(args.exe)
    hits = section_versiontests(args.exe)
    section_tables(read)
    section_v71(args.exe)
    section_header(args.exe)
    print("RLG_STATIC hits=%d functions=%d" % (hits, len(FUNCS)))


if __name__ == "__main__":
    sys.exit(main())
