---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/quests/0001-progression.md
  - ../../findings/quests/0002-travel.md
resolution: "Plan 0066 Phase 3 (lane/n66qr, 2026-11-16): word 32's game-record b13 write, e3's direct raiser in NpcActTravel, the operate wrapper 0x00584540, the travel check's act and position tests and A2Q6_WrongTombMsg written in. [quests/progression](../../specs/quests/progression.md#b-events-and-dispatch), [quests/travel](../../specs/quests/travel.md#d-waypoint-travel)"
---

Plan 0066 batch S3c part 1 (`lane/n66p`) found refinements and one correction for Phase 3, with the reverser's
records in [quests/0001 § 20](../../findings/quests/0001-progression.md#20-plan-0066-batch-s3c-part-1-second-tool-reference-argument-and-table-scans-2026-11-16-lanen66p)
and [quests/0002 § 17](../../findings/quests/0002-travel.md#17-plan-0066-batch-s3c-part-1-second-tool-reference-scans-2026-11-16-lanen66p).
Not blocking.

1. **Correction, quests/progression word 32** (line 1218 at `b5999f5e`, "Word 32 has one write through the record
   functions"): true of the player record; the game record's word 32 also gets b13 from `A3Q7_FirstJoin`'s
   `GameQuestSet(32, 13)` (0x005BD2EE) when the joining player's w32 b0 is set.
2. **Events table, e3** (line 201): a third raiser, `NpcActTravel`'s Warriv branch, calls quest object 6's `+0xAC`
   slot directly with event 3, level 40 (0x00546A22–0x00546AA3).
3. **travel § Entry points** (line 28): the case-2 chain has the operate wrapper 0x00584540 between `UnitInteract`
   and `OBJ_OperateDispatch` (also called by `MonAiOpenDoor`, 0x005B0FC1).
4. **travel D3** (line 375): the server's travel check also refuses when the operator's and the waypoint's rooms lie
   in different acts (0x005495BC) and tests the position (`PktPosFar`, 0x00549647); the target's act is not tested.
5. **progression word 14** (line 947): the act `+0x094` readers include `A2Q6_WrongTombMsg` (0x0059D731).
