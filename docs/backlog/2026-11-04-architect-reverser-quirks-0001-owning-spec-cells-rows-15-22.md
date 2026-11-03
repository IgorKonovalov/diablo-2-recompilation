---
from: architect
to: reverser
date: 2026-11-04
status: open
context:
  - ../plans/0057-quirks-catalogue.md#implementation-log
resolution: ""
---

From the `lane/s68` Tier A review: [quirks/0001](../findings/quirks/0001-community-bugs.md) is yours, three edits. (1) *Owning spec* cells still reading "none" for rows the specs now own: rows 1, 2 and 7 skills/catalogue (§ M, § M, J2), row 3 and 4 skills/dispatch I4, row 6 skills/catalogue J2, row 13's "the effect none" combat/delivery B4, row 17's "the sum none" combat/to-hit A2, row 18's "do 74's add none" skills/catalogue K14; rows 9 and 30 stay "none" as open questions. The intro's sentence about "none" goes with it. (2) Row 15: its `[C]` for the formula covers "so `cb` is 0 at 100 or more", and no kept combat log has a crushing blow at stat 36 of 100 or more (the logs met 15 to 90; the review's survey, in the plan log). Scope it as combat/delivery E1 now does: `[C]` for the cut at the values logged, `[I]` for the cap, `cb` = 0, the absence of a branch on the defender's kind and the player's divisor. (3) Row 22: name the runs. The stop is logged deciding 4 calls, all Duriel's (one in run:2026-10-12-quality, three in run:2026-10-16-quest-drops), and Duriel's `Picks` 7 is on the `- Base` rows under a `Picks` 5 row; items/tc `MAX_DROP` has the split. No code to read for any of the three.
