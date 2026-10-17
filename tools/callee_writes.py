#!/usr/bin/env python3
"""Callee closure of a set of root functions in the pinned Game.exe, and the memory writes in it.

    python3 -I tools/callee_writes.py [--exe workspace/install/app/game.exe] [--asm <objdump .text dump>]
                                      [--stop 0xADDR,...] [--disp 0x0,...] [--all-writes] ROOT[:END] ...

Each ROOT is a function entry (hex). `ROOT:END` walks that function only up to, not including, the instruction at END
(a prefix of a function, such as 0x00680200 up to the test at 0x0068023B). The walk is a recursive descent over a GNU
objdump disassembly of `.text`: from each entry it follows the fall-through, every `jcc` and direct `jmp` target, and
every direct `call` target (a new function in the closure, walked whole); it stops a path at `ret`, at an indirect
`jmp` and at a direct `jmp`/`call` into a `--stop` address (listed, not followed: for allocators and CRT helpers). A switch jump
`jmp *TABLE(,%reg,4)` is followed through its table, read from the image: the dwords from TABLE while each points
into `.text` within 0x1000 bytes of the jump (at most 256; the table bound check in the code is not read, so a table
followed by code addresses could be over-read: the T line gives the count to check by hand). Any other indirect call
(`call *...`) or jump is listed as unresolved, with its site: the closure is complete only when that list is empty or
each entry is read by hand (resolved targets go in as further roots).

Output:
  F <entry> <name> <instructions>          every function in the closure (names from re/symbols.csv)
  T <site> <function> <table> <entries>    switch tables followed
  U <site> <function> <instruction>        unresolved indirect call / jump
  S <site> <function> -> <stop target>     calls into --stop functions
  W <site> <function> <instruction>        memory writes whose destination is a base register with a displacement
                                           in --disp (default 0: `(%reg)`, `0x0(%reg)`, `(%reg,%idx,s)`), and every
                                           string store (`stos`, `movs`); with --all-writes every memory write
A write is an instruction whose last AT&T operand is a memory operand and whose mnemonic modifies it (mov*, or, and,
xor, add, sub, adc, sbb, inc, dec, not, neg, shl/shr/sar/rol/ror, set*, xchg, pop to memory, fst*/fist*), plus the
string stores. Which object each base register holds is not resolved: the W lines are a list to classify by hand.
Stdlib only; runs objdump once unless --asm gives a saved dump. Read-only.
"""
import argparse
import csv
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
SYMS = os.path.join(ROOT, "re", "symbols.csv")

LINE = re.compile(r"^\s*([0-9a-f]+):\s+(\S+)\s*(.*)$")
WRITE_MN = re.compile(r"^(mov[a-z]*|or[bwl]?|and[bwl]?|xor[bwl]?|add[bwl]?|sub[bwl]?|adc[bwl]?|sbb[bwl]?|inc[bwl]?|"
                      r"dec[bwl]?|not[bwl]?|neg[bwl]?|sh[lr][bwl]?|sar[bwl]?|ro[lr][bwl]?|set[a-z]+|xchg[bwl]?|"
                      r"pop[lw]?|fst[a-z]*|fist[a-z]*|cmpxchg[bwl]?|xadd[bwl]?|bt[src][bwl]?)$")
STRING = re.compile(r"^(rep[a-z]* )?(stos|movs)")
MEM = re.compile(r"^(-?0x[0-9a-f]+)?\((%e[a-z]{2})?(,%e[a-z]{2},\d)?\)$")


def disasm(exe):
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-j", ".text", exe],
                         check=True, capture_output=True, text=True).stdout
    return out.splitlines()


def parse(lines):
    ins, order = {}, []
    for ln in lines:
        m = LINE.match(ln)
        if m:
            va = int(m.group(1), 16)
            mn, ops = m.group(2), m.group(3).split("#")[0].strip()
            if mn.startswith("rep") and ops and not ops.startswith(("$", "%", "(", "0x", "-", "*")):
                mn, ops = mn + " " + ops.split(None, 1)[0], (ops.split(None, 1)[1] if " " in ops else "")
            ins[va] = (mn, ops)
            order.append(va)
    nxt = {order[i]: order[i + 1] for i in range(len(order) - 1)}
    return ins, nxt


def operands(ops):
    depth, parts, cur = 0, [], ""
    for ch in ops:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def symbols():
    names = {}
    if os.path.exists(SYMS):
        with open(SYMS, newline="") as f:
            for r in csv.DictReader(f):
                if r["kind"] == "func":
                    names[int(r["address"], 16)] = r["name"]
    return names


