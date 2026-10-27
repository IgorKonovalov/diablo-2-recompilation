---
from: architect
to: reverser
date: 2026-10-27
status: open
context:
  - ../plans/0045-skills-missiles-machinery.md#implementation-log
  - ../findings/skills/0002-missiles.md#12-plan-0045-phase-2-part-2-the-run-run2026-10-27-skills
resolution: ""
---

Plan 0045 case C2 (the `VelLev` term, skills/0002 § 12) stays `[I]`: part 2's 22 `spike2` creations were all at level 1, where `(7 · 1) / 8` is 0. Ruled at the `lane/p45k` review (ruling (b)): no Nightmare/Hell session. A `spike1` (`VelLev` 8, `Vel` 10; MonStats `quillrat1`'s `MissA2`, a table reading, the creation path not read) separates already at level 1: the read `((VelLev · lvl) / 8 + Vel) << 8` gives 11, the lead's `VelLev · (lvl − 1) + Vel` gives 10. `quillrat1` is in the pool of level 2 (Blood Moor) in all three difficulties. Not blocking and no session of its own: when a harness lane with the skills logger (rev 5) passes Blood Moor, keep the log and run `tools/skills.py check` on it; `MC.vel` checks every creation. A `spike1` creation with 0 mismatches raises C2 at its level. Close this entry with the run, or leave it open.
