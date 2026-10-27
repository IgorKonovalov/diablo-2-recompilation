---
from: reverser
to: reverser
date: 2026-10-20
status: open
context:
  - ../findings/skills/0002-missiles.md#leads-used
  - ../findings/skills/0003-handlers.md#leads-used
  - ../plans/done/0045-skills-missiles-machinery.md#implementation-log
resolution: ""
---

plan 0045 Phase 2 required cases from the Phase 1b contradicted leads (skills/0002 and skills/0003 *Leads used*), all reachable on stock data: (C1) Raise Skeleton's summon level `min(max(L·3/4 + skill level, 1), L)` against src:arreat-summit-skill-trees "generated at the caster's level": a Necromancer whose character level L exceeds 4 × the skill level, the summon's stat 12 logged at `sub_005C49E0_SummonSetLevel`; (C2) missile velocity `((VelLev · lvl) / 8 + Vel) << 8` against src:d2dfg-blizzard `Vel + VelLev` per level beyond 1: a `spike1`–`spike4` missile (the only four `VelLev` rows, monster missiles) with the creation velocity and the request level logged; (C3) `Accel` added on every fifth path step, capped at `MaxVel << 8` and floored at 0, against src:d2dfg-blizzard "per frame": Nova, Frost Nova or Howl missiles (tier A, `Accel` −1000) in the per-frame position window, at least one followed past its fifth step; (C4) range `LevRange · lvl + Range` against src:d2dfg-blizzard `Range` + `LevRange` per caster level beyond 1: one of the 32 `LevRange` rows (none in tier A: `blaze` 25, `firewallmaker` 2, `bonewallmaker` 2, …) created by a skill at a known level, the stored range logged (the architect rules whether a non-tier-A cast is added); (C5) a missed `ToHit` piercing missile ends at that unit against src:purediablo-piercing "keeps traveling but doesn't deal any damage": a `Pierce` arrow (Multiple Shot or Attack with a bow, a pierce stat > 0) whose `COMBAT_ToHitRoll` fails, the missile's free and its stat 328 logged. *Architect, P1b review 2026-10-20 ([plan log](../plans/done/0045-skills-missiles-machinery.md#implementation-log)):* (C4) add a Blaze cast (`blaze`, `LevRange` 25) at a skill level ≥ 2, about 30 creations, its do function a value oracle, Blaze not in tier A; Fire Wall the fallback. (C2) a monster-session case riding on the 200 monster skill uses, about 30 creations; a named shortfall if no reachable monster uses `spike1`–`spike4`. Item casts of an `ItemTarget` 2–4 skill, if met, are logged with the given unit's seed around the helper (not a required case).
