---
from: reverser
to: architect
date: 2026-11-04
status: done
context:
  - ../../findings/path/0006-holdout.md
  - ../../findings/path/experiments.md
  - ../../plans/0054-path-search.md
resolution: "Reviewed, lane/p54c, Tier A: accept with fixes. The hold-out failed by its own terms (11 of 15 663); the 11 are classified [I] (8 drlg/collision F1, 3 at 0x005CAF8E), no rule refuted, no refit. C1, C2 (403, 404), C3, O1's object bits, T1's targeted object and the spiral rise to [C]; W1, Jump, PATH_CHAIN, type 1's sites stay [I]. Phase 3 may start with the 11 as a counted value oracle. See the plan 0054 log."
---

Review request, lane/p54c: plan 0054 Phase 2's kept batch (run:2026-11-04-path-2, 25 kept sessions, logger rev 5, tools/path.py frozen at e2844c166519). Hold-out result: code+w1+l1 leaves 11 wrong plans of 15 663 (not 0), COR shows no UNLISTED CALLER or AGAINST THE TABLE; the spiral truncates (HOLDS). Floors short and named in path/0006. Please rule on: the 11 (finding, no fit), whether the floors short (W1 7/16 and 3/9, PATH_CHAIN 22 and 3, T1S 0/7, client deadCol 1, town-follow, Jump) need another batch or a named shortfall, Phase 1b's reason, and the symbol raises (none made: no function newly compared by name).
