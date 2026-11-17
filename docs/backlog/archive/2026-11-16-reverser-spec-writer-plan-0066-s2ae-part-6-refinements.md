---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/skills/0002-missiles.md
  - ../../specs/skills/dispatch.md
resolution: "Plan 0066 Phase 3, skills cluster (lane/n66sk): all seven items in [skills/dispatch](../../specs/skills/dispatch.md) § K (handlers 8, 10, 18, 31 in the table, handler 9's formula in K2, K2's remainder list narrowed) and I4 (Kick's start [C], flag 2's meaning left to I1)."
---

Plan 0066 batch S2ae part 6 (`lane/n66sa`, run:2026-11-16-sweep2-s2ae6) raised skills/dispatch row 93 (I4, Kick's
start) whole and rows 117, 119, 124, 133, 135 and 178 (§ K, § P) in part, and moved rows 182 and 184 (§ P's
Armageddon row and P2) to b. For Phase 3 to carry when the skills cluster is re-tagged (claims and anchors in
[skills/0002 § 22](../../findings/skills/0002-missiles.md#22-plan-0066-batch-s2ae-part-6-six-stat-event-handlers-and-kicks-start-emulated-the-open-routes-read-2026-11-16-lanen66sa)).
No contradiction. Not blocking.

1. **K, handler 18** (refinement): the code adds more than "for a demon victim, life `+= stat · 256`". It returns 0
   unless the unit's life (stat 6) is **below its maximum** (stat 7, layer 0); the sum is **floored at 0 and capped at
   the maximum** before `UnitSetStat(unit, 6, x, 0)`; a negative stat goes on (and lowers life), a stat of 0 returns.
   (0x005C02A0–0x005C02DC)
2. **K, handler 10** (refinement): a gate the table does not state: the other unit's `+0xC4` bit 2 must be set. The
   packet is `+0x04` 0x4021, `+0x1C` `stat << 8`, `+0x60` 0x4D, passed to `COMBAT_ApplyDamage(other, 1, packet)`.
   (0x005BF739–0x005BF7A2)
3. **K2, handler 9** (the chance formula, now `[C]` to its call): `c = 5·(L_unit + 4·stat − L_other + 6)` (32-bit; `L`
   stat 12), divided by 3 for event id 6 when positive, clamped to 1..99; `Range(seed, 100) < c` calls `0x005C39C0`
   with `n = (c − r)/5 + 1` clamped to 1..20; a stat of 0 returns, a negative one goes on. (0x005BFAE8–0x005BFB88)
4. **K, handler 31** (refinement of "reanimate"): an other unit of type 1 whose MonsterData `+0x16` has no bit of
   0x0C, a stat > 0, one `RangeB(seed, 100) < stat`; the handler's unit's player (the unit itself, or the first type-0
   unit up its `MonsterOwner` chain, none returning 0); then `UNIT_AddEvent` on the **other** unit with (0x0D, the
   event word's layer, the player's guid, `SkillReviveDo` 0x005C07A0, 0, the guid). What the event does stays `[I]`.
   (0x005C09F6–0x005C0A74)
5. **K, handler 8**: the call is `MonFleeFrom(game, unit; other, 0x82, 0x14, 0x14)`; "flees" stays `[I]` (b).
6. **K2's remainder list**: knockback's mask and bit, howl's gate and stupidity's formula are now `[C]` (the six
   handlers' maps); handlers 1–4 and 23–27 remain the reading.
7. **I4, Kick**: the bullet's sentences up to the `ResolveAndQueue(…, 0x80)` call are `[C]` (the packet compared byte
   for byte, the three direct calls); the parenthetical on flags 2 stays I1's.
