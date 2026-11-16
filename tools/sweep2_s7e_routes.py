#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S7e part 2 (`lane/n66u`): the route reads behind the rows that leave c-emu. For each root,
the direct-call graph under it (tools/sweep_s4b.py's objdump body walker, recursive descent; indirect calls counted, not
followed), cut at the pool allocator and free entries and the fatal handlers, to a depth bound; printed per root: the
first path to each allocator entry reached, every import call (`call [slot]` with the slot in the import address table
0x006CC000-0x006CC5FF) with its site, and the number of other indirect calls.

    python3 -I tools/sweep2_s7e_routes.py [--depth N] > workspace/logs/n66u/s7e/routes.txt

Stdlib only, plus the objdump binary. Read-only.
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as W  # noqa: E402

POOL = {0x0040B4B0: "pool alloc 0x0040B4B0", 0x0040B430: "pool alloc 0x0040B430", 0x0040B480: "pool free 0x0040B480",
        0x00540BB0: "EventBlockNew 0x00540BB0"}
FATAL = {0x00408090: "assert", 0x00408A60: "fatal", 0x00681E09: "fatal"}
IAT = (0x006CC000, 0x006CC600)
SLOT = re.compile(r"ds:0x([0-9a-f]+)")

ROOTS = [   # (label, entry, rows)
    ("ActUnitsFrameReset", 0x0053B000, "frame 55, 56"),
    ("UnitFrameReset", 0x00553220, "frame 57"),
    ("ClientsRoomSync", 0x0052D440, "frame 64"),
    ("ClientRoomSync", 0x005380D0, "frame 65"),
    ("ActLevelsUnloadTick", 0x00643200, "frame 75; lifecycle 28"),
    ("UnitRoomUnlink", 0x0064C370, "frame 115"),
    ("PathMoveReset", 0x00648DC0, "path-README 4, 19"),
    ("PathPlan", 0x00649970, "path-README 20, 23, 25, 52, 69, 74"),
    ("PathReplan", 0x00650350, "path-README 27-30, 75"),
    ("PathSetFacing", 0x006488A0, "path-README 71"),
    ("PathLineFree", 0x00679720, "path-search 1"),
    ("PathPlanKnockback", 0x0067A000, "path-search 8"),
    ("T15Follow", 0x0067BDF0, "path-search 13, 33"),
    ("PathPlanRandomWalk", 0x0067A240, "path-search 16, 22"),
    ("PathPlanSpiral", 0x0067A140, "path-search 23"),
    ("PathPlanStraight", 0x00649760, "path-search 22, 23"),
    ("PathPlanSearch", 0x0067AD00, "path-search 25"),
    ("PathPlanType12", 0x00679E60, "path-search 32"),
    ("RoomWandererTick", 0x0054F060, "lifecycle 3, 72, 73, 75, 76"),
    ("WandererRoll", 0x0054EFF0, "lifecycle 74"),
    ("InactiveUnitSave", 0x00542E30, "lifecycle 47, 60"),
    ("ItemGroundExpiry", 0x00558A10, "lifecycle 50"),
]


def walk(A, root, depth):
    seen = {root: None}
    q = collections.deque([(root, 0)])
    pool, imports, icalls, fatal = {}, [], 0, set()
    while q:
        e, d = q.popleft()
        vas, calls, ic = W.body(A, e)
        for va in ic:
            mn, ops = A.at(va)
            m = SLOT.search(ops)
            if m and IAT[0] <= int(m.group(1), 16) < IAT[1]:
                imports.append((va, int(m.group(1), 16), e))
            else:
                icalls += 1
        for site, t in calls:
            if t in POOL:
                pool.setdefault(t, (site, path(seen, e)))
                continue
            if t in FATAL:
                fatal.add(t)
                continue
            if t not in seen and d + 1 <= depth:
                seen[t] = e
                q.append((t, d + 1))
    return seen, pool, imports, icalls, fatal


def path(seen, e):
    out = []
    while e is not None:
        out.append("%08X" % e)
        e = seen[e]
    return " <- ".join(out)


def main(argv):
    depth = int(argv[argv.index("--depth") + 1]) if "--depth" in argv else 3
    A = W.asm()
    print("S7E-ROUTES depth=%d roots=%d" % (depth, len(ROOTS)))
    for label, root, rows in ROOTS:
        seen, pool, imports, icalls, fatal = walk(A, root, depth)
        print("ROOT %s %08X (%s): functions=%d pool=%d imports=%d indirect=%d fatal=%d"
              % (label, root, rows, len(seen), len(pool), len(imports), icalls, len(fatal)))
        for t, (site, p) in sorted(pool.items()):
            print("  POOL %s at %08X via %s" % (POOL[t], site, p))
        for va, slot, e in imports:
            print("  IMPORT slot %08X at %08X in %08X" % (slot, va, e))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
