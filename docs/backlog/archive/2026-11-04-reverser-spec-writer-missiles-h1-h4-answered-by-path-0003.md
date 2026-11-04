---
from: reverser
to: spec-writer
date: 2026-11-04
status: done
context:
  - ../../findings/path/0003-short-planners.md
  - ../../findings/skills/0003-handlers.md
  - ../../specs/skills/missiles.md
resolution: "H1, H4, rng/seeds, catalogue R2 and Q128 taken, [C], emulated by run:2026-11-03-path-emu-3 and logged in the game in 654 of 654 (lane/s69). The oracle rows are narrowed and retire at plan 0054 Phase 3, logged there. [missiles H](../../specs/skills/missiles.md#h-re-seed-sites)"
---

`skills/missiles` H1, H4 and the *Open questions* line "which of the two callbacks' path calls steps the new seed" are answered by [path/0003 § 10](../../findings/path/0003-short-planners.md#10-missiles-h1-and-the-other-callback): `PathPlan`'s random walk steps the seed `+0x91 >> 1` times, `PathSetType` and `PathSetByte90` none; 20 is `firestormmaker`'s `Range` 40, 38 is `lightunique`'s 98 capped at 77 by `0x005C9290` (which writes the cap back to the range and frames left), 10 is class 408's `Range` 20 under `0x005AC040` (no write-back, a cap at 255 first). `[C]`, run:2026-11-03-path-emu-3 and 654 of 654 game creations (`p3-h1log.txt`). The planner stays a value oracle in skills/README and skills/missiles only until `path/search` is reviewed (plan 0054 P3): take the H1 and H4 text now, the oracle row then, after this batch's review. Not blocking.
