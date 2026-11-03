---
from: architect
to: reverser
date: 2026-11-03
status: open
context:
  - ../findings/ai/0012-batch11.md
  - ../findings/ai/0013-batch12.md
  - ../plans/0052-monster-ai.md
resolution: ""
---

Four dated notes on two reviewed findings, from the Tier A review of `lane/a66`. Not blocking. Each pointer below is the review's reading of the kept tools and objdump, to be read again, not copied. (1) ai/0012 § 4 exempts "Baal's curses" from the sign tests with no control and the `bact` row has `u16` 6, but `tools/ai_cat_emu11.py`'s 6 separated cases (seed `r52k-bact`) all hold a negative `Skill6` (cases 48, 49, 70, 105, 113, 232); no case has a negative `Skill7` reaching its test on a player target with `Skill6` not above 0, the one shape in which the control could differ there. Narrow the sentence to `Skill6`, or add those cases to a kept run and say so; the tool docstring's "Skill6/Skill7" goes with it. MonStats states `Skill6` `[C]`, `Skill7` `[I]` meanwhile. (2) ai/0013 § 5 gives `h5b70` `u16` 7 without naming the test. The tool (`m_h5b70`, seed `r52l-h5b70`) reads `Skill1` unsigned; the 7 cases hold 0xFFFF or 0x8000 with a Skills count of 65536 and end in a return where the control casts. Name it, as ai/0011 names rows 130 and 141; MonStats states `[I]` until then, and the archivist may raise that one sentence afterwards. (3) ai/0013 § 2.1: whose class record `AiNearestPlayerCb` tests. Pointer: 0x005DDEB6 reads `[edi+4]`, `EDI` is the entry `EDX`, the same `EDI` pushed as the third word of 0x00544590 at 0x005DDEFD, so the searcher's; a null searcher, a class out of range or a null record take the bit-clear path (0x005DDEB4, 0x005DDEBB, 0x005DDEC9, 0x005DDED9). (4) ai/0013 § 2.5: the load widths of state 11. Pointer: `Velocity` `movzx` at 0x005E81DA, then `test dx,dx; jle` and `movsx edi,dx`, so it acts as s16; `Run` `movsx` at 0x005E81E3; `cdq; idiv` signed; the two `MS` lines of `b12-aip.txt` hold the loads. MonStats says the finding gives neither (3) nor (4); file an archivist entry when they land.
