---
from: reverser
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../findings/monsters/0003-special-monsters.md#lane-rbd-monpostcreateboss-and-the-h4a-chained-models-2026-10-27
  - ../findings/drlg/0002-room-build-draws.md#lane-rbd-entry-bit-0x400-on-a-neighbours-walls-2026-10-27
resolution: ""
---

From lane/rbd (the H4a chained-model entry). (1) monsters/special § J: monsters/0003 § Lane rbd gives MonPostCreateBoss's full case table by BaseId (mods in call order, flag 1 except firegolem's 31, the uber classes' sets), the MonPostCreateMods flag-2 gate in MonSpawnTry (0x005B2ECF, [I]) and Nihlathak's mod 22 at [C] (run:2026-10-21-sweep-monsters-a); the rest of the table is [I]. § J's 'Blood Raven (12 and 22)' and the Maggot Queen line can take the table; § G row 60's escort tail is now chained by the model too. (2) drlg/room-tiles 9d's note on the bits that are not the build's: add 0x400, the client wall fade's alpha-0 mark (0x004DF05A, 0x004DF2A8, [I]), seen on a near room's wall entries only (33 entries in the council log, [C]); the checker now treats it like 0x20000 and 0x40000 on a neighbour. After the architect's review of lane/rbd.
