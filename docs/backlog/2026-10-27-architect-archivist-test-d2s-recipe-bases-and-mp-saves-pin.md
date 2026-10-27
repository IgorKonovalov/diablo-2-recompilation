---
from: architect
to: archivist
date: 2026-10-27
status: open
context:
  - ../formats/d2s.md
  - ../plans/0050-animation-frame-timing.md#implementation-log
resolution: ""
---

Two `tools/test_d2s.py` tests fail on `main` (found at the `lane/a50t` review, 2026-10-27; that lane did not cause them). Both come from recipes other lanes added to `tools/d2s_recipes/` without updating the test.

1. `RecipeTest.test_every_recipe_has_a_base`: 13 recipes have no `RECIPE_BASES` row. They are `mp-pal-conv`, `mp-sock-join` and `mp-wound-join` (plan 0051 Phase 1a, the MP25 offensive, MP18 and open-wounds recipes) and `skills-ama`, `skills-amaj`, `skills-ass`, `skills-bar`, `skills-barh`, `skills-dru`, `skills-nec`, `skills-pal`, `skills-sor` and `skills-sorlow` (plan 0045's skills runs). No row is stale. `travel-tab2` is not among them: the review request named it from the positional list diff. For each recipe, give its base save and the sha256 of the built output, as the other rows do, with its run id where one exists.
2. `QuestBitsTest.test_mp_saves_check` pins `SURVEY mp_saves recipes=27 bad=0 pairs=18 pairs_bad=0`, but the survey now gives `recipes=30 bad=0 pairs=21 pairs_bad=0` (the three recipes above and their pairs MP25 offensive, MP18 and open wounds, all `ok`). Re-pin it, after checking that the three new pairs are the only change.

Done when `python3 -I tools/test_d2s.py` runs green (47 tests at the review). Non-blocking for plan 0050.
