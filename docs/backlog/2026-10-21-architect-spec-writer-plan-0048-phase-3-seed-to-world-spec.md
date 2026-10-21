---
from: architect
to: spec-writer
date: 2026-10-21
status: open
context:
  - ../plans/0048-seed-to-world.md
  - ../findings/chain/0001-oracles.md
  - ../findings/chain/0002-retirements.md
  - ../findings/chain/0003-end-to-end-run.md
  - ../findings/chain/experiments.md
resolution: ""
---

Plan 0048 Phase 3 is released (Phase 2 accepted with fixes 2026-10-21, `lane/p48r2` review). Write `docs/specs/chain/README.md` from the template: the composition from the game seed to a populated level and a drop as a sequence diagram; the inputs a reimplementation supplies, by class, from chain/0001 (with oracle 25, the restored monster's class, cell and state, which run 2 takes for each revisit re-creation) and the counts of [run:2026-10-21-chain2](../findings/chain/experiments.md#run2026-10-21-chain2); each subsystem's entry contract (seed, arguments, state read) by link; worked examples from the run. Update each core spec's *Inputs and oracles* table where Phase 1 retired an oracle (chain/0002; a link to the model, not a restatement), and the revisit re-creation's marks in the collision or lifecycle spec from chain/0003 § 2 (marks `[C]` on 1 903 compared, the dead sequences on the 140 outside r2-xn1; the call path `[I]`). Carry into *Open questions*: the chest interact-byte writer (chain/0003 open question 2; three kinds, 7 cases, a counted oracle of the operate path, run-1 review ruling 3) and the parts of oracle 13's MonEquip model the stock table cannot reach (chain/0002 § 11). Then Phase 4 (wiki).
