---
from: reverser
to: spec-writer
date: 2026-10-16
status: done
context:
  - ../../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b
resolution: "Applied 2026-10-27 (spec-writer, lane/s38m, plan 0038 Phase 3, monsters cluster): (a) monsters/special § J, a restored aura special holds two auras [C]; (b) § H, PresetFallenVariant keys on the BaseId of the class LevelClassVariant returns [C]; (c) § I1, the fixed-name branch reached for 156, 242 and 256 [C]; (d) monsters/spawn H5, evilhut 528 [C] (with 228 from H5d); (e) special 65 split, special 27's clamps [I], stats B3 [C] for 311 and 312 (H4a's class-312 piece) ([monsters/special](../../specs/monsters/special.md#j-other-entry-paths-and-pre-existing-mods)). Not applied here: drlg/lifecycle H2b's restore line, listed in the lane's architect entry."
---

[2026-10-16] from reverser → spec-writer (Phase 3 of plan 0038, after the H4b review): corrections from
run:2026-10-16-sweep-monsters-b. (a) [monsters/special](../../specs/monsters/special.md) restore (L653): `SpecialMonRestore`'s
apply steps a fresh name seed and its `aura` call draws on it; only then is the saved name seed written, and the
second `UModAura` gives the first instance's aura, so a restored aura special holds two aura skills (monsters/0003 §
Plan 0038 batch H4b, special 1/74). (b) L572: `PresetFallenVariant` keys on the BaseId of the class
`LevelClassVariant` returns (level 6: `fallen1` → `fallen3` → `fallen2`). (c) § I: the fixed-name branch is reached
(Izual, string 1014). (d) [monsters/spawn § H5](../../specs/monsters/spawn.md): `evilhut` (528) is reached (presets window) and
its offset-cell test reproduced; the tentaclehead branch is in monsters/0002 § Plan 0038 batch H4b. (e) *Added at the H4b review:* special 65 (L572) is raised in part (cases 19–22, 25, 27, 28, 32, the normal group of 24 and 26 stay `[I]`); special 27 (L322): the clamp at 99 and AuraTable row 7 have no stock observable (d-none), the clamp at 1 stays `[I]`; stats 13/14: `doomknight3`'s two writes stay `[I]`. Context: [monsters/0003 § Plan 0038 batch H4b](../../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b)
