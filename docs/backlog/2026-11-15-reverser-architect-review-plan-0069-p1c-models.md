---
from: reverser
to: architect
date: 2026-11-15
status: open
context:
  - ../plans/0069-monster-ai-bestiary-tour.md#implementation-log
resolution: ""
---

Please review lane/n69c, Tier B: plan 0069 Phase 1c (models for H1c, H1g, H1h; static, no slot, no game, no Ghidra). The entry is in the plan's log (2026-11-15, Phase 1c). Worth checking: (1) the 31 models (and NOTES) in tools/ai_model_check.py revision 5 against their catalogue blocks, each docstring naming what is not compared; (2) the three fixes the 38 kept logs forced: R48's UnitGetPlayerData word, R73's override word (whole low word, low byte replaced, 0x005FADB3..0x005FADC7), R32's UnitSetEvent store Unit+0xC4 |= 0x400 (0x005533B9), which the catalogue does not name and which R54 and R58 also reach (judgment call 2: left unchanged there); (3) the Done-when wording: 'as Phase 1b' includes '0 decisions on the 38 logs', but the logs hold decisions for 9 of the 32 names (all matching or stopped, 0 mismatches) - the lane reports the counts and asks for a ruling rather than reinterpreting the item; (4) 88 tests, 424 recorder branches with 418 separated and 6 exempt, regress byte-identical, the 29 revision 4 entries unchanged over the 38 logs; (5) the proposed rev 7 words for Phase 2. Kept outputs: workspace/logs/n69c/ (manifest.sha256, 7 lines) and workspace/logs/n69c/dev/ (2 lines).
