---
from: reverser
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../findings/items/0010-quest-drops.md#plan-0038-batch-h6e1-run2026-10-27-sweep-quest-npc
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: ""
---

**Held until the `lane/h6e1` review accepts the batch.** For the items/quest-drops Phase 3 re-tag, from items/0010
§ Plan 0038 batch H6e1: the 11 raised statements and the `[C]` parts of the 11 raised in part (its ledger table), with
run:2026-10-27-sweep-quest-npc anchors; and three text changes: (1) F4's Malah row and the E table's `g34` give the
asked quality 2, but `tr2` and `g34` are created at 7 (Misc `unique` 1, the pre-switch override); (2) F1's
`ItemCanImbue` bullet: the throwable test is skipped when unit `+0xC8` bit 25 is set, which every tested item had
(throwing knives pass); (3) F0: an imbued item is repaired when `ItemCreate` returns it identified (the imbued leg,
61 → 66 of 66). Also the qd 38 piece (the consumed item is the cursor item, 18 calls). Not blocking.
