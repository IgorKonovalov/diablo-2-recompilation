---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../specs/sim/frame.md
  - ../../wiki/server-frame.md
resolution: "Note raised to [C] with H2c's anchors (the windows' 4 rooms), quirk Q506 [C]; wiki/server-frame left to the wiki refresh lane. 2026-11-17 (lane/fus) [../specs/sim/frame.md]"
---

sim/frame's Reimplementation notes keep "[I] The new-rooms flag is cleared after the walk, so a room created during its own act's walk waits (§ H2c)", while H2's block header is now [C] (all of H2, on one act) and H2c is [C] with the windows' 4 such rooms. The note reads as left behind by the frame re-tag (review-fixes 7, 8). wiki/server-frame keeps that trap under "read from the code" (review-fixes 1, the weaker of the two) until the note is raised or the spec says why it stays [I]. Not blocking.
