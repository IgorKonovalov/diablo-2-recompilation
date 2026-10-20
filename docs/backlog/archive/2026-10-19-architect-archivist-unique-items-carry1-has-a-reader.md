---
from: architect
to: archivist
date: 2026-10-19
status: done
context:
  - ../../tables/UniqueItems.md
  - ../../findings/items/0011-economy.md#phase-2b-runtime-results-run2026-10-19-economy2
resolution: "Plan 0049 P0 (lane/p49a): [UniqueItems.md](../../tables/UniqueItems.md#semantics-from-the-unique-builder-plan-0019-phase-1) cites two carry1 readers (sub_0055CA40_InvHoldsQuestDup via the item-move gate, items/0010 Q20; sub_00575FA0_ItemIsCarry1Unique in NPC_SellItem, items/0011 P2b item 8, Annihilus at runtime); the open question narrowed to lvl req and a full xref of 0x006CE270."
---

UniqueItems.md's open question "whether any code outside the unique builder reads `carry1` or `lvl req`" (`[L]`) and the `[I]` row "not read by the builders" can now cite a reader: `sub_00575FA0_ItemIsCarry1Unique` (0x00575FA0) tests the record's `+0x2C` AND the byte at 0x006CE270 (4, bit 2) for a quality-7 item, and `NPC_SellItem` uses it to refuse the store copy (0x005796E6); a `carry1` unique (Annihilus) was refused at runtime (items/0011 § Phase 2b item 8, run:2026-10-19-economy2). Update the column's semantics and the open question (`lvl req` remains). Not blocking.
