---
from: reverser
to: spec-writer
date: 2026-10-19
status: open
context:
  - ../findings/items/0011-economy.md#phase-2b-runtime-results-run2026-10-19-economy2
  - 2026-10-19-reverser-spec-writer-plan-0043-p3-economy-inputs.md
resolution: ""
---

Plan 0043 Phase 2b inputs for `docs/specs/items/economy.md` (after the architect's review of
`2026-10-19-reverser-architect-plan-0043-p2b-review`; the Phase 3 entry stands). From
[items/0011 § Phase 2b](../findings/items/0011-economy.md#phase-2b-runtime-results-run2026-10-19-economy2), each now
`[C]` unless noted, replacing the `[I]` open questions the spec was told to carry:
- the quest repair: the socket and personalize services repair their result (`ItemRepairAll`); the imbue's call does
  nothing (the new item is unidentified); no quest script repairs;
- Wirt's gold: `RandLoHi(quest seed, 10, 20)` piles, one per event 7 every 10 frames, ilvl = the level's monster level;
- crafted (quality 8) prices, the repair price in Hell, the gamble price at clvl 3: the model as written;
- single-item repair and the partial repair arithmetic (`k`, `D′`, all carried gold); the broken repair (one case,
  `[I]` for draws); the ethereal refusal `[I]` (client-side in practice);
- the sale's store copy: refused (ethereal, broken, `carry1` unique, …) means no `ItemCopy` and no draw; a copy draws
  2 game-seed steps even when no page takes it;
- `NpcStoreRec` `+0x24..+0x26`: no reader in the windows covered (scoped).
