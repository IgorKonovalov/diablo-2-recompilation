---
from: architect
to: reverser
date: 2026-10-30
status: done
context:
  - ../../findings/player/0001-creation.md#plan-0038-batch-h6g-run2026-10-27-sweep-player
  - ../../findings/player/0001-creation.md#plan-0038-batch-s3b-2026-10-16
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "Applied 2026-10-30 (lane/rfix) as dated notes in player/0001, no ledger or class change: (1) H6g rows 3/30 read five deaths, four cases (the Nightmare clamp case twice), DG0 5; (2) S3b row 21's [C] narrowed to the cell for classes 0..6, the column-0 clamp [I] (never reached, H1a rows 11/20/34); (3) Open questions annotated: the death loss and cap ran in H6g rows 3/30 and 28, class 7 in H1a row 11, client +0x3D4 bit 0 in H6g row 12 (raised in part); XP_PartyShare still not run. [player/0001 § S3b](../../findings/player/0001-creation.md#plan-0038-batch-s3b-2026-10-16)"
---

Filed at the lane/s38p Tier A review (2026-10-30). Three wording fixes in player/0001; no ledger or class change. (1) § Plan 0038 batch H6g, rows 3/30: the [C] bullet says "reproduced in four deaths on three difficulties", but the kept logs hold five deaths (deathn, deathh, the first deathnm log 6717 and the two deaths of r5); the gate's DG0 count is 5 and the static read says "all five deaths". Say five deaths, four cases (the Nightmare clamp case twice); player/creation J3 and its Entry points row now say five. (2) § Plan 0038 batch S3b, row 21: the [C] sentence includes "with c 0 for a class outside 0..6". That clamp is never reached (no class-7 player exists: the H1a ruling on rows 20 and 34), and EXP_LevelFromExp's "same clamp" is a second reading of the same pattern, not a case that runs the branch. Narrow the [C] to the cell for classes 0..6 and keep the column-0 clamp [I], as player/creation F2 does (the lane/s38p review's F2 ruling). (3) § Open questions: "Not run in Phase 2: ... PLAYER_DeathExpLoss, the experience cap, class 7" and "client +0x3D4 bit 0" are stale after H6g (rows 3/30, 28, 12) and H1a (row 11); annotate them with the batches that ran them.
