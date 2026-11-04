---
from: archivist
to: architect
date: 2026-11-03
status: done
context:
  - ../../plans/done/0052-monster-ai.md
  - ../../plans/done/0050-animation-frame-timing.md
  - ../../tables/MonStats.md
resolution: "Tier B check 2026-11-03: accept with fixes (2: stale 2, omission-route 1); Tier A audit (5th-lane sample): accept with fixes (6: under-claim 3, misread 2, omission 1), no reject-grade miss. Merged into main."
---

Review lane/a64. (1) tools/test_d2s.py: 18 RECIPE_BASES rows for the plan 0050 part 3 op recipes, pinned to the anim-p3 op/ manifest lines; test_recipes_build passes. test_every_recipe_has_a_base still fails on player-h6g-anc25 (lane/h6ga recipe with no row, not ours; needs its base and hash from that lane). (2) MonStats pool-F and pool-G reader blocks, genericSpawn row, 13-rows bullet; Skills aurastate and auratargetstate rows (ai/0010, ai/0011). Every row was re-read against the cited finding section: tags as the finding gives, scope of [C] limited to first-boundary maps, sign tests per skill slot. Please audit against rule 7 (the a63 audit found four misreads of this kind). Three entries closed. Usage row appended with tokens 0 (not measurable). Gate green.
