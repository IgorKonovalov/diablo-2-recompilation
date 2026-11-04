#!/usr/bin/env python3
"""lane/s52c review: registers an inline seed step zeroes that a think then pushes.

An inline step's `adc` often takes a register it zeroed with `xor r, r`, and a later `push r` passes that 0, so a listing
that collapses the step hides the argument. Rows 18, 49 and 74's `T56` flags were misread that way (plan 0052's log).

    python3 -I tools/ai_step_regs.py <game.exe>

For each think named in docs/specs/monsters/ai/catalogue.md: one line per such push. A linear scan with a 0x50-byte window:
it names sites to read at their instructions and proves nothing about the others. Stdlib and objdump only.
"""
import bisect
import csv
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def thinks():
    path = os.path.join(HERE, "..", "docs", "specs", "monsters", "ai", "catalogue.md")
    seen = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"#### (R\d+|S\d+)\..*@0x([0-9A-F]{8})", line)
        if m:
            seen.setdefault(int(m[2], 16), m[1])
    return seen


def func_starts():
    path = os.path.join(HERE, "..", "re", "symbols.csv")
    return sorted(int(r["address"], 16) for r in csv.DictReader(open(path, encoding="utf-8")) if r["kind"] == "func")


def listing(image):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", image], capture_output=True, text=True, check=True).stdout
    code = []
    for line in out.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+(.*)", line)
        if m:
            code.append((int(m[1], 16), re.sub(r"\s+", " ", m[2]).strip()))
    return code


def scan(code):
    """Yield (address of the push, register, address of the xor) for one function's lines."""
    zero = {}
    for i, (x, t) in enumerate(code):
        m = re.match(r"xor (e[a-z]{2}),\1$", t)
        if m:
            if any(re.match(r"adc e[a-z]{2}," + m[1] + "$", code[j][1]) for j in range(i + 1, min(i + 8, len(code)))):
                zero[m[1]] = x
            continue
        p = re.match(r"push (e[a-z]{2})$", t)
        if p and p[1] in zero and x - zero[p[1]] < 0x50:
            yield x, p[1], zero[p[1]]
        w = re.match(r"(mov|lea|movzx|movsx|add|sub|pop|imul|and|or|shr|sar|shl) (e[a-z]{2})\b", t)
        if w:
            zero.pop(w[2], None)
        if t.startswith(("call", "ret")):
            for r in ("eax", "ecx", "edx"):
                zero.pop(r, None)


def main(argv):
    if len(argv) != 1:
        raise SystemExit(__doc__)
    names, starts, lines = thinks(), func_starts(), listing(argv[0])
    addrs = [x for x, _ in lines]
    steps = pushes = 0
    for a in sorted(names):
        k = bisect.bisect_right(starts, a)
        e = starts[k] if k < len(starts) else a + 0x1000
        code = lines[bisect.bisect_left(addrs, a) : bisect.bisect_left(addrs, e)]
        steps += sum(t.startswith("adc") for _, t in code)
        for x, r, z in scan(code):
            pushes += 1
            print(f"{names[a]} 0x{x:08X} push {r} zeroed 0x{z:08X}")
    print(f"adc={steps} pushes={pushes}")


if __name__ == "__main__":
    main(sys.argv[1:])
