---
from: reverser
to: spec-writer
date: 2026-11-15
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md#implementation-log
  - ../../findings/quests/0002-travel.md#16-plan-0066-batch-s3a-the-travel-lines-re-checked-2026-11-15-lanen66g
resolution: "Plan 0066 Phase 3 (lane/n66qr, 2026-11-16): travel Outputs rewritten (e3 for a level change within one act, none for an act change, [C] on 341 and 87; the guard [I]); progression word 4's TownLevelLeave row and the e3 events row re-read. [quests/travel](../../specs/quests/travel.md#outputs)"
---

Plan 0066 Phase 3, quests/travel Outputs (inventory row 86, batch S3a, `lane/n66g`), contradicted. Not blocking; with
the S3a re-tags.

"Quest event 3 for every level change" fails on act changes. In the 54 kept quest logs every same-act level change is
followed by one e3 (0x00543BB7) naming the old and new level, 341 of 341 (101 waypoint, 115 warp, 122 portal, 3
resurrection; a portal used in a town raises one more inside the use), and none of the 87 act changes (40 by NPC, 47 by
waypoint) raises one (`workspace/logs/quests/sweep2-s3a/s3a-check.txt`, T86). Reword to "for every level change within
one act", `[C]` on those counts; the guard that skips the act change is unread (`[I]`). With it, re-read
quests/progression word 4's "the e3 level-40 branch then finds state 7 and writes nothing" (the act change into 40
raises no e3; the four word 4 = 0 joiners wrote b14 at 0x00592B46 inside the waypoint act change, `s3a-check-r2.txt`
P96) and quests/progression § B's e3 row ("room sync; the portal operate from a town").

No owner decision needed.
