#!/usr/bin/env python3
"""Static scans behind docs/findings/anim/0001-modes-frames.md (plan 0050 Phase 1, batch P1.1).

Usage:
  python3 -I tools/anim_scan.py <game.exe>             # all sections
  python3 -I tools/anim_scan.py <game.exe> tables      # the mode, event and animation tables in the image
  python3 -I tools/anim_scan.py <game.exe> pseq        # the player sequence tables (0x007483B8)
  python3 -I tools/anim_scan.py <game.exe> calls       # direct callers of the animation functions
  python3 -I tools/anim_scan.py <game.exe> queue       # the event kind pushed at each UnitQueueEvent call of the schedulers
  python3 -I tools/anim_scan.py <game.exe> rows <excel dir>   # (not in `all`) the table checks the finding cites

Reads the PE image for the tables and runs `objdump -d -M intel --no-show-raw-insn` for the code scans (an
independent linear disassembly: it also sees the jump-table case blocks that Ghidra leaves outside a function body).
Prints addresses and the binary's own table values only, no excel data. One `SCAN <section> ...` summary per section.
  tables  PEV/MEV the player and monster unit-event tables (0x006E1810, 0x006E2490, 15 slots); PMODE the player mode
          tables (start {xy, unit} 0x006E1740, frame 0x00732C10, 20 modes); MMODE the monster mode records
          (0x006E2260, 16 B: start, frame, end, schedule flag; rows 0..15 by mode, 16..20 the class overrides);
          MPF the per-frame mode table 0x006E23D0 (12 B per mode: always, never, by MonStats2 +0x104 bit); MEND the
          mode-end byte table 0x0073C6D0; START the attack start-frame table 0x006E8E60 (14 weapon classes x 7
          character classes); IWCLS the item weapon-class index list 0x007446A0 (count 0x007446E0); CWCLS the token
          list 0x006EB748 (13); SEQCOL the sequence column map 0x00748418 (14); P2M/M2P the transform mode maps
          0x006EB348 (20) and 0x006EB308 (16); TOKP/TOKM the mode token remaps 0x00745900 (count 0x00745910) and
          0x00745914 (count 0x0074591C).
  pseq    PSEQ <seqnum> <col> ptr len frames for every non-empty entry of 0x007483B8[0..23] (14 columns of 12 B),
          and PSEQF <seqnum> <col> <i> mode frame dir event for each 6-byte frame record.
  calls   `call 0x<target>` / `jmp 0x<target>` for each target in TARGETS, with the enclosing function (the nearest
          preceding padding-delimited start).
  rows    OVR <class> chart=<0|1> for the classes MonModeRecord's switch names (MonStats `SplGetModeChart`);
          SEQNUM: the largest Skills `seqnum` of a row with a `charclass`, and the count of rows without one whose
          `seqnum` exceeds 23 (the last g_PlrSeqTables index). Flags and counts only.
  queue   every `call 0x5417d0` in the scheduler range 0x005539B0-0x00553F20 with the immediate pushed as its first
          stack argument (the event kind).
"""
import bisect
import hashlib
import re
import struct
import subprocess
import sys


TARGETS = {
    0x00624690: "UNIT_SetMode",
    0x00624390: "UNIT_AnimInit",
    0x00623F50: "UNIT_AnimSetRate",
    0x00623E00: "UNIT_AnimAdvance",
    0x00621310: "UNIT_AnimAdvanceLoop",
    0x006217C0: "UNIT_AnimAtEnd",
    0x00623B10: "UNIT_AnimStartFrame",
    0x00621260: "UNIT_SeqInit",
    0x00621210: "UNIT_SeqReadFrame",
    0x006212C0: "sub_006212C0_UnitSetSeqPos",
    0x005533D0: "SUNIT_AnimInit",
    0x005539B0: "SUNIT_ScheduleModeEvents",
    0x00553B10: "SUNIT_RescheduleFromPct",
    0x00553C70: "SUNIT_RescheduleSkip",
    0x00553DC0: "SUNIT_RescheduleAt",
    0x00553F00: "SUNIT_ModeEveryFrame",
    0x00553990: "SUNIT_CancelModeEvents",
    0x00553570: "SUNIT_SetMode",
    0x00581020: "sub_00581020_PlayerModeEnd",
    0x005A8030: "MON_ModeEndGeneric",
}
SCHED_LO, SCHED_HI = 0x005539B0, 0x00553F20


