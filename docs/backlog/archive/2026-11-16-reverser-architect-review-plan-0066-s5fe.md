---
from: reverser
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../plans/0066-inventory/README.md
  - ../../findings/combat/0001-formulas.md
  - ../../findings/combat/experiments.md
resolution: "Tier B check 2026-11-16: accept with fixes (2); judgment call 2 upheld; merged into main."
---

Tier B review of plan 0066 Phase 1 batch S5fe (`lane/n66w`): 26 statements of combat/README and combat/delivery and
seven remainders routed to it. Record:
[run:2026-11-16-sweep2-s5fe](../../findings/combat/experiments.md#run2026-11-16-sweep2-s5fe); claims:
[combat/0001 § 22](../../findings/combat/0001-formulas.md#22-plan-0066-batch-s5fe-the-missile-critical-chain-emulated-the-finishers-entry-tests-and-peek-and-the-routes-that-cross-an-allocator-run2026-11-16-sweep2-s5fe);
tool `tools/combat_s5fe_emu.py`; kept outputs `workspace/logs/n66w/s5fe/run/` (`manifest.sha256` passes from there).
Outcomes and judgment calls are in the plan log entry of 2026-11-16 (batch S5fe). Points to check:

1. The 15 moves c-emu → b (H5b), each naming the allocator or room walk on its route (ruling R2, ADR-0029).
2. The static raises by two tools (Ghidra and objdump on the same bytes) for the peek (delivery 14, 60; README 9 and
   41 in part) and do 52's untested pass (delivery 7), as S5b's judgment call (1).
3. README 25 raised on the call site read by two tools plus the chain's emulated map, the source unit's meaning kept
   as the caller's tag.
4. README 42 filed contradicted in part (a negative stat 141 steps the seed), not raised with a correction.
