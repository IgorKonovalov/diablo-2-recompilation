---
from: architect
to: reverser
date: 2026-10-27
status: done
context:
  - ../../findings/skills/0002-missiles.md
  - ../../specs/skills/missiles.md
  - ../../plans/done/0045-skills-missiles-machinery.md#implementation-log
resolution: "lane/rbd 2026-10-27: folded into [skills/0002 § 6](../../findings/skills/0002-missiles.md#6-the-packet-at-the-hit-missile_builddamage) at [I]: every bound and the mastery read on the missile (ESI from the first stack argument, 0x005A89B9; MissileElemRoll's EBX, 0x005A891C/0x005A8937/0x005A895F; the missile at MISSILE_HitUnit's call 0x005AE150; seven other callers unfollowed), the bounds tested > 0 before the mastery, an inverted pair swapped (0x005A894B–0x005A8951, physical 0x005A89EB–0x005A89F1). tools/skills.py's bd swaps now (test_bd_swap both ways); the re-check of both runs' 33 logs gives 4 118 builds, 0 mismatches, no inverted pair. Whether a missile carries its owner's masteries is still unknown: none of the 54 655 MH0 lists holds one (§ Open questions, [L])."
---

**skills/0002 § 6 (`MISSILE_BuildDamage`): two readings to fold in.** Found at the 0045·P3 review (objdump, pinned image): (1) every bound and the mastery stat are read on the **missile** (`STATS_GetUnitStat` with the missile at `0x005A891C`, `0x005A8937`, `0x005A895F` in `sub_005A8910_MissileElemRoll`, and `0x005A89C4`/`0x005A89D9` for the physical pair), which § 6 leaves unsaid and the first spec draft gave as the owner's; `tools/skills.py`'s `bd` reads the missile's stats too. (2) a pair whose minimum is above its maximum is **swapped** before the mastery and the draw (`0x005A894B`–`0x005A8951`, physical `0x005A89EB`–`0x005A89F1`), and the bounds are tested `> 0` before the mastery is added; § 6 omits both. No build of run:2026-10-25-skills had an inverted pair (the checker does not swap and found 0 mismatches). Fold both into § 6 at `[I]`; skills/missiles F1 already states them at `[I]` from the review's reading. Whether a missile's stat list carries the owner's masteries (329–332, 357) is open; a logged build with a non-zero mastery would settle it.
