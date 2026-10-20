---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../plans/0048-seed-to-world.md
  - ../../findings/chain/0001-oracles.md
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (1: oracle 14's variant roll already modelled by tools/mon_sweep.py pool, S3a). All ten proposed oracles assigned to Phase 1, 14 moved before 16/17, barrier grid and type-11 point with 20; S/N classes meet the Done-when; both proposed input classes accepted into the plan's Context; oracle 31 stays listed; stale spawn row routed to the spec-writer; MonEquip table doc asked of the archivist. Plan 0048 log, 2026-10-20 review entry. Phase 1 can start."
---

Review plan 0048 Phase 0 (`lane/p48a`, static, no Ghidra, no harness): [chain/0001](../../findings/chain/0001-oracles.md),
`tools/oracle_ledger.py`, the findings index row and the plan log entry. Blocking Phase 1, whose scope this review
rules.

Asked of the review in particular:
- **Which oracles Phase 1 retires.** The proposal is
  [§ 4](../../findings/chain/0001-oracles.md#4-proposed-phase-1-retirements-for-the-architects-ruling), in order: 2 staff
  mods as the default (already modelled, plan 0038 S2b); 16 and 17 (`InitFn` 46), the window's monsters; 14 the
  unit-seed variant steps; 22 the `Orient89Unit` creation; 19 the gate's DRLG parts; 21 another room's seed; 20 the grid
  snapshot, with its barrier grid and type-11 point; 7 the gold piles' items; 6 an object's drop; 13 MonEquip. Not
  proposed: 8, 12, 18, 24, 25 (inputs) and 9, 10, 11, 23 (off the chain).
- **Two input classes that the plan's *Context* does not list** (§ 3.3): the game seed at each drop, and the killer's
  magic find (the player's character). Phase 2's 500 drops need both, or a ruling that they are logged inputs.
- **Activation order** (§ 3.2, the plan's open question): an input beyond the per-room seeds. The game seed at a pass
  entry is chained only while no simulation unit was created since the previous pass.
- **Ledger classes.** Besides an oracle number, a line is S (heading, link, ADR title, definition, diagram participant)
  or N (a "no oracle" statement). The plan's *Done when* says "in the list or a historical sentence"; retired oracles
  are listed with status *chained*, so the historical lines map to them. Is S/N acceptable as a third class?
- **Oracle 31** (the plan 0014 tile placement) has no matching line of its own: the only match in its paragraph is a
  link. It is listed for completeness.
- **Tags.** The inventory rows carry the owning spec's tag and anchors: `[C]` where the spec's run backs it, `[I]` for
  oracles 9, 13 and 25. The proposals and the activation-order inferences are `[I]`. There is no new code reading.
- **Spec lag (§ 5)**, for Phase 3: affixes and properties on staff mods, the uniques-sets builder rows, spawn's
  snapshot row, vendors on `HIRE_BuildStock`, and the drlg/overview maze wording.
