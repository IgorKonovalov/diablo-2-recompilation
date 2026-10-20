---
from: architect
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../specs/monsters/spawn.md#inputs-and-oracles
  - ../findings/chain/0001-oracles.md#5-spec-text-that-lags-the-models-for-phase-3
resolution: ""
---

Plan 0048 Phase 0 review (`lane/p48a`): the *grid snapshot at pass entry* row of [monsters/spawn § Inputs and oracles](../specs/monsters/spawn.md#inputs-and-oracles) says "The object marks are still logged values ... not yet fed to the collision model (plan 0023 Phase 2 ruling)". Plan 0027 Phase 2 modelled them: all 1847 object marks of run:2026-10-15-objects are predicted ([objects § Inputs and oracles](../specs/objects/README.md#inputs-and-oracles), object marks row; [drlg/collision § Inputs and oracles](../specs/drlg/collision.md#inputs-and-oracles)). Correct the row: the object marks are modelled; what stays a value oracle is the rest of the snapshot (players, walk-ins, items, corpses), oracle 20 of [chain/0001](../findings/chain/0001-oracles.md). This one is a wrong statement in a reviewed spec, so it need not wait for plan 0048 Phase 3; the other four passages of chain/0001 § 5 are Phase 3's.
