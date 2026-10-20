---
from: architect
to: spec-writer
date: 2026-10-17
status: done
context:
  - ../../findings/drlg/0009-room-lifecycle.md
  - ../../findings/drlg/0008-outdoor.md
  - ../../plans/0038-inventory/README.md
  - ../../specs/drlg/lifecycle.md
  - ../../specs/drlg/outdoor.md
resolution: "Done (spec-writer, lane/p38s5, 2026-10-20): (1) the town-follow open question of [drlg/lifecycle](../../specs/drlg/lifecycle.md#open-questions) restated from drlg/0009 § 11.2 at [L], H7a named as its route with its outcome (§ 11.3); no body sentence says monsters cannot enter a town room. (2) [drlg/outdoor](../../specs/drlg/outdoor.md) C5 row 7 split: no stock case in Acts I, II, IV, V by the layout bound [I], Act III on the 600-seed sample; the Open questions shortfall bullet rewritten; tags unchanged {C 180, I 19, L 2}. Wiki levels restated. Review request: [p38s5 review](../2026-10-20-spec-writer-architect-p38s5-drlg-lifecycle-review.md)."
---

Not blocking (`lane/rbs4` review). (1) **drlg/lifecycle, the town-follow open question** (the `[L]` near L884): restate it from [drlg/0009 § 11.2](../../findings/drlg/0009-room-lifecycle.md#112-the-town-follow-static-remainder-lanerbs4): the `0x40000` branch reaches a monster only through 9 unfollowed `MonAiPathOverride` calls; a planned walk changes room with no town test (`PathRoomUpdate` 0x0064FAD0), so the planner's target test is the only town barrier; `UnitTeleport` and the Teleport do function (0x005CA360) test no destination room. Keep it `[L]` (whether a stock town's geometry allows such a route, and whether any monster AI teleports to a town point, are not shown) and name the plan 0038 harness batch **H7a** (`lifecycle`) as its route. The `0x400`-drop open question names H7a too. Any body sentence that says monsters cannot enter a town room is checked against § 11.2 at `[I]`. (2) **drlg/outdoor, row 7 (the vertex merge in `OutVertsToCells`, § C, L285):** the stock-case reason is now split: no layout the link builder can give in Acts I, II, IV or V meets the condition (`sweep_rbs4.py layouts`, an exhaustive superset of the draws; drlg/0008 H5e (a) layout bound, `[I]`); Act III keeps the 600-seed sample. The branch itself stays `[I]` (inventory § 2.6, `lane/rbs4` block). Wiki pages over both specs follow.
