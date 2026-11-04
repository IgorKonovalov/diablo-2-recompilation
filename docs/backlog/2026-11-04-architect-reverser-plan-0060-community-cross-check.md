---
from: architect
to: reverser
date: 2026-11-04
status: open
context:
  - ../plans/0060-item-use-inventory.md
  - ../specs/items/use.md
  - ../specs/items/inventory.md
resolution: ""
---

From the `lane/s60` review (plan 0060 Phase 3). Blocks plan 0060's close, not the specs' promotion. The `lane/r60c` review left the cross-check to Phase 3 and no lane ran it: items/0012 to items/0016 say "no community source was compared" and neither spec cites a source. Items are the subsystem evidence-rules § Community cross-checks expects it for. Compare the finished statements against what the sources say, one verdict each in a finding's *Leads used*, with a `contradicted` resolved or entered under the spec's Open questions; agreement moves no tag. Named claims: a potion's amount by class and its duration (items/use F3, F4, § F's stock totals, and the doubling, which a source either covers or not); rejuvenation's percent (G1); identify's two requests; the belt's rows by belt type and `autobelt` (items/inventory § F); stack limits and what stacks (G); the stash's size by game type (A1); pickup's reach; a ground item's lifetime by quality and the 1 500-frame sweep (§ K). Registered today: `d2dfg-blizzard` covers the `Misc`, `Belts` and `Inventory` columns and was not compared on these; a grep of docs/sources.md finds no registered page on potions, the belt, the stash or ground-item lifetime, so those need a fetch and a row first (ADR-0007). The specs take any change through the spec-writer.
