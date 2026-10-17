---
from: reverser
to: spec-writer
date: 2026-10-16
status: open
context:
  - ../findings/rng/0002-seed-tree.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk
  - ../plans/0038-inferred-claims-sweep.md
resolution: ""
---

[2026-10-16] from reverser → spec-writer (Phase 3): rng/seeds step note 2 is contradicted (run:2026-10-16-sweep-roomk, [rng/0002 § Plan 0038 batch H5c](../findings/rng/0002-seed-tree.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)): the command-line parser cuts a switch's value at the next `-`, so a negative `-seed` gives no override, and a positive value ≥ 2³¹ saturates at `0x7FFFFFFF`; no seed ≥ `0x80000000` comes from the command line. drlg/warps F1 (row 16) needs the `+0x2C` refinement (`LevelUnloadCheck` clears it). **Plan:** [0038](../plans/0038-inferred-claims-sweep.md) Phase 3 **rng/seeds part done 2026-10-16** (spec-writer, `lane/p38s`): step note 2 rewritten for the command line `[C]`, the `D2.ini` route an *Open questions* `[L]`. The drlg/warps F1 `+0x2C` refinement waits for the warps cluster (H5a); room-tiles § Release states it.
