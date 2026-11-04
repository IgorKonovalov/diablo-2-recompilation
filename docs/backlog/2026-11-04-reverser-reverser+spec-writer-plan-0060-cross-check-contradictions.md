---
from: reverser
to: reverser, spec-writer
date: 2026-11-04
status: open
context:
  - ../plans/0060-item-use-inventory.md
  - ../findings/items/0017-community-cross-check.md
  - ../specs/items/use.md
  - ../specs/items/inventory.md
resolution: ""
---

From the `lane/r60d` cross-check ([items/0017](../findings/items/0017-community-cross-check.md)), rewritten at its review, 2026-11-04. Verdict ids are the finding's. No tag moved on any of this. **Nothing here blocks plan 0060's close:** every `contradicted` verdict is resolved or under its spec's Open questions.

**Contradictions, each with its state:** H1, B7 and T2 resolved by the record, no action; B3 resolved for 1.14d, noted in items/inventory § Open questions; H3 open, below. H2 and B8 are no longer contradictions or gaps (`held with refinement`).

**To reverser, for a third harness run if the owner schedules one (not scheduled; within plan 0060). Stock data, one lane:**

1. **H3, a mana potion to the hireling.** `0x26` with the flag, a hireling alive, an expansion game, for `mp1`, `hp1`, `rvs`, `yps`, `wms`; and `0x61` for the same rows on the cursor. Log `ITEMS_UnitIsType`'s three results and whether `ItemUse` is reached with the hireling as user. A wrong reading would show `mp1` reaching `ItemUse`. The client sends the flag first (0x00498B4F), so a stock shift-click should reach it with no forced field.
2. **H2, the blend live.** A pair of **different tiers**, the meter below its maximum at both uses (a pair of equal tiers cannot separate the blend from `v ÷ len`): the list `UNIT_FindStatListByState` returns, the rates set, and the frame the list is freed at the maximum.
3. **B8, a death with a belt.** A worn belt holding boxes above 3, inventory room and no room: where each item goes.

**To reverser, next static lane:**

4. Name the function at `0x0057F410` in `re/symbols.csv` (the corpse's move of a body item, between `CorpseDropGold` and `CorpseOverflowDrop`).

**Done at the review, nothing left for the spec-writer:** items/use F1f, D3's comment and § Open questions (H2, H3, P3); items/inventory F6 and § Open questions (B3, B8).

If the owner declines the run, close this entry at plan 0060's close once 4 has a home: the cases stay named in the specs' Open questions.
