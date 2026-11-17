#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S1ne (`lane/n66ne`): the route reads behind the batch's rows (ruling R2 of the plan 0066
inventory, ADR-0021, ADR-0029). For each root (a monsters/ai machinery or README function a row names), the direct-call
graph under it (tools/sweep2_s7e_routes.py's walker over tools/sweep_s4b.py's objdump bodies; indirect calls counted,
not followed), cut at the pool allocator and free entries and the fatal handlers, to a depth bound. Printed per root:
the first path to each allocator entry with the call site, every import call with its site, the number of other
indirect calls, the first path to each room or collision walker reached (MARK lines), and the root's direct call sites
in address order (SITE lines: the site, the callee and its symbol name), so a row's claim can be placed before or after
the first call whose route leaves the declarable set. A root's listing says which callees a route can reach; whether a
given case reaches them is the branch's reading, cited per row in the finding.

    python3 -I tools/ai_s1ne_routes.py [--depth N] > workspace/logs/n66ne/s1ne/routes/routes.txt

Stdlib only, plus the objdump binary. Read-only.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as W  # noqa: E402
import sweep2_s7e_routes as R  # noqa: E402

MARKS = {0x0064E260: "COLL_LineTest", 0x00463740: "RoomAtSubtile", 0x0061A010: "DUNGEON_GetCollMap",
         0x00649970: "PathPlan", 0x005A7C20: "MonSetMode", 0x005DEB60: "MonAiMove", 0x005416B0: "EventQueueAt",
         0x005DCE60: "AiSearchNearRooms", 0x005DCEE0: "AiSearchNearClients", 0x005DCF70: "AiSearchNearRoomsNoTown"}

ROOTS = [   # (label, entry, rows: m = machinery, r = README inventory rows)
    ("MonAiFindTarget", 0x005DD7F0, "m5, m6, m11, m12"),
    ("MonAiForcedTarget", 0x005DD610, "m13, m51"),
    ("MonAiFindHostile", 0x005DDC30, "m14"),
    ("MonAiPreferDecoy", 0x005DD510, "m11, m14"),
    ("AiHostileCandidate", 0x005DC970, "m16, m52"),
    ("AiDistUnits", 0x005DC380, "m17"),
    ("AiDistToPointSized", 0x005DC480, "m17"),
    ("UnitDistSq", 0x005B0BD0, "m18"),
    ("MonAiUseSeqSkill", 0x005DE000, "m24"),
    ("MonAiWalkToUnit", 0x005DEC80, "m27"),
    ("MonAiWalkToUnitOrZero", 0x005DECA0, "m27"),
    ("MonAiWalkToUnitType13", 0x005DED40, "m27"),
    ("MonAiWalkToPoint", 0x005DED90, "m27"),
    ("MonAiWalkToPointOrStop", 0x005DEE50, "m27"),
    ("MonAiWalkToPointCmd", 0x005DEF30, "m27"),
    ("MonAiWalkToUnitStop", 0x005DEF80, "m27"),
    ("MonAiWanderRing", 0x005DE200, "m28, m48"),
    ("MonAiWanderRingDirect", 0x005DF400, "m29, m48"),
    ("MonAiWanderNearUnit", 0x005DF530, "m29, m48"),
    ("MonAiRunNearUnit", 0x005DF680, "m29, m48"),
    ("MonAiStepAway", 0x005DEFE0, "m30"),
    ("MonAiStepAwayXY", 0x005DF140, "m31"),
    ("MonAiWalkToUnitType56", 0x005DF7D0, "m32, m50"),
    ("MonAiWalkTowardUnit", 0x005DE6D0, "m33"),
    ("MonAiMoveToUnitDist", 0x005DE4E0, "m33"),
    ("MonAiPathOverride", 0x005DE190, "m8, m36"),
    ("AiPathOverrideSet", 0x005A6260, "m8, m37"),
    ("AiParamsAlloc", 0x0058EC90, "m46"),
    ("AiParamsPop", 0x0058ED10, "m46"),
    ("AiParamsHead", 0x0058EE80, "m46"),
    ("AiParamsFind", 0x0058EEF0, "m46"),
    ("AiParamsPush", 0x0058EF40, "m46"),
    ("AiDeadMinionCb", 0x005DCDA0, "m65, m111"),
    ("AiFallenCorpseCb", 0x005F1380, "m65"),
    ("AiGreaterMummyCb", 0x005F2A00, "m73, m111, r56"),
    ("MonModeStartNeutral", 0x005A73E0, "r5, r6, r17"),
    ("MonAiDelayEarlier", 0x005DE130, "r20"),
    ("MonAiEntryGet", 0x005B15D0, "r24, r50"),
    ("gate 0x00623470", 0x00623470, "r25"),
    ("MonAiInit", 0x005B0E00, "r29, r31"),
    ("MonAiPreChecks", 0x005B10E0, "r39"),
    ("MonSpcWalkCheck", 0x005B13E0, "r42"),
]


def names():
    out = {}
    with open(os.path.join(os.path.dirname(HERE), "re", "symbols.csv"), newline="") as f:
        for row in csv.DictReader(f):
            if row["kind"] == "func":
                out[int(row["address"], 16)] = row["name"]
    return out


def marks(A, root, depth):
    seen, first = {root: None}, {}
    q = [(root, 0)]
    while q:
        e, d = q.pop(0)
        _, calls, _ = W.body(A, e)
        for site, t in calls:
            if t in MARKS and t != root:
                first.setdefault(t, (site, R.path(seen, e)))
                continue
            if t in R.POOL or t in R.FATAL:
                continue
            if t not in seen and d + 1 <= depth:
                seen[t] = e
                q.append((t, d + 1))
    return first


def main(argv):
    depth = int(argv[argv.index("--depth") + 1]) if "--depth" in argv else 4
    A = W.asm()
    nm = names()
    print("S1NE-ROUTES depth=%d roots=%d" % (depth, len(ROOTS)))
    for label, root, rows in ROOTS:
        seen, pool, imports, icalls, fatal = R.walk(A, root, depth)
        print("ROOT %s %08X (%s): functions=%d pool=%d imports=%d indirect=%d fatal=%d"
              % (label, root, rows, len(seen), len(pool), len(imports), icalls, len(fatal)))
        for t, (site, p) in sorted(pool.items()):
            print("  POOL %s at %08X via %s" % (R.POOL[t], site, p))
        for va, slot, e in imports:
            print("  IMPORT slot %08X at %08X in %08X" % (slot, va, e))
        for t, (site, p) in sorted(marks(A, root, depth).items()):
            print("  MARK %s at %08X via %s" % (MARKS[t], site, p))
        _, calls, ic = W.body(A, root)
        for site, t in sorted(calls):
            print("  SITE %08X -> %08X %s" % (site, t, nm.get(t, "?")))
        for va in sorted(ic):
            print("  SITE %08X -> indirect" % va)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
