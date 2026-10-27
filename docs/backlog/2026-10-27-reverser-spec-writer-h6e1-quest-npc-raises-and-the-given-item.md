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

**Released by the `lane/h6e1` review (2026-10-27, accept with fixes; plan 0038 log).** Phase 3 re-tag input for
items/quest-drops from plan 0038 batch H6e1 (run:2026-10-27-sweep-quest-npc). The 11 raised statements and the `[C]`
parts of the 11 raised in part are in items/0010's H6e1 ledger table and the inventory § 2.6 H6e1 block. For a row
raised in part, only the half marked `[C]` there moves. qd 38 (S2c) is now **raised**: the consumed item is the cursor
item, 18 calls.

Points beyond a tag change:
- F4's Malah row and the E table's `g34` row: the asked quality is 2, but `tr2` and `g34` are created at 7 (Misc
  `unique` 1, the pre-switch override; `xyz`, a `ques` item with `unique` 0, keeps 2). `[C]`.
- F1's `ItemCanImbue` bullet: the throwable test is skipped when unit `+0xC8` bit 25 is set. Every tested item had that
  bit set, and throwing knives passed the test. `[C]` for the skip; what sets the bit is an open question.
- F0, and the Outputs line "the imbued item is not (F0)": an imbued item is repaired when `ItemCreate` returns it
  identified. `[C]`: the leg went 61 → 66 of 66 (this run), and the unidentified `cap` kept 10 of 12
  (run:2026-10-19-economy2). The gate is `sub_0062E660_ItemCanRepair` (0x005761CB), which also refuses an ethereal
  item. That ethereal half is `[I]`: this run's ethereal `cap` was also unidentified, and at full durability (review
  fix). items/economy F7 states the imbue case as if the new rare were always unidentified. It needs the same
  qualifier (see the items/0011 note).
- Malah's `ice` stays `[I]` (qd 32 and 46): the potion is offered only in quest state 4, which no run reached. Her talk
  table at 0x00589B9C is the reading. Open question: what sets state 4.
- `QUESTS_GiveItem` and the five NPC message handlers, the three service tests, `CursorItemConsume`, `ItemRepairAll`
  and `ItemIdentifyAttach` are `[C]` symbols now. Use them as the anchors.

With this entry and H6e2's, every items/quest-drops batch (S2c, H6d, H6e2, H6e1) is accepted, so the spec is ready for
its Phase 3 re-tag.
