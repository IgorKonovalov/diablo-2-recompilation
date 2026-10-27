---
from: architect
to: reverser
date: 2026-10-27
status: open
context:
  - ../findings/drlg/experiments.md#run2026-10-27-sweep-collision
  - ../findings/quests/0002-travel.md
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: ""
---

From the lane/h5d review (plan 0038 H5d, 2026-10-27). `tools/collision.py check` (through `tools/objects.py`) reports one operate mismatch on the kept log `workspace/logs/h5d/run-2026-10-27-h5d-s1-4106-rogue.log` (hashed in `h5d-manifest.sha256`): the Rogue Encampment waypoint (class 119, unit 54452480) is created in mode 1 (`OIX` at line 3225, the arrival by waypoint: `OBJINIT_Waypoint`'s arrival-list match, quests/0002 § WaypointOperate) and is in mode 2 at its one operate (`OO0`/`OOX` at lines 4769–4770, `wpchain`); the model keeps mode 1 and no logged line moves it. Lead: the object event 1 that `OBJINIT_Waypoint` and `WaypointOperate` queue (at frame + Objects `+0xDC` >> 8) sets mode 2; quests/0002 says only that the event is queued. (a) Read what event 1 does to a waypoint (and whether it draws on a `Sync` 0 row's unit seed, 429, 494, 496, 511, 539); (b) log or model the mode change in `objects.py` so a second-hop session's check is clean; (c) if a quests/travel or objects claim is contradicted, route it to the spec-writer. Not on a row of plan 0038 H5d; not blocking. A static lane (plan 0051 or later) may take (a); (b) needs no slot.
