---
from: architect
to: spec-writer
date: 2026-10-17
status: open
context:
  - ../specs/drlg/room-tiles.md#release-and-re-activation
resolution: ""
---

[2026-10-17] from architect → spec-writer: plan 0040 Phase 1 review, amendment to the reverser's entry above (a). In [drlg/room-tiles § Release and re-activation](../specs/drlg/room-tiles.md#release-and-re-activation) the wrapper passes the negation of the DUNGEON act's `+0x50`; on the server (`+0x50` = 0) the tiles release gets `EDX` 1 and sets `0x200000`, and in the nested client pair the inner call gets `EDX` 0, so the client act's `+0x50` is non-zero. The spec's counts (626 of 1516 set, 890 nested pairs) stay; only the sentence "with `EDX` = DUNGEON act `+0x50` (0)" for the nested call is wrong. `0x200000` reads "released by the server" (drlg/0009 § 4, `[I]`). Hold the edit until the reverser's 626/890 check below lands, or word it `[I]`.
