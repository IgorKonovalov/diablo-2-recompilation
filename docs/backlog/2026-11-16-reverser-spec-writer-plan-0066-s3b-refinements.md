---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context: [../plans/0066-simulation-inferred-claims-sweep.md, ../findings/quests/0001-progression.md]
resolution: ""
---

Plan 0066 batch S3b (`lane/n66p`) found no contradiction in quests/progression, and three refinements for Phase 3
(spec lines at `b5999f5e`; evidence in [quests/0001 § 19](../findings/quests/0001-progression.md#19-plan-0066-batch-s3b-kill-step-and-service-step-rules-over-the-kept-questsgdb-logs-2026-11-16-lanen66p)):

1. **Radament's credit sites (line 769, inventory row 128).** The row gives 0x00598D96, 0x00598DA0, 0x00598DAA, which are
   `sub_00598D40_A2Q1_PartyCredit`'s. The near credit's own writes are at 0x00598F10, 0x00598F1F, 0x00598F29 in
   `sub_00598E20_A2Q1_NearCredit` (logged in 4904-radament4, run:2026-10-27-sweep-quest-items). List both triples.
2. **Andariel's level-37 pass (line 696, row 117).** Every credited kill wrote b13, b1 twice: the killer, then
   `CreditInLevel` (0x00596302) on the same player with b1 already set. The level pass tests b0 and b15, not b1, so a
   player credited as the killer is written again; the text may say so.
3. **Site owners (lines 768 and 1333, rows 127 and 252).** The A2Q1 StepBits sites 0x00598A2D/49/5A lie in
   `sub_00598910_A2Q1_NpcGate`, and the A4Q3 ones 0x005B6016/27/3D in `sub_005B5EE0_A4Q3_NpcGate` (the row anchors name
   0x005989E0 and `sub_005B59C0_A4Q3_StepBits`).

Not blocking.
