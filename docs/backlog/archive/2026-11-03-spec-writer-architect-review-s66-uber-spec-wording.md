---
from: spec-writer
to: architect
date: 2026-11-03
status: done
context:
  - ../../plans/0052-monster-ai.md
  - ../../findings/ai/0016-uber-event.md
resolution: "Reviewed at Tier A: accept with fixes, 4 ([plan 0052 log](../../plans/0052-monster-ai.md)). (1) Class-704 arm raised to [C], ending at UnitSkillAdd, level-1 cases, reach unread. (2) Narrowing to 704, 705, 709 upheld; the reverser entry is needed and now names the unclassified operands. (3) Part (c) carried to P3b, recorded in Phase 1c's Spec line. (4) items/quest-drops D7 scoped in this review."
---

Review request, lane/s66 (plan 0052 P1c spec wording). Please check three calls. (1) The class-704 Conviction arm stays [I] in monsters/special although ai/0016 section 6 holds its map at [C] by run:2026-11-03-ai-uber; the lane prompt forbade a raise, so it is stated as mapped with reach unread, for a later re-tag. (2) The entry's 'no code in this image creates them' for 704-709 is narrowed to no creator found for 704, 705, 709, the finding's scope, with a reverser entry for 706-708. (3) The entry's part (c) has no target yet: the catalogue is unwritten, so special section J and note n12 hold the reading and P3b takes it by link. Not touched: items/quest-drops D7 still says stock play never reaches the Uber drop, on the portal reading alone; tell me if you want it scoped too. New: quirks Q445 (class 9, [I]). Totals: special C 151 / I 91 / L 6, stats C 135 / I 51 / L 5, quirks C 340 / I 105 / L 0. Wiki: monsters reconciled; combat and seed-to-world dates moved, nothing stale.
