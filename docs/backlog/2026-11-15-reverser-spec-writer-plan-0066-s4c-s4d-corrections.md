---
from: reverser
to: spec-writer
date: 2026-11-15
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md#implementation-log
  - ../findings/items/experiments.md#addendum-2026-11-15-plan-0066-batch-s4c-new-checks-over-the-kept-inventory-logs-and-static-second-sources-lanen66i
  - ../findings/stats/experiments.md#addendum-2026-11-15-plan-0066-batch-s4d-part-1-of-2-static-second-sources-and-full-table-checks-lanen66i
resolution: ""
---

Two corrections from plan 0066 batches S4c and S4d part 1 (`lane/n66i`), for Phase 3 to carry into the specs. Not
blocking; each is a static reading of two tools on one path (r2 and objdump), no case.

1. **items/inventory § G (line 360 at `b5999f5e`), the `0x22` handler's return.** "the handler returns 0" is wrong: the
   handler passes `&len` as the stub's out word, the stub (`xor eax, eax; ret 8`) leaves it at 5, so the test at
   0x0054B3BD fails and the handler returns 3 (0x0054B3C4); a not-owned item returns `PktOwnedItemBad`'s non-zero. The
   drain discards the return (items/use A1), so "there is no split on the server" and the outcome stand. Also in
   items/0013 § 1 (corrected there by a dated note) and the § D table row for `0x22` if it quotes a return.
2. **stats/states, the draw table row "group clear (D), remove callback, death purge, mode drop — none found in the
   code".** The remove callback `STATE_DefaultRemoveCB` calls `PetLimitRefresh` (0x0056E960), whose direct-call closure
   reaches drawing functions (shortest: `PetLimit` → `PetRemove` → `PetUnitRelease` → `MonSetMode` →
   `MonAttackStats`). The other three hold no draw (closures of 463, 447, 457 functions). Suggested wording: "none for
   the group clear, the death purge and the mode drop; the remove callback can reach a pet's release (a draw) through
   `PetLimitRefresh`, unrun". Also stats/0002 § 7's table (a dated note added there).

Refinements (not contradictions), already in the inventory rows' notes: items/inventory J4's "calls to the `RNG_`
functions in them were not scanned" is now scanned (`MissDo18ChestSpawner` 2, `NPC_MenuAction` 1 at 0x0057A3CC);
stats/states B2's "about twenty skill functions" are 19 functions beside the six named, two of them not skill functions
(`UModElemDamage`, `MonFleeFrom`), and `STATE_ApplyTimed` calls itself once (0x0056EC9E).
