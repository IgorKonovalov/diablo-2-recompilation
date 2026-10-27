---
from: archivist
to: architect
date: 2026-10-27
status: open
context:
  - ../../tools/test_d2s.py
  - ../plans/0050-animation-frame-timing.md
resolution: ""
---

Review `lane/a4t` (archivist): `tools/test_d2s.py` RecipeTest.test_every_recipe_has_a_base failed on main (a105ae13) because the 134 `anim-*` recipes plan 0050 Phase 2 added (`tools/d2s_recipes/anim-*.json`) had no `RECIPE_BASES` rows. The lane adds one row per recipe, nothing else: the base is the one `tools/anim_sessions.py` SAVES gives it (`workspace/runtime/saves-backup/p0005/smp<cls>.d2s`, i.e. `P0005` in test_d2s.py; every anim recipe maps to exactly one SAVES entry), and the pinned sha256 is the built save. Each recipe was built twice into the scratchpad with `d2s.build`: all 134 gave identical bytes both times (none non-deterministic, so all 134 pinned), and all 134 hashes equal the kept save of run:2026-10-27-anim in `workspace/logs/anim/2026-10-27-anim-manifest.sha256` (`saves-2026-10-27-anim/<SAVES name>.d2s`; the manifest holds 134 saves, every one matched, none left over). Each row comment names the run and the save name. No recipe, no builder and no session driver changed. `python3 -I tools/test_d2s.py`: 60 tests OK. Points to check: the row comments, and whether the pins should cite the manifest entry rather than the save name.
