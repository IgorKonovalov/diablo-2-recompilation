# 0006 — The server frame, part 6: frame windows on the harness

> **Subsystem:** sim/frame
> **Question:** does a stock game, logged in full over 250 or more consecutive frames in a small scene, chain every entry seed to the previous logged reading with nothing resynchronised, and in which order do shared-seed events run?
> **Date:** 2026-11-04   **Plan:** 0055 (Phase 2b)   **Status:** open (review requested: the town pilot passes, the pack pilot fails (b); Q2's trigger for the pack, stop for the architect)

## Predictions (committed before the kept session's log exists)

Tool revision: `tools/gdb/frame.py` and `tools/frame_window.py` at the commit that adds this file (the smoke sessions
`dev-2026-11-04-frame*` found two defects, both fixed and committed first: the post-call SV1 sites firing without an entry, and the
reader not printing its outcome mix). The model is the reader's chain: a seed object's entry reading equals its previous logged
reading (handed), a draw before an `FP` or `TM` site is located, every other difference is a mismatch.

Pilot (Act I town, normal, seed 5501, slot 1, first window of 250 frames, a fresh process):

- [I] (a) whole: an `FT0` and an `FT1` for each of 250 consecutive frames, 0 unparsed lines, every pair closed.
- [I] (b) unmoved: 0 mismatches, 0 located. The game seed does not move in the town window (a dev window showed 0 game-seed
  moves in 750 frames), so it is handed at every reading; unit seeds move in about 4 to 10 `UE0` events. Chained events 450 to 750.
- [I] (c) carried: about 10 s wall, about 25 frames per wall second (the stock rate), 7.5 to 9.5 lines per frame (0.5 to 0.6 of
  `estimate13` mid, 15.9), about 19.4 stops per frame, `QE`+`QF` per `UE0` near 0.53, the session far below 177 860 lines.
- [I] Timers in the window: `T20` 12 or 13, `D12` 21, `U11` 22 or 23, `S1500` 0, no `RC`, no `SV0`, no shared-seed pair.
- [I] What the town window cannot test: with the game seed never drawing, the game-seed chain is tested only as "unchanged".

### Predictions for the pack pilot (committed before its kept log exists)

Tool revision `8f026bf2` plus this file's commit. Cold Plains by the waypoint, seed 5501, slot 1, first window of 250 frames,
a pack in range (the runner waits for three live monsters within 22 sub-tiles), Nova by the pilot. The dev sessions
`dev-2026-11-04-frame-g` and `-h` (the same scene) are the basis; they showed 15 000 to 18 000 lines per window.

- [I] (a) whole: passes (the one logger defect the dev sessions showed, a second `UE1` at the join of the callback path, is fixed).
- [I] (c) carried: passes; 55 to 75 lines per frame (1.3 to 1.8 times `estimate13` mid 41.3; the 3x stop is 124.0), 70 to 90 stops
  per frame, 20 to 25 frames per wall second, the session far below 177 860 lines.
- [I] (b) unmoved: **does not pass**. The dev windows held 8 and 10 mismatches over 6 400 to 7 500 chained events, all on
  monsters' own seeds (stepped 1 to 14), none on the game seed or a player's. The reading to test: a monster's seed is
  drawn inside another unit's event (a Nova missile's hit, a kill's drop roll: the dev trace `FRAME_TRACE` showed five
  `0x0055879F`-`0x0055891A` steps of a dead monster's seed inside a missile's `UE0`/`UE1`) and the chain keyed by the event's
  own unit cannot see it. Predicted: 5 to 15 mismatches, every one a unit seed of type 1 stepped inside a window in which a
  missile (type 3) event was open between the two readings; none on `G`, none on a player.
- [I] Chained events 5 000 to 9 000 in the window; shared-seed pairs 0 to 5.

## Answer (summary)

