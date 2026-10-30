#!/usr/bin/env python3
"""Global (absolute-address) memory writes in the callee closure of a set of roots (plan 0055 P1.1).

    python3 -I tools/frame_globals.py [--exe workspace/install/app/game.exe] [--stop 0xADDR,...] ROOT ...

The closure is `tools/callee_writes.py`'s recursive descent (same walk, same stops, same switch-table rule). This
tool lists every instruction in it whose destination operand is an absolute address with no base register (AT&T
`mov %eax,0x731010`, `addl $0x1,0x883d48`, `incl 0x7a0648`, or an indexed `0x88c708(,%eax,4)`) inside the image's
writable `.data` section (0x00705000-0x00995000), plus each `lock`-prefixed instruction. Such a write touches state
that is not reached through a game pointer, so it is the candidate list for "state that two games share".

Output:
  G <site> <function> <address> <instruction>     one per absolute write
  A <address> <count> <functions...>              per address: sites and the functions writing it
  totals: functions <n>, unresolved <n>, absolute writes <n>, addresses <n>
Unresolved indirect calls are not followed (their count is printed; `callee_writes.py` lists them). Read-only.
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import callee_writes as cw  # noqa: E402

DATA_LO, DATA_HI = 0x00705000, 0x00995000
ABS = re.compile(r"^(?:\*)?0x([0-9a-f]+)(\(,%e[a-z]{2},\d\))?$")


def abs_writes(ins, funcs):
    out = []
    for entry, seen in funcs.items():
        for va in sorted(seen):
            mn, ops = ins[va]
            lock = mn.startswith("lock")
            if lock:
                mn = mn.split(None, 1)[1] if " " in mn else mn
            if not (cw.WRITE_MN.match(mn) or cw.STRING.match(mn) or lock):
                continue
            parts = cw.operands(ops)
            if not parts:
                continue
            m = ABS.match(parts[-1])
            if not m:
                if lock:
                    out.append((va, entry, None, mn + " " + ops))
                continue
            a = int(m.group(1), 16)
            if DATA_LO <= a < DATA_HI:
                out.append((va, entry, a, mn + " " + ops))
    return sorted(out)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exe", default=cw.EXE)
    ap.add_argument("--stop", default="")
    ap.add_argument("roots", nargs="+")
    ns = ap.parse_args(argv)
    ins, nxt = cw.parse(cw.disasm(ns.exe))
    roots = [(int(r, 16), None) for r in ns.roots]
    stops = {int(x, 16) for x in ns.stop.split(",") if x}
    names = cw.symbols()
    funcs, unresolved, stopped, tables = cw.walk(ins, nxt, roots, stops, cw.image(ns.exe))

    def nm(a):
        return names.get(a, "sub_%08X" % a)

    print("roots: %s  stops: %s" % (" ".join(ns.roots), ns.stop or "-"))
    w = abs_writes(ins, funcs)
    per = collections.defaultdict(list)
    for va, e, a, t in w:
        print("G 0x%08X %s %s %s" % (va, nm(e), "0x%08X" % a if a is not None else "lock", t))
        per[a].append(nm(e))
    for a in sorted(per, key=lambda x: -1 if x is None else x):
        fs = sorted(set(per[a]))
        print("A %s %d %s" % ("0x%08X" % a if a is not None else "lock", len(per[a]), " ".join(fs)))
    print("totals: functions %d, unresolved %d, absolute writes %d, addresses %d"
          % (len(funcs), len(unresolved), len(w), len(per)))


if __name__ == "__main__":
    main(sys.argv[1:])
