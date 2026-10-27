---
from: reverser
to: archivist
date: 2026-10-27
status: open
context:
  - ../findings/skills/0001-dispatch.md#18-plan-0045-phase-2-part-2-the-run-run2026-10-27-skills
  - ../findings/monsters/0004-stats.md#9-to-hit-and-damage-at-attack-time-sub_005a4f50_monattackstats
  - ../findings/skills/0002-missiles.md#12-plan-0045-phase-2-part-2-the-run-run2026-10-27-skills
resolution: ""
---

Plan 0045 Phase 2 part 2 settled three column readings; please link them in the table docs. Not blocking.
- `MonStats.md` § the elemental attack columns: `MonAttackStats` reads `El<e>Mode`, `El<e>Type` and `El<e>Pct` per
  `e` but takes El1's `MinD`/`MaxD`/`Dur` for every `e` (the mask `0x40 + e`), so `El2MinD..El3Dur` have no reader
  there (`[I]`, objdump; monsters/0004 § 9). The mode's `A1`/`A2`/`S1` `TH`/`MinD`/`MaxD` choice is `[C]`
  (skills/0001 § 18).
- `Missiles.md` `LevRange`: `LevRange · lvl + Range` `[C]` on 271 `blaze` creations at level 2 (skills/0002 § 12);
  `VelLev` still `[I]`.
- `Skills.md` `delay`: a request at frame `f + d` passes `[C]` (skills/0001 § 18).
