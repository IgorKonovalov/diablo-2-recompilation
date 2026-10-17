---
from: spec-writer
to: spec-writer
date: 2026-10-17
status: open
context:
  - ../plans/0041-stats-and-states.md#implementation-log
resolution: ""
---

Not blocking; for after the plan 0041 Phase 3 review. ADR-0012 lets a wiki page cover reviewed specs only, so
`lane/p41s` wrote none. Once [stats/aggregate](../specs/stats/aggregate.md) and [stats/states](../specs/stats/states.md)
are reviewed: (a) a new wiki page on how stats add up and how states live (`docs/wiki/stats.md`, `based_on` the two
specs and the overview), linked from the wiki index; (b) refresh [wiki/combat](../wiki/combat.md) (the "where the
inputs come from" bullet and the player's life tick, now reproduced under poison in combat/delivery E4) and
[wiki/items](../wiki/items.md) (`add func` when worn; its `based_on` items/properties date is stale, gate W4); (c) the
characters page if it states how the maxima add up.
