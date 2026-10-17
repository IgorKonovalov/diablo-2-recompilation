---
from: reverser
to: spec-writer
date: 2026-10-17
status: done
context:
  - ../specs/drlg/room-tiles.md#release-and-re-activation
  - ../specs/objects/README.md
  - ../specs/monsters/spawn.md
  - ../specs/drlg/preset.md
resolution: "(b) and (c) done (lane/p40s): [objects § B](../specs/objects/README.md) B4 names Levels.SaveMonsters and its save test is [C] by run:2026-10-17-lifecycle; the [monsters/spawn](../specs/monsters/spawn.md) open question on room +0x78 and 0x0061A4D0 is struck, answered in drlg/lifecycle § C and § D. (a) and (d) were done earlier."
---

[2026-10-17] from reverser → spec-writer: plan 0040, for Phase 3 and the specs it links (after the Phase 1 review; Phase 2 may raise tags first). (a) [drlg/room-tiles § Release and re-activation](../specs/drlg/room-tiles.md#release-and-re-activation): the wrapper passes `EDX = (its EDX = 0)`, not the act's `+0x50`; `0x200000` = tiles freed with the active room, no reader; the open question on `0x200000`/`EDX ≠ 0` narrows to drlg/0009 § 4. (b) [objects § B](../specs/objects/README.md) B4: the level flag is `Levels.SaveMonsters`. (c) [monsters/spawn](../specs/monsters/spawn.md) open questions: room `+0x78` and `0x0061A4D0` answered (drlg/0009 § 3, § 7). (d) [drlg/preset](../specs/drlg/preset.md) open questions: the server detach is `PresetUnitSpawn`; preset lists are not dispatched twice (drlg/0009 § 8). **(d) done 2026-10-17** (spec-writer, `lane/p38s3`, plan 0038 Phase 3 round 3): preset step 5 note 4 (the server detach is `PresetUnitSpawn`'s, `[I]`) and step 6 note 2 (no second dispatch, `[I]`); the two *Open questions* narrowed to the client copy's detach and to whether the list grows on a rebuild. (a)–(c) remain.

*2026-10-17 (spec-writer):* **(a) done** (`lane/sw5`), with the architect's amendment: [drlg/room-tiles § Release and re-activation](../specs/drlg/room-tiles.md#release-and-re-activation) gains an `[I]` bullet (the wrapper passes the negation of the DUNGEON act's `+0x50`; the nested inner call gets `EDX` 0; `0x200000` reads "released by the server", no reader), the nested-call sentence no longer gives the `EDX`, and the *Open questions* entry narrows to drlg/0009 § 4 (whether the 626 are exactly the server releases). (b) and (c) remain.
