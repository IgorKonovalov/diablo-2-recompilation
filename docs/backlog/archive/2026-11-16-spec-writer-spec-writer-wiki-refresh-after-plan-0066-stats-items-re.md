---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../specs/README.md
resolution: "Refreshed in lane/fuw: [wiki/stats-and-states](../../wiki/stats-and-states.md) (the floor and ops 3/10/12 under emulation, the act-clock refresh with 136 in 22 of 28 logs, the open draw path through skill reselect, sockets, the weapon switch, the state test's object answer, durations, the monster refusal, the stamina bonus in the run mode), [wiki/economy](../../wiki/economy.md) (the price core's early exits, ear and body bases, recharge, reduced prices on repair, the gold write, the ethereal refusal, the 13 bases without durability, the melee-only wear caller) and [wiki/inventory](../../wiki/inventory.md) (the handlers to their callees, the discarded refusals, the split stub, belts, stacking, pickup); based_on bumped."
---

Plan 0066 Phase 3, the stats/items cluster (`lane/n66si`), updated stats/aggregate, stats/states, stats/README,
items/economy, items/use, items/inventory and quirks (Q369, Q391, Q490, Q514) on 2026-11-16, so three wiki pages carry
W4: stats-and-states, economy and inventory. What changed for a reader: most of the stat-list machinery (links, the
take test, the ops, the floor, the event list, the weapon switch, the passive rebuild) is now confirmed by the kept
logs, emulation or a second tool; the idle requirement refresh is queued by the act clock pass, and its 136-frame gap
is the commonest in 22 of 28 kept logs, not every one (wiki/stats-and-states says "in every session"); the
requirement refresh can reach drawing code through `PlayerSkillReselect` (whether a stock refresh draws is open);
`UNIT_HasState` answers 0 for objects; the price core is confirmed whole under emulation; the 13 `nodurability`
repair bases are 12 crossbows and the Phase Blade; the `0x22` handler returns 3 (discarded); the request handlers,
pickup, belt tests and stacking are confirmed to their first callees. Refresh the pages against the specs (spec-writer
review-fixes 1: a page follows the spec that carries the raise) and bump `based_on`. Not blocking.
