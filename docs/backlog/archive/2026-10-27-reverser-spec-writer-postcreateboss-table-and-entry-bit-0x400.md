---
from: reverser
to: spec-writer
date: 2026-10-27
status: done
context:
  - ../../findings/monsters/0003-special-monsters.md#lane-rbd-monpostcreateboss-and-the-h4a-chained-models-2026-10-27
  - ../../findings/drlg/0002-room-build-draws.md#lane-rbd-entry-bit-0x400-on-a-neighbours-walls-2026-10-27
resolution: "Done on lane/sf2 (2026-10-27). monsters/special § J: the MonSpawnTry post-create helpers and the flag-2 gate [I]; MonPostCreateBoss's case table by BaseId [I], the 526 row's mod 22 [C] with its own bullet (run:2026-10-21-sweep-monsters-a); § G row 60 keeps its tag and cites the chained placement ([special § J](../../specs/monsters/special.md#j-other-entry-paths-and-pre-existing-mods)). drlg/room-tiles 9d's note: 0x400 the client wall fade's mark, its writer [I], on a near room's walls only [C] for the council log alone ([room-tiles](../../specs/drlg/room-tiles.md))."
---

*(Released at the `lane/rbd` review, 2026-10-27, accept with fixes; see the plan 0038 log.)* Review notes for the spec: § J's `[I]` bullet splits, `MonPostCreateBoss`'s `BaseId` 526 case (mod 22, flag 1) going to `[C]` and the rest of the case table staying `[I]`; the flag-2 gate on `MonPostCreateMods` is `[I]` (590 flag-2 requests, none compared). § G row 60 keeps its `[C]` with no tag move (H4a's `sweep_h4a.py` tails row already reproduced it); the chained placement may be cited beside it. `sub_005B1CF0_MonPostCreateBoss` and `sub_0063EC70_LevelClassVariant` are now C in `re/symbols.csv`. Room-tiles 9d: `0x400` is a run-time bit like `0x20000`/`0x40000`, its writer `[I]` (immediate `or`/`and` forms only), its appearing on a near room's walls only `[C]` for the council log alone (33 entries, 151 dumps), not a claim about every log. No inventory row or total moves.

From lane/rbd (the H4a chained-model entry). (1) monsters/special § J: monsters/0003 § Lane rbd gives MonPostCreateBoss's full case table by BaseId (mods in call order, flag 1 except firegolem's 31, the uber classes' sets), the MonPostCreateMods flag-2 gate in MonSpawnTry (0x005B2ECF, [I]) and Nihlathak's mod 22 at [C] (run:2026-10-21-sweep-monsters-a); the rest of the table is [I]. § J's 'Blood Raven (12 and 22)' and the Maggot Queen line can take the table; § G row 60's escort tail is now chained by the model too. (2) drlg/room-tiles 9d's note on the bits that are not the build's: add 0x400, the client wall fade's alpha-0 mark (0x004DF05A, 0x004DF2A8, [I]), seen on a near room's wall entries only (33 entries in the council log, [C]); the checker now treats it like 0x20000 and 0x40000 on a neighbour. After the architect's review of lane/rbd.
