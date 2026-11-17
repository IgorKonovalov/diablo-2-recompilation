---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/quests/0001-progression.md
  - ../../findings/quests/0002-travel.md
resolution: "Plan 0066 Phase 3 (lane/n66qr, 2026-11-16): A6's read side (QUESTS_SendGameRecord's SaveBytes, the callbacks never reading it) written in; travel C3's 'draws again' was already removed by plan 0063 Phase 3, the table half raised. [quests/progression](../../specs/quests/progression.md#a-the-quest-record)"
---

Plan 0066 batch S3c part 2 (`lane/n66p`) found one refinement and carried one earlier correction to the spec, for
Phase 3. The reverser's records are
[quests/0001 § 21](../../findings/quests/0001-progression.md#21-plan-0066-batch-s3c-part-2-the-game-records-data-flow-the-placement-scans-with-a-second-parser-2026-11-16-lanen66p)
and [quests/0002 § 18](../../findings/quests/0002-travel.md#18-plan-0066-batch-s3c-part-2-the-travel-tables-and-the-field-centre-2026-11-16-lanen66p).
Not blocking.

1. **quests/progression A6, the read side.** The game record is "read through `GameQuestGet`". `QUESTS_SendGameRecord`
   also reads it whole: it serialises it with `QUESTRECORD_SaveBytes` at 0x0054456E. The quest objects' log-state
   callbacks (`+0xE8`) get it as stack argument 1 and never read it. The write side ("only through `GameQuestSet` and
   the join") held.
2. **quests/travel C3, the mode 1 → 2 change.** "Its later change to mode 2 draws again" is superseded by
   quests/0002 § 15 (plan 0063 Phase 2b). Event 1 (`sub_00581490_ObjEvOperateEnd`) writes mode 2 directly
   (0x005814B0), not through `UNIT_SetMode`, so that change makes no draw. The table half of C3 (the five `Sync` 0
   rows, `FrameDelta` 200/100) held over all 16 waypoint rows. The draw at a mode-0 operate stays `[I]` (a-run, H3e).