def image(exe):
    """(va -> dword) reader over the PE sections of exe."""
    import struct
    b = open(exe, "rb").read()
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    opt = struct.unpack_from("<H", b, pe + 20)[0]
    base = struct.unpack_from("<I", b, pe + 24 + 28)[0]
    secs = []
    for i in range(nsec):
        o = pe + 24 + opt + 40 * i
        vsz, va, rsz, raw = struct.unpack_from("<IIII", b, o + 8)
        secs.append((base + va, max(vsz, rsz), raw, rsz))

    def dword(addr):
        for va, sz, raw, rsz in secs:
            if va <= addr < va + sz and addr - va + 4 <= rsz:
                return struct.unpack_from("<I", b, raw + addr - va)[0]
        return None
    return dword


SWITCH = re.compile(r"^\*0x([0-9a-f]+)\(,%e[a-z]{2},4\)$")


def target(ops):
    m = re.match(r"^0x([0-9a-f]+)$", ops)
    return int(m.group(1), 16) if m else None


def walk(ins, nxt, roots, stops, dword):
    funcs, unresolved, stopped, tables = {}, [], [], []
    queue = list(roots)
    while queue:
        entry, end = queue.pop(0)
        if entry in funcs:
            continue
        seen, work = set(), [entry]
        while work:
            va = work.pop()
            while va is not None and va not in seen and va in ins and va != end:
                seen.add(va)
                mn, ops = ins[va]
                if mn.startswith("ret"):
                    break
                if mn == "call" or mn == "jmp":
                    t = target(ops)
                    sw = SWITCH.match(ops) if mn == "jmp" else None
                    if t is None and sw:
                        tab, n = int(sw.group(1), 16), 0
                        while n < 256:
                            d = dword(tab + 4 * n)
                            if d is None or d not in ins or abs(d - va) > 0x1000:
                                break
                            work.append(d)
                            n += 1
                        tables.append((va, entry, tab, n))
                        break
                    if t is None:
                        unresolved.append((va, entry, mn + " " + ops))
                        if mn == "jmp":
                            break
                    elif t in stops:
                        stopped.append((va, entry, t))
                        if mn == "jmp":
                            break
                    elif mn == "call":
                        queue.append((t, None))
                    else:
                        work.append(t)
                        break
                elif mn.startswith("j") or mn.startswith("loop"):
                    t = target(ops)
                    if t is None:
                        unresolved.append((va, entry, mn + " " + ops))
                    else:
                        work.append(t)
                va = nxt.get(va)
        funcs[entry] = seen
    return funcs, unresolved, stopped, tables


def writes(ins, funcs, disps, every):
    out = []
    for entry, seen in funcs.items():
        for va in sorted(seen):
            mn, ops = ins[va]
            if STRING.match(mn):
                out.append((va, entry, mn + " " + ops))
                continue
            if not WRITE_MN.match(mn):
                continue
            parts = operands(ops)
            if not parts:
                continue
            m = MEM.match(parts[-1])
            if not m or m.group(2) is None:
                continue
            d = int(m.group(1), 16) if m.group(1) and not m.group(1).startswith("-") else (
                -int(m.group(1)[1:], 16) if m.group(1) else 0)
            if every or d in disps:
                out.append((va, entry, mn + " " + ops))
    return sorted(out)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exe", default=EXE)
    ap.add_argument("--asm")
    ap.add_argument("--stop", default="")
    ap.add_argument("--disp", default="0x0")
    ap.add_argument("--all-writes", action="store_true")
    ap.add_argument("roots", nargs="+")
    ns = ap.parse_args(argv)
    lines = open(ns.asm).read().splitlines() if ns.asm else disasm(ns.exe)
    ins, nxt = parse(lines)
    roots = []
    for r in ns.roots:
        a, _, b = r.partition(":")
        roots.append((int(a, 16), int(b, 16) if b else None))
    stops = {int(x, 16) for x in ns.stop.split(",") if x}
    disps = {int(x, 16) for x in ns.disp.split(",") if x}
    names = symbols()
    funcs, unresolved, stopped, tables = walk(ins, nxt, roots, stops, image(ns.exe))

    def nm(a):
        return names.get(a, "sub_%08X" % a)

    print("roots: %s  stops: %s  disp: %s" % (" ".join(ns.roots), ns.stop or "-", ns.disp))
    for e in sorted(funcs):
        print("F 0x%08X %s %d" % (e, nm(e), len(funcs[e])))
    for va, e, tab, n in sorted(tables):
        print("T 0x%08X %s 0x%08X %d" % (va, nm(e), tab, n))
    for va, e, t in sorted(unresolved):
        print("U 0x%08X %s %s" % (va, nm(e), t))
    for va, e, t in sorted(stopped):
        print("S 0x%08X %s -> 0x%08X %s" % (va, nm(e), t, nm(t)))
    w = writes(ins, funcs, disps, ns.all_writes)
    for va, e, t in w:
        print("W 0x%08X %s %s" % (va, nm(e), t))
    print("totals: functions %d, instructions %d, switch tables %d, unresolved %d, stopped %d, writes %d"
          % (len(funcs), sum(len(s) for s in funcs.values()), len(tables), len(unresolved), len(stopped), len(w)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
