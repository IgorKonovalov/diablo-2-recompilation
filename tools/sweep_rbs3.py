#!/usr/bin/env python3
"""Static scans of the reverser sweep pass 3 (`lane/rbs3`) over the pinned Game.exe.

    python3 -I tools/sweep_rbs3.py callers 0xADDR [0xADDR ...]
    python3 -I tools/sweep_rbs3.py flagreads 0xOFF BIT [--getter 0xADDR:INDEX ...]
    python3 -I tools/sweep_rbs3.py window 0xADDR [BEFORE AFTER]
    python3 -I tools/sweep_rbs3.py pushes 0xADDR N
    python3 -I tools/sweep_rbs3.py writes 0xOFF [--mask 0xM] [--lo 0xA --hi 0xB]
    python3 -I tools/sweep_rbs3.py switch 0xBYTES 0xJUMPS FIRST COUNT [NJUMPS]

All subcommands read one GNU objdump Intel-syntax disassembly of `.text` (`objdump -d --no-show-raw-insn -M intel
-j .text`), run once per invocation; `--exe` overrides the image path. Function entries come from re/symbols.csv
(kind func) and, for code with no symbol row, from the first instruction after a run of `int3` padding; a site's
function is the nearest entry at or below it, printed with its symbols.csv name when it has one.

- `callers`: every direct `call`/`jmp` to each target: `X <site> <kind> <function entry> <name>`, then a count line
  `N <target> <sites> <functions>`.
- `flagreads OFF BIT`: every byte read of `[reg+OFF]` whose value is tested against bit BIT, either by an immediate
  mask `1<<BIT` on the same instruction (`test BYTE PTR [r+OFF],imm`), or by the bit-mask table `0x006CE268`
  (dword i = 1<<i) entry BIT read within 4 instructions before or after it. With `--getter ADDR:INDEX` it also lists the
  calls to a flag getter `(ecx=record, edx=bit index)` such as MONSTATS_FlagTest (0x00457490) whose `edx` is set to
  INDEX by a `mov edx,imm` within 6 instructions before the call, and the calls whose edx is not an immediate (`?`).
  Lines: `R <site> <function> <name> <instruction>`, `G <site> <function> <name> edx=<value>`, then counts.
  Over-approximation: the reg is not resolved to a table; each R line is classified by hand.
- `pushes ADDR N`: per direct call to ADDR, the operands of the last N `push` instructions before it (within 30
  instructions), nearest first, so argument 1 of a `__stdcall` comes first: `P <site> <function> <name> a1 | a2 ...`.
  A register operand is not resolved: read the window.
- `writes OFF`: every instruction that modifies a byte/word/dword at `[reg+OFF]` (mov, or, and, xor, add, sub, adc,
  sbb, inc, dec, not, neg, bts/btr/btc), optionally only sites in [lo, hi) and, with `--mask M`, only `or`/`mov` with an
  immediate that has a bit of M set, plus every register-source `or`/`mov` and every `and`/`xor`/`btr` (a clear or a
  write the scan cannot value): `W <site> <function> <name> <instruction>`, then a count.
- `switch BYTES JUMPS FIRST COUNT [NJUMPS]`: an MSVC two-level switch read from the image: case FIRST+i (i < COUNT)
  goes to dword `JUMPS[BYTES[i]]`; with BYTES = `-` the dword table is indexed directly. `S <case> <index> <target>`.
  The bound check and the default are read from the code (window).
- `window ADDR [B A]`: B instructions before and A after ADDR (default 12 12), for kept excerpts.

Stdlib only. Read-only.
"""
import argparse
import bisect
import csv
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
SYMS = os.path.join(ROOT, "re", "symbols.csv")
MASKS = 0x006CE268
LINE = re.compile(r"^\s+([0-9a-f]+):\s+(.*)$")


def disasm(exe):
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-M", "intel", "-j", ".text", exe],
                         check=True, capture_output=True, text=True).stdout
    ins = []
    for line in out.splitlines():
        m = LINE.match(line)
        if m:
            ins.append((int(m.group(1), 16), re.sub(r"\s+", " ", m.group(2).strip())))
    return ins


