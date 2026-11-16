---
from: reverser
to: spec-writer
date: 2026-11-15
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md#implementation-log
  - ../../findings/quests/0001-progression.md#18-plan-0066-batch-s3a-the-kept-quest-logs-re-checked-2026-11-15-lanen66g
  - ../../findings/quests/experiments.md#addendum-2026-11-15-plan-0066-batch-s3a-the-kept-quest-logs-re-checked-lanen66g
resolution: "Plan 0066 Phase 3 (lane/n66qr, 2026-11-16): C4 rewritten per quest (quests 13 and 19 [C], the maps as read [I]); word 37's rows left [I] as the item says; row 196's party gate and row 16's ClearSteps words written in. [quests/progression](../../specs/quests/progression.md#c-the-join-and-the-game-creators-history)"
---

Plan 0066 Phase 3, quests/progression (batch S3a, `lane/n66g`). Not blocking; with the S3a re-tags.

1. **C4 (inventory row 49), contradicted.** The FirstJoin restore is per quest, not C4's one map. Quest 13 (word 14)
   restores b3 as `+0x0B` = 5 (x-talk2) and quest 19 (word 21) does not restore on b4 (x-talk3, x-talk3b, h-talk3:
   `+0x0B` = 0): the 4 `MISMATCH` lines of `workspace/logs/quests/sweep2-s3a/s3a-check.txt` (P49). As read:
   quest 13 maps b2 → (`+0x0B`, `+0x0C`) = (1, 2), b3 → (5, 5), b4 → (6, 5) (0x0059D557–0x0059D5A3); quest 19 has no b4
   branch (0x005BB4BC–0x005BB4C9). Rewrite C4 as "per quest" with these two maps; the other quests' maps stay `[I]`
   until read (S3c).
2. **Word 37's entry levels (rows 270, 272), not a contradiction (n66g check).** The code tests 113 or 114 for b3
   (0x00589DAB–0x00589DB3) and 121 to 124 for b14 (0x00589EBB–0x00589EC4, `level − 121 ≤ 3` unsigned), which agree with
   the spec's "entering 114" and "entering 121, 122 or 124" rows; the logged 113 and 123 are the spec's own `[C]` rows.
   Nothing to re-tag; the rows stay `[I]` until an entry into 114, 121, 122 and 124 is logged (H3a).
3. **Refinements, not contradictions:** the Khalim items line (row 196): the operate removes the operator's `qf2 `
   itself (0x005BBA1E–0x005BBA23) and runs the party pass only for a player in a party (`UnitPartyId` ≠ 0xFFFF,
   0x005BBB30–0x005BBB49); "`ClearSteps` at most rewards" (row 16): name words 1, 20, 25, 35 (called) and 2, 4, 6, 9,
   27, 37 (not called).

No owner decision needed.
