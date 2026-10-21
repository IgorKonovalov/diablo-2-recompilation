---
from: reverser
to: archivist
date: 2026-10-21
status: open
context:
  - ../findings/skills/0016-monster-8a.md
  - ../tables/Skills.md
  - ../tables/MonStats.md
  - ../tables/MonStats2.md
  - ../tables/Missiles.md
resolution: ""
---

Not blocking. Plan 0046 batch 8a ([skills/0016](../findings/skills/0016-monster-8a.md)) settles code readers for these
columns; please link them from the table docs.

- [Skills](../tables/Skills.md) `Param4` (`+0x154`): do 111 (FetishAura) reads it raw, not as a calc: the radius
  `Param4 + 2·lvl` of `0x0056C210`'s unit list round the target point (§ 6, `[C]` as the map up to the allocation).
- [Skills](../tables/Skills.md) `lob` (`+0x004` bit 1): do 110 casts `srvmissilea` with `SkillMissileCreateLob` when
  it is set (§ 3, `[C]`); no stock row of the batch has it.
- [Skills](../tables/Skills.md) `summon` (`+0x0BC`) / `summode` (`+0x0BF`) and [MonStats](../tables/MonStats.md)
  `spawn` (`+0x020`), `spawnx`/`spawny` (`+0x022`/`+0x023`), `spawnmode` (`+0x024`): `SkillSummonClass` with
  `EDX` 1 (start 49, do 84, do 87) takes a **monster caster's own** MonStats `spawn` as the class, its position plus
  `spawnx`/`spawny`, and `spawnmode` (1 outside 0–15); a non-monster's Skills `summon`/`summode` (§ 4, `[C]` as the map).
  So the MonStats.md rows' "name: offset of the spawned unit from the spawner" and "the spawned unit's starting mode"
  `[L]` have a reader (start 49's node words; do 84's mode; do 87 ignores the offsets and steps one cell towards the
  target).
- [MonStats](../tables/MonStats.md) `+0x04B` (the chain position, written at load): do 85 adds it to `srvmissilea`
  through `MONSTATS_GetClassChainPos`, so the n-th class of a chain casts the n-th missile after the named one (§ 6,
  `[C]` as the map).
- [Missiles](../tables/Missiles.md) `Vel` (`+0x09A`) and `VelLev` (`+0x09B`): do 95 writes `(VelLev · lvl) / 8 + Vel`
  (signed division toward 0) into its `MissileCreate` block's `+0x28` (§ 6, `[C]` as the map; that this is the creation
  velocity, the term skills/0002 § 2 reads with `<< 8`, is `[I]`).
- [MonStats2](../tables/MonStats2.md) `InfernoLen` (`+0x108`): `0x005CC3B0` (do 95's end) queues the next event at
  `frame + InfernoLen` (11 without a row) (§ 6, `[I]`, after its `CancelEvents` boundary); `InfernoAnim` (`+0x109`):
  `0x005CC440` (§ 6, `[I]`).
