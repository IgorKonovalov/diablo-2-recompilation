---
from: reverser
to: archivist
date: 2026-10-17
status: done
context:
  - ../findings/stats/0001-aggregate.md#phase-0-surprises
  - ../tables/Sets.md#bonus-blocks-plan-0041-phase-0
resolution: "Done: excel_bin.py names= params follow the PropParamCell order (atol, then skills → montype → states, 0 unmatched) for Sets, SetItems and Runes; Known limit dropped in [Sets § Bonus blocks](../tables/Sets.md#bonus-blocks-plan-0041-phase-0); excel_layout baseline unchanged."
---

plan 0041 P1 review follow-up (e), answered in [stats/0001 § Phase 0 surprises](../findings/stats/0001-aggregate.md#phase-0-surprises) (`[I]`, code reading): the Sets compiler resolves a bonus param name by a **fixed table order, not by the block's property**. All 16 `PParam`/`FParam` fields (and SetItems `par1..9`, `apar1a..5b`, Runes `T1Param`) use the type 0x19 callback `sub_006336A0_PropParamCell`: a cell starting with `-` or a digit is `atol`; else the first `EXCEL_FindName` hit in `skills`, then `montype`, then `states` (case-insensitive); a blank cell or no hit stores 0. Request: make `excel_bin.py`'s Sets (and SetItems) param lookup follow that rule (`names="skills:skill|montype:<name column>|states:state"`, plus the 0 default for an unmatched name), drop the *Known limit* paragraph of [Sets § Bonus blocks](../tables/Sets.md#bonus-blocks-plan-0041-phase-0) and cite the finding. On stock data the bytes do not change (none of the ten named cells is a montype name).
