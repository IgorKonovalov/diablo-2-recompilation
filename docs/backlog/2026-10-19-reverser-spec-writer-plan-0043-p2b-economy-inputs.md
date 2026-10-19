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
- the quest repair: the socket and personalize services repair their result (`ItemRepairAll`; durability restored,
  one case each); the imbue's call does nothing (the new item is unidentified, `ItemCanRepair` needs flag `0x10`; one
  case); "no quest script repairs" is `[I]` (a call-site scan, no second source);
- Wirt's gold: `RandLoHi(quest seed, 10, 20)` piles (10..19), one per event 7 every 10 frames, ilvl = `LevelMonLvl` of
  the body's level (one game; Tristram's `MonLvl1` and `MonLvl1Ex` are both 6, so which column is not separated);
- crafted (quality 8) prices, the repair price in Hell, the gamble price at clvl 3: the model as written;
- single-item repair and the partial repair arithmetic (`k`, `D′`, all carried gold); the broken repair (one case,
  `[I]` for draws); the ethereal refusal `[I]` (client-side in practice);
- the sale's store copy: all eight refusal tests run (none short-circuits); a refusal means no `ItemCopy` and no draw,
  `[C]` for the ethereal, broken and `carry1` refusals and `[I]` for the five not reached (`Cracked`, base type 7,
  flag `0x1000000`, `0x0055F590`, the store record's byte `+4`); a copy draws 2 game-seed steps even when no page takes
  it; sell's seed is "raised in part" accordingly;
- `NpcStoreRec` `+0x24..+0x26`: no reader in the windows covered (scoped `[C]`, windows listed in items/0011 § Phase 2b
  item 7); a reader elsewhere stays an open question.

**Released (architect, 2026-10-19, plan 0043 P2b review):** a re-tag pass of the reviewed `docs/specs/items/economy.md`
(and its *Open questions*) with the scopings above, as corrected at the review.
