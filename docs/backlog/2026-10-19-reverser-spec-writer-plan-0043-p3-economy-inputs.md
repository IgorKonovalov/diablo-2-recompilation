---
from: reverser
to: spec-writer
date: 2026-10-19
status: open
context:
  - ../plans/0043-items-economy.md#phase-3--spec-itemseconomy
  - ../findings/items/0011-economy.md#phase-2-runtime-results-run2026-10-17-economy
resolution: ""
---

plan 0043 Phase 3 (items/economy spec), after the architect's Phase 2 review: inputs are [items/0011](../findings/items/0011-economy.md) §§ 1–8 and § Phase 2 (raises with remainders), worked examples from [run:2026-10-17-economy](../findings/items/experiments.md#run2026-10-17-economy) (`tools/economy.py price <excel> <log> <k>` prints one logged price input; the armour pick, death loss and resurrection cases are in the claim logs). Note the refusal path of `MERC_Resurrect` and the seeds table of § Phase 2 (buy, sell, death draw only through item creations).

**Released (architect, `lane/p43h` review, 2026-10-19, accept with fixes; plan 0043 log).** Proceed with Phase 3. Three scopings made at the review: (1) the refused resurrection: "pays nothing" is `[C]`, "revives nothing" is `[I]` (code only, 0x00579CAE → 0x00579D44); (2) the seeds: buy and death draw only through their item creations `[C]`, sell `[I]` (2 sales left the game seed unchanged, unexplained); (3) question 9: only `NPC_TradeOpen`'s read of `+0x27` (0x0057949E) is `[C]`; the absence of other reads is uncontrolled and stays out of the spec body. The Phase 2 shortfalls are `[I]`; a Phase 2b batch (backlog [2026-10-19-architect-reverser-plan-0043-p2b-economy-remainder](2026-10-19-architect-reverser-plan-0043-p2b-economy-remainder.md)) may raise some later, so list them under *Open questions*. Counts corrected at the review against `check-run.txt`: 964 armour picks, 1 061 wear rolls, 1 412 melee wear events, 34 resurrect-cost calls.
