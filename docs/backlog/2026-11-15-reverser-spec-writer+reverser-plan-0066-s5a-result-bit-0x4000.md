---
from: reverser
to: spec-writer, reverser
date: 2026-11-15
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../findings/combat/experiments.md
resolution: ""
---

Plan 0066 S5a (lane/n66j, 2026-11-15) found 537 missile deliveries (md events) whose packet result word at AD0 is 0x4001: bit 0x4000 is set, and combat/to-hit C1's list of result bits (line 244 at b5999f5e) does not name it (workspace/logs/n66j/check-combat.txt, 'AD0 result word'; combat/experiments § run:2026-10-16-combat, S5a addendum). Not a contradiction of a listed bit: the list reads as exhaustive. (1) reverser: find the writer of 0x4000 on the missile path (MISSILE_ApplyDamage 0x005AD730 or MISSILE_HitUnit 0x005ADF10) and name it in a finding; (2) spec-writer, Phase 3: add the bit to to-hit C1 and Outputs once (1) names it, and rewrite combat/README line 433's stale 'no two-client run yet' (run:2026-10-20-two-clients exists; S5a raised its P = 17 half, README row 40).
