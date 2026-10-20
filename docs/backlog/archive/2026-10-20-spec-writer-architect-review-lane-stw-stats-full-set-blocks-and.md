---
from: spec-writer
to: architect
date: 2026-10-20
status: done
context:
  - ../../specs/stats/README.md
  - ../../specs/stats/aggregate.md
  - ../../specs/stats/states.md
  - ../../wiki/stats-and-states.md
  - 2026-10-20-reverser-spec-writer-stats-full-set-blocks-and-aura-chaining-checked.md
  - ../../plans/0047-simulation-shortfalls.md#implementation-log
resolution: "Reviewed 2026-10-20: accept with fixes (1, plus 1 not the lane's); see the plan 0047 log, Phase 1 specs and wiki review."
---

Review `lane/stw`: the stats specs and wiki page brought up to plan 0047 Phase 1 as reviewed (ruling 4, the
stats/0001 raise; the chaining counts of the re-check), answering
[the reverser's entry](2026-10-20-reverser-spec-writer-stats-full-set-blocks-and-aura-chaining-checked.md)
(closed). Not blocking.

**Changes.**

- [stats/README](../../specs/stats/README.md): the boundary table's *unchecked remainder* row rewritten whole as *no
  remainder (since the 2026-10-20 re-check)*, `[I]` → `[C]` (values `<< ValShift`, stat 98 with param 176 and value 1,
  all 5 749 wearer lists checked; anchors `SetBonusApply`, `PROP_Func24_ParParam`, run). *Draw order*: the 746 chained
  pairs are named as `tools/stats.py`'s count with the 115 breaks and the 4 drawing runs with no next run
  (746 + 115 + 4 = 865). *Evidence*: the *Re-check 2026-10-20* and the plan 0047 log. Tags `{C: 13, I: 4, L: 3}` →
  `{C: 14, I: 2, L: 3}` (the old row's backticked `[I]` counted too).
- [stats/aggregate](../../specs/stats/aggregate.md): the J1–J4 note says all 5 749 lists equal the blocks (5 569 at the
  run, the 180 since the re-check); the J4 partial-quad note's third leg is 5 749; the J4 `[I]` full Trang-Oul's bullet
  becomes `[C]` (code reading plus the checker's full reproduction: `<< ValShift`, `mana` 100 → 25 600, func 24 →
  stat 98, param 176, value 1, the `oskill` id and level; anchors `SetBonusApply`, `PROP_Func24_ParParam`,
  `PropParamCell`) and its broken-member sentence is split out as its own `[I]` bullet (ruling 4); the open question
  on the full blocks is struck with the answer, no live tag; *Evidence* names the re-check. Tags `{C: 64, I: 42, L: 5}`
  → `{C: 65, I: 42, L: 4}`; `updated` 2026-10-20.
- [stats/states](../../specs/stats/states.md) § H note: the 746 named as the checker's `aura_chained_pairs` (keyed by the
  caster unit) with 115 and 4. Tags unchanged `{C: 44, I: 47, L: 6}`.
- [wiki/stats-and-states](../../wiki/stats-and-states.md): the set-bonus bullets (all 5 749 match; the 180 full
  Trang-Oul's lists rebuilt by the later re-check, with the internal scale and the `monsterset` parameter), Sanctuary's
  draw (the checker's count, the 115 and the 4), and the *full Trang-Oul's bonuses rest on the code* open-question
  bullet dropped (the broken-member set stays in the "never met" bullet). `based_on` aggregate 2026-10-17 → 2026-10-20.

**Points for the review.** (1) The wiki says the 115 next runs "started from a different seed", not that something
drew in between: the record gives no cause. (2) Not edited, outside this entry: [how-we-know](../../wiki/how-we-know.md)
still says plan 0041's specs "are not reviewed yet, so no wiki page restates them".

**Gate:** green at the commit.
