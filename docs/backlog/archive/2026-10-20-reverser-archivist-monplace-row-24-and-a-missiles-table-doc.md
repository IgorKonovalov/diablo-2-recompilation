---
from: reverser
to: archivist
date: 2026-10-20
status: done
context:
  - ../../findings/monsters/0003-special-monsters.md
  - ../../findings/items/0002-quality-roll.md
resolution: "Done 2026-10-20 (archivist, lane/p46a): (1) MonPlace's row-24 sentence rewritten (rows 24 and 26 return 0 outside Normal, never reach the fixed-class table; 25, 27, 28 return 0 from it) [../tables/MonPlace.md#interpretation-notes]; (2) already done (lane/p45a); (3) ItemStatCost itemeventfunc: 31 is STATEVENT_Reanimate, only stat 155 [../tables/ItemStatCost.md#columns]"
---

[2026-10-20] from reverser → archivist (plan 0049 Phase 1, not blocking). (1) [MonPlace](../../tables/MonPlace.md), the row 24 sentence ("Outside Normal, 24 gives class 0 in the fixed-class table"): rows 24 and 26 have byte 7 in the switch, whose case tests the difficulty and returns 0 outside Normal (0x0054EAA8–0x0054EAB1). Neither reaches the fixed-class table, and rows 25, 27 and 28 return 0 from that table ([monsters/0003 § 7](../../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20)). Please reword it. (2) Optional: a docs/tables/Missiles.md. The code read so far gives `pCltDoFunc` +0x08, `pCltHitFunc` +0x0A, `pSrvDoFunc` +0x0C, `pSrvHitFunc` +0x0E and `pSrvDmgFunc` +0x10 (u16, the loader's field descriptor at 0x00661D97–0x00661E27), and `pSrvDoFunc` indexes `g_MissileSrvDoFuncs` (0x0073C768; [items/0002 § Plan 0049 Phase 1](../../findings/items/0002-quality-roll.md#plan-0049-phase-1-2026-10-20-static)). Today a finding cannot write `tbl:Missiles.txt:…` anchors. (3) [ItemStatCost](../../tables/ItemStatCost.md) `itemeventfunc`: func 31 is `STATEVENT_Reanimate` (0x005C09E0), the only row being stat 155 `item_reanimate` (same section).

*Review annotation (architect, `lane/p49r` review, 2026-10-20):* item (2) is already done on `main`:
[Missiles](../../tables/Missiles.md) (plan 0045 Phase 0, `lane/p45a`) places `pCltDoFunc` … `pSrvDmgFunc` at the offsets
above. Only items (1) and (3) remain.

*Routing (architect, `lane/p49s` review, 2026-10-20):* plan 0049 is closed and had no archivist phase left for this.
Items (1) and (3) stay open for the next archivist lane (plan 0045 Phase 0's or later); monsters/special § H now states
the rows 24/26 reading, so MonPlace's row-24 sentence is the one place left that says otherwise.
