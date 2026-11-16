---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../specs/sim/frame.md
  - ../specs/drlg/collision.md
  - ../plans/0066-simulation-inferred-claims-sweep.md#implementation-log
resolution: ""
---

Plan 0066 batch S7e part 2 (`lane/n66u`, [run:2026-11-16-sweep2-s7e](../findings/frame/experiments.md#run2026-11-16-sweep2-s7e))
found two readings the specs do not state. Not blocking. Both are maps of the code under emulation; what the game does at the
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
