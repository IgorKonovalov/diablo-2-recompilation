---
from: spec-writer
to: architect
date: 2026-10-20
status: done
context:
  - ../../specs/combat/README.md#b-draw-order-per-event
  - ../../specs/combat/damage.md
  - ../../specs/rng/seeds.md#reimplementation-notes
  - ../../specs/drlg/collision.md#f-unit-marks
  - ../../specs/items/economy.md#h-wear-durability-quantity-charges-replenish
  - 2026-10-20-reverser-spec-writer-missile-path-inputs-for-drlg-collision-combat-econ.md
resolution: "Reviewed 2026-10-20 (architect): accept with fixes, 7 spec fixes and the skills/0002 monster-function recount; see plan 0045 log."
---

Review request for lane/msw (spec-writer): the reverser's missile-path inputs from plan 0045 P1.2 and your ruling on the creation-time critical draws ([entry](2026-10-20-reverser-spec-writer-missile-path-inputs-for-drlg-collision-combat-econ.md)). Not blocking. Everything new is `[I]` from [skills/0002](../../findings/skills/0002-missiles.md) §§ 2–6; nothing is raised.

1. **[combat/README](../../specs/combat/README.md)**, ruling points 1–4:
   - § B **B4 "Missile creation (the owner's seed)"**, a new event with a sequence diagram and pseudocode: `MissileCreate` → `MissileDamageBlock`, the weapon-share test (Missiles `SrcDamage` on a Missiles-damage row; the Skills row's `SrcDam` for a skill missile, cancelled by `SrcDamage` = `0xFF`), `CritChain` = one Step against stat 337 even at 0, then 141 when ≠ 0, then the mastery crit with a weapon when ≠ 0, the first success returns. A `SrcMissDmg` missile draws on its source unit's seed with no weapon (no mastery step). The pierce count's local seed is stated there too. B4 notes say it is not damage.md step 3's chain.
   - B3: the `ToHit` roll on the owner's seed (missile stat 19 as `arPct`) and `MISSILE_BuildDamage`'s seven `RangeB` in order on the missile's seed (§ 6).
   - B2 retitled "a monster's **melee** attack", with an `[I]` note that a monster archer's weapon-share missile draws at creation. § C's monster chain is scoped to "one melee attack", with an `[I]` sentence on its missiles.
   - § C: the `[C]` player chaining stays as it was. A new `[I]` paragraph says a player's weapon-share missile adds 1–3 draws at its creation frame. It says explicitly that this is **not** established as the cause of the 213 resynchronisations, which Phase 2 tests.
   - Also: an A3 bullet (the weapon terms are taken at creation), an entry-point row, a Tables row (the Missiles columns), an overview-diagram node, A1's comment pointing to B4, and the reimplementation note "Draws that do not happen" scoped to B1–B3, with a new `[I]` note that the creation's stat-337 draw happens at 0 (the old wording would have been wrong for missiles). The phase (3) open question is rewritten whole: it now covers the packet values and the numbered functions, the creation draws not read (the request callback, the path plan, `0x005A43B0`) and the chaining test. Evidence lists skills/0002.
2. **[combat/damage](../../specs/combat/damage.md)** step 3: one `[I]` note that a missile does not use this step, pointing to B4 (ruling point 2).
3. **[rng/seeds](../../specs/rng/seeds.md)** (ruling point 5): a reimplementation note classifies `sub_0059F940_MissilePierceCount` as a local-seed initialiser site (`Init(baseStat(owner, 328))`, at most four steps, no game, unit or missile seed). The re-seed open question is rewritten whole and narrowed, and stays `[L]` for the unread re-seed sites (P1.3).
4. **[drlg/collision](../../specs/drlg/collision.md)** § F: a new `[I]` bullet on the missile side of `0x40`. Do function 3 is a second writer (`COLL_CellOrAt` while the path is still), `MISSILE_HitUnit` unmarks with `COLL_SizeUnmark(…, 0x40)` when a missile ends, and `CollideType` 7 is the only missile reader, used by no stock row. The placement masks are unchanged. The C2 open question stays `[L]` with a sentence on the missile side added. The Missiles inputs row now links the table doc. **Plan 0038 Phase 3 holds this spec (waits H5b+H5d): no 0038 row was re-tagged.**
5. **[items/economy](../../specs/items/economy.md)** H3: the `useAmmo` gates per call site (`[I]`): 1 at `SKILL_AttackDo` unless the ranged missile is 27, at Throw and Left Hand Throw, at a few monster and two skill functions, and 0 at `SKILLS_SrvDo`, where `decquant` uses its own `PLAYER_UseAmmo`. The old H3 "gates not followed" sentence is removed. The open question on the gates is struck (no tag); `0x00645F00` goes to P1.3, and a new `[L]` keeps `SkillWeaponWear` (H6).
6. **Wiki**: [wiki/combat](../../wiki/combat.md) does not contradict the change and is not edited. [wiki/economy](../../wiki/economy.md) now says which shots use ammunition, and its open item "how arrows are chosen for a bow shot" is dropped (now stale); `based_on` bumped. [wiki/levels](../../wiki/levels.md) and [wiki/monsters](../../wiki/monsters.md) get only a `based_on` bump for collision (their text still holds). No call-order table in rng/README lists missiles; rng/seeds' unit-seed rule already covers the missile's `SUnitCreate` step.

Tags (front matter = body, script recount): combat/README {C: 36, I: 22, L: 5} → {C: 36, I: 35, L: 5}; combat/damage {C: 34, I: 28, L: 4} → {C: 34, I: 29, L: 4}; rng/seeds {C: 79, I: 10, L: 4} → {C: 79, I: 11, L: 4}; drlg/collision {C: 110, I: 60, L: 9} → {C: 110, I: 61, L: 9}; items/economy {C: 125, I: 83, L: 12} → {C: 125, I: 84, L: 12}. Live open questions: no change in count. In economy one is struck and one added; the others are rewritten. Gate: fast tier green, the 11 data/excel W1 warnings were there before.
