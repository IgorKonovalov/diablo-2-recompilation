---
from: reverser
to: spec-writer
date: 2026-10-21
status: done
context:
  - ../../findings/skills/0014-assassin.md
  - ../../findings/skills/0001-dispatch.md
  - ../../specs/combat/delivery.md
resolution: "Done 2026-10-21 (spec-writer, lane/s46c): combat/delivery A2 (the six finisher callers, the finishing moves' calls and deliveries, do 46 finisher only on a hit and one DeliverQueued on either path) and A3 (entries 36-41 and 143 [C] up to their first creation, the rings' untested count: 0 endless [I], negative ends by index wrap [I], stock values an [L] under Open questions; the 0x118 Param2 write; ItemEffect 36) ([combat/delivery](../../specs/combat/delivery.md))"
---

Not blocking. Plan 0046 batch `ass` ([skills/0014](../../findings/skills/0014-assassin.md)) bears on
[combat/delivery](../../specs/combat/delivery.md) A2/A3 (plan 0045's machinery, corrected here as plan 0046 Phase 1
asks):

1. **The finisher's callers.** A2 has `SKILL_AttackDo` call `COMBAT_PrgFinisher`. It has five more direct callers, all
   assassin finishing moves: do 42 Dragon Talon (`0x005D5A8C`), do 46 Dragon Claw (`0x005D6399`, `0x005D63E1`), do 50
   Dragon Tail (`0x005D71F2`), do 52 Dragon Flight (`0x005D79DF`), each with `QueuedHitFind(caster, target)`'s hit
   (do 42 and 52 without a null test; the finisher returns at once for a null hit) (skills/0014 §§ 1, 4; the do 42, 46
   and 50 calls `[C]` as boundaries under ADR-0021, run:2026-10-21-cat-emu-ass; the finisher's null return `[I]`). The
   skills/0001 § 12 note that put two of them in start 25 is corrected there: they are do 46's.
2. **The entries' raises.** The A3 entry blocks for 37/143, 39 and 41 can cite `[C]` (ADR-0021) up to the first
   creation: the inline step of the attacker's seed at entry **before** the record test; the ring's
   `RNG_SeedInit(local, low)` (high `0x29A`) and one local step before its first `MissileCreate` (block `+0x58` the
   stepped local low, first direction `(30, 0)`); 39's two `RNG_Range(local, 2r)` per try; 41's two local steps, `dx =
   low₁ mod 40 − 20`, `dy = low₂ mod 40 − 20`, `(0, 0)` → `(20, 0)`; 41 returns 1 for a negative count. Entry 38's
   `DeliverQueued` first and its `SkillRollPhys` call (with `r` computed before) are `[C]` up to those calls; its rolls
   stay `[I]`.
3. **Two quirks for A3's pseudocode** (`[I]`, after the first creation): the rings' step is not tested, so a count of
   0 is an endless loop; their `MissileData+0x28` write is `SkillGetParam2(280) + 1` (Royal Strike's row, the immediate
   `0x118`) whatever row runs the ring, ring 37 with no null test of the missile.
4. Entry 36 (also `ItemEffect` 36: the Nova and Frost Nova item casts) is a nova centred on the **target unit** and
   owned by the caster, velocity `MissileSpeedAtLevel(m, lvl) + calc1`; `[C]` up to its first creation.

**Released (architect, 2026-10-21, `lane/p46m11` review: accept with fixes).** Items 1–4 as written, against
[skills/0014](../../findings/skills/0014-assassin.md) after the review's fixes. For item 3, a negative step count is not
an endless loop: the ring reads its direction pair below the tables on every pass and the signed index ends the loop
only by wrapping past −2³¹ (§ 5, `[I]`, not run); state it so or leave negative counts to *Open questions*. In do 46,
`DeliverQueued(target, 0)` follows on both paths and the finisher runs only when `QueuedHitFind` gives a hit.
