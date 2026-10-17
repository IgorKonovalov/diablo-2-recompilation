---
from: architect
to: spec-writer
date: 2026-10-17
status: done
context:
  - ../specs/drlg/room-tiles.md#release-and-re-activation
  - ../wiki/levels.md
resolution: "Done (lane/p40s): [drlg/room-tiles](../specs/drlg/room-tiles.md) § Release and re-activation, the EDX bullet raised to [C] by run:2026-10-17-lifecycle (2 440 server releases EDX 1 with 0x200000 set, 8 277 client releases EDX 0 with it clear), no reader kept [I]; open question struck; runtime-state row, research-map row and both levels wiki passages restated; {C 120, I 32} -> {C 121, I 32}."
---

[2026-10-17] from architect → spec-writer: `lane/sw5` review follow-up, **after `lane/p40h` (plan 0040 Phase 2) merges**. That run logged `0x200000` set on 2 440 server releases and clear on 8 277 client releases. Check whether its accepted finding answers the open question in [drlg/room-tiles](../specs/drlg/room-tiles.md#open-questions) ("whether the 626 calls with `EDX` ≠ 0 are exactly the server releases") and, if it does, raise the `[I]` bullet *The `EDX` the wrapper passes* in § Release and re-activation as far as the accepted ledger allows, strike the open question, update the runtime-state row for `0x200000` and the research-map row, and restate the two [levels](../wiki/levels.md) passages on the release flag (§ release, and the open list). Not before the p40h review lands.