class PE:
    def __init__(self, path):
        self.d = open(path, "rb").read()
        pe = struct.unpack_from("<I", self.d, 0x3C)[0]
        n = struct.unpack_from("<H", self.d, pe + 6)[0]
        osz = struct.unpack_from("<H", self.d, pe + 20)[0]
        self.secs = []
        o = pe + 24 + osz
        for _ in range(n):
            _name, vs, va, rs, ra = struct.unpack_from("<8sIIII", self.d, o)
            self.secs.append((va + 0x400000, vs, ra, rs))
            o += 40

    def rd(self, va, n):
        for base, vs, ra, rs in self.secs:
            if base <= va < base + max(vs, rs):
                off = va - base
                if off + n <= rs:
                    return self.d[ra + off:ra + off + n]
                return b"\0" * n  # .bss: zero-initialised
        raise ValueError(hex(va))

    def dw(self, va):
        return struct.unpack("<I", self.rd(va, 4))[0]


def h(v):
    return "0x%08X" % v


def code4(b):
    return b.decode("latin-1").replace(" ", "_")


def tables(pe):
    n = 0
    for name, base in (("PEV", 0x006E1810), ("MEV", 0x006E2490)):
        for i in range(15):
            print(name, i, h(pe.dw(base + 4 * i)))
            n += 1
    for m in range(20):
        print("PMODE", m, h(pe.dw(0x006E1740 + 8 * m)), h(pe.dw(0x006E1744 + 8 * m)), h(pe.dw(0x00732C10 + 4 * m)))
        n += 1
    for r in range(21):
        a = 0x006E2260 + 16 * r
        print("MMODE", r, h(pe.dw(a)), h(pe.dw(a + 4)), h(pe.dw(a + 8)), pe.dw(a + 12))
        n += 1
    for m in range(16):
        a = 0x006E23D0 + 12 * m
        print("MPF", m, pe.dw(a), pe.dw(a + 4), pe.dw(a + 8))
        print("MEND", m, pe.rd(0x0073C6D0 + m, 1)[0])
        n += 2
    for wc in range(14):
        print("START", wc, *[pe.dw(0x006E8E60 + 4 * (wc * 7 + c)) for c in range(7)])
        n += 1
    for i in range(pe.dw(0x007446E0)):
        print("IWCLS", i, code4(pe.rd(0x007446A0 + 8 * i, 4)), pe.dw(0x007446A4 + 8 * i))
        n += 1
    for i in range(13):
        print("CWCLS", i, code4(pe.rd(0x006EB748 + 8 * i, 4)), pe.dw(0x006EB74C + 8 * i))
        n += 1
    for i in range(14):
        print("SEQCOL", i, pe.dw(0x00748418 + 8 * i), pe.dw(0x0074841C + 8 * i))
        n += 1
    print("P2M", *[pe.dw(0x006EB348 + 4 * i) for i in range(20)])
    print("M2P", *[pe.dw(0x006EB308 + 4 * i) for i in range(16)])
    for name, base, cnt in (("TOKP", 0x00745900, 0x00745910), ("TOKM", 0x00745914, 0x0074591C)):
        for i in range(pe.dw(cnt)):
            print(name, i, code4(pe.rd(base + 8 * i, 4)), pe.dw(base + 4 + 8 * i))
            n += 1
    print("SCAN tables lines=%d" % (n + 2))


