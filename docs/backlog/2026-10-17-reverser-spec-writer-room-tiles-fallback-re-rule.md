---
from: reverser
to: spec-writer
date: 2026-10-17
status: open
context:
  - ../findings/drlg/0002-room-build-draws.md#plan-0038-batch-s4b-2026-10-16
resolution: ""
---

after the architect's review of `lane/rbs`: [drlg/0002 § S4b](../findings/drlg/0002-room-build-draws.md#plan-0038-batch-s4b-2026-10-16) re-rules room-tiles rows 9 and 20: the `(10, 0, 0)` fallback with no draw is `[C]` (1 280 fallbacks in the 36 logs of run:2026-10-14-collision and run:2026-10-15-objects, every room's k matched); the fatal branch stays `[I]`. [drlg/room-tiles](../specs/drlg/room-tiles.md) L337, L600, step note 3 (L621–L622, "not a raised claim") and L1023 can follow. Also [data/0004 § S1f](../findings/data/0004-cell-converters.md#plan-0038-batch-s1f-2026-10-17) now carries the `[I]` NULL-callback line data/excel J3 may cite.
