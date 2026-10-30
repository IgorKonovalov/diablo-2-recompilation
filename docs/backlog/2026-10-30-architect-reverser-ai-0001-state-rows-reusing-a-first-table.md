---
from: architect
to: reverser
date: 2026-10-30
status: open
context:
  - ../findings/ai/0001-machinery.md#3-the-ai-table-and-its-dispatch
  - ../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review
  - ../plans/0052-monster-ai.md
resolution: ""
---

ai/0001 § 3 "The second table's bound" says "Seven state rows reuse a first-table think word: 1 Idle, 4 Hireable, 5 GoodNpcRanged, 7 NecroPet, 15 SuicideMinion, and 10 and 17, which share 0x005E8020". By the bytes (tools/ai_survey.py states; gate key st_fn8_in_first=5) five state rows repeat a g_MonAiTable +8 word; states 10 and 17 share 0x005E8020 with each other and with no first-table row. Please reword the sentence in your next ai/0001 touch (five reuse a first-table word; 10 and 17 share one of their own). MonAI.md § The second table already states it this way (lane/a7b audit, plan 0052 log). Not blocking.
