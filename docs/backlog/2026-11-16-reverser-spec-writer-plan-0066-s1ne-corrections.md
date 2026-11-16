---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../findings/ai/experiments.md#run2026-11-16-sweep2-s1ne
  - ../findings/ai/0001-machinery.md#14-plan-0066-batch-s1ne-part-1-twelve-maps-emulated-the-routes-read-2026-11-16-lanen66ne
  - ../plans/0066-simulation-inferred-claims-sweep.md
resolution: ""
---

[2026-11-16] from reverser → spec-writer: plan 0066 batch S1ne part 1 (`lane/n66ne`) corrects or refines six
statements of [monsters/ai/README](../specs/monsters/ai/README.md) and [machinery](../specs/monsters/ai/machinery.md).
Carry them into the spec text at the Phase 3 re-tag of the monsters/ai cluster (line numbers at `b5999f5e`). The
evidence is [ai/0001 § 14](../findings/ai/0001-machinery.md#14-plan-0066-batch-s1ne-part-1-twelve-maps-emulated-the-routes-read-2026-11-16-lanen66ne)
and [run:2026-11-16-sweep2-s1ne](../findings/ai/experiments.md#run2026-11-16-sweep2-s1ne). Not blocking.

1. README L205 (C4 `MonAiDelayEarlier`): `n` becomes 1 only when it is 0, and a negative `n` is kept (`T + n`), so it
   is not `max(n, 1)`. The "at or after `T + n`" test is an unsigned `cmp; jb` (0x005DE15F). C2 and C3 (`MonAiIdle`,
   `MonAiDelay`) say `max(n, 1)` too. Those were not run, so read them before rewording.
2. README L193 (C1 `MonModeStartNeutral`): when the unit is not under state 21 and has no MonStats pointer in its
   MonsterData, it returns 1 and queues nothing (7 cases in the run). The same exit for a unit with no MonsterData, or
   one that is not a monster, comes from objdump only (0x005A7430–0x005A7444) and was not run.
3. Machinery L319 (D2 `MonAiPathOverride`): for a unit with no MonsterData, `AiPathOverrideSet` gets `ECX` 0, and a
   non-zero word is then written through a null pointer (0x005DE1CE).
4. Machinery L168 (A7): `AiDistToPointSized` subtracts `(size >> 1) + 1` with an unsigned `shr`, so a negative
   MonStats2 size is not halved as a signed value. `UNIT_GetSizeX` for a monster is the MonStats2 `+0x08` signed byte.
5. Machinery L580 (T22a): `MONSTATS_IsUndead` is MonStats `+0x0D` bit 3 or bit 4 (`lUndead` or `hUndead`).
6. Machinery L504 (T13a): `AiDeadMinionCb` computes `AiDistUnits(searcher, candidate)` before its null and type
   tests.