def pseq(pe):
    ne = nf = 0
    for s in range(24):
        tab = pe.dw(0x007483B8 + 4 * s)
        if not tab:
            continue
        for col in range(14):
            ptr, ln, fr = (pe.dw(tab + 12 * col + k) for k in (0, 4, 8))
            if not ptr:
                continue
            ne += 1
            print("PSEQ", s, col, h(ptr), ln, fr)
            for i in range(ln):
                rec = pe.rd(ptr + 6 * i, 6)
                print("PSEQF", s, col, i, rec[2], rec[3], rec[4], rec[5])
                nf += 1
    print("SCAN pseq entries=%d frames=%d" % (ne, nf))


def disasm(exe):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", exe], check=True,
                         capture_output=True, text=True).stdout
    ins = []
    for line in out.splitlines():
        m = re.match(r"\s+([0-9a-f]+):\s+(.*)$", line)
        if m:
            ins.append((int(m.group(1), 16), m.group(2).strip()))
    return ins


def starts(ins):
    s = []
    prev = None
    for a, t in ins:
        if prev is not None and (prev.startswith("int3") or prev.startswith("ret")) and not t.startswith("int3"):
            s.append(a)
        prev = t
    return s


def calls(ins):
    st = starts(ins)
    tot = 0
    for tgt, name in TARGETS.items():
        sites = [(a, t) for a, t in ins if re.match(r"(call|jmp)\s+0x%x$" % tgt, t)]
        for a, t in sites:
            i = bisect.bisect_right(st, a) - 1
            print("CALL", name, h(tgt), h(a), t.split()[0], "in", h(st[i]) if i >= 0 else "?")
        print("CALLS", name, h(tgt), len(sites))
        tot += len(sites)
    print("SCAN calls targets=%d sites=%d" % (len(TARGETS), tot))


def queue(ins):
    n = 0
    for k, (a, t) in enumerate(ins):
        if not (SCHED_LO <= a < SCHED_HI and re.match(r"call\s+0x5417d0$", t)):
            continue
        ev = None
        for j in range(k - 1, max(k - 12, 0), -1):
            m = re.match(r"push\s+(0x[0-9a-f]+)$", ins[j][1])
            if m:
                ev = int(m.group(1), 16)
                break
            if ins[j][1].startswith("push"):
                ev = "reg:" + ins[j][1].split()[1]
                break
        print("QEV", h(a), "event", ev)
        n += 1
    print("SCAN queue sites=%d" % n)


OVERRIDE_CLASSES = (0xF3, 0x14D, 0x193, 0x1A1, 0x1A2, 0x21F, 0x220, 0x23A, 0x2C1, 0x2C5)


def read_txt(path):
    lines = open(path, encoding="latin-1").read().split("\n")
    hdr = lines[0].rstrip("\r").split("\t")
    return [dict(zip(hdr, l.rstrip("\r").split("\t"))) for l in lines[1:] if l.strip()]


def rows(xdir):
    mon = read_txt(xdir + "/monstats.txt")
    for c in OVERRIDE_CLASSES:
        print("OVR", c, "chart=%d" % (1 if mon[c].get("SplGetModeChart", "").strip() else 0))
    sk = read_txt(xdir + "/skills.txt")
    withc = [int(r["seqnum"]) for r in sk if r.get("seqnum", "").strip() and r.get("charclass", "").strip()]
    over = [r for r in sk if r.get("seqnum", "").strip() and not r.get("charclass", "").strip() and int(r["seqnum"]) > 23]
    print("SEQNUM charclass_rows=%d max=%d noclass_over23=%d" % (len(withc), max(withc), len(over)))
    print("SCAN rows overrides=%d" % len(OVERRIDE_CLASSES))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    exe = sys.argv[1]
    sec = sys.argv[2] if len(sys.argv) > 2 else "all"
    print("SHA256", hashlib.sha256(open(exe, "rb").read()).hexdigest())
    pe = PE(exe)
    if sec in ("all", "tables"):
        tables(pe)
    if sec in ("all", "pseq"):
        pseq(pe)
    if sec == "rows":
        rows(sys.argv[3])
    if sec in ("all", "calls", "queue"):
        ins = disasm(exe)
        if sec in ("all", "calls"):
            calls(ins)
        if sec in ("all", "queue"):
            queue(ins)


if __name__ == "__main__":
    main()
