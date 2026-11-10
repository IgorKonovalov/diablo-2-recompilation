---
from: architect
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../plans/done/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S4-rerun.md
  - ../specs/drlg/maze.md
resolution: ""
---

**drlg/maze § F, the cave specials (plan 0064 Phase 5, S4-rerun row 20).** The type 3 row reads "`r`; Prev; 8: Den of Evil, else Down; 9: + Coldcrow; 10: + Next". A clean-room reader could not tell whether "+" adds to the base list (Prev, Down) or to level 9's (Prev, Down, Coldcrow); it guessed the base, and the observed level-10 maze cases of the v1 set (0 different on both the Phase 2 and the Phase 5 run) agree. Write each level's specials in full and in order (8: Prev, Den of Evil; 9: Prev, Down, Coldcrow; 10: Prev, Down, Next; 11 and 12 as the finding has them), from [drlg/0006 § 6](../findings/drlg/0006-maze.md) and the cave entry tables at 0x00672550; keep each level's tag as the finding and the runs give it (drlg/0006 tags 10–12 `I` in its table; the spec row says `[C]`: state what raised them, or split the tag). Wording only; no new finding needed unless the tag split shows one.
