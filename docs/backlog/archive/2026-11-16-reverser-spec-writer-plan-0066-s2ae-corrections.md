---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/skills/0002-missiles.md
resolution: "Plan 0066 Phase 3, skills cluster (lane/n66sk): items 1 and 4 in skills/missiles (part 1); items 2 (C5's null refusals and restricted test), 3 (L5's SummonSetDataBytes copy, class 363's flag and class 364's step) and 5 (I4's Kick maximum tail call, [C]) in [skills/dispatch](../../specs/skills/dispatch.md) (part 2)."
---

Plan 0066 batch S2ae (`lane/n66sa`) settled rows of skills/dispatch and skills/missiles by emulation
(run:2026-11-16-sweep2-s2ae) and by earlier kept runs; the claims are in
[skills/0002 § 17](../../findings/skills/0002-missiles.md#17-plan-0066-batch-s2ae-part-1-leaf-functions-emulated-earlier-runs-re-read-the-routes-2026-11-16-lanen66sa).
Besides the re-tags listed in the plan log (Phase 3's), these texts need a change. Not blocking; for the skills
cluster's Phase 3. Part 2 of the batch will append its own items here.

1. **skills/missiles D4 (`PathVelocityStep`), refinement.** The clamp at 0 is the `else` of the cap (`if v > max: v ←
   max; accel ← 0; else if v < 0: v ← 0`), so a sum above a negative maximum keeps it; the step is taken when the
   incremented count is above 4 (not "= 5"); the multiplier is the `ECX` argument (`0x400` when below 1), not a
   constant; the function **writes** the step to `+0x72`/`+0x76` (`(dir · s) >> 12`), it does not add to the position.
2. **skills/dispatch C5 (`RestrictOk`), refinement.** A null record refuses (also a null unit or entry). The restricted
   test (`0x0063A510` → `0x0063A130`) is any common bit between the unit's state bits (read only when its list has
   bit 31 of `+0x10`) and the mask words at DataTables `+0x110`; the spec can drop "not read".
3. **skills/dispatch L5 (`SummonClassRoll`), refinement.** Both paths call `SummonSetDataBytes` with `EAX` = 1 (state 97
   off), which first copies row 1 of the 9-byte rows at 0x00741940 into MonsterData `+4`, `+5`, `+0xC`, `+0xD`, `+6`,
   `+7`, `+8`, `+0x0B` (this one only when its first argument, the class-363 flag, is non-zero); class 363 then writes
   `+9` from the row and draws nothing more; class 364 steps the caster's seed once, writes `low & 3` to `+0x0F` and
   `+0x10` and calls `0x005B0D70`. The flag of class 363 is SummonSetDataBytes' first argument, the `+0x0B` write.
4. **skills/missiles H, the table's do-34 row:** "path X" is `SubX` (the re-seed is `(SubX, 666)`), as skills/0005 § 8.
5. **skills/dispatch I4:** the kick maximum's tail call is now read: `GetPhysMax` loads `ESI` from its first argument
   and returns `SkillKickDamage(flag 0)`'s value (0x00647D3D–0x00647D49), so "The emulation stops at that call" can go
   with the `[I]`.
