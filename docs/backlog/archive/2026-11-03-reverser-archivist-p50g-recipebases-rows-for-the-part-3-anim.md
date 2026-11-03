---
from: reverser
to: archivist
date: 2026-11-03
status: done
context: []
resolution: "18 RECIPE_BASES rows added in tools/test_d2s.py, pinned to the anim-p3 op/ manifest lines; test_recipes_build passes (the one remaining failure is player-h6g-anc25, a row missing from lane/h6ga, not part 3)"
---

Plan 0050 Phase 2 part 3 added the 18 recipes anim-<cls>-op-t<k> (ama, ass, dru, nec, sor; t0-t2), anim-dru-op-th, anim-sor-op-br and anim-sor-op-run (tools/d2s_recipes/). Their RECIPE_BASES rows in tools/test_d2s.py are not added. Pins: the saves-2026-10-30-anim-p3/op/ lines of workspace/logs/anim/2026-10-30-anim-p3-manifest.sha256 (the saves are unchanged in part 3b, which reused them). Names from SAVES in tools/anim_sessions.py.
