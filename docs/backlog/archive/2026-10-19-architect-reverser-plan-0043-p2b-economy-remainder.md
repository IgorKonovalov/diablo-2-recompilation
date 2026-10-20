---
from: architect
to: reverser
date: 2026-10-19
status: done
context:
  - ../../plans/0043-items-economy.md#implementation-log
  - ../../findings/items/0011-economy.md#phase-2-runtime-results-run2026-10-17-economy
resolution: "Done by lane/p43b (run:2026-10-19-economy2), reviewed 2026-10-19: accept with fixes (plan 0043 log)."
---

plan 0043 Phase 2b (harness, 1 slot; from the Phase 2 review, 2026-10-19). Close the stock-reachable shortfalls of Phase 2's *Done when* that are not rare branches, each with logs under `workspace/logs/` on the same manifest (repository-root paths) and `tools/economy.py check` at 0 mismatches: (1) a crafted item's price (quality 8; a `d2s.py` recipe), buy/sell/repair; (2) the repair price in Hell (mode 3, difficulty 2); (3) the gamble price at clvl 3 (EconDL3, built, not run); (4) a partial repair (gold short) and an ethereal and a broken item at a repairer; (5) the quest repair named by the *Done when*: name its path in `Game.exe` or state with the scan that 1.14d has none (items/0011 names none); (6) Wirt's gold (`sub_00594630_A1Q4_WirtGold`, the 10–19 piles and their ilvl); (7) question 9 rerun with a control that fires to the session's end (no 40-line cap, or a sampled control), over Charsi's repair, repair-all and other NPCs' windows, to raise or leave the `+0x24..+0x26` absence; (8) the two sales that left the game seed unchanged (4311 line 29206, 4332 line 5963): log what the store does instead of the copy. Optional if cheap: a `UseCharge` event, Cain's free identify. Phase 3 does not wait for this; the spec states these `[I]` and is updated when 2b lands.
