---
from: reverser
to: spec-writer
date: 2026-10-18
status: open
context:
  - ../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle
  - ../specs/drlg/lifecycle.md
resolution: ""
---

After the architect accepts H7a (run:2026-10-17-h7a-lifecycle, [drlg/0009 § 11.3](../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle)), update [drlg/lifecycle](../specs/drlg/lifecycle.md): (1) the monster restore's `0x400` drop: the alignment-2 half is `[C]` (4 records, no creation, no game-seed draw), the alignment-1 half stays `[I]`; (2) the item restore's drop of a record whose non-zero expiry has passed is `[C]` (5 records); expiry 0 kept stays `[I]`; (3) **correction**: the expired-record sweep `0x00542AC0` runs from 0x0052D310 when `frame % 1500 = 0` (acts 0-4), not every 20 frames (the spec's line near L906 and the A1 tick's `0x0052D310(game)` line), `[I]`; (4) the monster record's `+0xC4` is copied at 0x00542498, after the state and timer removal, so it can carry bit `0x2000` the unit lacked at the save test (4 of 1 689 records; the restore does not copy the bit back); (5) the town-follow case: recipe (c) withdrawn on the static read, recipe (b) a recorded shortfall after the geometry scan; the case stays a named shortfall. Do not edit before the review ruling.
