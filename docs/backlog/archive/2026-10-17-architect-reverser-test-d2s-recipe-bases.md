---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "Fixed on lane/arc5 (2026-10-17): RECIPE_BASES gains combatow, combatsorh and six other legacy recipes plus the 0042/0044 sets; test_d2s.py 45 tests OK. If lane/rbs2 adds the same entries, keep one copy at merge."
---

`tools/test_d2s.py` fails on `main` (seen at the `lane/rbs` review, 2026-10-17): `RecipeTest.test_every_recipe_has_a_base` finds `tools/d2s_recipes/combatow.json` and `combatsorh.json` (added in e2d42b1, the plan 0037 resume lane's gear revisions) with no entry in `RECIPE_BASES`. Add their base saves to `RECIPE_BASES` (or say why they have none) and re-run the test: 44 tests, 0 failures.
