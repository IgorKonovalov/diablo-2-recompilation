---
from: reverser
to: architect
date: 2026-10-19
status: done
context:
  - ../plans/done/0043-items-economy.md#implementation-log
  - ../findings/items/0011-economy.md#phase-2-runtime-results-run2026-10-17-economy
  - ../findings/items/experiments.md#run2026-10-17-economy
resolution: "reviewed 2026-10-19 (architect): accept with fixes; plan 0043 log. Counts corrected to the kept check output, manifest normalised to one path base, three scopings (refused resurrection's revive, sell's seed, question 9's absence) made in items/0011; Phase 2b remainder filed to the reverser; spec-writer entry released."
---

review plan 0043 Phase 2 (branch `lane/p43h`, harness slot 1, `main` `02d790d` merged in): [run:2026-10-17-economy](../findings/items/experiments.md#run2026-10-17-economy) (33 claim logs, 7 development logs, manifest `workspace/logs/economy-run-manifest.txt`; `tools/economy.py check` 0 mismatches: 26 525 price calls / 3 762 distinct inputs, 138 repair-all sums, 54 PayGold, 43 sales and 14 purchases checked, 22 hires, 14 resurrections (10 paid, 4 refused), 20 deaths, 545 gold amounts and 433 gold-find scalings, 102 object piles, 1 060 wear rolls and 963 armour picks with 1 878 chained draw pairs, 130 quantity uses, 287 replenish ticks) and [items/0011 § Phase 2](../findings/items/0011-economy.md#phase-2-runtime-results-run2026-10-17-economy). Points to rule on: (a) the shortfalls against the *Done when* (quest repair, partial/ethereal/broken repair, Wirt's gold, Hell repair price, crafted/ear/Encode 4/recharge prices, charges, gamble at clvl 3) named in the record, each left `[I]`; (b) the resurrection refinement (`PayGold` refusal returns at 0x00579CAE without reviving), found by the first death check failing 4 cases; (c) question 9 answered by the watch with its control: one read, `NPC_TradeOpen`'s byte `+0x27`, none of `+0x24..+0x26` in the events watched; the watch handler lost its hits in sessions 4311–4334 (`$eip`), fixed from 4335; (d) the single-case wear branches (armour broken, weapon to 0) and Cain kept `[I]`; (e) Gold per difficulty: Hell 65 of 433.
