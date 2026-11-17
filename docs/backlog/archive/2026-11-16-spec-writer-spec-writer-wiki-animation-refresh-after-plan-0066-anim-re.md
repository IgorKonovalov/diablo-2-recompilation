---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../wiki/animation.md
  - ../../specs/anim/movement.md
resolution: "Refreshed wiki/animation from anim/README, timing and movement (the run-to-walk turn now states movement D2's 75 turns in the drain's frame and the 6 later mode sets, open item removed; the monster strike's code 1 and 2 corrected) and wiki/quirks from quirks/README (class table recounted to 538 entries, the raised quirks stated confirmed)."
---

Plan 0066 Phase 3 (`lane/n66v`) re-tagged anim/timing, anim/movement and anim/README (updated 2026-11-16), so wiki/animation's `based_on` dates are stale (W4). Two paragraphs now understate the specs: the run's turn to a walk at 0 stamina is said to have an unexplained offset-1 frame in 6 of 81 cases (wiki/animation lines near 323 and the open item near 368); anim/movement D2 now states it `[C]`: the 75 turns step in the drain's frame and the 6 others are later phase-11 sets, not the drain's turn. Also wiki/quirks (quirks/README updated 2026-11-16: Q40, Q117, Q249, Q372, Q373, Q375 now `[C]`). Refresh both pages from the specs, with the stronger tags.
