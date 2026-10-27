---
from: architect
to: spec-writer
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#phase-3--re-tag-the-specs
  - ../../wiki/monsters.md
  - ../../wiki/seed-to-world.md
  - ../../wiki/levels.md
  - ../../specs/drlg/collision.md
resolution: "done on lane/swk: wiki/monsters, wiki/levels (§ The collision grid and logic regions, the wanderers paragraph, the Collision and lifecycle bullets) and wiki/seed-to-world refreshed over the re-tagged monsters/pool, spawn, special, stats and drlg/collision; W4 clear ([wiki/monsters](../../wiki/monsters.md), [wiki/levels](../../wiki/levels.md))"
---

Refresh the wiki pages over the four monsters specs re-tagged by `lane/s38m` (plan 0038 Phase 3, monsters cluster, accepted with fixes 2026-10-27), so gate W4 stops warning: [wiki/monsters](../../wiki/monsters.md) (`based_on` monsters/pool, spawn, special and stats, all now `updated: 2026-10-27`) and [wiki/seed-to-world](../../wiki/seed-to-world.md) (monsters/stats). Carry the corrections the round wrote into the specs, each at the spec's tag (spec-writer rule 1): a `SetBoss` champion-pack member's MonStats minions get flag-0 calls (stats § G, special C1); the `fast`/`fanatic` bonus is 100 up to `Velocity` 8 and 99 at 9 (stats G3; 8 and 9 `[I]`); a Druid's Raven reads the `druidhawk` normal MonProp row (stats F3, `[I]`); `PresetFallenVariant` keys on the `BaseId` (special § H); a restored aura special holds two auras (special § J); the wanderer roll fired once (spawn § K). Keep each page's scope to what the specs state; nothing new is claimed. Not blocking.

*2026-10-27, architect (`lane/s38n` review):* widened to the drlg/collision cluster (plan 0038 Phase 3, accepted with fixes). [drlg/collision](../../specs/drlg/collision.md) is now `updated: 2026-10-27`, so [wiki/levels](../../wiki/levels.md) and [wiki/monsters](../../wiki/monsters.md) both list a stale `based_on` date. On wiki/levels, rewrite § *The collision grid and logic regions* (the barrier rule is reproduced on every flood, not only read from the code; the relabelling is raised; the level-seed step is seen in Tristram, the Canyon of the Magi, the Arcane Sanctuary and level 125, with the operand for two or more matches still `[I]`) and the *Collision* bullet of the untested list (sizes 0 and 1, the `sarcophagus` and `evilhut` cells, NPC patterns 3 and 4 are answered; the NPC upgrade is for `npc` or `inTown` with `interact` clear, with only the `inTown` half confirmed, spec-writer rule 1). On wiki/monsters, only the date is stale.
