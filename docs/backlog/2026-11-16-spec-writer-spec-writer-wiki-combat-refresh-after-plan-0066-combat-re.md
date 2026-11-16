---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../wiki/combat.md
  - ../wiki/characters.md
resolution: ""
---

Plan 0066 Phase 3, combat cluster (lane/n66y), updated combat/README, to-hit, damage, reductions and delivery and player/party on 2026-11-16, so wiki/combat and wiki/characters carry W4. Refresh wiki/combat against the re-tagged specs: many statements it may give as read from the code are now confirmed by run or emulation (the packet's size and zeroing, the missile critical chain, the finisher's peek, A7 and B1, the walking block, P's every branch, sanctuary, pierce, absorb on every row, the stat events' branches, the player's 256 floor), and these statements were corrected (the missile's deadly-strike step on a non-zero stat 141, the peek steps the seed itself between a save and a restore, B1 for a defence of 0 or below, sanctuary only for a positive resistance, step 1's condition and stat 120's sign, the crushing-blow cap above 0x100000, freeze's x·4, the poison roll replacing its field). Take each from the spec section, at the spec's tag (spec-writer review-fixes 1). wiki/characters needs only its based_on date unless its party section restates the MonAttackStats player-count bonus.
