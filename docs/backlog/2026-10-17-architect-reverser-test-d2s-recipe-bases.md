---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "lane/rbs2 2026-10-17: combatow and combatsorh pinned on smpsor-l50.d2s (b07db91b…, 210b2c0c… = the recorded saves, combat/experiments); six more recipes from ed40eba (H6d) had the same gap and are pinned to their recorded saves (questfreshct on the classic base). tools/test_d2s.py: 44 tests, 0 failures. [tools/test_d2s.py](../../tools/test_d2s.py)"
---

`tools/test_d2s.py` fails on `main` (seen at the `lane/rbs` review, 2026-10-17): `RecipeTest.test_every_recipe_has_a_base` finds `tools/d2s_recipes/combatow.json` and `combatsorh.json` (added in e2d42b1, the plan 0037 resume lane's gear revisions) with no entry in `RECIPE_BASES`. Add their base saves to `RECIPE_BASES` (or say why they have none) and re-run the test: 44 tests, 0 failures.
