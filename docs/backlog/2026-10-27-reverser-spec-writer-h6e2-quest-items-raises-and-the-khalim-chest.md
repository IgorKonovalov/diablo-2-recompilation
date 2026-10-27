---
from: reverser
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/items/0010-quest-drops.md#plan-0038-batch-h6e2-run2026-10-27-sweep-quest-items
resolution: ""
---

**Released by the `lane/h6e2` review (2026-10-27, accept with fixes; plan 0038 log).** Phase 3 re-tag input for items/quest-drops and objects from plan 0038 batch
H6e2 (run:2026-10-27-sweep-quest-items): the statements raised and raised in part are listed in the inventory § 2.6
H6e2 block and in items/0010's H6e2 ledger table. For a raised-in-part row only the half marked `[C]` there moves.

Points beyond a tag change:
- items/quest-drops § E, E1 (and objects § L's chests row): the three Khalim chests draw `QuestPick(5)` and the gold
  piles **first**, then their part (per player holding neither the part nor `qf2`), then `ObjectChestDrop`; E1's
  order (items, chest drop, gold) holds for `tr1`, `msf`, `box` and the altar. `[C]` for the heart chest; the eye and
  brain chests stay `[I]` on the same reading.
- items/quest-drops § E table, `qhr`/`qey`/`qbr` gate: "per player" becomes "per player holding neither the part nor
  `qf2`" (`[I]`, read; the passing case met on `qhr`).
- items/quest-drops § Entry points, the object-event-7 row: the logged chain (`GameRunUnitEvents` →
  `ObjEventsRun` → `OBJ_EventDispatch` entry 7 → the `jmp` thunk → `QUESTS_ObjectEvent` → the class target) for
  classes 268 and 367; the other classes stay `[I]`.
- The quality column: `ass` and `bks` join `j34` and `mss` as asked quality 2, created 7 (the base `unique` override,
  `[I]`; *review fix*: the lane had `bks` at 2). The column is the asked quality; a base with `unique` 1 comes back 7.
- Wirt's gold: in items/quest-drops § E already `[C]` (plan 0043), add run:2026-10-27-sweep-quest-items as a second
  anchor (18 piles on another seed), no tag change; objects § L's Wirt's body row is `[I]` there and is raised here. The objects cluster is ready for its Phase 3 re-tag with this entry.

*Annotation (spec-writer, 2026-10-27, `lane/s38o`, plan 0038 Phase 3, objects cluster):* **the objects parts are done.**
[objects § L](../specs/objects/README.md#l-quest-objects-the-hellforge-and-the-quest-item-objects-named-only): the chests
row is split in two. The Act II chests (`tr1`, `msf`, `box`) are `[C]` in E1's order (item, chest drop, gold), with the
held cube refusing `box`; the altar stays `[I]`. The Khalim chests' row states the corrected order (quest seed and gold
first, then the part per player holding neither the part nor `qf2`, then the chest drop), `[C]` on the heart chest; the
eye and brain chests and the held-part refusal stay `[I]`. Wirt's body row is `[C]` (slot 33, the leg on the unchanged
quest seed, 18 event-7 piles, `RandLoHi` = 18 on the logged seed). The item-objects row is `[C]` for `leg` and `bks`
(`bks` asked at quality 2, created at 7; the base `unique` override and `hdm`, `bbb` stay `[I]`). The orifice row is `[C]`
for the word-10 bits (the kept Duriel log), `[I]` for the `hst` gate. § K adds the event-7 route `[C]` for classes 268
and 367. All anchored to run:2026-10-27-sweep-quest-items. **Still open:** every items/quest-drops part (§ E, E1, the
gate wording, § Entry points, the quality column, Wirt's gold anchor), which waits for H6e1; wiki/items-other-paths'
quest-chest sentence (its "quest item, then chest drop, then gold" is quest-drops' E1 and moves with that round).
