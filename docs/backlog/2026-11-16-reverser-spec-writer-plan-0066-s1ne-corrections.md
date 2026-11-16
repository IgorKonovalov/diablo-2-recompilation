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

[2026-11-16] reverser (S1ne part 2, `lane/n66ne`): five more items for the same Phase 3 pass, on
[ai/0001 § 15](../findings/ai/0001-machinery.md#15-plan-0066-batch-s1ne-part-2-the-walkers-monaiuseseqskill-the-parameter-list-and-the-notation-2026-11-16-lanen66ne)
and [run:2026-11-16-sweep2-s1ne-p2](../findings/ai/experiments.md#run2026-11-16-sweep2-s1ne-p2).

7. Machinery E4 (`AiParamsFind`): the scan starts at the head's next record and ends with the head, so the head is
   examined last; with the kind at the head and elsewhere, the other record is returned.
8. Machinery B8b: `MonAiWanderRingDirect` centres on the unit itself and calls `MonSetMode(G, cmd, 1)` in WL directly,
   not `MonAiMove`; `MonAiWanderNearUnit` with a null other is `MonAiWanderRing(2)`; `MonAiRunNearUnit` takes RN, or WL
   with the override words cleared under state 60, tested after the draws. All three use `r & 0xFF` (also B8's odd
   branch, written `dx ← r`).
9. Machinery B4: `MonAiUseSeqSkill` calls `MonSetMode(G, cmd, 0)` (flag 0), and sets the used skill to
   `SkillFindByOwner`'s result even when it is 0.
10. Machinery B7: `MonAiWalkToUnitStop` and `MonAiRunToUnitStop` replace only the low byte of the stop word by 1 when
    that byte is 0; the high bytes pass to `MonAiMove` unchanged.
11. Machinery reimplementation note on row 125 (L1025): Skill1 is sign-extended (`movsx`, 0x005E378C) into
    `MonAiUseSkill`'s skill argument.

[2026-11-16] reverser (S1ne part 3, `lane/n66ne`, the closing part): five more items for the same Phase 3 pass, on
[ai/0001 § 16](../findings/ai/0001-machinery.md#16-plan-0066-batch-s1ne-part-3-monaiinit-monaiprechecks-aihostilecandidate-and-monaiforcedtarget-2026-11-16-lanen66ne)
and [run:2026-11-16-sweep2-s1ne-p3](../findings/ai/experiments.md#run2026-11-16-sweep2-s1ne-p3). Seven S1ne rows stay
`[I]` with their routes in the inventory (machinery 5, 6, 11, 12, 14; README 42, 43): no rewording for them.

12. README E1 (`MonAiInit`): the state-54 test (`UNIT_HasState(U, 54)`, fatal) comes before the null tests; "free the
    parameter records" acts on MonsterData `+0x28`'s control, not on the `ctl` argument; after the state and think
    stores the think is passed to KERNEL32 `IsBadCodePtr` and a non-zero return is fatal (0x005B0F30–0x005B0F43, a
    reading: the import was not run). "Returns without setting anything when a record is missing" holds, with the
    `+0x14/+0x18/+0x1C` clears and the free already done, as the pseudocode's order says.
13. Machinery A3 (`MonAiForcedTarget`): kind 0 returns 0 with no clear; a kind past 4 (unsigned) clears. The line test
    and the kind-6 search are chosen by the function's flag argument (non-zero), the kind-5 search by flag 0, not by
    the caller's name. The out distance is `AiDistUnits(found, unit)`, sized by the found unit.
14. Machinery A6 (`AiHostileCandidate`): the candidate's death is tested before the searcher's; a candidate with no
    room counts as not in town.
15. README F1 (`MonAiPreChecks`) and machinery § E (`MonAiKeepNear`): `KeepNear` clears `AiCtl+0x0C` to −1 when the
    class may not take mode 2, when the unit is not found or when it is dead; the distance compares (`> 1`, `> 20`)
    are signed, and `StepAway(found, 19, 1)` is taken only for a player (type 0), a monster at `d ≤ 1` returning 0.
16. README F2 (`MonAiOpenDoor`): the opendoors bit is MonStats `+0x0C` bit 3 of the `ctx` record (`ctx+0x1C`), tested
    before the collision read.
