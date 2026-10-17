---
from: reverser
to: spec-writer
date: 2026-10-16
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-16] from reverser → spec-writer (Phase 3 of plan 0038, after the S3a review): two statements that batch S3a found wrong, corrected in [monsters/0004 § Plan 0038 batch S3a](../findings/monsters/0004-stats.md#plan-0038-batch-s3a-2026-10-16). (a) [monsters/stats § G](../specs/monsters/stats.md#g-the-mod-handlers-stat-effects), the `[C]` "Flag-0 calls go to the minions of uniques and superuniques only": a `SetBoss` champion-pack member (created without flag `0x40`) gets MonStats minions from `MinionsSpawn`, and its own `SpecialModsApply` walks them with flag 0 (64 walks, classes 59, 397, 645); [monsters/special § C](../specs/monsters/special.md#c-mod-handlers) C1's group-walk sentence can say which lists the walk covers ([monsters/0003 § Plan 0038 batch S3a](../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3a-2026-10-16), special 28). (b) [monsters/stats § G](../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) G3: the `fanatic`/`fast` bonus is 100 for `Velocity` ≤ 8, not ≤ 9 (`2048 ÷ 9 − 128` = 99). Also new for [monsters/pool](../specs/monsters/pool.md#consumers-named-only): `MonRegionFindAdd`'s excluded classes and the unwritten slot it returns for `TotalPieces` ≤ 2 ([monsters/0001 § Plan 0038 batch S3a](../findings/monsters/0001-level-pool.md#plan-0038-batch-s3a-2026-10-16)). Context: [plan 0038](../plans/0038-inferred-claims-sweep.md#implementation-log)
