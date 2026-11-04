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
