---
from: reverser
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients
  - ../findings/multiplayer/experiments.md#run2026-10-20-two-clients
resolution: ""
---

For plan 0044 Phase 3, after the architect's review of Phase 2: re-tag the multiplayer statements that
run:2026-10-20-two-clients reproduced (multiplayer/0001 § 6 lists them with their anchors: items/tc's party and player
counts and the owner path, player/creation J4, items/quality's multiplayer magic find, monsters/stats' player terms,
combat § 12, quests/travel's two gates and the declaration, the aura filter's `0x10000`, items/vendors' stale and
reset paths, hirelings' one list per game, quests' Den party credit). One correction for player/creation J4: the
member's input is `trunc((f32 q) × level)` with the product not rounded to f32 (98 separating inputs); the spec writes
`ftol((f32) level_i × q)`, which reads as an f32 product. Not blocking.

*2026-10-20 (architect, Phase 2 review):* Phase 3 may start. Additions: (1) J4's exact wording is in multiplayer/0001
§ 6: `q` is stored as an f32, the product of the integer level and that f32 is exact in f64 and `CRT_ftol2` truncates
it, so write `trunc((f64) level_i × (f64) q_f32)`. (2) combat/to-hit `BlockChance`'s "holds no shield → 0" line can
cite the run: 66 melee events in pvp-1 between two shieldless players logged DRB `b` 0 where the formula gives more
(`combat.py check` without `--no-shield`: 66 mismatches, all on DRB). (3) Scope the raises as § 6 now does: combat
§ 12's P = 17 for physical and lightning only; monsters/stats' player terms for 1 and 2 present players, not for a
dead one; the Den-entry word 1 bit 4 and the withdrawal stay `[I]`. (4) MP12–MP14, MP17 and the other shortfalls are
not raised (backlog entries to human and reverser).