def symbols():
    names = {}
    with open(SYMS, newline="") as f:
        for row in csv.DictReader(f):
            if row["kind"] == "func":
                names[int(row["address"], 16)] = row["name"]
    return names


class Image:
    def __init__(self, exe):
        self.ins = disasm(exe)
        self.addrs = [a for a, _ in self.ins]
        self.names = symbols()
        entries = set(self.names)
        for i in range(1, len(self.ins)):
            if self.ins[i - 1][1] == "int3" and self.ins[i][1] != "int3":
                entries.add(self.ins[i][0])
        self.entries = sorted(entries)

    def func(self, addr):
        i = bisect.bisect_right(self.entries, addr) - 1
        e = self.entries[i] if i >= 0 else 0
        return e, self.names.get(e, "-")

    def index(self, addr):
        i = bisect.bisect_left(self.addrs, addr)
        if i >= len(self.addrs) or self.addrs[i] != addr:
            raise SystemExit("no instruction at %#x" % addr)
        return i


def cmd_callers(img, targets):
    for t in targets:
        pat = re.compile(r"^(call|jmp) 0x%x$" % t)
        funcs = set()
        n = 0
        for a, txt in img.ins:
            m = pat.match(txt)
            if m:
                e, name = img.func(a)
                funcs.add(e)
                n += 1
                print("X 0x%08X %s 0x%08X %s" % (a, m.group(1), e, name))
        print("N 0x%08X %d sites %d functions" % (t, n, len(funcs)))


def cmd_flagreads(img, off, bit, getters):
    mem = re.compile(r"BYTE PTR \[(e[a-z]{2})\+0x%x\]" % off)
    mask_ref = "0x%x" % (MASKS + 4 * bit)
    imm = 1 << bit
    nr = 0
    for i, (a, txt) in enumerate(img.ins):
        if not mem.search(txt) or txt.startswith("mov BYTE PTR") or txt.startswith("lea "):
            continue
        hit = False
        m = re.search(r",0x([0-9a-f]+)$", txt)
        if txt.startswith("test BYTE PTR") and m and int(m.group(1), 16) & imm:
            hit = True
        for j in range(max(0, i - 4), min(len(img.ins), i + 5)):
            if mask_ref in img.ins[j][1].split("ds:")[-1].split(",")[-1] or ("ds:" + mask_ref) in img.ins[j][1]:
                hit = True
        if hit:
            e, name = img.func(a)
            nr += 1
            print("R 0x%08X 0x%08X %s %s" % (a, e, name, txt))
    print("N reads %d (offset %#x bit %d)" % (nr, off, bit))
    for g, want in getters:
        pat = "call 0x%x" % g
        ng = 0
        for i, (a, txt) in enumerate(img.ins):
            if txt != pat:
                continue
            val = "?"
            for j in range(i - 1, max(0, i - 7), -1):
                t = img.ins[j][1]
                if t.startswith("mov edx,") or t.startswith("lea edx,") or t.startswith("xor edx,edx"):
                    v = t.split(",", 1)[1]
                    if t.startswith("xor"):
                        val = "0"
                    elif re.fullmatch(r"0x[0-9a-f]+", v):
                        val = str(int(v, 16))
                    else:
                        val = "?" + v.replace(" ", "")
                    break
            if val == str(want) or val.startswith("?"):
                e, name = img.func(a)
                ng += 1
                print("G 0x%08X 0x%08X %s edx=%s" % (a, e, name, val))
        print("N getter 0x%08X index %d: %d calls listed (immediate %d or not immediate)" % (g, want, ng, want))


def cmd_pushes(img, target, n):
    pat = "call 0x%x" % target
    k = 0
    for i, (a, txt) in enumerate(img.ins):
        if txt != pat:
            continue
        got = []
        j = i - 1
        while j > i - 30 and len(got) < n:
            if img.ins[j][1].startswith("push "):
                got.append(img.ins[j][1][5:])
            j -= 1
        e, name = img.func(a)
        k += 1
        print("P 0x%08X 0x%08X %s %s" % (a, e, name, " | ".join(got)))
    print("N 0x%08X %d calls" % (target, k))


WRITE_OPS = ("mov", "or", "and", "xor", "add", "sub", "adc", "sbb", "inc", "dec", "not", "neg", "bts", "btr", "btc")


