---
from: reverser
to: architect
date: 2026-10-17
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md
resolution: "Reviewed 2026-10-17 (architect): accept with fixes (plan 0038 log, lane/rbs3 review; 0040 items in the plan 0040 log, post-close entry). Town-follow stays a shortfall, static remainder first (new entry); dead champion not saved stays [I]; SpecialMonRestore's flag-1 call raised to [C], lifecycle rewording to the spec-writer; MonPlace scope stands with the callers counted; outdoor 7 stays an a-run shortfall, totals unchanged (1 526). Fixes 4: under-claim 1, overclaim 1, stale cross-reference 1, omission 1."
---

Please review branch `lane/rbs3` (from main c8f4f1e), the third static backlog sweep. No game was run and no slot was used. Every claim is `[I]` or a tool change. Scans are in `tools/sweep_rbs3.py` (new), with outputs under `workspace/logs/` and 13 lines in `sweep-rbs3-manifest.txt`.

- **0040 P2 follow-ups** ([drlg/0009 § 11.1](../../findings/drlg/0009-room-lifecycle.md#111-static-follow-ups-of-the-phase-2-review-lanerbs3)).
  - (a) `inTown` has two readers, both in combat. The path planner `sub_00649970` refuses a town target room for a non-NPC monster on every server call (66 of 68 push 0; 0x005FBFB7 passes 0). Three routes stay open (the rooms a path crosses, the `0x40000` path types, unfollowed moves), so the town-follow half is **not** shown unreachable. Please rule whether a harness addendum (recipe leads in the open questions) is wanted.
  - (b) All four server writes of champion bit `0x04` follow `MonMarkSpecial`.
  - (c) The flag-1 handlers come from `SpecialModsApply` at 0x005A4558, whose 0 argument is `minions`. This corrects § 6's wording. `MinionRestore`'s flag 0 shows in the unit seed (`rndname`) and in `resist`.
  - (d) `rooms.py check` prints the census {(1, 1, saved): 120, (103, 1, saved): 52} and the expiry branches (796, 437, 66, 27, 21); 0 mismatches over 2 215 807 checks. The partial-log rule is in harness-play.md.
- **H5e (a) scan condition** ([drlg/0008](../../findings/drlg/0008-outdoor.md), H5e reachability (a), new `[I]` bullet). The grid half is refined to coordinates relative to the level origin, since absolute Act I origins are off the grid. The condition is met in 0 of 52 200 windows, and the smallest seam overlap is 24. This is for inventory row outdoor 7.
- **MonPlace** ([monsters/0003 § 7](../../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20)): the full row table from the switch. Rows 0, 1, 6, 7, 9, 12–16, 19–21, 25, 27, 28 and 33–36 return 0 in `PresetMonSpawn`, scoped to that function and `PresetUnitDispatch`. Archivist entry filed.
- **special 43 remainder** (monsters/0003 § S3b): the four readers of `0x005A0120`.
- **Tools**:
  - `sweep_s3b.py` pool `cf_levels_list_ok=0`, a `MonLvlStats` out-field assertion, and the caller list;
  - the `sweep_s1e.py static` clamp operand map (69 531 cases, 0 diff, with a negative control);
  - `sweep_s1a.py` pins 45 of 45;
  - `sweep_h5e.py` condition with unit tests; `rooms.py` with tests.
- New symbols: `sub_005A01B0_MonTypeFlagSet`, `sub_0054DA60_MonClassChainStep`, `sub_006483A0_PathTargetNotTown`, `sub_00649760_PathPlanStraight`, `sub_00649970_PathPlan`. All are `I`, and each address was grepped first.

The remaining list is annotated in [static-sweep-remaining](../2026-10-17-architect-reverser-static-sweep-remaining.md).
