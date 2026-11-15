---
from: reverser
to: spec-writer
date: 2026-11-15
status: open
context:
  - ../findings/ai/experiments.md#run2026-11-15-sweep2-s1e
  - ../plans/0066-simulation-inferred-claims-sweep.md
resolution: ""
---

[2026-11-15] from reverser → spec-writer: plan 0066 batch S1e (`lane/n66e`) corrects six catalogue statements; route them
to the spec text at the Phase 3 re-tag of [monsters/ai/catalogue](../specs/monsters/ai/catalogue.md) (line numbers at
`b5999f5e`; evidence in [ai/experiments, run:2026-11-15-sweep2-s1e](../findings/ai/experiments.md#run2026-11-15-sweep2-s1e),
*Corrections* 1 to 6). Not blocking.

1. L3916–3917 (R51 `pick(w, n)`): a sum ≤ 0 takes `r = 0` with no step and still scans, so a positive prefix returns
   its `k`; the fallback only when no running sum exceeds `r` (0x005FC153). The inline copies are read only (`[I]`).
2. L3593 block (R129 `AiGenSpawnPickClass`): with `n` = 0, no draw, but entry 0 is still tested (0x005E6075); the first
   store `453 or −1` (0x005E6054) is dead, every exit storing `*out` again.
3. L58 (Notation table) and L4689 (Reimplementation notes, "Two life readers … Keep them apart"): `AiLifePct` is
   `push ecx; call UnitLifePct; ret` (0x005DD280), one map with two calling conventions. The same sentence is
   [quirks Q515](../specs/quirks/README.md) and [ai/0002 § 2.10's note](../findings/ai/0002-pool-a.md) (corrected there).
4. L2697 (R50c): the first draw only when `blk[3]` ≠ 0 (0x005F780B); with no find and `blk[5]` 0 (a monster searcher; the one-caller claim is `[I]`), no draw and `t`.
5. L687 (R23b): "not dying" is `MonIsDeathMode`, 0 for every player; ties replace (`≤`).
6. L2031 (R105 block head): 0, 1 or 3 draws, not three per tried skill; the fourth argument `melee` is never read.

The findings' copies carry dated correction notes: ai/0002, 0003, 0006, 0008, 0011, 0012.
