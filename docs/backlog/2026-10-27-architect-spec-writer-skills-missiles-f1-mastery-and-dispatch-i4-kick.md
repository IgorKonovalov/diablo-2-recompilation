---
from: architect
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../specs/skills/missiles.md#f-the-packet-at-the-hit-missile_builddamage
  - ../specs/skills/dispatch.md#i-the-skill-packet
  - ../plans/done/0045-skills-missiles-machinery.md#implementation-log
  - archive/2026-10-27-architect-reverser-skills-0002-builddamage-pair-swap-and-unit.md
resolution: ""
---

*(Released at the `lane/rbd` review, 2026-10-27, accept with fixes; see the plan 0038 log and the plan 0045 log.)* What to write for (1), from skills/0002 § 6 after `lane/rbd`: no logged build separates the mastery (0 of 54 655 `MH0` lists hold 329–332 or 357; `rbd-mastery-scan.txt`), so take the mastery clause out of F1's `[C]` bullet and tag the pseudocode's `k ←` and `if k ≠ 0` lines `[I]` inline (anchor `0x005A895F`, fn:sub_005A8910_MissileElemRoll@0x005A8910). The `[C]` bullet may now cite both runs: 4 118 builds over 33 logs, 0 mismatches (run:2026-10-25-skills, run:2026-10-27-skills); keep its own breakdown (778 builds, 39/720/19) as run:2026-10-25-skills's, or restate it from `rbd-skills-check.txt` if you cite the larger count. Keep the swap and the missile-unit reading in the `[I]` bullet with the order *test both bounds > 0, swap, mastery, draw*, and say no build of either run had an inverted pair. Add under *Open questions* `[L]`: whether a missile's stat list ever carries its owner's masteries (329–332, 357), so that the mastery term is non-zero (skills/0002 § 6's `[L]`; a logged build by a caster with Fire Mastery settles it). `MISSILE_BuildDamage` and `MissileElemRoll` are now C in `re/symbols.csv` (rule 14, the drawn fields), which changes no spec tag. Bump wiki/skills' `based_on` if `updated:` moves. Part (2) is unchanged.

**Reconcile two skills-spec statements** (found at the `lane/s45p4` review, plan 0045 Phase 4). **Wait for `lane/rbd`** (the reverser folding the `BuildDamage` pair swap and the missile-mastery reading into skills/0002 § 6, [entry](archive/2026-10-27-architect-reverser-skills-0002-builddamage-pair-swap-and-unit.md)) to merge, and take its tags.

(1) **missiles § F1, the mastery.** The `[C]` bullet (778 builds) says "the mastery `MulDiv` (the missile's own mastery stat) on both bounds first", and the pseudocode's `[C]` header covers the `k ← stat(m, mastery)` line untagged, while the `[I]` bullet below gives the same reading on the missile at `[I]`. Unless skills/0002 § 6 (after `lane/rbd`) records that some of the 778 builds had a non-zero mastery stat on the missile, the run did not separate the mastery step (a zero mastery adds nothing): take the mastery out of the `[C]` bullet, tag the `k` line `[I]` inline, and keep the `[I]` bullet. If the finding leaves open whether a missile's stat list carries its owner's masteries (329–332, 357), add that as an `[L]` open question. wiki/skills § *Missiles: the hit* already states the mastery as read from the code; bump its `based_on` if the spec's `updated:` moves.

(2) **dispatch § I4 and the `Kick` damage.** I4 gives "`SKILLS_GetPhysMin/Max`: a `Kick` row gives `(max(x, 1) ÷ 4) << 8`" for both bounds; [Skills § `Kick`](../tables/Skills.md) gives `GetPhysMin` ÷ 4 `[C]` (emulated inside hit 43, skills/0007 § 3) and `GetPhysMax` ÷ 3 `[I]` (`sub_00644C20_SkillKickDamage` with flag 0). Restate I4 per bound with those tags. Also § O's Kick row builds its start hit with "physical `MinDam << HitShift`" while I4 gives a `Kick` row's skill damage from strength and dexterity: check the Kick row's `MinDam` in the table doc and say which damage Kick's start hit carries if skills/0003 § 5 settles it, else file the question to the reverser and list it under *Open questions* `[L]`.
