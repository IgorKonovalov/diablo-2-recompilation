---
from: architect
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../specs/skills/missiles.md#f-the-packet-at-the-hit-missile_builddamage
  - ../specs/skills/dispatch.md#i-the-skill-packet
  - ../plans/done/0045-skills-missiles-machinery.md#implementation-log
  - ../backlog/2026-10-27-architect-reverser-skills-0002-builddamage-pair-swap-and-unit.md
resolution: ""
---

**Reconcile two skills-spec statements** (found at the `lane/s45p4` review, plan 0045 Phase 4). **Wait for `lane/rbd`** (the reverser folding the `BuildDamage` pair swap and the missile-mastery reading into skills/0002 § 6, [entry](2026-10-27-architect-reverser-skills-0002-builddamage-pair-swap-and-unit.md)) to merge, and take its tags.

(1) **missiles § F1, the mastery.** The `[C]` bullet (778 builds) says "the mastery `MulDiv` (the missile's own mastery stat) on both bounds first", and the pseudocode's `[C]` header covers the `k ← stat(m, mastery)` line untagged, while the `[I]` bullet below gives the same reading on the missile at `[I]`. Unless skills/0002 § 6 (after `lane/rbd`) records that some of the 778 builds had a non-zero mastery stat on the missile, the run did not separate the mastery step (a zero mastery adds nothing): take the mastery out of the `[C]` bullet, tag the `k` line `[I]` inline, and keep the `[I]` bullet. If the finding leaves open whether a missile's stat list carries its owner's masteries (329–332, 357), add that as an `[L]` open question. wiki/skills § *Missiles: the hit* already states the mastery as read from the code; bump its `based_on` if the spec's `updated:` moves.

(2) **dispatch § I4 and the `Kick` damage.** I4 gives "`SKILLS_GetPhysMin/Max`: a `Kick` row gives `(max(x, 1) ÷ 4) << 8`" for both bounds; [Skills § `Kick`](../tables/Skills.md) gives `GetPhysMin` ÷ 4 `[C]` (emulated inside hit 43, skills/0007 § 3) and `GetPhysMax` ÷ 3 `[I]` (`sub_00644C20_SkillKickDamage` with flag 0). Restate I4 per bound with those tags. Also § O's Kick row builds its start hit with "physical `MinDam << HitShift`" while I4 gives a `Kick` row's skill damage from strength and dexterity: check the Kick row's `MinDam` in the table doc and say which damage Kick's start hit carries if skills/0003 § 5 settles it, else file the question to the reverser and list it under *Open questions* `[L]`.
