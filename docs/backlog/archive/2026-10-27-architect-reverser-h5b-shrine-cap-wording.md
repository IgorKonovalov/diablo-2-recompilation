---
from: architect
to: reverser
date: 2026-10-27
status: done
context:
  - ../../findings/objects/0001-object-population.md#h5b2-population-clusters-caps-themes-and-orientation-rows-3-13-1517-19-20-50-51
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "objects/0001 § H5b.2's shrine-cap bullet reworded to \"before any placement draw (after the handler's `P100(S)` draw)\", with a dated correction anchored at 0x00552B9A–0x00552BBA (seed step), 0x00552BC5 (HealthShrineDue) and 0x00552BF7 (cap call), objdump-checked; no other finding repeats it; no tag changes [objects/0001](../../findings/objects/0001-object-population.md#h5b2-population-clusters-caps-themes-and-orientation-rows-3-13-1517-19-20-50-51)"
---

Wording fix in objects/0001 § H5b.2 (the `lane/s38o` review, plan 0038 Phase 3, ruling 1). The shrine-cap bullet says the cap "returned before any draw of the handler". `OBJPOP_Shrine` makes its `P100` draw on the room seed (0x00552B9A–0x00552BBA) before `HealthShrineDue` (0x00552BC5) and the cap test (0x00552BF7), and `tools/objects.py` `pop_2` models that draw before the cap. So the seeds that matched after the two cap returns confirm one room draw, then the return before any placement draw. Reword the bullet to "before any placement draw (after the handler's `P100(S)` draw)". objects/README E2 and *Constants* already say this. No tag changes.
