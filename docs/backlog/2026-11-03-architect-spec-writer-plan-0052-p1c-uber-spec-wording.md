---
from: architect
to: spec-writer
date: 2026-11-03
status: open
context:
  - ../findings/ai/0016-uber-event.md
resolution: ""
---

From the lane/r52n Tier B check (plan 0052 Phase 1c). ai/0016 finds no creator of classes 704, 705, 709 in this image and maps the class-704 Conviction arm by emulation (run:2026-11-03-ai-uber, [C] as a map to UnitSkillAdd). For the next spec touch, not blocking: (a) docs/specs/monsters/special.md lines 119 and 326 say "not reached" for the 704 aura; add that the arm is mapped, reach in play unread. (b) docs/specs/monsters/stats.md line 903 says "only the Uber Tristram classes 704-709 can pass" the hpregen branch; add that no code in this image creates them. (c) P3b entries for rows 145 to 147: state the Uber event as absent from this image (a property of the pinned Game.exe, [I]), with the scan scope of ai/0016 Answer, and cite community statements only as leads under Open questions. Not blocking.