- [C] **The Act I town pilot passes all three tests** (run:2026-11-04-frame, `2026-11-04-frame-s1-5501-town.log` `dfbd4401…`, first window frames 501-750):
  (a) 250 consecutive `FT0`/`FT1` pairs, no gap or repeat, 0 unparsed lines, every pair closed; (b) 0 mismatches, 0 located draws,
  0 reversed-inside, 413 chained events (426 `UE0`), 852 entry and 852 exit readings; (c) 10.0 s wall for 250 frames,
  25.1 frames per wall second, no crash, hang, lost input or watchdog stop. The two further town windows of the session
  (the walk, 17 `MSG0`, and the `mod 1500` frame 1500) also pass (a) and (b): 573 and 557 chained events, 0 mismatches, 0 located.
- [C] **The pack pilot fails (b)** (`…-5501-pack.log` `35915470…`, frames 1280-1529, Cold Plains by the waypoint, Nova): (a) passes, (c) passes,
  (b) shows **8 mismatches in 3 369 chained events**, every one a unit seed stepped between two logged readings (stepped 1, 1, 3, 4,
  5, 5, 5, 8): seven on monsters (type 1) and one on the player (type 0, id 1). This is Q2's trigger for the pack scene (plan 0055 Phase 2b);
  the maze scene was not run.
- [I] **What the traced draws are.** In a development session of the same scene with `FRAME_TRACE=1` (`dev-2026-11-04-frame-h`, 10 mismatches), the 8 draws the trace could attribute were
  steps of a monster's seed at return addresses 0x0055879F-0x0055891A (the item-drop quality code of 0x00558640-0x005589A0) inside an open
  missile (type 3) `UE0` pair: a kill's drop roll drawn on the dead monster's seed. The mismatches with steps of 1, 3 and 5 had no trace line:
  the trace covers the six RNG entries only (0x0045C370, 0x0045C390, 0x0045C3E0, 0x00472210, 0x00472240, 0x00472280), not the inline copies of the step.
  None of the traced steps came from the logger (no write; the same units step the same amounts in a run with no trace hooks, below).
- [I] **The chain keyed by an event's own unit cannot hold in a scene with hits.** Unit seeds are drawn inside other units' events
  (missile, skill and death handlers); a window with kills needs the other units' seeds read at those events, or those events given
  as boundary oracles for the seeds they touch. This is the architect's call (Q2).

## Leads used

None.

## Functions

No new name and no symbol row.

## Walkthrough

### 1. What the smoke sessions found (tools, not the game)

Four tool defects, each fixed and committed with a test where no game is needed (`tools/test_frame_window.py`, 16 tests): (1) `SV1` was logged at the three
instructions after the `SaveGameClients` calls, which the branch that skips a call also reaches (2 `SV1` per frame, no `SV0`): it is now logged only after an
`SV0`; (2) the callback path of every unit-event site jumps to the dispatch call's next instruction, so both `UE1` breakpoints fire for one event
(0x00540FB4 jumps to 0x00540FC9, and the nine like it): the second logs nothing (4 `LOGERR` in the first pack window); (3) the `SpecNova` recipe starts in
Act IV (difficulty byte 131; `RL` `lid` 103), so the first "town" session was the Pandemonium Fortress: the frame sessions use `tools/d2s_recipes/framenova.json`
(128) and refuse a session whose first level is not 1 (that log is kept as `dev-act4-*`, its window passed all three tests as well); (4) Teleport does not cast
in a town room (`InTown` clear), the hop did nothing and no message was sent: the town's second window walks (`hop --walk --hop-times`).
The Act I waypoint is at (4884, 5629) for map seed 5501 (an `OU0` of an objects log; the player starts at (4863, 5653)); another seed moves the town, so the
sessions use seed 5501. The pack scene waits for three live monsters within 22 sub-tiles (the `MON` line) before its window. The reader prints each window's
mismatches, located draws and outcome mix. The smoke sessions needed `--view-h 0` (the display shows 600 rows).

### 2. Figures the record states

