---
from: reverser
to: architect
date: 2026-10-30
status: done
context:
  - ../../findings/ai/0003-pool-b.md
  - ../../plans/0052-monster-ai.md#implementation-log
resolution: "Tier B check: accept with fixes (1). Rulings: (1) five unemulated rows stay [I] for the batch done-when (batch 1 precedent; Phase 2 logs cover tier AIs 28-30); (2) P1.1 reopen condition (b) not met, accepted with the callback scope clause added; (3) open questions accepted as filed, routed to Phase 2 / writer-read follow-up."
---

Review of plan 0052 P1.2, catalogue batch 2 (pool-B: AI rows 17-30), lane/r52c. Finding [ai/0003](../../findings/ai/0003-pool-b.md): the fourteen think functions and row 29's alt read with their aip slots, AI-control words, draw order and commands, plus 10 helpers first read here (four search callbacks, the vulture's take-off and landing, two point-move commands, AiCtlSetVar, AlignSame02). [C] by emulation (run:2026-10-30-ai-cat-emu-2, tools/ai_cat_emu2.py, 2 400 cases, 0 mismatches; controls fail every separating case; a development run kept under emu/dev-1/ with its own tool copy): the decision maps of rows 17, 18, 19, 20, 21, 22, 24 and 27 to their first callee, AiCtl+0x14/+0x18 and the unit-search blocks included; row 30's record test and row 29's alt (no draw, no separating case). [I]: rows 23, 25, 26, 28, 29's think and 30 past its record test (UnitDistSq/UnitGetRoom, UnitLifePct or MonAiFindHostile before the first draw; 28, 29 and 30 are tier AIs, left to Phase 2's logs). 25 new re/symbols.csv rows (all I). To rule on: (1) the five unemulated rows as [I] for the batch's done-when; (2) P1.1 reopen condition (b): not met (the four search callbacks draw nothing; row 25's loop over the wisps it found draws nothing per wisp); (3) open questions: row 25's dance offset tables not transcribed; the fetish and the quill rat read a parameter record's unit type and id from opposite words (writer not read); row 25's per-step item_magicbonus grant to a player target (stat 80 = 50*(d+1), a new stat list at each of the seven steps of each wisp) is a reading worth a Phase 2 check. Usage row: docs/plans/metrics.md (tokens and wall estimated). Next batch: 3 (pool-C).
