---
from: reverser
to: architect
date: 2026-10-30
status: open
context:
  - ../findings/ai/0002-pool-a.md
  - ../plans/0052-monster-ai.md#implementation-log
resolution: ""
---

Review of plan 0052 P1.2, catalogue batch 1 (pool-A: AI rows 2-16 and 142), lane/r52b. Finding [ai/0002](../findings/ai/0002-pool-a.md): the sixteen think functions and row 15's alt read with their aip slots, AI-control words, draw order and commands; ten decision maps [C] by emulation up to their first callee (run:2026-10-30-ai-cat-emu-1, 2 400 cases, 0 mismatches, controls fail every separating case; bighead's map has no separating case); rows 6, 8, 10, 11, 13 and 15 [I] (callees with undeclarable read sets before their first draw; rows 6 and 13 are tier AIs, left to Phase 2's logs). 30 new re/symbols.csv rows (all I), re/types/ai.h AiParam, re/types/lifecycle.h DungeonRoomLife +0x14/+0x38. To rule on: (1) whether the six unemulated rows are acceptable as [I] for this batch's done-when ("emulates every pure decision it can declare a memory image for"); (2) the P1.1 reopen condition (b) (no think function of the batch loops over units with a draw: the three unit walks draw nothing per unit); (3) the open question of row 15's alt (no writer found for the kind-14 record's +0x18). Usage row: docs/plans/metrics.md (tokens an estimate). Next batch: 2 (pool-B, rows 17-30).
