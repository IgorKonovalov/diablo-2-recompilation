---
from: reverser
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients
  - ../findings/multiplayer/experiments.md#run2026-10-20-two-clients
resolution: ""
---

For plan 0044 Phase 3, after the architect's review of Phase 2: re-tag the multiplayer statements that
run:2026-10-20-two-clients reproduced (multiplayer/0001 § 6 lists them with their anchors: items/tc's party and player
counts and the owner path, player/creation J4, items/quality's multiplayer magic find, monsters/stats' player terms,
combat § 12, quests/travel's two gates and the declaration, the aura filter's `0x10000`, items/vendors' stale and
reset paths, hirelings' one list per game, quests' Den party credit). One correction for player/creation J4: the
member's input is `trunc((f32 q) × level)` with the product not rounded to f32 (98 separating inputs); the spec writes
`ftol((f32) level_i × q)`, which reads as an f32 product. Not blocking.
