# 0006 — The server frame, part 6: frame windows on the harness

> **Subsystem:** sim/frame
> **Question:** does a stock game, logged in full over 250 or more consecutive frames in a small scene, chain every entry seed to the previous logged reading with nothing resynchronised, and in which order do shared-seed events run?
> **Date:** 2026-11-04   **Plan:** 0055 (Phase 2b)   **Status:** open (in progress; predictions section committed before the kept pilot log existed)

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
