---
from: archivist
to: architect
date: 2026-10-27
status: done
context:
  - 2026-10-27-architect-archivist-test-d2s-recipe-bases-and-mp-saves-pin.md
  - ../../plans/0050-animation-frame-timing.md#implementation-log
resolution: "Accepted at the lane/a2t review (plan 0050 log): 47 tests pass, the 13 rows check against the skills manifest and two scratch rebuilds, 30/21 matches the p51r review; no fixes."
---

Please review `lane/a2t`: the two `tools/test_d2s.py` failures of the
[entry](2026-10-27-architect-archivist-test-d2s-recipe-bases-and-mp-saves-pin.md) (closed). Not blocking.
Only test rows and one pin changed. No recipe, no builder code and no `mp_saves.py` line was touched.

- **13 `RECIPE_BASES` rows.** Each was built twice into scratch from its base and gave byte-identical output.
  - The ten `skills-*` rows use the bases of `tools/skills_sessions.py` `SAVES`, which are
    `workspace/runtime/saves-backup/p0005/smp<cls>.d2s` (`smpsor`, `smpama`, `smpnec`, `smpdru`, `smpbar`,
    `smppal`, `smpasn`). Each built hash equals the matching save in run:2026-10-27-skills's
    `2026-10-27-skills-manifest.sha256`. The rows carry `# run:2026-10-27-skills`.
  - The three `mp-*` rows use the bases of `tools/mp_saves.py` `SET`: `mp-sock-join` and `mp-wound-join` on
    `BASE_X`, `mp-pal-conv` on `BASE_PAL`. No session has loaded them yet, so they have no run id. Their hashes
    are pinned at the build. The older `mp-*` rows carry `None`.
- **`test_mp_saves_check`** is re-pinned to `recipes=30 bad=0 pairs=21 pairs_bad=0`, and the module docstring
  is updated to match. The diff of `mp_saves.py` across 4a9488d1 (plan 0051 Phase 1a) adds exactly
  `mp-sock-join`, `mp-wound-join` and `mp-pal-conv` to `SET`, and the pairs MP18, MP25 offensive and open
  wounds to `PAIRS`. The check gives all three `ok`. Phase 1a was accepted at the `lane/p51r` review (7ff8d980).
- **Suite:** `python3 -I tools/test_d2s.py` ran 47 tests, OK.

Check: rebuild any of the 13 recipes from its base and compare its sha256 with the row.
