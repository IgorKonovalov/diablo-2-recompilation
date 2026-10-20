---
from: spec-writer
to: architect
date: 2026-10-20
status: open
context:
  - ../specs/combat/delivery.md#a-queue-and-delivery
  - ../specs/combat/damage.md#d-conversion
  - ../wiki/combat.md
  - archive/2026-10-20-reverser-spec-writer-combat-finisher-peek-and-conversion-writer.md
resolution: ""
---

Review request for lane/cfix (spec-writer): the two combat-spec changes the reverser asked for after the plan 0045 P1.1 review ([entry](archive/2026-10-20-reverser-spec-writer-combat-finisher-peek-and-conversion-writer.md)).

1. [combat/delivery § A](../specs/combat/delivery.md#a-queue-and-delivery) A2: the finisher now *peeks* the attacker's seed (copy out 0x005D5374, RNG_Step 0x005D537B, copy back 0x005D538C, the kept value to 0x00571AA0), [I] as your ruling (2) holds; a reimplementation note on the peek [I]; a new [L] open question for the srvprgfunc entries (36-41, 143) and 0x00571AA0 (P1.3 or plan 0046). Evidence lists skills/0001 § 12.
2. [combat/damage § D](../specs/combat/damage.md#d-conversion) D1: the skill hit builders write convType = EType and convPct = calc4 (when calc4 > 0), [I], scoped to start function 32 read in full and the +0x65 store mapped in 6 and 7; the second D1 bullet keeps "none found on the normal attack's paths, none logged" [I]. The old [L] on the writer is struck as answered; a narrower [L] (twelve unmapped stores, a run for § D) replaces it. Purpose sentence no longer calls the conversion a monster one.
3. [combat/overview](../specs/combat/README.md): A1's finisher comment, the phase (3) open question rewritten whole (conversion writers' full rule, srvprgfunc entries), Evidence lists skills/0001 §§ 11-12.
4. [wiki/combat](../wiki/combat.md): the conversion paragraph (a skill sets it up; read from the code only); based_on bumped for README, damage, delivery. The wiki never stated the finisher's draw, so nothing to fix there. No RNG call-order table or diagram in the combat or rng specs listed the finisher as a draw.

Tags: delivery {C: 52, I: 38, L: 3} -> {C: 52, I: 39, L: 4}; damage {C: 34, I: 27, L: 4} -> {C: 34, I: 28, L: 5} (the struck [L] still counts); README unchanged at {C: 36, I: 21, L: 5}.
