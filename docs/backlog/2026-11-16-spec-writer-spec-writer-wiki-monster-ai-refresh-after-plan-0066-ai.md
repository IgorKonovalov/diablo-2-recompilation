---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../specs/README.md
resolution: ""
---

Plan 0066 Phase 3, the monsters/ai cluster part 1 (`lane/n66ai`), updated monsters/ai/README and monsters/ai/machinery
on 2026-11-16, so wiki/monster-ai carries W4. What changed for a reader: the tick's pass order, the AI context words,
`Idle(n)`/`Delay(n)` giving the next event at `T + n` (with 68 of 2 573 idles beaten by another queue), the table, its
row kinds and the state rows are confirmed by the logs or two tools; `MonAiInit`, the 10–12 gate, the pre-checks with
`MonAiKeepNear`, the forced target, the hostility test, the distances, the walkers, the override and the helpers' draws
are confirmed under emulation to their first callees; `MonAiDelayEarlier` turns 0 into 1 and keeps a negative `n` (not
`max(n, 1)`); `UModTeleportTry` draws up to twice on the unit's seed; curses are not the only setters of states 10 and 11;
row 20 Scarab now meets the H1 sentence. Refresh the page against the two specs (spec-writer review-fixes 1) and bump
`based_on`; the catalogue's re-tag (part 2) may change the same page, so one refresh after part 2 is enough. Not blocking.
