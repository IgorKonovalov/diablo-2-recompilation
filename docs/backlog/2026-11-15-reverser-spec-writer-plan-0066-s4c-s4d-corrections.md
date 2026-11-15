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

**2026-11-15 (reverser, S4d part 2, `lane/n66i`).** Five more, each in [stats/experiments § Addendum S4d part 2](../findings/stats/experiments.md#addendum-2026-11-15-plan-0066-batch-s4d-part-2-of-2-new-checks-over-the-kept-stats-logs-and-static-second-sources-lanen66i)
and the inventory rows' notes, with dated notes in stats/0001 and stats/0002:

3. **stats/aggregate, Entry points "An item is equipped or unequipped" and stats/README's entry row.** The body-to-cursor
   pickup unlinks through `sub_0063AAF0_InvItemRemove` → `UNIT_UnlinkItemStatList`, not `ITEMS_DetachFromOwner` (260
   unlinks with no detach in their frame). Suggested: name the pickup path beside H2.
4. **stats/aggregate, Constants: list flags `0x2`.** On the unit list it marks a flag-4 child (set by
   `STATLIST_LinkToUnit`, tested and cleared by `StatListsDropOnMode`); "timed" holds for plain lists only. B1's
   `unitList.flags |= 0x2` line is that marker.
5. **stats/aggregate, Draw order "no RNG call was found in their code" (the requirement refresh).** `EquipReqRefresh`'s
   direct-call closure reaches 122 drawing functions (`PlayerSkillReselect` → `PlayerSetSkill` → `AuraSelect` →
   `SKILLS_SrvDo` → `PlayerModeCmd` → `PlayerModeAllowed`); no seed moved in 972 logged refreshes. The set activation and
   the passive refresh reach none.
6. **stats/states A2 "`UNIT_HasState` answers for players, monsters and objects".** Types 0, 1, 3: players, monsters,
   missiles; objects answer 0. Also B1's gate anchor: 0x0056E9C7–0x0056EA08, not 0x0056E9A7–0x0056E9C3 (lines 123, 179).
7. **stats/aggregate H4 and the reimplementation note "the commonest gap … in every session".** 136 is the commonest gap
   in 22 of the 28 kept logs; six s1017 logs have 1.

Refinements: I3's "both hands" is each occupied hand (76 swaps: 4+5 ↔ 4+5, 4+5 → 4, 4 → 4+5); C2's "a player gets a skill
refresh" is `PetLimitRefresh` (type 0 only), after a first call of 0x005C0B50; the stamina shrine's list holds stat 28 alone
at its first dump.
