#!/usr/bin/env python3
"""Static scan for readers of a unit's light radius and of the `invis` state in the pinned Game.exe (backlog
2026-10-30 architect-reverser light-radius-server-readers, `lane/rfix`).

    python3 -I tools/light_radius_scan.py [--exe PATH] [--symbols re/symbols.csv]

Runs `objdump -d -M intel` over the image (objdump must be on PATH) and prints, from the disassembly alone:
  - `GETTERS`: the call count to each of the ten stat getters below, and `STATIMM <id> <n>`, the histogram of the
    stat id pushed as an immediate for those calls (the second push before the call: stdcall `(unit, stat, layer)`);
    `NONIMM <n>`: the calls whose stat push is not an immediate.
  - `IMM59`: every instruction with the immediate 0x59 (stat 89 `lightradius`) outside a memory operand, with the
    nearest named function before it (`re/symbols.csv`).
  - `GET59`: every getter call with a `push 0x59` or `mov <reg>, 0x59` among its ten previous instructions.
  - `D12F`: every instruction with the displacement `+0x12f]` (the item record's `lightradius` byte, Weapons/Armor/
    Misc `+0x12F`).
  - `ST146`: every call to `UNIT_HasState` (0x00639DF0) or `UNIT_HasStateFlag` (0x0063A7B0) with `push 0x92`
    (state 146 `invis`) among its six previous instructions.
  - `CALLEES <fn>`: the direct call targets of the target-search functions (`MonAiFindTarget` and the four it reaches
    for a candidate), each body taken up to the next named function, with counts.
The scan under-approximates a stat id computed at run time or read from a table (the `NONIMM` calls). Stdlib only.
Read-only.
"""
import argparse
import bisect
import collections
import csv
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
SYMS = os.path.join(ROOT, "re", "symbols.csv")
GETTERS = {0x624ED0: "StatListGetBaseValue", 0x624F60: "StatListGetValue", 0x624FE0: "STATLIST_SumOwnAndChildren",
           0x625350: "StatListGetBaseStat", 0x625420: "StatListGetStat", 0x625480: "STATS_GetUnitStat",
           0x625500: "UnitGetStat", 0x6253B0: "STATS_GetUnitBaseStat", 0x625560: "UnitStatDelta",
           0x625D00: "StatListGetBaseStatJ"}
SEARCH_FNS = (0x5DD7F0, 0x5DD610, 0x5DD510, 0x5DD0B0, 0x5DC970)
STATE_FNS = {0x639DF0: "UNIT_HasState", 0x63A7B0: "UNIT_HasStateFlag"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default=EXE)
    ap.add_argument("--symbols", default=SYMS)
    a = ap.parse_args()
    dis = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", a.exe],
                         capture_output=True, text=True, check=True).stdout
    L = []
    for line in dis.splitlines():
        m = re.match(r"\s+([0-9a-f]+):\t(.*)", line)
        if m:
            L.append((int(m.group(1), 16), m.group(2).strip()))
    S = []
    with open(a.symbols, newline="") as f:
        for r in csv.reader(f):
            if r and r[0].startswith("0x") and r[1] == "func":
                S.append((int(r[0], 16), r[2]))
    S.sort()
    keys = [x for x, _ in S]

    def owner(addr):
        i = bisect.bisect_right(keys, addr) - 1
        return f"{S[i][1]}+{addr - S[i][0]:#x}" if i >= 0 else "?"

    def callee(t):
        m = re.match(r"call\s+0x([0-9a-f]+)$", t)
        return int(m.group(1), 16) if m else None

    calls = collections.Counter()
    ids = collections.Counter()
    nonimm = 0
    get59, st146 = [], []
    imm = re.compile(r"(?<![0-9a-fx+\-])0x59(?![0-9a-f])")
    imm59 = [(x, t) for x, t in L if imm.search(t) and not re.search(r"\[[^\]]*0x59\]", t)]
    d12f = [(x, t) for x, t in L if re.search(r"\+0x12f\]", t)]
    for i, (x, t) in enumerate(L):
        c = callee(t)
        if c in GETTERS:
            calls[c] += 1
            pushes = []
            for j in range(i - 1, max(0, i - 15), -1):
                tt = L[j][1]
                if tt.startswith(("call", "ret", "jmp")):
                    break
                if tt.startswith("push"):
                    pushes.append(tt)
                    if len(pushes) == 2:
                        break
            if len(pushes) == 2 and re.match(r"push\s+0x[0-9a-f]+$", pushes[1]):
                ids[int(pushes[1].split()[1], 16)] += 1
            else:
                nonimm += 1
            for j in range(max(0, i - 10), i):
                tt = L[j][1]
                if re.match(r"(push|mov)\s+(\S+,)?0x59$", tt):
                    get59.append((x, L[j][0], tt))
                    break
        if c in STATE_FNS:
            for j in range(max(0, i - 6), i):
                if L[j][1] == "push   0x92":
                    st146.append((x, STATE_FNS[c]))
                    break
    print(f"GETTERS calls={sum(calls.values())} " + " ".join(f"{GETTERS[k]}={calls[k]}" for k in sorted(GETTERS)))
    for k in sorted(ids):
        print(f"STATIMM {k} {ids[k]}")
    print(f"NONIMM {nonimm}")
    print(f"STATIMM89 {ids.get(0x59, 0)}")
    print(f"GET59 {len(get59)}")
    for x, y, tt in get59:
        print(f"  {x:#010x} {owner(x)} <- {y:#010x} {tt}")
    print(f"IMM59 {len(imm59)}")
    for x, t in imm59:
        print(f"  {x:#010x} {owner(x)} :: {t}")
    print(f"D12F {len(d12f)}")
    for x, t in d12f:
        print(f"  {x:#010x} {owner(x)} :: {t}")
    print(f"ST146 {len(st146)}")
    for x, n in st146:
        print(f"  {x:#010x} {owner(x)} {n}")
    names = dict(S)
    for fn in SEARCH_FNS:
        end = keys[bisect.bisect_right(keys, fn)]
        cs = collections.Counter(callee(t) for x, t in L if fn <= x < end and callee(t) is not None)
        print(f"CALLEES {names.get(fn, hex(fn))} {sum(cs.values())}")
        for c in sorted(cs):
            print(f"  {c:#010x} {names.get(c, '?')} {cs[c]}")


if __name__ == "__main__":
    main()