def cmd_writes(img, off, mask, lo, hi):
    mem = re.compile(r"^(\w+) (BYTE|WORD|DWORD) PTR \[e[a-z]{2}\+0x%x\](,(.*))?$" % off)
    k = 0
    for a, txt in img.ins:
        if not (lo <= a < hi):
            continue
        m = mem.match(txt)
        if not m or m.group(1) not in WRITE_OPS:
            continue
        op, src = m.group(1), m.group(4)
        if mask is not None and op in ("mov", "or") and src is not None and re.fullmatch(r"0x[0-9a-f]+", src):
            if not int(src, 16) & mask:
                continue
        elif mask is not None and op not in ("mov", "or", "and", "xor", "btr", "bts", "btc"):
            continue
        e, name = img.func(a)
        k += 1
        print("W 0x%08X 0x%08X %s %s" % (a, e, name, txt))
    print("N writes %d (offset %#x%s)" % (k, off, "" if mask is None else " mask %#x" % mask))


def image_reader(exe):
    sys.path.insert(0, HERE)
    import pe_info
    data = open(exe, "rb").read()
    secs = pe_info.parse(exe)["sections"]

    def read(va, n):
        rva = va - 0x400000
        for sc in secs:
            if sc["va"] <= rva < sc["va"] + max(sc["vsize"], sc["rsize"]):
                o = rva - sc["va"] + sc["raw"]
                return data[o:o + n]
        raise SystemExit("address %#x not in the image" % va)
    return read


def cmd_switch(exe, bytes_va, jumps_va, first, count, njumps):
    read = image_reader(exe)
    if bytes_va is None:
        idx = list(range(count))
    else:
        idx = list(read(bytes_va, count))
    n = njumps or (max(idx) + 1)
    jt = [int.from_bytes(read(jumps_va + 4 * k, 4), "little") for k in range(n)]
    for i, k in enumerate(idx):
        print("S %d %d 0x%08X" % (first + i, k, jt[k]))


def cmd_window(img, addr, before, after):
    i = img.index(addr)
    for a, txt in img.ins[max(0, i - before):i + after + 1]:
        print("0x%08X %s" % (a, txt))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exe", default=EXE)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("callers")
    p.add_argument("targets", nargs="+")
    p = sub.add_parser("flagreads")
    p.add_argument("off")
    p.add_argument("bit", type=int)
    p.add_argument("--getter", action="append", default=[])
    p = sub.add_parser("window")
    p.add_argument("addr")
    p.add_argument("before", nargs="?", type=int, default=12)
    p.add_argument("after", nargs="?", type=int, default=12)
    p = sub.add_parser("pushes")
    p.add_argument("target")
    p.add_argument("n", type=int)
    p = sub.add_parser("writes")
    p.add_argument("off")
    p.add_argument("--mask")
    p.add_argument("--lo", default="0")
    p.add_argument("--hi", default="0xffffffff")
    p = sub.add_parser("switch")
    p.add_argument("bytes")
    p.add_argument("jumps")
    p.add_argument("first", type=int)
    p.add_argument("count", type=int)
    p.add_argument("njumps", nargs="?", type=int, default=0)
    a = ap.parse_args(argv)
    if a.cmd == "switch":
        cmd_switch(a.exe, None if a.bytes == "-" else int(a.bytes, 16), int(a.jumps, 16), a.first, a.count, a.njumps)
        return
    img = Image(a.exe)
    if a.cmd == "callers":
        cmd_callers(img, [int(t, 16) for t in a.targets])
    elif a.cmd == "flagreads":
        gs = []
        for g in a.getter:
            x, y = g.split(":")
            gs.append((int(x, 16), int(y)))
        cmd_flagreads(img, int(a.off, 16), a.bit, gs)
    elif a.cmd == "pushes":
        cmd_pushes(img, int(a.target, 16), a.n)
    elif a.cmd == "writes":
        cmd_writes(img, int(a.off, 16), None if a.mask is None else int(a.mask, 16), int(a.lo, 16), int(a.hi, 16))
    else:
        cmd_window(img, int(a.addr, 16), a.before, a.after)


if __name__ == "__main__":
    main(sys.argv[1:])
