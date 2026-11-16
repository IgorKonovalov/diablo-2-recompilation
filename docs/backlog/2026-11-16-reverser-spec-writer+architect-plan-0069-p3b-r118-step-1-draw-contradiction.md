---
from: reverser
to: spec-writer, architect
date: 2026-11-16
status: open
context:
  - ../findings/ai/experiments.md
  - ../plans/0069-monster-ai-bestiary-tour.md
resolution: ""
---

Plan 0069 Phase 3b (lane/n69f), run:2026-11-16-ai-tour-3: catalogue row 118 (Succubus, fn:sub_005E1E00_AiSuccubus@0x005E1E00) step 1 as modelled (dist < aip(4) then chance(3), one draw at 0x005E1E4E, then step 2 or 4 each with its own draw) is contradicted by the log of t-a5-crystal: 12 checker mismatches (kept model-check.txt, workspace/logs/n69f/manifest.sha256), all with the unit seed one step behind the model (Idle seed after 1 step in the log, 2 in the model; the Walk/SetModeAtUnit calls the model chose from the second draw are Idle in the log). Probe tools/ai_r118_probe.py (r118-probe.txt): of the 25 decisions with dist < aip(4) and the rev 7 word logged, every one took exactly 1 seed step and none entered the curse arm; the 4 with 2 steps and the 3 that call UnitGetMaxHp are among the 7 without the word line. The word R118.flag0x20 (EAX at 0x005E1E34) reads 0 in all 33 lines, while the 25 near decisions that carry it behave as if the flag test had been taken, so either the word does not read what the row says or the flag at the test differs from it. Unresolved at the lane's time box; rows 347 and 348 stay [I]; the model's other branches (far case, 8 decisions) match. Needs a spec decision on the block and, to settle, a rev 8 word at 0x005E1E3C or a look at the call at 0x005E1E2F. R119 (0x005E2120) and R128 were not reached (no warp 81 in level 129; Halls of Vaught not entered), so they cannot confirm either side.
