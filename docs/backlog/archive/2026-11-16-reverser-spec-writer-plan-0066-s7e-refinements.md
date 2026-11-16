---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../specs/sim/frame.md
  - ../../specs/drlg/collision.md
  - ../../specs/quests/travel.md
  - ../../plans/0066-simulation-inferred-claims-sweep.md#implementation-log
resolution: "Items 1 and 2 done 2026-11-16 in plan 0066 Phase 3, frame cluster (lane/n66pf): sim/frame D9 states the frame −2 null tail as the code's map ([I] for the game's fault) and the slot below the control; drlg/collision E4 returns 0x27 for a room with no map and reads a null cell pointer through ([I]); item 3 was done in the quests cluster [log](../../plans/0066-simulation-inferred-claims-sweep.md#2026-11-16--phase-3-the-frame-cluster-re-tagged-spec-writer-lanen66pf)"
---

Plan 0066 batch S7e part 2 (`lane/n66u`, [run:2026-11-16-sweep2-s7e](../../findings/frame/experiments.md#run2026-11-16-sweep2-s7e))
found two readings and one scope the specs do not state. Not blocking. Both are maps of the code under emulation; what the game does at the
faulting access stays `[I]` (ADR-0015 (5)).

1. **sim/frame D9 / E1, the counter's wrap.** At current frame −2 a frame at or below it is raised to −1, the
   every-frame sentinel. `EventQueueAt` then tests the raised frame against −1 (0x00541721), takes a null tail
   (0x0054173D), reads and writes the dword at address 0 (0x00541771, 0x0054177D: an access violation in the game) and
   sets the type's every-frame head when it is empty (0x00541782–0x005417BB). D9 says only that a positive frame is kept
   against a negative current one (now raised by `qx`). Also: a negative frame of list 0 indexes its head slot below the
   control (`ctl + 4 + 4·smod64(F)`), the case the "smod64" note may want.
2. **drlg/collision E4, "r has no cells".** `COLL_RectTest` tests the room's map (0x0064CEDE) but not the map's cell
   pointer; `COLL_RectTestInMap` (0x0064CC30) reads from `0 + 2·index` (0x0064CCA0). E4's `0x27` return holds for a
   missing map; a map with a null cell pointer is read through the null pointer. Whether the stock game ever holds such a
   map is not read.
3. **quests/travel B1, a scope bullet for the free-cell search at other sizes and steps.** The search through both wrappers
   (`0x0064E7E0` as `PlayerChangeAct` calls it, step 5; `0x0064E810` as `PortalObjectCreate` calls it, radius 50, step 1,
   size 3 with `maskA` 0x3E01 and the walk's `maskB` 0x0C01) and directly with an origin, at sizes 0 to 4 and steps 1 to 5,
   is the code's map `[C]` (ADR-0015, ADR-0029 (a)): family `ffn` of run:2026-11-16-sweep2-s7e, 596 cases compared with 0
   mismatches (600 run; 4 left out, a map with no cell array, see item 2). The ring step (`step1` separates 268), the walk
   and its mask (`nowalk` 94, `walkmaskA` 37) and the footprints (`sizeone` 326) each separate. Not covered: the callers
   after the return (`PortalObjectCreate` 0x0056D218, "the open fails"). The bullet is the lane's draft text; the lane did
   not write it into the spec (it is the spec-writer's file). Then the spec's tag count and the research-map row move by
   the number of `[C]` statements the bullet adds.

**2026-11-16, spec-writer (`lane/n66qr`, plan 0066 Phase 3, quests cluster):** item 3 taken. quests/travel B1 now
holds the scope bullet `[C]` (ADR-0015, ADR-0029 (a)) on family `ffn` of run:2026-11-16-sweep2-s7e, 596 of 600 cases,
the 4 left out named; A5's step 5 and G2's walk back are `[C]` on the same family, G2's "the open fails" stays `[I]`
(the caller after the return). Items 1 (sim/frame D9/E1) and 2 (drlg/collision E4) are left open for the path/frame
cluster.
