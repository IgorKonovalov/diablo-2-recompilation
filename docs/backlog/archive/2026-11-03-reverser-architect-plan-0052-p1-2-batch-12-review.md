---
from: reverser
to: architect
date: 2026-11-03
status: done
context:
  - ../../findings/ai/0013-batch12.md
  - ../../plans/0052-monster-ai.md#implementation-log
resolution: "Tier A audit 2026-11-03: accept with fixes (6), recorded in plan 0052's implementation log. The six no-setter rows stay [I]; Phase 2's Done-when requires the AiCtl.state log with a live control. Phase 1c may start."
---

Review of plan 0052 P1.2, catalogue batch 12, the last (towns, NPCs and the state rows: AI rows 31, 32, 41, 42, 54, 58, 60, 62, 81, 88, 91, 99, 100; state rows 2, 3, 8-14, 17; no tier AI), lane/r52l (from main c34cb3cb; main a292a88f merged before filing). Finding ai/0013: 41 functions emulated, run:2026-11-03-ai-cat-emu-12 (tools/ai_cat_emu12.py, 9 840 cases, 0 mismatches, 0 stopped, 18 traced reads all accounted; controls le 205, cmp 272, u16 7, lo8 47, arg 1 255 separate and fail; d0 separates none because no emulated path reads the difficulty before a boundary, stated; site control passes none; dev-1 result=FAIL with its tool copy). Setters named, five register sites resolved, catalogue recount 148 + 18, rows left short: none. For the check: (1) state rows 2, 3, 8, 9, 14, 17 are [I] no setter, scoped in ai/0013 section 3: a store through a longer pointer chain outside the two AI ranges is not excluded, and no run observed the absence; is that scope enough to mark them dead for P3b, or is a Phase 2 log wanted? (2) AiNpcNearPlayer, row 54's near branch and row 58's v18 stay [I], since AiUnitSearch is the first call; the 25 quest callees are unfollowed; (3) row 99's unsigned position compare is read, not separated (16-bit positions); (4) states 4 and 7 meet the same scan, outside this batch, noted in section 3. 48 symbol rows (46 func, 2 data, all I), the commit subject's 49 is a miscount; re/types/ai.h names AiCtl+0x38; ai/0001 section 3 gained a dated note. Not blocking any lane but Phase 2 scheduling.
