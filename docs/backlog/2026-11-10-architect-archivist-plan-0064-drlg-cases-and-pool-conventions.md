---
from: architect
to: archivist
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S3.md
  - ../plans/0064-cleanroom/S4.md
  - ../formats/golden-trace.md
resolution: ""
---

**Golden-set and format defects (plan 0064 P3 triage, S4 rows 1–5 and 22, S3 row 3).** (a) **Maze `first_room_seed` is emitted after the run mutated it** (S4 row 2): `tools/golden.py` `observed_maze` passes the `Seed` object `first` to `mz.run`, which assigns it to R0 and steps it in growth, then writes `first.lo/first.hi` into the case. Over the 50 maze cases the input equals maze B1's seed (`Init(window_seed.low)`, one `Step`) stepped k more times, k = 0 (the five level-8 cases, no growth) to 5; 45 of 50 differ from B1. Write the seed before the run (or drop the input: B1 derives it from `window_seed`, and say so in § Drlg cases), re-emit, re-join the v1 set and record the new digest. (b) **Maze room order** (S4 row 1): golden-trace § Fields (and `golden.py`'s field description) says "in creation order"; the digest is over the logged list, newest first (drlg/maze § Outputs; all 50 matched once the implementer used list order). Write "in list order (newest first, drlg/maze § Outputs)". (c) **Maze cases carry no `difficulty`** (S4 row 3) while maze C1 reads `Rooms[difficulty]`; add it as outdoor does (from the log's name), or state that the v1 maze levels have equal `Rooms` in all three. (d) **Coordinate frames** (S4 rows 4–5): `presets_digest`'s `x, y` and `rooms_digest`'s "rect origin the room-link line logs" name no frame for a reader who never sees the log; state absolute tiles, `L.rect.x + 8·cx` (drlg/overview step 8). (e) **Pool order** (S3 row 3): § Conventions' "the model's order" for `.region.N` and the digest; state "the kept (`isSpawn`) entries in append order, monsters/pool § C8 and § Outputs". (f) **File-name case** (S4 row 22): specs and tables write `LvlMaze.txt`, `Act1/Outdoors/BorderMiddle.ds1`; the sandbox holds lower-case names. Either keep the case in `cleanroom.py make` or say in the brief (or formats/mpq) that archive paths compare case-insensitively. (g) tables/MonStats.md types `MonStatsEx` `+0x018` as a u16 index and its row-identity note says a blank stores −1; monsters/pool § Inputs types it i16 (S3 row 4): make the table doc agree with itself (the spec-writer's pool entry takes the spec side).
