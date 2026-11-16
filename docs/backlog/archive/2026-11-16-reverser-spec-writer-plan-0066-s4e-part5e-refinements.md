---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/items/0013-grids-belts-stacks.md
  - ../../findings/stats/0001-aggregate.md
  - ../../findings/stats/0002-states.md
resolution: "Applied in plan 0066 Phase 3, the stats/items cluster (lane/n66si): item 1 in items/inventory, items 2–4 in stats/aggregate H3 and stats/states B2 [log](../../plans/0066-simulation-inferred-claims-sweep.md)"
---

Plan 0066 batch S4e part 5e (`lane/n66z`) raised or refined these spec statements. Not blocking. Re-tag when the
inventory rows are accepted at the batch's Tier B review; the evidence is in the findings named.

1. **items/inventory I6** (`ItemAutoEquipSlot`) with `skipReq` 0: `[C]` (ADR-0015) per
   [items/0013 § 18](../../findings/items/0013-grids-belts-stacks.md#18-plan-0066-batch-s4e-part-5e-itemautoequipslot-through-itemreqcheck-run2026-11-16-sweep2-s4e-emu):
   a failed `ItemReqCheck` gives 0 with the location untouched; a passed one runs the same four tests, then the
   location code. With part 5d's entry, all of I6 is `[C]`.
2. **stats/aggregate H3** (`ItemReqCheck`), evidence beside the H4e run of stats/aggregate row 27 (no class move
   there): under emulation, on the path `ItemAutoEquipSlot` takes (third argument 0) and the quality-default level
   path, the stat-91 percent term, the level test (`max(0, Items +0x13F + the item's stat 92)`), the type-18 test,
   the class test and the monster 560/561 test each decided cases (items/0013 § 18). The step note's "values the check
   reads through `0x0062B450`" applies only when the third argument is non-zero; with 0 neither `0x00625820` nor
   `0x0062B450` is called.
3. **stats/aggregate G3** (the event registration): `[C]` (ADR-0015, ADR-0021) per
   [stats/0001 § 13](../../findings/stats/0001-aggregate.md#13-plan-0066-batch-s4e-part-5e-the-stat-event-list-under-emulation-run2026-11-16-sweep2-s4e-emu):
   0x005C0BE0 finds the first node of the unit's `+0x90` list with kind, stat and `+0x0C` equal; 0x005C0B50 marks a
   matching node in use (word `+0x02` bit 0) with bit 1 and unlinks and frees one not in use; `AddStatEvent` refuses
   a `func` above 0x31 or with a null `g_StatEventFuncs` entry. `[I]` (one reading): the node is keyed by kind 2 and
   the stat at both `+0x08` and `+0x0C`, so a found node blocks both `itemevent1` and `itemevent2`, and a fourth
   argument of 0 frees every kind-2 node of the stat not in use.
4. **stats/states B2** ("poison, burn, cold and freeze use their own appliers with the same list shape"): `[C]`
   (static, objdump pins and call scans) per
   [stats/0002 § 12](../../findings/stats/0002-states.md#12-plan-0066-batch-s4e-part-5e-the-elemental-appliers-lists-run2026-11-16-sweep2-s4e-emu-static),
   with a refinement: the remove callbacks differ (poison and burn 0x0056E900, cold 0x0057AD80, freeze 0x0057B170).
   combat/delivery D2–D4 may name the states (2, 115, 11, 1) and the shape there too.
