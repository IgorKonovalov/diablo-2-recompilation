---
from: architect
to: reverser
date: 2026-10-27
status: open
context:
  - ../findings/objects/0001-object-population.md#h5b2-population-clusters-caps-themes-and-orientation-rows-3-13-1517-19-20-50-51
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

Wording fix in objects/0001 § H5b.2 (the `lane/s38o` review, plan 0038 Phase 3, ruling 1). The shrine-cap bullet says the cap "returned before any draw of the handler". `OBJPOP_Shrine` makes its `P100` draw on the room seed (0x00552B9A–0x00552BBA) before `HealthShrineDue` (0x00552BC5) and the cap test (0x00552BF7), and `tools/objects.py` `pop_2` models that draw before the cap. So the seeds that matched after the two cap returns confirm one room draw, then the return before any placement draw. Reword the bullet to "before any placement draw (after the handler's `P100(S)` draw)". objects/README E2 and *Constants* already say this. No tag changes.
