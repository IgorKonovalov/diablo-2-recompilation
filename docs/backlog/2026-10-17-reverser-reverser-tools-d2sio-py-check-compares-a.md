---
from: reverser
to: reverser
date: 2026-10-17
status: open
context:
  - ../findings/save/0001-d2s-io.md#plan-0039-batch-p1b-2026-10-17
resolution: ""
---

[2026-10-17] from reverser → reverser: `tools/d2sio.py check` compares a written character stat with the writer's runtime base entry; apply the `CSvBits` clamp (unsigned `min(v, 2^bits − 1)`, signed range, as `D2S_WriteStats` does) before comparing, so that the 10 clamped entries of run:2026-10-16-player stop showing as differences ([save/0001 § Plan 0039 batch P1b](../findings/save/0001-d2s-io.md#plan-0039-batch-p1b-2026-10-17)). Not blocking.
