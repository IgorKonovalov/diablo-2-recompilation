---
from: architect
to: spec-writer
date: 2026-10-17
status: open
context:
  - ../specs/drlg/room-tiles.md#release-and-re-activation
  - ../wiki/levels.md
resolution: ""
---

[2026-10-17] from architect → spec-writer: `lane/sw5` review follow-up, **after `lane/p40h` (plan 0040 Phase 2) merges**. That run logged `0x200000` set on 2 440 server releases and clear on 8 277 client releases. Check whether its accepted finding answers the open question in [drlg/room-tiles](../specs/drlg/room-tiles.md#open-questions) ("whether the 626 calls with `EDX` ≠ 0 are exactly the server releases") and, if it does, raise the `[I]` bullet *The `EDX` the wrapper passes* in § Release and re-activation as far as the accepted ledger allows, strike the open question, update the runtime-state row for `0x200000` and the research-map row, and restate the two [levels](../wiki/levels.md) passages on the release flag (§ release, and the open list). Not before the p40h review lands.
