---
from: reverser
to: spec-writer
date: 2026-10-20
status: done
context:
  - ../../plans/0049-backlog-sweep-5.md
resolution: "Folded by lane/p49s (plan 0049 Phase 2): monsters/special § H rows 24/26 Normal-only groups, open question closed; drlg/lifecycle § E act +0x50 [C] (run window scoped), the 31 pin sites, the wanderer's alignment 2 (§ H, § I); drlg/room-tiles already had the corrected release order (nothing to change); items/quest-drops A3 and Duriel's bits [C] with the closure's limits; quests/progression word 41 (object 1's second word), word 32's one write, MissileCreateAt W4c and the missile ids, open question closed; player/creation A1 mode word, E4 the freed main list (ilvl-1 magic starting items), J3 the saved corpse, open question closed; items/quality M3 STATEVENT_Reanimate, FormationSpawn case 5, bonewallmaker; items/tc B1 the revive callback; rng/seeds step 5 note the kept split 359/115/58/0 and the 132/132, 0/25 re-seed count. No spec carried the 'rare cube outputs' wording. [plan](../../plans/0049-backlog-sweep-5.md)"
---

[2026-10-20] from reverser → spec-writer (plan 0049 Phase 1, `lane/p49r`; after the architect's review). New or changed readings for the specs, all [I] from code unless a finding says otherwise:
- **monsters/special § H**: MonPlace rows 24 and 26 place nothing outside Normal (the 0x0054EAA8 difficulty test), and rows 19–21 never reach the fixed-class table. The open question on row 24 can close ([monsters/0003 § 7](../../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20)).
- **drlg room tiles / lifecycle, the release order**: the active-room free (EDX 0, +0x30 set) comes first, then +0x30 ← 0, then the logic-record free, then the 0x100000 test ([drlg/0002 § H5c](../../findings/drlg/0002-room-build-draws.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk), *Release*).
- **drlg/lifecycle**: DUNGEON act +0x50 is 1 on a client act and 0 on a server act. A wanderer is alignment 2, so a saved wanderer is dropped. All 31 `RoomPinSet` sites are listed ([drlg/0009 § 11.4](../../findings/drlg/0009-room-lifecycle.md#114-the-plan-0040-phase-1-review-follow-ups-plan-0049-phase-1-lanep49r-static)).
- **items/quest-drops**: the qd 8, 10 and 19 remainders are traced. Every register site and every steps clear is resolved: no player bit-15 write but the loader's, word 9's the only bit-15 clear, no write of Duriel's bits 1 and 5, and word 41 is object 1's ([items/0010 § Plan 0049 Phase 1](../../findings/items/0010-quest-drops.md#plan-0049-phase-1-2026-10-20-static-the-s2c-static-leftovers)).
- **player/creation**: the starting items lose their main property list (`StartItemCreate`, 0x00534CB5). A saved corpse loses its stat 13. The default ladder bit is on only for the *Battle.net* button's mode 1 ([player/0001 § Plan 0049 Phase 1](../../findings/player/0001-creation.md#plan-0049-phase-1-2026-10-20-static)).
- **items** (monster ownership, the death-drop skip table): `0x005C09E0` is `STATEVENT_Reanimate`, the item property `reanimate` (Tomb Reaver, Faith): a kill of a non-champion, non-unique monster raises it for the killer's owning player on a `RangeB(killer seed, 100) < value` draw. `FormationSpawn` case 5 is never reached ([items/0002 § Plan 0049 Phase 1](../../findings/items/0002-quality-roll.md#plan-0049-phase-1-2026-10-20-static)).
- **quests**: `0x0056EDE0` is a missile creator; the stones, Countess chests and Baal's death create missiles 288, 332 and 625 ([quests/0001 § 7](../../findings/quests/0001-progression.md)).
- **rng/seeds row 3**: `sweep_s1b.py seeds` counts 132 of 132 type-2 re-seeds at the room's creation seed and 0 of 25 type-1 ([rng/0002 § S1b](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16), tool addendum).

*Review annotations (architect, `lane/p49r` review, 2026-10-20):* this entry is plan 0049 Phase 2's item 2. Tags moved at
the review: the DUNGEON act `+0x50` reading (1 on a client act, 0 on a server act) is `[C]` (drlg/0009 § 11.4 (a));
qd 10 and qd 19 are raised, so the items/quest-drops "only word 9 clears bit 15" and "Duriel's bit 5 never cleared"
statements may go to `[C]` with the closure's limits of items/0010 qd 10 stated beside them; qd 8's remainder stays
`[I]`. The rng/seeds rows 3 and 15 indirect-call split is the tool's 359 / 115 / 58 / 0. Everything else above stays as
tagged.
