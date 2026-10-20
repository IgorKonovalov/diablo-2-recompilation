---
from: reverser
to: reverser
date: 2026-10-17
status: done
context:
  - ../../findings/items/0011-economy.md#leads-used
  - ../../plans/done/0043-items-economy.md#implementation-log
resolution: "all five reproduced in run:2026-10-17-economy (case 1: W and 963 of 963 armour picks with 3/5/4/4/2/2/2); items/0011 § Phase 2 [../findings/items/0011-economy.md#phase-2-runtime-results-run2026-10-17-economy]"
---

plan 0043 Phase 2 required cases from the Phase 1b contradicted leads (items/0011 *Leads used*): (1) armour wear slot weights: `g_ArmorWearSlots` 3/5/4/4/2/2/2 against src:maxroll-d2r-items 2/3/2/1/1/1 (P2 question 10, the `RangeB` pair and the slot picked); (2) an ethereal item's sale value `S/4` against "25 % less" (question 1); (3) an ethereal throwing stack's sale value against "always 1 gold" (question 1); (4) an all-resistance magic item's affix term over 1024 for `S` against "4096ths for sell" (question 1); (5) the computed gamble price against `gamble cost` (question 2, any non-ring base). Not a case: Books `BaseCost` (equal to the Misc `cost` on stock data).

*2026-10-17 (reverser, `lane/p43h`):* cases 2–5 reproduced in [run:2026-10-17-economy](../../findings/items/experiments.md#run2026-10-17-economy)
(29 ethereal sale inputs with `S / 4`; the ethereal throwing stack sold for 1 040 at 15 NPCs; 16 all-resistance sale
inputs over 1024; 55 of 55 computed gamble prices). Case 1 (armour slot weights) waits for a wear session; the entry
stays open until Phase 2 closes.
