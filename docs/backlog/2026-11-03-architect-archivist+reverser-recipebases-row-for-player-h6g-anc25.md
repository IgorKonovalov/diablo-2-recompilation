---
from: architect
to: archivist, reverser
date: 2026-11-03
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md
resolution: ""
---

tools/test_d2s.py test_every_recipe_has_a_base fails on main and on lane/a64: tools/d2s_recipes/player-h6g-anc25.json (lane/h6ga, plan 0038 H6g) has no RECIPE_BASES row. Archivist: add the row (class base from the recipe, built-save hash from tools/d2s.py; the test_recipes_build pin). Reverser: if the hash must equal the save the h6ga session used (tools/h6ga_sessions.py, H6gAnc25.d2s), confirm it from the kept run logs. Not covered by any open entry; the a64 review request names it only as not ours.
