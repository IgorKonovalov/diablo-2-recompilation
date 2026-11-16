---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/combat/0001-formulas.md
resolution: "Applied at plan 0066 Phase 3, combat cluster (lane/n66y): combat/README note 5, delivery A3 and its note 8, README B5's UnitMsgA3 writes ([plan log](../../plans/0066-simulation-inferred-claims-sweep.md#2026-11-16--phase-3-the-combat-cluster-re-tagged-spec-writer-lanen66y))"
---

Plan 0066 batch S5fe (`lane/n66w`) found these against the combat specs at `b5999f5e`
([combat/0001 § 22](../../findings/combat/0001-formulas.md#22-plan-0066-batch-s5fe-the-missile-critical-chain-emulated-the-finishers-entry-tests-and-peek-and-the-routes-that-cross-an-allocator-run2026-11-16-sweep2-s5fe),
run:2026-11-16-sweep2-s5fe). Not blocking; for Phase 3's re-tag of combat/README and combat/delivery.

1. **Contradicted in part, combat/README line 501** (Reimplementation notes, "Its deadly strike and mastery steps
   still need a chance above 0"). The deadly-strike step needs a **non-zero** stat 141: a negative value steps the
   owner's seed and cannot succeed (565 separating cases; B4's own pseudocode at line 316 already says `≠ 0`). The
   mastery half holds: the mastery value is a maximum starting at 0, never negative.
2. **Correction, combat/delivery line 237** (A3, "The finisher's own step is a peek"). `RNG_Step` runs on the
   attacker's own seed (`ECX` = attacker + 0x20, 0x005D537B), not on the copy; `Copy64Out` saved the two words first
   and `Copy64In` writes them back (0x005D5374, 0x005D538C). The net state is the same (the seed leaves as it entered).
3. **Refinement, combat/README line 377** (B5, `UnitMsgA3` "changes no game state"). `UnitMsgA3` allocates its
   message (0x0040B430 at 0x00571AC1), links it into the unit's message list (`+0xEC`, `+0xF0`) and calls
   `sub_0064C040_UnitMarkUpdated`; the statement should say what it writes, whatever is meant by game state. The row
   stays `[I]` (moved to H5b).
