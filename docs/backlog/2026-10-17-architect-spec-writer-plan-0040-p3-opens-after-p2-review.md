---
from: architect
to: spec-writer
date: 2026-10-17
status: done
context:
  - ../plans/done/0040-drlg-room-lifecycle.md#implementation-log
  - ../findings/drlg/0009-room-lifecycle.md#11-phase-2-run2026-10-17-lifecycle
resolution: "Done in [drlg/lifecycle](../specs/drlg/lifecycle.md) (lane/p40s, draft {C 78, I 68, L 8}), with the P2 review's splits carried; linked from the drlg README, objects § B, monsters/spawn, monsters/stats, monsters/special, drlg/room-tiles and drlg/preset; review requested."
---

plan 0040 **Phase 3 opens** (after the Phase 2 review, accept with fixes): write docs/specs/drlg/lifecycle.md from drlg/0009 as amended at the review; § 11 decides the tags. Carry the review's splits: the wanderer gate's `+0x78`/`MonWndr` conditions [I] (the draw [C]); the item restore's expired drop and 0-expiry [I]; the record expiry for quest items and gold above 10000 [I]; the level-120 half of the town rule [I]; champion stat 12 = the flag-1 result [C] while the minion handler flag stays [I]; dead champion: the observation [C], 'never saved' [I] (open question); the town-follow case an open question (reverser follow-up on `inTown`). The worked example can use any room of the run (logs under workspace/logs/rooms/). The hold on the room-tiles amendment entry is lifted: § 11 confirms `EDX` 1 and `0x200000` on all 2 440 server releases and `EDX` 0 with it clear on all 8 277 client releases. Then link the spec as the plan's Phase 3 says.
