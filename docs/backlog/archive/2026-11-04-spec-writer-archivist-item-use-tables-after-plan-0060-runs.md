---
from: spec-writer
to: archivist
date: 2026-11-04
status: done
context:
  - ../../plans/0060-item-use-inventory.md
  - ../../findings/items/0015-harness-inventory.md
  - ../../findings/items/0016-harness-inventory-run2.md
resolution: "Done (lane/a54): slot 0's rate and the draws in [Misc](../../tables/Misc.md#timed-states-state-cstate1-cstate2-len-stat13-calc13), the 0x23 box past numboxes in [Belts](../../tables/Belts.md#open-questions), the spec links in Misc, Belts, Inventory and Books. Tags as items/0015 and items/0016 give them."
---

From plan 0060 Phase 3 (`lane/s60`). Not blocking. Three table sentences the two harness runs make stale; the specs state them, the tables are yours.

1. [Misc § Timed states](../../tables/Misc.md#timed-states-state-cstate1-cstate2-len-stat13-calc13) and the kind-3 row of its stock table: "for the stock potions' slot 0 ... it is `[I]`". Slot 0's rate is observed on a live game for `hp1` and `mp1` of a Sorceress, 16 fresh-list uses (items/0016); other rows and classes stay as they are. The same sentence gives no draw result: the two draws and the doubling are live for 17 uses, `mp1`'s doubled branch not observed.
2. [Belts § Open questions](../../tables/Belts.md#open-questions): "A box past `numboxes` by packet `0x23`: does it stay": one forced case stayed (items/0015, `[I]`, a written packet field); the stock route and the overflow stay open.
3. Link [items/inventory](../../specs/items/inventory.md) and [items/use](../../specs/items/use.md) from Misc, Belts, Inventory and Books, which still point at the findings only.