| | town window 1 | pack window 1 |
|---|---|---|
| frames | 501-750 | 1280-1529 |
| wall s, frames per wall s | 10.0, 25.1 | 10.4, 24.0 |
| lines, per frame | 1 792, 7.17 | 8 744, 34.98 |
| `estimate13` mid, ratio | 15.9, 0.45 | 41.3, 0.85 |
| stops, per frame | 4 542, 18.2 | 11 497, 46.0 |
| `estimate13` stops | 32.9 | 58.3 |
| `QE`+`QF` per `UE0` (stated mid) | 0.90 (1.35) | 0.19 (1.01) |
| `UE0` / chained events | 426 / 413 | 3 699 / 3 369 |
| mismatches / located | 0 / 0 | 8 / 0 |
| shared-seed pairs (handed, in pass order) | 0 | 2 (2, 2) |
| timers `T20`, `D12`, `U11` seen of due | 12/12, 21/21, 23/23 | 13/13, 21/21, 23/23 |
| room activations (`RC`; in a `NewRoomsUpdate` walk) | 0 | 9 (1) |

gdb's own hit count: `WEND.ghits` is `{}` in every window, so the per-breakpoint count is `WEND.hits` (town window 1: `FT0` 250, `FP` 2 000, `ACL` 250, `UE0` 426,
`UE1` 426, `SV1` 500 (hits; none logged), `TM` 56, `QE` 381, `SYS` 2). The session's logger lines: 2 321 (town, all three windows 6 026 in windows), 10 037 (pack), far below Q2's 177 860.
Draw-free kind-11 runs (entry and exit seeds equal on every seed logged): 8 of 8 in the town window, 8 of 8 in the pack window.

### 3. Predictions against the outcome

The town predictions (committed before the kept log) missed on two figures: 413 chained events against 450 to 750 and `QE`+`QF` per `UE0` 0.90 against about 0.53,
because they were taken from the Act IV smoke window. The pack predictions held for (a), (c) lines per frame missed (35.0 against 55 to 75), chained events missed
(3 369 against 5 000 to 9 000), mismatches 8 against 5 to 15 held, and "none on a player" **failed**: one mismatch is the player's (`('U', 0, 1)` stepped 4, 66 `UE0`/`UE1` lines between).
The player's step is untraced (no trace line in the kept log, none in the dev runs).

### 4. What the zeros test, and what they cannot

- [I] The town window: the game seed never moved (0 `G UE0`, 0 `FP`/`TM` with a draw), 6 `UE0` moved a unit seed. Its 0 mismatches test that no unit seed
  moves outside its own events in a quiet town and that the game seed is unchanged; the reader's negative controls (a gap, a repeat, an unclosed pair, a seed off by one,
  a reversed pair, an unparsed line, stray text, a lost `FT1`; `window-selftest`) each fail the test they are for. The town cannot test a draw order.
- [I] The pack window has 11 `UE0` that moved the game seed and 16 that moved a unit seed, 2 shared-seed pairs: the chain was tested where seeds move, and it failed where another unit's event moves a seed.
- [I] Boundary oracles: none were declared in the town or the pack window (the kinds in Cold Plains' pack were not classified against the reviewed tier in this run); the window counts for event order and for the chain, and the pack's 8 are not given as oracles.

### 5. Not done

The maze scene, the batch (the floors: 10 windows of 250 frames in three scenes with two windows each, 5 000 chained events, 20 shared-seed pairs, a window with a `mod 8192` frame) and the
`lane/s52a` scene-kind bookkeeping (tier kinds against boundary oracles) were not run: the pack pilot's failure stops the batch (plan 0055 Phase 2b: Q2's trigger). Met so far: one town session of 3 windows (750 frames, 1 543 chained events), one `mod 1500` frame (town), no `mod 8192`, 2 shared-seed pairs, 9 room activations (1 in a walk).

## Open questions

- `[L]` the player's stepped seed in the pack window (type 0, id 1, 4 steps, 66 events between): which handler drew it.
- `[L]` whether the inline copies of the step (the multiplier 0x6AC690C5 outside the six entries) account for the mismatches the trace did not see.
- `[L]` sound: every session ran with `-ns` (the runner's default, no `--sound`); no figure here is known to depend on it, and none was run with sound.
