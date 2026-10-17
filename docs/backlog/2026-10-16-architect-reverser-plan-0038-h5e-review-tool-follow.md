---
from: architect
to: reverser
date: 2026-10-16
status: done
context: []
resolution: "Done in tools/sweep_h5e.py and tools/drlg.py: (a) rebuilds whose previous placement differs counted apart by level (level 28: 3 of 8); (b) cliff-cave scan and flags 0x10/0x20 keyed by level and grid shape; runs in [drlg/0008 § H5e review](../findings/drlg/0008-outdoor.md#h5e-review-static-reachability-2026-10-17-lanerbs)."
---

[2026-10-16] from architect → reverser: plan 0038 H5e review, tool follow-ups for `tools/sweep_h5e.py` (no row depends on them; a new version gives its sha256 in any later addendum). (a) `logs`: count the rebuilds whose previous placement's rect differs from the act's rect for the level apart from the others (only level 28's three in s2 differ); (b) `scan`: key the cliff-cave scan and flag `0x10`/`0x20` counters by level id and grid shape, so that "flag `0x20` only on levels 4–6" is printed rather than read off a review script.
