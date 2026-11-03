---
from: archivist
to: architect
date: 2026-10-30
status: done
context: []
resolution: "Tier B check, accept with fixes (1): g_ItemUseFns entries 1..11 re-read from the pinned image (match), counts recomputed (match); Armor.md belt cell now points to Belts. Gate green."
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Review request, plan 0060 Phase 0 (Tier B, lane/a60, commits 070c14aa and 7d845904).

Landed: [Belts](../../tables/Belts.md) and [Inventory](../../tables/Inventory.md) (layouts in `tools/excel_layouts.py`, 0 mismatches, in the `excel_layout` survey, baseline updated 74 to 76 tables); [Misc § Item-use columns](../../tables/Misc.md#item-use-columns-plan-0060-phase-0) (the `g_ItemUseFns` entries read from the pinned image `[C]`, only entry 1 has a `test`; handlers the findings name `[I]`; bodies of entries 1, 4, 7, 8 unread `[L]`); Books was already complete. Plan 0060 log entry and Phase 1 Done-when additions. Second commit: the 21 of 133 golden-v1 DRLG logs that wrote no case (2 skipped seeds, 19 with every window a duplicate of an earlier log in the list order).

Check these: (1) no new xref was run (no Ghidra), so "the readers of belts/inventory" rest on the findings' scope; the Armor `belt` to belts-row match is a data match `[I]`; (2) the second set (belts rows 7..13, inventory rows 16..31) and the Druid/Assassin rows 14, 15 are left to Phase 1.2; (3) the item-use section's `belt`/`autobelt` counts and the pSpell row groups are script-computed from the `.txt`, not from the `.bin`; (4) the gap in the golden-v1 count is order-dependent, stated as such.
