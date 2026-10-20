---
from: spec-writer
to: architect
date: 2026-10-17
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md
resolution: "Reviewed 2026-10-17 (architect): accept with fixes (4: under-claim 1, stale cross-reference 1, omission 1, other 1). See the plan 0038 log, lane/sw6 review."
---

Not blocking. Review `lane/sw6` (from `main` `925d060`; commits `c210e90` specs and research map, `e99c773` wiki, then
this entry and the plan 0038 log). It applies two spec-writer entries that need no new evidence:
[rbs3 lifecycle and MonPlace readings](2026-10-17-reverser-spec-writer-rbs3-lifecycle-and-monplace-readings.md) (with the
`lane/rbs3` review annotation) and [outdoor H5e remainders](2026-10-17-architect-spec-writer-outdoor-h5e-remainders-after-rbs2.md).

Old → new:
- [drlg/lifecycle](../../specs/drlg/lifecycle.md) {C 78, I 70, L 8} → **{C 80, I 73, L 7}**. H2b: the `SpecialModsApply`
  call's flag-1 handlers `[C]` (0x005A4558, the run's 15 champion restores), its pushed 0 the `minions` argument `[I]`.
  H2c: `MinionRestore`'s own flag-0 calls, no `rndname` unit-seed step (comment, no tag). § F: the dead-champion
  bullet restated from drlg/0009 § 11.1 (b), still `[I]`; the `[C]` "No logged dead champion was saved" unchanged.
  § H: the champion bullet's "which call is open" sentence removed; new `[C]` bullet (flag 1 through
  `SpecialModsApply`), new `[I]` bullets (the `minions` 0; `MinionRestore`'s flag 0, "would show outside stat 12,
  not looked for"). The "dead special would come back alive" bullet now points at the § F reading. Open questions:
  town-follow kept `[L]` with § 11.1 (a) (the path planner's town refusal, three routes open, `inTown` two combat
  readers) in place of the `inTown` lead; "a champion without `0x08`" and "which call applies flag 1" struck; the
  minion-flag half kept as its own `[L]`.
- [monsters/special](../../specs/monsters/special.md) {C 106, I 92, L 3} → **{C 106, I 94, L 3}**. § H: new `[I]` bullet,
  every MonPlace row from the `PresetMonSpawn` switch (the rows that place nothing, `place_group25`–`100` included,
  and a table of rows 4, 5, 8, 10, 11), scoped to `PresetMonSpawn` reached through `PresetUnitDispatch` (first spawn
  and restore), the four other callers unfollowed; the fixed-class bullet's "19–21 class 0" corrected (they never reach
  that table) and 27 added to the rows that place nothing. § J: the restored-champion `[C]` bullet now names the
  `SpecialModsApply` call; new `[I]` bullet (the `minions` 0, `MinionRestore`'s flag 0). E1: the S3b readers of the
  mod list (save, restore re-append with flag 0, the three-slot packet, `SuperUniqueSpawn`'s append), kept `[I]`.
- [drlg/preset](../../specs/drlg/preset.md) {C 137, I 23, L 2} → **{C 137, I 25, L 2}**. § 6: new `[I]` bullet, a kept
  `place_group` unit places nothing in `PresetMonSpawn`, at the review's scope. Reimplementation notes: the
  `place_group` note says the roll is still drawn though the unit places nothing `[I]`.
- [drlg/outdoor](../../specs/drlg/outdoor.md) {C 180, I 19, L 3} → **{C 180, I 19, L 2}**. H2 (old L731, the entry's
  L693) and H6 (old L909, the entry's L866) say why there is no stock case: (e), (e′) for the Blood Moor's `0x20`;
  (c) with the border-piece rotation (`OutPresetFileRotate`, index never 3 for Defs 4–7) for at most 4 endpoints;
  (d) for at most 45 pool nodes. The H6 pool clause is folded into the endpoint bullet, so no `[I]` is added. Open
  questions: the road branches and the swapped scan struck (answered); the branches entry keeps the vertex merge and
  the waypoint pass with their scan conditions.

Research-map rows for all four rewritten whole. Wiki: [levels](../../wiki/levels.md) (dead champion, restore forms,
town-follow, kept group presets, the three outdoor branches) and [monsters](../../wiki/monsters.md) (MonPlace rows)
restated; `based_on` dates already 2026-10-17, W4 0. Points for the review: (1) the monsters/special fixed-class
correction (19–21) follows monsters/0003 § 7's new bullet over its older one; (2) the S3b E1 restatement was in the
entry's third bullet, not in the task's list; (3) the outdoor L count drops by one through a struck answered question,
not a re-tag.
