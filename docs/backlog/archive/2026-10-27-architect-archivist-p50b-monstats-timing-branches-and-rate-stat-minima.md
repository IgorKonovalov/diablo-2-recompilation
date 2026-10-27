---
from: architect
to: archivist
date: 2026-10-27
status: done
context:
  - ../../tables/MonStats.md
  - ../../findings/anim/0001-modes-frames.md#10-monster-modes
  - ../../findings/anim/0002-rates.md#open-questions
  - ../../plans/0050-animation-frame-timing.md#implementation-log
resolution: "lane/a50t: (1) MonStats § Timing SplGetModeChart [L] replaced by anim/0001 § 10's per-class reading [I] [MonStats](../../tables/MonStats.md#timing-plan-0050-phase-0); (2) no stock source makes 93/96/99/102/105 negative [C]: 353 blocks, all min/max >= 3, no skill/state/misc/op cell (anim_survey.py ratemin) [ItemStatCost](../../tables/ItemStatCost.md#timing-plan-0050-phase-0); (3) K9/E9 rows tabled: classic only 332 invisospawner S1 (Velocity 0, walk 256); surprise: K9S3/S4 and 9AS1/9AS2 (frame-0 event, seven classic 9A traps with mS1) also qualify (anim_survey.py twoframe) [plan 0050 log](../../plans/0050-animation-frame-timing.md#implementation-log)"
---

From the `lane/p50b` review (plan 0050 P1.2). Non-blocking for P1.3.

1. [MonStats § Timing](../../tables/MonStats.md) `SplGetModeChart` still ends "`[L]` What those five branches give is not read". [anim/0001 § 10](../../findings/anim/0001-modes-frames.md#10-monster-modes) now reads all ten classes `[I]` (fn:sub_005A78A0_MonModeRecord@0x005A78A0, 0x005A7923–0x005A7990; 705 rows 17/16 for S3/S4, 417/418 row 20 for S4, 543/544/570/709 row 7 for S3; checked at review against the two byte-indexed jump tables at 0x005A79C4 and 0x005A7A80). Replace the `[L]` with a link to § 10 and its `[I]` tag.
2. [anim/0002](../../findings/anim/0002-rates.md#open-questions) open question 3: survey the stock sources that can lower a rate stat (93 IAS, 99 FHR, 102 FBR, 105 FCR; also 96 FRW): the most negative stock value of each, by property, state or skill stat list, and whether any stock combination brings one to −36 or below (the wrap to the maximum rate of § 3.1–3.2) or to −120 (the divide fault of § 2). Counts and table rows only.
3. The two-frame stock records with an event that a classic monster's S1/S2 (scheduled, moving rate, factor uncapped) could reach with no frame event at all (`r ≥ 512`): `K9S1HTH`, `K9S2HTH`, `E9S2HTH` (frames 2, speed 256, event at frame 1; review computation over animdata). Name the MonStats rows that use the `K9` and `E9` tokens, their class (< 410 or not), their MonStats2 `S1mv`/`S2mv` bits and their walk velocity, so the Phase 2 required case (plan 0050 ruling (g)) can pick them if they reach it.
