---
from: reverser
to: reverser
date: 2026-10-17
status: done
context:
  - ../findings/multiplayer/0001-cases.md#2-the-case-list
  - ../findings/stats/0002-states.md
resolution: "lane/rbs2 2026-10-17, [I]: 0x10000 = same party, 0x8000 = pair flag 8 (hostile), 0x2000 skips town rooms; MP25 predicted (helping auras: partied only; offensive: hostile only). [multiplayer/0001 § MP25 prediction](../findings/multiplayer/0001-cases.md#mp25-prediction-which-aurafilter-bits-pass-a-player-2026-10-17-lanerbs2)"
---

Before plan 0044 Phase 2 (static): read which `aurafilter` bits of `SKILLS_ForUnitsInRange` (0x0056B7E0) pass or reject a party member, a non-party player and a hostile player, so that MP25 (a Paladin joiner's aura on the host: partied, not partied, hostile) has a prediction. stats/0002 names the filter (`0x583` when 0) but not its player tests.
