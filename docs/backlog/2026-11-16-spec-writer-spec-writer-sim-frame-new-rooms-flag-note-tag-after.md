---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../specs/sim/frame.md
  - ../wiki/server-frame.md
resolution: ""
---

sim/frame's Reimplementation notes keep "[I] The new-rooms flag is cleared after the walk, so a room created during its own act's walk waits (§ H2c)", while H2's block header is now [C] (all of H2, on one act) and H2c is [C] with the windows' 4 such rooms. The note reads as left behind by the frame re-tag (review-fixes 7, 8). wiki/server-frame keeps that trap under "read from the code" (review-fixes 1, the weaker of the two) until the note is raised or the spec says why it stays [I]. Not blocking.
