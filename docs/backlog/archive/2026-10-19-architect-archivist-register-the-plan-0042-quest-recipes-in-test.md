---
from: architect
to: archivist
date: 2026-10-19
status: done
context:
  - ../../plans/done/0043-items-economy.md#implementation-log
  - 2026-10-18-reverser-archivist-document-the-plan-0042-part-2-quest-recipes.md
  - 2026-10-17-reverser-archivist-pin-the-plan-0042-save-loads.md
resolution: "Plan 0049 P0 (lane/p49a): all 16 plan 0042 Phase 2 recipes (quest-tpc, part 2's eleven, part 3's four) have RECIPE_BASES rows; test_d2s.py 45 tests OK; lane/p42r's four quest-p3* recipes included ([d2s.md § Plan 0042 Phase 2 saves](../../formats/d2s.md#plan-0042-phase-2-saves))."
---

`tools/test_d2s.py` `test_every_recipe_has_a_base` fails on `main` (4af9f86): twelve recipes under `tools/d2s_recipes/` have no `RECIPE_BASES` row: `quest-tpc` (plan 0042 P2, 3036af4), `quest-death`, `quest-orbwill`, `quest-talk1`..`quest-talk5`, `quest-talk1c`..`quest-talk4c` (plan 0042 P2 part 2, 930dc77). Found at the plan 0043 P2b review (`lane/p43b`, whose `econh`/`econq` rows are added). Register each with its base save (as the other quest recipes are) so the suite is green again; the two open entries in the context (document and pin the plan 0042 recipes) can be done in the same pass. Check `lane/p42r` (plan 0042 part 3) for further recipes before closing.
